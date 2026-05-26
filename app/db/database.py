from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import os
from app.db.models import Base
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = f"postgresql+asyncpg://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT_CONTAINER')}/{os.getenv('DB_NAME')}"

engine = create_async_engine(DATABASE_URL, echo=os.getenv('SQLALCHEMY_ECHO', 'false').lower() == 'true')

async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    # Function logic: provide one managed database session per API request.
    async with async_session() as session:
        yield session

async def init_db():
    # Function logic: create any registered tables missing at startup.
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)