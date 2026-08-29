import os
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import bcrypt
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from jose import JWTError, jwt
from llama_index.llms.openai import OpenAI
from pydantic import BaseModel, EmailStr, Field

from database import get_connection, init_database


# =========================================================
# ENVIRONMENT
# =========================================================

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_FILE = BASE_DIR / "frontend" / "index.html"


# =========================================================
# APPLICATION
# =========================================================

app = FastAPI(
    title="Shadow.Ai",
    description="Shadow.Ai - AI Assistant",
    version="1.0.0",
)


# =========================================================
# DATABASE
# =========================================================

init_database()


# =========================================================
# SHADOW.AI IDENTITY
# =========================================================

SHADOW_AI_NAME = "Shadow.Ai"
SHADOW_AI_VERSION = "1.0.0"

# این مقدار را بعداً می‌توانیم با نام واقعی سازنده عوض کنیم.
SHADOW_AI_DEVELOPER = os.getenv(
    "SHADOW_AI_DEVELOPER",
    "Shadow.Ai Development Team",
)

SHADOW_AI_CREATOR = os.getenv(
    "SHADOW_AI_CREATOR",
    "Shadow.Ai Development Team",
)

SHADOW_AI_DESCRIPTION = (
    "دستیار هوش مصنوعی عمومی برای پاسخ‌گویی، "
    "آموزش، برنامه‌نویسی، تحلیل و حل مسئله."
)

SHADOW_AI_CAPABILITIES = [
    "پاسخ‌گویی هوشمند",
    "آموزش و یادگیری",
    "برنامه‌نویسی",
    "رفع خطای برنامه‌نویسی",
    "حل مسئله",
    "تحلیل اطلاعات",
    "تولید محتوا",
    "ویرایش متن",
    "ترجمه",
    "کمک در پروژه‌های فنی",
    "گفتگوی هوشمند",
]


# =========================================================
# PLAN CONFIGURATION
# =========================================================

FREE_PLAN = "free"
STANDARD_PLAN = "standard"
PRO_PLAN = "pro"

FREE_MESSAGE_LIMIT = 30

STANDARD_MESSAGE_LIMIT = None
PRO_MESSAGE_LIMIT = None

STANDARD_PRICE_TOMAN = 100_000
PRO_PRICE_TOMAN = 500_000

SUBSCRIPTION_DAYS = 30


# =========================================================
# AUTHENTICATION
# =========================================================

SECRET_KEY = os.getenv("SECRET_KEY")

if not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY is missing in environment variables."
    )

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 30


# =========================================================
# GAPGPT CONFIGURATION
# =========================================================

GAPGPT_API_KEY = os.getenv("GAPGPT_API_KEY")

GAPGPT_BASE_URL = os.getenv(
    "GAPGPT_BASE_URL",
    "https://api.gapgpt.app/v1",
)

MODEL = os.getenv(
    "MODEL",
    "gpt-4o-mini",
)

PRO_MODEL = os.getenv(
    "PRO_MODEL",
    MODEL,
)

PRO_GAPGPT_API_KEY = os.getenv(
    "PRO_GAPGPT_API_KEY",
    GAPGPT_API_KEY,
)


if not GAPGPT_API_KEY:
    raise RuntimeError(
        "GAPGPT_API_KEY is missing in environment variables."
    )


# =========================================================
# AI CLIENTS
# =========================================================

standard_llm = OpenAI(
    model=MODEL,
    api_key=GAPGPT_API_KEY,
    api_base=GAPGPT_BASE_URL,
)

pro_llm = OpenAI(
    model=PRO_MODEL,
    api_key=PRO_GAPGPT_API_KEY,
    api_base=GAPGPT_BASE_URL,
)


# =========================================================
# SYSTEM PROMPT
# =========================================================

