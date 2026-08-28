"""In-process async event bus (pub/sub).

HI-2: the application defined an event-bus contract — ``app.state.event_bus``,
``WorkflowExecutor._event_bus``, ``ConnectionManager.set_event_bus`` — but
never provided an implementation. The bus was always ``None``, so:

* workflow progress events (``WorkflowStarted``/``WorkflowStep``/
  ``WorkflowCompleted``) were dropped at ``workflow_executor.py:_publish_event``;
* the WebSocket broadcaster's ``start_broadcaster`` returned immediately
  (``websocket.py:_broadcast_loop`` was never entered);
* plugin events (``plugins/events.py``) had no delivery mechanism.

This module is the minimal in-memory async bus that activates all three.
Publishers call ``await bus.publish(event)`` (async callers) or
``bus.publish_nowait(event)`` (sync callers such as the Write Queue
dispatcher). Subscribers iterate ``async for event in bus.subscribe()`` (the
WebSocket manager) or register a callback via ``bus.add_subscriber(type, fn)``
(future plugin/ engine hooks).

Events may be plain dicts (``{"type": "WorkflowStep", ...}`` — what
``WorkflowExecutor`` and the dispatcher emit) or dataclass instances (domain /
plugin events). The WebSocket manager normalizes both.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, AsyncIterator, Callable


logger = logging.getLogger(__name__)


class InMemoryEventBus:
    """Async in-process pub/sub event bus."""

    def __init__(self, max_queue: int = 512) -> None:
        self._subscribers: list[asyncio.Queue] = []
        self._handlers: list[tuple[str | None, Callable[[Any], None]]] = []
        self._max_queue = max_queue

    # ── Publish ────────────────────────────────────────────────────────

    def _event_name(self, event: Any) -> str:
        if isinstance(event, dict):
            return str(event.get("type") or "unknown")
        return type(event).__name__

    def _dispatch(self, event: Any) -> None:
        """Fan an event out to all queue subscribers + matching handlers."""
        for q in list(self._subscribers):
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                # F-PLUG-02: a slow subscriber must not stall the publisher, but
                # log the drop instead of swallowing it silently.
                logger.warning("Event '%s' dropped: subscriber queue full", name)
        name = self._event_name(event)
        for etype, handler in list(self._handlers):
            if etype is None or etype == name:
                try:
                    handler(event)
                except Exception:
                    # F-PLUG-02: a faulty handler must not break other
                    # subscribers, but log it instead of hiding it.
                    logger.warning("Event handler raised for '%s'", name, exc_info=True)

    async def publish(self, event: Any) -> None:
        """Publish an event (async callers, e.g. WorkflowExecutor)."""
        self._dispatch(event)

    def publish_nowait(self, event: Any) -> None:
        """Publish an event from a sync context (e.g. Write Queue dispatcher)."""
        self._dispatch(event)

    # ── Subscribe ──────────────────────────────────────────────────────

    def subscribe(self) -> "_Subscription":
        """Return an async iterator yielding every published event.

        Used by the WebSocket ``ConnectionManager._broadcast_loop``:
        ``async for event in bus.subscribe(): ...``.
        """
        q: asyncio.Queue = asyncio.Queue(maxsize=self._max_queue)
        self._subscribers.append(q)
        return _Subscription(self, q)

    def add_subscriber(
        self, event_type: str | None, handler: Callable[[Any], None]
    ) -> None:
        """Register a sync callback for events matching ``event_type``.

        ``event_type=None`` subscribes to all events. Used by plugins/engines
        (``PluginContext.subscribe_event`` in HI-4 will bind here). Handlers
        run on the publisher's thread — keep them cheap or schedule a task.
        """
        self._handlers.append((event_type, handler))

    def remove_subscriber(self, handler: Callable[[Any], None]) -> None:
        try:
            self._handlers = [(t, h) for t, h in self._handlers if h is not handler]
        except Exception:
            pass

    def _remove_queue(self, q: asyncio.Queue) -> None:
        try:
            self._subscribers.remove(q)
        except ValueError:
            pass


class _Subscription:
    """Async-iterator view over a single subscriber's queue."""

    def __init__(self, bus: InMemoryEventBus, q: asyncio.Queue) -> None:
        self._bus = bus
        self._q = q

    def __aiter__(self) -> AsyncIterator[Any]:
        return self

    async def __anext__(self) -> Any:
        try:
            return await self._q.get()
        except asyncio.CancelledError:
            self._bus._remove_queue(self._q)
            raise
