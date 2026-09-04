"""
FinGraph Prometheus Metrics Exporter.
Collects and renders standard Prometheus text exposition format metrics.
"""
import collections
import time
from typing import Dict, List, Optional


class PrometheusMetrics:
    """In-memory metrics collector."""

    def __init__(self):
        # Counters: key -> count
        self.http_requests_total: Dict[str, int] = collections.defaultdict(int)
        self.http_errors_total: Dict[str, int] = collections.defaultdict(int)
        self.neo4j_queries_total: Dict[str, int] = collections.defaultdict(int)
        self.neo4j_query_failures_total: Dict[str, int] = collections.defaultdict(int)
        self.kafka_messages_consumed_total: Dict[str, int] = collections.defaultdict(int)
        self.websocket_events_sent_total: Dict[str, int] = collections.defaultdict(int)
        self.alerts_created_total: Dict[str, int] = collections.defaultdict(int)
        self.risk_calculations_total: Dict[str, int] = collections.defaultdict(int)

        # Gauges
        self.websocket_active_connections: int = 0

        # Request latency buffer (last 500 requests for summary)
        self._latencies: List[float] = []

    def record_http_request(self, method: str, path: str, status_code: int, duration_seconds: float):
        # Clean path template
        clean_path = path.split("?")[0]
        key = f'method="{method}",path="{clean_path}",status="{status_code}"'
        self.http_requests_total[key] += 1
        if status_code >= 400:
            err_key = f'path="{clean_path}",status="{status_code}"'
            self.http_errors_total[err_key] += 1

        self._latencies.append(duration_seconds)
        if len(self._latencies) > 1000:
            self._latencies.pop(0)

    def record_neo4j_query(self, query_name: str, success: bool = True):
        key = f'query="{query_name}"'
        self.neo4j_queries_total[key] += 1
        if not success:
            self.neo4j_query_failures_total[key] += 1

    def record_kafka_consumed(self, topic: str):
        key = f'topic="{topic}"'
        self.kafka_messages_consumed_total[key] += 1

    def record_ws_event_sent(self, event_type: str):
        key = f'event="{event_type}"'
        self.websocket_events_sent_total[key] += 1

    def record_alert_created(self, severity: str):
        key = f'severity="{severity}"'
        self.alerts_created_total[key] += 1

    def record_risk_calculated(self, risk_level: str):
        key = f'level="{risk_level}"'
        self.risk_calculations_total[key] += 1

    def set_active_ws_connections(self, count: int):
        self.websocket_active_connections = count

    def render_prometheus_text(self) -> str:
        """Renders metrics in official Prometheus 0.0.4 text format."""
        lines = []

        # HTTP Requests Total
        lines.append("# HELP fingraph_http_requests_total Total number of HTTP requests.")
        lines.append("# TYPE fingraph_http_requests_total counter")
        if self.http_requests_total:
            for labels, count in sorted(self.http_requests_total.items()):
                lines.append(f"fingraph_http_requests_total{{{labels}}} {count}")
        else:
            lines.append('fingraph_http_requests_total{method="GET",path="/health",status="200"} 0')

        # HTTP Errors Total
        lines.append("# HELP fingraph_http_errors_total Total number of HTTP request errors.")
        lines.append("# TYPE fingraph_http_errors_total counter")
        for labels, count in sorted(self.http_errors_total.items()):
            lines.append(f"fingraph_http_errors_total{{{labels}}} {count}")

        # HTTP Request Duration Summary
        lines.append("# HELP fingraph_http_request_duration_seconds HTTP request latency summary.")
        lines.append("# TYPE fingraph_http_request_duration_seconds summary")
        count = len(self._latencies)
        total_sum = sum(self._latencies) if count > 0 else 0.0
        lines.append(f"fingraph_http_request_duration_seconds_count {count}")
        lines.append(f"fingraph_http_request_duration_seconds_sum {total_sum:.4f}")

        # Neo4j Queries
        lines.append("# HELP fingraph_neo4j_queries_total Total Neo4j Cypher queries executed.")
        lines.append("# TYPE fingraph_neo4j_queries_total counter")
        for labels, count in sorted(self.neo4j_queries_total.items()):
            lines.append(f"fingraph_neo4j_queries_total{{{labels}}} {count}")

        # WebSocket Connections Gauge
        lines.append("# HELP fingraph_websocket_active_connections Current active WebSocket client connections.")
        lines.append("# TYPE fingraph_websocket_active_connections gauge")
        lines.append(f"fingraph_websocket_active_connections {self.websocket_active_connections}")

        # WebSocket Events Sent
        lines.append("# HELP fingraph_websocket_events_sent_total Total events dispatched to WebSockets.")
        lines.append("# TYPE fingraph_websocket_events_sent_total counter")
        for labels, count in sorted(self.websocket_events_sent_total.items()):
            lines.append(f"fingraph_websocket_events_sent_total{{{labels}}} {count}")

        # Alerts Created
        lines.append("# HELP fingraph_alerts_created_total Total fraud alerts created.")
        lines.append("# TYPE fingraph_alerts_created_total counter")
        for labels, count in sorted(self.alerts_created_total.items()):
            lines.append(f"fingraph_alerts_created_total{{{labels}}} {count}")

        # Risk Calculations
        lines.append("# HELP fingraph_risk_calculations_total Total risk score evaluations performed.")
        lines.append("# TYPE fingraph_risk_calculations_total counter")
        for labels, count in sorted(self.risk_calculations_total.items()):
            lines.append(f"fingraph_risk_calculations_total{{{labels}}} {count}")

        return "\n".join(lines) + "\n"


# Singleton instance
_global_metrics: Optional[PrometheusMetrics] = None


def get_metrics() -> PrometheusMetrics:
    global _global_metrics
    if _global_metrics is None:
        _global_metrics = PrometheusMetrics()
    return _global_metrics
