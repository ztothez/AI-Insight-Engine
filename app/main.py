from fastapi import FastAPI
from app.routes.chat import router as chat_router

app = FastAPI()


@app.get("/health")
def health_check():
    return {"status": "200 OK"}
