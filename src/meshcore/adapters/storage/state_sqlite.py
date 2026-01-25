"""SQLite state storage"""

import asyncio
import json
import sqlite3
from datetime import datetime

from meshcore.domain.models import NodeId, NodeState


class SqliteStateStore:
    """SQLite state storage"""

    def __init__(self, path: str = "state.db") -> None:
        self._conn = sqlite3.connect(
            path,
            check_same_thread=False,
        )
        self._conn.row_factory = sqlite3.Row
        self._initialize()

    def _initialize(self) -> None:
        cur = self._conn.cursor()
        cur.execute("PRAGMA journal_mode=WAL;")
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS node_states (
                node_id TEXT PRIMARY KEY,
                last_seen TEXT NOT NULL,
                first_seen TEXT NOT NULL,
                event_count INTEGER NOT NULL,
                last_telemetry_json TEXT,
                last_position_json TEXT,
                last_text TEXT
            )
            """
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_states_last_seen ON "
            "node_states(last_seen)"
        )
        self._conn.commit()

    async def upsert_node(self, state: NodeState) -> None:
        def _upsert():
            self._conn.execute(
                """
                INSERT INTO node_states (
                    node_id,
                    last_seen,
                    first_seen,
                    event_count,
                    last_telemetry_json,
                    last_position_json,
                    last_text
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(node_id) DO UPDATE SET
                    last_seen=excluded.last_seen,
                    event_count=excluded.event_count,
                    last_telemetry_json=excluded.last_telemetry_json,
                    last_position_json=excluded.last_position_json,
                    last_text=excluded.last_text
                """,
                (
                    state.node_id.value,
                    state.last_seen.isoformat(),
                    state.first_seen.isoformat(),
                    state.event_count,
                    json.dumps(state.last_telemetry) if state.last_telemetry else None,
                    json.dumps(state.last_position) if state.last_position else None,
                    state.last_text,
                ),
            )
            self._conn.commit()
        await asyncio.to_thread(_upsert)

    async def get_node(self, node_id: NodeId) -> NodeState | None:
        def _get():
            cur = self._conn.execute(
                "SELECT * FROM node_states WHERE node_id = ?",
                (node_id.value,)
            )
            return cur.fetchone()
        row = await asyncio.to_thread(_get)
        if not row:
            return None
        return NodeState(
            node_id=NodeId(value=row["node_id"]),
            last_seen=datetime.fromisoformat(row["last_seen"]),
            first_seen=datetime.fromisoformat(row["first_seen"]),
            event_count=row["event_count"],
            last_telemetry=json.loads(row["last_telemetry_json"]) if row["last_telemetry_json"] else None,
            last_position=json.loads(row["last_position_json"]) if row["last_position_json"] else None,
            last_text=row["last_text"],
        )

    async def list_nodes(self) -> list[NodeState]:
        def _list():
            cur = self._conn.execute(
                "SELECT * FROM node_states ORDER BY last_seen DESC"
            )
            return cur.fetchall()
        rows = await asyncio.to_thread(_list)
        return [
            NodeState(
                node_id=NodeId(value=row["node_id"]),
                last_seen=datetime.fromisoformat(row["last_seen"]),
                first_seen=datetime.fromisoformat(row["first_seen"]),
                event_count=row["event_count"],
                last_telemetry=json.loads(row["last_telemetry_json"]) if row["last_telemetry_json"] else None,
                last_position=json.loads(row["last_position_json"]) if row["last_position_json"] else None,
                last_text=row["last_text"],
            )
            for row in rows
        ]

    async def delete_node(self, node_id: NodeId) -> None:
        def _delete():
            self._conn.execute(
                "DELETE FROM node_states WHERE node_id = ?",
                (node_id.value,)
            )
            self._conn.commit()
        await asyncio.to_thread(_delete)

