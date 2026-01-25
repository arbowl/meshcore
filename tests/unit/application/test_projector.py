import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock
from meshcore.application.state_projection import StateProjection
from tests.fixtures.factories import EventFactory, StateFactory


@pytest.mark.asyncio
async def test_projection_creates_state_from_event(mock_state_store):
    projection = StateProjection(mock_state_store)
    mock_state_store.get_node = AsyncMock(return_value=None)
    mock_state_store.upsert_node = AsyncMock()
    event = EventFactory.telemetry_event(node_id="!test")
    await projection.project(event)
    mock_state_store.upsert_node.assert_called_once()
    saved_state = mock_state_store.upsert_node.call_args[0][0]
    assert saved_state.node_id.value == "!test"


@pytest.mark.asyncio
async def test_projection_updates_existing_state_with_telemetry(mock_state_store):
    projection = StateProjection(mock_state_store)
    existing_state = StateFactory.node_state(node_id="!test")
    mock_state_store.get_node = AsyncMock(return_value=existing_state)
    mock_state_store.upsert_node = AsyncMock()
    event = EventFactory.telemetry_event(node_id="!test", battery_level=75)
    await projection.project(event)
    mock_state_store.upsert_node.assert_called_once()
    saved_state = mock_state_store.upsert_node.call_args[0][0]
    assert saved_state.last_telemetry["battery_level"] == 75


@pytest.mark.asyncio
async def test_projection_updates_position(mock_state_store):
    projection = StateProjection(mock_state_store)
    existing_state = StateFactory.node_state(node_id="!test")
    mock_state_store.get_node = AsyncMock(return_value=existing_state)
    mock_state_store.upsert_node = AsyncMock()
    event = EventFactory.position_event(
        node_id="!test",
        latitude=40.7128,
        longitude=-74.0060
    )
    await projection.project(event)
    mock_state_store.upsert_node.assert_called_once()
    saved_state = mock_state_store.upsert_node.call_args[0][0]
    assert saved_state.last_position["latitude"] == 40.7128
    assert saved_state.last_position["longitude"] == -74.0060


@pytest.mark.asyncio
async def test_projection_updates_last_seen(mock_state_store):
    projection = StateProjection(mock_state_store)
    old_time = datetime.now() - timedelta(hours=1)
    existing_state = StateFactory.node_state(node_id="!test", last_seen=old_time)
    mock_state_store.get_node = AsyncMock(return_value=existing_state)
    mock_state_store.upsert_node = AsyncMock()
    new_time = datetime.now()
    event = EventFactory.telemetry_event(node_id="!test", timestamp=new_time)
    await projection.project(event)
    saved_state = mock_state_store.upsert_node.call_args[0][0]
    assert saved_state.last_seen == new_time


@pytest.mark.asyncio
async def test_projection_increments_event_count(mock_state_store):
    projection = StateProjection(mock_state_store)
    existing_state = StateFactory.node_state(node_id="!test", event_count=5)
    mock_state_store.get_node = AsyncMock(return_value=existing_state)
    mock_state_store.upsert_node = AsyncMock()
    event = EventFactory.telemetry_event(node_id="!test")
    await projection.project(event)
    saved_state = mock_state_store.upsert_node.call_args[0][0]
    assert saved_state.event_count == 6

