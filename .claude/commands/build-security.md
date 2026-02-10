Implement security hardening for the Gujarat Police SLM system. This handles sensitive law enforcement data.

## 1. Data Encryption (`src/security/encryption.py`)
- At rest: AES-256 encryption for stored documents using cryptography library
- PII fields: Additional field-level encryption with SEPARATE key (PII_ENCRYPTION_KEY from .env)
- Functions: encrypt_field(data, key), decrypt_field(data, key)
- encrypt_document(doc_dict, pii_fields=["complainant_name","accused_details","address","phone","aadhaar"])

## 2. PII Handler (`src/security/pii.py`)
- Detect PII in text: names, addresses, phone numbers, Aadhaar numbers
- Regex patterns for Indian PII formats
- Tag PII spans in document text
- Redact capability (replace with [REDACTED]) for training data
- Store PII mapping separately with encryption

## 3. Authentication (`src/security/auth.py`)
- JWT token generation and verification
- Password hashing with bcrypt (12 rounds)
- Access token: 15 minutes, Refresh token: 7 days
- Token blacklist in Redis for logout
- Brute force: lock account after 5 failed attempts for 30 minutes

## 4. RBAC (`src/security/rbac.py`)
- Roles: admin, senior_officer, officer, viewer
- Permission matrix:
  - admin: ALL endpoints + user management + audit logs
  - senior_officer: all features + analytics + export
  - officer: SOP assistant + chargesheet review + search
  - viewer: read-only search
- Decorator: @require_role("admin", "senior_officer")

## 5. Audit Logger (`src/security/audit.py`)
- Log every API call: user_id, action, resource, timestamp, IP, user_agent
- Log every document access
- Log every search query and model response
- Tamper-proof: each log entry includes hash of previous entry (hash chain)
- Append-only PostgreSQL table (UPDATE/DELETE rules blocked in init-db.sql)
- Retain for 2 years

## 6. Input Sanitization (`src/security/sanitize.py`)
- Prevent prompt injection: strip/escape control characters, limit input length
- SQL injection prevention (via SQLAlchemy parameterized queries, but double-check)
- XSS prevention for any user-generated content
- Rate limiting: per user AND per IP (using Redis)

## 7. Network Security (document in configs/security_policy.md)
- No external API calls from production system (air-gapped)
- Only ports 443 (HTTPS) and 22 (SSH) open
- VPN requirement for remote access
- All inter-service communication on internal Docker network only

## 8. Tests
Create tests/unit/test_security.py:
- Test encryption/decryption roundtrip
- Test PII detection accuracy
- Test JWT token lifecycle
- Test RBAC permission checks
- Test prompt injection prevention
- Test audit log chain integrity
