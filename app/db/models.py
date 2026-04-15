from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import DeclarativeBase
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