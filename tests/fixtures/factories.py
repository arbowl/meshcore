from datetime import datetime, timedelta
from typing import Optional
from meshcore.domain.events import (
    NodeDiscovered,
    MessageReceived,
    TelemetryReceived,
    PositionUpdate,
    NodeInfo
)
from meshcore.domain.state import NodeState


class EventFactory:
    @staticmethod
    def node_discovered(
        node_id: str = "!test1234",
        long_name: str = "Test Node",
        short_name: str = "TN",
        hardware_model: str = "TBEAM",
        role: str = "CLIENT",
        timestamp: Optional[datetime] = None
    ) -> NodeDiscovered:
        return NodeDiscovered(
            timestamp=timestamp or datetime.now(),
            node_id=node_id,
            long_name=long_name,
            short_name=short_name,
            hardware_model=hardware_model,
            role=role
        )
    @staticmethod
    def message_received(
        from_id: str = "!from1234",
        to_id: str = "!to5678",
        text: str = "Test message",
        channel: int = 0,
        packet_id: int = 12345,
        timestamp: Optional[datetime] = None,
        hop_limit: int = 3,
        want_ack: bool = False
    ) -> MessageReceived:
        return MessageReceived(
            timestamp=timestamp or datetime.now(),
            from_id=from_id,
            to_id=to_id,
            text=text,
            channel=channel,
            packet_id=packet_id,
            hop_limit=hop_limit,
            want_ack=want_ack
        )
    @staticmethod
    def telemetry_received(
        node_id: str = "!node1234",
        battery_level: Optional[int] = 85,
        voltage: Optional[float] = 4.2,
        channel_utilization: Optional[float] = 15.5,
        air_util_tx: Optional[float] = 5.2,
        temperature: Optional[float] = None,
        humidity: Optional[float] = None,
        pressure: Optional[float] = None,
        timestamp: Optional[datetime] = None
    ) -> TelemetryReceived:
        return TelemetryReceived(
            timestamp=timestamp or datetime.now(),
            node_id=node_id,
            battery_level=battery_level,
            voltage=voltage,
            channel_utilization=channel_utilization,
            air_util_tx=air_util_tx,
            temperature=temperature,
            humidity=humidity,
            pressure=pressure
        )
    @staticmethod
    def position_update(
        node_id: str = "!node1234",
        latitude: float = 37.7749,
        longitude: float = -122.4194,
        altitude: Optional[int] = 100,
        precision_bits: int = 32,
        timestamp: Optional[datetime] = None
    ) -> PositionUpdate:
        return PositionUpdate(
            timestamp=timestamp or datetime.now(),
            node_id=node_id,
            latitude=latitude,
            longitude=longitude,
            altitude=altitude,
            precision_bits=precision_bits
        )
    @staticmethod
    def node_info(
        node_id: str = "!node1234",
        user_id: str = "!user5678",
        long_name: str = "Test User",
        short_name: str = "TU",
        hardware_model: str = "TBEAM",
        role: str = "CLIENT",
        timestamp: Optional[datetime] = None
    ) -> NodeInfo:
        return NodeInfo(
            timestamp=timestamp or datetime.now(),
            node_id=node_id,
            user_id=user_id,
            long_name=long_name,
            short_name=short_name,
            hardware_model=hardware_model,
            role=role
        )


class StateFactory:
    @staticmethod
    def node_state(
        node_id: str = "!node1234",
        long_name: str = "Test Node",
        short_name: str = "TN",
        hardware_model: str = "TBEAM",
        role: str = "CLIENT",
        first_seen: Optional[datetime] = None,
        last_seen: Optional[datetime] = None,
        battery_level: Optional[int] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None
    ) -> NodeState:
        now = datetime.now()
        return NodeState(
            node_id=node_id,
            long_name=long_name,
            short_name=short_name,
            hardware_model=hardware_model,
            role=role,
            first_seen=first_seen or now,
            last_seen=last_seen or now,
            battery_level=battery_level,
            latitude=latitude,
            longitude=longitude
        )


def create_event_sequence(node_id: str, count: int = 5):
    base_time = datetime.now()
    events = []
    events.append(EventFactory.node_discovered(node_id=node_id, timestamp=base_time))
    for i in range(count):
        timestamp = base_time + timedelta(minutes=i + 1)
        events.append(EventFactory.telemetry_received(node_id=node_id, timestamp=timestamp))
    return events

