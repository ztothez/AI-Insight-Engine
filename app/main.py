from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException
from pathlib import Path
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
from app.routes.agent import router as agent_router
from app.routes.audit import router as audit_router

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Function logic: ensure database tables exist before serving requests.
    await init_db()
    yield


# STEP 1: Configure shared API behavior and error handling.
app = FastAPI(lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

# STEP 2: Expose the agent and analysis business workflows.
app.include_router(agent_router)
app.include_router(analyze_router)
app.include_router(audit_router)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def landing_page():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/analyze")
def analyze_page():
    return FileResponse(STATIC_DIR / "analyze.html")


@app.get("/agent")
def agent_page():
    return FileResponse(STATIC_DIR / "agent.html")


@app.get("/health")
def health_check():
    # Function logic: provide a lightweight availability check.
    return {"status": "200 OK"}
