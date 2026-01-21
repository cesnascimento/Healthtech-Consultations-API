"""
Testes para os summarizers.

Verifica a geração de resumos e o funcionamento das estratégias.
"""

from datetime import date

import pytest

from app.models.common import BiologicalSex, SummarizerStrategy
from app.models.consultation import ConsultationCreate
from app.models.patient import Patient, VitalSigns
from app.services.summarizers.base import SummarizerProtocol, SummarizerResult
from app.services.summarizers.factory import get_summarizer, get_rule_based_summarizer
from app.services.summarizers.rule_based import RuleBasedSummarizer


class TestRuleBasedSummarizer:
    """Testes para o RuleBasedSummarizer."""

    @pytest.fixture
    def summarizer(self) -> RuleBasedSummarizer:
        """Instância do summarizer."""
        return RuleBasedSummarizer()

    def test_implements_protocol(self, summarizer: RuleBasedSummarizer) -> None:
        """Summarizer deve implementar o protocolo."""
        assert isinstance(summarizer, SummarizerProtocol)

    def test_strategy_name(self, summarizer: RuleBasedSummarizer) -> None:
        """Deve retornar o nome correto da estratégia."""
        assert summarizer.STRATEGY_NAME == "rule_based"

    def test_summarize_returns_result(
        self,
        summarizer: RuleBasedSummarizer,
        minimal_consultation: ConsultationCreate,
    ) -> None:
        """summarize() deve retornar SummarizerResult."""
        result = summarizer.summarize(minimal_consultation)

        assert isinstance(result, SummarizerResult)
        assert result.strategy_used == "rule_based"
        assert len(result.sections) > 0
        assert result.full_text != ""

    def test_generates_identification_section(
        self,
        summarizer: RuleBasedSummarizer,
        complete_consultation: ConsultationCreate,
    ) -> None:
        """Deve gerar seção de identificação."""
        result = summarizer.summarize(complete_consultation)

        identification = next(
            (s for s in result.sections if s.code == "identification"),
            None,
        )
        assert identification is not None
        assert identification.order == 1
        assert "Maria Silva Santos" in identification.content
        assert "123.456.789-00" in identification.content

    def test_generates_complaint_section(
        self,
        summarizer: RuleBasedSummarizer,
        complete_consultation: ConsultationCreate,
    ) -> None:
        """Deve gerar seção de queixa e história."""
        result = summarizer.summarize(complete_consultation)

        complaint = next(
            (s for s in result.sections if s.code == "complaint_history"),
            None,
        )
        assert complaint is not None
        assert complaint.order == 2
        assert "Dor de cabeça" in complaint.content

    def test_generates_vital_signs_section(
        self,
        summarizer: RuleBasedSummarizer,
        complete_consultation: ConsultationCreate,
    ) -> None:
        """Deve gerar seção de sinais vitais."""
        result = summarizer.summarize(complete_consultation)

        vitals = next(
            (s for s in result.sections if s.code == "vital_signs"),
            None,
        )
        assert vitals is not None
        assert vitals.order == 3
        assert "120x80" in vitals.content or "120" in vitals.content
        assert "72" in vitals.content  # FC

    def test_generates_background_section(
        self,
        summarizer: RuleBasedSummarizer,
        complete_consultation: ConsultationCreate,
    ) -> None:
        """Deve gerar seção de antecedentes."""
        result = summarizer.summarize(complete_consultation)

        background = next(
            (s for s in result.sections if s.code == "background"),
            None,
        )
        assert background is not None
        assert background.order == 4
        assert "dipirona" in background.content.lower()  # Alergia
        assert "losartana" in background.content.lower()  # Medicamento

    def test_generates_physical_exam_section_when_present(
        self,
        summarizer: RuleBasedSummarizer,
        complete_consultation: ConsultationCreate,
    ) -> None:
        """Deve gerar seção de exame físico quando presente."""
        result = summarizer.summarize(complete_consultation)

        exam = next(
            (s for s in result.sections if s.code == "physical_exam"),
            None,
        )
        assert exam is not None
        assert "BEG" in exam.content

    def test_no_physical_exam_section_when_absent(
        self,
        summarizer: RuleBasedSummarizer,
        minimal_consultation: ConsultationCreate,
    ) -> None:
        """Não deve gerar seção de exame físico quando ausente."""
        result = summarizer.summarize(minimal_consultation)

        exam = next(
            (s for s in result.sections if s.code == "physical_exam"),
            None,
        )
        assert exam is None

    def test_generates_assessment_section(
        self,
        summarizer: RuleBasedSummarizer,
        complete_consultation: ConsultationCreate,
    ) -> None:
        """Deve gerar seção de avaliação."""
        result = summarizer.summarize(complete_consultation)

        assessment = next(
            (s for s in result.sections if s.code == "assessment"),
            None,
        )
        assert assessment is not None
        assert assessment.order == 6

    def test_generates_plan_section_when_present(
        self,
        summarizer: RuleBasedSummarizer,
        complete_consultation: ConsultationCreate,
    ) -> None:
        """Deve gerar seção de plano quando presente."""
        result = summarizer.summarize(complete_consultation)

        plan = next(
            (s for s in result.sections if s.code == "plan"),
            None,
        )
        assert plan is not None
        assert "Paracetamol" in plan.content

    def test_no_plan_section_when_absent(
        self,
        summarizer: RuleBasedSummarizer,
        minimal_consultation: ConsultationCreate,
    ) -> None:
        """Não deve gerar seção de plano quando ausente."""
        result = summarizer.summarize(minimal_consultation)

        plan = next(
            (s for s in result.sections if s.code == "plan"),
            None,
        )
        assert plan is None

    def test_full_text_contains_all_sections(
        self,
        summarizer: RuleBasedSummarizer,
        complete_consultation: ConsultationCreate,
    ) -> None:
        """full_text deve conter todas as seções."""
        result = summarizer.summarize(complete_consultation)

        assert "IDENTIFICAÇÃO" in result.full_text
        assert "QUEIXA E HISTÓRIA" in result.full_text
        assert "SINAIS VITAIS" in result.full_text
        assert "ANTECEDENTES" in result.full_text

    def test_collects_clinical_warnings(
        self,
        summarizer: RuleBasedSummarizer,
        consultation_with_abnormal_vitals: ConsultationCreate,
    ) -> None:
        """Deve coletar warnings do validador clínico."""
        result = summarizer.summarize(consultation_with_abnormal_vitals)

        assert len(result.warnings) > 0
        # Deve ter warnings de sinais vitais anormais
        vital_warnings = [w for w in result.warnings if "BP" in w.code or "HEART" in w.code]
        assert len(vital_warnings) > 0

    def test_truncates_long_text(
        self,
        summarizer: RuleBasedSummarizer,
        valid_patient: Patient,
    ) -> None:
        """Deve truncar textos muito longos e gerar warning."""
        long_text = "A" * 5000  # Excede limite
        consultation = ConsultationCreate(
            patient=valid_patient,
            consultation_date=date(2024, 1, 15),
            chief_complaint="Dor de cabeça",
            history_present_illness=long_text,
            professional_name="Dr. João",
        )

        result = summarizer.summarize(consultation)

        truncation_warnings = [w for w in result.warnings if w.code == "TEXT_TRUNCATED"]
        assert len(truncation_warnings) > 0

    def test_removes_duplicate_medications(
        self,
        summarizer: RuleBasedSummarizer,
        valid_patient: Patient,
        valid_medication,
    ) -> None:
        """Deve remover medicamentos duplicados e gerar warning."""
        from app.models.common import MedicationFrequency, MedicationRoute
        from app.models.medication import Medication

        # Mesmo medicamento duas vezes
        med1 = valid_medication
        med2 = Medication(
            active_ingredient="Losartana Potássica",  # Mesmo, case diferente
            dosage="100mg",
            frequency=MedicationFrequency.ONCE_DAILY,
            route=MedicationRoute.ORAL,
        )

        consultation = ConsultationCreate(
            patient=valid_patient,
            consultation_date=date(2024, 1, 15),
            chief_complaint="Controle HAS",
            current_medications=[med1, med2],
            professional_name="Dr. João",
        )

        result = summarizer.summarize(consultation)

        duplicate_warnings = [w for w in result.warnings if w.code == "DUPLICATE_REMOVED"]
        assert len(duplicate_warnings) > 0

    def test_calculates_imc(
        self,
        summarizer: RuleBasedSummarizer,
        valid_patient: Patient,
    ) -> None:
        """Deve calcular IMC quando peso e altura disponíveis."""
        vital_signs = VitalSigns(
            weight_kg=70.0,
            height_cm=170.0,
        )
        consultation = ConsultationCreate(
            patient=valid_patient,
            consultation_date=date(2024, 1, 15),
            chief_complaint="Check-up",
            vital_signs=vital_signs,
            professional_name="Dr. João",
        )

        result = summarizer.summarize(consultation)

        vitals_section = next(s for s in result.sections if s.code == "vital_signs")
        assert "IMC" in vitals_section.content
        assert "24.2" in vitals_section.content  # 70 / (1.70)^2 ≈ 24.2

    def test_formats_pregnant_patient(
        self,
        summarizer: RuleBasedSummarizer,
        pregnant_patient: Patient,
    ) -> None:
        """Deve formatar corretamente paciente gestante."""
        consultation = ConsultationCreate(
            patient=pregnant_patient,
            consultation_date=date(2024, 1, 15),
            chief_complaint="Pré-natal",
            professional_name="Dr. João",
        )

        result = summarizer.summarize(consultation)

        identification = next(s for s in result.sections if s.code == "identification")
        assert "Gestante" in identification.content
        assert "28" in identification.content  # semanas

    def test_highlights_allergies(
        self,
        summarizer: RuleBasedSummarizer,
        valid_patient: Patient,
        severe_allergy,
    ) -> None:
        """Deve destacar alergias na seção de antecedentes."""
        consultation = ConsultationCreate(
            patient=valid_patient,
            consultation_date=date(2024, 1, 15),
            chief_complaint="Check-up",
            allergies=[severe_allergy],
            professional_name="Dr. João",
        )

        result = summarizer.summarize(consultation)

        background = next(s for s in result.sections if s.code == "background")
        assert "ALERGIAS" in background.content
        assert "penicilina" in background.content.lower()


