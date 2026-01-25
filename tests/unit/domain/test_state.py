import pytest
from datetime import datetime, timedelta
from meshcore.domain.models import NodeState, NodeId


def test_node_state_creation(sample_node_state):
    assert sample_node_state.node_id.value == "!abcd1234"
    assert sample_node_state.event_count == 1


def test_node_state_optional_fields():
    state = NodeState(
        node_id=NodeId(value="!test"),
        first_seen=datetime.now(),
        last_seen=datetime.now(),
        event_count=0
    )
    assert state.last_telemetry is None
    assert state.last_position is None
    assert state.last_text is None


def test_node_state_with_telemetry():
    state = NodeState(
        node_id=NodeId(value="!test"),
        first_seen=datetime.now(),
        last_seen=datetime.now(),
        event_count=1,
        last_telemetry={
            "battery_level": 85,
            "voltage": 4.2
        }
    )
    assert state.last_telemetry["battery_level"] == 85
    assert state.last_telemetry["voltage"] == 4.2


def test_node_state_with_position():
    state = NodeState(
        node_id=NodeId(value="!test"),
        first_seen=datetime.now(),
        last_seen=datetime.now(),
        event_count=1,
        last_position={
            "latitude": 37.7749,
            "longitude": -122.4194,
            "altitude": 100
        }
    )
    assert state.last_position["latitude"] == 37.7749
    assert state.last_position["longitude"] == -122.4194


def test_node_state_with_text():
    state = NodeState(
        node_id=NodeId(value="!test"),
        first_seen=datetime.now(),
        last_seen=datetime.now(),
        event_count=1,
        last_text="Hello World"
    )
    assert state.last_text == "Hello World"


def test_node_state_serialization(sample_node_state):
    data = sample_node_state.model_dump()
    assert data["node_id"]["value"] == "!abcd1234"
    reconstructed = NodeState(**data)
    assert reconstructed.node_id.value == sample_node_state.node_id.value

