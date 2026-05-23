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
