# 📦 Deployment Guide

Complete production deployment instructions for Intelligent Energy Grid Balancer.

## Table of Contents

1. [Docker Deployment](#docker-deployment)
2. [Systemd Service (Linux)](#systemd-service-linux)
3. [Nginx Reverse Proxy](#nginx-reverse-proxy)
4. [SSL/TLS Configuration](#ssltls-configuration)
5. [Environment Variables](#environment-variables)
6. [Database Migration](#database-migration)
7. [Monitoring & Logging](#monitoring--logging)
8. [Backup Strategy](#backup-strategy)
9. [Scaling](#scaling)
10. [Troubleshooting](#troubleshooting)

---

## Docker Deployment

### Quick Deploy

```bash
cd backend
docker-compose up -d
```

This starts the application and makes it available at `http://localhost:8000`.

### Dockerfile

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose (Production)

```yaml
version: '3.8'
services:
  grid-balancer:
    build: .
    container_name: intelligent-grid-balancer
    ports:
      - "8000:8000"
    environment:
      DEBUG: "False"
      LOG_LEVEL: "INFO"
      SERVER_HOST: "0.0.0.0"
      SERVER_PORT: "8000"
    volumes:
      - ./data/:/app/data/
      - ./logs/:/app/logs/
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### Deploy to Production

```bash
# Build image
docker build -t grid-balancer:latest .

# Run container
docker run -d \
  --name grid-balancer \
  -p 8000:8000 \
  -e DEBUG=False \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/.env:/app/.env \
  --restart unless-stopped \
  grid-balancer:latest

# Check logs
docker logs -f grid-balancer

# Stop container
docker stop grid-balancer
```

---

## Systemd Service (Linux)

### Create Service File

Create `/etc/systemd/system/grid-balancer.service`:

```ini
[Unit]
Description=Intelligent Energy Grid Balancer
After=network.target

[Service]
Type=simple
User=nobody
WorkingDirectory=/opt/grid-balancer
Environment="PATH=/opt/grid-balancer/venv/bin"
Environment="PYTHONUNBUFFERED=1"
ExecStart=/opt/grid-balancer/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Setup

```bash
# Copy application
sudo cp -r backend /opt/grid-balancer
cd /opt/grid-balancer

# Setup virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create directories
sudo mkdir -p /var/log/grid-balancer
sudo mkdir -p /var/lib/grid-balancer/data

# Update permissions
sudo chown -R nobody:nobody /opt/grid-balancer
sudo chown -R nobody:nobody /var/log/grid-balancer
sudo chown -R nobody:nobody /var/lib/grid-balancer
```

### Start Service

```bash
# Enable at boot
sudo systemctl enable grid-balancer

# Start service
sudo systemctl start grid-balancer

# Check status
sudo systemctl status grid-balancer

# View logs
sudo journalctl -u grid-balancer -f
```

### Stop/Restart

```bash
sudo systemctl stop grid-balancer
sudo systemctl restart grid-balancer
```

---

## Nginx Reverse Proxy

### Install Nginx

```bash
# Ubuntu/Debian
sudo apt-get install nginx

# Start service
sudo systemctl start nginx
sudo systemctl enable nginx
```

### Configuration

Create in `/etc/nginx/sites-available/grid-balancer`:

```nginx
upstream grid_balancer_backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name grid-balancer.example.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name grid-balancer.example.com;

    ssl_certificate /etc/letsencrypt/live/grid-balancer.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/grid-balancer.example.com/privkey.pem;

    # SSL Configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;

    # Logging
    access_log /var/log/nginx/grid-balancer-access.log;
    error_log /var/log/nginx/grid-balancer-error.log;

    # Proxy Configuration
    location / {
        proxy_pass http://grid_balancer_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;
        proxy_request_buffering off;
    }

    # WebSocket support
    location /ws {
        proxy_pass http://grid_balancer_backend/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 86400;
    }
}
```

### Enable Configuration

```bash
sudo ln -s /etc/nginx/sites-available/grid-balancer /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## SSL/TLS Configuration

### Let's Encrypt (Free SSL)

```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Generate certificate
sudo certbot certonly --nginx -d grid-balancer.example.com

# Auto-renewal setup
sudo systemctl enable certbot-renew
sudo systemctl start certbot-renew
```

### Self-Signed Certificate (Testing)

```bash
openssl req -x509 -newkey rsa:4096 -nodes \
  -out cert.pem -keyout key.pem -days 365

# Update Nginx configuration
ssl_certificate /path/to/cert.pem;
ssl_certificate_key /path/to/key.pem;
```

---

## Environment Variables

Production `.env` file:

```env
# Server Configuration
DEBUG=False
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
SERVER_WORKERS=4

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/grid-balancer/app.log
LOG_ROTATION=daily

# Security
SECRET_KEY=your-secret-key-here-generate-with-openssl-rand-hex-32
ALLOWED_ORIGINS=https://grid-balancer.example.com

# Database (Future - Currently uses JSON)
DATABASE_URL=postgresql://user:password@localhost:5432/grid_balancer

# Analytics
ENABLE_ANALYTICS=true
ANALYTICS_ENDPOINT=https://analytics.example.com

# Email Alerts
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
ALERT_EMAIL=operations@example.com
```

---

## Database Migration

### Current State (JSON Storage)

- Data stored in `backend/data/grid_state.json`
- Daily backup to `backend/data/backups/`
- Suitable for: Development, testing, small deployments

### PostgreSQL Migration (Optional)

For production with 1000+ requests/minute:

```bash
# Install PostgreSQL
sudo apt-get install postgresql postgresql-contrib

# Create database
sudo -u postgres createdb grid_balancer
sudo -u postgres createuser grid_user -P

# Update requirements.txt
pip install psycopg2-binary sqlalchemy

# Update environment variables
DATABASE_URL=postgresql://grid_user:password@localhost:5432/grid_balancer
```

---

## Monitoring & Logging

### Application Logs

```bash
# View logs
tail -f logs/app.log

# Rotate logs daily
sudo apt-get install logrotate

# Logrotate configuration: /etc/logrotate.d/grid-balancer
/var/log/grid-balancer/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 nobody nobody
    sharedscripts
    postrotate
        systemctl reload grid-balancer > /dev/null 2>&1 || true
    endscript
}
```

### Health Monitoring

```bash
# Check health endpoint
curl https://grid-balancer.example.com/health

# Monitor with Prometheus
# Add to backend monitoring:
GET /metrics (returns Prometheus metrics)
```

### Set Up Alerts

```bash
# Email alerts via health check
curl -f https://grid-balancer.example.com/health || \
  send_alert "Grid Balancer is DOWN"

# System monitoring with New Relic or Datadog
pip install newrelic
newrelic-admin run-program uvicorn main:app
```

### Performance Monitoring

```bash
# Monitor system resources
top -p $(pgrep -f "uvicorn main:app")

# Check network connections
netstat -tan | grep 8000

# Monitor disk usage for data
du -sh data/
```

---

## Backup Strategy

### Automated Daily Backups

Create `/opt/grid-balancer/backup.sh`:

```bash
#!/bin/bash

BACKUP_DIR="/var/lib/grid-balancer/backups"
SOURCE_DIR="/opt/grid-balancer/data"
DATE=$(date +%Y-%m-%d)

# Create dated backup
tar -czf "$BACKUP_DIR/grid-data-$DATE.tar.gz" "$SOURCE_DIR"

# Keep only last 30 days
find "$BACKUP_DIR" -name "grid-data-*.tar.gz" -mtime +30 -delete

# Upload to cloud storage (optional)
aws s3 cp "$BACKUP_DIR/grid-data-$DATE.tar.gz" \
    s3://my-bucket/backups/
```

### Add to Crontab

```bash
# Run daily at 2 AM
0 2 * * * /opt/grid-balancer/backup.sh

# Install cron
sudo apt-get install cron
sudo systemctl enable cron
```

### Restore from Backup

```bash
# List backups
ls -la /var/lib/grid-balancer/backups/

# Restore
tar -xzf /var/lib/grid-balancer/backups/grid-data-2024-01-15.tar.gz \
    -C /opt/grid-balancer/
```

---

## Scaling

### Horizontal Scaling (Multiple Instances)

```bash
# Run multiple workers
uvicorn main:app --workers 4 --port 8000

# Load balancing with Nginx (see Nginx section)
upstream grid_balancer_backend {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
    server 127.0.0.1:8003;
}
```

### Kubernetes Deployment (EKS/GKE)

Create `k8s-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: grid-balancer
spec:
  replicas: 3
  selector:
    matchLabels:
      app: grid-balancer
  template:
    metadata:
      labels:
        app: grid-balancer
    spec:
      containers:
      - name: grid-balancer
        image: grid-balancer:latest
        ports:
        - containerPort: 8000
        env:
        - name: DEBUG
          value: "False"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
```

### Deploy to Kubernetes

```bash
kubectl apply -f k8s-deployment.yaml
kubectl scale deployment grid-balancer --replicas=5
kubectl rollout status deployment/grid-balancer
```

---

## Troubleshooting

### Port Already in Use

```bash
# Find process on port 8000
lsof -i :8000

# Kill process
kill -9 <PID>

# Or use different port
uvicorn main:app --port 8001
```

### High Memory Usage

```bash
# Check memory
free -h
ps aux | grep uvicorn

# Restart service
sudo systemctl restart grid-balancer
```

### Connection Refused

```bash
# Check if service is running
ps aux | grep uvicorn

# Check port listening
netstat -tuln | grep 8000

# Check firewall
sudo ufw status
sudo ufw allow 8000
```

### SSL Certificate Issues

```bash
# Verify certificate
openssl x509 -in /etc/letsencrypt/live/domain/fullchain.pem -text -noout

# Check expiration
openssl x509 -in /etc/letsencrypt/live/domain/cert.pem -noout -dates

# Renew manually
sudo certbot renew --force-renewal
```

### Database Connection Issues

```bash
# Test PostgreSQL connection
psql -U grid_user -d grid_balancer -h localhost

# Check connection string in .env
echo $DATABASE_URL

# Verify PostgreSQL is running
sudo systemctl status postgresql
```

### WebSocket Connection Issues

```bash
# Check WebSocket endpoint
curl -i -N -H "Connection: Upgrade" \
     -H "Upgrade: websocket" \
     http://localhost:8000/ws

# Monitor WebSocket traffic
tcpdump -i lo -n 'tcp port 8000'
```

---

## Performance Optimization

### FastAPI Tuning

```bash
# Use production ASGI server
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app

# Or Uvicorn with workers
uvicorn main:app --workers 4 --loop uvloop
```

### Database Optimization

```bash
# Add indexes to PostgreSQL
CREATE INDEX idx_grid_state_timestamp ON grid_state(timestamp);
CREATE INDEX idx_alerts_severity ON alerts(severity);
```

### Caching Strategy

```python
# Add response caching
from fastapi_cache2 import FastAPICache2
from fastapi_cache2.backends.redis import RedisBackend
from redis import asyncio as aioredis

redis = await aioredis.from_url("redis://localhost")
FastAPICache2.init(RedisBackend(redis), prefix="grid-balancer")
```

---

## Security Hardening

### Firewall Configuration

```bash
sudo ufw enable
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
```

### API Security

- ✅ CORS enabled for specific origins only
- ✅ Rate limiting implemented (100 requests/minute default)
- ✅ Input validation via Pydantic models
- ✅ SQL injection protection (prepared statements with ORM)
- ✅ HTTPS enforced in production

### Database Security

```bash
# PostgreSQL security
sudo -u postgres psql

# Create read-only user
CREATE USER read_only PASSWORD 'password';
GRANT SELECT ON ALL TABLES IN SCHEMA public TO read_only;
```

---

## Rollback Procedure

```bash
# Keep previous version
cp -r /opt/grid-balancer /opt/grid-balancer-backup-$(date +%Y%m%d)

# On failure, restore
sudo systemctl stop grid-balancer
sudo rm -rf /opt/grid-balancer
sudo cp -r /opt/grid-balancer-backup-YYYYMMDD /opt/grid-balancer
sudo systemctl start grid-balancer
```

---

## Support & Monitoring Services

| Service | Purpose | Link |
|---------|---------|------|
| Datadog | Monitoring & Logs | https://www.datadoghq.com |
| New Relic | APM & Monitoring | https://www.newrelic.com |
| PagerDuty | Alerting | https://www.pagerduty.com |
| StatusPage | Status Dashboard | https://www.statuspage.io |

---

**Questions?** Check the README.md for architecture details or QUICK_START.md for setup help.

**Version:** 1.0 | **Last Updated:** 2024
# Environment="PATH=/home/gridbalancer/intelligent-grid-balancer/venv/bin"
# ExecStart=/home/gridbalancer/intelligent-grid-balancer/venv/bin/uvicorn main:app \
#     --host 127.0.0.1 \
#     --port 8000 \
#     --workers 4 \
#     --log-config logging.ini
# Restart=always
# RestartSec=10
# 
# [Install]
# WantedBy=multi-user.target

# Enable service:
# sudo systemctl daemon-reload
# sudo systemctl enable grid-balancer
# sudo systemctl start grid-balancer

# Check status:
# sudo systemctl status grid-balancer
# sudo journalctl -u grid-balancer -f

# STEP 4: NGINX REVERSE PROXY
# =============================

# Create Nginx config:
# sudo nano /etc/nginx/sites-available/grid-balancer

# Content:
# upstream grid_balancer {
#     server 127.0.0.1:8000;
# }
# 
# server {
#     listen 80;
#     server_name yourdomain.com;
#     
#     client_max_body_size 20M;
#     
#     location / {
#         proxy_pass http://grid_balancer;
#         proxy_set_header Host $host;
#         proxy_set_header X-Real-IP $remote_addr;
#         proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
#         proxy_set_header X-Forwarded-Proto $scheme;
#     }
#     
#     location /ws {
#         proxy_pass http://grid_balancer;
#         proxy_http_version 1.1;
#         proxy_set_header Upgrade $http_upgrade;
#         proxy_set_header Connection "upgrade";
#         proxy_set_header Host $host;
#         proxy_set_header X-Real-IP $remote_addr;
#     }
# }

# Enable site:
# sudo ln -s /etc/nginx/sites-available/grid-balancer /etc/nginx/sites-enabled/
# sudo nginx -t
# sudo systemctl restart nginx

# STEP 5: SSL CERTIFICATE (Let's Encrypt)
# ========================================

# Install Certbot:
# sudo apt-get install certbot python3-certbot-nginx -y

# Get certificate:
# sudo certbot --nginx -d yourdomain.com

# Auto-renewal:
# sudo systemctl enable certbot.timer

# STEP 6: MONITORING
# ==================

# Install monitoring tools:
# sudo apt-get install htop iotop nethogs -y

# Setup log rotation:
# sudo nano /etc/logrotate.d/grid-balancer

# Content:
# /home/gridbalancer/intelligent-grid-balancer/logs/*.log {
#     daily
#     rotate 30
#     compress
#     delaycompress
#     notifempty
#     create 0640 gridbalancer gridbalancer
#     sharedscripts
#     postrotate
#         systemctl reload grid-balancer > /dev/null 2>&1 || true
#     endscript
# }

# STEP 7: BACKUP STRATEGY
# =======================

# Daily backup script:
# Create /home/gridbalancer/backup.sh

#!/bin/bash
# BACKUP_DIR="/backups/grid-balancer"
# APP_DIR="/home/gridbalancer/intelligent-grid-balancer"
# DATE=$(date +%Y%m%d_%H%M%S)
# 
# mkdir -p $BACKUP_DIR
# tar -czf $BACKUP_DIR/data_$DATE.tar.gz $APP_DIR/data/
# tar -czf $BACKUP_DIR/config_$DATE.tar.gz $APP_DIR/.env
# 
# # Upload to cloud storage (AWS S3)
# aws s3 cp $BACKUP_DIR/data_$DATE.tar.gz s3://your-bucket/backups/
# 
# # Cleanup old backups (keep 30 days)
# find $BACKUP_DIR -type f -mtime +30 -delete

# Make executable & add to crontab:
# chmod +x /home/gridbalancer/backup.sh
# crontab -e
# 0 2 * * * /home/gridbalancer/backup.sh

# STEP 8: SECURITY
# ================

# 1. Firewall rules:
#    sudo ufw allow 22/tcp
#    sudo ufw allow 80/tcp
#    sudo ufw allow 443/tcp
#    sudo ufw enable
#
# 2. SSH hardening:
#    - Disable password auth
#    - Use SSH keys only
#    - Change default port
#
# 3. Application security:
#    - Enable API authentication
#    - Add rate limiting
#    - Use HTTPS only
#    - Enable CORS restrictions
#
# 4. Database security (if using PostgreSQL):
#    - Change default password
#    - Enable SSL connections
#    - Restrict network access

# STEP 9: PERFORMANCE TUNING
# ===========================

# 1. Increase worker processes:
#    --workers 8  (match CPU cores)
#
# 2. Increase max connections:
#    worker_connections 1024
#
# 3. Enable HTTP compression:
#    gzip on; in nginx config
#
# 4. Enable caching:
#    Cache predictions, historical data
#
# 5. Optimize database queries:
#    Use indexes, connection pooling

# STEP 10: TESTING DEPLOYMENT
# ============================

# 1. Health check:
#    curl https://yourdomain.com/health
#
# 2. API test:
#    curl https://yourdomain.com/grid/status
#
# 3. WebSocket test:
#    websocat wss://yourdomain.com/ws
#
# 4. Load testing:
#    ab -n 1000 -c 100 https://yourdomain.com/health

# MONITORING & ALERTS
# ====================

# Setup monitoring with:
# - Prometheus (metrics)
# - Grafana (dashboards)
# - ELK Stack (logs)
# - PagerDuty (alerts)

# Recommended alerts:
# - Service down
# - High error rate
# - High memory/CPU usage
# - Disk space low
# - Battery critical

# TROUBLESHOOTING
# ===============

# Check service status:
# sudo systemctl status grid-balancer

# View recent logs:
# sudo journalctl -u grid-balancer -n 50

# Test Nginx config:
# sudo nginx -t

# Check port binding:
# sudo netstat -tlnp | grep 8000

# CPU/Memory usage:
# ps aux | grep uvicorn
# top -p $(pgrep -f uvicorn | tr '\n' ',')

# Network connections:
# netstat -an | grep :8000

# UPGRADES & DOWNTIME
# ===================

# Zero-downtime upgrade:
# 1. Deploy new version to secondary server
# 2. Test thoroughly
# 3. Switch load balancer to new version
# 4. Decommission old version

# Rolling update:
# 1. Update code on server
# 2. Reload systemd: sudo systemctl daemon-reload
# 3. Restart service: sudo systemctl restart grid-balancer
# 4. Verify: curl https://yourdomain.com/health

print("Production deployment guide completed. See comments above for detailed steps.")
