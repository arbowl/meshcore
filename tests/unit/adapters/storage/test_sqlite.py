import pytest
from datetime import datetime, timedelta
from meshcore.adapters.storage.sqlite import SqliteEventStore
from meshcore.adapters.storage.state_sqlite import SqliteStateStore
from meshcore.domain.models import NodeId
from tests.fixtures.factories import EventFactory, StateFactory


@pytest.mark.asyncio
async def test_event_store_initialization(temp_db_path):
    store = SqliteEventStore(temp_db_path)
    assert store is not None
    store._conn.close()


@pytest.mark.asyncio
async def test_event_store_append_and_replay(temp_db_path):
    store = SqliteEventStore(temp_db_path)
    event = EventFactory.telemetry_event(node_id="!test")
    await store.append(event)
    events = []
    async for e in store.replay(since=None, until=None):
        events.append(e)
    assert len(events) == 1
    assert events[0].node_id.value == "!test"
    store._conn.close()


@pytest.mark.asyncio
async def test_event_store_multiple_events(temp_db_path):
    store = SqliteEventStore(temp_db_path)
    await store.append(EventFactory.telemetry_event(node_id="!node1"))
    await store.append(EventFactory.text_event(node_id="!node1"))
    await store.append(EventFactory.telemetry_event(node_id="!node2"))
    events = []
    async for e in store.replay(since=None, until=None):
        events.append(e)
    assert len(events) == 3
    store._conn.close()


@pytest.mark.asyncio
async def test_event_store_time_filtering(temp_db_path):
    store = SqliteEventStore(temp_db_path)
    now = datetime.now()
    await store.append(EventFactory.telemetry_event(
        node_id="!test",
        timestamp=now - timedelta(hours=2)
    ))
    await store.append(EventFactory.telemetry_event(
        node_id="!test",
        timestamp=now - timedelta(hours=1)
    ))
    since = now - timedelta(hours=1, minutes=30)
    events = []
    async for e in store.replay(since=since, until=None):
        events.append(e)
    assert len(events) == 1
    store._conn.close()


@pytest.mark.asyncio
async def test_state_store_initialization(temp_db_path):
    store = SqliteStateStore(temp_db_path)
    assert store is not None
    store._conn.close()


@pytest.mark.asyncio
async def test_state_store_upsert_and_get(temp_db_path):
    store = SqliteStateStore(temp_db_path)
    state = StateFactory.node_state(node_id="!test")
    await store.upsert_node(state)
    retrieved = await store.get_node(NodeId(value="!test"))
    assert retrieved is not None
    assert retrieved.node_id.value == "!test"
    store._conn.close()


@pytest.mark.asyncio
async def test_state_store_list_nodes(temp_db_path):
    store = SqliteStateStore(temp_db_path)
    await store.upsert_node(StateFactory.node_state(node_id="!node1"))
    await store.upsert_node(StateFactory.node_state(node_id="!node2"))
    states = await store.list_nodes()
    assert len(states) == 2
    store._conn.close()


@pytest.mark.asyncio
async def test_state_store_update_existing(temp_db_path):
    store = SqliteStateStore(temp_db_path)
    state = StateFactory.node_state(
        node_id="!test",
        last_telemetry={"battery_level": 85}
    )
    await store.upsert_node(state)
    state = state.model_copy(update={
        "last_telemetry": {"battery_level": 75}
    })
    await store.upsert_node(state)
    retrieved = await store.get_node(NodeId(value="!test"))
    assert retrieved.last_telemetry["battery_level"] == 75
    store._conn.close()


@pytest.mark.asyncio
async def test_state_store_delete_node(temp_db_path):
    store = SqliteStateStore(temp_db_path)
    state = StateFactory.node_state(node_id="!test")
    await store.upsert_node(state)
    await store.delete_node(NodeId(value="!test"))
    retrieved = await store.get_node(NodeId(value="!test"))
    assert retrieved is None
    store._conn.close()
