-- Gujarat Police SLM - Database Initialization
-- PostgreSQL 16

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ============================================
-- Users and Authentication
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'officer',
    rank VARCHAR(100),
    badge_number VARCHAR(50),
    police_station VARCHAR(200),
    district VARCHAR(100),
    phone VARCHAR(20),
    is_active BOOLEAN DEFAULT true,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- Documents
-- ============================================
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_type VARCHAR(50) NOT NULL,
    source VARCHAR(50) NOT NULL,
    source_url TEXT,
    title TEXT NOT NULL,
    content TEXT,
    content_hash VARCHAR(64) UNIQUE,
    language VARCHAR(10) DEFAULT 'en',
    case_number VARCHAR(200),
    court VARCHAR(200),
    district VARCHAR(100),
    police_station VARCHAR(200),
    date_published DATE,
    date_ingested TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ocr_confidence FLOAT,
    processing_status VARCHAR(50) DEFAULT 'pending',
    metadata JSONB DEFAULT '{}',
    sections_cited TEXT[],
    judges TEXT[],
    parties TEXT[],
    is_indexed BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_documents_type ON documents(document_type);
CREATE INDEX idx_documents_source ON documents(source);
CREATE INDEX idx_documents_district ON documents(district);
CREATE INDEX idx_documents_case_number ON documents(case_number);
CREATE INDEX idx_documents_date ON documents(date_published);
CREATE INDEX idx_documents_sections ON documents USING GIN(sections_cited);
CREATE INDEX idx_documents_content_trgm ON documents USING GIN(content gin_trgm_ops);
CREATE INDEX idx_documents_title_trgm ON documents USING GIN(title gin_trgm_ops);

-- ============================================
-- Section Mappings (IPC ↔ BNS, CrPC ↔ BNSS)
-- ============================================
CREATE TABLE IF NOT EXISTS section_mappings (
    id SERIAL PRIMARY KEY,
    old_code VARCHAR(20) NOT NULL,
    old_section VARCHAR(20) NOT NULL,
    new_code VARCHAR(20) NOT NULL,
    new_section VARCHAR(20),
    old_title TEXT,
    new_title TEXT,
    description TEXT,
    is_decriminalized BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(old_code, old_section, new_code)
);

CREATE INDEX idx_section_old ON section_mappings(old_code, old_section);
CREATE INDEX idx_section_new ON section_mappings(new_code, new_section);

-- ============================================
-- FIR Structured Data
-- ============================================
CREATE TABLE IF NOT EXISTS firs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    fir_number VARCHAR(100) NOT NULL,
    fir_date DATE,
    fir_time TIME,
    police_station VARCHAR(200),
    district VARCHAR(100),
    complainant_name VARCHAR(255),
    complainant_address TEXT,
    complainant_relation VARCHAR(100),
    accused_details JSONB DEFAULT '[]',
    sections_cited TEXT[],
    incident_description TEXT,
    incident_location TEXT,
    incident_date DATE,
    incident_time TIME,
    evidence_mentioned TEXT[],
    status VARCHAR(50) DEFAULT 'registered',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_firs_number ON firs(fir_number);
CREATE INDEX idx_firs_district ON firs(district);
CREATE INDEX idx_firs_ps ON firs(police_station);
CREATE INDEX idx_firs_date ON firs(fir_date);
CREATE INDEX idx_firs_sections ON firs USING GIN(sections_cited);

-- ============================================
-- Chargesheet Structured Data
-- ============================================
CREATE TABLE IF NOT EXISTS chargesheets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    case_number VARCHAR(200),
    fir_reference VARCHAR(100),
    fir_id UUID REFERENCES firs(id),
    accused_list JSONB DEFAULT '[]',
    witnesses_list JSONB DEFAULT '[]',
    evidence_inventory JSONB DEFAULT '[]',
    sections_charged TEXT[],
    investigation_officer VARCHAR(255),
    investigation_chronology JSONB DEFAULT '[]',
    forensic_reports JSONB DEFAULT '[]',
    filing_date DATE,
    court_name VARCHAR(200),
    completeness_score FLOAT,
    review_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- Court Rulings Structured Data
-- ============================================
CREATE TABLE IF NOT EXISTS court_rulings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    case_citation VARCHAR(500),
    case_number VARCHAR(200),
    court_name VARCHAR(200),
    bench VARCHAR(200),
    judges TEXT[],
    parties TEXT[],
    charges_considered TEXT[],
    verdict VARCHAR(50),
    verdict_details JSONB DEFAULT '{}',
    key_reasoning TEXT,
    sentences_imposed TEXT[],
    precedents_cited TEXT[],
    judgment_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_rulings_court ON court_rulings(court_name);
CREATE INDEX idx_rulings_verdict ON court_rulings(verdict);
CREATE INDEX idx_rulings_date ON court_rulings(judgment_date);

-- ============================================
-- Audit Log (append-only, tamper-proof)
-- ============================================
CREATE TABLE IF NOT EXISTS audit_log (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    user_id UUID REFERENCES users(id),
    username VARCHAR(100),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id VARCHAR(255),
    details JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    request_method VARCHAR(10),
    request_path TEXT,
    response_status INTEGER,
    prev_hash VARCHAR(64),
    entry_hash VARCHAR(64)
);

CREATE INDEX idx_audit_user ON audit_log(user_id);
CREATE INDEX idx_audit_timestamp ON audit_log(timestamp);
CREATE INDEX idx_audit_action ON audit_log(action);

-- Make audit log append-only (no UPDATE/DELETE)
CREATE OR REPLACE RULE audit_no_update AS ON UPDATE TO audit_log DO INSTEAD NOTHING;
CREATE OR REPLACE RULE audit_no_delete AS ON DELETE TO audit_log DO INSTEAD NOTHING;

-- ============================================
-- User Feedback
-- ============================================
CREATE TABLE IF NOT EXISTS feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    query TEXT NOT NULL,
    response TEXT NOT NULL,
    rating INTEGER CHECK (rating BETWEEN 1 AND 5),
    is_positive BOOLEAN,
    correction TEXT,
    feature VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- Search History
-- ============================================
CREATE TABLE IF NOT EXISTS search_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    query TEXT NOT NULL,
    filters JSONB DEFAULT '{}',
    results_count INTEGER,
    top_result_id UUID,
    response_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- Training Progress (for officer training module)
-- ============================================
CREATE TABLE IF NOT EXISTS training_progress (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    module_id VARCHAR(50) NOT NULL,
    module_name VARCHAR(200),
    status VARCHAR(50) DEFAULT 'not_started',
    score FLOAT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, module_id)
);

-- ============================================
-- System Metrics
-- ============================================
CREATE TABLE IF NOT EXISTS system_metrics (
    id BIGSERIAL PRIMARY KEY,
    metric_name VARCHAR(100) NOT NULL,
    metric_value FLOAT NOT NULL,
    tags JSONB DEFAULT '{}',
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_metrics_name ON system_metrics(metric_name);
CREATE INDEX idx_metrics_time ON system_metrics(recorded_at);

-- ============================================
-- Default Admin User
-- password: changeme (bcrypt hash)
-- ============================================
INSERT INTO users (username, email, password_hash, full_name, role, district)
VALUES (
    'admin',
    'admin@gujpol.gov.in',
    '$2b$12$LJ3mFsAil.2LrVUBPh0O4eF1rXXzJvF8V0K8wF5qF5qF5qF5qF5q',
    'System Administrator',
    'admin',
    'Gandhinagar'
) ON CONFLICT (username) DO NOTHING;
