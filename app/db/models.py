from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import DeclarativeBase
from pgvector.sqlalchemy import Vector


import datetime

class Base(DeclarativeBase):
    pass

class AnalysisRequest(Base):
    __tablename__ = "analysis_requests"

    id = Column(Integer, primary_key=True, index=True)
    code_snippet = Column(String, nullable=False)
    language = Column(String, nullable=False)
    strictness_level = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class AnalysisResponse(Base):
    __tablename__ = "analysis_responses"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("analysis_requests.id"), nullable=False)
    overall_score = Column(Float, nullable=False)
    security_score = Column(Float, nullable=False)
    maintainability_score = Column(Float, nullable=False)
    readability_score = Column(Float, nullable=False)
    violations = Column(String, nullable=False)  # Store as comma-separated string
    suggestion = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class CodeEmbedding(Base):
    __tablename__ = "code_embeddings"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(String, nullable=False)

    embedding = Column(Vector(1024), nullable=False)  # Assuming 1024-dimensional embeddings
    doc_id = Column(String, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class BlockedInput(Base):
    """Audit log for inputs rejected by the prompt-injection validator.

    Stored server-side only. NEVER expose these rows to API clients —
    they contain attack payloads and matched-pattern details that would
    give attackers feedback on what tripped the detector.
    """
    __tablename__ = "blocked_inputs"

    id = Column(Integer, primary_key=True, index=True)
    blocked_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False, index=True)
    client_ip = Column(String(45), nullable=True)              # IPv6 max length = 45 chars
    reason = Column(String(50), nullable=False, index=True)    # RejectionReason enum value
    matched_pattern = Column(String(100), nullable=True)       # human-readable label
    input_snippet = Column(String, nullable=False)             # full rejected input
    input_length = Column(Integer, nullable=False)             # denormalized for fast stats
    user_agent = Column(String(500), nullable=True)            # helps identify bot patterns
