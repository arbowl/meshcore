"""Interfaces for the app"""

from dataclasses import dataclass
from datetime import datetime
from typing import AsyncIterator, Optional, Protocol

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
    """Interface for an event store"""

    async def append(self, event: MeshEvent) -> None: ...
    async def replay(
        self, since: Optional[datetime], until: Optional[datetime]
    ) -> AsyncIterator[MeshEvent]: ...


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
    async def get_node(self, node_id: NodeId) -> NodeState | None: ...
    async def list_nodes(self) -> list[NodeState]: ...
    async def delete_node(self, node_id: NodeId) -> None: ...
