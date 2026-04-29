"""Web API driver for Smart Agent Wiki.

Provides FastAPI-based REST API and WebSocket support for real-time updates.
"""
from saw.drivers.web.app import create_app

__all__ = ["create_app"]
