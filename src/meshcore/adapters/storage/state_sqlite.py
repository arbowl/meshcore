"""SQLite state storage with proper async safety"""

import asyncio
import json
import logging
import sqlite3
from datetime import datetime

from meshcore.domain.models import NodeId, NodeState

logger = logging.getLogger(__name__)


class SqliteStateStore:
    """SQLite state storage with thread-safe async operations"""

    def __init__(self, path: str = "state.db") -> None:
        self._path = path
        self._conn: sqlite3.Connection | None = None
        self._lock: asyncio.Lock | None = None
        self._lock_loop: asyncio.AbstractEventLoop | None = None
        self._closed = False

    async def __aenter__(self):
        """Async context manager entry"""
        await self._ensure_connection()
        return self

    async def __aexit__(self, *args):
        """Async context manager exit"""
        await self.close()

    async def _ensure_connection(self) -> None:
        """Ensure database connection is established"""
        # Recreate lock if we're in a different event loop (happens with asyncio.run())
        current_loop = asyncio.get_running_loop()
        if self._lock is None or self._lock_loop != current_loop:
            self._lock = asyncio.Lock()
            self._lock_loop = current_loop
        
        if self._conn is None and not self._closed:
            await self._connect()

    async def _connect(self) -> None:
        """Connect to database and initialize schema"""
        def _init():
            conn = sqlite3.connect(self._path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("PRAGMA journal_mode=WAL;")
            cur.execute("PRAGMA busy_timeout=5000;")
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
            conn.commit()
            return conn

        self._conn = await asyncio.to_thread(_init)
        logger.info(f"Connected to state store at {self._path}")

    async def close(self) -> None:
        """Close database connection"""
        if self._conn and not self._closed:
            await asyncio.to_thread(self._conn.close)
            self._conn = None
            self._closed = True
            logger.info("State store connection closed")

    async def upsert_node(self, state: NodeState) -> None:
        """Insert or update node state"""
        await self._ensure_connection()

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
                    json.dumps(state.last_telemetry) if state.last_telemetry else None,  # noqa: E501
                    json.dumps(state.last_position) if state.last_position else None,  # noqa: E501
                    state.last_text,
                ),
            )
            self._conn.commit()

        async with self._lock:
            await asyncio.to_thread(_upsert)

    async def get_node(self, node_id: NodeId) -> NodeState | None:
        """Retrieve node state by ID"""
        await self._ensure_connection()

        def _get():
            cur = self._conn.execute(
                "SELECT * FROM node_states WHERE node_id = ?",
                (node_id.value,)
            )
            return cur.fetchone()

        async with self._lock:
            row = await asyncio.to_thread(_get)
        if not row:
            return None
        return NodeState(
            node_id=NodeId(value=row["node_id"]),
            last_seen=datetime.fromisoformat(row["last_seen"]),
            first_seen=datetime.fromisoformat(row["first_seen"]),
            event_count=row["event_count"],
            last_telemetry=json.loads(row["last_telemetry_json"]) if row["last_telemetry_json"] else None,  # noqa: E501
            last_position=json.loads(row["last_position_json"]) if row["last_position_json"] else None,  # noqa: E501
            last_text=row["last_text"],
        )

    async def list_nodes(self) -> list[NodeState]:
        """List all nodes ordered by last seen"""
        await self._ensure_connection()

        def _list():
            cur = self._conn.execute(
                "SELECT * FROM node_states ORDER BY last_seen DESC"
            )
            return cur.fetchall()
        async with self._lock:
            rows = await asyncio.to_thread(_list)
        return [
            NodeState(
                node_id=NodeId(value=row["node_id"]),
                last_seen=datetime.fromisoformat(row["last_seen"]),
                first_seen=datetime.fromisoformat(row["first_seen"]),
                event_count=row["event_count"],
                last_telemetry=json.loads(row["last_telemetry_json"]) if row["last_telemetry_json"] else None,  # noqa: E501
                last_position=json.loads(row["last_position_json"]) if row["last_position_json"] else None,  # noqa: E501
                last_text=row["last_text"],
            )
            for row in rows
        ]

    async def delete_node(self, node_id: NodeId) -> None:
        """Delete a node from state"""
        await self._ensure_connection()

        def _delete():
            self._conn.execute(
                "DELETE FROM node_states WHERE node_id = ?",
                (node_id.value,)
            )
            self._conn.commit()

        async with self._lock:
            await asyncio.to_thread(_delete)
