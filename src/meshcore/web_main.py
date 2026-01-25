"""Web UI entry point"""

from meshcore.adapters.ui.web import create_app


def main():
    """Run the web server"""
    app = create_app()
    print("MeshCore Web UI starting...")
    print("Dashboard: http://localhost:5000")
    print("API: http://localhost:5000/api/nodes")
    print("Press Ctrl+C to stop")
    app.run(host="0.0.0.0", port=5000, debug=False)


if __name__ == "__main__":
    main()

