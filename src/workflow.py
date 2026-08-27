from dotenv import load_dotenv

from llama_index.core.agent.workflow import AgentWorkflow
from llama_index.core.settings import Settings

from src.settings import init_settings


def create_workflow() -> AgentWorkflow:
    load_dotenv()
    init_settings()

    system_prompt = """
You are Edunova AI, a helpful Persian-speaking AI assistant.

Rules:
- Answer the user's question clearly and accurately.
- Prefer Persian when the user speaks Persian.
- Explain difficult topics simply.
- Do not claim to know something you are unsure about.
- Keep answers organized and useful.
"""

    return AgentWorkflow.from_tools_or_functions(
        tools_or_functions=[],
        llm=Settings.llm,
        system_prompt=system_prompt,
    )


workflow = create_workflow()