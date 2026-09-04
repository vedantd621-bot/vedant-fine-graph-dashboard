"""
FinGraph Real-Time Package Forwarder.
"""
from backend.app.realtime.events import (
    EventType,
    RealtimeEvent,
    AlertCreatedPayload,
    AlertUpdatedPayload,
    RiskUpdatedPayload,
    TransactionCreatedPayload,
    GraphUpdatedPayload,
    ErrorPayload,
    create_realtime_event,
)
from backend.app.realtime.event_bus import EventBus, get_event_bus
from backend.app.realtime.connection_manager import (
    WebSocketConnectionManager,
    get_connection_manager,
)
from backend.app.realtime.kafka_consumer import (
    RealtimeKafkaConsumer,
    get_realtime_kafka_consumer,
)

__all__ = [
    "EventType",
    "RealtimeEvent",
    "AlertCreatedPayload",
    "AlertUpdatedPayload",
    "RiskUpdatedPayload",
    "TransactionCreatedPayload",
    "GraphUpdatedPayload",
    "ErrorPayload",
    "create_realtime_event",
    "EventBus",
    "get_event_bus",
    "WebSocketConnectionManager",
    "get_connection_manager",
    "RealtimeKafkaConsumer",
    "get_realtime_kafka_consumer",
]
