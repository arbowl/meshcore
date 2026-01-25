"""Message query service"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from meshcore.adapters.storage.sqlite import SqliteEventStore
from meshcore.domain.models import MeshEvent


class Message:
    """Message view model"""

    def __init__(self, event: MeshEvent):
        self.id = event.event_id.value
        self.from_node = event.node_id.value
        self.text = event.payload.get("text", "")
        self.timestamp = event.timestamp
        self.to_node = event.payload.get("to", None)
        self.channel = event.payload.get("channel", 0)
        self.encrypted = event.payload.get("encrypted", False)


class MessageQueryService:
    """Query and filter messages from event store"""

    def __init__(self, event_store: SqliteEventStore):
        self._event_store = event_store

    async def get_recent_messages(
        self,
        limit: int = 100,
        since: Optional[datetime] = None,
    ) -> list[Message]:
        """Get recent text messages"""
        if since is None:
            since = datetime.now(timezone.utc) - timedelta(days=7)

        events = await self._event_store.query_by_type(
            event_type="text",
            since=since,
            limit=limit,
        )
        return [Message(event) for event in events]

    async def get_messages_by_node(
        self,
        node_id: str,
        limit: int = 100,
    ) -> list[Message]:
        """Get messages from a specific node"""
        since = datetime.now(timezone.utc) - timedelta(days=30)
        events = await self._event_store.query_by_type(
            event_type="text",
            node_id=node_id,
            since=since,
            limit=limit,
        )
        return [Message(event) for event in events]

    async def search_messages(
        self,
        query: str,
        limit: int = 100,
    ) -> list[Message]:
        """Search messages by text content"""
        events = await self._event_store.search_messages(query, limit)
        return [Message(event) for event in events]

    async def get_conversation(
        self,
        node_a: str,
        node_b: str,
        limit: int = 100,
    ) -> list[Message]:
        """Get messages between two nodes"""
        # Get messages from both nodes
        since = datetime.now(timezone.utc) - timedelta(days=30)
        events_a = await self._event_store.query_by_type(
            event_type="text",
            node_id=node_a,
            since=since,
            limit=limit,
        )
        events_b = await self._event_store.query_by_type(
            event_type="text",
            node_id=node_b,
            since=since,
            limit=limit,
        )

        # Combine and sort by timestamp
        all_events = events_a + events_b
        all_events.sort(key=lambda e: e.timestamp, reverse=True)

        return [Message(event) for event in all_events[:limit]]
