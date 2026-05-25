from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.db.models import CodeEmbedding
from together import Together
from dotenv import load_dotenv
import os

load_dotenv()

def get_embedding(text: str) -> list[float]:
    # Function logic: convert text into the vector format used for similarity search.
    client = Together(api_key=os.getenv("TOGETHER_API_KEY"))
    response = client.embeddings.create(
        model="intfloat/multilingual-e5-large-instruct",
        input=text
    )

    return response.data[0].embedding


async def store_embedding(text: str, doc_id: str, chunk_index: int, db: AsyncSession) -> CodeEmbedding:
    # Function logic: embed one chunk and persist its source identity.
    embedding_vector = get_embedding(text)
    code_embedding = CodeEmbedding(
        text=text,
        embedding=embedding_vector,
        doc_id=doc_id,
        chunk_index=chunk_index
    )
    db.add(code_embedding)
    await db.commit()
    await db.refresh(code_embedding)
    return code_embedding

async def ingest_document(text: str, doc_id: str, db: AsyncSession) -> list[CodeEmbedding]:
    # STEP 1: Split a reference document into searchable sections.
    from app.services.chunker_service import chunk_text
    chunks = chunk_text(text)
    embeddings = []
    # STEP 2: Store each section with its document and position metadata.
    for idx, chunk in enumerate(chunks):
        embedding = await store_embedding(chunk, doc_id, idx, db)
        embeddings.append(embedding)
    return embeddings

async def retrieve(query: str, db: AsyncSession, top_k: int = 5) -> list[CodeEmbedding]:
    # STEP 1: Embed the submitted code in the same space as the references.
    query_vector = get_embedding(query)
    # STEP 2: Return the closest reference chunks for prompt grounding.
    result = await db.execute(
        select(CodeEmbedding)
        .order_by(CodeEmbedding.embedding.op("<=>")(query_vector))
        .limit(top_k)
    )
    return result.scalars().all()
