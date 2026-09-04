# FinGraph Production Deployment Guide

## Quick Deployment
`ash
# 1. Clone repository and navigate to root
cd fingraph

# 2. Copy production environment configuration
cp .env.production.example .env

# 3. Deploy full stack using orchestration script
./deploy.sh
# or on Windows:
.\deploy.ps1
`

## Architecture Components
- **Frontend SPA**: Nginx Alpine serving React UI on port 80.
- **Backend API**: Gunicorn/Uvicorn cluster on port 8000.
- **Database**: Neo4j Enterprise 5.18 on ports 7474 / 7687.
- **Stream Ingestion**: Apache Kafka 7.5.0 on port 9092.
- **Stream Processing**: Apache Flink 1.18.1 cluster on port 8081.
- **Observability**: Prometheus telemetry server on port 9090.
