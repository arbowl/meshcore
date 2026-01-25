"""Meshtastic TCP/IP source"""

import asyncio
from typing import AsyncIterator, Optional

import meshtastic
import meshtastic.tcp_interface

from meshcore.application.ports import EventSource
from meshcore.domain.models import MeshEvent

from .translate import translate_packet


class MeshtasticTcpSource(EventSource):
    """TCP/IP network connection to Meshtastic device"""

    def __init__(self, host: str, port: int = 4403) -> None:
        self._host = host
        self._port = port
        self._interface: Optional[meshtastic.tcp_interface.TCPInterface] = None
        self._queue: asyncio.Queue = asyncio.Queue()

    async def _connect(self) -> None:
        self._interface = meshtastic.tcp_interface.TCPInterface(
            hostname=self._host
        )
        self._interface.onReceive = self._on_receive

    def _on_receive(self, packet: dict) -> None:
        event = translate_packet(packet)
        if event:
            self._queue.put_nowait(event)

    async def events(self) -> AsyncIterator[MeshEvent]:
        await self._connect()
        while True:
            event: MeshEvent = await self._queue.get()
            yield event

