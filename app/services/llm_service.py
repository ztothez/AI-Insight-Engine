import json
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.embedding_service import retrieve
from app.services.prompt_service import SYSTEM_PROMPT, build_user_prompt
from app.schemas.analyze import LLMAnalysisResult, CitationSource

async def analyze_code(code_snippet: str, language: str, strictness_level: int, db: AsyncSession) -> tuple[dict, list]:
    # Step 1: Retrieve context
    context_chunks = await retrieve(code_snippet, db)
    context = "\n\n".join([chunk.text for chunk in context_chunks])

    # Step 2: Build prompt
    user_prompt = build_user_prompt(code_snippet, language, strictness_level, context)

    # Step 3: Send to Ollama
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
        citation_sources = [
        CitationSource(
            doc_id=chunk.doc_id,
            chunk_index=chunk.chunk_index,
            text=chunk.text[:200]
        )
        for chunk in context_chunks
    ]
    return parsed.model_dump(), citation_sources