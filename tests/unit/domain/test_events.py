import pytest
from datetime import datetime
from meshcore.domain.events import (
    NodeDiscovered,
    MessageReceived,
    TelemetryReceived,
    PositionUpdate
)


def test_node_discovered_creation(node_discovered_event):
    assert node_discovered_event.node_id == "!abcd1234"
    assert node_discovered_event.long_name == "Test Node"
    assert node_discovered_event.short_name == "TN"
    assert node_discovered_event.hardware_model == "TBEAM"
    assert node_discovered_event.role == "ROUTER"


def test_node_discovered_serialization(node_discovered_event):
    data = node_discovered_event.model_dump()
    assert data["node_id"] == "!abcd1234"
    assert data["event_type"] == "NODE_DISCOVERED"
    reconstructed = NodeDiscovered(**data)
    assert reconstructed.node_id == node_discovered_event.node_id


def test_message_received_creation(message_received_event):
    assert message_received_event.from_id == "!abcd1234"
    assert message_received_event.to_id == "!ffff1111"
    assert message_received_event.text == "Hello World"
    assert message_received_event.channel == 0


def test_message_received_serialization(message_received_event):
    data = message_received_event.model_dump()
    assert data["event_type"] == "MESSAGE_RECEIVED"
    reconstructed = MessageReceived(**data)
    assert reconstructed.text == message_received_event.text


def test_telemetry_received_creation(telemetry_received_event):
    assert telemetry_received_event.node_id == "!abcd1234"
    assert telemetry_received_event.battery_level == 85
    assert telemetry_received_event.voltage == 4.2
    assert telemetry_received_event.channel_utilization == 15.5


def test_telemetry_received_optional_fields():
    event = TelemetryReceived(
        timestamp=datetime.now(),
        node_id="!test",
        battery_level=None,
        voltage=None,
        channel_utilization=None,
        air_util_tx=None
    )
    assert event.battery_level is None
    assert event.voltage is None


def test_position_update_creation(position_update_event):
    assert position_update_event.node_id == "!abcd1234"
    assert position_update_event.latitude == 37.7749
    assert position_update_event.longitude == -122.4194
    assert position_update_event.altitude == 100


def test_position_update_optional_altitude():
    event = PositionUpdate(
        timestamp=datetime.now(),
        node_id="!test",
        latitude=0.0,
        longitude=0.0,
        altitude=None,
        precision_bits=32
    )
    assert event.altitude is None

