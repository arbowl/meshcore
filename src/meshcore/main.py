"""Main"""

import asyncio
from datetime import datetime, timezone

from meshcore.adapters.meshtastic.mock import MockMeshtasticEventSource
from meshcore.adapters.pubsub.mqtt import MqttEventPublisher
from meshcore.adapters.storage.sqlite import SqliteEventStore
from meshcore.adapters.storage.state_sqlite import SqliteStateStore
from meshcore.application.services import MeshEventService
from meshcore.application.state_projection import StateProjection
from meshcore.domain.models import EventId, MeshEvent, NodeId


class FakeSource:
    async def events(self):
        yield MeshEvent(
            event_id=EventId(),
            node_id=NodeId(value="test--node"),
            event_type="test",
            timestamp=datetime.now(timezone.utc),
            ingested_at=datetime.now(timezone.utc),
            payload={"hello": "world"},
            provenance={"source": "fake"},
        )


async def main_loop():
    state_store = SqliteStateStore()
    state_projection = StateProjection(state_store)
    service = MeshEventService(
        source=MockMeshtasticEventSource(interval=1.5),
        store=SqliteEventStore(),
        publisher=MqttEventPublisher(
            host="localhost",
            topic="meshcore/events",
        ),
        state_projection=state_projection,
    )
    await service.run()


async def async_main():
    await main_loop()


def main():
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
