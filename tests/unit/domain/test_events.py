import pytest
from datetime import datetime
from meshcore.domain.models import MeshEvent, EventId, NodeId


def test_mesh_event_creation():
    event = MeshEvent(
        event_id=EventId(),
        node_id=NodeId(value="!test1234"),
        event_type="telemetry",
        timestamp=datetime.now(),
        ingested_at=datetime.now(),
        payload={"battery_level": 85},
        provenance={"source": "test"}
    )
    assert event.node_id.value == "!test1234"
    assert event.event_type == "telemetry"
    assert event.payload["battery_level"] == 85


def test_mesh_event_serialization():
    event = MeshEvent(
        event_id=EventId(),
        node_id=NodeId(value="!test"),
        event_type="text",
        timestamp=datetime.now(),
        ingested_at=datetime.now(),
        payload={"text": "Hello"},
        provenance={}
    )
    data = event.model_dump()
    assert data["event_type"] == "text"
    assert data["payload"]["text"] == "Hello"


def test_telemetry_event(mesh_event_telemetry):
    assert mesh_event_telemetry.event_type == "telemetry"
    assert mesh_event_telemetry.payload["battery_level"] == 85
    assert mesh_event_telemetry.payload["voltage"] == 4.2


def test_text_event(mesh_event_message):
    assert mesh_event_message.event_type == "text"
    assert mesh_event_message.payload["text"] == "Hello World"


def test_position_event(mesh_event_position):
    assert mesh_event_position.event_type == "position"
    assert mesh_event_position.payload["latitude"] == 37.7749
    assert mesh_event_position.payload["longitude"] == -122.4194


def test_event_id_uniqueness():
    id1 = EventId()
    id2 = EventId()
    assert id1.value != id2.value


def test_node_id_equality():
    id1 = NodeId(value="!test")
    id2 = NodeId(value="!test")
    assert id1.value == id2.value