class TestSummarizerFactory:
    """Testes para a factory de summarizers."""

    def test_get_summarizer_default(self) -> None:
        """Sem parâmetro, deve retornar summarizer baseado no .env."""
        summarizer = get_summarizer()
        # Pode ser RuleBasedSummarizer ou LLMBasedSummarizer dependendo do .env
        assert isinstance(summarizer, SummarizerProtocol)

    def test_get_summarizer_rule_based(self) -> None:
        """Com strategy rule_based, deve retornar RuleBasedSummarizer."""
        summarizer = get_summarizer(SummarizerStrategy.RULE_BASED)
        assert isinstance(summarizer, RuleBasedSummarizer)

    def test_get_summarizer_llm_returns_protocol(self) -> None:
        """Com strategy llm_based, deve retornar um SummarizerProtocol."""
        summarizer = get_summarizer(SummarizerStrategy.LLM_BASED)
        # Retorna LLMBasedSummarizer se configurado, senão RuleBasedSummarizer
        assert isinstance(summarizer, SummarizerProtocol)

    def test_get_rule_based_summarizer_direct(self) -> None:
        """get_rule_based_summarizer deve retornar RuleBasedSummarizer."""
        summarizer = get_rule_based_summarizer()
        assert isinstance(summarizer, RuleBasedSummarizer)


