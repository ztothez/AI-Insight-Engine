from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent
from app.services.tools import check_code_complexity, search_best_practices, calculate_risk_score

async def run_agent(code_snippet: str) -> str:
    llm = ChatOllama(model="qwen2.5:3b-instruct")
    tools = [check_code_complexity, search_best_practices, calculate_risk_score]
    agent = create_react_agent(llm, tools)
    result = await agent.ainvoke({"messages": [{"role": "user", "content": code_snippet}]})
    return result["messages"][-1].content