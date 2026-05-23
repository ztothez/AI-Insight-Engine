import httpx
from loguru import logger
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.analyze import AnalyzeRequest, AnalyzeResponse, QualityScore
from app.db.database import get_db
from app.db.models import AnalysisRequest, AnalysisResponse
from app.core.limiter import limiter
from fastapi import Request
from app.services.llm_service import analyze_code

router = APIRouter()

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
    try:
        result = await analyze_code(body.code_snippet, body.language, body.strictness_level, db)
        logger.debug(f"Received analysis response: {result}")
    except httpx.HTTPError as e:
        logger.error(f"HTTP error during code analysis: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during code analysis: {e}")
        raise

    analysis_response = AnalyzeResponse(
        scores=QualityScore(
            overall=result["overall"],
            security=result["security"],
            maintainability=result["maintainability"],
            readability=result["readability"],
        ),
        violations=result["violations"],
        suggestion=result["suggestion"],
    )

    # STEP 5: Save the response to DB
    db_response = AnalysisResponse(
        request_id=db_request.id,
        overall_score=result["overall"],
        security_score=result["security"],
        maintainability_score=result["maintainability"],
        readability_score=result["readability"],
        violations=",".join(result["violations"]),
        suggestion=result["suggestion"],
    )

    db.add(db_response)
    await db.commit()
    await db.refresh(db_response)
    logger.info(f"Saved response to DB with id: {db_response.id}")

    # STEP 6: Return the response
    return analysis_response