"""State projection service"""

from datetime import datetime

from meshcore.application.ports import StateStore
from meshcore.domain.models import MeshEvent, NodeId, NodeState


class StateProjection:
    """Projects events into current state"""

    def __init__(self, state_store: StateStore) -> None:
        self._state_store = state_store

    async def project(self, event: MeshEvent) -> None:
        existing = await self._state_store.get_node(event.node_id)
        if existing:
            state = self._update_state(existing, event)
        else:
            state = self._create_state(event)
        await self._state_store.upsert_node(state)

    def _create_state(self, event: MeshEvent) -> NodeState:
        return NodeState(
            node_id=event.node_id,
            last_seen=event.timestamp,
            first_seen=event.timestamp,
            event_count=1,
            last_telemetry=event.payload if event.event_type == "telemetry" else None,
            last_position=event.payload if event.event_type == "position" else None,
            last_text=event.payload.get("text") if event.event_type == "text" else None,
        )

    def _update_state(self, state: NodeState, event: MeshEvent) -> NodeState:
        updates = {
            "last_seen": event.timestamp,
            "event_count": state.event_count + 1,
        }
        if event.event_type == "telemetry":
            updates["last_telemetry"] = event.payload
        elif event.event_type == "position":
            updates["last_position"] = event.payload
        elif event.event_type == "text":
            updates["last_text"] = event.payload.get("text")
        return state.model_copy(update=updates)

