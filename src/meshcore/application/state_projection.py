"""State projection service"""

from datetime import datetime

from meshcore.application.ports import StateStore
from meshcore.domain.models import MeshEvent, NodeId, NodeState


class StateProjection:
    """Projects events into current state"""

    def __init__(self, state_store: StateStore) -> None:
        self._state_store = state_store

    async def project(self, event: MeshEvent) -> None:
        # ACK events update sent_message tracking, not node state.
        if event.event_type == "ack":
            request_id = event.payload.get("request_id")
            if request_id and hasattr(self._state_store, "mark_acked"):
                await self._state_store.mark_acked(
                    packet_id=request_id,
                    acking_node=event.node_id.value,
                    error_reason=event.payload.get("error_reason", "NONE"),
                    ack_at=event.timestamp,
                )
            return

        existing = await self._state_store.get_node(event.node_id)
        if existing:
            state = self._update_state(existing, event)
        else:
            state = self._create_state(event)
        await self._state_store.upsert_node(state)

    def _create_state(self, event: MeshEvent) -> NodeState:
        long_name = None
        short_name = None
        if event.event_type == "node_info":
            long_name = event.payload.get("long_name")
            short_name = event.payload.get("short_name")
        return NodeState(
            node_id=event.node_id,
            long_name=long_name,
            short_name=short_name,
            last_seen=event.timestamp,
            first_seen=event.timestamp,
            event_count=1,
            last_telemetry=event.payload if event.event_type == "telemetry" else None,
            last_position=event.payload if event.event_type == "position" else None,
            last_text=event.payload.get("text") if event.event_type == "text" else None,
            last_snr=event.provenance.get("rx_snr"),
            last_rssi=event.provenance.get("rx_rssi"),
            last_hops_away=event.provenance.get("hops_away"),
        )

    def _update_state(self, state: NodeState, event: MeshEvent) -> NodeState:
        updates = {
            "last_seen": event.timestamp,
            "event_count": state.event_count + 1,
        }
        snr = event.provenance.get("rx_snr")
        rssi = event.provenance.get("rx_rssi")
        hops_away = event.provenance.get("hops_away")
        if snr is not None:
            updates["last_snr"] = snr
        if rssi is not None:
            updates["last_rssi"] = rssi
        if hops_away is not None:
            updates["last_hops_away"] = hops_away
        if event.event_type == "telemetry":
            updates["last_telemetry"] = event.payload
        elif event.event_type == "position":
            updates["last_position"] = event.payload
        elif event.event_type == "text":
            updates["last_text"] = event.payload.get("text")
        elif event.event_type == "node_info":
            if event.payload.get("long_name"):
                updates["long_name"] = event.payload["long_name"]
            if event.payload.get("short_name"):
                updates["short_name"] = event.payload["short_name"]
        return state.model_copy(update=updates)

