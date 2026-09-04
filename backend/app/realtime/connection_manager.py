"""
FinGraph WebSocket Connection Manager.
Manages active WebSocket sessions, client subscription filters, heartbeats, and reliable multi-client event broadcasting.
"""
import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set
from fastapi import WebSocket, WebSocketDisconnect

from backend.app.realtime.event_bus import EventBus, get_event_bus
from backend.app.realtime.events import EventType, RealtimeEvent, create_realtime_event

logger = logging.getLogger("FinGraph.ConnectionManager")


class WebSocketConnectionManager:
    """Manages active WebSocket client connections and broadcasts real-time events."""

    def __init__(
        self,
        event_bus: Optional[EventBus] = None,
        max_clients: int = 100,
        heartbeat_interval: int = 30,
    ):
        self.event_bus = event_bus or get_event_bus()
        self.max_clients = max_clients
        self.heartbeat_interval = heartbeat_interval
        self._connections: Dict[WebSocket, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._total_broadcast_count: int = 0
        self._failed_broadcast_count: int = 0

        # Subscribe connection manager to event bus
        self.event_bus.subscribe("ws_connection_manager", self._on_bus_event)

    async def start(self) -> None:
        """Starts background heartbeat sender."""
        if self._heartbeat_task is None or self._heartbeat_task.done():
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            logger.info("WebSocket Connection Manager started with heartbeat.")

    async def stop(self) -> None:
        """Closes all active WebSocket connections and cancels background tasks."""
        if self._heartbeat_task and not self._heartbeat_task.done():
            self._heartbeat_task.cancel()

        async with self._lock:
            sockets = list(self._connections.keys())
            for ws in sockets:
                try:
                    await ws.close(code=1000, reason="Server shutting down")
                except Exception:
                    pass
            self._connections.clear()
        logger.info("WebSocket Connection Manager stopped.")

    async def connect(self, websocket: WebSocket, client_info: Optional[Dict[str, Any]] = None) -> bool:
        """Accepts a new WebSocket connection if within capacity limits."""
        async with self._lock:
            if len(self._connections) >= self.max_clients:
                logger.warning(f"Connection rejected: Max capacity ({self.max_clients}) reached.")
                await websocket.close(code=1008, reason="Max concurrent connections reached")
                return False
            await websocket.accept()
            info = client_info or {}
            self._connections[websocket] = {
                "connected_at": datetime.now(timezone.utc),
                "client_info": info,
                "tenant_id": info.get("tenant_id", "tnt_default"),
                "is_platform_admin": info.get("is_platform_admin", False) or info.get("role") == "PLATFORM_ADMIN",
                "channels": {"all", "alerts", "risk", "transactions", "graph"},
                "watched_accounts": set(),
            }
            logger.info(f"WebSocket client connected. Active: {len(self._connections)}")
            return True

    async def disconnect(self, websocket: WebSocket) -> None:
        """Removes a disconnected client."""
        async with self._lock:
            if websocket in self._connections:
                del self._connections[websocket]
                logger.info(f"WebSocket client disconnected. Active: {len(self._connections)}")

    def set_client_subscriptions(
        self,
        websocket: WebSocket,
        channels: Optional[List[str]] = None,
        watch_account: Optional[str] = None,
    ) -> None:
        """Updates channel or account filters for a client session."""
        if websocket in self._connections:
            if channels:
                self._connections[websocket]["channels"] = set(channels).union({"all"})
            if watch_account:
                self._connections[websocket]["watched_accounts"].add(watch_account)

    async def _on_bus_event(self, event: RealtimeEvent) -> None:
        """Callback invoked whenever an event is published to the EventBus."""
        await self.broadcast(event)

    async def broadcast(self, event: RealtimeEvent) -> None:
        """Broadcasts an event envelope to matching connected clients respecting tenant isolation."""
        self._total_broadcast_count += 1
        payload_str = json.dumps(event.to_json_dict())

        stale_sockets: List[WebSocket] = []

        async with self._lock:
            sockets = list(self._connections.items())

        for ws, meta in sockets:
            # 1. Check Tenant Isolation: If event is tenant-scoped, only send to matching tenant or platform admin
            if event.tenant_id and event.tenant_id != "GLOBAL":
                client_tenant = meta.get("tenant_id", "tnt_default")
                is_plat_admin = meta.get("is_platform_admin", False)
                if not is_plat_admin and client_tenant != event.tenant_id:
                    continue

            # 2. Check channel filtering
            evt_category = event.event.value.split(".")[0]
            if "all" not in meta["channels"] and evt_category not in meta["channels"]:
                continue

            # 3. Check account filter if applicable
            data_dict = event.data if isinstance(event.data, dict) else (
                event.data.model_dump(mode="json") if hasattr(event.data, "model_dump") else {}
            )
            evt_account = data_dict.get("account_id") or data_dict.get("primary_account")
            if meta["watched_accounts"] and evt_account and evt_account not in meta["watched_accounts"]:
                continue

            try:
                await ws.send_text(payload_str)
            except (WebSocketDisconnect, RuntimeError, Exception) as exc:
                self._failed_broadcast_count += 1
                logger.debug(f"Failed send to client, marking for cleanup: {exc}")
                stale_sockets.append(ws)

        # Cleanup disconnected clients
        if stale_sockets:
            async with self._lock:
                for ws in stale_sockets:
                    if ws in self._connections:
                        del self._connections[ws]

    async def _heartbeat_loop(self) -> None:
        """Sends periodic ping heartbeat to keep connections alive and detect stale sessions."""
        while True:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                ping_event = create_realtime_event(
                    EventType.SYSTEM_PING,
                    {"ping": True, "active_clients": len(self._connections)},
                )
                await self.broadcast(ping_event)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.warning(f"Heartbeat loop error: {exc}")

    @property
    def active_connections_count(self) -> int:
        return len(self._connections)

    @property
    def metrics(self) -> Dict[str, Any]:
        return {
            "active_connections": len(self._connections),
            "max_clients": self.max_clients,
            "broadcasts_total": self._total_broadcast_count,
            "broadcasts_failed": self._failed_count if hasattr(self, "_failed_count") else self._failed_broadcast_count,
        }


# Global Singleton
_global_connection_manager: Optional[WebSocketConnectionManager] = None


def get_connection_manager() -> WebSocketConnectionManager:
    """Returns the singleton WebSocketConnectionManager instance."""
    global _global_connection_manager
    if _global_connection_manager is None:
        _global_connection_manager = WebSocketConnectionManager()
    return _global_connection_manager
