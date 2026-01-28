"""Storage for artifacts"""

from datetime import datetime
from typing import AsyncIterator, Optional
from uuid import UUID

from meshcore.domain.models import MeshEvent


class InMemoryEventStore:
    """In-memory event storage implementing EventStore protocol"""

    def __init__(self) -> None:
        self._events: list[MeshEvent] = []
        self._event_ids: set[UUID] = set()

    async def append(self, event: MeshEvent) -> bool:
        """Append event to store

        Returns:
            True if event was inserted, False if duplicate
        """
        event_id = event.event_id.value
        if event_id in self._event_ids:
            return False

        self._events.append(event)
        self._event_ids.add(event_id)
        return True

    async def replay(
        self,
        since: Optional[datetime],
        until: Optional[datetime],
    ) -> AsyncIterator[MeshEvent]:
        """Replay events with optional time filtering"""
        for event in self._events:
            if since and event.timestamp < since:
                continue
            if until and event.timestamp > until:
                continue
            yield event

    async def event_exists(self, event_id: UUID) -> bool:
        """Check if event already exists"""
        return event_id in self._event_ids

    async def close(self) -> None:
        """Close the store (no-op for in-memory store)"""
        pass
