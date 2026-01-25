"""Storage for artifacts"""

from datetime import datetime
from typing import AsyncIterator, Optional
from meshcore.domain.models import MeshEvent


class InMemoryEventStore:
    """In-memory event storage"""

    def __init__(self) -> None:
        self._events: list[MeshEvent] = []

    async def append(self, event: MeshEvent) -> None:
        self._events.append(event)

    async def replay(
        self,
        since: Optional[datetime],
        until: Optional[datetime],
    ) -> AsyncIterator[MeshEvent]:
        for event in self._events:
            if since and event.timestamp < since:
                continue
            if until and event.timestamp > until:
                continue
            yield event
