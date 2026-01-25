import pytest
from datetime import datetime
from meshcore.adapters.storage.sqlite import SqliteEventStore
from meshcore.adapters.storage.state_sqlite import SqliteStateStore
from meshcore.application.state_projection import StateProjection
from meshcore.domain.models import NodeId
from tests.fixtures.factories import EventFactory, create_event_sequence


@pytest.mark.asyncio
async def test_event_sourcing_flow(temp_db_path):
    event_store = SqliteEventStore(temp_db_path)
    state_store = SqliteStateStore(temp_db_path)
    projection = StateProjection(state_store)
    node_id = "!test1234"
    telemetry_event = EventFactory.telemetry_event(
        node_id=node_id,
        battery_level=85
    )
    await event_store.append(telemetry_event)
    await projection.project(telemetry_event)
    state = await state_store.get_node(NodeId(value=node_id))
    assert state is not None
    assert state.node_id.value == node_id
    assert state.last_telemetry["battery_level"] == 85
    position_event = EventFactory.position_event(node_id=node_id)
    await event_store.append(position_event)
    await projection.project(position_event)
    updated_state = await state_store.get_node(NodeId(value=node_id))
    assert updated_state.last_position is not None
    events = []
    async for e in event_store.replay(since=None, until=None):
        events.append(e)
    assert len(events) == 2
    event_store._conn.close()
    state_store._conn.close()


@pytest.mark.asyncio
async def test_multiple_nodes_flow(temp_db_path):
    event_store = SqliteEventStore(temp_db_path)
    state_store = SqliteStateStore(temp_db_path)
    projection = StateProjection(state_store)
    for i in range(3):
        node_id = f"!node{i}"
        event = EventFactory.telemetry_event(node_id=node_id)
        await event_store.append(event)
        await projection.project(event)
    states = await state_store.list_nodes()
    assert len(states) == 3
    event_store._conn.close()
    state_store._conn.close()


@pytest.mark.asyncio
async def test_event_sequence(temp_db_path):
    event_store = SqliteEventStore(temp_db_path)
    node_id = "!test"
    events = create_event_sequence(node_id, count=5)
    for event in events:
        await event_store.append(event)
    all_events = []
    async for e in event_store.replay(since=None, until=None):
        all_events.append(e)
    assert len(all_events) == 5
    event_store._conn.close()


@pytest.mark.asyncio
async def test_state_persistence(temp_db_path):
    state_store = SqliteStateStore(temp_db_path)
    projection = StateProjection(state_store)
    event = EventFactory.telemetry_event(node_id="!persist")
    await projection.project(event)
    state_store._conn.close()
    new_store = SqliteStateStore(temp_db_path)
    retrieved = await new_store.get_node(NodeId(value="!persist"))
    assert retrieved is not None
    assert retrieved.node_id.value == "!persist"
    new_store._conn.close()

