# Production Deployment Guide

## Overview

This guide covers the complete deployment process for AlphaShield in production environments. AlphaShield is a sophisticated AI-powered autonomous trading and loan management system that requires careful setup and monitoring.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Database Setup](#database-setup)
4. [API Keys and Secrets](#api-keys-and-secrets)
5. [Deployment Options](#deployment-options)
6. [Configuration](#configuration)
7. [Monitoring and Observability](#monitoring-and-observability)
8. [Backup and Disaster Recovery](#backup-and-disaster-recovery)
9. [Security Considerations](#security-considerations)
10. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

- **OS**: Linux (Ubuntu 22.04 LTS recommended) or compatible
- **Python**: 3.11 or 3.12
- **Memory**: 8GB RAM minimum, 16GB recommended
- **Storage**: 100GB SSD minimum for database and logs
- **Network**: Stable internet connection for API calls

### Required Accounts

- MongoDB Atlas account (or self-hosted MongoDB 7.0+)
- Alpaca Markets account (paper or live trading)
- Voyage AI API key (for embeddings)
- Optional: D-Wave Leap account (for quantum optimization)
- Optional: OpenAI API key (for LLM agents)

### Required Tools

```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install -y \
    python3.11 \
    python3.11-venv \
    python3-pip \
    git \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev
```

---

## Environment Setup

### 1. Clone Repository

```bash
git clone https://github.com/wildhash/AlphaShield.git
cd AlphaShield
```

### 2. Create Virtual Environment

```bash
python3.11 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt

# For development/testing
pip install -r requirements-dev.txt
```

### 4. Verify Installation

```bash
python -c "import alphashield; print('AlphaShield installed successfully')"
pytest tests/ -v --tb=short
```

---

## Database Setup

### MongoDB Atlas (Recommended for Production)

1. **Create Cluster**
   - Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
   - Create new M10+ cluster (M30 recommended for production)
   - Select region closest to your application

2. **Configure Network Access**
   - Add your application server IPs to whitelist
   - Or use VPC peering for secure access

3. **Create Database User**
   - Create user with `readWrite` role on `alphashield` database
   - Use strong password (min 32 characters)

4. **Get Connection String**
   ```
   mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/alphashield?retryWrites=true&w=majority
   ```

### Self-Hosted MongoDB

```bash
# Install MongoDB 7.0
wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
sudo apt-get update
sudo apt-get install -y mongodb-org

# Start MongoDB
sudo systemctl start mongod
sudo systemctl enable mongod

# Create database and user
mongosh <<EOF
use alphashield
db.createUser({
  user: "alphashield_user",
  pwd: "STRONG_PASSWORD_HERE",
  roles: [{ role: "readWrite", db: "alphashield" }]
})
EOF
```

### Database Indexes

Create indexes for optimal performance:

```javascript
// Connect to MongoDB
use alphashield

// Context capsules
db.context_capsules.createIndex({ "borrower_id": 1, "timestamp": -1 })
db.context_capsules.createIndex({ "embedding": "vector" })

// Replay buffer
db.replay_buffer.createIndex({ "agent": 1, "timestamp": -1 })
db.replay_buffer.createIndex({ "episode_id": 1 })

// Policies
db.policies.createIndex({ "agent": 1, "version": -1 })

// Trading decisions
db.trading_decisions.createIndex({ "borrower_id": 1, "timestamp": -1 })
db.trading_decisions.createIndex({ "strategy": 1 })

// Loan applications
db.loan_applications.createIndex({ "borrower_id": 1, "status": 1 })
db.loan_applications.createIndex({ "created_at": -1 })
```

---

## API Keys and Secrets

### Environment Variables

Create a `.env` file (never commit this to git):

```bash
# MongoDB
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/alphashield

# Alpaca Trading (Paper Trading)
ALPACA_API_KEY=PK...
ALPACA_SECRET_KEY=...
ALPACA_BASE_URL=https://paper-api.alpaca.markets

# For Live Trading (use with extreme caution!)
# ALPACA_API_KEY=AK...
# ALPACA_SECRET_KEY=...
# ALPACA_BASE_URL=https://api.alpaca.markets

# Voyage AI (Embeddings)
VOYAGE_API_KEY=pa-...

# OpenAI (optional, for LLM agents)
OPENAI_API_KEY=sk-...

# D-Wave Quantum (optional)
DWAVE_API_TOKEN=...

# Application Settings
ENVIRONMENT=production
LOG_LEVEL=INFO
MAX_WORKERS=4

# Security
SECRET_KEY=generate_a_strong_random_key_here
JWT_SECRET=another_strong_random_key

# Monitoring
SENTRY_DSN=https://...@sentry.io/...
```

### Generate Secrets

```bash
# Generate strong random secrets
python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"
python -c "import secrets; print('JWT_SECRET=' + secrets.token_urlsafe(32))"
```

### Secure Secret Management

For production, use a secret manager:

**AWS Secrets Manager**:
```bash
aws secretsmanager create-secret \
    --name alphashield/production \
    --secret-string file://secrets.json
```

**HashiCorp Vault**:
```bash
vault kv put secret/alphashield @secrets.json
```

---

## Deployment Options

### Option 1: Docker Deployment (Recommended)

#### Build Image

```bash
docker build -t alphashield:latest .
```

#### Run with Docker Compose

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  alphashield:
    image: alphashield:latest
    restart: always
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    
  redis:
    image: redis:7-alpine
    restart: always
    volumes:
      - redis_data:/data
    
  prometheus:
    image: prom/prometheus
    restart: always
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus

volumes:
  redis_data:
  prometheus_data:
```

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Option 2: Kubernetes Deployment

#### Create Namespace

```bash
kubectl create namespace alphashield
```

#### Apply Configurations

```bash
# Secrets
kubectl create secret generic alphashield-secrets \
    --from-env-file=.env \
    -n alphashield

# Deployment
kubectl apply -f k8s/deployment.yaml -n alphashield

# Service
kubectl apply -f k8s/service.yaml -n alphashield

# Ingress (optional)
kubectl apply -f k8s/ingress.yaml -n alphashield
```

**Example deployment.yaml**:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: alphashield
  namespace: alphashield
spec:
  replicas: 3
  selector:
    matchLabels:
      app: alphashield
  template:
    metadata:
      labels:
        app: alphashield
    spec:
      containers:
      - name: alphashield
        image: alphashield:latest
        ports:
        - containerPort: 8000
        envFrom:
        - secretRef:
            name: alphashield-secrets
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
```

### Option 3: Systemd Service (Traditional)

Create service file `/etc/systemd/system/alphashield.service`:

```ini
[Unit]
Description=AlphaShield Trading Engine
After=network.target

[Service]
Type=simple
User=alphashield
Group=alphashield
WorkingDirectory=/opt/alphashield
Environment="PATH=/opt/alphashield/venv/bin"
EnvironmentFile=/opt/alphashield/.env
ExecStart=/opt/alphashield/venv/bin/python -m alphashield.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable alphashield
sudo systemctl start alphashield
```

---

## Configuration

### Trading Configuration

Edit `config/trading.yaml`:

```yaml
trading:
  mode: paper  # paper or live
  
  # Risk management
  risk:
    max_position_size: 0.15  # 15% max per position
    max_daily_loss: 0.05     # 5% daily loss limit
    max_drawdown: 0.20       # 20% max drawdown
    
  # Rebalancing
  rebalance:
    frequency: daily
    min_trade_size: 100      # Minimum $100 trades
    max_slippage: 0.01       # 1% max slippage
    
  # Backtesting
  backtest:
    initial_capital: 100000
    commission: 0.001        # 10 bps
    slippage: 0.0005         # 5 bps

quantum:
  enabled: false  # Enable when D-Wave token available
  timeout: 5      # seconds
  fallback: classical
```

### RL Configuration

Edit `config/rl.yaml`:

```yaml
rl:
  training:
    window_days: 60
    min_samples: 100
    deployment_threshold: 0.05  # 5% improvement required
    
  agents:
    Lender:
      n_actions: 5
      context_dim: 10
      alpha: 1.5
      
    AlphaTrading:
      n_actions: 5
      context_dim: 15
      alpha: 1.2
      
    SpendingGuard:
      n_actions: 3
      context_dim: 8
      alpha: 1.8
```

---

## Monitoring and Observability

### Logging

Logs are written to `logs/` directory:

```bash
# View application logs
tail -f logs/alphashield.log

# View trading logs
tail -f logs/trading.log

# View training logs
tail -f logs/training_*.log
```

### Metrics

AlphaShield exposes Prometheus metrics at `/metrics`:

```yaml
# monitoring/prometheus.yml
scrape_configs:
  - job_name: 'alphashield'
    static_configs:
      - targets: ['localhost:8000']
    scrape_interval: 15s
```

**Key Metrics**:
- `alphashield_trades_total` - Total number of trades
- `alphashield_pnl_total` - Cumulative P&L
- `alphashield_portfolio_value` - Current portfolio value
- `alphashield_agent_decisions_total` - Agent decision counts
- `alphashield_rl_training_duration` - Training duration

### Dashboards

Import Grafana dashboard from `monitoring/grafana_dashboard.json`:

```bash
# Start Grafana
docker run -d -p 3000:3000 grafana/grafana

# Import dashboard
curl -X POST http://admin:admin@localhost:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d @monitoring/grafana_dashboard.json
```

### Alerting

Configure alerts in `monitoring/alerts.yml`:

```yaml
groups:
  - name: alphashield
    rules:
      - alert: HighDailyLoss
        expr: alphashield_daily_pnl < -5000
        for: 5m
        annotations:
          summary: "High daily loss detected"
          
      - alert: TrainingFailed
        expr: alphashield_training_failures_total > 0
        for: 1m
        annotations:
          summary: "RL training failed"
```

---

## Backup and Disaster Recovery

### Database Backups

**Automated MongoDB Backups**:

```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/mongodb"
DB_NAME="alphashield"

# Create backup
mongodump --uri="$MONGODB_URI" \
  --db="$DB_NAME" \
  --out="$BACKUP_DIR/$DATE"

# Compress
tar -czf "$BACKUP_DIR/$DATE.tar.gz" "$BACKUP_DIR/$DATE"
rm -rf "$BACKUP_DIR/$DATE"

# Upload to S3
aws s3 cp "$BACKUP_DIR/$DATE.tar.gz" s3://alphashield-backups/

# Retain last 30 days
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +30 -delete
```

Add to crontab:
```bash
0 2 * * * /opt/alphashield/backup.sh
```

### Disaster Recovery Plan

1. **Database Restoration**
   ```bash
   # Download backup
   aws s3 cp s3://alphashield-backups/20241209_020000.tar.gz .
   
   # Extract
   tar -xzf 20241209_020000.tar.gz
   
   # Restore
   mongorestore --uri="$MONGODB_URI" dump/
   ```

2. **Configuration Restore**
   - Keep `.env` and `config/` in version control (encrypted)
   - Or store in secret manager

3. **Code Deployment**
   - Tag releases in git
   - Deploy from known good commit

---

## Security Considerations

### API Key Rotation

Rotate keys every 90 days:

```bash
# 1. Generate new Alpaca keys in dashboard
# 2. Update .env with new keys
# 3. Restart application
# 4. Revoke old keys after 24 hours
```

### Access Control

- Use firewall rules to restrict access
- Enable MongoDB authentication
- Use TLS for all connections
- Implement API authentication/authorization

### Audit Logging

All trading decisions are logged:

```python
# Audit logs stored in MongoDB
db.audit_logs.find({
    "action": "trade_executed",
    "timestamp": {"$gte": ISODate("2024-12-01")}
})
```

---

## Troubleshooting

### Common Issues

**Issue**: MongoDB connection timeout

```bash
# Check connectivity
mongosh "$MONGODB_URI"

# Check IP whitelist in Atlas
# Verify network security groups
```

**Issue**: Alpaca API authentication failed

```bash
# Verify credentials
echo $ALPACA_API_KEY
echo $ALPACA_SECRET_KEY

# Test connection
curl -H "APCA-API-KEY-ID: $ALPACA_API_KEY" \
     -H "APCA-API-SECRET-KEY: $ALPACA_SECRET_KEY" \
     https://paper-api.alpaca.markets/v2/account
```

**Issue**: High memory usage

```bash
# Check memory usage
ps aux | grep alphashield

# Reduce MAX_WORKERS in .env
MAX_WORKERS=2

# Enable garbage collection logging
export PYTHONMALLOC=malloc
```

### Debug Mode

Enable debug logging:

```bash
export LOG_LEVEL=DEBUG
python -m alphashield.main
```

### Health Checks

```bash
# Application health
curl http://localhost:8000/health

# Database health
mongosh --eval "db.adminCommand('ping')" "$MONGODB_URI"

# Broker connectivity
python -c "from alphashield.trading.broker_adapters import AlpacaAdapter; AlpacaAdapter().get_account()"
```

---

## Production Checklist

Before going live:

- [ ] All environment variables configured
- [ ] Database backups automated
- [ ] Monitoring and alerts configured
- [ ] Logs properly configured and rotated
- [ ] API keys secured (not in code/git)
- [ ] Paper trading tested extensively
- [ ] Risk limits configured appropriately
- [ ] Disaster recovery plan documented
- [ ] Team trained on operations
- [ ] Runbooks created for common tasks
- [ ] Security audit completed
- [ ] Performance testing completed
- [ ] Start with small capital allocation
- [ ] Monitor closely for first 2 weeks

---

## Support

- **Documentation**: [GitHub Wiki](https://github.com/wildhash/AlphaShield/wiki)
- **Issues**: [GitHub Issues](https://github.com/wildhash/AlphaShield/issues)
- **Email**: support@alphashield.ai (placeholder)

---

## License

MIT License - See LICENSE file for details
