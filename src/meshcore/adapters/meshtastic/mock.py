"""Mock node for testing"""

import asyncio
import random
from datetime import datetime, timedelta, timezone
from typing import Optional, AsyncIterator

from meshcore.application.ports import EventSource
from meshcore.domain.models import EventId, NodeId, MeshEvent


class MockMeshtasticEventSource(EventSource):
    """Fake node"""

    def __init__(
        self,
        node_ids: Optional[list[str]] = None,
        interval: float = 2.0,
    ):
        self.node_ids = node_ids or [
            "node-alpha",
            "node-bravo",
            "node-charlie",
        ]
        self.interval = interval

    async def events(self) -> AsyncIterator[MeshEvent]:
        """Async iterator of MeshEvents from the mock source"""
        while True:
            await asyncio.sleep(self._next_delay())
            yield self._generate_event()

    def _next_delay(self) -> float:
        """Fake jitter"""
        return max(0.2, random.gauss(self.interval, 0.5))

    def _generate_event(self) -> MeshEvent:
        """Generate a mock event"""
        node = random.choice(self.node_ids)
        event_type = random.choices(
            ["telemetry", "position", "text"],
            weights=[0.5, 0.3, 0.2],
        )[0]
        payload = self._payload_for(event_type)
        now = datetime.now(timezone.utc)
        return MeshEvent(
            event_id=EventId(),
            node_id=NodeId(value=node),
            event_type=event_type,
            timestamp=now - timedelta(seconds=random.uniform(0, 3)),
            ingested_at=now,
            payload=payload,
            provenance={
                "source": "mock",
                "generator": "MockMeshtasticEventSource",
            },
        )

    def _payload_for(self, event_type: str) -> dict:
        """Generate payload based on event type"""
        if event_type == "telemetry":
            return {
                "battery": round(random.uniform(3.7, 4.2), 2),
                "temperature": round(random.uniform(15, 35), 1),
                "rssi": random.randint(-120, -70),
            }
        if event_type == "position":
            return {
                "lat": 37.7749 + random.uniform(-0.001, 0.001),
                "lon": -122.4194 + random.uniform(-0.001, 0.001),
                "alt": random.randint(0, 50),
            }
        if event_type == "text":
            return {
                "text": random.choice(
                    [
                        "hello mesh",
                        "ping",
                        "status ok",
                        "testing 1 2 3",
                    ]
                )
            }
        return {}
