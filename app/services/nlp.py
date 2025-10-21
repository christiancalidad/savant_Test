from typing import Optional

try:
    from langchain_openai import AzureChatOpenAI  
except Exception:  
    AzureChatOpenAI = None 

from app.config import settings


async def generate_response(prompt: str) -> str:
    """
    Generate a brief, single-turn response to a user prompt using Azure OpenAI via LangChain.
    This asynchronous function initializes a LangChain AzureChatOpenAI client with
    configuration from `settings`, sends a minimal chat composed of a system instruction
    (in Spanish) and the user's prompt, and returns the model's textual reply. The system
    prompt instructs the assistant to answer any topic briefly and in the user's language.
    Args:
        prompt: The user's input message to be sent to the model.
    Returns:
        The assistant's reply text produced by Azure OpenAI.
    Notes:
    - Uses LangChain's AzureChatOpenAI with:
      - settings.azure_openai_deployment
      - settings.azure_openai_endpoint
      - settings.azure_openai_api_key
      - settings.azure_openai_api_version
    - Single-turn conversation: [SystemMessage, HumanMessage].
    Raises:
        Any exceptions from the underlying LangChain/Azure OpenAI client (e.g., configuration,
        authentication, or network errors) are propagated.
    Example:
        >>> reply = await generate_response("¿Cuál es la capital de Francia?")
        >>> reply
        'París.'
    """

    llm = AzureChatOpenAI(
        azure_deployment=settings.azure_openai_deployment,
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
        temperature=0.3,
    )

    # Minimal single-turn prompt
    sys_prompt = (
        "Eres un asistente que responde preguntas sobre cualquier tema. Responde brevemente en el idioma del usuario."
    )

    from langchain_core.messages import SystemMessage, HumanMessage

    messages = [SystemMessage(content=sys_prompt), HumanMessage(content=prompt)]
    result = await llm.ainvoke(messages)
    text: str = getattr(result, "content", "") or str(result)
    return text
