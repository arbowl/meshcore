"""Meshtastic packet translation with complete payload decoding"""

import logging
from collections import defaultdict
from datetime import datetime, timezone
from typing import Optional, Any

from meshcore.domain.models import EventId, NodeId, MeshEvent

logger = logging.getLogger(__name__)

# Port number to event type mapping
_event_type_from_port: defaultdict[int, str] = defaultdict(lambda: "unknown")
_event_type_from_port[1] = "text"
_event_type_from_port[3] = "telemetry"
_event_type_from_port[4] = "position"
_event_type_from_port[5] = "node_info"


def translate_packet(packet: dict) -> Optional[MeshEvent]:
    """Convert a Meshtastic packet to a MeshEvent with full decoding"""
    decoded: dict = packet.get("decoded", {})
    if not decoded:
        return None
    portnum = decoded.get("portnum", "")
    event_type = _event_type_from_port[portnum]
    payload = _decode_payload(portnum, decoded)
    if not payload:
        logger.debug(f"Skipping event with empty payload from port {portnum}")
        return None
    return MeshEvent(
        event_id=EventId(),
        node_id=NodeId(value=str(packet.get("from", ""))),
        event_type=event_type,
        timestamp=_packet_timestamp(packet),
        ingested_at=datetime.now(timezone.utc),
        payload=payload,
        provenance={
            "source": "meshtastic",
            "portnum": portnum,
            "hp_limit": packet.get("hp_limit", None),
            "rx_snr": packet.get("rxSnr", None),
            "rx_rssi": packet.get("rxRssi", None),
        }
    )


def _packet_timestamp(packet: dict) -> datetime:
    """Extract timestamp from packet or use current time"""
    ts = packet.get("rxTime")
    if ts:
        return datetime.fromtimestamp(ts, tz=timezone.utc)
    return datetime.now(timezone.utc)


def _decode_payload(portnum: int, decoded: dict) -> dict[str, Any]:
    """Decode payload based on port number with proper type handling"""
    if portnum == 1:
        payload_bytes = decoded.get("payload", b"")
        if isinstance(payload_bytes, bytes):
            try:
                return {"text": payload_bytes.decode("utf-8")}
            except Exception as e:
                logger.warning(f"Failed to decode text payload: {e}")
                return {"raw": payload_bytes.hex()}
        elif isinstance(payload_bytes, str):
            return {"text": payload_bytes}
        return {}
    elif portnum == 3:
        return _decode_telemetry(decoded)
    elif portnum == 4:
        return _decode_position(decoded)
    elif portnum == 5:
        return _decode_node_info(decoded)
    else:
        payload_bytes = decoded.get("payload", b"")
        if isinstance(payload_bytes, bytes):
            return {"raw": payload_bytes.hex()}
        return {}


def _decode_telemetry(decoded: dict) -> dict[str, Any]:
    """Decode telemetry data from Meshtastic packet"""
    telemetry = {}
    device_metrics = decoded.get("deviceMetrics", decoded.get("device", {}))
    if device_metrics:
        if "batteryLevel" in device_metrics:
            telemetry["battery_level"] = device_metrics["batteryLevel"]
        if "voltage" in device_metrics:
            telemetry["voltage"] = device_metrics["voltage"]
        if "channelUtilization" in device_metrics:
            telemetry["channel_utilization"] = (
                device_metrics["channelUtilization"]
            )
        if "airUtilTx" in device_metrics:
            telemetry["air_util_tx"] = device_metrics["airUtilTx"]
    env_metrics = decoded.get(
        "environmentMetrics", decoded.get("environment", {})
    )
    if env_metrics:
        if "temperature" in env_metrics:
            telemetry["temperature"] = env_metrics["temperature"]
        if "relativeHumidity" in env_metrics:
            telemetry["humidity"] = env_metrics["relativeHumidity"]
        if "barometricPressure" in env_metrics:
            telemetry["pressure"] = env_metrics["barometricPressure"]
    power_metrics = decoded.get("powerMetrics", decoded.get("power", {}))
    if power_metrics:
        if "ch1Voltage" in power_metrics:
            telemetry["ch1_voltage"] = power_metrics["ch1Voltage"]
        if "ch1Current" in power_metrics:
            telemetry["ch1_current"] = power_metrics["ch1Current"]
    if not telemetry:
        for key in [
            "battery_level", "voltage", "temperature", "channelUtilization"
        ]:
            if key in decoded:
                telemetry[key] = decoded[key]
    return telemetry if telemetry else {"raw": str(decoded)}


def _decode_position(decoded: dict) -> dict[str, Any]:
    """Decode position data from Meshtastic packet"""
    position = {}
    pos_data: dict = decoded.get("position", decoded)
    if "latitude" in pos_data or "latitudeI" in pos_data:
        lat = pos_data.get("latitude") or pos_data.get("latitudeI", 0) / 1e7
        lon = pos_data.get("longitude") or pos_data.get("longitudeI", 0) / 1e7
        position["latitude"] = lat
        position["longitude"] = lon
        if "altitude" in pos_data:
            position["altitude"] = pos_data["altitude"]
        if "groundSpeed" in pos_data:
            position["speed"] = pos_data["groundSpeed"]
        if "groundTrack" in pos_data:
            position["heading"] = pos_data["groundTrack"]
        if "satsInView" in pos_data:
            position["satellites"] = pos_data["satsInView"]
    return position if position else {"raw": str(decoded)}


def _decode_node_info(decoded: dict) -> dict[str, Any]:
    """Decode node info from Meshtastic packet"""
    node_info = {}
    user = decoded.get("user", {})
    if user:
        if "id" in user:
            node_info["node_id"] = user["id"]
        if "longName" in user:
            node_info["long_name"] = user["longName"]
        if "shortName" in user:
            node_info["short_name"] = user["shortName"]
        if "macaddr" in user:
            node_info["mac_address"] = user["macaddr"]
        if "hwModel" in user:
            node_info["hardware_model"] = user["hwModel"]
    return node_info if node_info else {"raw": str(decoded)}
