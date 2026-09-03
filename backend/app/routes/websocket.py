"""
FinGraph WebSocket & Real-Time Endpoints.
Provides live event streaming to connected React dashboards and status inspection.
"""
import asyncio
import json
import logging
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status

from backend.app.config import get_api_config
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
):
    """Processes bidirectional WebSocket session."""
    client_host = websocket.client.host if websocket.client else "unknown"
    accepted = await manager.connect(websocket, client_info={"host": client_host})
    if not accepted:
        return

    # Send initial connection acknowledgment
    welcome_event = create_realtime_event(
        EventType.SYSTEM_PONG,
        {
            "connected": True,
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
                    manager.set_client_subscriptions(websocket, channels=channels)
                    ack = create_realtime_event(
                        EventType.SYSTEM_PONG,
                        {"subscribed_channels": list(channels)},
                    )
                    await websocket.send_text(json.dumps(ack.to_json_dict()))

                elif action == "watch_account":
                    acc_id = msg.get("account_id")
                    if acc_id:
                        manager.set_client_subscriptions(websocket, watch_account=acc_id)
                        ack = create_realtime_event(
                            EventType.SYSTEM_PONG,
                            {"watching_account": acc_id},
                        )
                        await websocket.send_text(json.dumps(ack.to_json_dict()))

                else:
                    # Echo unknown action safely
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
    except Exception as exc:
        logger.debug(f"WebSocket session closed with exception: {exc}")
        await manager.disconnect(websocket)


@router.websocket("/api/v1/ws")
async def websocket_v1_endpoint(
    websocket: WebSocket,
    manager: WebSocketConnectionManager = Depends(get_connection_manager),
):
    """Primary versioned WebSocket connection route."""
    await handle_websocket_session(websocket, manager)


@router.websocket("/ws")
async def websocket_legacy_endpoint(
    websocket: WebSocket,
    manager: WebSocketConnectionManager = Depends(get_connection_manager),
):
    """Unversioned WebSocket alias route."""
    await handle_websocket_session(websocket, manager)
