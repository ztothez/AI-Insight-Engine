from pydantic import BaseModel, Field
from enum import Enum
from typing import List

class ProgrammingLanguage(str, Enum):
    PYTHON = "python"

class AnalyzeRequest(BaseModel):
    code_snippet: str
    language: ProgrammingLanguage
    strictness_level: int = Field(default=3, ge=1, le=5)

class QualityScore(BaseModel):
    overall: float = Field(ge=0.0, le=10.0)
    security: float = Field(ge=0.0, le=10.0)
    maintainability: float = Field(ge=0.0, le=10.0)
    readability: float = Field(ge=0.0, le=10.0)

class AnalyzeResponse(BaseModel):
    scores: QualityScore
    violations: List[str]
    suggestion: str