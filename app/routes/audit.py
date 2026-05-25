"""Unified audit endpoint: routes to RAG or agent based on query type."""
import httpx
from loguru import logger
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.audit import AuditRequest, AuditResponse
from app.schemas.analyze import AnalyzeResponse, QualityScore
from app.schemas.agent import AgentResponse
from app.db.database import get_db
from app.core.limiter import limiter
from app.core.input_validator import validate_code_input
from app.core.block_logger import log_blocked_input
from app.core.query_router import route, RouteTarget
from app.core.llm_retry import LLMUnavailable
from app.services.llm_service import analyze_code
from app.services.agent_service import run_agent


router = APIRouter()

_REJECTION_MESSAGE = (
    "Your input doesn't appear to be a code snippet. "
    "Please submit code in a supported language."
)


@router.post("/audit", response_model=AuditResponse)
@limiter.limit("5/minute")
async def audit(
    request: Request,
    body: AuditRequest,
    db: AsyncSession = Depends(get_db),
):
    # STEP 0: Input validation — silent rejection on prompt injection
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
        raise HTTPException(status_code=400, detail=_REJECTION_MESSAGE)

    # STEP 1: Route the request
    target = route(body.code_snippet)
    logger.info(
        f"/audit routing to {target.value} for input length {len(body.code_snippet)}"
    )

    # STEP 2: Dispatch to the chosen backend
    try:
        if target == RouteTarget.RAG:
            result, sources = await analyze_code(
                body.code_snippet, body.language, body.strictness_level, db
            )
            analyze_response = AnalyzeResponse(
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
            return AuditResponse(route="rag", analyze_response=analyze_response)

        # target == RouteTarget.AGENT
        agent_result = await run_agent(body.code_snippet)
        agent_response = AgentResponse(result=agent_result)
        return AuditResponse(route="agent", agent_response=agent_response)

    except LLMUnavailable as e:
        logger.error(f"LLM unavailable after retries: {e}")
        raise HTTPException(
            status_code=503,
            detail="Analysis service is temporarily unavailable. Please retry shortly.",
            headers={"Retry-After": "30"},
        )
    except httpx.HTTPError as e:
        logger.error(f"HTTP error during audit: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    except Exception as e:
        logger.exception(f"Unexpected error during audit: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")