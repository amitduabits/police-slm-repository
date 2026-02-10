Create the complete Docker deployment package that can be deployed on Gujarat Police servers.

## docker-compose.yml services (8 total):

1. **app-api** - FastAPI backend (build from docker/Dockerfile.api)
   - Port 8000, depends on postgres/redis/chroma
   - Health check, 4GB memory limit
   - Volumes: data/, logs/, configs/

2. **app-frontend** - React dashboard via Nginx (build from docker/Dockerfile.frontend)
   - Port 3000 → 80, reverse proxy /api/ to app-api

3. **db-postgres** - PostgreSQL 16 Alpine
   - Port 5432, volume for persistence
   - Init script: docker/init-db.sql
   - Health check with pg_isready

4. **db-chroma** - ChromaDB latest
   - Port 8100, persistent volume
   - Telemetry disabled

5. **cache-redis** - Redis 7 Alpine
   - Port 6379, password auth, 512MB max memory
   - Health check

6. **model-server** - llama.cpp server (build from docker/Dockerfile.model)
   - Port 8080, GPU passthrough
   - Model weights mounted from ./models/ (not baked into image)
   - 8GB memory limit

7. **prometheus** - Prometheus monitoring
   - Port 9090, scrape api and model-server

8. **grafana** - Grafana dashboards
   - Port 3001, auto-provision Prometheus datasource

## Create Dockerfiles:

### docker/Dockerfile.api
- FROM python:3.11-slim
- Install: tesseract-ocr + hin + guj, libpq-dev, build-essential
- Poetry install --no-dev
- Non-root user, health check
- CMD: uvicorn with 2 workers

### docker/Dockerfile.model
- FROM ubuntu:22.04
- Build llama.cpp from source (cmake)
- Non-root user, health check
- ENTRYPOINT: llama-server with model from /models/ volume

### docker/Dockerfile.frontend
- Multi-stage: node:20-alpine build → nginx:alpine serve
- Copy nginx.conf with security headers, SPA routing, API proxy

### docker/Dockerfile.backup
- Alpine with pg_dump, supercronic for cron scheduling
- Backup script: postgres dump + chroma tar + configs
- Configurable retention (default 90 days)

## Also create:
- docker/nginx.conf - Security headers, gzip, SPA routing, /api/ proxy
- docker/prometheus.yml - Scrape targets
- docker/grafana-datasources.yml - Auto-provision Prometheus
- docker/init-db.sql - Complete schema (users, documents, FIRs, chargesheets, rulings, audit_log, feedback, etc.)

## Deployment scripts:
- scripts/deploy.sh - Full deployment: build images, up services, run migrations, verify health
- scripts/backup.sh - Manual backup trigger
- scripts/restore.sh - Restore from backup

## Requirements:
- Single `docker-compose up -d` starts everything
- All data on mounted volumes (persistent)
- Resource limits on every container
- Restart policies (unless-stopped)
- Internal network (172.28.0.0/16)
- Log rotation configured
- Health checks on all services
