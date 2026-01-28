"""Web UI entry point with proper logging"""

import logging

from meshcore.adapters.ui.web import create_app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Run the web server"""
    app = create_app()
    logger.info("MeshCore Web UI starting...")
    logger.info("Dashboard: http://localhost:5000")
    logger.info("API: http://localhost:5000/api/nodes")
    logger.info("Press Ctrl+C to stop")
    try:
        app.run(host="0.0.0.0", port=5000, debug=False)
    except KeyboardInterrupt:
        logger.info("\nShutting down web server...")
    except Exception as e:
        logger.error(f"Web server error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
