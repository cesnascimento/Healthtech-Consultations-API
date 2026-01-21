"""
Summarizer baseado em regras determinísticas.

Implementa a estratégia rule_based para geração de resumos clínicos
sem uso de inteligência artificial.

Características:
- 100% determinístico e reproduzível
- Não infere diagnósticos
- Apenas reorganiza e normaliza dados fornecidos
- Gera warnings para inconsistências
"""

from app.core.constants import TEXT_LIMITS
from app.models.common import WarningLevel
from app.models.consultation import (
    ConsultationCreate,
    ConsultationWarning,
    SummarySection,
)
from app.services.summarizers.base import SummarizerResult
from app.services.validators.clinical import ClinicalValidator
from app.utils.text import TextProcessor


class RuleBasedSummarizer:
    """
    Summarizer baseado em regras determinísticas.

    Processa dados de consulta médica e gera resumo estruturado
    seguindo regras fixas de formatação e organização.

    O resumo é dividido em seções padronizadas:
    1. Identificação
    2. Queixa e História
    3. Sinais Vitais
    4. Antecedentes e Segurança
    5. Exame Físico (se presente)
    6. Avaliação (se presente)
    7. Plano (se presente)

    Example:
        ```python
        summarizer = RuleBasedSummarizer()
        result = summarizer.summarize(consultation)
        print(result.sections)
        print(result.warnings)
        ```
    """

    STRATEGY_NAME = "rule_based"

    def __init__(self) -> None:
        """Inicializa o summarizer."""
        self._text_processor = TextProcessor()
        self._validator = ClinicalValidator()
        self._warnings: list[ConsultationWarning] = []

    def summarize(self, consultation: ConsultationCreate) -> SummarizerResult:
        """
        Processa consulta e gera resumo estruturado.

        Args:
            consultation: Dados completos da consulta.

        Returns:
            SummarizerResult com seções, texto e warnings.
        """
        self._warnings = []

        clinical_warnings = self._validator.validate(consultation)
        self._warnings.extend(clinical_warnings)

        sections = self._generate_sections(consultation)

        full_text = self._build_full_text(sections)

        return SummarizerResult(
            sections=sections,
            full_text=full_text,
            warnings=self._warnings,
            strategy_used=self.STRATEGY_NAME,
        )

    def _generate_sections(
        self, consultation: ConsultationCreate
    ) -> list[SummarySection]:
        """Gera todas as seções do resumo."""
        sections: list[SummarySection] = []

        sections.append(self._build_identification_section(consultation))

        sections.append(self._build_complaint_section(consultation))

        if consultation.vital_signs:
            sections.append(self._build_vital_signs_section(consultation))

        sections.append(self._build_background_section(consultation))

        if consultation.physical_examination:
            sections.append(self._build_physical_exam_section(consultation))

        sections.append(self._build_assessment_section(consultation))

        if consultation.treatment_plan:
            sections.append(self._build_plan_section(consultation))

        return sections

    def _build_identification_section(
        self, consultation: ConsultationCreate
    ) -> SummarySection:
        """Constrói seção de identificação do paciente."""
        patient = consultation.patient

        age = TextProcessor.calculate_age(str(patient.birth_date))
        age_str = f" ({age} anos)" if age is not None else ""

        birth_date_br = TextProcessor.format_date_br(str(patient.birth_date))

        sex_map = {
            "male": "Masculino",
            "female": "Feminino",
            "intersex": "Intersexo",
        }
        sex_str = sex_map.get(patient.biological_sex.value, patient.biological_sex.value)

        lines = [
            f"Paciente: {patient.full_name}",
            f"CPF: {patient.cpf}",
            f"Nascimento: {birth_date_br}{age_str}",
            f"Sexo biológico: {sex_str}",
        ]

        if patient.blood_type:
            lines.append(f"Tipo sanguíneo: {patient.blood_type.value}")

        if patient.is_pregnant:
            weeks = patient.gestational_weeks or "?"
            lines.append(f"Gestante: {weeks} semanas")

        consult_date_br = TextProcessor.format_date_br(str(consultation.consultation_date))
        consult_type_map = {
            "first_visit": "Primeira consulta",
            "follow_up": "Retorno",
            "emergency": "Emergência",
            "telemedicine": "Teleconsulta",
            "routine": "Rotina",
        }
        consult_type_str = consult_type_map.get(
            consultation.consultation_type, consultation.consultation_type
        )

        lines.append(f"Data da consulta: {consult_date_br}")
        lines.append(f"Tipo: {consult_type_str}")

        if consultation.facility_name:
            lines.append(f"Local: {consultation.facility_name}")

        lines.append(f"Profissional: {consultation.professional_name}")
        if consultation.professional_council_id:
            lines.append(f"Registro: {consultation.professional_council_id}")
        if consultation.specialty:
            lines.append(f"Especialidade: {consultation.specialty}")

        return SummarySection(
            title="Identificação",
            code="identification",
            content=" | ".join(lines),
            order=1,
        )

    def _build_complaint_section(
        self, consultation: ConsultationCreate
    ) -> SummarySection:
        """Constrói seção de queixa e história."""
        parts = [f"Queixa principal: {consultation.chief_complaint}"]

        if consultation.history_present_illness:
            hpi, was_truncated = TextProcessor.truncate(
                consultation.history_present_illness,
                TEXT_LIMITS["history_present_illness"],
            )
            if was_truncated:
                self._add_truncation_warning(
                    "history_present_illness",
                    TEXT_LIMITS["history_present_illness"],
                )
            parts.append(f"\nHDA: {TextProcessor.normalize_whitespace(hpi)}")

        return SummarySection(
            title="Queixa e História",
            code="complaint_history",
            content="\n".join(parts),
            order=2,
        )

    def _build_vital_signs_section(
        self, consultation: ConsultationCreate
    ) -> SummarySection:
        """Constrói seção de sinais vitais."""
        vs = consultation.vital_signs
        if not vs:
            return SummarySection(
                title="Sinais Vitais",
                code="vital_signs",
                content="Não informados",
                order=3,
            )

        parts: list[str] = []

        if vs.systolic_bp is not None and vs.diastolic_bp is not None:
            parts.append(f"PA: {vs.systolic_bp}x{vs.diastolic_bp} mmHg")
        elif vs.systolic_bp is not None:
            parts.append(f"PAS: {vs.systolic_bp} mmHg")
        elif vs.diastolic_bp is not None:
            parts.append(f"PAD: {vs.diastolic_bp} mmHg")

        if vs.heart_rate is not None:
            parts.append(f"FC: {vs.heart_rate} bpm")

        if vs.respiratory_rate is not None:
            parts.append(f"FR: {vs.respiratory_rate} irpm")

        if vs.temperature_celsius is not None:
            parts.append(f"Tax: {vs.temperature_celsius}°C")

        if vs.oxygen_saturation is not None:
            parts.append(f"SpO2: {vs.oxygen_saturation}%")

        if vs.pain_scale is not None:
            parts.append(f"Dor: {vs.pain_scale}/10")

        if vs.weight_kg is not None:
            parts.append(f"Peso: {vs.weight_kg} kg")
        if vs.height_cm is not None:
            parts.append(f"Altura: {vs.height_cm} cm")

        if vs.weight_kg is not None and vs.height_cm is not None:
            height_m = vs.height_cm / 100
            imc = vs.weight_kg / (height_m * height_m)
            parts.append(f"IMC: {imc:.1f} kg/m²")

        content = " | ".join(parts) if parts else "Não informados"

        return SummarySection(
            title="Sinais Vitais",
            code="vital_signs",
            content=content,
            order=3,
        )

    def _build_background_section(
        self, consultation: ConsultationCreate
    ) -> SummarySection:
        """Constrói seção de antecedentes e segurança."""
        parts: list[str] = []

        if consultation.allergies:
            allergy_items = []
            for allergy in consultation.allergies:
                severity_map = {
                    "mild": "leve",
                    "moderate": "moderada",
                    "severe": "GRAVE",
                    "life_threatening": "RISCO DE VIDA",
                }
                severity = severity_map.get(allergy.severity, allergy.severity)
                confirmed = "✓" if allergy.confirmed else "?"
                allergy_items.append(f"{allergy.allergen} ({severity}) {confirmed}")

            parts.append(f"⚠️ ALERGIAS: {'; '.join(allergy_items)}")
        else:
            parts.append("Alergias: Não informadas")

        if consultation.current_medications:
            seen_meds: set[str] = set()
            unique_meds: list[str] = []
            duplicates: list[str] = []

            for med in consultation.current_medications:
                key = med.active_ingredient.lower()
                if key not in seen_meds:
                    seen_meds.add(key)
                    freq_str = med.frequency.value if med.frequency else ""
                    unique_meds.append(f"{med.active_ingredient} {med.dosage} {freq_str}".strip())
                else:
                    duplicates.append(med.active_ingredient)

            if duplicates:
                self._add_duplicate_warning("current_medications", duplicates)

            parts.append(f"Medicamentos em uso: {'; '.join(unique_meds)}")
        else:
            parts.append("Medicamentos em uso: Nenhum informado")

        if consultation.past_medical_history:
            history, removed = TextProcessor.remove_duplicates(
                consultation.past_medical_history
            )
            if removed:
                self._add_duplicate_warning("past_medical_history", removed)
            parts.append(f"Antecedentes pessoais: {'; '.join(history)}")
        else:
            parts.append("Antecedentes pessoais: Não informados")

        if consultation.family_history:
            family, removed = TextProcessor.remove_duplicates(
                consultation.family_history
            )
            if removed:
                self._add_duplicate_warning("family_history", removed)
            parts.append(f"Antecedentes familiares: {'; '.join(family)}")

        if consultation.social_history:
            social, was_truncated = TextProcessor.truncate(
                consultation.social_history, 500
            )
            if was_truncated:
                self._add_truncation_warning("social_history", 500)
            parts.append(f"História social: {social}")

        return SummarySection(
            title="Antecedentes e Segurança",
            code="background",
            content="\n".join(parts),
            order=4,
        )

    def _build_physical_exam_section(
        self, consultation: ConsultationCreate
    ) -> SummarySection:
        """Constrói seção de exame físico."""
        exam = consultation.physical_examination or ""

        exam_text, was_truncated = TextProcessor.truncate(
            exam, TEXT_LIMITS["physical_examination"]
        )
        if was_truncated:
            self._add_truncation_warning(
                "physical_examination",
                TEXT_LIMITS["physical_examination"],
            )

        return SummarySection(
            title="Exame Físico",
            code="physical_exam",
            content=TextProcessor.normalize_whitespace(exam_text) or "Não realizado",
            order=5,
        )

    def _build_assessment_section(
        self, consultation: ConsultationCreate
    ) -> SummarySection:
        """
        Constrói seção de avaliação.

        IMPORTANTE: Esta seção NÃO contém diagnósticos.
        Apenas resume o contexto clínico apresentado.
        """
        parts = [
            f"Consulta de {consultation.consultation_type.replace('_', ' ')}",
            f"realizada em {TextProcessor.format_date_br(str(consultation.consultation_date))}.",
        ]

        age = TextProcessor.calculate_age(str(consultation.patient.birth_date))
        if age is not None:
            if age < 18:
                parts.append(f"Paciente pediátrico ({age} anos).")
            elif age >= 65:
                parts.append(f"Paciente idoso ({age} anos).")

        if consultation.patient.is_pregnant:
            weeks = consultation.patient.gestational_weeks
            parts.append(f"Gestante de {weeks} semanas.")

        if consultation.allergies:
            severe = [a for a in consultation.allergies if a.severity in ("severe", "life_threatening")]
            if severe:
                parts.append(f"ATENÇÃO: {len(severe)} alergia(s) grave(s) documentada(s).")

        if consultation.additional_notes:
            notes, was_truncated = TextProcessor.truncate(
                consultation.additional_notes, TEXT_LIMITS["additional_notes"]
            )
            if was_truncated:
                self._add_truncation_warning(
                    "additional_notes", TEXT_LIMITS["additional_notes"]
                )
            parts.append(f"Observações: {notes}")

        return SummarySection(
            title="Avaliação",
            code="assessment",
            content=" ".join(parts),
            order=6,
        )

    def _build_plan_section(
        self, consultation: ConsultationCreate
    ) -> SummarySection:
        """Constrói seção de plano terapêutico."""
        plan = consultation.treatment_plan or ""

        plan_text, was_truncated = TextProcessor.truncate(
            plan, TEXT_LIMITS["treatment_plan"]
        )
        if was_truncated:
            self._add_truncation_warning(
                "treatment_plan", TEXT_LIMITS["treatment_plan"]
            )

        return SummarySection(
            title="Plano",
            code="plan",
            content=TextProcessor.normalize_whitespace(plan_text) or "Não definido",
            order=7,
        )

    def _build_full_text(self, sections: list[SummarySection]) -> str:
        """Monta texto completo a partir das seções."""
        parts: list[str] = []

        for section in sorted(sections, key=lambda s: s.order):
            header = f"=== {section.title.upper()} ==="
            parts.append(header)
            parts.append(section.content)
            parts.append("") 

        full_text = "\n".join(parts).strip()

        if len(full_text) > TEXT_LIMITS["full_summary"]:
            full_text = full_text[: TEXT_LIMITS["full_summary"] - 3] + "..."
            self._add_truncation_warning("full_summary", TEXT_LIMITS["full_summary"])

        return full_text

    def _add_truncation_warning(self, field: str, limit: int) -> None:
        """Adiciona warning de truncamento."""
        self._warnings.append(
            ConsultationWarning(
                code="TEXT_TRUNCATED",
                level=WarningLevel.INFO,
                message=f"Campo '{field}' truncado para {limit} caracteres",
                field=field,
                value=str(limit),
            )
        )

    def _add_duplicate_warning(self, field: str, duplicates: list[str]) -> None:
        """Adiciona warning de duplicatas removidas."""
        self._warnings.append(
            ConsultationWarning(
                code="DUPLICATE_REMOVED",
                level=WarningLevel.INFO,
                message=f"Duplicata(s) removida(s) de '{field}': {', '.join(duplicates[:3])}",
                field=field,
                value=str(len(duplicates)),
            )
        )
