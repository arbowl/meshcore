"""Meshtastic source"""

import asyncio
import logging
from typing import AsyncIterator, Optional

import meshtastic
import meshtastic.serial_interface
from pubsub import pub

from meshcore.application.ports import EventSource
from meshcore.domain.models import MeshEvent
from .translate import translate_packet, translate_node_update

logger = logging.getLogger(__name__)


class MeshtasticSource(EventSource):
    """Serial device path"""

    def __init__(self, device: Optional[str] = None) -> None:
        self._device = device
        self._interface: Optional[
            meshtastic.serial_interface.SerialInterface
        ] = None
        self._queue: asyncio.Queue = asyncio.Queue()
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    # The meshtastic library publishes to handler-specific sub-topics
    # (e.g. "meshtastic.receive.text") for all known port types.
    # The generic "meshtastic.receive" topic is only used as a fallback
    # for UNKNOWN_APP packets, so we must subscribe to each sub-topic.
    _PACKET_TOPICS = (
        "meshtastic.receive",           # UNKNOWN_APP fallback
        "meshtastic.receive.text",      # TEXT_MESSAGE_APP
        "meshtastic.receive.position",  # POSITION_APP
        "meshtastic.receive.user",      # NODEINFO_APP
        "meshtastic.receive.telemetry", # TELEMETRY_APP
        "meshtastic.receive.routing",   # ROUTING_APP (ACK)
    )

    async def _connect(self) -> None:
        self._loop = asyncio.get_running_loop()
        for topic in self._PACKET_TOPICS:
            pub.subscribe(self._on_receive, topic)
        pub.subscribe(self._on_node_updated, "meshtastic.node.updated")
        self._interface = meshtastic.serial_interface.SerialInterface(
            devPath=self._device
        )

    def _on_receive(self, packet, interface=None) -> None:
        """Called from meshtastic's publishing thread — must be thread-safe."""
        event = translate_packet(packet)
        if event:
            self._loop.call_soon_threadsafe(self._queue.put_nowait, event)

    def _on_node_updated(self, node, interface=None) -> None:
        """Called when node DB is updated (initial sync + periodic)."""
        event = translate_node_update(node)
        if event:
            self._loop.call_soon_threadsafe(self._queue.put_nowait, event)

    async def events(self) -> AsyncIterator[MeshEvent]:
        """Async iterator of MeshEvents from Meshtastic device"""
        await self._connect()
        while True:
            event: MeshEvent = await self._queue.get()
            yield event
