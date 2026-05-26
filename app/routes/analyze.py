import httpx
from loguru import logger
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.cache import get_redis_client, make_cache_key, get_cached, set_cached
from app.schemas.analyze import AnalyzeRequest, AnalyzeResponse, QualityScore
from app.db.database import get_db
from app.db.models import AnalysisRequest, AnalysisResponse
from app.core.limiter import limiter
from app.core.input_validator import validate_code_input
from app.core.block_logger import log_blocked_input
from app.services.llm_service import analyze_code
from app.core.llm_retry import LLMUnavailable

router = APIRouter()
redis_client = get_redis_client()


# Function logic: keep rejection reasons internal while giving clients one safe response.
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
    # STEP 1: Reject unsafe or non-code input before saving an analysis request.
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
        # Function logic: record the reason internally, but do not expose it.
        raise HTTPException(status_code=400, detail=_REJECTION_MESSAGE)

    # STEP 2: Log the accepted request for operational visibility.
    logger.debug(f"Received analysis request: {body}")

    # STEP 2.5: Check cache before hitting the LLM
    cache_key = make_cache_key(body.code_snippet, body.language, body.strictness_level)
    cached = await get_cached(redis_client, cache_key)
    if cached:
        logger.info(f"Cache hit for key {cache_key[:16]}...")
        return AnalyzeResponse(**cached)
    logger.info(f"Cache miss for key {cache_key[:16]}...")

    # STEP 3: Save the accepted request before running external analysis.
    db_request = AnalysisRequest(
        code_snippet=body.code_snippet,
        language=body.language,
        strictness_level=body.strictness_level,
    )
    db.add(db_request)
    await db.commit()
    await db.refresh(db_request)
    logger.info(f"Saved request to DB with id: {db_request.id}")

    # STEP 4: Run the retrieval-grounded LLM analysis.
    try:
        result, sources = await analyze_code(
            body.code_snippet, body.language, body.strictness_level, db
        )
        logger.debug(f"Received analysis response: {result}")
    except LLMUnavailable:
        logger.error("LLM unavailable after all retry attempts")
        raise HTTPException(status_code=503, detail="Service temporarily unavailable")
    except httpx.HTTPError as e:
        logger.error(f"HTTP error during code analysis: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during code analysis: {e}")
        raise

    # STEP 5: Shape and validate the response returned by the API.
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

    # STEP 6: Persist the scored result for traceability.
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

    # STEP 7: Return the structured result and its source citations.
    await set_cached(redis_client, cache_key, analysis_response.model_dump())
    return analysis_response
