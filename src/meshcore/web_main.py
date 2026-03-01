"""Web UI entry point with proper logging"""

import logging

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


def create_commander(config: MeshCoreConfig):
    """Create commander based on configuration"""
    if config.meshtastic_source == "serial":
        device_info = config.meshtastic_device or "auto-detect"
        logger.info(f"Using SERIAL commander: {device_info}")
        return MeshtasticCommander(device=config.meshtastic_device)
    elif config.meshtastic_source == "tcp":
        logger.info(f"Using TCP commander: {config.meshtastic_tcp_host}")
        return MeshtasticTcpCommander(host=config.meshtastic_tcp_host)
    else:
        logger.info("Using MOCK commander (no messages will be broadcast)")
        return MockCommander()


def main():
    """Run the web server"""
    config = MeshCoreConfig.from_env()
    commander = create_commander(config)
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
        commander.close() if hasattr(commander, 'close') else None


if __name__ == "__main__":
    main()
