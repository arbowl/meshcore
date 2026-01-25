"""Meshtastic command adapter for sending messages"""

import asyncio
import logging
from typing import Optional

import meshtastic.serial_interface

from meshcore.application.ports import CommandResult, MeshCommandPort

logger = logging.getLogger(__name__)


class MeshtasticCommander(MeshCommandPort):
    """Send commands through Meshtastic serial interface"""

    def __init__(self, device: Optional[str] = None):
        self._device = device
        self._interface: Optional[meshtastic.serial_interface.SerialInterface] = None

    def _ensure_connected(self) -> None:
        """Ensure we have an active connection"""
        if self._interface is None:
            self._interface = meshtastic.serial_interface.SerialInterface(
                devPath=self._device
            )

    async def send_text(
        self,
        text: str,
        destination: Optional[str] = None,
        channel: int = 0,
    ) -> CommandResult:
        """Send text message to the mesh"""
        try:
            self._ensure_connected()

            # Default to broadcast if no destination
            dest_id = destination if destination else "^all"

            # Send message in thread to avoid blocking
            await asyncio.to_thread(
                self._interface.sendText,
                text,
                destinationId=dest_id,
                channelIndex=channel,
            )

            logger.info(f"Sent message to {dest_id}: {text[:50]}...")
            return CommandResult(
                success=True,
                message=f"Message sent to {dest_id}",
            )

        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return CommandResult(
                success=False,
                message="Failed to send message",
                error=str(e),
            )

    async def send_position(
        self,
        latitude: float,
        longitude: float,
        altitude: Optional[float] = None,
        destination: Optional[str] = None,
    ) -> CommandResult:
        """Send position update"""
        try:
            self._ensure_connected()

            dest_id = destination if destination else "^all"

            # Meshtastic library method for sending position
            await asyncio.to_thread(
                self._interface.sendPosition,
                latitude=latitude,
                longitude=longitude,
                altitude=altitude or 0,
                destinationId=dest_id,
            )

            logger.info(f"Sent position to {dest_id}: {latitude}, {longitude}")
            return CommandResult(
                success=True,
                message=f"Position sent to {dest_id}",
            )

        except Exception as e:
            logger.error(f"Failed to send position: {e}")
            return CommandResult(
                success=False,
                message="Failed to send position",
                error=str(e),
            )

    def close(self) -> None:
        """Close the connection"""
        if self._interface:
            self._interface.close()
            self._interface = None


class MockCommander(MeshCommandPort):
    """Mock commander for testing without hardware"""

    async def send_text(
        self,
        text: str,
        destination: Optional[str] = None,
        channel: int = 0,
    ) -> CommandResult:
        """Mock send text"""
        dest = destination or "broadcast"
        logger.info(f"[MOCK] Sending to {dest}: {text}")
        await asyncio.sleep(0.1)  # Simulate network delay
        return CommandResult(
            success=True,
            message=f"Message sent to {dest}",
        )

    async def send_position(
        self,
        latitude: float,
        longitude: float,
        altitude: Optional[float] = None,
        destination: Optional[str] = None,
    ) -> CommandResult:
        """Mock send position"""
        dest = destination or "broadcast"
        logger.info(f"[MOCK] Sending position to {dest}: {latitude}, {longitude}")
        await asyncio.sleep(0.1)
        return CommandResult(
            success=True,
            message=f"Position sent to {dest}",
        )
