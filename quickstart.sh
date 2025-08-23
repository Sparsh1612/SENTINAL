#!/bin/bash

# Sentinel Fraud Detection System - Quick Start Script
# This script sets up and starts the complete Sentinel system

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SENTINEL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SENTINEL_DIR/.env"
DOCKER_COMPOSE_FILE="$SENTINEL_DIR/docker-compose.yml"

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        error "This script should not be run as root"
        exit 1
    fi
}

# Check system requirements
check_requirements() {
    log "Checking system requirements..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        error "Python 3.8+ is required but not installed"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    if [[ $(echo "$PYTHON_VERSION >= 3.8" | bc -l) -eq 0 ]]; then
        error "Python 3.8+ is required, found $PYTHON_VERSION"
        exit 1
    fi
    log "Python $PYTHON_VERSION found"
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        error "Docker is required but not installed"
        exit 1
    fi
    log "Docker found"
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is required but not installed"
        exit 1
    fi
    log "Docker Compose found"
    
    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        error "Docker daemon is not running"
        exit 1
    fi
    log "Docker daemon is running"
}

# Setup environment
setup_environment() {
    log "Setting up environment..."
    
    if [[ ! -f "$ENV_FILE" ]]; then
        if [[ -f "$SENTINEL_DIR/env.example" ]]; then
            log "Creating .env file from template..."
            cp "$SENTINEL_DIR/env.example" "$ENV_FILE"
            warn "Please review and update the .env file with your configuration"
        else
            error "env.example file not found"
            exit 1
        fi
    else
        log ".env file already exists"
    fi
    
    # Create necessary directories
    mkdir -p "$SENTINEL_DIR/data/models"
    mkdir -p "$SENTINEL_DIR/data/processed"
    mkdir -p "$SENTINEL_DIR/data/raw"
    mkdir -p "$SENTINEL_DIR/data/uploads"
    mkdir -p "$SENTINEL_DIR/logs"
    
    log "Environment setup complete"
}

# Install Python dependencies
install_dependencies() {
    log "Installing Python dependencies..."
    
    # Create virtual environment if it doesn't exist
    if [[ ! -d "$SENTINEL_DIR/venv" ]]; then
        log "Creating virtual environment..."
        python3 -m venv "$SENTINEL_DIR/venv"
    fi
    
    # Activate virtual environment
    source "$SENTINEL_DIR/venv/bin/activate"
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install requirements
    if [[ -f "$SENTINEL_DIR/requirements.txt" ]]; then
        log "Installing requirements..."
        pip install -r "$SENTINEL_DIR/requirements.txt"
    else
        warn "requirements.txt not found, skipping dependency installation"
    fi
    
    # Install Sentinel in development mode
    log "Installing Sentinel in development mode..."
    pip install -e "$SENTINEL_DIR"
    
    log "Dependencies installation complete"
}

# Start infrastructure services
start_infrastructure() {
    log "Starting infrastructure services..."
    
    # Check if docker-compose file exists
    if [[ ! -f "$DOCKER_COMPOSE_FILE" ]]; then
        error "docker-compose.yml not found"
        exit 1
    fi
    
    # Start only infrastructure services
    log "Starting PostgreSQL, Redis, and Kafka..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d postgres redis zookeeper kafka
    
    # Wait for services to be ready
    log "Waiting for services to be ready..."
    sleep 10
    
    # Check service health
    check_service_health
    
    log "Infrastructure services started"
}

# Check service health
check_service_health() {
    log "Checking service health..."
    
    # Check PostgreSQL
    if docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T postgres pg_isready -U sentinel &> /dev/null; then
        log "PostgreSQL is ready"
    else
        warn "PostgreSQL is not ready yet, waiting..."
        sleep 5
        if docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T postgres pg_isready -U sentinel &> /dev/null; then
            log "PostgreSQL is now ready"
        else
            error "PostgreSQL failed to start"
            exit 1
        fi
    fi
    
    # Check Redis
    if docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T redis redis-cli ping &> /dev/null; then
        log "Redis is ready"
    else
        warn "Redis is not ready yet, waiting..."
        sleep 5
        if docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T redis redis-cli ping &> /dev/null; then
            log "Redis is now ready"
        else
            error "Redis failed to start"
            exit 1
        fi
    fi
    
    # Check Kafka
    if docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T kafka kafka-topics --bootstrap-server localhost:9092 --list &> /dev/null; then
        log "Kafka is ready"
    else
        warn "Kafka is not ready yet, waiting..."
        sleep 10
        if docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T kafka kafka-topics --bootstrap-server localhost:9092 --list &> /dev/null; then
            log "Kafka is now ready"
        else
            error "Kafka failed to start"
            exit 1
        fi
    fi
}

# Initialize database
initialize_database() {
    log "Initializing database..."
    
    # Activate virtual environment
    source "$SENTINEL_DIR/venv/bin/activate"
    
    # Check if Sentinel CLI is available
    if ! command -v sentinel &> /dev/null; then
        error "Sentinel CLI not found. Please install dependencies first."
        exit 1
    fi
    
    # Initialize database
    if sentinel init-db; then
        log "Database initialized successfully"
    else
        error "Failed to initialize database"
        exit 1
    fi
}

