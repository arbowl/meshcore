"""Custom widgets for the TUI"""

from datetime import datetime

from textual.widgets import DataTable, Static


class NodeTable(DataTable):
    """Data table showing node states"""

    def __init__(self) -> None:
        super().__init__()
        self.cursor_type = "row"

    def on_mount(self) -> None:
        self.add_columns(
            "Node ID",
            "Last Seen",
            "Events",
            "Battery",
            "Temp",
            "Position",
            "Last Text",
        )

    def update_nodes(self, nodes: list) -> None:
        self.clear()
        for node in nodes:
            battery = ""
            temp = ""
            if node.last_telemetry:
                battery = f"{node.last_telemetry.get('battery', 'N/A')}"
                temp = f"{node.last_telemetry.get('temperature', 'N/A')}"
            position = ""
            if node.last_position:
                lat = node.last_position.get('lat', 0)
                lon = node.last_position.get('lon', 0)
                position = f"{lat:.4f}, {lon:.4f}"
            last_seen = self._format_time_ago(node.last_seen)
            self.add_row(
                node.node_id.value,
                last_seen,
                str(node.event_count),
                battery,
                temp,
                position,
                node.last_text or "",
            )

    def _format_time_ago(self, timestamp: datetime) -> str:
        now = datetime.now(timestamp.tzinfo)
        delta = now - timestamp
        if delta.total_seconds() < 60:
            return f"{int(delta.total_seconds())}s ago"
        elif delta.total_seconds() < 3600:
            return f"{int(delta.total_seconds() / 60)}m ago"
        elif delta.total_seconds() < 86400:
            return f"{int(delta.total_seconds() / 3600)}h ago"
        else:
            return f"{int(delta.total_seconds() / 86400)}d ago"


class StatusBar(Static):
    """Status bar showing app info"""

    def update_status(self, node_count: int, last_update: datetime) -> None:
        time_str = last_update.strftime("%H:%M:%S")
        self.update(f"Nodes: {node_count} | Last Update: {time_str} | Press Q to quit, R to refresh")

