"""
Utilitários para geração de metadados de auditoria.

Fornece funções para criação de identificadores únicos,
timestamps e metadados de rastreabilidade.
"""

import time
from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.core.constants import RULE_ENGINE_VERSION
from app.models.common import SummarizerStrategy
from app.models.consultation import SummaryMetadata


class AuditGenerator:
    """
    Gerador de metadados de auditoria para consultas.

    Centraliza a criação de IDs, timestamps e metadados
    de rastreabilidade do processamento.
    """

    @staticmethod
    def generate_request_id() -> UUID:
        """
        Gera um identificador único para a requisição.

        Returns:
            UUID v4 único.
        """
        return uuid4()

    @staticmethod
    def get_timestamp() -> datetime:
        """
        Obtém timestamp UTC atual.

        Returns:
            Datetime UTC com timezone.
        """
        return datetime.now(UTC)

    @staticmethod
    def create_metadata(
        request_id: UUID,
        strategy_requested: SummarizerStrategy | None,
        strategy_used: str,
        processing_start_ns: int,
        llm_model: str | None = None,
        fallback_reason: str | None = None,
    ) -> SummaryMetadata:
        """
        Cria objeto de metadados completo para a resposta.

        Args:
            request_id: ID único da requisição.
            strategy_requested: Estratégia solicitada pelo cliente.
            strategy_used: Estratégia efetivamente utilizada.
            processing_start_ns: Timestamp de início em nanosegundos.
            llm_model: Modelo LLM utilizado (se aplicável).
            fallback_reason: Motivo do fallback (se aplicável).

        Returns:
            SummaryMetadata preenchido.
        """
        processing_time_ms = (time.perf_counter_ns() - processing_start_ns) // 1_000_000

        return SummaryMetadata(
            request_id=request_id,
            strategy_used=strategy_used,
            strategy_requested=strategy_requested,
            rule_engine_version=RULE_ENGINE_VERSION,
            processed_at=AuditGenerator.get_timestamp(),
            processing_time_ms=processing_time_ms,
            llm_model=llm_model,
            fallback_reason=fallback_reason,
        )

    @staticmethod
    def start_timer() -> int:
        """
        Inicia um timer de alta precisão.

        Returns:
            Timestamp em nanosegundos.
        """
        return time.perf_counter_ns()
