from pydantic import BaseModel

class AgentRequest(BaseModel):
    code_snippet: str
    session_id: str = "default"

class AgentResponse(BaseModel):
    result: str

