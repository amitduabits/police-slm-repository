Execute Sprint 3: Build real FastAPI backend wired to RAG pipeline.

PREREQUISITE: Sprint 2 must be complete (RAG pipeline returning answers with citations).

Goal: Full working API that the React dashboard can call.

## TASK 1: Database Setup (20 min)

We need PostgreSQL running for structured data and auth.

**Option A: Docker (recommended)**
```bash
docker run -d --name gujpol-postgres -e POSTGRES_DB=gujpol_slm -e POSTGRES_USER=gujpol_admin -e POSTGRES_PASSWORD=changeme -p 5432:5432 -v pgdata:/var/lib/postgresql/data postgres:16-alpine
# Then apply schema:
# On Windows: Get-Content docker/init-db.sql | docker exec -i gujpol-postgres psql -U gujpol_admin -d gujpol_slm
# On Linux: docker exec -i gujpol-postgres psql -U gujpol_admin -d gujpol_slm < docker/init-db.sql
```

**Option B: SQLite for development (simpler, no Docker needed)**
Create `src/api/database.py` that supports both PostgreSQL and SQLite:
- If DATABASE_URL starts with "postgresql://", use asyncpg
- If DATABASE_URL starts with "sqlite://", use aiosqlite
- Default to SQLite for development: `sqlite:///data/gujpol.db`

Create SQLAlchemy models in `src/api/models.py` matching docker/init-db.sql schema.
Run Alembic migration or create tables directly.

## TASK 2: Authentication (30 min)

Create `src/api/auth.py` with REAL working JWT authentication:

- POST /auth/login: Accept username+password, return JWT access_token + refresh_token
- Hash passwords with bcrypt
- Create default admin user on first startup
- JWT access token expires in 15 min, refresh in 7 days
- Dependency injection: `get_current_user` extracts user from JWT header

Create `src/api/dependencies.py`:
```python
async def get_current_user(token: str = Depends(oauth2_scheme), db = Depends(get_db)):
    # Verify JWT, look up user, return User object
    
def require_role(*roles):
    # Return dependency that checks user.role is in allowed roles
```

Test: Can login with admin/changeme, get a token, use token to call protected endpoints.

## TASK 3: Real API Endpoints (60 min)

Replace ALL stubs in `src/api/main.py` with real implementations.

Create route files in `src/api/routes/`:

**`src/api/routes/sop.py`** - Wire to RAG pipeline:
```python
@router.post("/sop/suggest")
async def suggest_investigation(
    request: SOPRequest,  # Pydantic model: fir_details, case_category
    user = Depends(get_current_user),
    db = Depends(get_db),
):
    # 1. Use RAG pipeline with use_case="sop"
    # 2. Log query to search_history table
    # 3. Log to audit trail
    # 4. Return structured response with citations
```

**`src/api/routes/chargesheet.py`** - Wire to RAG pipeline:
- POST /chargesheet/review: Accept chargesheet text or file upload
- Use RAG with use_case="chargesheet"
- Return completeness score + issues + recommendations

**`src/api/routes/search.py`** - Wire to hybrid search:
- POST /search/query: Natural language search
- POST /search/similar: Find similar cases by document ID
- GET /search/filters: Return available filter options from DB

**`src/api/routes/documents.py`**:
- POST /documents/upload: Accept PDF/DOC/TXT, trigger OCR + processing pipeline
- GET /documents/{id}: Return document details from DB
- GET /documents/: List documents with pagination

**`src/api/routes/utils.py`**:
- GET /utils/convert-section/{section}: Wire to SectionNormalizer

**`src/api/routes/admin.py`** (admin only):
- GET /admin/audit-log: Query audit_log table
- GET /admin/system-health: Check all services
- POST /admin/users: Create new user

## TASK 4: Pydantic Schemas (15 min)

Create `src/api/schemas.py` with request/response models:
- LoginRequest, TokenResponse
- SOPRequest, SOPResponse (with citations)
- ChargesheetReviewRequest, ChargesheetReviewResponse (with score)
- SearchRequest, SearchResponse (with results list)
- DocumentUploadResponse
- SectionConvertResponse
- UserCreate, UserResponse

## TASK 5: Middleware (15 min)

In `src/api/main.py` add:
- Audit logging middleware (log every request to DB)
- Rate limiting (100 requests/min per user via Redis or in-memory)
- Error handling (return proper HTTP codes, not 500 for everything)

## TASK 6: Test (10 min)

Start server: `python -m src.cli serve --reload`

Test with curl or Swagger UI at http://localhost:8000/docs:

```bash
# Login
curl -X POST http://localhost:8000/auth/login -H "Content-Type: application/json" -d '{"username":"admin","password":"changeme"}'

# Use token for protected endpoints
TOKEN="<paste token from login response>"
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/search/filters
curl -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" http://localhost:8000/sop/suggest -d '{"fir_details":"Theft at jewelry shop in Surat. CCTV footage available.","case_category":"theft"}'
curl -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" http://localhost:8000/search/query -d '{"query":"murder bail conditions Gujarat"}'
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/utils/convert-section/302?from_code=IPC&to_code=BNS
```

All should return real data, not stub messages.

## DONE CRITERIA:
- Database running with schema applied
- JWT auth working (login → token → protected endpoints)
- /sop/suggest returns AI-generated investigation guidance with citations
- /chargesheet/review returns completeness score with issues
- /search/query returns relevant results
- /utils/convert-section returns correct mappings
- Print "SPRINT 3 COMPLETE - API WORKING"
