"""
FinGraph Asynchronous Event Bus.
Decoupled pub/sub event dispatcher routing real-time pipeline signals to WebSocket managers.
"""
import asyncio
import collections
import logging
from typing import Any, Callable, Coroutine, Deque, Dict, List, Optional
from backend.app.realtime.events import RealtimeEvent

logger = logging.getLogger("FinGraph.EventBus")


class EventBus:
    """In-memory async publish-subscribe event bus."""

    def __init__(self, history_size: int = 200):
        self._subscribers: Dict[str, Callable[[RealtimeEvent], Coroutine[Any, Any, None]]] = {}
        self._history: Deque[RealtimeEvent] = collections.deque(maxlen=history_size)
        self._published_count: int = 0
        self._failed_count: int = 0
        self._lock = asyncio.Lock()

    def subscribe(
        self,
        subscriber_id: str,
        callback: Callable[[RealtimeEvent], Coroutine[Any, Any, None]],
    ) -> None:
        """Registers an async event handler callback."""
        self._subscribers[subscriber_id] = callback
        logger.debug(f"Subscriber registered: {subscriber_id} (Total: {len(self._subscribers)})")

    def unsubscribe(self, subscriber_id: str) -> None:
        """Unregisters an event handler callback."""
        if subscriber_id in self._subscribers:
            del self._subscribers[subscriber_id]
            logger.debug(f"Subscriber removed: {subscriber_id}")

    async def publish(self, event: RealtimeEvent) -> None:
        """Dispatches an event concurrently to all active subscribers."""
        self._published_count += 1
        self._history.append(event)

        if not self._subscribers:
            return

        handlers = list(self._subscribers.values())
        coros = []
        for handler in handlers:
            coros.append(self._safe_invoke(handler, event))

        await asyncio.gather(*coros, return_exceptions=True)

    async def _safe_invoke(
        self,
        handler: Callable[[RealtimeEvent], Coroutine[Any, Any, None]],
        event: RealtimeEvent,
    ) -> None:
        """Invokes a single handler with error isolation."""
        try:
            await handler(event)
        except Exception as exc:
            self._failed_count += 1
            logger.warning(f"Error dispatching event {event.event_id} ({event.event}): {exc}")

    def get_recent_events(self, limit: int = 50) -> List[RealtimeEvent]:
        """Returns snapshot of recently published events."""
        return list(self._history)[-limit:]

    @property
    def metrics(self) -> Dict[str, Any]:
        """Returns event bus telemetry."""
        return {
            "subscribers_count": len(self._subscribers),
            "events_published": self._published_count,
            "events_failed": self._failed_count,
            "history_buffered": len(self._history),
        }


# Global Singleton
_global_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Returns the singleton EventBus instance."""
    global _global_event_bus
    if _global_event_bus is None:
        _global_event_bus = EventBus()
    return _global_event_bus
