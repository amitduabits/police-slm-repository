Execute Phase 3 (Dashboard and Deployment) of the Gujarat Police SLM project.

Weeks 13-20. Wrap everything in usable, secure interface.

## Step 1: Build API backend
- Implement all FastAPI endpoints (auth, sop, chargesheet, search, documents, analytics, admin)
- Wire up RAG pipeline to API endpoints
- Add JWT authentication and RBAC
- Add audit logging middleware
- Test all endpoints via /docs swagger

## Step 2: Build React dashboard
- Initialize React + TypeScript + Vite project in src/dashboard/
- Build all 8 pages: Login, Dashboard, SOP, Chargesheet, Search, Analytics, Tools, Training
- Wire up to API with axios + react-query
- Test responsive design on mobile

## Step 3: Security hardening
- Implement encryption (AES-256 at rest, TLS in transit)
- PII detection and encryption
- Audit logging with hash chain
- Input sanitization and prompt injection prevention
- Rate limiting

## Step 4: Docker deployment
- Build all Docker images
- Test docker-compose up on clean machine
- Verify all 8 services start and pass health checks
- Test backup and restore

## Step 5: Integration testing
- Complete user journey: login → upload FIR → get guidance → search similar → view analytics
- Test with 10 concurrent users
- Test on slow network (3G simulation)
- Security audit: RBAC, injection attempts

## Step 6: Phase 3 Report
Generate data/phase3_report.md with pass/fail for each test.

Print "PHASE 3 COMPLETE" when done.
