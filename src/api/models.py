"""
SQLAlchemy ORM Models - Database tables for Gujarat Police SLM.

Matches schema in docker/init-db.sql
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Time,
    BigInteger,
    ARRAY,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.orm import relationship

from src.api.database import Base


# ============================================
# Users and Authentication
# ============================================
class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="officer")
    rank = Column(String(100))
    badge_number = Column(String(50))
    police_station = Column(String(200))
    district = Column(String(100))
    phone = Column(String(20))
    is_active = Column(Boolean, default=True)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime)
    last_login = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    search_history = relationship("SearchHistory", back_populates="user")
    feedback = relationship("Feedback", back_populates="user")


# ============================================
# Documents
# ============================================
class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_type = Column(String(50), nullable=False, index=True)
    source = Column(String(50), nullable=False, index=True)
    source_url = Column(Text)
    title = Column(Text, nullable=False)
    content = Column(Text)
    content_hash = Column(String(64), unique=True)
    language = Column(String(10), default="en")
    case_number = Column(String(200), index=True)
    court = Column(String(200))
    district = Column(String(100), index=True)
    police_station = Column(String(200))
    date_published = Column(Date, index=True)
    date_ingested = Column(DateTime, default=datetime.utcnow)
    ocr_confidence = Column(Float)
    processing_status = Column(String(50), default="pending")
    doc_metadata = Column("metadata", Text, default="{}")  # JSON string for SQLite compatibility
    sections_cited = Column(Text)  # JSON array as string for SQLite
    judges = Column(Text)  # JSON array as string for SQLite
    parties = Column(Text)  # JSON array as string for SQLite
    is_indexed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    fir = relationship("FIR", back_populates="document", uselist=False)
    chargesheet = relationship("Chargesheet", back_populates="document", uselist=False)
    court_ruling = relationship("CourtRuling", back_populates="document", uselist=False)


# ============================================
# Section Mappings
# ============================================
class SectionMapping(Base):
    __tablename__ = "section_mappings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    old_code = Column(String(20), nullable=False, index=True)
    old_section = Column(String(20), nullable=False)
    new_code = Column(String(20), nullable=False, index=True)
    new_section = Column(String(20))
    old_title = Column(Text)
    new_title = Column(Text)
    description = Column(Text)
    is_decriminalized = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# ============================================
# FIR Structured Data
# ============================================
class FIR(Base):
    __tablename__ = "firs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"))
    fir_number = Column(String(100), nullable=False, index=True)
    fir_date = Column(Date, index=True)
    fir_time = Column(Time)
    police_station = Column(String(200), index=True)
    district = Column(String(100), index=True)
    complainant_name = Column(String(255))
    complainant_address = Column(Text)
    complainant_relation = Column(String(100))
    accused_details = Column(Text, default="[]")  # JSON array as string
    sections_cited = Column(Text)  # JSON array as string
    incident_description = Column(Text)
    incident_location = Column(Text)
    incident_date = Column(Date)
    incident_time = Column(Time)
    evidence_mentioned = Column(Text)  # JSON array as string
    status = Column(String(50), default="registered")
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    document = relationship("Document", back_populates="fir")
    chargesheets = relationship("Chargesheet", back_populates="fir")


# ============================================
# Chargesheet Structured Data
# ============================================
class Chargesheet(Base):
    __tablename__ = "chargesheets"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"))
    case_number = Column(String(200))
    fir_reference = Column(String(100))
    fir_id = Column(String(36), ForeignKey("firs.id"))
    accused_list = Column(Text, default="[]")  # JSON array as string
    witnesses_list = Column(Text, default="[]")  # JSON array as string
    evidence_inventory = Column(Text, default="[]")  # JSON array as string
    sections_charged = Column(Text)  # JSON array as string
    investigation_officer = Column(String(255))
    investigation_chronology = Column(Text, default="[]")  # JSON array as string
    forensic_reports = Column(Text, default="[]")  # JSON array as string
    filing_date = Column(Date)
    court_name = Column(String(200))
    completeness_score = Column(Float)
    review_notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    document = relationship("Document", back_populates="chargesheet")
    fir = relationship("FIR", back_populates="chargesheets")


# ============================================
# Court Rulings Structured Data
# ============================================
class CourtRuling(Base):
    __tablename__ = "court_rulings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"))
    case_citation = Column(String(500))
    case_number = Column(String(200))
    court_name = Column(String(200), index=True)
    bench = Column(String(200))
    judges = Column(Text)  # JSON array as string
    parties = Column(Text)  # JSON array as string
    charges_considered = Column(Text)  # JSON array as string
    verdict = Column(String(50), index=True)
    verdict_details = Column(Text, default="{}")  # JSON as string
    key_reasoning = Column(Text)
    sentences_imposed = Column(Text)  # JSON array as string
    precedents_cited = Column(Text)  # JSON array as string
    judgment_date = Column(Date, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    document = relationship("Document", back_populates="court_ruling")


# ============================================
# Audit Log
# ============================================
class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"))
    username = Column(String(100))
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(100))
    resource_id = Column(String(255))
    details = Column(Text, default="{}")  # JSON as string
    ip_address = Column(String(45))  # IPv6 compatible
    user_agent = Column(Text)
    request_method = Column(String(10))
    request_path = Column(Text)
    response_status = Column(Integer)
    prev_hash = Column(String(64))
    entry_hash = Column(String(64))


# ============================================
# User Feedback
# ============================================
class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"))
    query = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    rating = Column(Integer)  # 1-5
    is_positive = Column(Boolean)
    correction = Column(Text)
    feature = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="feedback")


# ============================================
# Search History
# ============================================
class SearchHistory(Base):
    __tablename__ = "search_history"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"))
    query = Column(Text, nullable=False)
    filters = Column(Text, default="{}")  # JSON as string
    results_count = Column(Integer)
    top_result_id = Column(String(36))
    response_time_ms = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="search_history")


# ============================================
# Training Progress
# ============================================
class TrainingProgress(Base):
    __tablename__ = "training_progress"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"))
    module_id = Column(String(50), nullable=False)
    module_name = Column(String(200))
    status = Column(String(50), default="not_started")
    score = Column(Float)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


# ============================================
# System Metrics
# ============================================
class SystemMetrics(Base):
    __tablename__ = "system_metrics"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    metric_name = Column(String(100), nullable=False, index=True)
    metric_value = Column(Float, nullable=False)
    tags = Column(Text, default="{}")  # JSON as string
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)
