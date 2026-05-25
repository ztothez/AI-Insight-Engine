from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent
from app.services.tools import check_code_complexity, search_best_practices, calculate_risk_score
from loguru import logger

async def run_agent(code_snippet: str) -> str:
    # STEP 1: Validate user input before exposing it to agent tools.
    validate_agent_input(code_snippet)
    logger.info("Agent input validated")
    
    # STEP 2: Assemble the reasoning model and available code-review tools.
    llm = ChatOllama(model="qwen2.5:3b-instruct")
    tools = [check_code_complexity, search_best_practices, calculate_risk_score]
    agent = create_react_agent(llm, tools)
    
    # STEP 3: Run the agent against the submitted snippet.
    logger.info(f"Agent processing: {code_snippet[:50]}...")
    result = await agent.ainvoke({"messages": [{"role": "user", "content": code_snippet}]})
    
    # STEP 4: Return the agent's final message as the endpoint result.
    output = result["messages"][-1].content
    logger.info(f"Agent returned: {output[:50]}...")
    return output

def validate_agent_input(code_snippet: str) -> None:
    # Function logic: reject empty, oversized, or directive-like agent inputs.
    if not code_snippet.strip():
        raise ValueError("Code snippet cannot be empty.")
    if len(code_snippet) > 10000:
        raise ValueError("Code snippet is too long.")

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
