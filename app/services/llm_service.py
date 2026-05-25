import json
import os
from together import Together
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.llm_retry import call_with_retry
from app.services.embedding_service import retrieve
from app.services.prompt_service import SYSTEM_PROMPT, build_user_prompt
from app.schemas.analyze import LLMAnalysisResult, CitationSource
from app.core.output_filter import filter_hallucinated_violations

async def analyze_code(code_snippet: str, language: str, strictness_level: int, db: AsyncSession) -> tuple[dict, list]:
    # STEP 1: Retrieve relevant knowledge-base context for the submitted code.
    context_chunks = await retrieve(code_snippet, db)
    context = "\n\n".join([chunk.text for chunk in context_chunks])

    # STEP 2: Build an analysis prompt grounded in the retrieved context.
    user_prompt = build_user_prompt(code_snippet, language, strictness_level, context)

    # STEP 3: Request a structured quality review from the language model.
    client = Together(api_key=os.getenv("TOGETHER_API_KEY"))

    async def call_llm():
        return client.chat.completions.create(
            model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=1000
        )

    response = await call_with_retry(call_llm)
    content = response.choices[0].message.content
    content = content.strip().removeprefix("```json").removesuffix("```").strip()

    # STEP 4: Validate the result and attach readable source references.
    parsed = LLMAnalysisResult.model_validate(json.loads(content))
    citation_sources = [
        CitationSource(doc_id=chunk.doc_id, chunk_index=chunk.chunk_index, text=chunk.text[:200])
        for chunk in context_chunks
    ]
    parsed.violations = filter_hallucinated_violations(parsed.violations, code_snippet)
    return parsed.model_dump(), citation_sources
