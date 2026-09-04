"""
FinGraph WebSocket & Real-Time Endpoints.
Provides authenticated live event streaming to connected React dashboards and status inspection.
"""
import asyncio
import json
import logging
from typing import Optional
from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect, status

from backend.app.config import get_api_config
from backend.app.metrics.prometheus import get_metrics
from backend.app.realtime.connection_manager import (
    WebSocketConnectionManager,
    get_connection_manager,
)
from backend.app.realtime.event_bus import EventBus, get_event_bus
from backend.app.realtime.events import EventType, create_realtime_event
from backend.app.realtime.kafka_consumer import (
    RealtimeKafkaConsumer,
    get_realtime_kafka_consumer,
)
from backend.app.security.jwt import decode_access_token
from backend.app.security.user_store import UserStore, get_user_store

logger = logging.getLogger("FinGraph.WebSocketRouter")
router = APIRouter(tags=["Realtime"])


@router.get("/health/realtime")
def realtime_health_check(
    manager: WebSocketConnectionManager = Depends(get_connection_manager),
    consumer: RealtimeKafkaConsumer = Depends(get_realtime_kafka_consumer),
    bus: EventBus = Depends(get_event_bus),
):
    """Returns telemetry and health status for the real-time event pipeline."""
    cfg = get_api_config()
    return {
        "status": "ok",
        "enabled": cfg.realtime_enabled,
        "connected_clients": manager.active_connections_count,
        "max_clients": cfg.realtime_max_clients,
        "event_consumer": "connected" if consumer.is_connected else "offline_or_simulated",
        "metrics": {
            "bus": bus.metrics,
            "manager": manager.metrics,
            "consumer": consumer.metrics,
        },
    }


async def handle_websocket_session(
    websocket: WebSocket,
    manager: WebSocketConnectionManager,
    token: Optional[str] = None,
):
    """Processes bidirectional authenticated WebSocket session."""
    # 1. Authenticate WebSocket Connection
    query_token = token or websocket.query_params.get("token")
    if not query_token and "authorization" in websocket.headers:
        auth_hdr = websocket.headers["authorization"]
        if auth_hdr.lower().startswith("bearer "):
            query_token = auth_hdr[7:].strip()

    user = None
    if query_token:
        claims = decode_access_token(query_token)
        if claims and "sub" in claims:
            user_store = get_user_store()
            user = user_store.get_user_by_id(claims["sub"]) or user_store.get_user_by_username(claims.get("username", ""))

    # If unauthenticated, close connection with 1008 (Policy Violation)
    if not user or not user.is_active:
        logger.warning("Rejected unauthenticated WebSocket connection attempt.")
        await websocket.close(code=1008, reason="Authentication required. Provide valid JWT token.")
        return

    client_host = websocket.client.host if websocket.client else "unknown"
    accepted = await manager.connect(
        websocket,
        client_info={"host": client_host, "user_id": user.user_id, "role": user.role.value},
    )
    if not accepted:
        return

    metrics = get_metrics()
    metrics.set_active_ws_connections(manager.active_connections_count)

    # Send initial connection acknowledgment
    welcome_event = create_realtime_event(
        EventType.SYSTEM_PONG,
        {
            "connected": True,
            "authenticated_as": user.username,
            "role": user.role.value,
            "message": "Connected to FinGraph Real-Time Investigation Stream",
            "active_clients": manager.active_connections_count,
        },
    )
    await websocket.send_text(json.dumps(welcome_event.to_json_dict()))

    try:
        while True:
            text = await websocket.receive_text()
            try:
                msg = json.loads(text)
                action = msg.get("action")

                if action == "ping":
                    pong = create_realtime_event(EventType.SYSTEM_PONG, {"pong": True})
                    await websocket.send_text(json.dumps(pong.to_json_dict()))

                elif action == "subscribe":
                    channels = msg.get("channels", [])
                    # Validate channel names
                    valid_channels = {"alerts", "risk", "transactions", "graph", "all"}
                    filtered_channels = [c for c in channels if c in valid_channels]
                    manager.set_client_subscriptions(websocket, channels=filtered_channels)
                    ack = create_realtime_event(
                        EventType.SYSTEM_PONG,
                        {"subscribed_channels": filtered_channels},
                    )
                    await websocket.send_text(json.dumps(ack.to_json_dict()))

                elif action == "watch_account":
                    acc_id = msg.get("account_id")
                    if acc_id and isinstance(acc_id, str) and len(acc_id) <= 64:
                        manager.set_client_subscriptions(websocket, watch_account=acc_id)
                        ack = create_realtime_event(
                            EventType.SYSTEM_PONG,
                            {"watching_account": acc_id},
                        )
                        await websocket.send_text(json.dumps(ack.to_json_dict()))

                else:
                    err = create_realtime_event(
                        EventType.ERROR,
                        {"code": "UNKNOWN_ACTION", "message": f"Action '{action}' is not supported."},
                    )
                    await websocket.send_text(json.dumps(err.to_json_dict()))

            except json.JSONDecodeError:
                err = create_realtime_event(
                    EventType.ERROR,
                    {"code": "INVALID_JSON", "message": "Expected valid JSON payload."},
                )
                await websocket.send_text(json.dumps(err.to_json_dict()))

    except WebSocketDisconnect:
        await manager.disconnect(websocket)
        metrics.set_active_ws_connections(manager.active_connections_count)
    except Exception as exc:
        logger.debug(f"WebSocket session closed with exception: {exc}")
        await manager.disconnect(websocket)
        metrics.set_active_ws_connections(manager.active_connections_count)


@router.websocket("/api/v1/ws")
async def websocket_v1_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
    manager: WebSocketConnectionManager = Depends(get_connection_manager),
):
    """Primary authenticated versioned WebSocket connection route."""
    await handle_websocket_session(websocket, manager, token=token)


@router.websocket("/ws")
async def websocket_legacy_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
    manager: WebSocketConnectionManager = Depends(get_connection_manager),
):
    """Authenticated legacy WebSocket alias route."""
    await handle_websocket_session(websocket, manager, token=token)