# Start application services
start_application() {
    log "Starting application services..."
    
    # Start API server
    log "Starting Sentinel API server..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d sentinel-api
    
    # Start frontend
    log "Starting Sentinel frontend..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d sentinel-frontend
    
    # Start Kafka consumer
    log "Starting Kafka consumer..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d sentinel-consumer
    
    log "Application services started"
}

# Wait for application to be ready
wait_for_application() {
    log "Waiting for application to be ready..."
    
    # Wait for API
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -s http://localhost:8000/health &> /dev/null; then
            log "API server is ready"
            break
        fi
        
        if [[ $attempt -eq $max_attempts ]]; then
            error "API server failed to start within expected time"
            exit 1
        fi
        
        log "Waiting for API server... (attempt $attempt/$max_attempts)"
        sleep 5
        ((attempt++))
    done
    
    # Wait for frontend
    attempt=1
    while [[ $attempt -le $max_attempts ]]; do
        if curl -s http://localhost:3000 &> /dev/null; then
            log "Frontend is ready"
            break
        fi
        
        if [[ $attempt -eq $max_attempts ]]; then
            error "Frontend failed to start within expected time"
            exit 1
        fi
        
        log "Waiting for frontend... (attempt $attempt/$max_attempts)"
        sleep 5
        ((attempt++))
    done
}

# Display status and next steps
show_status() {
    log "=== Sentinel System Status ==="
    
    # Show running containers
    log "Running containers:"
    docker-compose -f "$DOCKER_COMPOSE_FILE" ps
    
    # Show service URLs
    echo
    log "=== Service URLs ==="
    echo -e "${BLUE}API Server:${NC} http://localhost:8000"
    echo -e "${BLUE}API Docs:${NC} http://localhost:8000/docs"
    echo -e "${BLUE}Frontend:${NC} http://localhost:3000"
    echo -e "${BLUE}Health Check:${NC} http://localhost:8000/health"
    
    echo
    log "=== Next Steps ==="
    echo "1. Open http://localhost:3000 in your browser to access the dashboard"
    echo "2. Use the API at http://localhost:8000/docs for development"
    echo "3. Check system status: sentinel status"
    echo "4. View logs: docker-compose logs -f"
    echo "5. Stop services: docker-compose down"
    
    echo
    log "=== Useful Commands ==="
    echo "Check system status: sentinel status"
    echo "Check health: sentinel health"
    echo "View logs: sentinel logs"
    echo "Reload models: sentinel reload-models"
    echo "Backup system: sentinel backup /path/to/backup"
    
    echo
    log "=== Troubleshooting ==="
    echo "If you encounter issues:"
    echo "1. Check logs: docker-compose logs -f"
    echo "2. Check service status: docker-compose ps"
    echo "3. Restart services: docker-compose restart"
    echo "4. View this script's output for errors"
}

# Stop all services
stop_services() {
    log "Stopping all services..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" down
    log "Services stopped"
}

# Clean up
cleanup() {
    log "Cleaning up..."
    
    # Stop services
    stop_services
    
    # Remove containers and volumes (optional)
    if [[ "$1" == "--clean" ]]; then
        log "Removing containers and volumes..."
        docker-compose -f "$DOCKER_COMPOSE_FILE" down -v --remove-orphans
    fi
    
    log "Cleanup complete"
}

# Main function
main() {
    local action="${1:-start}"
    
    case $action in
        "start")
            log "Starting Sentinel Fraud Detection System..."
            check_root
            check_requirements
            setup_environment
            install_dependencies
            start_infrastructure
            initialize_database
            start_application
            wait_for_application
            show_status
            log "Sentinel system started successfully!"
            ;;
        "stop")
            stop_services
            ;;
        "restart")
            stop_services
            sleep 5
            main start
            ;;
        "clean")
            cleanup --clean
            ;;
        "status")
            if [[ -f "$DOCKER_COMPOSE_FILE" ]]; then
                docker-compose -f "$DOCKER_COMPOSE_FILE" ps
            else
                error "docker-compose.yml not found"
                exit 1
            fi
            ;;
        "logs")
            if [[ -f "$DOCKER_COMPOSE_FILE" ]]; then
                docker-compose -f "$DOCKER_COMPOSE_FILE" logs -f
            else
                error "docker-compose.yml not found"
                exit 1
            fi
            ;;
        "help"|"-h"|"--help")
            echo "Usage: $0 [COMMAND]"
            echo ""
            echo "Commands:"
            echo "  start     Start the complete Sentinel system (default)"
            echo "  stop      Stop all services"
            echo "  restart   Restart all services"
            echo "  clean     Stop services and remove containers/volumes"
            echo "  status    Show service status"
            echo "  logs      Show service logs"
            echo "  help      Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0              # Start the system"
            echo "  $0 stop         # Stop the system"
            echo "  $0 restart      # Restart the system"
            echo "  $0 logs         # View logs"
            ;;
        *)
            error "Unknown command: $action"
            echo "Use '$0 help' for usage information"
            exit 1
            ;;
    esac
}

# Handle script interruption
trap 'error "Script interrupted"; exit 1' INT TERM

# Run main function with all arguments
main "$@"
