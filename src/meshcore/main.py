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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Config:
    """Configuration container"""
    def __init__(self):
        self.source_type = "mock"
        self.device = None
        self.tcp_host = None
        self.mock_interval = 1.5
        self.mqtt_enabled = True
        self.mqtt_host = "localhost"
        self.mqtt_topic = "meshcore/events"


def parse_args():
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
    config = Config()
    config.source_type = args.source
    config.device = args.device
    config.tcp_host = args.tcp_host
    config.mock_interval = args.mock_interval
    config.mqtt_enabled = not args.no_mqtt
    config.mqtt_host = args.mqtt_host
    config.mqtt_topic = args.mqtt_topic
    return config


def interactive_config():
    print("\n=== MeshCore Configuration ===\n")
    print("Select event source:")
    print("  1. Mock (simulated data)")
    print("  2. Serial USB")
    print("  3. TCP/IP Network")
    print("  4. Exit")
    choice = input("\nChoice [1-4]: ").strip()
    config = Config()
    if choice == "1":
        config.source_type = "mock"
        interval = input("Event interval in seconds [1.5]: ").strip()
        config.mock_interval = float(interval) if interval else 1.5
    elif choice == "2":
        config.source_type = "serial"
        device = input("Device port (Enter for auto-detect): ").strip()
        config.device = device if device else None
    elif choice == "3":
        config.source_type = "tcp"
        host = input("Device IP address: ").strip()
        if not host:
            print("Error: IP address required")
            sys.exit(1)
        config.tcp_host = host
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


def create_source(config):
    if config.source_type == "mock":
        logger.info(f"Using MOCK source (interval: {config.mock_interval}s)")
        return MockMeshtasticEventSource(interval=config.mock_interval)
    elif config.source_type == "serial":
        device_info = config.device or "auto-detect"
        logger.info(f"Using SERIAL source: {device_info}")
        return MeshtasticSource(device=config.device)
    elif config.source_type == "tcp":
        logger.info(f"Using TCP source: {config.tcp_host}")
        return MeshtasticTcpSource(host=config.tcp_host)
    else:
        raise ValueError(f"Unknown source type: {config.source_type}")


async def create_publisher(config):
    """Create and initialize publisher with proper lifecycle"""
    if config.mqtt_enabled:
        logger.info(f"MQTT publishing enabled: {config.mqtt_host}")
        publisher = MqttEventPublisher(
            host=config.mqtt_host,
            topic=config.mqtt_topic
        )
        await publisher.__aenter__()
        return publisher
    else:
        logger.info("MQTT disabled, using console logging")
        return LoggingPublisher()


async def main_loop(config):
    """Main service loop with proper resource management"""
    source = create_source(config)
    publisher = None
    event_store = None
    state_store = None
    try:
        publisher = await create_publisher(config)
        event_store = SqliteEventStore()
        await event_store.__aenter__()
        state_store = SqliteStateStore()
        await state_store.__aenter__()
        state_projection = StateProjection(state_store)
        logger.info("Starting MeshCore service...")
        logger.info("Press Ctrl+C to stop\n")
        service = MeshEventService(
            source=source,
            store=event_store,
            publisher=publisher,
            state_projection=state_projection,
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
