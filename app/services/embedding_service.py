from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.db.models import CodeEmbedding
from together import Together
from dotenv import load_dotenv
import os

load_dotenv()

def get_embedding(text: str) -> list[float]:
    client = Together(api_key=os.getenv("TOGETHER_API_KEY"))
    response = client.embeddings.create(
        model="intfloat/multilingual-e5-large-instruct",
        input=text
    )

    return response.data[0].embedding


async def store_embedding(text: str, doc_id: str, chunk_index: int, db: AsyncSession) -> CodeEmbedding:
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
    from app.services.chunker_service import chunk_text
    chunks = chunk_text(text)
    embeddings = []
    for idx, chunk in enumerate(chunks):
        embedding = await store_embedding(chunk, doc_id, idx, db)
        embeddings.append(embedding)
    return embeddings

async def retrieve(query: str, db: AsyncSession, top_k: int = 3) -> list[CodeEmbedding]:
    query_vector = get_embedding(query)
    result = await db.execute(
        select(CodeEmbedding)
        .order_by(CodeEmbedding.embedding.op("<=>")(query_vector))
        .limit(top_k)
    )
    return result.scalars().all()