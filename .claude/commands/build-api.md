Build the complete FastAPI backend for the Gujarat Police SLM Dashboard.

## Create these files:

### `src/api/main.py` - Application factory
- FastAPI app with lifespan (startup: connect DB, load models; shutdown: cleanup)
- CORS middleware (configured from .env ALLOWED_ORIGINS)
- Request logging middleware (log every request for audit)
- Error handling middleware
- Include all routers
- Prometheus metrics via prometheus-fastapi-instrumentator
- Health check endpoint at /health

### `src/api/database.py` - Database setup
- SQLAlchemy async engine + session factory
- Connection pool configuration
- Base model class

### `src/api/models.py` - SQLAlchemy ORM models
Map all tables from docker/init-db.sql:
- User, Document, FIR, Chargesheet, CourtRuling, AuditLog, Feedback, SearchHistory, TrainingProgress, SystemMetric

### `src/api/schemas.py` - Pydantic schemas
Request/response models for all endpoints.

### `src/api/auth.py` - Authentication router
- POST /auth/login - JWT authentication (username + password → access_token + refresh_token)
- POST /auth/refresh - Token refresh
- GET /auth/me - Current user info
- JWT: 15-min access token, 7-day refresh token
- Brute force protection: lock after 5 failed attempts
- Password hashing with bcrypt

### `src/api/dependencies.py` - Dependency injection
- get_db - database session
- get_current_user - JWT verification
- require_role(roles) - RBAC check (admin, senior_officer, officer, viewer)

### `src/api/routes/sop.py` - SOP Assistant
- POST /sop/suggest - Given FIR details, suggest investigation steps (uses RAG pipeline)
- POST /sop/checklist - Generate investigation checklist for case category
- GET /sop/templates/{category} - Get SOP template

### `src/api/routes/chargesheet.py` - Chargesheet Reviewer
- POST /chargesheet/review - Upload and review draft chargesheet (uses RAG pipeline)
- POST /chargesheet/compare - Compare against successful chargesheets
- GET /chargesheet/checklist/{category} - Get completeness checklist

### `src/api/routes/search.py` - Case Search
- POST /search/query - Natural language search (uses hybrid search)
- POST /search/similar - Find similar cases
- GET /search/filters - Available filter options

### `src/api/routes/documents.py` - Document management
- POST /documents/upload - Upload new document for processing
- GET /documents/{id} - Get document details
- GET /documents/{id}/chunks - Get document chunks

### `src/api/routes/analytics.py` - Pattern insights
- GET /analytics/patterns - Hotspot and trend data
- GET /analytics/conviction-rate - By category, district, time

### `src/api/routes/admin.py` - Admin operations
- GET /admin/audit-log - View access logs (admin only)
- GET /admin/system-health - System status
- POST /admin/reindex - Trigger re-indexing
- POST /admin/users - Create user (admin only)

### `src/api/routes/utils.py` - Utility endpoints
- GET /utils/convert-section/{section} - IPC↔BNS conversion
- GET /utils/section-info/{section} - Section details

### `src/api/audit.py` - Audit logging middleware
- Log every API call: who, what, when, from where
- Tamper-proof: each entry hashed with previous entry's hash (hash chain)
- Store in audit_log table

## Requirements:
- All endpoints require JWT auth except /health and /auth/login
- Rate limiting: 100 requests/minute per user
- Input validation via Pydantic
- OpenAPI docs at /docs
- CORS for dashboard origin only
- Response streaming for SOP/chargesheet review (long answers)

Wire up: `python -m src.cli serve --reload`
