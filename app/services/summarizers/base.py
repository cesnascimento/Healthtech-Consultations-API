"""
Base protocol e tipos para summarizers.

Define a interface que todos os summarizers devem implementar,
permitindo substituição transparente entre estratégias.
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from app.models.consultation import ConsultationWarning, SummarySection

if TYPE_CHECKING:
    from app.models.consultation import ConsultationCreate


@dataclass
class SummarizerResult:
    """
    Resultado do processamento de um summarizer.

    Contém as seções geradas, texto completo e warnings coletados
    durante o processamento.

    Attributes:
        sections: Lista de seções estruturadas do resumo.
        full_text: Texto completo concatenado para visualização.
        warnings: Warnings gerados durante o processamento.
        strategy_used: Identificador da estratégia utilizada.
    """

    sections: list[SummarySection]
    full_text: str
    warnings: list[ConsultationWarning] = field(default_factory=list)
    strategy_used: str = "rule_based"


@runtime_checkable
class SummarizerProtocol(Protocol):
    """
    Protocolo que define a interface de um summarizer.

    Qualquer classe que implemente o método `summarize` com a
    assinatura correta é considerada um summarizer válido.

    Example:
        ```python
        class MySummarizer:
            def summarize(self, consultation: ConsultationCreate) -> SummarizerResult:
                # implementação
                ...

        # MySummarizer é automaticamente compatível com SummarizerProtocol
        summarizer: SummarizerProtocol = MySummarizer()
        ```
    """

    def summarize(self, consultation: "ConsultationCreate") -> SummarizerResult:
        """
        Processa uma consulta e gera um resumo estruturado.

        Args:
            consultation: Dados completos da consulta médica.

        Returns:
            SummarizerResult contendo seções, texto e warnings.
        """
        ...
