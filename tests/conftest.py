import pytest
import tempfile
import os
from datetime import datetime
from unittest.mock import Mock
from meshcore.domain.models import MeshEvent, NodeState, EventId, NodeId


@pytest.fixture
def temp_db_path():
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    yield db_path
    try:
        os.unlink(db_path)
    except (FileNotFoundError, PermissionError):
        pass
    for suffix in ['-wal', '-shm']:
        try:
            os.unlink(db_path + suffix)
        except (FileNotFoundError, PermissionError):
            pass


@pytest.fixture
def sample_timestamp():
    return datetime(2026, 1, 24, 12, 0, 0)


@pytest.fixture
def node_id():
    return NodeId(value="!abcd1234")


@pytest.fixture
def mesh_event_telemetry(node_id, sample_timestamp):
    return MeshEvent(
        event_id=EventId(),
        node_id=node_id,
        event_type="telemetry",
        timestamp=sample_timestamp,
        ingested_at=sample_timestamp,
        payload={
            "battery_level": 85,
            "voltage": 4.2,
            "channel_utilization": 15.5
        },
        provenance={"source": "test"}
    )


@pytest.fixture
def mesh_event_message(node_id, sample_timestamp):
    return MeshEvent(
        event_id=EventId(),
        node_id=node_id,
        event_type="text",
        timestamp=sample_timestamp,
        ingested_at=sample_timestamp,
        payload={
            "text": "Hello World",
            "from_id": "!abcd1234",
            "to_id": "!ffff1111"
        },
        provenance={"source": "test"}
    )


@pytest.fixture
def mesh_event_position(node_id, sample_timestamp):
    return MeshEvent(
        event_id=EventId(),
        node_id=node_id,
        event_type="position",
        timestamp=sample_timestamp,
        ingested_at=sample_timestamp,
        payload={
            "latitude": 37.7749,
            "longitude": -122.4194,
            "altitude": 100
        },
        provenance={"source": "test"}
    )


@pytest.fixture
def sample_node_state(node_id, sample_timestamp):
    return NodeState(
        node_id=node_id,
        first_seen=sample_timestamp,
        last_seen=sample_timestamp,
        event_count=1
    )


@pytest.fixture
def mock_event_store():
    from unittest.mock import AsyncMock
    mock = Mock()
    mock.append = AsyncMock(return_value=None)
    mock.get_all = AsyncMock(return_value=[])
    return mock


@pytest.fixture
def mock_state_store():
    from unittest.mock import AsyncMock
    mock = Mock()
    mock.upsert_node = AsyncMock(return_value=None)
    mock.get_node = AsyncMock(return_value=None)
    mock.get_all_nodes = AsyncMock(return_value=[])
    return mock


@pytest.fixture
def mock_mqtt_client():
    mock = Mock()
    mock.connect.return_value = None
    mock.publish.return_value = Mock(rc=0)
    mock.loop_start.return_value = None
    mock.loop_stop.return_value = None
    return mock
