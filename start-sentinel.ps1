# Start Sentinel using Docker
# This script starts the entire Sentinel system using Docker containers

Write-Host "Starting Sentinel Credit Card Fraud Detection System" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green

# Check if Docker is running
Write-Host "Checking Docker status..." -ForegroundColor Yellow
try {
    docker info > $null 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
        exit 1
    }
    Write-Host "Docker is running" -ForegroundColor Green
} catch {
    Write-Host "Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
    exit 1
}

# Check if Docker Compose is available
if (-not (Get-Command docker-compose -ErrorAction SilentlyContinue)) {
    Write-Host "Docker Compose not found. Please install Docker Desktop which includes it." -ForegroundColor Red
    exit 1
}

Write-Host "Docker Compose found" -ForegroundColor Green

# Stop any existing containers
Write-Host "Stopping any existing containers..." -ForegroundColor Yellow
docker-compose down

# Build and start the infrastructure services first
Write-Host "Starting infrastructure services..." -ForegroundColor Yellow
docker-compose up -d postgres redis zookeeper kafka

# Wait for services to be ready
Write-Host "Waiting for services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

# Check service health
Write-Host "Checking service health..." -ForegroundColor Yellow
$healthy = $false
$attempts = 0
$maxAttempts = 10

while (-not $healthy -and $attempts -lt $maxAttempts) {
    $attempts++
    Write-Host "Attempt $attempts of $maxAttempts..." -ForegroundColor Cyan
    
    try {
        $postgres = docker-compose ps postgres | Select-String "healthy"
        $redis = docker-compose ps redis | Select-String "healthy"
        $kafka = docker-compose ps kafka | Select-String "healthy"
        
        if ($postgres -and $redis -and $kafka) {
            $healthy = $true
            Write-Host "All infrastructure services are healthy!" -ForegroundColor Green
        } else {
            Write-Host "Waiting for services to become healthy..." -ForegroundColor Yellow
            Start-Sleep -Seconds 10
        }
    } catch {
        Write-Host "Error checking service health..." -ForegroundColor Red
        Start-Sleep -Seconds 10
    }
}

if (-not $healthy) {
    Write-Host "Services did not become healthy. Check logs with: docker-compose logs" -ForegroundColor Red
    exit 1
}

# Start the application services
Write-Host "Starting application services..." -ForegroundColor Yellow
docker-compose up -d sentinel-api sentinel-frontend sentinel-consumer

# Wait for application services
Write-Host "Waiting for application services..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Show status
Write-Host "System Status:" -ForegroundColor Green
docker-compose ps

Write-Host "`nAccess URLs:" -ForegroundColor Green
Write-Host "   Frontend Dashboard: http://localhost:3000" -ForegroundColor White
Write-Host "   API: http://localhost:8000" -ForegroundColor White
Write-Host "   API Documentation: http://localhost:8000/docs" -ForegroundColor White

Write-Host "`nUseful Commands:" -ForegroundColor Green
Write-Host "   View logs: docker-compose logs -f" -ForegroundColor White
Write-Host "   View specific service logs: docker-compose logs -f sentinel-api" -ForegroundColor White
Write-Host "   Stop services: docker-compose down" -ForegroundColor White
Write-Host "   Restart services: docker-compose restart" -ForegroundColor White

Write-Host "`nSentinel is starting up!" -ForegroundColor Green
Write-Host "The system may take a few minutes to fully initialize." -ForegroundColor Yellow
Write-Host "Check the dashboard at http://localhost:3000" -ForegroundColor Cyan
