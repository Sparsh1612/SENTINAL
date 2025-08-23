# Test Sentinel Infrastructure
# This script tests the Docker infrastructure and shows how to access Sentinel

Write-Host "Testing Sentinel Infrastructure" -ForegroundColor Green
Write-Host "==============================" -ForegroundColor Green

# Check Docker infrastructure
Write-Host "Checking Docker services..." -ForegroundColor Yellow
docker-compose ps

# Test database connection
Write-Host "Testing database connection..." -ForegroundColor Yellow
try {
    $result = docker exec sentinal-postgres-1 psql -U sentinel -d sentinel_db -c "SELECT version();" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "PostgreSQL is working!" -ForegroundColor Green
    } else {
        Write-Host "PostgreSQL connection failed" -ForegroundColor Red
    }
} catch {
    Write-Host "Could not test PostgreSQL" -ForegroundColor Red
}

# Test Redis connection
Write-Host "Testing Redis connection..." -ForegroundColor Yellow
try {
    $result = docker exec sentinal-redis-1 redis-cli ping 2>&1
    if ($result -eq "PONG") {
        Write-Host "Redis is working!" -ForegroundColor Green
    } else {
        Write-Host "Redis connection failed" -ForegroundColor Red
    }
} catch {
    Write-Host "Could not test Redis" -ForegroundColor Red
}

# Test Kafka connection
Write-Host "Testing Kafka connection..." -ForegroundColor Yellow
try {
    $result = docker exec sentinal-kafka-1 kafka-topics --bootstrap-server localhost:9092 --list 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Kafka is working!" -ForegroundColor Green
    } else {
        Write-Host "Kafka connection failed" -ForegroundColor Red
    }
} catch {
    Write-Host "Could not test Kafka" -ForegroundColor Red
}

Write-Host "Next Steps:" -ForegroundColor Green
Write-Host "1. Fix Python installation (reinstall from python.org)" -ForegroundColor White
Write-Host "2. Run: .\start-python-backend.ps1" -ForegroundColor Cyan
Write-Host "3. Access Sentinel at: http://localhost:8000" -ForegroundColor Cyan

Write-Host "Current Status:" -ForegroundColor Green
Write-Host "   Infrastructure: Running in Docker" -ForegroundColor White
Write-Host "   Python: Needs reinstallation" -ForegroundColor White
Write-Host "   Backend: Waiting for Python" -ForegroundColor White
