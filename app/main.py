import os
from fastapi import FastAPI
from fastapi_health import health
from app.routes.chat import router as chat_router

app = FastAPI()
favicon_path = "favicon.ico"

@app.get("/favicon.ico")
def favicon():
    return {"message": "This is the favicon endpoint."}
app.include_router(chat_router)

@app.get("/health")
def health_check():
    return {"status": "200 OK"}