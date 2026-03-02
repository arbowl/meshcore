"""Web UI entry point with proper logging"""

import asyncio
import logging
import threading

from meshcore.adapters.meshtastic.commander import (
    MeshtasticCommander,
    MeshtasticTcpCommander,
    MockCommander,
)
from meshcore.adapters.ui.web import create_app
from meshcore.config import MeshCoreConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def _run_event_collection(config: MeshCoreConfig, interface) -> None:
    """Async loop that collects mesh events and writes them to the DBs."""
    from meshcore.adapters.meshtastic.tcp import MeshtasticTcpSource
    from meshcore.adapters.pubsub.logging import LoggingPublisher
    from meshcore.adapters.storage.sqlite import SqliteEventStore
    from meshcore.adapters.storage.state_sqlite import SqliteStateStore
    from meshcore.application.services import MeshEventService
    from meshcore.application.state_projection import StateProjection

    source = MeshtasticTcpSource(
        host=config.meshtastic_tcp_host, interface=interface
    )
    event_store = SqliteEventStore(path=config.event_db_path)
    state_store = SqliteStateStore(path=config.state_db_path)

    async with event_store, state_store:
        projection = StateProjection(state_store)
        service = MeshEventService(
            source=source,
            store=event_store,
            publisher=LoggingPublisher(),
            state_projection=projection,
        )
        await service.run()


def _start_event_collection(config: MeshCoreConfig, interface) -> None:
    """Spawn a daemon thread that runs the event collection asyncio loop."""
    def _run():
        try:
            asyncio.run(_run_event_collection(config, interface))
        except Exception as e:
            logger.error(f"Event collection thread died: {e}", exc_info=True)

    thread = threading.Thread(target=_run, daemon=True, name="EventCollector")
    thread.start()
    logger.info("Background event collection started")


def main():
    """Run the web server"""
    config = MeshCoreConfig.from_env()

    commander = None
    if config.meshtastic_source == "tcp":
        import meshtastic.tcp_interface
        logger.info(f"Using TCP mode: {config.meshtastic_tcp_host}")
        # Create one shared interface so the source and commander both use the
        # same TCP connection.  Having two interfaces in the same process would
        # cause every received packet to be processed twice via pubsub.
        interface = meshtastic.tcp_interface.TCPInterface(
            hostname=config.meshtastic_tcp_host
        )
        _start_event_collection(config, interface)
        commander = MeshtasticTcpCommander(
            host=config.meshtastic_tcp_host, interface=interface
        )
    elif config.meshtastic_source == "serial":
        logger.info(f"Using SERIAL commander: {config.meshtastic_device}")
        commander = MeshtasticCommander(device=config.meshtastic_device)
    else:
        logger.info("Using MOCK commander (no messages will be broadcast)")
        commander = MockCommander()

    app = create_app(
        state_db_path=config.state_db_path,
        events_db_path=config.event_db_path,
        commander=commander,
    )
    logger.info(f"MeshCore Web UI starting with config: {config}")
    logger.info("Dashboard: http://localhost:5000")
    logger.info("API: http://localhost:5000/api/nodes")
    logger.info("Press Ctrl+C to stop")
    try:
        app.run(host=config.web_host, port=config.web_port, debug=config.web_debug)
    except KeyboardInterrupt:
        logger.info("\nShutting down web server...")
    except Exception as e:
        logger.error(f"Web server error: {e}", exc_info=True)
        raise
    finally:
        if hasattr(commander, 'close'):
            commander.close()


if __name__ == "__main__":
    main()
