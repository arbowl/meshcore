"""Main entry point with flexible configuration and proper lifecycle
management
"""

import argparse
import asyncio
import logging
import sys

from meshcore.adapters.meshtastic.mock import MockMeshtasticEventSource
from meshcore.adapters.meshtastic.source import MeshtasticSource
from meshcore.adapters.meshtastic.tcp import MeshtasticTcpSource
from meshcore.adapters.pubsub.logging import LoggingPublisher
from meshcore.adapters.pubsub.mqtt import MqttEventPublisher
from meshcore.adapters.storage.sqlite import SqliteEventStore
from meshcore.adapters.storage.state_sqlite import SqliteStateStore
from meshcore.application.services import MeshEventService
from meshcore.application.state_projection import StateProjection
from meshcore.config import MeshCoreConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_args() -> MeshCoreConfig | None:
    """Parse command line arguments and return config"""
    parser = argparse.ArgumentParser(
        description="MeshCore Event Service",
        add_help=True
    )
    parser.add_argument(
        "--source",
        choices=["mock", "serial", "tcp"],
        help="Event source type"
    )
    parser.add_argument("--device", help="Serial device path")
    parser.add_argument("--tcp-host", help="TCP host address")
    parser.add_argument("--mock-interval", type=float, default=1.5)
    parser.add_argument("--mqtt-host", default="localhost")
    parser.add_argument("--mqtt-topic", default="meshcore/events")
    parser.add_argument("--no-mqtt", action="store_true")
    parser.add_argument(
        "--debug", action="store_true", help="Enable debug logging"
    )
    if len(sys.argv) == 1:
        return None
    args = parser.parse_args()
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Start with environment variables, then override with CLI args
    config = MeshCoreConfig.from_env()
    
    if args.source:
        config.meshtastic_source = args.source
    if args.device:
        config.meshtastic_device = args.device
    if args.tcp_host:
        config.meshtastic_tcp_host = args.tcp_host
    config.mock_interval = args.mock_interval
    config.mqtt_enabled = not args.no_mqtt
    if args.mqtt_host:
        config.mqtt_host = args.mqtt_host
    if args.mqtt_topic:
        config.mqtt_topic = args.mqtt_topic
    
    return config


def interactive_config() -> MeshCoreConfig:
    """Interactive configuration prompts"""
    print("\n=== MeshCore Configuration ===\n")
    print("Select event source:")
    print("  1. Mock (simulated data)")
    print("  2. Serial USB")
    print("  3. TCP/IP Network")
    print("  4. Exit")
    choice = input("\nChoice [1-4]: ").strip()
    
    # Start with environment variables
    config = MeshCoreConfig.from_env()
    
    if choice == "1":
        config.meshtastic_source = "mock"
        interval = input("Event interval in seconds [1.5]: ").strip()
        config.mock_interval = float(interval) if interval else 1.5
    elif choice == "2":
        config.meshtastic_source = "serial"
        device = input("Device port (Enter for auto-detect): ").strip()
        config.meshtastic_device = device if device else None
    elif choice == "3":
        config.meshtastic_source = "tcp"
        host = input("Device IP address: ").strip()
        if not host:
            print("Error: IP address required")
            sys.exit(1)
        config.meshtastic_tcp_host = host
    elif choice == "4":
        print("Exiting...")
        sys.exit(0)
    else:
        print("Invalid choice")
        sys.exit(1)
    
    mqtt = input("\nEnable MQTT publishing? [Y/n]: ").strip().lower()
    config.mqtt_enabled = mqtt != "n"
    if config.mqtt_enabled:
        host = input("MQTT broker host [localhost]: ").strip()
        config.mqtt_host = host if host else "localhost"
    
    return config


def create_source(config: MeshCoreConfig):
    """Create event source based on configuration"""
    if config.meshtastic_source == "mock":
        logger.info(f"Using MOCK source (interval: {config.mock_interval}s)")
        return MockMeshtasticEventSource(interval=config.mock_interval)
    elif config.meshtastic_source == "serial":
        device_info = config.meshtastic_device or "auto-detect"
        logger.info(f"Using SERIAL source: {device_info}")
        return MeshtasticSource(device=config.meshtastic_device)
    elif config.meshtastic_source == "tcp":
        logger.info(f"Using TCP source: {config.meshtastic_tcp_host}")
        return MeshtasticTcpSource(host=config.meshtastic_tcp_host)
    else:
        raise ValueError(f"Unknown source type: {config.meshtastic_source}")


async def create_publisher(config: MeshCoreConfig):
    """Create and initialize publisher with proper lifecycle"""
    if config.mqtt_enabled:
        logger.info(
            f"MQTT publishing enabled: "
            f"{config.mqtt_host}:{config.mqtt_port}"
        )
        publisher = MqttEventPublisher(
            host=config.mqtt_host,
            port=config.mqtt_port,
            topic=config.mqtt_topic,
            client_id=config.mqtt_client_id,
        )
        await publisher.__aenter__()
        return publisher
    else:
        logger.info("MQTT disabled, using console logging")
        return LoggingPublisher()


async def main_loop(config: MeshCoreConfig):
    """Main service loop with proper resource management"""
    source = create_source(config)
    publisher = None
    event_store = None
    state_store = None
    try:
        publisher = await create_publisher(config)
        event_store = SqliteEventStore(path=config.event_db_path)
        await event_store.__aenter__()
        state_store = SqliteStateStore(path=config.state_db_path)
        await state_store.__aenter__()
        state_projection = StateProjection(state_store)
        logger.info(f"Starting MeshCore service with config: {config}")
        logger.info("Press Ctrl+C to stop\n")
        service = MeshEventService(
            source=source,
            store=event_store,
            publisher=publisher,
            state_projection=state_projection,
            max_retries=config.max_retries,
            retry_delay=config.retry_delay,
        )
        await service.run()
    except asyncio.CancelledError:
        logger.info("Service shutdown requested")
    except Exception as e:
        logger.error(f"Service error: {e}", exc_info=True)
        raise
    finally:
        logger.info("Cleaning up resources...")
        if publisher and config.mqtt_enabled:
            try:
                await publisher.__aexit__(None, None, None)
            except Exception as e:
                logger.error(f"Error closing publisher: {e}")
        if event_store:
            try:
                await event_store.__aexit__(None, None, None)
            except Exception as e:
                logger.error(f"Error closing event store: {e}")
        if state_store:
            try:
                await state_store.__aexit__(None, None, None)
            except Exception as e:
                logger.error(f"Error closing state store: {e}")
        logger.info("Shutdown complete")


def main():
    try:
        config = parse_args()
        if config is None:
            config = interactive_config()
        asyncio.run(main_loop(config))
    except KeyboardInterrupt:
        logger.info("\n\nShutdown requested. Goodbye!")
    except Exception as e:
        logger.error(f"\nError: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
