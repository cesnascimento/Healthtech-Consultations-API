"""
Testes para os utilitários.

Verifica funções auxiliares de texto e auditoria.
"""

import time
from datetime import UTC, datetime
from uuid import UUID

import pytest

from app.models.common import SummarizerStrategy
from app.utils.audit import AuditGenerator
from app.utils.text import TextProcessor


class TestTextProcessorTruncate:
    """Testes para TextProcessor.truncate()."""

    def test_no_truncation_needed(self) -> None:
        """Texto curto não deve ser truncado."""
        result, was_truncated = TextProcessor.truncate("Hello", 10)

        assert result == "Hello"
        assert was_truncated is False

    def test_exact_length_no_truncation(self) -> None:
        """Texto exato no limite não deve ser truncado."""
        result, was_truncated = TextProcessor.truncate("Hello", 5)

        assert result == "Hello"
        assert was_truncated is False

    def test_truncation_with_default_suffix(self) -> None:
        """Texto longo deve ser truncado com '...'."""
        result, was_truncated = TextProcessor.truncate("Hello World", 8)

        assert result == "Hello..."
        assert was_truncated is True
        assert len(result) == 8

    def test_truncation_with_custom_suffix(self) -> None:
        """Deve usar sufixo customizado."""
        result, was_truncated = TextProcessor.truncate(
            "Hello World", 10, suffix="[...]"
        )

        assert result.endswith("[...]")
        assert was_truncated is True

    def test_none_input_returns_empty(self) -> None:
        """None deve retornar string vazia."""
        result, was_truncated = TextProcessor.truncate(None, 10)

        assert result == ""
        assert was_truncated is False

    def test_empty_string_returns_empty(self) -> None:
        """String vazia deve retornar vazia."""
        result, was_truncated = TextProcessor.truncate("", 10)

        assert result == ""
        assert was_truncated is False

    def test_whitespace_stripped(self) -> None:
        """Espaços devem ser removidos das pontas."""
        result, was_truncated = TextProcessor.truncate("  Hello  ", 10)

        assert result == "Hello"
        assert was_truncated is False


class TestTextProcessorNormalizeWhitespace:
    """Testes para TextProcessor.normalize_whitespace()."""

    def test_multiple_spaces(self) -> None:
        """Múltiplos espaços devem virar um só."""
        result = TextProcessor.normalize_whitespace("Hello    World")
        assert result == "Hello World"

    def test_tabs_to_spaces(self) -> None:
        """Tabs devem virar espaços."""
        result = TextProcessor.normalize_whitespace("Hello\tWorld")
        assert result == "Hello World"

    def test_multiple_newlines(self) -> None:
        """Múltiplas quebras devem virar no máximo 2."""
        result = TextProcessor.normalize_whitespace("Hello\n\n\n\nWorld")
        assert result == "Hello\n\nWorld"

    def test_none_returns_empty(self) -> None:
        """None deve retornar string vazia."""
        result = TextProcessor.normalize_whitespace(None)
        assert result == ""

    def test_strips_edges(self) -> None:
        """Espaços nas pontas devem ser removidos."""
        result = TextProcessor.normalize_whitespace("  Hello World  ")
        assert result == "Hello World"


class TestTextProcessorRemoveDuplicates:
    """Testes para TextProcessor.remove_duplicates()."""

    def test_removes_exact_duplicates(self) -> None:
        """Deve remover duplicatas exatas."""
        unique, removed = TextProcessor.remove_duplicates(["a", "b", "a", "c"])

        assert unique == ["a", "b", "c"]
        assert removed == ["a"]

    def test_case_insensitive(self) -> None:
        """Deve ser case-insensitive."""
        unique, removed = TextProcessor.remove_duplicates(["Hello", "HELLO", "World"])

        assert unique == ["Hello", "World"]
        assert removed == ["HELLO"]

    def test_preserves_order(self) -> None:
        """Deve preservar ordem de aparição."""
        unique, removed = TextProcessor.remove_duplicates(["c", "b", "a", "b"])

        assert unique == ["c", "b", "a"]

    def test_strips_items(self) -> None:
        """Deve fazer strip dos itens."""
        unique, removed = TextProcessor.remove_duplicates(["  hello  ", "hello"])

        assert unique == ["hello"]
        assert removed == ["hello"]

    def test_empty_list(self) -> None:
        """Lista vazia deve retornar vazia."""
        unique, removed = TextProcessor.remove_duplicates([])

        assert unique == []
        assert removed == []

    def test_ignores_empty_items(self) -> None:
        """Itens vazios devem ser ignorados."""
        unique, removed = TextProcessor.remove_duplicates(["a", "", "  ", "b"])

        assert unique == ["a", "b"]


