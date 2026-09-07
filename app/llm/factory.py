from functools import lru_cache

from app.config import settings
from app.llm.base import LLMProvider
from app.llm.api_provider import FreeAPIProvider
from app.llm.ollama_provider import OllamaProvider


@lru_cache
def get_llm_provider() -> LLMProvider:
    if settings.LLM_PROVIDER == "free_api":
        return FreeAPIProvider()
    return OllamaProvider()


@lru_cache
def get_embedding_provider() -> LLMProvider:
    return OllamaProvider()