import httpx
from loguru import logger
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.analyze import AnalyzeRequest, AnalyzeResponse, QualityScore
from app.db.database import get_db
from app.db.models import AnalysisRequest, AnalysisResponse
from app.core.limiter import limiter
from fastapi import Request

router = APIRouter()
url = "https://httpbin.org/get"

@router.post("/analyze", response_model=AnalyzeResponse)
@limiter.limit("5/minute")
async def analyze(request: Request, body: AnalyzeRequest, db: AsyncSession = Depends(get_db)):
    
    # STEP 1: Log the incoming request
    logger.debug(f"Received analysis request: {body}")
    
    # STEP 2: Save the request to DB
    db_request = AnalysisRequest(
        code_snippet=body.code_snippet,
        language=body.language,
        strictness_level=body.strictness_level,
    )
    db.add(db_request)
    await db.commit()
    await db.refresh(db_request)
    logger.info(f"Saved request to DB with id: {db_request.id}")

    # STEP 3: Make HTTP call
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        logger.info(f"External API response: {response.status_code}")

    # STEP 4: Build the response object
    analysis_response = AnalyzeResponse(
        scores=QualityScore(
            security=6.5,
            maintainability=5.0,
            readability=5.5,
            overall=5.5
        ),
        violations=["Hardcoding Values", "Lack of Error Handling", "Inconsistent Naming"],
        suggestion="Consider using configuration files for hardcoded values.",
    )

    # STEP 5: Save the response to DB
    db_response = AnalysisResponse(
        request_id=db_request.id,  # links to the request we saved in step 2
        overall_score=analysis_response.scores.overall,
        security_score=analysis_response.scores.security,
        maintainability_score=analysis_response.scores.maintainability,
        readability_score=analysis_response.scores.readability,
        violations=",".join(analysis_response.violations),
        suggestion=analysis_response.suggestion,
    )
    db.add(db_response)
    await db.commit()
    await db.refresh(db_response)
    logger.info(f"Saved response to DB with id: {db_response.id}")

    # STEP 6: Return the response
    return analysis_response