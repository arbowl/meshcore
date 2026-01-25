import pytest
from datetime import datetime, timedelta
from meshcore.application.telemetry_service import TelemetryQueryService, DataPoint
from tests.fixtures.factories import EventFactory


def test_telemetry_query_service_initialization(mock_event_store):
    service = TelemetryQueryService(mock_event_store)
    assert service.event_store == mock_event_store


def test_get_time_series_returns_data_points(mock_event_store):
    telemetry_events = [
        EventFactory.telemetry_received(
            node_id="!test",
            battery_level=85,
            timestamp=datetime.now() - timedelta(hours=2)
        ),
        EventFactory.telemetry_received(
            node_id="!test",
            battery_level=80,
            timestamp=datetime.now() - timedelta(hours=1)
        )
    ]
    mock_event_store.get_telemetry_series.return_value = telemetry_events
    service = TelemetryQueryService(mock_event_store)
    results = service.get_time_series("!test", "battery_level", hours=24)
    assert len(results) == 2
    assert results[0].value == 85
    assert results[1].value == 80


def test_get_time_series_filters_none_values(mock_event_store):
    telemetry_events = [
        EventFactory.telemetry_received(node_id="!test", voltage=4.2),
        EventFactory.telemetry_received(node_id="!test", voltage=None)
    ]
    mock_event_store.get_telemetry_series.return_value = telemetry_events
    service = TelemetryQueryService(mock_event_store)
    results = service.get_time_series("!test", "voltage", hours=24)
    assert len(results) == 1
    assert results[0].value == 4.2


def test_get_statistics_calculates_correctly(mock_event_store):
    telemetry_events = [
        EventFactory.telemetry_received(node_id="!test", battery_level=80),
        EventFactory.telemetry_received(node_id="!test", battery_level=85),
        EventFactory.telemetry_received(node_id="!test", battery_level=90)
    ]
    mock_event_store.get_telemetry_series.return_value = telemetry_events
    service = TelemetryQueryService(mock_event_store)
    stats = service.get_statistics("!test", "battery_level", hours=24)
    assert stats.min == 80
    assert stats.max == 90
    assert stats.avg == 85.0
    assert stats.count == 3


def test_get_statistics_returns_none_for_no_data(mock_event_store):
    mock_event_store.get_telemetry_series.return_value = []
    service = TelemetryQueryService(mock_event_store)
    stats = service.get_statistics("!test", "battery_level", hours=24)
    assert stats.min is None
    assert stats.max is None
    assert stats.avg is None
    assert stats.count == 0


def test_get_all_metrics_returns_available_metrics(mock_event_store):
    telemetry_events = [
        EventFactory.telemetry_received(
            node_id="!test",
            battery_level=85,
            voltage=4.2,
            temperature=25.5
        )
    ]
    mock_event_store.get_telemetry_series.return_value = telemetry_events
    service = TelemetryQueryService(mock_event_store)
    metrics = service.get_all_metrics("!test", hours=24)
    assert "battery_level" in metrics
    assert "voltage" in metrics
    assert "temperature" in metrics
    assert len(metrics["battery_level"]) == 1

