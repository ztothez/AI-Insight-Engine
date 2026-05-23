import json
import os
from together import Together
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

    # Step 3: Send to Together.ai Llama 3.3 70B
    client = Together(api_key=os.getenv("TOGETHER_API_KEY"))
    response = client.chat.completions.create(
        model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        max_tokens=1000
    )
    content = response.choices[0].message.content
    content = content.strip().removeprefix("```json").removesuffix("```").strip()

    parsed = LLMAnalysisResult.model_validate(json.loads(content))
    citation_sources = [
        CitationSource(doc_id=chunk.doc_id, chunk_index=chunk.chunk_index, text=chunk.text[:200])
        for chunk in context_chunks
    ]
    return parsed.model_dump(), citation_sources