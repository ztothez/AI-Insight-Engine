from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from app.routes.analyze import router as analyze_router
from app.db.database import init_db
from app.core.errors import (
    validation_exception_handler,
    http_exception_handler,
    unhandled_exception_handler,
)
from app.core.limiter import limiter
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

app.include_router(analyze_router)

@app.get("/health")
def health_check():
    return {"status": "200 OK"}

