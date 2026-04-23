import httpx
from loguru import logger
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.analyze import AnalyzeRequest, AnalyzeResponse, QualityScore
from app.db.database import get_db
from app.db.models import AnalysisRequest
from app.core.limiter import limiter
from fastapi import Request

router = APIRouter()
url = "https://httpbin.org/get"

@router.post("/analyze", response_model=AnalyzeResponse)
@limiter.limit("5/minute")
async def analyze(request: Request, body: AnalyzeRequest, db: AsyncSession = Depends(get_db)):
    logger.debug(f"Received analysis request: {body}")
    db_request = AnalysisRequest(
        code_snippet=body.code_snippet,
        language=body.language,
        strictness_level=body.strictness_level,
    )

    db.add(db_request)
    await db.commit()
    await db.refresh(db_request)
    logger.info(f"saved analysis request to database with id: {db_request.id}")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        logger.info(f"External API response: {response.status_code} - {response.text}")
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