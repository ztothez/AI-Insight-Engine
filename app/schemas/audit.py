from pydantic import BaseModel
from app.schemas.analyze import AnalyzeRequest, AnalyzeResponse
from app.schemas.agent import AgentResponse


class AuditRequest(AnalyzeRequest):
    """Same shape as AnalyzeRequest. Agent ignores language and strictness."""
    pass


class AuditResponse(BaseModel):
    """Wraps either an analyze response or an agent response.
    
    Exactly one of analyze_response or agent_response is populated;
    `route` tells the client which.
    """
    route: str
    analyze_response: AnalyzeResponse | None = None
    agent_response: AgentResponse | None = None