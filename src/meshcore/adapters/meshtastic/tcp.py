"""Meshtastic TCP/IP source"""

import asyncio
import logging
from typing import AsyncIterator, Optional

import meshtastic
import meshtastic.tcp_interface
from pubsub import pub

from meshcore.application.ports import EventSource
from meshcore.domain.models import MeshEvent

from .translate import translate_packet, translate_node_update

logger = logging.getLogger(__name__)


class MeshtasticTcpSource(EventSource):
    """TCP/IP network connection to Meshtastic device"""

    def __init__(self, host: str, port: int = 4403) -> None:
        self._host = host
        self._port = port
        self._interface: Optional[meshtastic.tcp_interface.TCPInterface] = None
        self._queue: asyncio.Queue = asyncio.Queue()
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    async def _connect(self) -> None:
        self._loop = asyncio.get_running_loop()
        pub.subscribe(self._on_receive, "meshtastic.receive")
        pub.subscribe(self._on_node_updated, "meshtastic.node.updated")
        self._interface = meshtastic.tcp_interface.TCPInterface(
            hostname=self._host
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
        await self._connect()
        while True:
            event: MeshEvent = await self._queue.get()
            yield event
