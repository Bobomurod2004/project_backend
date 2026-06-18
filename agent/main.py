import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import chat

app = FastAPI(title="AI Agent", version="0.1.0")

# CORS — production'da aniq domenlar:
# CORS_ORIGINS="https://ai.example.com,https://app.example.com"
_origins_raw = os.getenv("CORS_ORIGINS", "*")
_origins = [o.strip() for o in _origins_raw.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins or ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/ai")


@app.get("/ai/health")
def health():
    return {"status": "ok", "service": "agent"}