class TestSummarizerResultDataclass:
    """Testes para o dataclass SummarizerResult."""

    def test_default_values(self) -> None:
        """Deve ter valores padrão corretos."""
        from app.models.consultation import SummarySection

        sections = [
            SummarySection(
                title="Test",
                code="test",
                content="Content",
                order=1,
            )
        ]
        result = SummarizerResult(
            sections=sections,
            full_text="Test content",
        )

        assert result.warnings == []
        assert result.strategy_used == "rule_based"

    def test_custom_strategy(self) -> None:
        """Deve aceitar estratégia customizada."""
        from app.models.consultation import SummarySection

        sections = [
            SummarySection(
                title="Test",
                code="test",
                content="Content",
                order=1,
            )
        ]
        result = SummarizerResult(
            sections=sections,
            full_text="Test content",
            strategy_used="custom_strategy",
        )

        assert result.strategy_used == "custom_strategy"


class TestSummarizerDeterminism:
    """Testes para garantir determinismo do rule_based."""

    def test_same_input_same_output(
        self,
        complete_consultation: ConsultationCreate,
    ) -> None:
        """Mesmo input deve gerar mesmo output."""
        summarizer1 = RuleBasedSummarizer()
        summarizer2 = RuleBasedSummarizer()

        result1 = summarizer1.summarize(complete_consultation)
        result2 = summarizer2.summarize(complete_consultation)

        # Mesmo número de seções
        assert len(result1.sections) == len(result2.sections)

        # Mesmo conteúdo em cada seção
        for s1, s2 in zip(result1.sections, result2.sections):
            assert s1.code == s2.code
            assert s1.content == s2.content
            assert s1.order == s2.order

        # Mesmo full_text
        assert result1.full_text == result2.full_text

    def test_multiple_runs_consistent(
        self,
        minimal_consultation: ConsultationCreate,
    ) -> None:
        """Múltiplas execuções devem ser consistentes."""
        summarizer = RuleBasedSummarizer()

        results = [summarizer.summarize(minimal_consultation) for _ in range(5)]

        # Todos os full_text devem ser iguais
        full_texts = [r.full_text for r in results]
        assert len(set(full_texts)) == 1  # Apenas um valor único


