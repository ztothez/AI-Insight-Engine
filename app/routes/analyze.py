import httpx
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.analyze import AnalyzeRequest, AnalyzeResponse, QualityScore
from app.db.database import get_db
from app.db.models import AnalysisRequest

router = APIRouter()
url = "https://httpbin.org/get"

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest, db: AsyncSession = Depends(get_db)) -> AnalyzeResponse:
    db_request = AnalysisRequest(
        code_snippet=request.code_snippet,
        language=request.language,
        strictness_level=request.strictness_level,
    )

    db.add(db_request)
    await db.commit()
    await db.refresh(db_request)

    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        print(response.status_code, response.json())
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