"""MQTT protocol for the meshcore pubsub adapter."""

import asyncio

import paho.mqtt.client as mqtt

from meshcore.domain.models import MeshEvent


class MqttEventPublisher:
    """MQTT event publisher"""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 1883,
        topic: str = "meshcore/events",
        client_id: str = "meshcore",
    ) -> None:
        self._host = host
        self._port = port
        self._topic = topic
        self._client = mqtt.Client(
            client_id=client_id, protocol=mqtt.MQTTv311
        )
        self._connected = False

    async def __aenter__(self):
        await asyncio.to_thread(
            self._client.connect, self._host, self._port
        )
        self._client.loop_start()
        self._connected = True
        return self

    async def __aexit__(self, *args):
        if self._connected:
            self._client.loop_stop()
            self._client.disconnect()
            self._connected = False

    async def publish(self, event: MeshEvent) -> None:
        if not self._connected:
            await asyncio.to_thread(
                self._client.connect, self._host, self._port
            )
            self._client.loop_start()
            self._connected = True
        payload = event.model_dump_json()
        topics = [
            f"{self._topic}/all",
            f"{self._topic}/type/{event.event_type}",
            f"{self._topic}/node/{event.node_id.value}",
            f"{self._topic}/node/{event.node_id.value}/type/"
            f"{event.event_type}",
        ]
        for topic in topics:
            self._client.publish(topic, payload, qos=1)
