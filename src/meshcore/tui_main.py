"""TUI entry point"""

from meshcore.adapters.storage.state_sqlite import SqliteStateStore
from meshcore.adapters.ui.tui import MeshTUI


def main() -> None:
    state_store = SqliteStateStore()
    app = MeshTUI(state_store)
    app.run()


if __name__ == "__main__":
    main()

