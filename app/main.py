from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.routes.analyze import router as analyze_router
from app.db.database import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(lifespan=lifespan)

app.include_router(analyze_router)

@app.get("/health")
def health_check():
    return {"status": "200 OK"}