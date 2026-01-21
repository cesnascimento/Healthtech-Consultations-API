"""
Factory para criação de summarizers.

Centraliza a lógica de instanciação de summarizers com base
na configuração e parâmetros da requisição.
"""

from app.core.config import get_settings
from app.models.common import SummarizerStrategy
from app.services.summarizers.base import SummarizerProtocol
from app.services.summarizers.rule_based import RuleBasedSummarizer


def get_summarizer(
    strategy: SummarizerStrategy | None = None,
) -> SummarizerProtocol:
    """
    Obtém instância do summarizer apropriado.

    A estratégia é determinada pela seguinte prioridade:
    1. Parâmetro `strategy` (se fornecido)
    2. Configuração `SUMMARIZER_STRATEGY` do ambiente

    Se a estratégia solicitada for `llm_based` mas o LLM não estiver
    configurado, retorna `rule_based` silenciosamente.

    Args:
        strategy: Estratégia desejada (opcional).

    Returns:
        Instância de SummarizerProtocol.

    Example:
        ```python
        # Usa configuração padrão
        summarizer = get_summarizer()

        # Força estratégia específica
        summarizer = get_summarizer(SummarizerStrategy.RULE_BASED)
        ```
    """
    settings = get_settings()

    effective_strategy = strategy or SummarizerStrategy(settings.SUMMARIZER_STRATEGY)

    if effective_strategy == SummarizerStrategy.RULE_BASED:
        return RuleBasedSummarizer()

    if effective_strategy == SummarizerStrategy.LLM_BASED:
        if not settings.is_llm_enabled:
            return RuleBasedSummarizer()


        try:
            from app.services.summarizers.llm_based import LLMBasedSummarizer

            fallback = RuleBasedSummarizer()
            return LLMBasedSummarizer(fallback=fallback)
        except ImportError:
            return RuleBasedSummarizer()

    return RuleBasedSummarizer()


def get_rule_based_summarizer() -> RuleBasedSummarizer:
    """
    Obtém instância do summarizer rule-based diretamente.

    Útil quando se quer garantir que apenas rule_based será usado,
    independente da configuração.

    Returns:
        Instância de RuleBasedSummarizer.
    """
    return RuleBasedSummarizer()
