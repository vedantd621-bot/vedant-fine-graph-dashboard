#!/usr/bin/env bash
# =======================================================================
# FinGraph Production Deployment & Verification Script
# =======================================================================
set -euo pipefail

echo "================================================================="
echo "FinGraph Production Deployment Orchestration"
echo "================================================================="

if [ ! -f ".env" ]; then
  echo "[!] No .env file found. Copying from .env.production.example..."
  cp .env.production.example .env
fi

echo "[+] Building and starting FinGraph production stack..."
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

echo "[+] Waiting for services to reach healthy status..."
sleep 15

echo "[+] Running production health smoke tests..."
curl -s -f http://localhost:8000/live > /dev/null && echo "  [PASS] Backend /live endpoint healthy"
curl -s -f http://localhost:8000/ready > /dev/null && echo "  [PASS] Backend /ready endpoint healthy"
curl -s -f http://localhost:8000/metrics > /dev/null && echo "  [PASS] Prometheus /metrics endpoint scraping"
curl -s -f http://localhost/ > /dev/null && echo "  [PASS] Frontend Nginx reverse proxy serving SPA"

echo "================================================================="
echo "FinGraph Production Deployment Complete & Verified!"
echo "Frontend URL: http://localhost"
echo "API Docs:     http://localhost:8000/docs"
echo "Prometheus:   http://localhost:9090"
echo "================================================================="
