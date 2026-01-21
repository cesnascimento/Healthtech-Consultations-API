from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configurações da aplicação.

    Todas as configurações podem ser sobrescritas via variáveis
    de ambiente. O prefixo HEALTHTECH_ é opcional.

    Example:
        ```bash
        export SUMMARIZER_STRATEGY=llm_based
        export GEMINI_API_KEY=your-key
        export LLM_TIMEOUT_SECONDS=15
        ```
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # === API ===
    APP_NAME: str = "Healthtech Consultations API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # === Summarizer ===
    SUMMARIZER_STRATEGY: Literal["rule_based", "llm_based"] = "rule_based"
    """
    Estratégia padrão para geração de resumos.

    - rule_based: Processamento determinístico (padrão)
    - llm_based: Processamento com IA (requer GEMINI_API_KEY)
    """

    # === LLM - Gemini ===
    GEMINI_API_KEY: str | None = None
    GEMINI_MODEL: str = "gemini-1.5-flash"

    # === LLM - OpenAI ===
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-4o-mini"

    # === LLM - Configurações Gerais ===
    LLM_TIMEOUT_SECONDS: int = 10
    LLM_MAX_RETRIES: int = 2

    # === Limites ===
    MAX_MEDICATIONS: int = 50
    MAX_ALLERGIES: int = 30

    # === CORS ===
    CORS_ORIGINS: list[str] = ["*"]

    @property
    def is_llm_enabled(self) -> bool:
        return self.SUMMARIZER_STRATEGY == "llm_based" and bool(
            self.GEMINI_API_KEY or self.OPENAI_API_KEY
        )

    @property
    def llm_provider(self) -> str | None:
        if self.GEMINI_API_KEY:
            return "gemini"
        if self.OPENAI_API_KEY:
            return "openai"
        return None


@lru_cache
def get_settings() -> Settings:
    """
    Obtém instância singleton das configurações.

    Utiliza cache para evitar múltiplas leituras do .env.

    Returns:
        Instância de Settings.
    """
    return Settings()
