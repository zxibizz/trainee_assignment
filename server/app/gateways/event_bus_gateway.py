"""Client for the downstream event bus / audit log.

Catalog mutations are published here; the network round-trip carries latency on
every write. Each message is a :class:`ProductEvent` envelope describing *what*
changed and *who* changed it.
"""

import time
import uuid
from collections.abc import Mapping
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from loguru import logger
from pydantic import BaseModel, Field

from app.config import settings


class ProductEventType(str, Enum):
    """The catalog mutation topics published to the event bus."""

    CREATED = "products:created"
    UPDATED = "products:updated"
    DELETED = "products:deleted"


class ProductEvent(BaseModel):
    """Envelope published for a single catalog mutation.

    ``data`` holds the product's record snapshot after the change for
    create/update, and is ``None`` for deletions (the record no longer exists).
    """

    event_type: ProductEventType
    actor: str
    product_id: int
    data: dict[str, Any] | None = None
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ProductEventBusGateway:
    """Thin client around the downstream event bus / audit log."""

    def publish(
        self,
        event_type: ProductEventType,
        *,
        actor: str,
        product_id: int,
        data: Mapping[str, Any] | None = None,
    ) -> None:
        """Publish a catalog mutation to the event bus.

        The message body carries the affected ``product_id``, the ``actor`` that
        made the change, and (for create/update) the resulting record snapshot
        in ``data``; deletions omit ``data`` since the record is gone.
        """
        event = ProductEvent(
            event_type=event_type,
            actor=actor,
            product_id=product_id,
            data=dict(data) if data is not None else None,
        )
        self._send(event)

    def _send(self, event: ProductEvent) -> None:
        """Ship one event envelope downstream (stubbed as network latency)."""
        time.sleep(settings.downstream_event_bus_latency_seconds)
        logger.info(
            "published event {event_id} type={event_type} product_id={product_id} "
            "actor={actor}",
            event_id=event.event_id,
            event_type=event.event_type.value,
            product_id=event.product_id,
            actor=event.actor,
        )
