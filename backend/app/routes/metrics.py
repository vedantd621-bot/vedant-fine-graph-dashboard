"""
FinGraph Prometheus Metrics Route.
Exposes standard Prometheus scrape endpoint for monitoring and observability.
"""
from fastapi import APIRouter, Response
from backend.app.metrics.prometheus import get_metrics

router = APIRouter(tags=["Observability"])


@router.get("/metrics")
def metrics():
    """Returns Prometheus text format telemetry metrics."""
    collector = get_metrics()
    rendered = collector.render_prometheus_text()
    return Response(content=rendered, media_type="text/plain; version=0.0.4")
