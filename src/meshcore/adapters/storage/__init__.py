"""Storage adapters for meshcore"""

from .memory import InMemoryEventStore
from .replay import ReplayEventSource
from .sqlite import SqliteEventStore
from .state_memory import InMemoryStateStore
from .state_sqlite import SqliteStateStore


StoreType = (
    SqliteEventStore
    | InMemoryEventStore
    | ReplayEventSource
)

__all__ = ["StoreType", "InMemoryStateStore", "SqliteStateStore"]
