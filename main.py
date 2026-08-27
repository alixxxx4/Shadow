import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from llama_index.llms.openai import OpenAI

load_dotenv()

app = FastAPI(title="Shadow.Ai")


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
    raise RuntimeError("GAPGPT_API_KEY is missing in .env")


llm = OpenAI(
    model=MODEL,
    api_key=GAPGPT_API_KEY,
    api_base=GAPGPT_BASE_URL,
)


class ChatRequest(BaseModel):
    message: str


@app.get("/")
def root():
    return FileResponse("frontend/index.html")


@app.get("/api/status")
def status():
    return {
        "name": "Shadow.Ai",
        "status": "online",
        "model": MODEL,
    }


@app.post("/chat")
def chat(request: ChatRequest):
    if not request.message.strip():
        raise HTTPException(
            status_code=400,
            detail="پیام نمی‌تواند خالی باشد.",
        )

    try:
        response = llm.complete(request.message)

        return {
            "answer": str(response),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )