"""Service for the app"""

import asyncio
import logging

from meshcore.application.ports import EventPublisher, EventSource, EventStore
from meshcore.application.state_projection import StateProjection

logger = logging.getLogger(__name__)


class MeshEventService:
    """Service for handling mesh events"""

    def __init__(
        self,
        source: EventSource,
        store: EventStore,
        publisher: EventPublisher,
        state_projection: StateProjection | None = None,
    ) -> None:
        self._source = source
        self._store = store
        self._publisher = publisher
        self._state_projection = state_projection

    async def run(self) -> None:
        try:
            async for event in self._source.events():
                try:
                    await self._store.append(event)
                    if self._state_projection:
                        await self._state_projection.project(event)
                    await self._publisher.publish(event)
                except Exception as e:
                    logger.error(f"Error processing event {event.event_id.value}: {e}")
        except asyncio.CancelledError:
            logger.info("MeshEventService shutdown requested")
            raise
        except Exception as e:
            logger.error(f"Fatal error in MeshEventService: {e}")
            raise
