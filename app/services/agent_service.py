from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent
from app.services.tools import check_code_complexity, search_best_practices, calculate_risk_score
from loguru import logger

async def run_agent(code_snippet: str) -> str:
    validate_agent_input(code_snippet)
    logger.info("Agent input validated")
    
    llm = ChatOllama(model="qwen2.5:3b-instruct")
    tools = [check_code_complexity, search_best_practices, calculate_risk_score]
    agent = create_react_agent(llm, tools)
    
    logger.info(f"Agent processing: {code_snippet[:50]}...")
    result = await agent.ainvoke({"messages": [{"role": "user", "content": code_snippet}]})
    
    output = result["messages"][-1].content
    logger.info(f"Agent returned: {output[:50]}...")
    return output

def validate_agent_input(code_snippet: str) -> None:
    BLOCKED_PHRASES = [
    "ignore previous instructions",
    "disregard all prior directives", 
    "forget instructions",
    "you are now",
    "run this",
    "execute",
    "install"
    ]

    for phrase in BLOCKED_PHRASES:
        if phrase in code_snippet.lower():
            raise ValueError(f"Input contains disallowed phrase: '{phrase}'")
    return None