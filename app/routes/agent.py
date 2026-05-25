from fastapi import APIRouter, HTTPException, Request
from app.services.agent_service import run_agent
from app.schemas.agent import AgentRequest, AgentResponse
from app.core.limiter import limiter
from loguru import logger
router = APIRouter()

@router.post("/agent", response_model=AgentResponse)
@limiter.limit("5/minute")
async def agent(request: Request, body: AgentRequest):
    # STEP 1: Record the received agent request.
    logger.debug(f"Received agent request: {body}")
    
    # STEP 2: Execute the agent and translate failures to API responses.
    try:
        result = await run_agent(body.code_snippet)
        logger.debug(f"Agent returned result: {result}")
    except ValueError as e:
        logger.error(f"Input validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during agent execution: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    
    # STEP 3: Return the agent's final recommendation.
    return AgentResponse(result=result)
