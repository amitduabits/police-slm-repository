# API Reference Documentation

## Gujarat Police AI Investigation Support System - REST API

**Version:** 0.1.0
**Base URL:** `http://localhost:8000`
**API Type:** REST with JSON
**Authentication:** JWT Bearer Token

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Core Endpoints](#core-endpoints)
4. [SOP Assistant API](#sop-assistant-api)
5. [Chargesheet Review API](#chargesheet-review-api)
6. [Search API](#search-api)
7. [Utility Endpoints](#utility-endpoints)
8. [Error Handling](#error-handling)
9. [Rate Limiting](#rate-limiting)
10. [Request/Response Examples](#requestresponse-examples)
11. [SDKs & Client Libraries](#sdks--client-libraries)

---

## Overview

The Gujarat Police SLM API provides programmatic access to three core features:

1. **SOP Assistant** - Investigation guidance based on similar cases
2. **Chargesheet Reviewer** - Completeness analysis of draft chargesheets
3. **Case Search** - Semantic search across legal documents

### Base URL

```
Production: http://localhost:8000
Development: http://localhost:8000
```

### Content Type

All requests and responses use JSON:
```
Content-Type: application/json
```

### API Versioning

Currently using URL path versioning:
```
/api/v1/...  (Future)
/...         (Current - no version prefix)
```

### Interactive Documentation

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## Authentication

### Overview

The API uses JWT (JSON Web Token) based authentication with refresh token support.

**Token Lifetimes:**
- Access Token: 60 minutes
- Refresh Token: 7 days

### Login

Obtain access and refresh tokens.

```http
POST /auth/login
Content-Type: application/json

{
  "username": "officer_kumar",
  "password": "securePassword123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**Status Codes:**
- `200 OK` - Login successful
- `401 Unauthorized` - Invalid credentials
- `403 Forbidden` - Account disabled

### Refresh Token

Obtain a new access token using refresh token.

```http
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### Using Access Token

Include the access token in the Authorization header:

```http
GET /auth/me
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Get Current User

Retrieve authenticated user details.

```http
GET /auth/me
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "officer_kumar",
  "email": "kumar@gujaratpolice.gov.in",
  "full_name": "Rajesh Kumar",
  "role": "officer",
  "rank": "Sub-Inspector",
  "badge_number": "GUJ-2024-1234",
  "police_station": "Ahmedabad City Police Station",
  "district": "Ahmedabad",
  "phone": "+91-9876543210",
  "is_active": true,
  "last_login": "2024-02-11T10:30:00Z",
  "created_at": "2024-01-01T00:00:00Z"
}
```

**Status Codes:**
- `200 OK` - User details retrieved
- `401 Unauthorized` - Invalid or expired token

---

## Core Endpoints

### Health Check

Check API health status.

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "gujpol-slm-api",
  "version": "0.1.0",
  "message": "Use /utils/health for detailed health check"
}
```

### Detailed Health Check

Comprehensive system health check.

```http
GET /utils/health
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-02-11T10:30:00Z",
  "version": "0.1.0",
  "services": {
    "database": {
      "status": "healthy",
      "latency_ms": 5,
      "details": "PostgreSQL 16 - 234 connections"
    },
    "vector_db": {
      "status": "healthy",
      "latency_ms": 12,
      "details": "ChromaDB - 150,000 vectors"
    },
    "cache": {
      "status": "healthy",
      "latency_ms": 2,
      "details": "Redis - 85% memory used"
    },
    "llm": {
      "status": "healthy",
      "latency_ms": 450,
      "details": "Mistral 7B - llama.cpp backend"
    },
    "embedding_model": {
      "status": "healthy",
      "details": "paraphrase-multilingual-MiniLM-L12-v2"
    }
  }
}
```

**Status Values:**
- `healthy` - All systems operational
- `degraded` - Some non-critical services down
- `unhealthy` - Critical services unavailable

### Root Endpoint

API information and endpoint listing.

```http
GET /
```

**Response:**
```json
{
  "service": "Gujarat Police AI Investigation Support System",
  "version": "0.1.0",
  "status": "operational",
  "endpoints": {
    "docs": "/docs",
    "redoc": "/redoc",
    "health": "/utils/health",
    "auth": {
      "login": "POST /auth/login",
      "refresh": "POST /auth/refresh",
      "me": "GET /auth/me"
    },
    "sop": {
      "suggest": "POST /sop/suggest"
    },
    "chargesheet": {
      "review": "POST /chargesheet/review"
    },
    "search": {
      "query": "POST /search/query",
      "similar": "POST /search/similar",
      "filters": "GET /search/filters"
    },
    "utils": {
      "convert_section": "GET /utils/convert-section/{section}",
      "health": "GET /utils/health"
    }
  },
  "message": "See /docs for interactive API documentation"
}
```

---

## SOP Assistant API

### Suggest Investigation Steps

Get AI-generated investigation guidance based on FIR details and similar past cases.

```http
POST /sop/suggest
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "fir_details": "Complaint received regarding theft of gold ornaments worth Rs. 2,50,000 from complainant's residence during night hours. Entry made through breaking window glass. No eyewitness available. CCTV footage recovered.",
  "case_category": "theft",
  "district": "Ahmedabad",
  "sections_cited": ["379 IPC", "457 IPC"],
  "top_k": 5
}
```

**Request Schema:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `fir_details` | string | Yes | FIR details or case description (min 10 chars) |
| `case_category` | string | No | Case type (e.g., "theft", "murder", "assault") |
| `district` | string | No | District name for location-based filtering |
| `sections_cited` | array[string] | No | List of IPC/BNS sections |
| `top_k` | integer | No | Number of similar cases to retrieve (1-20, default: 5) |

**Response:**
```json
{
  "query": "Complaint received regarding theft... | Category: theft | Sections: 379 IPC, 457 IPC",
  "response": "Based on similar cases, here are the recommended investigation steps:\n\n1. CRITICAL STEPS (within 24 hours):\n   - Preserve and document the crime scene, focusing on the broken window and entry point - Cite [Source 1: State v. Patel (2023)]\n   - Collect fingerprints from window frame and glass pieces - Cite [Source 2: State v. Shah (2022)]\n   - Review CCTV footage and preserve digital evidence - Cite [Source 1]\n   - Record statements from neighbors regarding suspicious persons - Cite [Source 3: State v. Kumar (2023)]\n\n2. IMPORTANT STEPS (within 1 week):\n   - Analyze CCTV footage for suspect identification - Cite [Source 1]\n   - Check records of known offenders in the area for similar MO - Cite [Source 4: Gujarat Police SOP 2024]\n   - Investigate pawn shops and jewelry markets for disposal of stolen items - Cite [Source 2]\n   - Cross-reference with other theft cases in the district - Cite [Source 5: NCRB Guidelines 2024]\n\n3. RECOMMENDED STEPS:\n   - Conduct technical surveillance if suspect identified - Cite [Source 4]\n   - Coordinate with neighboring districts for similar cases - Cite [Source 5]\n   - Document evidence chain of custody meticulously - Cite [Source 1]",
  "citations": [
    {
      "source": "State of Gujarat v. Dinesh Patel (2023)",
      "doc_type": "court_ruling",
      "court": "Gujarat High Court",
      "score": 0.87
    },
    {
      "source": "State v. Ramesh Shah - Theft Investigation (2022)",
      "doc_type": "court_ruling",
      "court": "District Court Ahmedabad",
      "score": 0.82
    },
    {
      "source": "State v. Suresh Kumar - House Breaking (2023)",
      "doc_type": "court_ruling",
      "court": "Gujarat High Court",
      "score": 0.78
    },
    {
      "source": "Gujarat Police Investigation SOP Manual 2024",
      "doc_type": "internal_document",
      "court": null,
      "score": 0.75
    },
    {
      "source": "NCRB Crime Investigation Guidelines 2024",
      "doc_type": "guideline",
      "court": null,
      "score": 0.71
    }
  ],
  "num_results": 5,
  "processing_time_ms": 2340
}
```

**Response Schema:**

| Field | Type | Description |
|-------|------|-------------|
| `query` | string | Processed query sent to RAG system |
| `response` | string | AI-generated investigation guidance |
| `citations` | array | Source documents used (see Citation schema) |
| `num_results` | integer | Number of retrieved similar cases |
| `processing_time_ms` | integer | Total processing time in milliseconds |

**Citation Schema:**

| Field | Type | Description |
|-------|------|-------------|
| `source` | string | Document title or case name |
| `doc_type` | string | Document type (court_ruling, guideline, etc.) |
| `court` | string | Court name (if applicable) |
| `score` | float | Relevance score (0.0-1.0) |

**Status Codes:**
- `200 OK` - Investigation steps generated successfully
- `400 Bad Request` - Invalid request parameters
- `401 Unauthorized` - Missing or invalid authentication
- `500 Internal Server Error` - Processing failed

**Example cURL:**
```bash
curl -X POST http://localhost:8000/sop/suggest \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "fir_details": "Theft of gold ornaments...",
    "case_category": "theft",
    "sections_cited": ["379 IPC"]
  }'
```

---

## Chargesheet Review API

### Review Chargesheet

Analyze a draft chargesheet for completeness and suggest improvements.

```http
POST /chargesheet/review
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "chargesheet_text": "CHARGESHEET UNDER SECTION 173 CrPC\n\nCase No: CR-123/2024\nPolice Station: Ahmedabad City\n\nAccused: Ramesh Kumar\nOffences: Section 302 IPC\n\nBrief Facts: The accused is alleged to have committed murder of the deceased on 15th January 2024...\n\n[Full chargesheet text here - minimum 50 characters]",
  "case_number": "CR-123/2024",
  "sections_charged": ["302 IPC"],
  "top_k": 5
}
```

**Request Schema:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `chargesheet_text` | string | Yes* | Full chargesheet text (min 50 chars) |
| `chargesheet_url` | string | No* | URL to chargesheet document (alternative to text) |
| `case_number` | string | No | Case number for reference |
| `sections_charged` | array[string] | No | List of sections charged |
| `top_k` | integer | No | Number of reference cases (1-20, default: 5) |

*Either `chargesheet_text` or `chargesheet_url` must be provided.

**Response:**
```json
{
  "query": "CHARGESHEET UNDER SECTION 173 CrPC...",
  "completeness_score": 72.5,
  "response": "Based on review of similar successful chargesheets:\n\n1. COMPLETENESS SCORE: 72.5/100\n   The chargesheet covers basic elements but lacks several critical components that could strengthen the prosecution's case.\n\n2. MISSING ELEMENTS:\n   - Detailed witness examination records - See [Source 1: State v. Patel (2023)]\n   - Forensic evidence linking accused to crime scene - See [Source 2: SC Guidelines]\n   - Chain of custody documentation for seized evidence - See [Source 1]\n   - Medical examination reports of the deceased - See [Source 3: State v. Shah (2022)]\n\n3. WEAK POINTS:\n   - Motive not clearly established - Strengthen by adding circumstantial evidence - See [Source 1]\n   - Timeline of events needs more detail - Cross-reference with witness statements - See [Source 4]\n   - Eyewitness testimony appears incomplete - Record complete statements - See [Source 2]\n\n4. STRENGTHS:\n   - Proper invocation of Section 302 IPC\n   - Clear identification of accused\n   - Basic facts properly documented\n\n5. RECOMMENDATIONS:\n   - Obtain and attach forensic reports (fingerprints, DNA if available)\n   - Record detailed witness statements with specific timelines\n   - Include photographs of crime scene and evidence\n   - Add post-mortem report with cause of death details\n   - Document chain of custody for all seized items",
  "missing_elements": [
    "Detailed witness examination records",
    "Forensic evidence linking accused to crime scene",
    "Chain of custody documentation",
    "Medical examination reports"
  ],
  "weak_points": [
    "Motive not clearly established",
    "Timeline of events lacks detail",
    "Eyewitness testimony incomplete"
  ],
  "strengths": [
    "Proper legal section invocation",
    "Clear accused identification",
    "Basic facts documented"
  ],
  "recommendations": [
    "Obtain and attach forensic reports",
    "Record detailed witness statements",
    "Include crime scene photographs",
    "Add post-mortem report",
    "Document evidence chain of custody"
  ],
  "citations": [
    {
      "source": "State of Gujarat v. Ramesh Patel - Murder Case (2023)",
      "doc_type": "court_ruling",
      "court": "Gujarat High Court",
      "score": 0.89
    },
    {
      "source": "Supreme Court Guidelines on Chargesheet Preparation",
      "doc_type": "guideline",
      "court": "Supreme Court",
      "score": 0.84
    },
    {
      "source": "State v. Dinesh Shah - Homicide (2022)",
      "doc_type": "court_ruling",
      "court": "Sessions Court Ahmedabad",
      "score": 0.79
    },
    {
      "source": "CrPC Section 173 - Prosecution Guidelines",
      "doc_type": "bare_act",
      "court": null,
      "score": 0.76
    }
  ],
  "processing_time_ms": 3120
}
```

**Response Schema:**

| Field | Type | Description |
|-------|------|-------------|
| `query` | string | Processed chargesheet text |
| `completeness_score` | float | Score out of 100 |
| `response` | string | Full AI-generated review |
| `missing_elements` | array[string] | Critical gaps identified |
| `weak_points` | array[string] | Areas needing strengthening |
| `strengths` | array[string] | Well-done elements |
| `recommendations` | array[string] | Specific improvement actions |
| `citations` | array | Reference documents |
| `processing_time_ms` | integer | Processing time |

**Status Codes:**
- `200 OK` - Review completed
- `400 Bad Request` - Invalid chargesheet text
- `401 Unauthorized` - Authentication required
- `500 Internal Server Error` - Review failed

---

## Search API

### Natural Language Search

Search across all legal documents using natural language queries.

```http
POST /search/query
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "query": "bail provisions for murder cases",
  "filters": {
    "court": "Supreme Court",
    "doc_type": "court_ruling",
    "date_published": {
      "$gte": "2020-01-01"
    }
  },
  "collection": "court_rulings",
  "top_k": 10
}
```

**Request Schema:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | string | Yes | Search query (min 3 chars) |
| `filters` | object | No | Metadata filters (see Filter Operators) |
| `collection` | string | No | Collection to search: `all_documents`, `court_rulings`, `bare_acts` (default: all_documents) |
| `top_k` | integer | No | Max results to return (1-50, default: 10) |

**Filter Operators:**

| Operator | Description | Example |
|----------|-------------|---------|
| `$eq` | Equals | `{"court": {"$eq": "Supreme Court"}}` |
| `$ne` | Not equals | `{"doc_type": {"$ne": "internal"}}` |
| `$gt` | Greater than | `{"date_published": {"$gt": "2023-01-01"}}` |
| `$gte` | Greater than or equal | `{"date_published": {"$gte": "2023-01-01"}}` |
| `$lt` | Less than | `{"date_published": {"$lt": "2024-01-01"}}` |
| `$lte` | Less than or equal | `{"date_published": {"$lte": "2024-01-01"}}` |
| `$in` | In list | `{"court": {"$in": ["Supreme Court", "Gujarat HC"]}}` |
| `$nin` | Not in list | `{"doc_type": {"$nin": ["draft", "pending"]}}` |

**Response:**
```json
{
  "query": "bail provisions for murder cases",
  "results": [
    {
      "id": "abc123_chunk_5",
      "title": "Arnesh Kumar v. State of Bihar (2014)",
      "snippet": "The Supreme Court held that under Section 437 CrPC, bail cannot be denied mechanically. Even in serious offences, the court must consider the circumstances...",
      "document_type": "court_ruling",
      "source": "indian_kanoon",
      "court": "Supreme Court",
      "date_published": "2014-07-02",
      "sections_cited": ["437 CrPC", "439 CrPC"],
      "score": 0.92,
      "url": "https://indiankanoon.org/doc/1234567"
    },
    {
      "id": "def456_chunk_12",
      "title": "Sanjay Chandra v. CBI (2011)",
      "snippet": "The Supreme Court reiterated that bail is the rule and jail is the exception. The gravity of the offence alone cannot be the sole criterion for denial of bail...",
      "document_type": "court_ruling",
      "source": "indian_kanoon",
      "court": "Supreme Court",
      "date_published": "2011-11-09",
      "sections_cited": ["437 CrPC"],
      "score": 0.88,
      "url": "https://indiankanoon.org/doc/7654321"
    }
  ],
  "total_results": 10,
  "processing_time_ms": 145,
  "filters_applied": {
    "court": "Supreme Court",
    "doc_type": "court_ruling",
    "date_published": {
      "$gte": "2020-01-01"
    }
  }
}
```

**Search Result Schema:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique document chunk ID |
| `title` | string | Document/case title |
| `snippet` | string | Relevant text excerpt (max 500 chars) |
| `document_type` | string | Type of document |
| `source` | string | Data source |
| `court` | string | Court name (if applicable) |
| `date_published` | string | Publication date (ISO 8601) |
| `sections_cited` | array[string] | Legal sections referenced |
| `score` | float | Relevance score (0.0-1.0) |
| `url` | string | Source URL (if available) |

**Status Codes:**
- `200 OK` - Search completed
- `400 Bad Request` - Invalid query or filters
- `401 Unauthorized` - Authentication required
- `500 Internal Server Error` - Search failed

### Find Similar Cases

Find documents similar to a specific case.

```http
POST /search/similar
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "document_id": "abc123_chunk_5",
  "top_k": 10
}
```

**Status:** `501 Not Implemented` (Coming Soon)

### Get Available Filters

Retrieve all available filter options for search.

```http
GET /search/filters
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "document_types": [
    "court_ruling",
    "bare_act",
    "guideline",
    "fir",
    "chargesheet",
    "investigation_report"
  ],
  "sources": [
    "indian_kanoon",
    "ecourts",
    "gujarat_hc",
    "supreme_court",
    "india_code",
    "local_upload"
  ],
  "courts": [
    "Supreme Court",
    "Gujarat High Court",
    "District Court Ahmedabad",
    "District Court Surat",
    "Sessions Court Vadodara"
  ],
  "districts": [
    "Ahmedabad",
    "Surat",
    "Vadodara",
    "Rajkot",
    "Bhavnagar"
  ],
  "years": [2024, 2023, 2022, 2021, 2020, 2019, 2018]
}
```

**Status Codes:**
- `200 OK` - Filters retrieved
- `401 Unauthorized` - Authentication required
- `500 Internal Server Error` - Failed to fetch filters

---

## Utility Endpoints

### Convert Section Number

Convert between IPC↔BNS or CrPC↔BNSS section numbers.

```http
GET /utils/convert-section/{section}?from={from_code}&to={to_code}
Authorization: Bearer <access_token>
```

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `section` | string | Section number (e.g., "302", "376") |

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `from` | string | Yes | Source code: `IPC`, `BNS`, `CrPC`, `BNSS`, `IEA`, `BSA` |
| `to` | string | Yes | Target code: `IPC`, `BNS`, `CrPC`, `BNSS`, `IEA`, `BSA` |

**Example Request:**
```http
GET /utils/convert-section/302?from=IPC&to=BNS
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "query": "302",
  "mapping": {
    "old_code": "IPC",
    "old_section": "302",
    "old_title": "Punishment for murder",
    "new_code": "BNS",
    "new_section": "103",
    "new_title": "Punishment for murder",
    "description": "Whoever commits murder shall be punished with death or imprisonment for life, and shall also be liable to fine.",
    "is_decriminalized": false
  },
  "message": "Section 302 IPC maps to Section 103 BNS"
}
```

**Response (Decriminalized):**
```json
{
  "query": "497",
  "mapping": {
    "old_code": "IPC",
    "old_section": "497",
    "old_title": "Adultery",
    "new_code": "BNS",
    "new_section": null,
    "new_title": null,
    "description": "This offence has been decriminalized and does not exist in BNS",
    "is_decriminalized": true
  },
  "message": "Section 497 IPC has been decriminalized in BNS"
}
```

**Status Codes:**
- `200 OK` - Conversion successful
- `404 Not Found` - Section not found in mapping
- `400 Bad Request` - Invalid code parameters
- `401 Unauthorized` - Authentication required

### System Statistics

Get system usage statistics (Admin only).

```http
GET /utils/stats
Authorization: Bearer <admin_access_token>
```

**Response:**
```json
{
  "documents": {
    "total": 15234,
    "by_type": {
      "court_ruling": 12450,
      "bare_act": 156,
      "guideline": 234,
      "fir": 1234,
      "chargesheet": 987,
      "investigation_report": 173
    },
    "by_source": {
      "indian_kanoon": 8456,
      "ecourts": 2345,
      "gujarat_hc": 1234,
      "supreme_court": 567,
      "india_code": 156,
      "local_upload": 2476
    }
  },
  "embeddings": {
    "total_vectors": 152340,
    "collections": {
      "all_documents": 152340,
      "court_rulings": 124500,
      "bare_acts": 1560
    }
  },
  "queries": {
    "total": 45678,
    "last_24h": 234,
    "by_use_case": {
      "sop": 12345,
      "chargesheet": 8765,
      "general": 24568
    }
  },
  "users": {
    "total": 156,
    "active_today": 34,
    "by_role": {
      "officer": 134,
      "supervisor": 18,
      "admin": 4
    }
  }
}
```

---

## Error Handling

### Error Response Format

All errors follow a consistent JSON structure:

```json
{
  "error": "Error title",
  "detail": "Detailed error message",
  "status_code": 400
}
```

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| `200` | OK | Request successful |
| `201` | Created | Resource created |
| `400` | Bad Request | Invalid request parameters |
| `401` | Unauthorized | Missing or invalid authentication |
| `403` | Forbidden | Insufficient permissions |
| `404` | Not Found | Resource not found |
| `422` | Unprocessable Entity | Validation error |
| `429` | Too Many Requests | Rate limit exceeded |
| `500` | Internal Server Error | Server-side error |
| `501` | Not Implemented | Feature not yet available |
| `503` | Service Unavailable | Service temporarily down |

### Error Examples

**400 Bad Request:**
```json
{
  "error": "Validation error",
  "detail": [
    {
      "loc": ["body", "fir_details"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ],
  "status_code": 422
}
```

**401 Unauthorized:**
```json
{
  "error": "Unauthorized",
  "detail": "Invalid or expired token",
  "status_code": 401
}
```

**500 Internal Server Error:**
```json
{
  "error": "Internal server error",
  "detail": "RAG pipeline failed: ChromaDB connection timeout",
  "status_code": 500
}
```

### Error Handling Best Practices

**Client-Side:**

```python
import requests

response = requests.post(
    "http://localhost:8000/sop/suggest",
    headers={"Authorization": f"Bearer {token}"},
    json={"fir_details": "..."}
)

if response.status_code == 200:
    result = response.json()
    print(result["response"])
elif response.status_code == 401:
    # Refresh token and retry
    new_token = refresh_access_token()
    # Retry request...
elif response.status_code == 429:
    # Rate limited - wait and retry
    time.sleep(60)
    # Retry request...
else:
    # Handle other errors
    error = response.json()
    print(f"Error: {error['error']} - {error['detail']}")
```

---

## Rate Limiting

### Current Limits

**Per User Limits:**
- 100 requests per minute
- 1000 requests per hour
- 10,000 requests per day

**Per Endpoint Limits:**
- `/sop/suggest`: 10 requests per minute (resource-intensive)
- `/chargesheet/review`: 10 requests per minute (resource-intensive)
- `/search/query`: 30 requests per minute
- Other endpoints: 100 requests per minute

### Rate Limit Headers

Responses include rate limit information:

```http
HTTP/1.1 200 OK
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1707649200
```

### Rate Limit Exceeded Response

```http
HTTP/1.1 429 Too Many Requests
Content-Type: application/json
Retry-After: 60

{
  "error": "Rate limit exceeded",
  "detail": "You have exceeded the rate limit of 100 requests per minute. Please try again in 60 seconds.",
  "status_code": 429
}
```

---

## Request/Response Examples

### Complete Workflow Example

**1. Login:**
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "officer_kumar",
    "password": "securePassword123"
  }'
```

**2. Store Token:**
```bash
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**3. Get Investigation Guidance:**
```bash
curl -X POST http://localhost:8000/sop/suggest \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "fir_details": "Theft of motorcycle from parking area",
    "case_category": "theft",
    "sections_cited": ["379 IPC"],
    "top_k": 5
  }'
```

**4. Search for Similar Cases:**
```bash
curl -X POST http://localhost:8000/search/query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "motorcycle theft investigation procedures",
    "collection": "court_rulings",
    "top_k": 10
  }'
```

**5. Convert Section Number:**
```bash
curl -X GET "http://localhost:8000/utils/convert-section/379?from=IPC&to=BNS" \
  -H "Authorization: Bearer $TOKEN"
```

---

## SDKs & Client Libraries

### Python SDK

**Installation:**
```bash
pip install gujpol-slm-client
```

**Usage:**
```python
from gujpol_slm import Client

# Initialize client
client = Client(
    base_url="http://localhost:8000",
    username="officer_kumar",
    password="securePassword123"
)

# Get investigation guidance
result = client.sop.suggest(
    fir_details="Theft of gold ornaments...",
    case_category="theft",
    sections_cited=["379 IPC"]
)

print(result.response)
for citation in result.citations:
    print(f"- {citation.source} (score: {citation.score})")

# Search documents
results = client.search.query(
    query="bail provisions",
    filters={"court": "Supreme Court"},
    top_k=5
)

for doc in results.results:
    print(f"{doc.title} - {doc.score}")
```

### JavaScript/TypeScript SDK

**Installation:**
```bash
npm install @gujpol/slm-client
```

**Usage:**
```typescript
import { GujPolClient } from '@gujpol/slm-client';

// Initialize client
const client = new GujPolClient({
  baseUrl: 'http://localhost:8000',
  username: 'officer_kumar',
  password: 'securePassword123'
});

// Get investigation guidance
const result = await client.sop.suggest({
  firDetails: 'Theft of gold ornaments...',
  caseCategory: 'theft',
  sectionsCited: ['379 IPC']
});

console.log(result.response);
result.citations.forEach(citation => {
  console.log(`- ${citation.source} (score: ${citation.score})`);
});
```

---

## Appendix

### Request Headers

**Standard Headers:**
```http
Content-Type: application/json
Authorization: Bearer <access_token>
Accept: application/json
User-Agent: GujPol-Client/1.0
```

### Response Headers

**Standard Headers:**
```http
Content-Type: application/json
X-Process-Time: 0.2340
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-Correlation-ID: 550e8400-e29b-41d4-a716-446655440000
```

### Postman Collection

Download the complete Postman collection:
```
http://localhost:8000/api/postman-collection.json
```

### OpenAPI Specification

Download the OpenAPI 3.0 spec:
```
http://localhost:8000/openapi.json
```

---

**Document Version:** 1.0
**Last Updated:** February 11, 2026
**Maintained By:** Gujarat Police SLM Development Team
