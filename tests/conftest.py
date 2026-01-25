import pytest
import tempfile
import os
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock
from meshcore.domain.events import (
    MeshEvent,
    NodeDiscovered,
    MessageReceived,
    TelemetryReceived,
    PositionUpdate
)
from meshcore.domain.state import NodeState


@pytest.fixture
def temp_db_path():
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
        db_path = f.name
    yield db_path
    try:
        os.unlink(db_path)
    except FileNotFoundError:
        pass


@pytest.fixture
def sample_timestamp():
    return datetime(2026, 1, 24, 12, 0, 0)


@pytest.fixture
def node_id():
    return "!abcd1234"


@pytest.fixture
def node_discovered_event(node_id, sample_timestamp):
    return NodeDiscovered(
        timestamp=sample_timestamp,
        node_id=node_id,
        long_name="Test Node",
        short_name="TN",
        hardware_model="TBEAM",
        role="ROUTER"
    )


@pytest.fixture
def message_received_event(node_id, sample_timestamp):
    return MessageReceived(
        timestamp=sample_timestamp,
        from_id=node_id,
        to_id="!ffff1111",
        text="Hello World",
        channel=0,
        packet_id=12345,
        hop_limit=3,
        want_ack=False
    )


@pytest.fixture
def telemetry_received_event(node_id, sample_timestamp):
    return TelemetryReceived(
        timestamp=sample_timestamp,
        node_id=node_id,
        battery_level=85,
        voltage=4.2,
        channel_utilization=15.5,
        air_util_tx=5.2
    )


@pytest.fixture
def position_update_event(node_id, sample_timestamp):
    return PositionUpdate(
        timestamp=sample_timestamp,
        node_id=node_id,
        latitude=37.7749,
        longitude=-122.4194,
        altitude=100,
        precision_bits=32
    )


@pytest.fixture
def sample_node_state(node_id, sample_timestamp):
    return NodeState(
        node_id=node_id,
        long_name="Test Node",
        short_name="TN",
        hardware_model="TBEAM",
        role="ROUTER",
        first_seen=sample_timestamp,
        last_seen=sample_timestamp
    )


@pytest.fixture
def mock_event_store():
    mock = Mock()
    mock.append.return_value = None
    mock.get_all.return_value = []
    mock.get_by_node.return_value = []
    return mock


@pytest.fixture
def mock_state_store():
    mock = Mock()
    mock.save.return_value = None
    mock.get.return_value = None
    mock.get_all.return_value = []
    return mock


@pytest.fixture
def mock_mqtt_client():
    mock = Mock()
    mock.connect.return_value = None
    mock.publish.return_value = Mock(rc=0)
    mock.loop_start.return_value = None
    mock.loop_stop.return_value = None
    return mock

