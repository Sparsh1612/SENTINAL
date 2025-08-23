# Start Sentinel Python Backend (Windows)
# This script starts the Python backend directly, using Docker infrastructure

Write-Host "Starting Sentinel Python Backend" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green

# Check if infrastructure is running
Write-Host "Checking Docker infrastructure..." -ForegroundColor Yellow
$postgres = docker-compose ps postgres | Select-String "healthy"
$redis = docker-compose ps redis | Select-String "healthy"
$kafka = docker-compose ps kafka | Select-String "healthy"

if (-not ($postgres -and $redis -and $kafka)) {
    Write-Host "Infrastructure services are not healthy. Starting them first..." -ForegroundColor Red
    docker-compose up -d postgres redis zookeeper kafka
    Start-Sleep -Seconds 15
}

Write-Host "Infrastructure is ready!" -ForegroundColor Green

# Set environment variables
$env:DATABASE_URL = "postgresql://sentinel:password@localhost:5432/sentinel_db"
$env:REDIS_URL = "redis://localhost:6379"
$env:KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"

Write-Host "Environment variables set:" -ForegroundColor Cyan
Write-Host "  DATABASE_URL: $env:DATABASE_URL" -ForegroundColor White
Write-Host "  REDIS_URL: $env:REDIS_URL" -ForegroundColor White
Write-Host "  KAFKA_BOOTSTRAP_SERVERS: $env:KAFKA_BOOTSTRAP_SERVERS" -ForegroundColor White

# Check if Python is available
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Python not found. Please run .\fix-python.ps1 first." -ForegroundColor Red
    exit 1
}

Write-Host "Python found: $(python --version)" -ForegroundColor Green

# Install requirements if needed
if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

# Install requirements
Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# Start the backend
Write-Host "Starting Sentinel backend..." -ForegroundColor Green
Write-Host "Access the API at: http://localhost:8000" -ForegroundColor Cyan
Write-Host "API docs at: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow

cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
