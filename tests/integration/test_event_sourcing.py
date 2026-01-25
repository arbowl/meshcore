import pytest
from datetime import datetime
from meshcore.adapters.storage.sqlite import SQLiteEventStore, SQLiteStateStore
from meshcore.application.projector import NodeStateProjection
from tests.fixtures.factories import EventFactory, create_event_sequence


def test_event_sourcing_flow(temp_db_path):
    event_store = SQLiteEventStore(temp_db_path)
    state_store = SQLiteStateStore(temp_db_path)
    projection = NodeStateProjection(state_store)
    node_id = "!test1234"
    discover_event = EventFactory.node_discovered(node_id=node_id)
    event_store.append(discover_event)
    projection.handle_event(discover_event)
    state = state_store.get(node_id)
    assert state is not None
    assert state.node_id == node_id
    telemetry_event = EventFactory.telemetry_received(
        node_id=node_id,
        battery_level=85
    )
    event_store.append(telemetry_event)
    projection.handle_event(telemetry_event)
    updated_state = state_store.get(node_id)
    assert updated_state.battery_level == 85
    all_events = event_store.get_by_node(node_id)
    assert len(all_events) == 2


def test_multiple_nodes_flow(temp_db_path):
    event_store = SQLiteEventStore(temp_db_path)
    state_store = SQLiteStateStore(temp_db_path)
    projection = NodeStateProjection(state_store)
    for i in range(3):
        node_id = f"!node{i}"
        event = EventFactory.node_discovered(
            node_id=node_id,
            long_name=f"Node {i}"
        )
        event_store.append(event)
        projection.handle_event(event)
    states = state_store.get_all()
    assert len(states) == 3


def test_telemetry_time_series(temp_db_path):
    event_store = SQLiteEventStore(temp_db_path)
    node_id = "!test"
    events = create_event_sequence(node_id, count=5)
    for event in events:
        event_store.append(event)
    telemetry = event_store.get_telemetry_series(node_id, hours=24)
    assert len(telemetry) == 5


def test_message_search_integration(temp_db_path):
    event_store = SQLiteEventStore(temp_db_path)
    messages = [
        EventFactory.message_received(text="Test message one"),
        EventFactory.message_received(text="Another test message"),
        EventFactory.message_received(text="Something else")
    ]
    for msg in messages:
        event_store.append(msg)
    results = event_store.search_messages("test")
    assert len(results) == 2


def test_state_persistence(temp_db_path):
    state_store = SQLiteStateStore(temp_db_path)
    state = EventFactory.node_discovered(node_id="!persist")
    initial_state = SQLiteStateStore(temp_db_path).get("!persist")
    state_obj = EventFactory.node_discovered(node_id="!persist")
    projection = NodeStateProjection(state_store)
    projection.handle_event(state_obj)
    new_store = SQLiteStateStore(temp_db_path)
    retrieved = new_store.get("!persist")
    assert retrieved is not None
    assert retrieved.node_id == "!persist"