class TestTextProcessorFormatDateBr:
    """Testes para TextProcessor.format_date_br()."""

    def test_converts_iso_to_br(self) -> None:
        """Deve converter ISO para formato BR."""
        result = TextProcessor.format_date_br("1985-03-15")
        assert result == "15/03/1985"

    def test_handles_invalid_date(self) -> None:
        """Data inválida deve retornar string original."""
        result = TextProcessor.format_date_br("invalid")
        assert result == "invalid"


class TestTextProcessorCalculateAge:
    """Testes para TextProcessor.calculate_age()."""

    def test_calculates_correct_age(self) -> None:
        """Deve calcular idade corretamente."""
        # Pessoa nascida há ~39 anos
        age = TextProcessor.calculate_age("1985-03-15")

        # Dependendo da data atual, será 38 ou 39
        assert age is not None
        assert 38 <= age <= 40

    def test_handles_invalid_date(self) -> None:
        """Data inválida deve retornar None."""
        age = TextProcessor.calculate_age("invalid")
        assert age is None


class TestTextProcessorMaskCpf:
    """Testes para TextProcessor.mask_cpf()."""

    def test_masks_cpf(self) -> None:
        """Deve mascarar primeiros dígitos do CPF."""
        result = TextProcessor.mask_cpf("123.456.789-00")
        assert result == "***.***.789-00"

    def test_short_cpf_returns_original(self) -> None:
        """CPF curto demais deve retornar original."""
        result = TextProcessor.mask_cpf("123")
        assert result == "123"

    def test_none_returns_empty(self) -> None:
        """None deve retornar string vazia."""
        result = TextProcessor.mask_cpf(None)  # type: ignore
        assert result == ""


class TestTextProcessorFormatVitalSign:
    """Testes para TextProcessor.format_vital_sign()."""

    def test_formats_with_label(self) -> None:
        """Deve formatar com label."""
        result = TextProcessor.format_vital_sign(120, "mmHg", "PAS")
        assert result == "PAS: 120 mmHg"

    def test_formats_without_label(self) -> None:
        """Deve formatar sem label."""
        result = TextProcessor.format_vital_sign(120, "mmHg")
        assert result == "120 mmHg"

    def test_none_value_returns_none(self) -> None:
        """Valor None deve retornar None."""
        result = TextProcessor.format_vital_sign(None, "mmHg")
        assert result is None

    def test_formats_float(self) -> None:
        """Deve formatar float."""
        result = TextProcessor.format_vital_sign(36.5, "°C", "Tax")
        assert result == "Tax: 36.5 °C"


class TestTextProcessorGetLimit:
    """Testes para TextProcessor.get_limit()."""

    def test_returns_defined_limit(self) -> None:
        """Deve retornar limite definido."""
        limit = TextProcessor.get_limit("history_present_illness")
        assert limit == 2000

    def test_returns_default_for_unknown(self) -> None:
        """Deve retornar padrão para campo desconhecido."""
        limit = TextProcessor.get_limit("unknown_field")
        assert limit == 2000


