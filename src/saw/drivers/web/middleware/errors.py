"""RFC 7807 Problem Details error handlers.

Per RESEARCH.md Pattern 5: Unified error response format.
Per T-03-02-04: No stack traces in production error responses.
"""
import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from saw.domain.exceptions import (
    SAWError,
    StorageError,
    VaultError,
    ClaimsDBError,
    FTS5Error,
    WriteQueueError,
    ConfigError,
    ConnectorError,
    AuthenticationError,
    RateLimitError,
    PipelineError,
    LLMError,
)

# Map exception types to HTTP status codes.
# More specific exceptions are checked first via MRO in the handler.
_ERROR_STATUS_MAP: dict[type[SAWError], int] = {
    AuthenticationError: 401,
    RateLimitError: 429,
    PipelineError: 422,
    StorageError: 503,
    VaultError: 503,
    ClaimsDBError: 503,
    FTS5Error: 503,
    WriteQueueError: 503,
    LLMError: 503,
    ConnectorError: 502,
    ConfigError: 500,
}


def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers for consistent error responses.

    Per D-03: All errors return RFC 7807 Problem Details format.

    Args:
        app: FastAPI application to register handlers on.
    """

    @app.exception_handler(SAWError)
    async def saw_error_handler(request: Request, exc: SAWError) -> JSONResponse:
        """Handle Smart Agent Wiki domain exceptions.

        Args:
            request: The request that caused the exception.
            exc: The domain exception.

        Returns:
            RFC 7807 formatted error response.
        """
        # Walk the MRO to find the most specific mapped exception type.
        http_status = 400
        for cls in type(exc).__mro__:
            if cls in _ERROR_STATUS_MAP:
                http_status = _ERROR_STATUS_MAP[cls]
                break

        return JSONResponse(
            status_code=http_status,
            content={
                "type": "https://smart-agent.wiki/errors/business",
                "title": exc.__class__.__name__,
                "status": http_status,
                "detail": str(exc),
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Handle Pydantic validation errors.

        Args:
            request: The request that failed validation.
            exc: The validation error.

        Returns:
            RFC 7807 formatted validation error response.
        """
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "type": "https://smart-agent.wiki/errors/validation",
                "title": "Request validation failed",
                "status": 422,
                "detail": exc.errors(),
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        """Reshape HTTPException (raised pervasively by routes) to RFC 7807.

        M-6: previously FastAPI's built-in handler returned ``{"detail": ...}``,
        producing two incompatible error schemas. For 5xx the detail is masked
        (routes interpolate ``{e}`` into 500 messages, leaking internals);
        4xx detail is preserved (useful, client-facing).
        """
        if exc.status_code >= 500:
            logging.exception(
                "HTTP %d in %s: %s", exc.status_code, request.url, exc.detail
            )
            detail = "An internal error occurred"
        else:
            detail = exc.detail if isinstance(exc.detail, str) else "Bad request"
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "type": f"https://smart-agent.wiki/errors/http-{exc.status_code}",
                "title": exc.__class__.__name__,
                "status": exc.status_code,
                "detail": detail,
            },
        )

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle unexpected exceptions.

        Per T-03-02-04: No stack traces in production.

        Args:
            request: The request that caused the exception.
            exc: The unexpected exception.

        Returns:
            RFC 7807 formatted internal error response.
        """
        # Log the full exception for debugging
        logging.exception("Unhandled exception in request %s", request.url)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "type": "https://smart-agent.wiki/errors/internal",
                "title": "Internal server error",
                "status": 500,
                "detail": "An unexpected error occurred",
            },
        )