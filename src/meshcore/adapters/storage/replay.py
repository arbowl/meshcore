"""Replay module"""

from datetime import datetime
from typing import AsyncIterator, Optional

from meshcore.application.ports import EventSource
from meshcore.domain.models import MeshEvent


class ReplayEventSource(EventSource):
    """Replay event source from a list of MeshEvents"""

    def __init__(
        self,
        store,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
    ) -> None:
        self._store = store
        self._since = since
        self._until = until

    async def events(self) -> AsyncIterator[MeshEvent]:
        """Async iterator of MeshEvents from the replay source"""
        async for event in self._store.replay(self._since, self._until):
            yield event
