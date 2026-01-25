"""TUI application for monitoring mesh network"""

import asyncio
from datetime import datetime

from textual.app import App, ComposeResult
from textual.widgets import Footer, Header

from meshcore.adapters.ui.widgets import NodeTable, StatusBar
from meshcore.application.ports import StateStore


class MeshTUI(App):
    """Textual app for monitoring mesh network state"""

    CSS = """
    Screen {
        background: $surface;
    }
    NodeTable {
        height: 1fr;
        border: solid $primary;
    }
    StatusBar {
        dock: bottom;
        height: 1;
        background: $primary;
        color: $text;
        content-align: center middle;
    }
    """
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
    ]

    def __init__(self, state_store: StateStore) -> None:
        super().__init__()
        self._state_store = state_store
        self._refresh_interval = 2.0

    def compose(self) -> ComposeResult:
        yield Header()
        yield NodeTable()
        yield StatusBar()
        yield Footer()

    async def on_mount(self) -> None:
        self.title = "MeshCore TUI"
        self.sub_title = "Mesh Network Monitor"
        self.set_interval(self._refresh_interval, self.refresh_data)
        await self.refresh_data()

    async def refresh_data(self) -> None:
        nodes = await self._state_store.list_nodes()
        table = self.query_one(NodeTable)
        status = self.query_one(StatusBar)
        table.update_nodes(nodes)
        status.update_status(len(nodes), datetime.now())

    def action_refresh(self) -> None:
        asyncio.create_task(self.refresh_data())

