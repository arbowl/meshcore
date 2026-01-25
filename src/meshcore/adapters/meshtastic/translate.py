"""Meshtastic packet translation"""

from collections import defaultdict
from datetime import datetime, timezone
from typing import Optional

from meshcore.domain.models import EventId, NodeId, MeshEvent


_event_type_from_port: defaultdict[int, str] = defaultdict(lambda: "unknown")
_event_type_from_port[1] = "text"
_event_type_from_port[3] = "telemetry"
_event_type_from_port[4] = "position"
_event_type_from_port[5] = "node_info"


def translate_packet(packet: dict) -> Optional[MeshEvent]:
    """Convert a Meshtastic packet to a MeshEvent"""
    decoded = packet.get("decoded", {})
    if not decoded:
        return None
    portnum = decoded.get("portnum", "")
    payload = decoded.get("payload", "")
    event_type = _event_type_from_port[portnum]
    return MeshEvent(
        event_id=EventId(),
        node_id=NodeId(value=str(packet.get("from", ""))),
        event_type=event_type,
        timestamp=_packet_timestamp(packet),
        ingested_at=datetime.now(timezone.utc),
        payload=_decode_payload(portnum, payload),
        provenance={
            "source": "meshtastic",
            "portnum": portnum,
            "hp_limit": packet.get("hp_limit", None),
        }
    )


def _packet_timestamp(packet: dict) -> datetime:
    """Extract timestamp from packet or use current time"""
    ts = packet.get("rxTime")
    if ts:
        return datetime.fromtimestamp(ts, tz=timezone.utc)
    return datetime.now(timezone.utc)


def _decode_payload(portnum: int, payload: bytes) -> dict:
    """Decode payload based on port number"""
    if portnum == 1:
        try:
            return {"text": payload.decode("utf-8")}
        except Exception:
            return {"raw": payload.hex()}
    return {"raw": payload.hex()}