SYSTEM_PROMPT = f"""
تو {SHADOW_AI_NAME} هستی؛ یک دستیار هوش مصنوعی با هویت اختصاصی.

اطلاعات هویتی:

نام:
{SHADOW_AI_NAME}

سازنده:
{SHADOW_AI_CREATOR}

توسعه‌دهنده:
{SHADOW_AI_DEVELOPER}

نسخه:
{SHADOW_AI_VERSION}

توضیح:
{SHADOW_AI_DESCRIPTION}

قابلیت‌های اصلی:

- پاسخ‌گویی هوشمند
- آموزش و یادگیری
- برنامه‌نویسی
- رفع خطای برنامه‌نویسی
- حل مسئله
- تحلیل اطلاعات
- تولید محتوا
- ویرایش متن
- ترجمه
- کمک در پروژه‌های فنی
- گفتگوی هوشمند

قوانین هویت:

1. نام تو {SHADOW_AI_NAME} است.

2. اگر کاربر پرسید «تو کی هستی؟»، «اسمت چیست؟»،
«چه هوش مصنوعی‌ای هستی؟» یا سؤال مشابه،
خودت را {SHADOW_AI_NAME} معرفی کن.

3. در شرایط عادی خودت را ChatGPT یا OpenAI معرفی نکن.

4. اگر کاربر به‌صورت مستقیم درباره مدل پایه،
سرویس ارائه‌دهنده یا زیرساخت فنی پرسید،
درباره آن صادق باش و چیزی را که نمی‌دانی جعل نکن.

5. اگر کاربر درباره سازنده یا توسعه‌دهنده Shadow.Ai پرسید،
بر اساس اطلاعات هویتی تعریف‌شده بالا پاسخ بده.

قوانین پاسخ:

6. اگر کاربر فارسی صحبت می‌کند، فارسی پاسخ بده.

7. اگر کاربر انگلیسی صحبت می‌کند، انگلیسی پاسخ بده.

8. پاسخ‌ها باید واضح، دقیق، طبیعی و کاربردی باشند.

9. اگر پاسخ را نمی‌دانی، حدس نزن.

10. در مسائل آموزشی مرحله‌به‌مرحله توضیح بده.

11. در مسائل برنامه‌نویسی کد قابل اجرا و توضیح مناسب ارائه بده.

12. API Key، رمز عبور، توکن، Environment Variable
و اطلاعات محرمانه سیستم را افشا نکن.

13. هیچ‌گاه از کاربر API Key درخواست نکن.

14. هدف اصلی {SHADOW_AI_NAME} کمک، آموزش،
حل مسئله و ارائه اطلاعات مفید است.
"""


# =========================================================
# REQUEST MODELS
# =========================================================

class ChatHistoryItem(BaseModel):
    role: str = Field(
        ...,
        pattern="^(user|assistant)$",
    )

    content: str = Field(
        ...,
        min_length=1,
        max_length=10_000,
    )


class ChatRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=12_000,
    )

    history: list[ChatHistoryItem] = Field(
        default_factory=list,
        max_length=20,
    )


class RegisterRequest(BaseModel):
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
    )

    email: EmailStr

    password: str = Field(
        ...,
        min_length=8,
        max_length=200,
    )


class LoginRequest(BaseModel):
    username: str = Field(
        ...,
        min_length=1,
        max_length=50,
    )

    password: str = Field(
        ...,
        min_length=1,
        max_length=200,
    )


# =========================================================
# PASSWORD HELPERS
# =========================================================

def hash_password(password: str) -> str:

    password_bytes = password.encode("utf-8")

    # bcrypt حداکثر 72 بایت را پشتیبانی می‌کند.
    if len(password_bytes) > 72:
        raise HTTPException(
            status_code=400,
            detail="رمز عبور بیش از حد مجاز است.",
        )

    salt = bcrypt.gensalt()

    hashed = bcrypt.hashpw(
        password_bytes,
        salt,
    )

    return hashed.decode("utf-8")


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:

    try:

        password_bytes = plain_password.encode(
            "utf-8"
        )

        if len(password_bytes) > 72:
            return False

        return bcrypt.checkpw(
            password_bytes,
            hashed_password.encode("utf-8"),
        )

    except (
        ValueError,
        TypeError,
    ):
        return False


# =========================================================
# JWT HELPERS
# =========================================================

def create_access_token(
    user_id: int,
    username: str,
    plan: str,
) -> str:

    expires_at = (
        datetime.now(timezone.utc)
        + timedelta(
            days=ACCESS_TOKEN_EXPIRE_DAYS
        )
    )

    payload = {
        "sub": str(user_id),
        "username": username,
        "plan": plan,
        "exp": expires_at,
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


def decode_access_token(
    token: str,
) -> dict:

    try:

        return jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )

    except JWTError as exc:

        raise HTTPException(
            status_code=401,
            detail="توکن نامعتبر یا منقضی شده است.",
        ) from exc


# =========================================================
# DATABASE USER HELPERS
# =========================================================