class TestLLMBasedSummarizer:
    """Testes para o LLMBasedSummarizer (quando configurado)."""

    def test_llm_summarizer_with_fallback(
        self,
        minimal_consultation: ConsultationCreate,
    ) -> None:
        """LLMBasedSummarizer deve ter fallback configurado."""
        from app.core.config import get_settings

        settings = get_settings()
        if not settings.is_llm_enabled:
            pytest.skip("LLM não configurado no .env")

        from app.services.summarizers.llm_based import LLMBasedSummarizer

        fallback = RuleBasedSummarizer()
        summarizer = LLMBasedSummarizer(fallback=fallback)

        # Deve ter fallback
        assert summarizer._fallback is not None

    def test_llm_summarizer_returns_result(
        self,
        minimal_consultation: ConsultationCreate,
    ) -> None:
        """LLMBasedSummarizer deve retornar SummarizerResult."""
        from app.core.config import get_settings

        settings = get_settings()
        if not settings.is_llm_enabled:
            pytest.skip("LLM não configurado no .env")

        from app.services.summarizers.llm_based import LLMBasedSummarizer

        fallback = RuleBasedSummarizer()
        summarizer = LLMBasedSummarizer(fallback=fallback)

        result = summarizer.summarize(minimal_consultation)

        assert isinstance(result, SummarizerResult)
        assert len(result.sections) > 0
        assert result.full_text != ""
        # strategy_used pode ser llm_based, llm_fallback, ou rule_based (se houver erro)
        assert result.strategy_used in ["llm_based", "llm_fallback", "rule_based"]

    def test_llm_via_factory(
        self,
        minimal_consultation: ConsultationCreate,
    ) -> None:
        """Factory deve retornar LLMBasedSummarizer quando configurado."""
        from app.core.config import get_settings

        settings = get_settings()
        if not settings.is_llm_enabled:
            pytest.skip("LLM não configurado no .env")

        summarizer = get_summarizer(SummarizerStrategy.LLM_BASED)

        # Deve ser LLMBasedSummarizer
        from app.services.summarizers.llm_based import LLMBasedSummarizer
        assert isinstance(summarizer, LLMBasedSummarizer)


class TestRuleBasedVsLLM:
    """Testes comparativos entre rule_based e llm_based."""

    def test_rule_based_always_available(
        self,
        minimal_consultation: ConsultationCreate,
    ) -> None:
        """rule_based deve estar sempre disponível."""
        summarizer = get_summarizer(SummarizerStrategy.RULE_BASED)
        assert isinstance(summarizer, RuleBasedSummarizer)

        result = summarizer.summarize(minimal_consultation)
        assert result.strategy_used == "rule_based"

    def test_both_strategies_produce_identification(
        self,
        minimal_consultation: ConsultationCreate,
    ) -> None:
        """Ambas estratégias devem produzir seção de identificação."""
        from app.core.config import get_settings

        # Teste rule_based
        rule_summarizer = get_summarizer(SummarizerStrategy.RULE_BASED)
        rule_result = rule_summarizer.summarize(minimal_consultation)
        rule_ids = [s.code for s in rule_result.sections]
        assert "identification" in rule_ids

        # Teste llm_based (se configurado)
        settings = get_settings()
        if settings.is_llm_enabled:
            llm_summarizer = get_summarizer(SummarizerStrategy.LLM_BASED)
            llm_result = llm_summarizer.summarize(minimal_consultation)
            llm_ids = [s.code for s in llm_result.sections]
            assert "identification" in llm_ids

    def test_fallback_on_llm_error(
        self,
        minimal_consultation: ConsultationCreate,
    ) -> None:
        """Em caso de erro no LLM, deve fazer fallback para rule_based."""
        from app.core.config import get_settings

        settings = get_settings()
        if not settings.is_llm_enabled:
            pytest.skip("LLM não configurado no .env")

        from app.services.summarizers.llm_based import LLMBasedSummarizer

        fallback = RuleBasedSummarizer()
        summarizer = LLMBasedSummarizer(fallback=fallback)

        # Mesmo que haja erro, deve retornar resultado (via fallback)
        result = summarizer.summarize(minimal_consultation)

        assert isinstance(result, SummarizerResult)
        assert len(result.sections) > 0
