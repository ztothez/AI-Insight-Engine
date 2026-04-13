import os
from fastapi import FastAPI
from app.routes.chat import router as chat_router

app = FastAPI()
favicon_path = "favicon.ico"

@app.get("/favicon.ico")
def favicon():
    return {"message": "This is the favicon endpoint."}
app.include_router(chat_router)