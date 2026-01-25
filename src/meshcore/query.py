"""CLI tool to query node state"""

import asyncio
import sys

from meshcore.adapters.storage.state_sqlite import SqliteStateStore


async def list_nodes():
    store = SqliteStateStore()
    nodes = await store.list_nodes()
    if not nodes:
        print("No nodes found in database.")
        return
    print(f"Found {len(nodes)} node(s):\n")
    for node in nodes:
        print(f"Node: {node.node_id.value}")
        print(f"  First seen: {node.first_seen}")
        print(f"  Last seen:  {node.last_seen}")
        print(f"  Events:     {node.event_count}")
        if node.last_telemetry:
            print(f"  Telemetry:  {node.last_telemetry}")
        if node.last_position:
            print(f"  Position:   {node.last_position}")
        if node.last_text:
            print(f"  Last text:  {node.last_text}")
        print()


async def get_node(node_id: str):
    store = SqliteStateStore()
    from meshcore.domain.models import NodeId
    node = await store.get_node(NodeId(value=node_id))
    if not node:
        print(f"Node {node_id} not found.")
        return
    print(f"Node: {node.node_id.value}")
    print(f"  First seen: {node.first_seen}")
    print(f"  Last seen:  {node.last_seen}")
    print(f"  Events:     {node.event_count}")
    if node.last_telemetry:
        print(f"  Telemetry:  {node.last_telemetry}")
    if node.last_position:
        print(f"  Position:   {node.last_position}")
    if node.last_text:
        print(f"  Last text:  {node.last_text}")


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python -m meshcore.query list")
        print("  python -m meshcore.query get <node_id>")
        sys.exit(1)
    command = sys.argv[1]
    if command == "list":
        asyncio.run(list_nodes())
    elif command == "get":
        if len(sys.argv) < 3:
            print("Error: node_id required")
            sys.exit(1)
        asyncio.run(get_node(sys.argv[2]))
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
