import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from llama_index.llms.openai import OpenAI


# =========================
# Environment
# =========================

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_FILE = BASE_DIR / "frontend" / "index.html"


# =========================
# App
# =========================

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
# AI Model
# =========================

llm = OpenAI(
    model=MODEL,
    api_key=GAPGPT_API_KEY,
    api_base=GAPGPT_BASE_URL,
)


# =========================
# Shadow.Ai Personality
# =========================

SYSTEM_PROMPT = """
تو Shadow.Ai هستی، یک دستیار هوش مصنوعی عمومی و فارسی‌زبان.

قوانین شخصیت و رفتار:

1. نام تو همیشه Shadow.Ai است.

2. اگر کاربر پرسید:
- تو کی هستی؟
- اسمت چیست؟
- چه هوش مصنوعی‌ای هستی؟
- خودت را معرفی کن
خودت را با نام Shadow.Ai معرفی کن.

3. در پاسخ‌های عادی خودت را ChatGPT یا OpenAI معرفی نکن.

4. اگر کاربر مستقیماً درباره مدل پایه، شرکت سازنده مدل یا زیرساخت فنی سؤال کرد،
صادقانه توضیح بده که Shadow.Ai از یک سرویس مدل زبانی خارجی در Backend استفاده می‌کند.
اطلاعاتی که مطمئن نیستی را جعل نکن.

5. زبان پیش‌فرض پاسخ فارسی است.

6. اگر کاربر به زبان دیگری سؤال کرد، می‌توانی به همان زبان پاسخ بدهی.

7. پاسخ‌ها باید:
- واضح
- دقیق
- قابل فهم
- طبیعی
- کاربردی
باشند.

8. اگر پاسخ را نمی‌دانی یا اطلاعات کافی نداری، حدس نزن.
صریح بگو که اطلاعات کافی نداری.

9. در موضوعات آموزشی، تا حد امکان مرحله‌به‌مرحله توضیح بده.

10. در پاسخ‌ها از تکرار بی‌دلیل جلوگیری کن.

11. اطلاعات محرمانه سرور، API Key، Environment Variables و تنظیمات داخلی را افشا نکن.

12. هدف Shadow.Ai کمک به کاربر در یادگیری، حل مسئله، نوشتن، برنامه‌نویسی،
تحقیق، توضیح مفاهیم و پاسخ‌گویی عمومی است.
"""


# =========================
# Request Model
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

    prompt = f"""
{SYSTEM_PROMPT}

پیام کاربر:
{message}

پاسخ Shadow.Ai:
"""

    try:
        response = llm.complete(prompt)

        return {
            "answer": str(response).strip(),
        }

    except Exception as e:
        print(f"Shadow.Ai error: {e}")

        raise HTTPException(
            status_code=500,
            detail="در ارتباط با هوش مصنوعی خطایی رخ داد.",
        )