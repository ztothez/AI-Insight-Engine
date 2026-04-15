from fastapi import APIRouter
from app.schemas.analyze import AnalyzeRequest, AnalyzeResponse, QualityScore

router = APIRouter()

@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    return AnalyzeResponse(
        scores=QualityScore(
            security=6.5,
            maintainability=5.0,
            readability=5.5,
            overall=5.5
        ),
        violations=["Hardcoding Values", "Lack of Error Handling", "Inconsistent Naming"],
        suggestion="Consider using configuration files for hardcoded values, adding try-except blocks for error handling, and following a consistent naming convention for variables and functions.",
    )