class TestAuditGeneratorRequestId:
    """Testes para AuditGenerator.generate_request_id()."""

    def test_returns_uuid(self) -> None:
        """Deve retornar UUID válido."""
        request_id = AuditGenerator.generate_request_id()

        assert isinstance(request_id, UUID)

    def test_unique_ids(self) -> None:
        """IDs devem ser únicos."""
        ids = [AuditGenerator.generate_request_id() for _ in range(100)]

        # Todos devem ser diferentes
        assert len(set(ids)) == 100


class TestAuditGeneratorTimestamp:
    """Testes para AuditGenerator.get_timestamp()."""

    def test_returns_utc_datetime(self) -> None:
        """Deve retornar datetime UTC."""
        ts = AuditGenerator.get_timestamp()

        assert isinstance(ts, datetime)
        assert ts.tzinfo == UTC

    def test_timestamp_is_current(self) -> None:
        """Timestamp deve ser aproximadamente atual."""
        before = datetime.now(UTC)
        ts = AuditGenerator.get_timestamp()
        after = datetime.now(UTC)

        assert before <= ts <= after


class TestAuditGeneratorStartTimer:
    """Testes para AuditGenerator.start_timer()."""

    def test_returns_int(self) -> None:
        """Deve retornar inteiro."""
        timer = AuditGenerator.start_timer()
        assert isinstance(timer, int)

    def test_timer_increases(self) -> None:
        """Timer deve aumentar com o tempo."""
        t1 = AuditGenerator.start_timer()
        time.sleep(0.001)  # 1ms
        t2 = AuditGenerator.start_timer()

        assert t2 > t1


class TestAuditGeneratorCreateMetadata:
    """Testes para AuditGenerator.create_metadata()."""

    def test_creates_metadata(self) -> None:
        """Deve criar metadados completos."""
        request_id = AuditGenerator.generate_request_id()
        start = AuditGenerator.start_timer()

        metadata = AuditGenerator.create_metadata(
            request_id=request_id,
            strategy_requested=SummarizerStrategy.RULE_BASED,
            strategy_used="rule_based",
            processing_start_ns=start,
        )

        assert metadata.request_id == request_id
        assert metadata.strategy_requested == SummarizerStrategy.RULE_BASED
        assert metadata.strategy_used == "rule_based"
        assert metadata.processing_time_ms >= 0
        assert metadata.llm_model is None
        assert metadata.fallback_reason is None

    def test_includes_llm_model(self) -> None:
        """Deve incluir modelo LLM quando fornecido."""
        request_id = AuditGenerator.generate_request_id()
        start = AuditGenerator.start_timer()

        metadata = AuditGenerator.create_metadata(
            request_id=request_id,
            strategy_requested=SummarizerStrategy.LLM_BASED,
            strategy_used="llm_based",
            processing_start_ns=start,
            llm_model="gemini-1.5-flash",
        )

        assert metadata.llm_model == "gemini-1.5-flash"

    def test_includes_fallback_reason(self) -> None:
        """Deve incluir motivo de fallback quando fornecido."""
        request_id = AuditGenerator.generate_request_id()
        start = AuditGenerator.start_timer()

        metadata = AuditGenerator.create_metadata(
            request_id=request_id,
            strategy_requested=SummarizerStrategy.LLM_BASED,
            strategy_used="llm_fallback",
            processing_start_ns=start,
            fallback_reason="Timeout after 10s",
        )

        assert metadata.strategy_used == "llm_fallback"
        assert metadata.fallback_reason == "Timeout after 10s"

    def test_calculates_processing_time(self) -> None:
        """Deve calcular tempo de processamento."""
        request_id = AuditGenerator.generate_request_id()
        start = AuditGenerator.start_timer()

        # Simula processamento
        time.sleep(0.01)  # 10ms

        metadata = AuditGenerator.create_metadata(
            request_id=request_id,
            strategy_requested=SummarizerStrategy.RULE_BASED,
            strategy_used="rule_based",
            processing_start_ns=start,
        )

        # Deve ser pelo menos 10ms (pode ser um pouco mais)
        assert metadata.processing_time_ms >= 10
