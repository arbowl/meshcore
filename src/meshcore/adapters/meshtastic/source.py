"""Meshtastic source"""

import asyncio
from typing import AsyncIterator, Optional

import meshtastic
import meshtastic.serial_interface

from meshcore.application.ports import EventSource
from meshcore.domain.models import MeshEvent
from .translate import translate_packet


class MeshtasticSource(EventSource):
    """Serial device path"""

    def __init__(self, device: Optional[str] = None) -> None:
        self._device = device
        self._interface: Optional[
            meshtastic.serial_interface.SerialInterface
        ] = None
        self._queue: asyncio.Queue = asyncio.Queue()

    async def _connect(self) -> None:
        self._interface = meshtastic.serial_interface.SerialInterface(
            devPath=self._device
        )
        self._interface.onReceive = self._on_receive

    def _on_receive(self, packet: dict) -> None:
        event = translate_packet(packet)
        if event:
            self._queue.put_nowait(event)

    async def events(self) -> AsyncIterator[MeshEvent]:
        """Async iterator of MeshEvents from Meshtastic device"""
        await self._connect()
        while True:
            event: MeshEvent = await self._queue.get()
            yield event
