"""MQTT protocol for the meshcore pubsub adapter with reconnection logic."""

import asyncio
import logging

import paho.mqtt.client as mqtt

from meshcore.domain.models import MeshEvent

logger = logging.getLogger(__name__)


class MqttEventPublisher:
    """MQTT event publisher with automatic reconnection"""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 1883,
        topic: str = "meshcore/events",
        client_id: str = "meshcore",
        max_retries: int = 5,
        initial_retry_delay: float = 1.0,
    ) -> None:
        self._host = host
        self._port = port
        self._topic = topic
        self._client = mqtt.Client(
            client_id=client_id, protocol=mqtt.MQTTv311
        )
        self._connected = False
        self._max_retries = max_retries
        self._initial_retry_delay = initial_retry_delay
        self._retry_count = 0
        self._lock = asyncio.Lock()
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        logger.info(f"MQTT publisher initialized for {host}:{port}")

    def _on_connect(self, client, userdata, flags, rc):
        """Callback when connection is established"""
        if rc == 0:
            self._connected = True
            self._retry_count = 0
            logger.info(f"MQTT connected to {self._host}:{self._port}")
        else:
            logger.error(f"MQTT connection failed with code {rc}")

    def _on_disconnect(self, client, userdata, rc):
        """Callback when disconnected"""
        self._connected = False
        if rc != 0:
            logger.warning(f"MQTT unexpected disconnection (code {rc})")

    async def __aenter__(self):
        """Async context manager entry"""
        await self._connect()
        return self

    async def __aexit__(self, *args):
        """Async context manager exit"""
        await self.close()

    async def _connect(self) -> None:
        """Connect with exponential backoff retry logic"""
        retry_delay = self._initial_retry_delay
        for attempt in range(self._max_retries):
            try:
                logger.info(
                    f"Attempting MQTT connection (attempt {attempt + 1}/"
                    f"{self._max_retries})"
                )
                await asyncio.to_thread(
                    self._client.connect, self._host, self._port, keepalive=60
                )
                self._client.loop_start()
                for _ in range(10):
                    await asyncio.sleep(0.1)
                    if self._connected:
                        return
                logger.warning("MQTT connection timeout")
            except Exception as e:
                logger.error(f"MQTT connection attempt failed: {e}")
            if attempt < self._max_retries - 1:
                logger.info(f"Retrying in {retry_delay:.1f}s...")
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 30)  # Cap at 30 seconds
        raise ConnectionError(
            f"Failed to connect to MQTT broker after {self._max_retries} "
            "attempts"
        )

    async def close(self) -> None:
        """Gracefully close the connection"""
        if self._connected:
            self._client.loop_stop()
            await asyncio.to_thread(self._client.disconnect)
            self._connected = False
            logger.info("MQTT publisher closed")

    async def _ensure_connected(self) -> None:
        """Ensure we have an active connection, reconnect if needed"""
        if not self._connected:
            logger.warning("MQTT not connected, attempting reconnection...")
            await self._connect()

    async def publish(self, event: MeshEvent) -> None:
        """Publish event to MQTT with automatic reconnection"""
        async with self._lock:
            await self._ensure_connected()
            payload = event.model_dump_json()
            topics = [
                f"{self._topic}/all",
                f"{self._topic}/type/{event.event_type}",
                f"{self._topic}/node/{event.node_id.value}",
                f"{self._topic}/node/{event.node_id.value}/type/"
                f"{event.event_type}",
            ]
            correlation_id = str(event.event_id.value)
            for topic in topics:
                try:
                    result = await asyncio.to_thread(
                        self._client.publish, topic, payload, qos=1
                    )
                    if result.rc != mqtt.MQTT_ERR_SUCCESS:
                        logger.error(
                            f"MQTT publish failed for {topic}: {result.rc}",
                            extra={"correlation_id": correlation_id}
                        )
                except Exception as e:
                    logger.error(
                        f"Exception publishing to {topic}: {e}",
                        extra={"correlation_id": correlation_id}
                    )
            logger.debug(
                f"Published event {event.event_type} from "
                f"{event.node_id.value}",
                extra={"correlation_id": correlation_id}
            )
