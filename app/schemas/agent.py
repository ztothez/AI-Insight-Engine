from pydantic import BaseModel

class AgentRequest(BaseModel):
    code_snippet: str

class AgentResponse(BaseModel):
    result: str