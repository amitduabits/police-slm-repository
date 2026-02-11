# Deployment Guide

## Gujarat Police AI Investigation Support System - Production Deployment

**Version:** 0.1.0
**Target Environment:** On-Premise, Air-Gapped
**Last Updated:** February 2026

---

## Table of Contents

1. [Overview](#overview)
2. [System Requirements](#system-requirements)
3. [Pre-Deployment Checklist](#pre-deployment-checklist)
4. [Docker Compose Setup](#docker-compose-setup)
5. [Air-Gapped Deployment](#air-gapped-deployment)
6. [Security Hardening](#security-hardening)
7. [SSL/TLS Configuration](#ssltls-configuration)
8. [Backup & Recovery](#backup--recovery)
9. [Monitoring & Logging](#monitoring--logging)
10. [Performance Tuning](#performance-tuning)
11. [Disaster Recovery](#disaster-recovery)
12. [Troubleshooting](#troubleshooting)

---

## Overview

This document provides comprehensive instructions for deploying the Gujarat Police SLM system in a production environment. The system is designed for on-premise, air-gapped deployment to ensure data sovereignty and security.

### Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Production Environment                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   NGINX      │  │  Frontend    │  │  FastAPI     │     │
│  │ (Reverse     │─▶│   (React)    │◀─│   Backend    │     │
│  │  Proxy)      │  │              │  │              │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│         │                                      │            │
│         │                                      ▼            │
│         │                          ┌──────────────┐        │
│         │                          │  PostgreSQL  │        │
│         │                          │  (Metadata)  │        │
│         │                          └──────────────┘        │
│         │                                      │            │
│         ▼                                      ▼            │
│  ┌──────────────┐                  ┌──────────────┐       │
│  │  Prometheus  │                  │   ChromaDB   │       │
│  │  + Grafana   │                  │   (Vectors)  │       │
│  │ (Monitoring) │                  └──────────────┘       │
│  └──────────────┘                           │              │
│         │                                   ▼              │
│         │                          ┌──────────────┐       │
│         │                          │    Redis     │       │
│         │                          │   (Cache)    │       │
│         │                          └──────────────┘       │
│         ▼                                   │              │
│  ┌──────────────┐                          ▼              │
│  │    Backup    │                  ┌──────────────┐      │
│  │   Service    │                  │ Model Server │      │
│  │ (Automated)  │                  │ (Mistral 7B) │      │
│  └──────────────┘                  └──────────────┘      │
│                                                            │
└─────────────────────────────────────────────────────────────┘
```

### Service Inventory

| Service | Purpose | Port | Critical |
|---------|---------|------|----------|
| NGINX | Reverse proxy, SSL termination | 80, 443 | Yes |
| Frontend | React dashboard | 3000 (internal) | Yes |
| API | FastAPI backend | 8000 (internal) | Yes |
| PostgreSQL | Metadata storage | 5432 (internal) | Yes |
| ChromaDB | Vector embeddings | 8100 (internal) | Yes |
| Redis | Caching | 6379 (internal) | No |
| Model Server | Mistral 7B inference | 8080 (internal) | Yes |
| Prometheus | Metrics collection | 9090 (internal) | No |
| Grafana | Dashboards | 3001 (internal) | No |
| Backup | Automated backups | - | Yes |

---

## System Requirements

### Hardware Requirements

**Minimum Production Setup:**
- CPU: 8 cores (Intel Xeon or AMD EPYC)
- RAM: 32 GB
- Storage: 500 GB SSD (1 TB recommended)
- Network: 1 Gbps

**Recommended Production Setup:**
- CPU: 16 cores (Intel Xeon Silver 4316 or equivalent)
- RAM: 64 GB
- Storage: 2 TB NVMe SSD
- GPU: NVIDIA T4 or better (optional, for faster inference)
- Network: 10 Gbps
- Redundant power supply

**Storage Breakdown:**
- Operating System: 50 GB
- Docker images: 20 GB
- PostgreSQL database: 50 GB
- ChromaDB vectors: 100 GB
- Model files: 10 GB
- Document storage: 200 GB
- Logs: 20 GB
- Backups: 300 GB
- **Total Required:** ~750 GB

### Software Requirements

**Operating System:**
- Ubuntu Server 22.04 LTS (recommended)
- RHEL 8.x / Rocky Linux 8.x
- Debian 11 or newer

**Required Software:**
- Docker Engine 24.0+ or Docker Desktop
- Docker Compose v2.20+
- Git 2.30+
- Python 3.11+ (for setup scripts)
- OpenSSL 1.1.1+

**Optional:**
- NVIDIA Docker runtime (for GPU support)
- HAProxy or NGINX (external load balancer)

### Network Requirements

**Ports (Internal):**
- 80/443: NGINX (HTTP/HTTPS)
- 5432: PostgreSQL
- 6379: Redis
- 8000: FastAPI
- 8080: Model Server
- 8100: ChromaDB
- 9090: Prometheus
- 3000: Frontend
- 3001: Grafana

**Firewall Rules:**
- Allow inbound: 80/443 (HTTPS only in production)
- Allow outbound: None (air-gapped)
- Internal network: All containers on bridge network

---

## Pre-Deployment Checklist

### Infrastructure Preparation

- [ ] Server hardware meets minimum requirements
- [ ] Operating system installed and updated
- [ ] Static IP address configured
- [ ] Hostname and DNS configured
- [ ] Firewall rules configured
- [ ] SSL certificates obtained
- [ ] Backup storage configured
- [ ] Monitoring infrastructure ready

### Software Preparation

- [ ] Docker Engine installed
- [ ] Docker Compose installed
- [ ] Git installed
- [ ] Project repository cloned
- [ ] Environment variables configured
- [ ] SSL certificates copied to server
- [ ] Data directories created
- [ ] Log rotation configured

### Security Preparation

- [ ] Security audit completed
- [ ] Access controls defined
- [ ] Encryption keys generated
- [ ] JWT secrets generated
- [ ] Database passwords generated
- [ ] API keys secured
- [ ] Audit logging enabled
- [ ] Backup encryption configured

### Data Preparation

- [ ] Legal documents collected
- [ ] Document ingestion completed
- [ ] Embeddings generated
- [ ] Database initialized
- [ ] Test users created
- [ ] Section mappings loaded
- [ ] Model files downloaded

---

## Docker Compose Setup

### Installation

**1. Install Docker Engine (Ubuntu 22.04):**

```bash
# Update package index
sudo apt-get update

# Install prerequisites
sudo apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# Add Docker's official GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Set up stable repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Verify installation
docker --version
docker compose version

# Add user to docker group (optional)
sudo usermod -aG docker $USER
# Log out and back in for group changes to take effect
```

**2. Install Docker Compose V2:**

```bash
# Already included with docker-compose-plugin above
# Verify installation
docker compose version
# Should output: Docker Compose version v2.20.0 or higher
```

**3. Configure Docker for Production:**

Create `/etc/docker/daemon.json`:

```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "default-address-pools": [
    {
      "base": "172.28.0.0/16",
      "size": 24
    }
  ],
  "storage-driver": "overlay2",
  "live-restore": true
}
```

Restart Docker:
```bash
sudo systemctl restart docker
```

### Environment Configuration

**1. Create .env file:**

```bash
cd /opt/gujpol-slm
cp .env.example .env
```

**2. Edit .env with production values:**

```bash
# Environment
APP_ENV=production

# Security (CHANGE THESE!)
JWT_SECRET_KEY=$(openssl rand -hex 32)
ENCRYPTION_KEY=$(openssl rand -hex 32)
POSTGRES_PASSWORD=$(openssl rand -base64 32)
REDIS_PASSWORD=$(openssl rand -base64 32)

# Database
POSTGRES_DB=gujpol_slm
POSTGRES_USER=gujpol_admin
POSTGRES_HOST=db-postgres
POSTGRES_PORT=5432

# Redis
REDIS_HOST=cache-redis
REDIS_PORT=6379

# ChromaDB
CHROMA_HOST=db-chroma
CHROMA_PORT=8100

# Model Server
MODEL_SERVER_HOST=model-server
MODEL_SERVER_PORT=8080
MODEL_GPU_LAYERS=0  # Set to 32 if using GPU
MODEL_THREADS=4

# Monitoring
PROMETHEUS_PORT=9090
GRAFANA_PORT=3001
GRAFANA_ADMIN_PASSWORD=$(openssl rand -base64 16)

# Backup
BACKUP_SCHEDULE_CRON="0 2 * * *"  # Daily at 2 AM
BACKUP_RETENTION_DAYS=90

# API Configuration
API_CORS_ORIGINS=https://yourhost.gujaratpolice.gov.in
API_RATE_LIMIT_PER_MINUTE=100
```

**3. Secure the .env file:**

```bash
chmod 600 .env
chown root:root .env
```

### Directory Structure Setup

```bash
# Create project root
sudo mkdir -p /opt/gujpol-slm
cd /opt/gujpol-slm

# Create data directories
sudo mkdir -p data/{raw,processed,sources,embeddings,training}
sudo mkdir -p data/embeddings/chroma
sudo mkdir -p configs
sudo mkdir -p logs
sudo mkdir -p backups
sudo mkdir -p models
sudo mkdir -p ssl

# Set permissions
sudo chown -R $USER:$USER /opt/gujpol-slm
sudo chmod -R 755 /opt/gujpol-slm
sudo chmod 700 /opt/gujpol-slm/backups
```

### Build and Start Services

**1. Build Docker images:**

```bash
docker compose build
```

**2. Start services:**

```bash
# Start in detached mode
docker compose up -d

# Verify all services are running
docker compose ps

# Check logs
docker compose logs -f
```

**3. Initial database setup:**

```bash
# Run database migrations
docker compose exec app-api python -m alembic upgrade head

# Create admin user
docker compose exec app-api python -m src.cli users create-admin \
  --username admin \
  --password "$(openssl rand -base64 16)" \
  --email admin@gujaratpolice.gov.in
```

**4. Verify deployment:**

```bash
# Health check
curl http://localhost:8000/health

# Check all services
docker compose exec app-api python -m src.cli health
```

### Service Management

**Start services:**
```bash
docker compose up -d
```

**Stop services:**
```bash
docker compose down
```

**Restart specific service:**
```bash
docker compose restart app-api
```

**View logs:**
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f app-api

# Last 100 lines
docker compose logs --tail=100 app-api
```

**Update services:**
```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker compose up -d --build
```

---

## Air-Gapped Deployment

### Overview

Air-gapped deployment requires transferring all dependencies offline.

### Preparation (Internet-Connected System)

**1. Export Docker Images:**

```bash
# List all images
docker compose pull

# Save images to tar file
docker save \
  postgres:16-alpine \
  chromadb/chroma:latest \
  redis:7-alpine \
  prom/prometheus:latest \
  grafana/grafana:latest \
  $(docker compose config | grep 'image:' | awk '{print $2}') \
  > gujpol-slm-images.tar

# Compress
gzip gujpol-slm-images.tar
```

**2. Download Python Dependencies:**

```bash
# Create requirements file
poetry export -f requirements.txt --output requirements.txt --without-hashes

# Download packages
pip download -r requirements.txt -d python-packages/

# Download sentence-transformers model
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')"

# Copy model cache
cp -r ~/.cache/torch/sentence_transformers models/
```

**3. Package Everything:**

```bash
# Create deployment package
tar czf gujpol-slm-offline.tar.gz \
  docker-compose.yml \
  docker/ \
  src/ \
  configs/ \
  models/ \
  python-packages/ \
  gujpol-slm-images.tar.gz \
  .env.example \
  Makefile \
  README.md
```

### Installation (Air-Gapped System)

**1. Transfer Package:**

```bash
# Use USB drive or secure file transfer
# Copy gujpol-slm-offline.tar.gz to target server
```

**2. Extract and Setup:**

```bash
# Extract package
cd /opt
sudo tar xzf gujpol-slm-offline.tar.gz
cd gujpol-slm

# Load Docker images
docker load < gujpol-slm-images.tar.gz

# Verify images loaded
docker images
```

**3. Install Python Dependencies:**

```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install from local packages
pip install --no-index --find-links=python-packages/ -r requirements.txt
```

**4. Configure and Deploy:**

```bash
# Copy environment file
cp .env.example .env
# Edit .env with production values

# Start services
docker compose up -d
```

### Offline Updates

**Update Procedure:**

```bash
# On internet-connected system:
# 1. Build new images
docker compose build

# 2. Export updated images
docker save app-api:latest > app-api-update.tar

# 3. Transfer to air-gapped system

# On air-gapped system:
# 4. Load new image
docker load < app-api-update.tar

# 5. Restart service
docker compose up -d --no-deps app-api
```

---

## Security Hardening

### System-Level Security

**1. Firewall Configuration (UFW):**

```bash
# Enable firewall
sudo ufw enable

# Allow SSH (if needed)
sudo ufw allow 22/tcp

# Allow HTTPS only
sudo ufw allow 443/tcp

# Deny all other incoming
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Verify rules
sudo ufw status verbose
```

**2. Secure SSH:**

Edit `/etc/ssh/sshd_config`:

```
# Disable root login
PermitRootLogin no

# Use key-based authentication only
PasswordAuthentication no
PubkeyAuthentication yes

# Disable empty passwords
PermitEmptyPasswords no

# Limit users
AllowUsers deploy_user

# Change default port (optional)
Port 2222
```

Restart SSH:
```bash
sudo systemctl restart sshd
```

**3. System Updates:**

```bash
# Enable automatic security updates
sudo apt-get install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

### Application-Level Security

**1. JWT Configuration:**

In `.env`:
```bash
# Strong secret keys (at least 256 bits)
JWT_SECRET_KEY=$(openssl rand -hex 32)
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
```

**2. Database Security:**

```bash
# PostgreSQL hardening
docker compose exec db-postgres psql -U gujpol_admin -d gujpol_slm

-- Revoke public schema privileges
REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT ALL ON SCHEMA public TO gujpol_admin;

-- Enable SSL connections (production)
ALTER SYSTEM SET ssl = on;

-- Set connection limits
ALTER USER gujpol_admin CONNECTION LIMIT 50;
```

**3. API Security Headers:**

Add to `src/api/main.py`:

```python
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

# Force HTTPS in production
if os.getenv("APP_ENV") == "production":
    app.add_middleware(HTTPSRedirectMiddleware)
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["yourhost.gujaratpolice.gov.in"]
    )
```

**4. Rate Limiting:**

Configure in `src/api/dependencies.py`:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

# Apply to sensitive endpoints
@limiter.limit("10/minute")
async def suggest_investigation_steps(...):
    ...
```

**5. Input Validation:**

All input validated via Pydantic schemas in `src/api/schemas.py`.

### Data Encryption

**1. Encryption at Rest:**

```bash
# Enable disk encryption (LUKS)
sudo cryptsetup luksFormat /dev/sdb
sudo cryptsetup luksOpen /dev/sdb gujpol_data
sudo mkfs.ext4 /dev/mapper/gujpol_data
sudo mount /dev/mapper/gujpol_data /opt/gujpol-slm/data
```

**2. PII Encryption:**

Configured in `src/security/encryption.py`:

```python
from cryptography.fernet import Fernet

# Load encryption key from env
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
cipher = Fernet(ENCRYPTION_KEY.encode())

# Encrypt sensitive fields
def encrypt_pii(data: str) -> str:
    return cipher.encrypt(data.encode()).decode()

# Decrypt when needed
def decrypt_pii(encrypted: str) -> str:
    return cipher.decrypt(encrypted.encode()).decode()
```

**3. Backup Encryption:**

```bash
# Encrypt backups with GPG
gpg --symmetric --cipher-algo AES256 backup.tar.gz
```

### Audit Logging

**Enable comprehensive audit logging:**

```python
# src/api/models.py
class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    user_id = Column(UUID)
    action = Column(String)  # CREATE, READ, UPDATE, DELETE
    resource_type = Column(String)  # document, user, etc.
    resource_id = Column(String)
    details = Column(JSONB)
    ip_address = Column(String)
    user_agent = Column(String)
    response_status = Column(Integer)
```

**Log all sensitive operations:**

```python
@app.middleware("http")
async def audit_middleware(request: Request, call_next):
    # Log request
    audit_entry = AuditLog(
        user_id=current_user.id if current_user else None,
        action=request.method,
        resource_type=request.url.path.split("/")[1],
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )

    response = await call_next(request)

    # Log response
    audit_entry.response_status = response.status_code
    db.add(audit_entry)
    await db.commit()

    return response
```

---

## SSL/TLS Configuration

### Certificate Generation

**Option 1: Self-Signed Certificate (Testing):**

```bash
# Generate self-signed certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ssl/server.key \
  -out ssl/server.crt \
  -subj "/C=IN/ST=Gujarat/L=Gandhinagar/O=Gujarat Police/CN=gujpol.local"
```

**Option 2: Internal CA Certificate (Recommended):**

```bash
# Request certificate from your organization's CA
# Copy certificate and key to ssl/ directory
cp /path/to/certificate.crt ssl/server.crt
cp /path/to/private-key.key ssl/server.key

# Set proper permissions
chmod 600 ssl/server.key
chmod 644 ssl/server.crt
```

### NGINX Configuration

Create `docker/nginx.conf`:

```nginx
# NGINX Production Configuration

upstream backend {
    server app-api:8000;
}

upstream frontend {
    server app-frontend:80;
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name yourhost.gujaratpolice.gov.in;
    return 301 https://$server_name$request_uri;
}

# HTTPS Server
server {
    listen 443 ssl http2;
    server_name yourhost.gujaratpolice.gov.in;

    # SSL Configuration
    ssl_certificate /etc/nginx/ssl/server.crt;
    ssl_certificate_key /etc/nginx/ssl/server.key;

    # Strong SSL settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-GCM-SHA256';
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # File upload limit
    client_max_body_size 50M;

    # Frontend
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Backend API
    location /api/ {
        proxy_pass http://backend/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts for long-running queries
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
        proxy_read_timeout 300;
    }

    # Monitoring (restrict access)
    location /grafana/ {
        proxy_pass http://grafana:3000/;
        allow 192.168.1.0/24;  # Internal network only
        deny all;
    }
}
```

### Update Docker Compose

Add NGINX service to `docker-compose.yml`:

```yaml
nginx:
  image: nginx:alpine
  container_name: gujpol-nginx
  restart: unless-stopped
  ports:
    - "80:80"
    - "443:443"
  volumes:
    - ./docker/nginx.conf:/etc/nginx/nginx.conf:ro
    - ./ssl:/etc/nginx/ssl:ro
    - ./logs/nginx:/var/log/nginx
  depends_on:
    - app-api
    - app-frontend
  networks:
    - gujpol-net
```

---

## Backup & Recovery

### Automated Backup System

**Backup Script (`docker/backup/backup.sh`):**

```bash
#!/bin/bash

# Gujarat Police SLM - Automated Backup Script

set -e

BACKUP_DIR=${BACKUP_DIR:-/backups}
RETENTION_DAYS=${RETENTION_DAYS:-90}
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="gujpol-slm-backup-${TIMESTAMP}"

echo "[$(date)] Starting backup: ${BACKUP_NAME}"

# Create backup directory
mkdir -p "${BACKUP_DIR}/${BACKUP_NAME}"

# 1. Backup PostgreSQL
echo "[$(date)] Backing up PostgreSQL..."
pg_dump \
  -h ${POSTGRES_HOST} \
  -U ${POSTGRES_USER} \
  -d ${POSTGRES_DB} \
  --format=custom \
  --file="${BACKUP_DIR}/${BACKUP_NAME}/postgres.dump"

# 2. Backup ChromaDB
echo "[$(date)] Backing up ChromaDB..."
tar czf "${BACKUP_DIR}/${BACKUP_NAME}/chroma.tar.gz" \
  -C /chroma-data .

# 3. Backup Configuration
echo "[$(date)] Backing up configuration..."
tar czf "${BACKUP_DIR}/${BACKUP_NAME}/configs.tar.gz" \
  -C /app/configs .

# 4. Backup Models
echo "[$(date)] Backing up models..."
tar czf "${BACKUP_DIR}/${BACKUP_NAME}/models.tar.gz" \
  -C /models .

# 5. Create manifest
echo "[$(date)] Creating backup manifest..."
cat > "${BACKUP_DIR}/${BACKUP_NAME}/manifest.json" <<EOF
{
  "timestamp": "${TIMESTAMP}",
  "version": "0.1.0",
  "files": {
    "postgres": "postgres.dump",
    "chroma": "chroma.tar.gz",
    "configs": "configs.tar.gz",
    "models": "models.tar.gz"
  },
  "checksums": {
    "postgres": "$(sha256sum ${BACKUP_DIR}/${BACKUP_NAME}/postgres.dump | cut -d' ' -f1)",
    "chroma": "$(sha256sum ${BACKUP_DIR}/${BACKUP_NAME}/chroma.tar.gz | cut -d' ' -f1)"
  }
}
EOF

# 6. Compress entire backup
echo "[$(date)] Compressing backup..."
tar czf "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" \
  -C "${BACKUP_DIR}" "${BACKUP_NAME}"

# 7. Encrypt backup
echo "[$(date)] Encrypting backup..."
gpg --symmetric --cipher-algo AES256 \
  --passphrase-file /run/secrets/backup_passphrase \
  "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"

# 8. Remove unencrypted backup
rm -rf "${BACKUP_DIR}/${BACKUP_NAME}"
rm "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"

# 9. Clean old backups
echo "[$(date)] Cleaning old backups (retention: ${RETENTION_DAYS} days)..."
find "${BACKUP_DIR}" -name "gujpol-slm-backup-*.tar.gz.gpg" -mtime +${RETENTION_DAYS} -delete

echo "[$(date)] Backup completed: ${BACKUP_NAME}.tar.gz.gpg"
```

**Backup Service in Docker Compose:**

Already included in `docker-compose.yml` - see line 229-250.

**Configure Backup Schedule:**

In `.env`:
```bash
# Daily at 2 AM
BACKUP_SCHEDULE_CRON="0 2 * * *"

# Retention period
BACKUP_RETENTION_DAYS=90
```

### Manual Backup

```bash
# Trigger manual backup
docker compose exec backup /backup.sh

# Verify backup
ls -lh backups/
```

### Recovery Procedure

**Full System Recovery:**

```bash
# 1. Stop services
docker compose down

# 2. Locate backup file
BACKUP_FILE="backups/gujpol-slm-backup-20240211_020000.tar.gz.gpg"

# 3. Decrypt backup
gpg --decrypt \
  --passphrase-file /run/secrets/backup_passphrase \
  "${BACKUP_FILE}" > backup.tar.gz

# 4. Extract backup
mkdir -p restore_temp
tar xzf backup.tar.gz -C restore_temp

# 5. Restore PostgreSQL
docker compose up -d db-postgres
sleep 10
pg_restore \
  -h localhost \
  -U gujpol_admin \
  -d gujpol_slm \
  --clean \
  --if-exists \
  restore_temp/gujpol-slm-backup-*/postgres.dump

# 6. Restore ChromaDB
rm -rf data/embeddings/chroma/*
tar xzf restore_temp/gujpol-slm-backup-*/chroma.tar.gz \
  -C data/embeddings/chroma/

# 7. Restore configurations
tar xzf restore_temp/gujpol-slm-backup-*/configs.tar.gz \
  -C configs/

# 8. Restore models
tar xzf restore_temp/gujpol-slm-backup-*/models.tar.gz \
  -C models/

# 9. Restart all services
docker compose up -d

# 10. Verify recovery
docker compose exec app-api python -m src.cli health

# 11. Clean up
rm -rf restore_temp backup.tar.gz
```

### Offsite Backup

**Sync to offsite location:**

```bash
# Using rsync over SSH (if network available)
rsync -avz --progress \
  backups/ \
  backup-server:/mnt/backups/gujpol-slm/

# Or copy to external storage
cp backups/*.gpg /mnt/external-backup/
```

---

## Monitoring & Logging

### Prometheus Configuration

**Prometheus config (`docker/prometheus.yml`):**

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'gujpol-api'
    static_configs:
      - targets: ['app-api:8000']
    metrics_path: '/metrics'

  - job_name: 'gujpol-model'
    static_configs:
      - targets: ['model-server:8080']

  - job_name: 'postgres'
    static_configs:
      - targets: ['db-postgres:5432']

  - job_name: 'redis'
    static_configs:
      - targets: ['cache-redis:6379']

  - job_name: 'chromadb'
    static_configs:
      - targets: ['db-chroma:8100']
```

### Grafana Dashboards

**Access Grafana:**
```
URL: http://localhost:3001
Username: admin
Password: (from .env GRAFANA_ADMIN_PASSWORD)
```

**Import Dashboards:**

1. **System Overview Dashboard:**
   - CPU, Memory, Disk usage
   - Network I/O
   - Service health status

2. **API Performance Dashboard:**
   - Request rate
   - Response time percentiles
   - Error rate
   - Active users

3. **RAG Pipeline Dashboard:**
   - Query latency
   - Search quality metrics
   - Cache hit rate
   - Vector DB performance

4. **Security Dashboard:**
   - Failed login attempts
   - Unusual access patterns
   - API abuse detection

### Log Management

**Centralized Logging with ELK Stack (Optional):**

Add to `docker-compose.yml`:

```yaml
elasticsearch:
  image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
  environment:
    - discovery.type=single-node
    - "ES_JAVA_OPTS=-Xms1g -Xmx1g"
  volumes:
    - elasticsearch_data:/usr/share/elasticsearch/data

logstash:
  image: docker.elastic.co/logstash/logstash:8.11.0
  volumes:
    - ./docker/logstash.conf:/usr/share/logstash/pipeline/logstash.conf
    - ./logs:/logs

kibana:
  image: docker.elastic.co/kibana/kibana:8.11.0
  ports:
    - "5601:5601"
  depends_on:
    - elasticsearch
```

**Log Rotation:**

```bash
# Configure logrotate
sudo tee /etc/logrotate.d/gujpol-slm <<EOF
/opt/gujpol-slm/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    missingok
    create 0644 root root
}
EOF
```

---

## Performance Tuning

### Database Optimization

**PostgreSQL Tuning:**

```sql
-- postgresql.conf optimizations
shared_buffers = 8GB  # 25% of RAM
effective_cache_size = 24GB  # 75% of RAM
maintenance_work_mem = 2GB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1  # For SSD
effective_io_concurrency = 200  # For SSD
work_mem = 64MB
min_wal_size = 2GB
max_wal_size = 8GB
max_worker_processes = 8
max_parallel_workers_per_gather = 4
max_parallel_workers = 8
```

Apply settings:
```bash
docker compose exec db-postgres psql -U gujpol_admin -d gujpol_slm

ALTER SYSTEM SET shared_buffers = '8GB';
ALTER SYSTEM SET effective_cache_size = '24GB';
-- ... etc

SELECT pg_reload_conf();
```

### Redis Optimization

In docker-compose.yml:

```yaml
cache-redis:
  command: redis-server \
    --requirepass ${REDIS_PASSWORD} \
    --maxmemory 4gb \
    --maxmemory-policy allkeys-lru \
    --save 900 1 \
    --save 300 10 \
    --save 60 10000
```

### ChromaDB Optimization

**Tuning HNSW Index:**

```python
# In embedding pipeline
collection.modify(
    metadata={
        "hnsw:space": "cosine",
        "hnsw:construction_ef": 200,  # Higher = better quality
        "hnsw:search_ef": 100,  # Higher = better recall
        "hnsw:M": 32  # Higher = better quality, more memory
    }
)
```

### Application Optimization

**API Server (Gunicorn):**

```bash
# docker/Dockerfile.api
CMD ["gunicorn", "src.api.main:app", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "300", \
     "--keep-alive", "5", \
     "--max-requests", "1000", \
     "--max-requests-jitter", "100"]
```

**Model Inference:**

```bash
# Use GPU if available
MODEL_GPU_LAYERS=32  # in .env

# Optimize thread count
MODEL_THREADS=8  # Match CPU cores
```

---

## Disaster Recovery

### Recovery Time Objective (RTO)

**Target:** 4 hours from catastrophic failure to full restoration

### Recovery Point Objective (RPO)

**Target:** Maximum 24 hours of data loss (daily backups)

### Disaster Recovery Plan

**1. Identify Failure:**
```bash
# Automated health check
docker compose exec app-api python -m src.cli health

# Manual verification
curl https://yourhost.gujaratpolice.gov.in/health
```

**2. Assess Damage:**
- Determine failed components
- Check data integrity
- Review logs for root cause

**3. Failover Procedure:**

If primary system fails:

```bash
# Stop failed services
docker compose down

# Start on backup hardware
scp -r /opt/gujpol-slm backup-server:/opt/gujpol-slm
ssh backup-server "cd /opt/gujpol-slm && docker compose up -d"
```

**4. Data Recovery:**

Follow backup recovery procedure (see above)

**5. Service Restoration:**

```bash
# Verify all services healthy
docker compose ps
docker compose logs

# Run system diagnostics
docker compose exec app-api python -m src.cli health
```

**6. Post-Incident Review:**
- Document incident
- Identify root cause
- Implement preventive measures
- Update DR plan

### High Availability Setup (Optional)

**Active-Passive Configuration:**

```
┌──────────────┐         ┌──────────────┐
│   Primary    │         │   Backup     │
│   Server     │────────▶│   Server     │
│  (Active)    │ Rsync   │  (Standby)   │
└──────────────┘         └──────────────┘
       │                        ▲
       │                        │
       │                   Failover
       ▼                        │
  ┌──────────────────────────────┐
  │    Load Balancer (HAProxy)   │
  └──────────────────────────────┘
```

**HAProxy Configuration:**

```
# /etc/haproxy/haproxy.cfg
frontend gujpol_frontend
    bind *:443 ssl crt /etc/ssl/certs/server.pem
    default_backend gujpol_backend

backend gujpol_backend
    balance roundrobin
    option httpchk GET /health
    server primary 192.168.1.10:443 check inter 5s fall 3 rise 2
    server backup 192.168.1.11:443 check inter 5s fall 3 rise 2 backup
```

---

## Troubleshooting

### Common Issues

#### 1. Services Won't Start

**Symptom:** `docker compose up -d` fails

**Diagnosis:**
```bash
docker compose logs
docker compose ps
```

**Solutions:**
- Check disk space: `df -h`
- Check port conflicts: `sudo netstat -tulpn`
- Verify .env file: `cat .env`
- Check Docker daemon: `sudo systemctl status docker`

#### 2. Database Connection Failures

**Symptom:** API can't connect to PostgreSQL

**Diagnosis:**
```bash
docker compose logs db-postgres
docker compose exec db-postgres psql -U gujpol_admin -d gujpol_slm
```

**Solutions:**
```bash
# Restart PostgreSQL
docker compose restart db-postgres

# Check credentials in .env
grep POSTGRES .env

# Test connection
docker compose exec app-api python -c "from src.api.database import engine; print(engine.url)"
```

#### 3. Out of Memory

**Symptom:** Containers being killed

**Diagnosis:**
```bash
docker stats
free -h
dmesg | grep -i kill
```

**Solutions:**
```bash
# Reduce service limits in docker-compose.yml
# Increase system RAM
# Enable swap
sudo fallocate -l 8G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

#### 4. Slow Performance

**Symptom:** Queries taking >10 seconds

**Diagnosis:**
```bash
# Check resource usage
docker stats

# Check database performance
docker compose exec db-postgres psql -U gujpol_admin -d gujpol_slm
SELECT * FROM pg_stat_activity WHERE state = 'active';

# Check ChromaDB
curl http://localhost:8100/api/v1/heartbeat
```

**Solutions:**
- Review Performance Tuning section
- Check disk I/O: `iostat -x 1`
- Optimize queries
- Add indexes to database

### Debug Mode

**Enable debug logging:**

In `.env`:
```bash
LOG_LEVEL=DEBUG
```

Restart services:
```bash
docker compose restart app-api
```

View debug logs:
```bash
docker compose logs -f app-api | grep DEBUG
```

### Support Contacts

**For deployment issues:**
- Email: support@gujpol-slm.local
- Internal ticket system: https://tickets.gujaratpolice.gov.in

**For security incidents:**
- Email: security@gujaratpolice.gov.in
- Phone: [EMERGENCY HOTLINE]

---

## Appendix

### Deployment Checklist

**Pre-Deployment:**
- [ ] Hardware meets requirements
- [ ] OS installed and updated
- [ ] Docker installed
- [ ] Firewall configured
- [ ] SSL certificates ready
- [ ] .env file configured
- [ ] Data directories created

**Deployment:**
- [ ] Docker images built
- [ ] Services started successfully
- [ ] Database initialized
- [ ] Admin user created
- [ ] Health checks passing
- [ ] Backups configured
- [ ] Monitoring enabled

**Post-Deployment:**
- [ ] SSL working correctly
- [ ] User accounts created
- [ ] Data ingested
- [ ] Embeddings generated
- [ ] Search functionality tested
- [ ] Backup tested
- [ ] Documentation updated
- [ ] Team trained

### Maintenance Schedule

**Daily:**
- Review logs for errors
- Check disk space
- Verify backups completed

**Weekly:**
- Review security logs
- Update system packages
- Test backup restoration

**Monthly:**
- Performance review
- Capacity planning
- Security audit
- User access review

**Quarterly:**
- Disaster recovery drill
- Update documentation
- Hardware health check
- Dependency updates

---

**Document Version:** 1.0
**Last Updated:** February 11, 2026
**Maintained By:** Gujarat Police SLM Development Team
