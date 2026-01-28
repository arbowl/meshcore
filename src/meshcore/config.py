"""Centralized configuration management with environment variable support"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class MeshCoreConfig:
    """Configuration for MeshCore application

    All values can be overridden via environment variables with
    MESHCORE_ prefix. For example: MESHCORE_EVENT_DB_PATH
    """

    # Database paths
    event_db_path: str = "events.db"
    state_db_path: str = "state.db"

    # MQTT Configuration
    mqtt_enabled: bool = True
    mqtt_host: str = "localhost"
    mqtt_port: int = 1883
    mqtt_topic: str = "meshcore/events"
    mqtt_client_id: str = "meshcore"

    # Web UI Configuration
    web_host: str = "0.0.0.0"
    web_port: int = 5000
    web_debug: bool = False

    # Meshtastic Configuration
    meshtastic_device: Optional[str] = None  # Auto-detect if None
    meshtastic_tcp_host: Optional[str] = None
    meshtastic_source: str = "mock"  # mock, serial, or tcp
    mock_interval: float = 1.5

    # Service Configuration
    max_retries: int = 3
    retry_delay: float = 1.0

    @classmethod
    def from_env(cls) -> "MeshCoreConfig":
        """Create configuration from environment variables"""
        return cls(
            event_db_path=os.getenv(
                "MESHCORE_EVENT_DB_PATH", "events.db"
            ),
            state_db_path=os.getenv(
                "MESHCORE_STATE_DB_PATH", "state.db"
            ),
            mqtt_enabled=(
                os.getenv("MESHCORE_MQTT_ENABLED", "true").lower()
                == "true"
            ),
            mqtt_host=os.getenv("MESHCORE_MQTT_HOST", "localhost"),
            mqtt_port=int(os.getenv("MESHCORE_MQTT_PORT", "1883")),
            mqtt_topic=os.getenv(
                "MESHCORE_MQTT_TOPIC", "meshcore/events"
            ),
            mqtt_client_id=os.getenv(
                "MESHCORE_MQTT_CLIENT_ID", "meshcore"
            ),
            web_host=os.getenv("MESHCORE_WEB_HOST", "0.0.0.0"),
            web_port=int(os.getenv("MESHCORE_WEB_PORT", "5000")),
            web_debug=(
                os.getenv("MESHCORE_WEB_DEBUG", "false").lower()
                == "true"
            ),
            meshtastic_device=os.getenv("MESHCORE_MESHTASTIC_DEVICE"),
            meshtastic_tcp_host=os.getenv(
                "MESHCORE_MESHTASTIC_TCP_HOST"
            ),
            meshtastic_source=os.getenv("MESHCORE_SOURCE", "mock"),
            mock_interval=float(
                os.getenv("MESHCORE_MOCK_INTERVAL", "1.5")
            ),
            max_retries=int(os.getenv("MESHCORE_MAX_RETRIES", "3")),
            retry_delay=float(os.getenv("MESHCORE_RETRY_DELAY", "1.0")),
        )

    def __repr__(self) -> str:
        """String representation hiding sensitive data"""
        return (
            f"MeshCoreConfig("
            f"event_db={self.event_db_path}, "
            f"state_db={self.state_db_path}, "
            f"mqtt={self.mqtt_host}:{self.mqtt_port}, "
            f"source={self.meshtastic_source})"
        )
