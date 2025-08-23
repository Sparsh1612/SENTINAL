# Sentinel Fraud Detection System - Deployment Guide

This guide covers deploying the Sentinel fraud detection system in various environments, from local development to production.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Docker Deployment](#docker-deployment)
4. [Production Deployment](#production-deployment)
5. [Kubernetes Deployment](#kubernetes-deployment)
6. [Monitoring & Observability](#monitoring--observability)
7. [Scaling & Performance](#scaling--performance)
8. [Security Considerations](#security-considerations)
9. [Backup & Recovery](#backup--recovery)
10. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- **CPU**: 4+ cores (8+ for production)
- **RAM**: 8GB+ (16GB+ for production)
- **Storage**: 50GB+ SSD (100GB+ for production)
- **OS**: Linux (Ubuntu 20.04+), macOS 10.15+, or Windows 10+

### Software Requirements

- **Python**: 3.8+
- **Docker**: 20.10+ (for containerized deployment)
- **Docker Compose**: 2.0+ (for local development)
- **PostgreSQL**: 13+ (for production)
- **Redis**: 6.0+
- **Kafka**: 2.8+ (for streaming)

### Network Requirements

- **Ports**: 8000 (API), 3000 (Frontend), 5432 (PostgreSQL), 6379 (Redis), 9092 (Kafka)
- **Firewall**: Configure to allow necessary ports
- **SSL/TLS**: Required for production

## Local Development Setup

### 1. Clone Repository

```bash
git clone https://github.com/your-org/sentinel.git
cd sentinel
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
pip install -e .  # Install in development mode
```

### 4. Environment Configuration

```bash
cp env.example .env
# Edit .env with your local settings
```

### 5. Start Infrastructure Services

```bash
# Start PostgreSQL, Redis, and Kafka
docker-compose up -d postgres redis zookeeper kafka
```

### 6. Initialize Database

```bash
sentinel init-db
```

### 7. Start Services

```bash
# Terminal 1: Start API server
sentinel start-api --reload

# Terminal 2: Start frontend
sentinel launch-ui

# Terminal 3: Start Kafka consumer
python -m backend.streaming.consumer
```

### 8. Verify Installation

```bash
# Check system status
sentinel status

# Check health
sentinel health

# Test API
curl http://localhost:8000/health
```

## Docker Deployment

### 1. Build Images

```bash
# Build backend image
docker build -t sentinel-backend:latest .

# Build frontend image
docker build -t sentinel-frontend:latest ./frontend
```

### 2. Environment Configuration

```bash
# Copy and configure environment file
cp env.example .env
# Edit .env with production values
```

### 3. Start All Services

```bash
# Start complete system
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### 4. Scale Services

```bash
# Scale API workers
docker-compose up -d --scale sentinel-api=4

# Scale consumers
docker-compose up -d --scale sentinel-consumer=2
```

## Production Deployment

### 1. Server Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3 python3-pip python3-venv postgresql redis-server

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

### 2. Database Setup

```bash
# Create database user
sudo -u postgres createuser --interactive sentinel

# Create database
sudo -u postgres createdb sentinel_db

# Set password
sudo -u postgres psql -c "ALTER USER sentinel PASSWORD 'secure_password';"
```

### 3. Application Deployment

```bash
# Create application directory
sudo mkdir -p /opt/sentinel
sudo chown $USER:$USER /opt/sentinel

# Clone repository
git clone https://github.com/your-org/sentinel.git /opt/sentinel
cd /opt/sentinel

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install gunicorn  # Production WSGI server
```

### 4. Systemd Service Configuration

Create `/etc/systemd/system/sentinel-api.service`:

```ini
[Unit]
Description=Sentinel Fraud Detection API
After=network.target postgresql.service redis.service

[Service]
Type=exec
User=sentinel
Group=sentinel
WorkingDirectory=/opt/sentinel
Environment=PATH=/opt/sentinel/venv/bin
ExecStart=/opt/sentinel/venv/bin/gunicorn backend.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 5. Nginx Configuration

Create `/etc/nginx/sites-available/sentinel`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /opt/sentinel/frontend/build/static/;
    }
}
```

### 6. SSL Configuration

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### 7. Start Services

```bash
# Enable and start services
sudo systemctl enable sentinel-api
sudo systemctl start sentinel-api

# Reload nginx
sudo systemctl reload nginx

# Check status
sudo systemctl status sentinel-api
```

## Kubernetes Deployment

### 1. Prerequisites

- Kubernetes cluster (1.20+)
- Helm 3.0+
- kubectl configured

### 2. Create Namespace

```bash
kubectl create namespace sentinel
kubectl config set-context --current --namespace=sentinel
```

### 3. Install Dependencies

```bash
# Install PostgreSQL operator
helm repo add bitnami https://charts.bitnami.com/bitnami
helm install postgres bitnami/postgresql -n sentinel

# Install Redis
helm install redis bitnami/redis -n sentinel

# Install Kafka
helm install kafka bitnami/kafka -n sentinel
```

### 4. Deploy Application

```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/

# Or use Helm chart
helm install sentinel ./helm/sentinel -n sentinel
```

### 5. Verify Deployment

```bash
# Check pods
kubectl get pods

# Check services
kubectl get svc

# Check ingress
kubectl get ingress
```

## Monitoring & Observability

### 1. Prometheus Setup

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'sentinel-api'
    static_configs:
      - targets: ['sentinel-api:8000']
    metrics_path: '/metrics'
```

### 2. Grafana Dashboards

Import pre-built dashboards for:
- System metrics
- Fraud detection performance
- API response times
- Database performance

### 3. Log Aggregation

```bash
# Install ELK stack
docker-compose -f elk/docker-compose.yml up -d

# Configure log forwarding
# Use Fluentd or Filebeat to forward logs
```

### 4. Health Checks

```bash
# API health
curl http://your-domain.com/health

# Database health
curl http://your-domain.com/health/db

# System health
curl http://your-domain.com/health/system
```

## Scaling & Performance

### 1. Horizontal Scaling

```bash
# Scale API replicas
kubectl scale deployment sentinel-api --replicas=5

# Scale consumers
kubectl scale deployment sentinel-consumer --replicas=3
```

### 2. Load Balancing

```bash
# Configure nginx upstream
upstream sentinel_backend {
    least_conn;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
    server 127.0.0.1:8003;
    server 127.0.0.1:8004;
}
```

### 3. Caching Strategy

```bash
# Redis configuration
maxmemory 2gb
maxmemory-policy allkeys-lru

# Application-level caching
CACHE_TTL=3600
CACHE_MAX_SIZE=10000
```

### 4. Database Optimization

```sql
-- Create indexes
CREATE INDEX idx_transactions_timestamp ON transactions(timestamp);
CREATE INDEX idx_transactions_card_id ON transactions(card_id);
CREATE INDEX idx_fraud_alerts_status ON fraud_alerts(status);

-- Partition tables
CREATE TABLE transactions_y2024 PARTITION OF transactions
FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');
```

## Security Considerations

### 1. Network Security

```bash
# Configure firewall
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# Use VPN for admin access
# Restrict database access to application servers
```

### 2. Application Security

```bash
# Generate secure secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Enable rate limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=1000

# Enable CORS restrictions
ALLOWED_ORIGINS=["https://your-domain.com"]
```

### 3. Data Encryption

```bash
# Enable TLS for database
ssl = on
ssl_cert_file = '/etc/ssl/certs/ssl-cert-snakeoil.pem'
ssl_key_file = '/etc/ssl/private/ssl-cert-snakeoil.key'

# Encrypt sensitive data at rest
# Use encryption keys stored in secure key management system
```

### 4. Access Control

```bash
# Implement JWT authentication
# Use role-based access control (RBAC)
# Regular security audits
# Monitor access logs
```

## Backup & Recovery

### 1. Database Backup

```bash
# Automated backup script
#!/bin/bash
BACKUP_DIR="/backup/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# Backup PostgreSQL
pg_dump -h localhost -U sentinel sentinel_db > $BACKUP_DIR/database.sql

# Backup models
tar -czf $BACKUP_DIR/models.tar.gz data/models/

# Backup configuration
cp .env $BACKUP_DIR/
cp docker-compose.yml $BACKUP_DIR/
```

### 2. Recovery Procedures

```bash
# Database recovery
psql -h localhost -U sentinel sentinel_db < backup/database.sql

# Model recovery
tar -xzf backup/models.tar.gz -C data/

# Configuration recovery
cp backup/.env .
cp backup/docker-compose.yml .
```

### 3. Disaster Recovery

```bash
# Multi-region deployment
# Automated failover
# Regular recovery testing
# Documented recovery procedures
```

## Troubleshooting

### Common Issues

#### 1. Service Won't Start

```bash
# Check logs
sudo journalctl -u sentinel-api -f

# Check configuration
sentinel config --validate

# Check dependencies
sentinel health
```

#### 2. Database Connection Issues

```bash
# Test connection
psql -h localhost -U sentinel -d sentinel_db

# Check PostgreSQL status
sudo systemctl status postgresql

# Check firewall
sudo ufw status
```

#### 3. Performance Issues

```bash
# Check system resources
htop
iostat -x 1
df -h

# Check application metrics
curl http://localhost:8000/metrics

# Check database performance
SELECT * FROM pg_stat_activity;
```

#### 4. Memory Issues

```bash
# Check memory usage
free -h
cat /proc/meminfo

# Check swap
swapon --show

# Optimize memory settings
# Adjust database connection pool
# Reduce cache size
```

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
export DEBUG=true

# Start with debug flags
sentinel start-api --reload --log-level debug

# Check detailed logs
docker-compose logs -f sentinel-api
```

### Performance Tuning

```bash
# Database tuning
# Adjust shared_buffers, effective_cache_size
# Optimize query plans

# Application tuning
# Adjust worker processes
# Optimize cache settings
# Monitor memory usage
```

## Support & Maintenance

### 1. Regular Maintenance

```bash
# Weekly health checks
# Monthly security updates
# Quarterly performance reviews
# Annual disaster recovery tests
```

### 2. Monitoring Alerts

```bash
# Set up alerting for:
# - Service downtime
# - High error rates
# - Performance degradation
# - Security incidents
```

### 3. Documentation

```bash
# Keep deployment guides updated
# Document configuration changes
# Maintain runbooks for common issues
# Record incident responses
```

## Conclusion

This deployment guide provides a comprehensive approach to deploying the Sentinel fraud detection system. Follow the security best practices, implement proper monitoring, and maintain regular backups to ensure a robust and reliable deployment.

For additional support, refer to:
- [API Documentation](API.md)
- [Architecture Guide](ARCHITECTURE.md)
- [Plugin Development](PLUGINS.md)
- [GitHub Issues](https://github.com/your-org/sentinel/issues)
