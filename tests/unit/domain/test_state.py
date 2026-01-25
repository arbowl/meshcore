import pytest
from datetime import datetime, timedelta
from meshcore.domain.state import NodeState


def test_node_state_creation(sample_node_state):
    assert sample_node_state.node_id == "!abcd1234"
    assert sample_node_state.long_name == "Test Node"
    assert sample_node_state.short_name == "TN"
    assert sample_node_state.hardware_model == "TBEAM"


def test_node_state_optional_fields():
    state = NodeState(
        node_id="!test",
        long_name="Test",
        short_name="T",
        hardware_model="UNKNOWN",
        role="CLIENT",
        first_seen=datetime.now(),
        last_seen=datetime.now()
    )
    assert state.battery_level is None
    assert state.latitude is None
    assert state.longitude is None


def test_node_state_with_position():
    state = NodeState(
        node_id="!test",
        long_name="Test",
        short_name="T",
        hardware_model="TBEAM",
        role="CLIENT",
        first_seen=datetime.now(),
        last_seen=datetime.now(),
        latitude=37.7749,
        longitude=-122.4194,
        altitude=100
    )
    assert state.latitude == 37.7749
    assert state.longitude == -122.4194
    assert state.altitude == 100


def test_node_state_with_telemetry():
    state = NodeState(
        node_id="!test",
        long_name="Test",
        short_name="T",
        hardware_model="TBEAM",
        role="CLIENT",
        first_seen=datetime.now(),
        last_seen=datetime.now(),
        battery_level=85,
        voltage=4.2,
        channel_utilization=15.5
    )
    assert state.battery_level == 85
    assert state.voltage == 4.2
    assert state.channel_utilization == 15.5


def test_node_state_serialization(sample_node_state):
    data = sample_node_state.model_dump()
    assert data["node_id"] == "!abcd1234"
    reconstructed = NodeState(**data)
    assert reconstructed.node_id == sample_node_state.node_id

