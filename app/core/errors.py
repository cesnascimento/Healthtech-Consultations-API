"""
Exceções customizadas e tratamento de erros.

Define exceções específicas da aplicação e handlers
para formatação consistente de respostas de erro.
"""

from typing import Any


class HealthtechError(Exception):
    """
    Exceção base para erros da aplicação.

    Todas as exceções customizadas devem herdar desta classe.
    """

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        """
        Inicializa a exceção.

        Args:
            message: Mensagem de erro legível.
            code: Código do erro para identificação programática.
            details: Detalhes adicionais (opcional).
        """
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}


class ValidationError(HealthtechError):
    """Erro de validação de dados."""

    def __init__(
        self,
        message: str,
        field: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            details={"field": field, **(details or {})},
        )
        self.field = field


class SummarizerError(HealthtechError):
    """Erro durante processamento do summarizer."""

    def __init__(
        self,
        message: str,
        strategy: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code="SUMMARIZER_ERROR",
            details={"strategy": strategy, **(details or {})},
        )
        self.strategy = strategy


class LLMError(HealthtechError):
    """Erro específico de integração com LLM."""

    def __init__(
        self,
        message: str,
        model: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code="LLM_ERROR",
            details={"model": model, **(details or {})},
        )
        self.model = model


class ConfigurationError(HealthtechError):
    """Erro de configuração da aplicação."""

    def __init__(
        self,
        message: str,
        setting: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code="CONFIGURATION_ERROR",
            details={"setting": setting, **(details or {})},
        )
        self.setting = setting
