"""Models for the app"""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class EventId(BaseModel):
    """Model for an event ID"""

    value: UUID = Field(default_factory=uuid4)


class NodeId(BaseModel):
    """Model for a node ID"""

    value: str


class MeshEvent(BaseModel):
    """Model for a mesh event"""

    event_id: EventId
    node_id: NodeId
    event_type: str
    timestamp: datetime
    ingested_at: datetime
    payload: dict[str, Any]
    provenance: dict[str, Any]


class NodeState(BaseModel):
    """Aggregate state for a node"""

    node_id: NodeId
    last_seen: datetime
    first_seen: datetime
    event_count: int = 0
    last_telemetry: dict[str, Any] | None = None
    last_position: dict[str, Any] | None = None
    last_text: str | None = None
