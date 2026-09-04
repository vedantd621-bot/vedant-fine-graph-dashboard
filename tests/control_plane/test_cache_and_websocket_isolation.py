import asyncio
import pytest
from backend.app.realtime.connection_manager import WebSocketConnectionManager
from backend.app.realtime.events import EventType, create_realtime_event

def test_websocket_tenant_filtering():
    async def _test():
        mgr = WebSocketConnectionManager()
        
        # Simulate two mock websockets
        class MockWS:
            def __init__(self):
                self.sent = []
            async def accept(self):
                pass
            async def send_text(self, text):
                self.sent.append(text)

        ws_a = MockWS()
        ws_b = MockWS()

        await mgr.connect(ws_a, client_info={"tenant_id": "tnt_alpha", "is_platform_admin": False})
        await mgr.connect(ws_b, client_info={"tenant_id": "tnt_beta", "is_platform_admin": False})

        # Broadcast event scoped strictly to tnt_alpha
        evt_a = create_realtime_event(EventType.ALERT_CREATED, {"alert_id": "ALT-A"}, tenant_id="tnt_alpha")
        await mgr.broadcast(evt_a)

        assert len(ws_a.sent) == 1
        assert len(ws_b.sent) == 0  # Tenant B did not receive Tenant A event!

    asyncio.run(_test())
