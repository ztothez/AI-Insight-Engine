import httpx
from loguru import logger
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.analyze import AnalyzeRequest, AnalyzeResponse, QualityScore
from app.db.database import get_db
from app.db.models import AnalysisRequest, AnalysisResponse
from app.core.limiter import limiter
from app.core.input_validator import validate_code_input
from app.core.block_logger import log_blocked_input
from app.services.llm_service import analyze_code


router = APIRouter()


# Generic message returned to the client on any rejection.
# Deliberately vague — does NOT reveal which pattern matched.
# Same message for prompt-injection attacks AND for users who just sent
# the wrong thing. Silent rejection — deny attackers iteration feedback.
_REJECTION_MESSAGE = (
    "Your input doesn't appear to be a code snippet. "
    "Please submit code in a supported language."
)


@router.post("/analyze", response_model=AnalyzeResponse)
@limiter.limit("5/minute")
async def analyze(
    request: Request,
    body: AnalyzeRequest,
    db: AsyncSession = Depends(get_db),
):
    # STEP 0: Input validation (prompt-injection / non-code guard).
    # Runs BEFORE the DB write so blocked inputs don't pollute analysis_requests.
    validation = validate_code_input(body.code_snippet)
    if not validation.is_safe:
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        await log_blocked_input(
            db=db,
            result=validation,
            input_snippet=body.code_snippet,
            client_ip=client_ip,
            user_agent=user_agent,
        )
        # Same generic message regardless of which pattern matched.
        raise HTTPException(status_code=400, detail=_REJECTION_MESSAGE)

    # STEP 1: Log the incoming (now-validated) request
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
        result, sources = await analyze_code(
            body.code_snippet, body.language, body.strictness_level, db
        )
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
        sources=sources,
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
