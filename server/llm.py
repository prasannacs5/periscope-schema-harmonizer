"""Foundation Model API client via OpenAI-compatible endpoint."""
from openai import AsyncOpenAI
from server.config import get_oauth_token, get_workspace_host, LLM_MODEL


def get_llm_client() -> AsyncOpenAI:
    token = get_oauth_token()
    host = get_workspace_host()
    return AsyncOpenAI(
        api_key=token,
        base_url=f"{host}/serving-endpoints",
    )


async def chat(messages: list[dict], model: str = LLM_MODEL, **kwargs) -> str:
    client = get_llm_client()
    response = await client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=kwargs.get("max_tokens", 4096),
        temperature=kwargs.get("temperature", 0.1),
    )
    return response.choices[0].message.content
