import pytest
from datetime import datetime, timedelta
from meshcore.application.projector import NodeStateProjection
from meshcore.domain.events import NodeDiscovered, TelemetryReceived, PositionUpdate
from tests.fixtures.factories import EventFactory, StateFactory


def test_projection_creates_state_from_node_discovered(mock_state_store):
    projection = NodeStateProjection(mock_state_store)
    event = EventFactory.node_discovered(node_id="!test", long_name="Test Node")
    projection.handle_event(event)
    mock_state_store.save.assert_called_once()
    saved_state = mock_state_store.save.call_args[0][0]
    assert saved_state.node_id == "!test"
    assert saved_state.long_name == "Test Node"


def test_projection_updates_existing_state_with_telemetry(mock_state_store):
    projection = NodeStateProjection(mock_state_store)
    existing_state = StateFactory.node_state(node_id="!test")
    mock_state_store.get.return_value = existing_state
    event = EventFactory.telemetry_received(node_id="!test", battery_level=75)
    projection.handle_event(event)
    mock_state_store.save.assert_called_once()
    saved_state = mock_state_store.save.call_args[0][0]
    assert saved_state.battery_level == 75


def test_projection_updates_position(mock_state_store):
    projection = NodeStateProjection(mock_state_store)
    existing_state = StateFactory.node_state(node_id="!test")
    mock_state_store.get.return_value = existing_state
    event = EventFactory.position_update(
        node_id="!test",
        latitude=40.7128,
        longitude=-74.0060
    )
    projection.handle_event(event)
    mock_state_store.save.assert_called_once()
    saved_state = mock_state_store.save.call_args[0][0]
    assert saved_state.latitude == 40.7128
    assert saved_state.longitude == -74.0060


def test_projection_updates_last_seen(mock_state_store):
    projection = NodeStateProjection(mock_state_store)
    old_time = datetime.now() - timedelta(hours=1)
    existing_state = StateFactory.node_state(node_id="!test", last_seen=old_time)
    mock_state_store.get.return_value = existing_state
    new_time = datetime.now()
    event = EventFactory.telemetry_received(node_id="!test", timestamp=new_time)
    projection.handle_event(event)
    saved_state = mock_state_store.save.call_args[0][0]
    assert saved_state.last_seen == new_time


def test_projection_creates_state_if_not_exists_on_telemetry(mock_state_store):
    projection = NodeStateProjection(mock_state_store)
    mock_state_store.get.return_value = None
    event = EventFactory.telemetry_received(node_id="!new")
    projection.handle_event(event)
    mock_state_store.save.assert_called_once()
    saved_state = mock_state_store.save.call_args[0][0]
    assert saved_state.node_id == "!new"

