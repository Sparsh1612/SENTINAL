# Sentinel Setup Script for Windows
# This script will help you set up the Sentinel credit card fraud detection system

Write-Host "Sentinel Credit Card Fraud Detection System Setup" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Green

# Function to check if a command exists
function Test-Command($cmdname) {
    return [bool](Get-Command -Name $cmdname -ErrorAction SilentlyContinue)
}

# Function to install Python using winget
function Install-Python {
    Write-Host "Installing Python..." -ForegroundColor Yellow
    
    if (Test-Command winget) {
        Write-Host "Using winget to install Python..." -ForegroundColor Cyan
        winget install Python.Python.3.11
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Python installed successfully!" -ForegroundColor Green
            return $true
        }
    }
    
    Write-Host "Python installation failed. Please install Python manually:" -ForegroundColor Red
    Write-Host "   1. Visit https://www.python.org/downloads/" -ForegroundColor White
    Write-Host "   2. Download Python 3.11 or later" -ForegroundColor White
    Write-Host "   3. Run installer and check 'Add Python to PATH'" -ForegroundColor White
    Write-Host "   4. Restart PowerShell and run this script again" -ForegroundColor White
    return $false
}

# Function to check and install Docker
function Install-Docker {
    Write-Host "Checking Docker installation..." -ForegroundColor Yellow
    
    if (Test-Command docker) {
        Write-Host "Docker is already installed" -ForegroundColor Green
        return $true
    }
    
    Write-Host "Installing Docker Desktop..." -ForegroundColor Yellow
    
    if (Test-Command winget) {
        winget install Docker.DockerDesktop
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Docker Desktop installed successfully!" -ForegroundColor Green
            Write-Host "Please restart your computer and run this script again" -ForegroundColor Yellow
            return $false
        }
    }
    
    Write-Host "Docker installation failed. Please install manually:" -ForegroundColor Red
    Write-Host "   1. Visit https://www.docker.com/products/docker-desktop/" -ForegroundColor White
    Write-Host "   2. Download Docker Desktop for Windows" -ForegroundColor White
    Write-Host "   3. Run installer and restart computer" -ForegroundColor White
    return $false
}

# Function to setup Python environment
function Setup-PythonEnvironment {
    Write-Host "Setting up Python environment..." -ForegroundColor Yellow
    
    # Create virtual environment
    if (Test-Path "venv") {
        Write-Host "Virtual environment already exists" -ForegroundColor Cyan
    } else {
        Write-Host "Creating virtual environment..." -ForegroundColor Cyan
        python -m venv venv
    }
    
    # Activate virtual environment
    Write-Host "Activating virtual environment..." -ForegroundColor Cyan
    & ".\venv\Scripts\Activate.ps1"
    
    # Upgrade pip
    Write-Host "Upgrading pip..." -ForegroundColor Cyan
    python -m pip install --upgrade pip
    
    # Install requirements
    Write-Host "Installing Python dependencies..." -ForegroundColor Cyan
    pip install -r ..\requirements.txt
    
    # Install Sentinel in development mode
    Write-Host "Installing Sentinel..." -ForegroundColor Cyan
    pip install -e ..
    
    Write-Host "Python environment setup complete!" -ForegroundColor Green
}

# Function to start services
function Start-SentinelServices {
    Write-Host "Starting Sentinel services..." -ForegroundColor Yellow
    
    # Start infrastructure
    Write-Host "Starting Docker infrastructure..." -ForegroundColor Cyan
    docker-compose up -d postgres redis zookeeper kafka
    
    # Wait for services to be ready
    Write-Host "Waiting for services to be ready..." -ForegroundColor Cyan
    Start-Sleep -Seconds 10
    
    # Initialize database
    Write-Host "Initializing database..." -ForegroundColor Cyan
    python -m sentinel.cli.main init-db
    
    # Start application
    Write-Host "Starting Sentinel application..." -ForegroundColor Cyan
    docker-compose up -d sentinel-api sentinel-frontend sentinel-consumer
    
    Write-Host "Sentinel services started!" -ForegroundColor Green
}

# Function to show status
function Show-Status {
    Write-Host "System Status:" -ForegroundColor Green
    docker-compose ps
    
    Write-Host "Access URLs:" -ForegroundColor Green
    Write-Host "   API: http://localhost:8000" -ForegroundColor White
    Write-Host "   Frontend: http://localhost:3000" -ForegroundColor White
    Write-Host "   API Docs: http://localhost:8000/docs" -ForegroundColor White
    
    Write-Host "Useful Commands:" -ForegroundColor Green
    Write-Host "   View logs: docker-compose logs -f" -ForegroundColor White
    Write-Host "   Stop services: docker-compose down" -ForegroundColor White
    Write-Host "   Restart: docker-compose restart" -ForegroundColor White
}

# Main execution
Write-Host "Checking system requirements..." -ForegroundColor Cyan

# Check Python
if (-not (Test-Command python)) {
    Write-Host "Python not found" -ForegroundColor Red
    if (-not (Install-Python)) {
        exit 1
    }
} else {
    $pythonVersion = python --version 2>&1
    Write-Host "Python found: $pythonVersion" -ForegroundColor Green
}

# Check Docker
if (-not (Test-Command docker)) {
    Write-Host "Docker not found" -ForegroundColor Red
    if (-not (Install-Docker)) {
        exit 1
    }
} else {
    Write-Host "Docker found" -ForegroundColor Green
}

# Check Docker Compose
if (-not (Test-Command docker-compose)) {
    Write-Host "Docker Compose not found" -ForegroundColor Red
    Write-Host "Please install Docker Compose or use Docker Desktop which includes it" -ForegroundColor Yellow
    exit 1
} else {
    Write-Host "Docker Compose found" -ForegroundColor Green
}

# Setup Python environment
Setup-PythonEnvironment

# Start services
Start-SentinelServices

# Show status
Show-Status

Write-Host "Sentinel setup complete!" -ForegroundColor Green
Write-Host "Open your browser and navigate to http://localhost:3000 to access the dashboard" -ForegroundColor Cyan
