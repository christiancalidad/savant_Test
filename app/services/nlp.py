from typing import Optional

try:
    from langchain_openai import AzureChatOpenAI  # type: ignore
except Exception:  # pragma: no cover
    AzureChatOpenAI = None  # type: ignore

from app.config import settings

# Simple wrapper around LLM. In tests/offline, returns a canned reply.
async def generate_response(prompt: str, language: str) -> str:

    llm = AzureChatOpenAI(
        azure_deployment=settings.azure_openai_deployment,
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
        temperature=0.3,
    )

    # Minimal single-turn prompt
    sys_prompt = (
        "Eres un asistente útil. Responde brevemente en el idioma del usuario."
    )

    from langchain_core.messages import SystemMessage, HumanMessage

    messages = [SystemMessage(content=sys_prompt), HumanMessage(content=prompt)]
    result = await llm.ainvoke(messages)
    text: str = getattr(result, "content", "") or str(result)
    return text
