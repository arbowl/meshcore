"""Interfaces for the app"""

from dataclasses import dataclass
from datetime import datetime
from typing import AsyncIterator, Optional, Protocol
from uuid import UUID

from meshcore.domain.models import MeshEvent, NodeId, NodeState


@dataclass
class CommandResult:
    """Result of a command execution"""

    success: bool
    message: str
    error: Optional[str] = None


class EventSource(Protocol):
    """Interface for an event source"""

    async def events(self) -> AsyncIterator[MeshEvent]:
        """Produces MeshEvents from some external system"""


class EventPublisher(Protocol):
    """Interface for an event publisher"""

    async def publish(self, event: MeshEvent) -> None: ...


class EventStore(Protocol):
    """Interface for an event store - basic append and replay"""

    async def append(self, event: MeshEvent) -> None: ...

    async def replay(
        self, since: Optional[datetime], until: Optional[datetime]
    ) -> AsyncIterator[MeshEvent]: ...

    async def event_exists(self, event_id: UUID) -> bool:
        """Check if an event already exists (for deduplication)"""

    async def close(self) -> None:
        """Close the store and cleanup resources"""


class EventQueryPort(Protocol):
    """Interface for querying events - separates writes from reads"""

    async def query_by_type(
        self,
        event_type: str,
        since: Optional[datetime] = None,
        node_id: Optional[str] = None,
        limit: int = 100,
    ) -> list[MeshEvent]:
        """Query events by type with optional filters"""

    async def get_telemetry_series(
        self,
        node_id: str,
        since: datetime,
        limit: int = 1000,
    ) -> list[MeshEvent]:
        """Get telemetry events for a node as time series"""

    async def search_messages(
        self,
        search_term: str,
        limit: int = 100,
    ) -> list[MeshEvent]:
        """Search text messages"""


class MeshInputPort(Protocol):
    """Interface for the mesh input port"""

    async def receive(self) -> AsyncIterator[MeshEvent]: ...


class MeshCommandPort(Protocol):
    """Interface for sending commands to the mesh network"""

    async def send_text(
        self,
        text: str,
        destination: Optional[str] = None,
        channel: int = 0,
    ) -> CommandResult:
        """Send text message to the mesh"""

    async def send_position(
        self,
        latitude: float,
        longitude: float,
        altitude: Optional[float] = None,
        destination: Optional[str] = None,
    ) -> CommandResult:
        """Send position update"""


class StateStore(Protocol):
    """Interface for storing and querying node state"""

    async def upsert_node(self, state: NodeState) -> None: ...
    async def get_node(self, node_id: NodeId) -> Optional[NodeState]: ...
    async def list_nodes(self) -> list[NodeState]: ...
    async def delete_node(self, node_id: NodeId) -> None: ...
    async def close(self) -> None: ...
