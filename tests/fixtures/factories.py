from datetime import datetime, timedelta
from typing import Optional, Any
from meshcore.domain.models import MeshEvent, NodeState, EventId, NodeId


class EventFactory:
    @staticmethod
    def mesh_event(
        node_id: str = "!test1234",
        event_type: str = "telemetry",
        payload: Optional[dict[str, Any]] = None,
        timestamp: Optional[datetime] = None
    ) -> MeshEvent:
        return MeshEvent(
            event_id=EventId(),
            node_id=NodeId(value=node_id),
            event_type=event_type,
            timestamp=timestamp or datetime.now(),
            ingested_at=timestamp or datetime.now(),
            payload=payload or {},
            provenance={"source": "test"}
        )
    @staticmethod
    def telemetry_event(
        node_id: str = "!node1234",
        battery_level: Optional[int] = 85,
        voltage: Optional[float] = 4.2,
        channel_utilization: Optional[float] = 15.5,
        timestamp: Optional[datetime] = None
    ) -> MeshEvent:
        payload = {}
        if battery_level is not None:
            payload["battery_level"] = battery_level
        if voltage is not None:
            payload["voltage"] = voltage
        if channel_utilization is not None:
            payload["channel_utilization"] = channel_utilization
        return EventFactory.mesh_event(
            node_id=node_id,
            event_type="telemetry",
            payload=payload,
            timestamp=timestamp
        )
    @staticmethod
    def text_event(
        node_id: str = "!from1234",
        text: str = "Test message",
        from_id: Optional[str] = None,
        to_id: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ) -> MeshEvent:
        payload = {"text": text}
        if from_id:
            payload["from_id"] = from_id
        if to_id:
            payload["to_id"] = to_id
        return EventFactory.mesh_event(
            node_id=node_id,
            event_type="text",
            payload=payload,
            timestamp=timestamp
        )
    @staticmethod
    def position_event(
        node_id: str = "!node1234",
        latitude: float = 37.7749,
        longitude: float = -122.4194,
        altitude: Optional[int] = 100,
        timestamp: Optional[datetime] = None
    ) -> MeshEvent:
        payload = {
            "latitude": latitude,
            "longitude": longitude
        }
        if altitude is not None:
            payload["altitude"] = altitude
        return EventFactory.mesh_event(
            node_id=node_id,
            event_type="position",
            payload=payload,
            timestamp=timestamp
        )


class StateFactory:
    @staticmethod
    def node_state(
        node_id: str = "!node1234",
        first_seen: Optional[datetime] = None,
        last_seen: Optional[datetime] = None,
        event_count: int = 0,
        last_telemetry: Optional[dict[str, Any]] = None,
        last_position: Optional[dict[str, Any]] = None,
        last_text: Optional[str] = None
    ) -> NodeState:
        now = datetime.now()
        return NodeState(
            node_id=NodeId(value=node_id),
            first_seen=first_seen or now,
            last_seen=last_seen or now,
            event_count=event_count,
            last_telemetry=last_telemetry,
            last_position=last_position,
            last_text=last_text
        )


def create_event_sequence(node_id: str, count: int = 5):
    base_time = datetime.now()
    events = []
    for i in range(count):
        timestamp = base_time + timedelta(minutes=i)
        events.append(EventFactory.telemetry_event(
            node_id=node_id,
            battery_level=85 - i,
            timestamp=timestamp
        ))
    return events

