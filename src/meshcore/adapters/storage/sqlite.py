"""SQLite3 storage adapter"""

import asyncio
import json
import sqlite3
from datetime import datetime
from typing import AsyncIterator, Optional
from uuid import UUID

from meshcore.domain.models import MeshEvent, EventId, NodeId


class SqliteEventStore:
    """SQLite3 event store"""

    def __init__(self, path: str = "events.db") -> None:
        self._conn = sqlite3.connect(
            path,
            check_same_thread=False,
        )
        self._conn.row_factory = sqlite3.Row
        self._initialize()

    def _initialize(self) -> None:
        """Create events table if not exist"""
        cur = self._conn.cursor()
        cur.execute("PRAGMA journal_mode=WAL;")
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                node_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                ingested_at TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                provenance_json TEXT NOT NULL
            )
            """
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_events_timestamp ON "
            "events(timestamp)"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_events_node ON events(node_id)"
        )
        self._conn.commit()

    async def append(self, event: MeshEvent) -> None:
        """Append a MeshEvent to the store"""

        def _insert():
            self._conn.execute(
                """
                INSERT INTO events (
                    id,
                    node_id,
                    event_type,
                    timestamp,
                    ingested_at,
                    payload_json,
                    provenance_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(event.event_id.value),
                    event.node_id.value,
                    event.event_type,
                    event.timestamp.isoformat(),
                    event.ingested_at.isoformat(),
                    json.dumps(event.payload),
                    json.dumps(event.provenance),
                ),
            )
            self._conn.commit()

        await asyncio.to_thread(_insert)

    async def replay(
        self,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
    ) -> AsyncIterator[MeshEvent]:
        query = "SELECT * FROM events WHERE 1=1"
        params = []
        if since:
            query += " AND timestamp >= ?"
            params.append(since.isoformat())
        if until:
            query += " AND timestamp <= ?"
            params.append(until.isoformat())
        query += " ORDER BY timestamp ASC"
        cur = self._conn.execute(query, params)
        for row in cur:
            yield MeshEvent(
                event_id=EventId(value=UUID(row["id"])),
                node_id=NodeId(value=row["node_id"]),
                event_type=row["event_type"],
                timestamp=datetime.fromisoformat(row["timestamp"]),
                ingested_at=datetime.fromisoformat(row["ingested_at"]),
                payload=json.loads(row["payload_json"]),
                provenance=json.loads(row["provenance_json"]),
            )

    async def query_by_type(
        self,
        event_type: str,
        since: Optional[datetime] = None,
        node_id: Optional[str] = None,
        limit: int = 100,
    ) -> list[MeshEvent]:
        """Query events by type with optional filters"""
        def _query():
            query = "SELECT * FROM events WHERE event_type = ?"
            params = [event_type]

            if since:
                query += " AND timestamp >= ?"
                params.append(since.isoformat())

            if node_id:
                query += " AND node_id = ?"
                params.append(node_id)

            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)

            cur = self._conn.execute(query, params)
            return cur.fetchall()

        rows = await asyncio.to_thread(_query)
        return [
            MeshEvent(
                event_id=EventId(value=UUID(row["id"])),
                node_id=NodeId(value=row["node_id"]),
                event_type=row["event_type"],
                timestamp=datetime.fromisoformat(row["timestamp"]),
                ingested_at=datetime.fromisoformat(row["ingested_at"]),
                payload=json.loads(row["payload_json"]),
                provenance=json.loads(row["provenance_json"]),
            )
            for row in rows
        ]

    async def get_telemetry_series(
        self,
        node_id: str,
        since: datetime,
        limit: int = 1000,
    ) -> list[MeshEvent]:
        """Get telemetry events for a node as time series"""
        def _query():
            query = """
                SELECT * FROM events
                WHERE event_type = 'telemetry'
                AND node_id = ?
                AND timestamp >= ?
                ORDER BY timestamp ASC
                LIMIT ?
            """
            cur = self._conn.execute(
                query, (node_id, since.isoformat(), limit)
            )
            return cur.fetchall()

        rows = await asyncio.to_thread(_query)
        return [
            MeshEvent(
                event_id=EventId(value=UUID(row["id"])),
                node_id=NodeId(value=row["node_id"]),
                event_type=row["event_type"],
                timestamp=datetime.fromisoformat(row["timestamp"]),
                ingested_at=datetime.fromisoformat(row["ingested_at"]),
                payload=json.loads(row["payload_json"]),
                provenance=json.loads(row["provenance_json"]),
            )
            for row in rows
        ]

    async def search_messages(
        self,
        search_term: str,
        limit: int = 100,
    ) -> list[MeshEvent]:
        """Search text messages"""
        def _query():
            query = """
                SELECT * FROM events
                WHERE event_type = 'text'
                AND payload_json LIKE ?
                ORDER BY timestamp DESC
                LIMIT ?
            """
            cur = self._conn.execute(query, (f"%{search_term}%", limit))
            return cur.fetchall()

        rows = await asyncio.to_thread(_query)
        return [
            MeshEvent(
                event_id=EventId(value=UUID(row["id"])),
                node_id=NodeId(value=row["node_id"]),
                event_type=row["event_type"],
                timestamp=datetime.fromisoformat(row["timestamp"]),
                ingested_at=datetime.fromisoformat(row["ingested_at"]),
                payload=json.loads(row["payload_json"]),
                provenance=json.loads(row["provenance_json"]),
            )
            for row in rows
        ]
