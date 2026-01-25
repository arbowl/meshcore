"""Telemetry query service"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from meshcore.adapters.storage.sqlite import SqliteEventStore


@dataclass
class DataPoint:
    """Time-series data point"""

    timestamp: datetime
    value: float


@dataclass
class TelemetryStats:
    """Statistics for a telemetry metric"""

    min_value: Optional[float]
    max_value: Optional[float]
    avg_value: Optional[float]
    current_value: Optional[float]
    data_points: int


class TelemetryQueryService:
    """Query and aggregate telemetry data"""

    def __init__(self, event_store: SqliteEventStore):
        self._event_store = event_store

    async def get_time_series(
        self,
        node_id: str,
        metric: str,
        since: Optional[datetime] = None,
        limit: int = 1000,
    ) -> list[DataPoint]:
        """Get time-series data for a specific metric"""
        if since is None:
            since = datetime.now(timezone.utc) - timedelta(hours=24)

        events = await self._event_store.get_telemetry_series(
            node_id=node_id,
            since=since,
            limit=limit,
        )

        data_points = []
        for event in events:
            value = event.payload.get(metric)
            if value is not None:
                data_points.append(DataPoint(
                    timestamp=event.timestamp,
                    value=float(value)
                ))

        return data_points

    async def get_statistics(
        self,
        node_id: str,
        metric: str,
        since: Optional[datetime] = None,
    ) -> TelemetryStats:
        """Get statistical summary for a metric"""
        data_points = await self.get_time_series(node_id, metric, since)

        if not data_points:
            return TelemetryStats(
                min_value=None,
                max_value=None,
                avg_value=None,
                current_value=None,
                data_points=0,
            )

        values = [dp.value for dp in data_points]
        return TelemetryStats(
            min_value=min(values),
            max_value=max(values),
            avg_value=sum(values) / len(values),
            current_value=data_points[-1].value if data_points else None,
            data_points=len(data_points),
        )

    async def get_all_metrics(
        self,
        node_id: str,
        since: Optional[datetime] = None,
    ) -> dict[str, list[DataPoint]]:
        """Get all available telemetry metrics for a node"""
        if since is None:
            since = datetime.now(timezone.utc) - timedelta(hours=24)

        events = await self._event_store.get_telemetry_series(
            node_id=node_id,
            since=since,
            limit=1000,
        )

        # Organize by metric type
        metrics: dict[str, list[DataPoint]] = {}
        for event in events:
            for key, value in event.payload.items():
                if isinstance(value, (int, float)):
                    if key not in metrics:
                        metrics[key] = []
                    metrics[key].append(DataPoint(
                        timestamp=event.timestamp,
                        value=float(value)
                    ))

        return metrics

    async def get_battery_history(
        self,
        node_id: str,
        since: Optional[datetime] = None,
    ) -> list[DataPoint]:
        """Convenience method for battery level history"""
        return await self.get_time_series(node_id, "battery_level", since)

    async def get_temperature_history(
        self,
        node_id: str,
        since: Optional[datetime] = None,
    ) -> list[DataPoint]:
        """Convenience method for temperature history"""
        return await self.get_time_series(node_id, "temperature", since)
