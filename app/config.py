from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS:int = 7
    LLM_PROVIDER: str = "ollama"

    OLLAMA_BASE_URL: str = "http://localhost:11434/v1"
    OLLAMA_MODEL: str = "qwen2.5"
    OLLAMA_EMBED_MODEL: str = "nomic-embed-text"

    FREE_API_BASE_URL: str = "https://api.groq.com/openai/v1"
    FREE_API_KEY: str = ""
    FREE_API_MODEL: str = "llama-3.1-8b-instant"

    EMBEDDING_DIM: int = 768
    DATABASE_URL_READONLY:str

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
