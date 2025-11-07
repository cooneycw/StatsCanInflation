#!/usr/bin/env python3
"""
Statistics Canada Inflation Analysis - Shiny Application

Main entry point for both local development and production deployment.

For local development: python main.py
For deployment: rsconnect deploy shiny . --entrypoint main:app --title stats_can_inflation
"""

import sys
import logging
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent))

from shiny import App
from src.ui.app_ui import app_ui
from src.server.app_server import server

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create the Shiny app
app = App(app_ui, server)


def main():
    """
    Run the Shiny app locally for development.
    """
    logger.info("Starting Statistics Canada Inflation Analysis application...")
    logger.info("App will be available at: http://127.0.0.1:8000")

    app.run(
        host="127.0.0.1",
        port=8000,
        reload=False,
        log_level="info"
    )


if __name__ == "__main__":
    main()
