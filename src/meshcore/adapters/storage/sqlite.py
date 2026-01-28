"""SQLite3 storage adapter with proper async safety"""

import asyncio
import json
import logging
import sqlite3
from datetime import datetime
from typing import AsyncIterator, Optional
from uuid import UUID

from meshcore.domain.models import MeshEvent, EventId, NodeId

logger = logging.getLogger(__name__)


class SqliteEventStore:
    """SQLite3 event store with thread-safe async operations"""

    def __init__(self, path: str = "events.db") -> None:
        self._path = path
        self._conn: Optional[sqlite3.Connection] = None
        self._lock = asyncio.Lock()
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
        if self._conn is None and not self._closed:
            await self._connect()

    async def _connect(self) -> None:
        """Connect to database and initialize schema"""

        def _init():
            conn = sqlite3.connect(self._path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("PRAGMA journal_mode=WAL;")
            cur.execute("PRAGMA busy_timeout=5000;")  # 5 second timeout
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
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_events_type ON "
                "events(event_type)"
            )
            conn.commit()
            return conn

        self._conn = await asyncio.to_thread(_init)
        logger.info(f"Connected to event store at {self._path}")

    async def close(self) -> None:
        """Close database connection"""
        if self._conn and not self._closed:
            await asyncio.to_thread(self._conn.close)
            self._conn = None
            self._closed = True
            logger.info("Event store connection closed")

    async def append(self, event: MeshEvent) -> None:
        """Append a MeshEvent to the store"""
        await self._ensure_connection()

        def _insert():
            try:
                self._conn.execute(
                    """
                    INSERT OR IGNORE INTO events (
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
            except sqlite3.Error as e:
                logger.error(f"Failed to append event "
                             f"{event.event_id.value}: {e}")
                raise

        async with self._lock:
            await asyncio.to_thread(_insert)

    async def replay(
        self,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
    ) -> AsyncIterator[MeshEvent]:
        """Replay events from the store with optional time filtering"""
        await self._ensure_connection()

        def _fetch_all():
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
            return cur.fetchall()

        async with self._lock:
            rows = await asyncio.to_thread(_fetch_all)
        for row in rows:
            yield MeshEvent(
                event_id=EventId(value=UUID(row["id"])),
                node_id=NodeId(value=row["node_id"]),
                event_type=row["event_type"],
                timestamp=datetime.fromisoformat(row["timestamp"]),
                ingested_at=datetime.fromisoformat(row["ingested_at"]),
                payload=json.loads(row["payload_json"]),
                provenance=json.loads(row["provenance_json"]),
            )

    async def event_exists(self, event_id: UUID) -> bool:
        """Check if an event already exists"""
        await self._ensure_connection()

        def _check():
            cur = self._conn.execute(
                "SELECT 1 FROM events WHERE id = ? LIMIT 1",
                (str(event_id),)
            )
            return cur.fetchone() is not None

        async with self._lock:
            return await asyncio.to_thread(_check)

    async def query_by_type(
        self,
        event_type: str,
        since: Optional[datetime] = None,
        node_id: Optional[str] = None,
        limit: int = 100,
    ) -> list[MeshEvent]:
        """Query events by type with optional filters"""
        await self._ensure_connection()

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

        async with self._lock:
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
        await self._ensure_connection()

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

        async with self._lock:
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
        await self._ensure_connection()

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

        async with self._lock:
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
