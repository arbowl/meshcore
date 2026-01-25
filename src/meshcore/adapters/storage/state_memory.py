"""In-memory state storage"""

from meshcore.domain.models import NodeId, NodeState


class InMemoryStateStore:
    """In-memory state storage"""

    def __init__(self) -> None:
        self._states: dict[str, NodeState] = {}

    async def upsert_node(self, state: NodeState) -> None:
        self._states[state.node_id.value] = state

    async def get_node(self, node_id: NodeId) -> NodeState | None:
        return self._states.get(node_id.value)

    async def list_nodes(self) -> list[NodeState]:
        return list(self._states.values())

    async def delete_node(self, node_id: NodeId) -> None:
        self._states.pop(node_id.value, None)

