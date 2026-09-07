"""
Free hosted API LLM provider (e.g. Groq, OpenRouter -- any
OpenAI-compatible endpoint). Swap FREE_API_BASE_URL / MODEL / KEY in
.env to change providers without touching this class.
"""
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.llm.base import LLMProvider


class FreeAPIProvider(LLMProvider):
    def __init__(self):
        self.client = AsyncOpenAI(base_url=settings.FREE_API_BASE_URL, api_key=settings.FREE_API_KEY)
        self.model = settings.FREE_API_MODEL

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
    async def generate(self, prompt: str, system: str | None = None) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.2,
        )
        return response.choices[0].message.content or ""

    async def embed(self, text: str) -> list[float]:
        raise NotImplementedError(
            
        )