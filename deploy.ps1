# ======================================================================
# FinGraph Production Deployment & Verification Script (PowerShell)
# ======================================================================
$ErrorActionPreference = "Stop"

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "FinGraph Production Deployment Orchestration (PowerShell)" -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan

if (-not (Test-Path ".env")) {
    Write-Host "[!] No .env file found. Copying from .env.production.example..." -ForegroundColor Yellow
    Copy-Item ".env.production.example" ".env"
}

Write-Host "[*] Building and starting FinGraph production stack..." -ForegroundColor Green
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
	]rite-Host "[*] Waiting for services to initialize..." -ForegroundColor Green
Start-Sleep -Seconds 15

Write-Host "[*] Running production smoke checks..." -ForegroundColor Green
try {
    $res = Invoke-RestMethod -Uri "http://localhost:8000/live" -Method Get
    Write-Host "  [PASS] Backend /live endpoint: $($res.status)" -ForegroundColor Green
} catch {
    Write-Host "  [FAIL] Backend /live check failed: $_" -ForegroundColor Red
}

try {
    $res = Invoke-RestMethod -Uri "http://localhost:8000/ready" -Method Get
    Write-Host "  [PASS] Backend /ready endpoint: $($res.status)" -ForegroundColor Green
} catch {
    Write-Host "  [FAIL] Backend /ready check failed: $_" -ForegroundColor Red
}

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "FinGraph Production Deployment Complete!" -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan
