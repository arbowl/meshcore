"""Web UI adapter using Flask and HTMX - Complete HQ Dashboard"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

from flask import Flask, render_template, jsonify, request, Response

from meshcore.adapters.storage.state_sqlite import SqliteStateStore
from meshcore.adapters.storage.sqlite import (
    SqliteEventStore,
    SqliteEventQuery,
)
from meshcore.adapters.meshtastic.commander import MockCommander
from meshcore.application.message_service import MessageQueryService
from meshcore.application.telemetry_service import TelemetryQueryService

logger = logging.getLogger(__name__)


async def _initialize_stores(app: Flask) -> None:
    """Initialize database connections for stores"""
    try:
        await app.config['STATE_STORE'].__aenter__()
        await app.config['EVENT_STORE'].__aenter__()
        logger.info("Database connections initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database connections: {e}")
        raise


async def _cleanup_stores(app: Flask) -> None:
    """Clean up database connections"""
    try:
        if 'STATE_STORE' in app.config:
            await app.config['STATE_STORE'].__aexit__(None, None, None)
        if 'EVENT_STORE' in app.config:
            await app.config['EVENT_STORE'].__aexit__(None, None, None)
        logger.info("Database connections closed successfully")
    except Exception as e:
        logger.error(f"Error during database cleanup: {e}")


def create_app(
    state_db_path: str = "state.db",
    events_db_path: str = "events.db",
    commander=None,
) -> Flask:
    """Create and configure the Flask app"""
    app = Flask(
        __name__,
        template_folder=str(Path(__file__).parent / "templates"),
        static_folder=str(Path(__file__).parent / "static"),
    )

    # Initialize services (connections established on first use or via init)
    app.config['STATE_STORE'] = SqliteStateStore(path=state_db_path)
    app.config['EVENT_STORE'] = SqliteEventStore(path=events_db_path)
    app.config['EVENT_QUERY'] = SqliteEventQuery(
        app.config['EVENT_STORE']
    )
    app.config['MESSAGE_SERVICE'] = MessageQueryService(
        app.config['EVENT_QUERY']
    )
    app.config['TELEMETRY_SERVICE'] = TelemetryQueryService(
        app.config['EVENT_QUERY']
    )
    app.config['COMMANDER'] = commander or MockCommander()
    app.config['STORES_INITIALIZED'] = False

    # ==================== Lifecycle Hooks ====================

    @app.before_request
    def ensure_stores_initialized():
        """Ensure database connections are initialized"""
        if not app.config['STORES_INITIALIZED']:
            asyncio.run(_initialize_stores(app))
            app.config['STORES_INITIALIZED'] = True

    # ==================== Dashboard Routes ====================

    @app.route("/")
    def index():
        """Main dashboard page"""
        return render_template("index.html")

    @app.route("/nodes")
    def nodes_table():
        """HTMX endpoint - returns just the nodes table HTML"""
        state_store = app.config['STATE_STORE']
        nodes = asyncio.run(state_store.list_nodes())
        return render_template(
            "nodes_table.html",
            nodes=nodes,
            now=datetime.now(timezone.utc)
        )

    @app.route("/stats")
    def stats():
        """HTMX endpoint - returns stats summary"""
        state_store = app.config['STATE_STORE']
        nodes = asyncio.run(state_store.list_nodes())

        total_nodes = len(nodes)
        now = datetime.now(timezone.utc)
        active_nodes = sum(
            1 for n in nodes
            if (now - n.last_seen).total_seconds() < 300
        )
        total_events = sum(n.event_count for n in nodes)

        return render_template(
            "stats.html",
            total_nodes=total_nodes,
            active_nodes=active_nodes,
            total_events=total_events,
        )

    # ==================== Message Routes ====================

    @app.route("/messages")
    def messages_page():
        """Message history page"""
        return render_template("messages.html")

    @app.route("/messages/list")
    def messages_list():
        """HTMX endpoint - returns messages list"""
        msg_service = app.config['MESSAGE_SERVICE']

        # Get query parameters
        node_id = request.args.get('node_id')
        search = request.args.get('search')
        limit = int(request.args.get('limit', 100))

        if search:
            messages = asyncio.run(
                msg_service.search_messages(search, limit)
            )
        elif node_id:
            messages = asyncio.run(
                msg_service.get_messages_by_node(node_id, limit)
            )
        else:
            messages = asyncio.run(msg_service.get_recent_messages(limit))

        return render_template("messages_list.html", messages=messages)

    @app.route("/api/messages")
    def api_messages():
        """JSON API for messages"""
        msg_service = app.config['MESSAGE_SERVICE']
        messages = asyncio.run(msg_service.get_recent_messages(limit=100))

        return jsonify([
            {
                "id": str(msg.id),
                "from": msg.from_node,
                "to": msg.to_node,
                "text": msg.text,
                "timestamp": msg.timestamp.isoformat(),
                "channel": msg.channel,
                "encrypted": msg.encrypted,
            }
            for msg in messages
        ])

    # ==================== Compose & Send Routes ====================

    @app.route("/compose")
    def compose_page():
        """Message composition page"""
        state_store = app.config['STATE_STORE']
        nodes = asyncio.run(state_store.list_nodes())
        return render_template("compose.html", nodes=nodes)

    @app.route("/api/send_message", methods=["POST"])
    def send_message():
        """Send a message through Meshtastic"""
        commander = app.config['COMMANDER']

        text = request.form.get('message', '')
        destination = request.form.get('recipient')
        channel = int(request.form.get('channel', 0))

        if not text:
            return render_template(
                "send_result.html",
                success=False,
                message="Message cannot be empty"
            ), 400

        # Handle broadcast
        if destination == 'broadcast':
            destination = None

        result = asyncio.run(commander.send_text(text, destination, channel))

        return render_template(
            "send_result.html",
            success=result.success,
            message=result.message,
            error=result.error
        )

    # ==================== Telemetry Routes ====================

    @app.route("/telemetry/<node_id>")
    def telemetry_page(node_id: str):
        """Telemetry dashboard for a specific node"""
        return render_template("telemetry.html", node_id=node_id)

    @app.route("/api/telemetry/<node_id>/<metric>")
    def api_telemetry_metric(node_id: str, metric: str):
        """Get time-series data for a metric"""
        telemetry_service = app.config['TELEMETRY_SERVICE']

        hours = int(request.args.get('hours', 24))
        since = datetime.now(timezone.utc) - timedelta(hours=hours)

        data_points = asyncio.run(
            telemetry_service.get_time_series(node_id, metric, since)
        )

        return jsonify({
            "metric": metric,
            "node_id": node_id,
            "data": [
                {
                    "timestamp": dp.timestamp.isoformat(),
                    "value": dp.value,
                }
                for dp in data_points
            ]
        })

    @app.route("/api/telemetry/<node_id>/all")
    def api_telemetry_all(node_id: str):
        """Get all telemetry metrics for a node"""
        telemetry_service = app.config['TELEMETRY_SERVICE']

        hours = int(request.args.get('hours', 24))
        since = datetime.now(timezone.utc) - timedelta(hours=hours)

        metrics = asyncio.run(
            telemetry_service.get_all_metrics(node_id, since)
        )

        return jsonify({
            metric_name: [
                {
                    "timestamp": dp.timestamp.isoformat(),
                    "value": dp.value,
                }
                for dp in data_points
            ]
            for metric_name, data_points in metrics.items()
        })

    # ==================== Node Details Route ====================

    @app.route("/node/<node_id>")
    def node_details(node_id: str):
        """Detailed view of a specific node"""
        state_store = app.config['STATE_STORE']
        msg_service = app.config['MESSAGE_SERVICE']

        from meshcore.domain.models import NodeId
        node_state = asyncio.run(state_store.get_node(NodeId(value=node_id)))

        if not node_state:
            return "Node not found", 404

        # Get recent messages from this node
        messages = asyncio.run(
            msg_service.get_messages_by_node(node_id, limit=20)
        )

        return render_template(
            "node_details.html",
            node=node_state,
            messages=messages
        )

    # ==================== Analytics Route ====================

    @app.route("/analytics")
    def analytics_page():
        """Analytics dashboard"""
        state_store = app.config['STATE_STORE']
        msg_service = app.config['MESSAGE_SERVICE']

        nodes = asyncio.run(state_store.list_nodes())
        messages = asyncio.run(msg_service.get_recent_messages(limit=1000))

        # Calculate statistics
        total_messages = len(messages)
        now = datetime.now(timezone.utc)
        messages_24h = len([
            m for m in messages
            if (now - m.timestamp).total_seconds() < 86400
        ])

        # Messages per node
        msg_counts = {}
        for msg in messages:
            msg_counts[msg.from_node] = msg_counts.get(msg.from_node, 0) + 1

        top_senders = sorted(
            msg_counts.items(), key=lambda x: x[1], reverse=True
        )[:10]

        return render_template(
            "analytics.html",
            nodes=nodes,
            total_messages=total_messages,
            messages_24h=messages_24h,
            top_senders=top_senders
        )

    # ==================== SSE Route ====================

    @app.route("/stream/events")
    def stream_events():
        """Server-Sent Events stream for real-time updates"""
        def event_stream():
            # Send initial connection message
            msg = "Connected to event stream"
            yield f"data: {{'type': 'connected', 'message': '{msg}'}}\n\n"

            # In a real implementation, subscribe to MQTT or events
            # For now, we'll send periodic keepalives
            import time
            while True:
                time.sleep(30)
                ts = datetime.now(timezone.utc).isoformat()
                yield f"data: {{'type': 'keepalive', 'timestamp': '{ts}'}}\n\n"

        return Response(event_stream(), mimetype="text/event-stream")

    # ==================== JSON API Routes ====================

    @app.route("/api/nodes")
    def api_nodes():
        """JSON API endpoint for nodes"""
        state_store = app.config['STATE_STORE']
        nodes = asyncio.run(state_store.list_nodes())
        return jsonify([
            {
                "node_id": node.node_id.value,
                "last_seen": node.last_seen.isoformat(),
                "first_seen": node.first_seen.isoformat(),
                "event_count": node.event_count,
                "last_telemetry": node.last_telemetry,
                "last_position": node.last_position,
                "last_text": node.last_text,
            }
            for node in nodes
        ])

    # ==================== Template Filters ====================

    @app.template_filter("timeago")
    def timeago_filter(dt: datetime) -> str:
        """Convert datetime to relative time ago"""
        if not dt:
            return "Never"

        now = datetime.now(timezone.utc)
        diff = now - dt

        seconds = diff.total_seconds()
        if seconds < 60:
            return f"{int(seconds)}s ago"
        elif seconds < 3600:
            return f"{int(seconds / 60)}m ago"
        elif seconds < 86400:
            return f"{int(seconds / 3600)}h ago"
        else:
            return f"{int(seconds / 86400)}d ago"

    @app.template_filter("format_datetime")
    def format_datetime(dt: datetime) -> str:
        """Format datetime for display"""
        if not dt:
            return "-"
        return dt.strftime("%Y-%m-%d %H:%M:%S")

    @app.template_filter("format_temp")
    def format_temp(telemetry: dict | None) -> str:
        """Format temperature from telemetry"""
        if not telemetry:
            return "-"
        temp = telemetry.get("temperature")
        if temp is None:
            return "-"
        return f"{temp:.1f}°C"

    @app.template_filter("format_battery")
    def format_battery(telemetry: dict | None) -> str:
        """Format battery level from telemetry"""
        if not telemetry:
            return "-"
        battery = telemetry.get("battery_level")
        if battery is None:
            return "-"
        return f"{battery}%"

    @app.template_filter("format_position")
    def format_position(position: dict | None) -> str:
        """Format position coordinates"""
        if not position:
            return "-"
        lat = position.get("latitude")
        lon = position.get("longitude")
        if lat is None or lon is None:
            return "-"
        return f"{lat:.4f}, {lon:.4f}"

    @app.template_filter("truncate_text")
    def truncate_text(text: str | None, length: int = 50) -> str:
        """Truncate text to specified length"""
        if not text:
            return "-"
        if len(text) <= length:
            return text
        return text[:length] + "..."

    @app.template_filter("status_class")
    def status_class(last_seen: datetime) -> str:
        """Return CSS class based on how recent the last seen time is"""
        now = datetime.now(timezone.utc)
        diff = (now - last_seen).total_seconds()

        if diff < 60:
            return "status-active"
        elif diff < 300:
            return "status-recent"
        elif diff < 3600:
            return "status-idle"
        else:
            return "status-offline"

    return app
