import json
import httpx
from app.services.prompt_service import SYSTEM_PROMPT, build_user_prompt
from app.schemas.analyze import LLMAnalysisResult

async def analyze_code(code_snippet: str, language: str, strictness_level: int) -> dict:
    user_prompt = build_user_prompt(code_snippet, language, strictness_level)
    payload = {
        "model": "qwen2.5:3b-instruct",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        "stream": False
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post("http://localhost:11434/api/chat", json=payload)
        response.raise_for_status()
        result = response.json()
        content = result["message"]["content"]
        content = content.strip().removeprefix("```json").removesuffix("```").strip()  
    parsed = LLMAnalysisResult.model_validate(json.loads(content))
    return parsed.model_dump()

    