import os

from llama_index.core import Settings
from llama_index.llms.openai import OpenAI


def init_settings():
    api_key = os.getenv("GAPGPT_API_KEY")
    if not api_key:
        raise RuntimeError("GAPGPT_API_KEY is missing in environment variables")

    Settings.llm = OpenAI(
        model=os.getenv("MODEL", "gpt-4o-mini"),
        api_key=api_key,
        api_base=os.getenv(
            "GAPGPT_BASE_URL",
            "https://api.gapgpt.app/v1",
        ),
    )