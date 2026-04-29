import asyncio
from app.services.agent_service import run_agent

async def test_run_agent():
    code_snippet = """
def factorial(n):
    if n == 0:
        return 1
    else:
        return n * factorial(n-1)
"""
    result = await run_agent(code_snippet)
    print("Agent Output:", result)

asyncio.run(test_run_agent())