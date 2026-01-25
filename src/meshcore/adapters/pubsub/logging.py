"""Pub/sub layer for the application"""

from meshcore.domain.models import MeshEvent


class LoggingPublisher:
    """Publisher that logs events"""

    async def publish(self, event: MeshEvent) -> None:
        """Publish the event by logging it to console"""
        print(event.model_dump_json())