def get_current_user(
    authorization: str | None,
):

    if not authorization:

        raise HTTPException(
            status_code=401,
            detail=(
                "برای استفاده از Shadow.Ai "
                "ابتدا وارد حساب خود شوید."
            ),
        )

    if not authorization.startswith(
        "Bearer "
    ):

        raise HTTPException(
            status_code=401,
            detail="فرمت توکن نامعتبر است.",
        )

    token = authorization[7:].strip()

    if not token:

        raise HTTPException(
            status_code=401,
            detail="توکن ارسال نشده است.",
        )

    payload = decode_access_token(
        token
    )

    user_id = payload.get("sub")

    if not user_id:

        raise HTTPException(
            status_code=401,
            detail=(
                "شناسه کاربر در توکن وجود ندارد."
            ),
        )

    try:

        user_id = int(user_id)

    except ValueError as exc:

        raise HTTPException(
            status_code=401,
            detail="شناسه کاربر نامعتبر است.",
        ) from exc

    connection = get_connection()

    try:

        user = connection.execute(
            """
            SELECT *
            FROM users
            WHERE id = ?
            """,
            (user_id,),
        ).fetchone()

    finally:

        connection.close()

    if not user:

        raise HTTPException(
            status_code=401,
            detail="کاربر پیدا نشد.",
        )

    return user


# =========================================================
# SUBSCRIPTION HELPERS
# =========================================================

def subscription_is_active(
    user,
) -> bool:

    if user["plan"] == FREE_PLAN:
        return True

    end = user["subscription_end"]

    if not end:
        return False

    try:

        expires_at = datetime.fromisoformat(
            end
        )

        if expires_at.tzinfo is None:

            expires_at = (
                expires_at.replace(
                    tzinfo=timezone.utc
                )
            )

        return (
            datetime.now(timezone.utc)
            < expires_at
        )

    except ValueError:

        return False


def get_effective_plan(
    user,
) -> str:

    if user["plan"] == FREE_PLAN:
        return FREE_PLAN

    if subscription_is_active(user):
        return user["plan"]

    return FREE_PLAN


def get_plan_limit(
    plan: str,
):

    if plan == FREE_PLAN:
        return FREE_MESSAGE_LIMIT

    if plan == STANDARD_PLAN:
        return STANDARD_MESSAGE_LIMIT

    if plan == PRO_PLAN:
        return PRO_MESSAGE_LIMIT

    return FREE_MESSAGE_LIMIT


def get_llm(
    plan: str,
):

    if plan == PRO_PLAN:
        return pro_llm

    return standard_llm


def get_plan_name(
    plan: str,
) -> str:

    names = {
        FREE_PLAN: "رایگان",
        STANDARD_PLAN: "معمولی",
        PRO_PLAN: "Pro",
    }

    return names.get(
        plan,
        "رایگان",
    )


# =========================================================
# PROMPT BUILDER
# =========================================================

def build_prompt(
    message: str,
    history: list[ChatHistoryItem],
    plan: str,
) -> str:

    prompt_parts = [
        SYSTEM_PROMPT,
        "",
        f"پلن فعلی کاربر: {plan}",
        "",
    ]

    if history:

        prompt_parts.append(
            "سابقه اخیر همین گفتگو:"
        )

        for item in history[-20:]:

            role_name = (
                "کاربر"
                if item.role == "user"
                else "Shadow.Ai"
            )

            prompt_parts.append(
                f"{role_name}: {item.content}"
            )

        prompt_parts.append("")

    prompt_parts.append(
        "پیام جدید کاربر:"
    )

    prompt_parts.append(
        message
    )

    prompt_parts.append("")

    prompt_parts.append(
        "پاسخ Shadow.Ai:"
    )

    return "\n".join(
        prompt_parts
    )


# =========================================================
# PLAN DETAILS
# =========================================================

PLAN_DETAILS = {

    FREE_PLAN: {
        "id": FREE_PLAN,
        "name": "رایگان",
        "price_toman": 0,
        "duration_days": None,
        "message_limit": FREE_MESSAGE_LIMIT,
        "model": MODEL,
    },

    STANDARD_PLAN: {
        "id": STANDARD_PLAN,
        "name": "معمولی",
        "price_toman": STANDARD_PRICE_TOMAN,
        "duration_days": SUBSCRIPTION_DAYS,
        "message_limit": "unlimited",
        "model": MODEL,
    },

    PRO_PLAN: {
        "id": PRO_PLAN,
        "name": "Pro",
        "price_toman": PRO_PRICE_TOMAN,
        "duration_days": SUBSCRIPTION_DAYS,
        "message_limit": "unlimited",
        "model": PRO_MODEL,
    },

}


# =========================================================
# ROOT
# =========================================================

@app.get("/")
def root():

    if not FRONTEND_FILE.exists():

        raise HTTPException(
            status_code=404,
            detail="Frontend file not found.",
        )

    return FileResponse(
        FRONTEND_FILE
    )


# =========================================================
# STATUS
# =========================================================

