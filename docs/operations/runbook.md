# FinGraph Operations & Incident Response Runbook

## 1. System Health Probes
FinGraph exposes standard Kubernetes-compatible health endpoints:
- GET /live: Liveness probe verifying process execution.
- GET /ready: Readiness probe verifying Neo4j and Kafka connectivity.
- GET /health: Detailed subsystem diagnostics:
  - Neo4j Bolt connectivity & response time.
  - Kafka consumer lag & partition assignments.
  - Real-time ConnectionManager active socket counts.

## 2. Telemetry & Metrics Scraping
- Prometheus metrics exporter: GET /metrics
- Core metrics exposed:
  - fingraph_http_requests_total: HTTP requests count by method, route, and status code.
  - fingraph_http_request_duration_seconds: Latency distribution histogram.
  - fingraph_websocket_active_connections: Real-time WebSocket clients gauge.
  - fingraph_neo4j_queries_total: Neo4j query count & errors.
  - fingraph_kafka_messages_consumed_total: Pipeline ingestion velocity.
  - fingraph_alerts_generated_total: Fraud detection alert trigger count.

## 3. Scaling & Resource Guidelines
- **FastAPI Backend**: Stateless; scale horizontally behind Nginx / ALB.
- **Neo4j Database**:
  - Minimum Heap: 1GB initial, 4GB max.
  - Pagecache: 1GB minimum.
  - GDS Memory: Tune projection cache based on active account count.
- **Apache Flink**:
  - TaskManager Task Slots: 4 per node.
  - Default Parallelism: Equal to Kafka transactions partition count.
