"""Web API middleware package."""
from saw.drivers.web.middleware.cors import get_cors_origins
from saw.drivers.web.middleware.errors import register_exception_handlers

__all__ = ["get_cors_origins", "register_exception_handlers"]
