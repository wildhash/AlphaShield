# Production Deployment Guide

This guide provides comprehensive instructions for deploying AlphaShield to production environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Architecture Overview](#architecture-overview)
3. [Infrastructure Setup](#infrastructure-setup)
4. [Deployment Procedures](#deployment-procedures)
5. [Configuration Management](#configuration-management)
6. [Monitoring & Alerting](#monitoring--alerting)
7. [Backup & Recovery](#backup--recovery)
8. [Runbooks](#runbooks)
9. [Security Checklist](#security-checklist)

---

## Prerequisites

### Required Accounts & Services

| Service | Purpose | Required Plan |
|---------|---------|---------------|
| MongoDB Atlas | Primary database | M10+ for production |
| Voyage AI | Embeddings API | Growth plan recommended |
| Alpaca | Paper/Live trading | Paper (free) or Live |
| D-Wave Leap | Quantum optimization | Free tier or Professional |
| Docker Hub / ECR | Container registry | Any |
| GitHub Actions | CI/CD | Free tier works |

### Required Secrets

Configure these in GitHub Actions secrets:

```bash
# Database
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/alphashield

# AI/ML Services
VOYAGE_API_KEY=vo-xxxxxxxxxxxx
OPENAI_API_KEY=sk-xxxxxxxxxxxx  # Optional

# Trading (Paper)
ALPACA_API_KEY_PAPER=PKxxxxxxxxxxxx
ALPACA_SECRET_KEY_PAPER=xxxxxxxxxxxx

# Trading (Live) - Only for production
ALPACA_API_KEY_LIVE=AKxxxxxxxxxxxx
ALPACA_SECRET_KEY_LIVE=xxxxxxxxxxxx

# Quantum Computing
DWAVE_API_TOKEN=DEV-xxxxxxxxxxxx

# Docker Registry
DOCKER_USERNAME=your-username
DOCKER_PASSWORD=your-token

# Monitoring
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxx
```

---

## Architecture Overview

### Production Stack

```
┌─────────────────────────────────────────────────────────────────┐
│                      Load Balancer (nginx/ALB)                  │
└─────────────────────────────────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
        ▼                       ▼                       ▼
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│  AlphaShield │       │  AlphaShield │       │  Dashboard   │
│   API (x3)   │       │  Worker (x2) │       │  (Streamlit) │
└──────────────┘       └──────────────┘       └──────────────┘
        │                       │                       │
        └───────────────────────┼───────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
        ▼                       ▼                       ▼
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│   MongoDB    │       │    Redis     │       │  Prometheus  │
│    Atlas     │       │   (Cache)    │       │   + Grafana  │
└──────────────┘       └──────────────┘       └──────────────┘
```

### Component Responsibilities

| Component | Responsibility | Replicas | Resources |
|-----------|---------------|----------|-----------|
| API Server | HTTP endpoints, orchestration | 3 | 2 CPU, 4GB RAM |
| Worker | Background tasks, RL training | 2 | 4 CPU, 8GB RAM |
| Dashboard | Monitoring UI | 1 | 1 CPU, 2GB RAM |
| Redis | Caching, rate limiting | 1 | 1 CPU, 2GB RAM |

---

## Infrastructure Setup

### Docker Deployment

1. **Build and push images:**

```bash
# Build production image
docker build -t alphashield:latest .

# Tag for registry
docker tag alphashield:latest your-registry/alphashield:v1.0.0

# Push to registry
docker push your-registry/alphashield:v1.0.0
```

2. **Deploy with Docker Compose:**

```bash
# Production deployment
docker-compose -f docker-compose.yml up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f alphashield
```

### Kubernetes Deployment

1. **Create namespace:**

```bash
kubectl create namespace alphashield
```

2. **Create secrets:**

```bash
kubectl create secret generic alphashield-secrets \
  --from-literal=mongodb-uri='mongodb+srv://...' \
  --from-literal=voyage-api-key='vo-xxx' \
  --from-literal=alpaca-api-key='PKxxx' \
  --from-literal=alpaca-secret-key='xxx' \
  -n alphashield
```

3. **Deploy application:**

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: alphashield-api
  namespace: alphashield
spec:
  replicas: 3
  selector:
    matchLabels:
      app: alphashield-api
  template:
    metadata:
      labels:
        app: alphashield-api
    spec:
      containers:
      - name: api
        image: your-registry/alphashield:v1.0.0
        ports:
        - containerPort: 8000
        env:
        - name: MONGODB_URI
          valueFrom:
            secretKeyRef:
              name: alphashield-secrets
              key: mongodb-uri
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
          initialDelaySeconds: 5
          periodSeconds: 5
```

```bash
kubectl apply -f k8s/deployment.yaml
```

---

## Deployment Procedures

### Standard Deployment (CI/CD)

The recommended deployment path uses GitHub Actions:

1. **Merge to main branch** triggers staging deployment
2. **Manual approval** required for production
3. **Automated rollback** on health check failure

```bash
# View deployment status
gh run list --workflow=deploy-production.yml

# Trigger manual deployment
gh workflow run deploy-production.yml
```

### Manual Deployment

For emergency deployments:

```bash
# 1. SSH to deployment server
ssh deploy@production.alphashield.com

# 2. Pull latest image
docker pull your-registry/alphashield:v1.0.0

# 3. Stop current deployment
docker-compose down

# 4. Start new deployment
docker-compose up -d

# 5. Verify health
curl http://localhost:8000/health
```

### Blue-Green Deployment

For zero-downtime deployments:

```bash
# 1. Deploy to green environment
docker-compose -f docker-compose.green.yml up -d

# 2. Verify green environment
./scripts/verify_deployment.sh green

# 3. Switch traffic to green
./scripts/switch_traffic.sh green

# 4. Drain blue environment
docker-compose -f docker-compose.blue.yml down
```

---

## Configuration Management

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `ENVIRONMENT` | Deployment environment | `development` | Yes |
| `LOG_LEVEL` | Logging verbosity | `INFO` | No |
| `MONGODB_URI` | MongoDB connection string | - | Yes |
| `VOYAGE_API_KEY` | Voyage AI API key | - | Yes |
| `ALPACA_API_KEY` | Alpaca API key | - | For trading |
| `ALPACA_SECRET_KEY` | Alpaca secret key | - | For trading |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379` | No |
| `PROMETHEUS_PORT` | Prometheus metrics port | `9090` | No |

### Feature Flags

Feature flags are managed in `config/features.yaml`:

```yaml
features:
  quantum_optimization: true
  live_trading: false  # Enable only in production
  rl_auto_training: true
  cross_agent_coordination: true
  
trading:
  paper_mode: true  # Set to false for live trading
  max_position_size: 10000
  risk_tolerance: 0.02
```

---

## Monitoring & Alerting

### Prometheus Metrics

Available at `:9090/metrics`:

```
# Training metrics
alphashield_training_episodes_total
alphashield_training_reward_avg
alphashield_training_loss_current

# Trading metrics
alphashield_orders_submitted_total
alphashield_orders_filled_total
alphashield_portfolio_value_usd

# System metrics
alphashield_api_requests_total
alphashield_api_latency_seconds
alphashield_db_connections_active
```

### Grafana Dashboards

Import dashboards from `monitoring/grafana/`:

1. **RL Training Dashboard** - Training progress, rewards, losses
2. **Trading Dashboard** - Orders, positions, P&L
3. **System Dashboard** - API health, resource usage

### Alert Rules

Configure in `monitoring/alertmanager/alerts.yml`:

```yaml
groups:
- name: alphashield
  rules:
  - alert: HighErrorRate
    expr: rate(alphashield_api_errors_total[5m]) > 0.1
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: High API error rate
      
  - alert: TrainingFailed
    expr: alphashield_training_last_success_timestamp < (time() - 86400)
    for: 1h
    labels:
      severity: warning
    annotations:
      summary: Nightly training has not run successfully
      
  - alert: LowReward
    expr: alphashield_training_reward_avg < 0.3
    for: 24h
    labels:
      severity: warning
    annotations:
      summary: Agent reward has dropped significantly
```

---

## Backup & Recovery

### Database Backups

MongoDB Atlas provides automated backups. For additional safety:

```bash
# Manual backup
mongodump --uri="$MONGODB_URI" --out=/backups/$(date +%Y%m%d)

# Restore from backup
mongorestore --uri="$MONGODB_URI" /backups/20240115/
```

### Policy Backups

RL policies are versioned and stored in MongoDB:

```python
from alphashield.rl.policy import PolicyManager

pm = PolicyManager()

# Export current policies
pm.export_policies("/backups/policies/")

# Import policies (rollback)
pm.import_policies("/backups/policies/v30/")
```

### Disaster Recovery

1. **RTO (Recovery Time Objective)**: 1 hour
2. **RPO (Recovery Point Objective)**: 24 hours

Recovery procedure:
1. Restore MongoDB from Atlas backup
2. Deploy latest stable Docker image
3. Import last known good policies
4. Verify system health
5. Resume trading in paper mode first

---

## Runbooks

### Runbook: Service Restart

**Trigger**: High memory usage, unresponsive API

```bash
# 1. Check current status
docker-compose ps

# 2. Restart specific service
docker-compose restart alphashield

# 3. Verify recovery
curl http://localhost:8000/health

# 4. Check logs for errors
docker-compose logs --tail=100 alphashield
```

### Runbook: Policy Rollback

**Trigger**: Agent performance degradation

```bash
# 1. Identify last good version
python -c "from alphashield.rl.policy import PolicyManager; pm = PolicyManager(); print(pm.list_versions('alpha_trading'))"

# 2. Rollback to previous version
python -c "from alphashield.rl.policy import PolicyManager; pm = PolicyManager(); pm.rollback('alpha_trading', 'v29')"

# 3. Verify rollback
python -c "from alphashield.rl.policy import PolicyManager; pm = PolicyManager(); print(pm.get_active_version('alpha_trading'))"
```

### Runbook: Trading Halt

**Trigger**: Unusual market conditions, system issues

```bash
# 1. Stop all trading immediately
python -c "
from alphashield.trading.adapters import AlpacaAdapter
import asyncio

async def halt():
    adapter = AlpacaAdapter()
    await adapter.connect()
    await adapter.cancel_all_orders()
    await adapter.close_all_positions()
    print('Trading halted - all orders cancelled, positions closed')

asyncio.run(halt())
"

# 2. Disable trading feature flag
# Update config/features.yaml: live_trading: false

# 3. Restart services with trading disabled
docker-compose restart
```

### Runbook: Database Connection Issues

**Trigger**: MongoDB connection failures

```bash
# 1. Check MongoDB Atlas status
# Visit: https://cloud.mongodb.com/

# 2. Verify network connectivity
nc -zv cluster0.mongodb.net 27017

# 3. Check connection string
echo $MONGODB_URI | grep -o 'mongodb+srv://[^@]*'

# 4. Test connection
python -c "from pymongo import MongoClient; c = MongoClient('$MONGODB_URI'); print(c.list_database_names())"

# 5. If IP whitelist issue, update in Atlas console
```

---

## Security Checklist

### Pre-Deployment

- [ ] All secrets stored in GitHub Actions secrets
- [ ] No credentials in code or config files
- [ ] Docker images scanned for vulnerabilities
- [ ] Dependencies updated and audited
- [ ] API authentication enabled
- [ ] Rate limiting configured

### Network Security

- [ ] HTTPS enforced for all endpoints
- [ ] Database accessible only from application
- [ ] Redis not exposed to public internet
- [ ] Firewall rules configured

### Access Control

- [ ] Separate API keys for paper/live trading
- [ ] Minimal permissions for service accounts
- [ ] Audit logging enabled
- [ ] Two-factor authentication for cloud consoles

### Monitoring

- [ ] Alerting configured for security events
- [ ] Failed authentication attempts logged
- [ ] Unusual trading activity monitored
- [ ] Resource usage tracked

---

## Appendix

### Useful Commands

```bash
# View running containers
docker ps

# Check container resource usage
docker stats

# View application logs
docker-compose logs -f alphashield --tail=100

# Execute command in container
docker-compose exec alphashield python -c "print('Hello')"

# Database shell
docker-compose exec mongodb mongosh

# Redis CLI
docker-compose exec redis redis-cli

# Run tests in container
docker-compose exec alphashield pytest tests/ -v

# Check disk usage
df -h

# Monitor system resources
htop
```

### Support Contacts

| Role | Contact | Escalation Time |
|------|---------|-----------------|
| On-Call Engineer | #alphashield-oncall | Immediate |
| Team Lead | @wildhash | 30 minutes |
| Infrastructure | @infra-team | 1 hour |

---

*Last Updated: January 2025*
*Version: 1.0*
