import pytest
import json
from unittest.mock import Mock, patch
from meshcore.adapters.pubsub.mqtt import MQTTEventPublisher
from tests.fixtures.factories import EventFactory


def test_mqtt_publisher_initialization():
    publisher = MQTTEventPublisher(broker="localhost", port=1883, topic="test/topic")
    assert publisher.broker == "localhost"
    assert publisher.port == 1883
    assert publisher.topic == "test/topic"


def test_mqtt_publisher_connect(mock_mqtt_client):
    with patch('paho.mqtt.client.Client', return_value=mock_mqtt_client):
        publisher = MQTTEventPublisher()
        publisher.connect()
        mock_mqtt_client.connect.assert_called_once()
        mock_mqtt_client.loop_start.assert_called_once()


def test_mqtt_publisher_publish_event(mock_mqtt_client):
    with patch('paho.mqtt.client.Client', return_value=mock_mqtt_client):
        publisher = MQTTEventPublisher()
        publisher.connect()
        event = EventFactory.node_discovered(node_id="!test")
        publisher.publish(event)
        mock_mqtt_client.publish.assert_called_once()
        call_args = mock_mqtt_client.publish.call_args
        assert call_args[0][0] == "meshcore/events"
        payload = json.loads(call_args[0][1])
        assert payload["node_id"] == "!test"


def test_mqtt_publisher_disconnect(mock_mqtt_client):
    with patch('paho.mqtt.client.Client', return_value=mock_mqtt_client):
        publisher = MQTTEventPublisher()
        publisher.connect()
        publisher.disconnect()
        mock_mqtt_client.loop_stop.assert_called_once()


def test_mqtt_publisher_custom_topic(mock_mqtt_client):
    with patch('paho.mqtt.client.Client', return_value=mock_mqtt_client):
        publisher = MQTTEventPublisher(topic="custom/topic")
        publisher.connect()
        event = EventFactory.message_received()
        publisher.publish(event)
        call_args = mock_mqtt_client.publish.call_args
        assert call_args[0][0] == "custom/topic"


def test_mqtt_publisher_serializes_datetime(mock_mqtt_client):
    with patch('paho.mqtt.client.Client', return_value=mock_mqtt_client):
        publisher = MQTTEventPublisher()
        publisher.connect()
        event = EventFactory.telemetry_received()
        publisher.publish(event)
        call_args = mock_mqtt_client.publish.call_args
        payload = json.loads(call_args[0][1])
        assert "timestamp" in payload

