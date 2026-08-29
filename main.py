import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from llama_index.llms.openai import OpenAI

# Load environment variables
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_FILE = BASE_DIR / "frontend" / "index.html"

app = FastAPI(
    title="Shadow.Ai",
    version="1.0.0",
)


# =========================
# Configuration
# =========================

GAPGPT_API_KEY = os.getenv("GAPGPT_API_KEY")

GAPGPT_BASE_URL = os.getenv(
    "GAPGPT_BASE_URL",
    "https://api.gapgpt.app/v1",
)

MODEL = os.getenv(
    "MODEL",
    "gpt-4o-mini",
)


if not GAPGPT_API_KEY:
    raise RuntimeError(
        "GAPGPT_API_KEY is missing in environment variables"
    )


# =========================
# AI
# =========================

llm = OpenAI(
    model=MODEL,
    api_key=GAPGPT_API_KEY,
    api_base=GAPGPT_BASE_URL,
)


# =========================
# Request model
# =========================

class ChatRequest(BaseModel):
    message: str


# =========================
# Routes
# =========================

@app.get("/")
def root():
    if not FRONTEND_FILE.exists():
        raise HTTPException(
            status_code=404,
            detail="Frontend file not found",
        )

    return FileResponse(FRONTEND_FILE)


@app.get("/api/status")
def status():
    return {
        "name": "Shadow.Ai",
        "status": "online",
        "model": MODEL,
    }


@app.post("/chat")
def chat(request: ChatRequest):

    message = request.message.strip()

    if not message:
        raise HTTPException(
            status_code=400,
            detail="پیام نمی‌تواند خالی باشد.",
        )

    try:
        response = llm.complete(message)

        return {
            "answer": str(response),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"AI request failed: {str(e)}",
        )