@app.get("/api/status")
def status():

    return {
        "name": SHADOW_AI_NAME,
        "status": "online",
        "version": SHADOW_AI_VERSION,
        "model": MODEL,
        "timestamp": datetime.now(
            timezone.utc
        ).isoformat(),
    }


# =========================================================
# SHADOW.AI INFORMATION
# =========================================================

@app.get("/api/info")
def shadow_info():

    return {
        "name": SHADOW_AI_NAME,
        "version": SHADOW_AI_VERSION,
        "creator": SHADOW_AI_CREATOR,
        "developer": SHADOW_AI_DEVELOPER,
        "description": SHADOW_AI_DESCRIPTION,
        "capabilities": SHADOW_AI_CAPABILITIES,
        "plans": PLAN_DETAILS,
    }


# =========================================================
# PLANS
# =========================================================

@app.get("/api/plans")
def plans():

    return {
        "plans": PLAN_DETAILS
    }


# =========================================================
# REGISTER
# =========================================================

@app.post("/register")
def register(
    request: RegisterRequest,
):

    username = request.username.strip()
    email = str(request.email).strip().lower()
    password = request.password

    password_bytes = password.encode(
        "utf-8"
    )

    if len(password_bytes) > 72:

        raise HTTPException(
            status_code=400,
            detail="رمز عبور بیش از 72 بایت است.",
        )

    connection = get_connection()

    try:

        existing_user = connection.execute(
            """
            SELECT id
            FROM users
            WHERE username = ?
               OR email = ?
            """,
            (
                username,
                email,
            ),
        ).fetchone()

        if existing_user:

            raise HTTPException(
                status_code=400,
                detail=(
                    "نام کاربری یا ایمیل "
                    "قبلاً ثبت شده است."
                ),
            )

        password_hash = hash_password(
            password
        )

        cursor = connection.execute(
            """
            INSERT INTO users (
                username,
                email,
                password_hash,
                plan,
                message_count,
                subscription_start,
                subscription_end
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                username,
                email,
                password_hash,
                FREE_PLAN,
                0,
                None,
                None,
            ),
        )

        user_id = cursor.lastrowid

        connection.commit()

    finally:

        connection.close()

    token = create_access_token(
        user_id=user_id,
        username=username,
        plan=FREE_PLAN,
    )

    return {
        "message": "ثبت‌نام با موفقیت انجام شد.",
        "access_token": token,
        "token_type": "bearer",
        "username": username,
        "plan": FREE_PLAN,
        "message_count": 0,
        "remaining_messages": FREE_MESSAGE_LIMIT,
    }


# =========================================================
# LOGIN
# =========================================================

@app.post("/login")
def login(
    request: LoginRequest,
):

    username = request.username.strip()

    connection = get_connection()

    try:

        user = connection.execute(
            """
            SELECT *
            FROM users
            WHERE username = ?
            """,
            (username,),
        ).fetchone()

    finally:

        connection.close()

    if not user:

        raise HTTPException(
            status_code=401,
            detail=(
                "نام کاربری یا رمز عبور اشتباه است."
            ),
        )

    if not verify_password(
        request.password,
        user["password_hash"],
    ):

        raise HTTPException(
            status_code=401,
            detail=(
                "نام کاربری یا رمز عبور اشتباه است."
            ),
        )

    plan = get_effective_plan(
        user
    )

    limit = get_plan_limit(
        plan
    )

    remaining = None

    if limit is not None:

        remaining = max(
            limit - user["message_count"],
            0,
        )

    token = create_access_token(
        user_id=user["id"],
        username=user["username"],
        plan=plan,
    )

    return {
        "message": "ورود با موفقیت انجام شد.",
        "access_token": token,
        "token_type": "bearer",
        "username": user["username"],
        "plan": plan,
        "message_count": user["message_count"],
        "remaining_messages": remaining,
        "subscription_end": user["subscription_end"],
    }


# =========================================================
# CURRENT USER
# =========================================================

@app.get("/me")
def me(
    authorization: str | None = Header(
        default=None
    ),
):

    user = get_current_user(
        authorization
    )

    plan = get_effective_plan(
        user
    )

    limit = get_plan_limit(
        plan
    )

    remaining = None

    if limit is not None:

        remaining = max(
            limit - user["message_count"],
            0,
        )

    return {
        "id": user["id"],
        "username": user["username"],
        "email": user["email"],
        "plan": plan,
        "plan_name": get_plan_name(plan),
        "message_count": user["message_count"],
        "remaining_messages": remaining,
        "subscription_start": user[
            "subscription_start"
        ],
        "subscription_end": user[
            "subscription_end"
        ],
        "created_at": user["created_at"],
    }


# =========================================================
# SUBSCRIPTION
# =========================================================

@app.get("/subscription")
def subscription(
    authorization: str | None = Header(
        default=None
    ),
):

    user = get_current_user(
        authorization
    )

    plan = get_effective_plan(
        user
    )

    details = PLAN_DETAILS[
        plan
    ]

    limit = details[
        "message_limit"
    ]

    remaining = None

    if limit != "unlimited":

        remaining = max(
            limit - user["message_count"],
            0,
        )

    return {
        "plan": plan,
        "plan_name": details["name"],
        "price_toman": details[
            "price_toman"
        ],
        "duration_days": details[
            "duration_days"
        ],
        "model": details[
            "model"
        ],
        "subscription_start": user[
            "subscription_start"
        ],
        "subscription_end": user[
            "subscription_end"
        ],
        "message_count": user[
            "message_count"
        ],
        "remaining_messages": remaining,
    }


# =========================================================
# CHAT
# =========================================================

@app.post("/chat")
def chat(
    request: ChatRequest,
    authorization: str | None = Header(
        default=None
    ),
):

    request_id = str(
        uuid.uuid4()
    )

    started_at = time.perf_counter()

    user = get_current_user(
        authorization
    )

    message = request.message.strip()

    if not message:

        raise HTTPException(
            status_code=400,
            detail="پیام نمی‌تواند خالی باشد.",
        )

    # -----------------------------------------
    # Active plan
    # -----------------------------------------

    plan = get_effective_plan(
        user
    )

    # -----------------------------------------
    # Expired subscription
    # -----------------------------------------

    if (
        user["plan"] != FREE_PLAN
        and not subscription_is_active(user)
    ):

        connection = get_connection()

        try:

            connection.execute(
                """
                UPDATE users
                SET plan = ?,
                    subscription_start = NULL,
                    subscription_end = NULL
                WHERE id = ?
                """,
                (
                    FREE_PLAN,
                    user["id"],
                ),
            )

            connection.commit()

        finally:

            connection.close()

        plan = FREE_PLAN

    # -----------------------------------------
    # Message quota
    # -----------------------------------------

    message_limit = get_plan_limit(
        plan
    )

    current_count = user[
        "message_count"
    ]

    if (
        message_limit is not None
        and current_count >= message_limit
    ):

        raise HTTPException(
            status_code=403,
            detail=(
                "سهمیه ۳۰ پیام رایگان شما "
                "تمام شده است. برای ادامه "
                "استفاده، اشتراک خود را ارتقا دهید."
            ),
        )

    # -----------------------------------------
    # Select model
    # -----------------------------------------

    selected_llm = get_llm(
        plan
    )

    # -----------------------------------------
    # Build prompt
    # -----------------------------------------

    prompt = build_prompt(
        message=message,
        history=request.history,
        plan=plan,
    )

    # -----------------------------------------
    # AI request
    # -----------------------------------------

    try:

        response = selected_llm.complete(
            prompt
        )

        answer = str(
            response
        ).strip()

        if not answer:

            raise HTTPException(
                status_code=502,
                detail=(
                    "هوش مصنوعی پاسخ خالی برگرداند."
                ),
            )

    except HTTPException:

        raise

    except Exception as exc:

        print(
            f"[{request_id}] "
            f"Shadow.Ai AI error: {exc}"
        )

        raise HTTPException(
            status_code=502,
            detail=(
                "در ارتباط با سرویس هوش مصنوعی "
                "خطایی رخ داد."
            ),
        ) from exc

    # -----------------------------------------
    # Increase message count
    # -----------------------------------------

    connection = get_connection()

    try:

        connection.execute(
            """
            UPDATE users
            SET message_count =
                message_count + 1
            WHERE id = ?
            """,
            (
                user["id"],
            ),
        )

        connection.commit()

        updated_user = connection.execute(
            """
            SELECT message_count
            FROM users
            WHERE id = ?
            """,
            (
                user["id"],
            ),
        ).fetchone()

    finally:

        connection.close()

    new_count = updated_user[
        "message_count"
    ]

    remaining = None

    if message_limit is not None:

        remaining = max(
            message_limit - new_count,
            0,
        )

    processing_time = round(
        time.perf_counter()
        - started_at,
        3,
    )

    return {
        "answer": answer,
        "request_id": request_id,
        "plan": plan,
        "plan_name": get_plan_name(
            plan
        ),
        "model": (
            PRO_MODEL
            if plan == PRO_PLAN
            else MODEL
        ),
        "message_count": new_count,
        "remaining_messages": remaining,
        "processing_time_seconds": processing_time,
    }