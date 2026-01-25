import pytest
from datetime import datetime, timedelta
from meshcore.adapters.storage.sqlite import SQLiteEventStore, SQLiteStateStore
from tests.fixtures.factories import EventFactory, StateFactory


def test_event_store_initialization(temp_db_path):
    store = SQLiteEventStore(temp_db_path)
    assert store.db_path == temp_db_path


def test_event_store_append_and_get_all(temp_db_path):
    store = SQLiteEventStore(temp_db_path)
    event = EventFactory.node_discovered(node_id="!test")
    store.append(event)
    events = store.get_all()
    assert len(events) == 1
    assert events[0].node_id == "!test"


def test_event_store_get_by_node(temp_db_path):
    store = SQLiteEventStore(temp_db_path)
    store.append(EventFactory.node_discovered(node_id="!node1"))
    store.append(EventFactory.telemetry_received(node_id="!node1"))
    store.append(EventFactory.telemetry_received(node_id="!node2"))
    events = store.get_by_node("!node1")
    assert len(events) == 2
    for event in events:
        assert event.node_id == "!node1"


def test_event_store_query_by_type(temp_db_path):
    store = SQLiteEventStore(temp_db_path)
    store.append(EventFactory.node_discovered(node_id="!node1"))
    store.append(EventFactory.message_received(from_id="!node1"))
    store.append(EventFactory.telemetry_received(node_id="!node1"))
    messages = store.query_by_type("MESSAGE_RECEIVED")
    assert len(messages) == 1
    assert messages[0].event_type == "MESSAGE_RECEIVED"


def test_event_store_get_telemetry_series(temp_db_path):
    store = SQLiteEventStore(temp_db_path)
    now = datetime.now()
    store.append(EventFactory.telemetry_received(
        node_id="!test",
        timestamp=now - timedelta(hours=2)
    ))
    store.append(EventFactory.telemetry_received(
        node_id="!test",
        timestamp=now - timedelta(hours=1)
    ))
    telemetry = store.get_telemetry_series("!test", hours=24)
    assert len(telemetry) == 2


def test_event_store_search_messages(temp_db_path):
    store = SQLiteEventStore(temp_db_path)
    store.append(EventFactory.message_received(text="Hello world"))
    store.append(EventFactory.message_received(text="Goodbye"))
    results = store.search_messages("Hello")
    assert len(results) == 1
    assert "Hello" in results[0].text


def test_state_store_initialization(temp_db_path):
    store = SQLiteStateStore(temp_db_path)
    assert store.db_path == temp_db_path


def test_state_store_save_and_get(temp_db_path):
    store = SQLiteStateStore(temp_db_path)
    state = StateFactory.node_state(node_id="!test")
    store.save(state)
    retrieved = store.get("!test")
    assert retrieved is not None
    assert retrieved.node_id == "!test"
    assert retrieved.long_name == state.long_name


def test_state_store_get_all(temp_db_path):
    store = SQLiteStateStore(temp_db_path)
    store.save(StateFactory.node_state(node_id="!node1"))
    store.save(StateFactory.node_state(node_id="!node2"))
    states = store.get_all()
    assert len(states) == 2


def test_state_store_update_existing(temp_db_path):
    store = SQLiteStateStore(temp_db_path)
    state = StateFactory.node_state(node_id="!test", battery_level=85)
    store.save(state)
    state.battery_level = 75
    store.save(state)
    retrieved = store.get("!test")
    assert retrieved.battery_level == 75


def test_state_store_get_nonexistent(temp_db_path):
    store = SQLiteStateStore(temp_db_path)
    retrieved = store.get("!nonexistent")
    assert retrieved is None

