import pytest
from datetime import datetime, timedelta
from meshcore.application.message_service import MessageQueryService, Message
from tests.fixtures.factories import EventFactory


def test_message_query_service_initialization(mock_event_store):
    service = MessageQueryService(mock_event_store)
    assert service.event_store == mock_event_store


def test_get_recent_messages_returns_sorted_list(mock_event_store):
    messages = [
        EventFactory.message_received(text="First", timestamp=datetime.now() - timedelta(minutes=3)),
        EventFactory.message_received(text="Second", timestamp=datetime.now() - timedelta(minutes=2)),
        EventFactory.message_received(text="Third", timestamp=datetime.now() - timedelta(minutes=1))
    ]
    mock_event_store.query_by_type.return_value = messages
    service = MessageQueryService(mock_event_store)
    results = service.get_recent_messages(limit=10)
    assert len(results) == 3
    assert results[0].text == "Third"
    assert results[-1].text == "First"


def test_get_recent_messages_respects_limit(mock_event_store):
    messages = [
        EventFactory.message_received(text=f"Message {i}")
        for i in range(10)
    ]
    mock_event_store.query_by_type.return_value = messages
    service = MessageQueryService(mock_event_store)
    results = service.get_recent_messages(limit=5)
    assert len(results) == 5


def test_get_messages_by_node_filters_correctly(mock_event_store):
    messages = [
        EventFactory.message_received(from_id="!node1", text="From node1"),
        EventFactory.message_received(to_id="!node1", text="To node1"),
        EventFactory.message_received(from_id="!node2", text="From node2")
    ]
    mock_event_store.query_by_type.return_value = messages
    service = MessageQueryService(mock_event_store)
    results = service.get_messages_by_node("!node1")
    assert len(results) == 2


def test_search_messages_filters_text(mock_event_store):
    messages = [
        EventFactory.message_received(text="Hello world"),
        EventFactory.message_received(text="Goodbye world"),
        EventFactory.message_received(text="Random text")
    ]
    mock_event_store.query_by_type.return_value = messages
    service = MessageQueryService(mock_event_store)
    results = service.search_messages("world")
    assert len(results) == 2


def test_get_conversation_returns_bidirectional_messages(mock_event_store):
    node1 = "!node1"
    node2 = "!node2"
    messages = [
        EventFactory.message_received(from_id=node1, to_id=node2, text="Hi"),
        EventFactory.message_received(from_id=node2, to_id=node1, text="Hello"),
        EventFactory.message_received(from_id="!node3", to_id=node1, text="Other")
    ]
    mock_event_store.query_by_type.return_value = messages
    service = MessageQueryService(mock_event_store)
    results = service.get_conversation(node1, node2)
    assert len(results) == 2

