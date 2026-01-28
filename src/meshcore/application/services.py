"""Service for the app with robust error handling and transaction support"""

import asyncio
import logging
from typing import Optional

from meshcore.application.ports import EventPublisher, EventSource, EventStore
from meshcore.application.state_projection import StateProjection
from meshcore.domain.models import MeshEvent

logger = logging.getLogger(__name__)


class MeshEventService:
    """Service for handling mesh events with error recovery"""

    def __init__(
        self,
        source: EventSource,
        store: EventStore,
        publisher: EventPublisher,
        state_projection: Optional[StateProjection] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> None:
        self._source = source
        self._store = store
        self._publisher = publisher
        self._state_projection = state_projection
        self._max_retries = max_retries
        self._retry_delay = retry_delay
        self._processed_count = 0
        self._error_count = 0
        self._duplicate_count = 0

    async def run(self) -> None:
        """Main event processing loop with error handling"""
        logger.info("MeshEventService starting...")
        try:
            event: MeshEvent
            async for event in self._source.events():
                correlation_id = str(event.event_id.value)
                try:
                    if await self._store.event_exists(event.event_id.value):
                        self._duplicate_count += 1
                        logger.debug(
                            f"Skipping duplicate event from "
                            f"{event.node_id.value}",
                            extra={"correlation_id": correlation_id}
                        )
                        continue
                    await self._process_event_with_retry(event, correlation_id)
                    self._processed_count += 1
                    if self._processed_count % 100 == 0:
                        logger.info(
                            f"Processed {self._processed_count} events "
                            f"(errors: {self._error_count}, "
                            f"duplicates: {self._duplicate_count})"
                        )
                except Exception as e:
                    self._error_count += 1
                    logger.error(
                        f"Fatal error processing event "
                        f"{event.event_id.value}: {e}",
                        extra={"correlation_id": correlation_id},
                        exc_info=True
                    )
        except asyncio.CancelledError:
            logger.info("MeshEventService shutdown requested")
            logger.info(
                f"Final stats - Processed: {self._processed_count}, "
                f"Errors: {self._error_count}, "
                f"Duplicates: {self._duplicate_count}"
            )
            raise
        except Exception as e:
            logger.error(
                f"Fatal error in MeshEventService: {e}", exc_info=True
            )
            raise

    async def _process_event_with_retry(
        self, event: MeshEvent, correlation_id: str
    ) -> None:
        """Process a single event with retry logic"""
        for attempt in range(self._max_retries):
            try:
                await self._store.append(event)
                if self._state_projection:
                    await self._state_projection.project(event)
                try:
                    await self._publisher.publish(event)
                except Exception as pub_error:
                    logger.warning(
                        f"Failed to publish event, continuing: {pub_error}",
                        extra={"correlation_id": correlation_id}
                    )
                logger.debug(
                    f"Successfully processed {event.event_type} from "
                    f"{event.node_id.value}",
                    extra={"correlation_id": correlation_id}
                )
                return
            except Exception as e:
                if attempt < self._max_retries - 1:
                    logger.warning(
                        f"Attempt {attempt + 1} failed, retrying: {e}",
                        extra={"correlation_id": correlation_id}
                    )
                    await asyncio.sleep(self._retry_delay * (attempt + 1))
                else:
                    logger.error(
                        f"All retry attempts exhausted for event: {e}",
                        extra={"correlation_id": correlation_id}
                    )
                    raise
