"""
Summarizer baseado em LLM (Gemini).

Implementa a estratégia llm_based para geração de resumos clínicos
com auxílio de inteligência artificial.

⚠️ IMPORTANTE:
- Esta estratégia é OPCIONAL
- SEMPRE possui fallback para rule_based
- NUNCA infere diagnósticos
- Possui guardrails explícitos

Características:
- Importação lazy do google-generativeai
- Timeout configurável
- Parse defensivo de resposta
- Filtro de termos diagnósticos
- Fallback automático em QUALQUER falha
"""

from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING, Any

from app.core.config import get_settings
from app.core.constants import FORBIDDEN_DIAGNOSTIC_TERMS
from app.models.common import WarningLevel
from app.models.consultation import (
    ConsultationCreate,
    ConsultationWarning,
    SummarySection,
)
from app.services.summarizers.base import SummarizerProtocol, SummarizerResult

if TYPE_CHECKING:
    pass


class LLMError(Exception):
    """Erro específico de integração com LLM."""

    def __init__(self, message: str, reason: str) -> None:
        super().__init__(message)
        self.reason = reason


class LLMBasedSummarizer:
    """
    Summarizer que utiliza LLM (Gemini) para geração de resumos.

    Esta classe encapsula completamente a integração com o Gemini,
    garantindo:
    - Importação lazy da biblioteca
    - Fallback automático para rule_based
    - Guardrails contra inferência diagnóstica
    - Timeout e retry configuráveis

    ⚠️ NUNCA quebra o fluxo clínico - qualquer falha resulta em fallback.

    Example:
        ```python
        from app.services.summarizers.rule_based import RuleBasedSummarizer

        fallback = RuleBasedSummarizer()
        summarizer = LLMBasedSummarizer(fallback=fallback)
        result = summarizer.summarize(consultation)
        ```
    """

    STRATEGY_NAME = "llm_based"
    FALLBACK_STRATEGY_NAME = "llm_fallback"

    SYSTEM_PROMPT = """Você é um assistente de documentação médica. Sua função é APENAS reorganizar e formatar dados clínicos fornecidos.

REGRAS OBRIGATÓRIAS - VIOLAÇÃO RESULTA EM REJEIÇÃO:

1. NUNCA inferir, sugerir ou mencionar diagnósticos
2. NUNCA usar termos como: "diagnóstico", "suspeita de", "sugere", "indica", "compatível com", "provável", "possível"
3. NUNCA criar hipóteses diagnósticas
4. NUNCA inventar dados não fornecidos
5. NUNCA adicionar interpretações clínicas
6. APENAS reorganizar os dados EXATAMENTE como fornecidos
7. APENAS formatar e estruturar as informações

Você deve retornar um JSON com a seguinte estrutura:
{
  "sections": [
    {"title": "string", "code": "string", "content": "string", "order": number}
  ]
}

Seções esperadas (em ordem):
1. identification - Identificação do paciente
2. complaint_history - Queixa e história
3. vital_signs - Sinais vitais (se fornecidos)
4. background - Antecedentes e segurança
5. physical_exam - Exame físico (se fornecido)
6. assessment - Avaliação (APENAS contexto, SEM diagnóstico)
7. plan - Plano (se fornecido)

IMPORTANTE: A seção "assessment" deve conter APENAS um resumo do contexto da consulta, NUNCA diagnósticos ou hipóteses."""

    def __init__(
        self,
        fallback: SummarizerProtocol,
    ) -> None:
        """
        Inicializa o summarizer LLM.

        Args:
            fallback: Summarizer para fallback (obrigatório).
        """
        self._fallback = fallback
        self._settings = get_settings()
        self._model: Any = None
        self._genai_module: Any = None
        self._warnings: list[ConsultationWarning] = []

    def summarize(self, consultation: ConsultationCreate) -> SummarizerResult:
        """
        Processa consulta usando LLM com fallback automático.

        Em caso de QUALQUER falha, utiliza automaticamente o
        summarizer de fallback (rule_based).

        Args:
            consultation: Dados da consulta.

        Returns:
            SummarizerResult com resumo gerado.
        """
        self._warnings = []

        try:
            if not self._settings.is_llm_enabled:
                raise LLMError(
                    "LLM não configurado",
                    reason="LLM not configured - missing API key",
                )

            self._lazy_init()

            result = self._generate_with_llm(consultation)

            return result

        except Exception as e:
            return self._execute_fallback(consultation, str(e))

    def _lazy_init(self) -> None:
        """
        Inicialização lazy do cliente Gemini.

        Importa a biblioteca apenas quando necessário,
        evitando overhead em instalações sem LLM.
        """
        if self._model is not None:
            return

        try:
            import google.generativeai as genai

            self._genai_module = genai

            genai.configure(api_key=self._settings.GEMINI_API_KEY)

            self._model = genai.GenerativeModel(
                model_name=self._settings.GEMINI_MODEL,
                generation_config={
                    "temperature": 0.1,
                    "top_p": 0.8,
                    "top_k": 40,
                    "max_output_tokens": 4096,
                },
            )

        except ImportError as e:
            raise LLMError(
                "Biblioteca google-generativeai não instalada",
                reason=f"ImportError: {e}",
            )
        except Exception as e:
            raise LLMError(
                "Falha ao inicializar Gemini",
                reason=f"Init error: {e}",
            )

    def _generate_with_llm(
        self, consultation: ConsultationCreate
    ) -> SummarizerResult:
        """
        Gera resumo usando o LLM.

        Args:
            consultation: Dados da consulta.

        Returns:
            SummarizerResult com resumo.

        Raises:
            LLMError: Em caso de falha.
        """
        user_prompt = self._build_user_prompt(consultation)

        try:
            response = self._model.generate_content(
                [self.SYSTEM_PROMPT, user_prompt],
                request_options={"timeout": self._settings.LLM_TIMEOUT_SECONDS},
            )

            if not response or not response.text:
                raise LLMError(
                    "Resposta vazia do LLM",
                    reason="Empty response from Gemini",
                )

            response_text = response.text

            sections = self._parse_response(response_text)

            sections = self._apply_guardrails(sections)

            full_text = self._build_full_text(sections)

            return SummarizerResult(
                sections=sections,
                full_text=full_text,
                warnings=self._warnings,
                strategy_used=self.STRATEGY_NAME,
            )

        except LLMError:
            raise
        except Exception as e:
            raise LLMError(
                f"Erro na geração: {e}",
                reason=f"Generation error: {type(e).__name__}: {e}",
            )

    def _build_user_prompt(self, consultation: ConsultationCreate) -> str:
        """
        Constrói o prompt do usuário com os dados da consulta.

        Args:
            consultation: Dados da consulta.

        Returns:
            Prompt formatado.
        """
        patient = consultation.patient

        data = {
            "paciente": {
                "nome": patient.full_name,
                "cpf": patient.cpf,
                "data_nascimento": str(patient.birth_date),
                "sexo_biologico": patient.biological_sex.value,
                "tipo_sanguineo": patient.blood_type.value if patient.blood_type else None,
                "gestante": patient.is_pregnant,
                "semanas_gestacionais": patient.gestational_weeks,
            },
            "consulta": {
                "data": str(consultation.consultation_date),
                "tipo": consultation.consultation_type,
                "local": consultation.facility_name,
                "profissional": consultation.professional_name,
                "registro": consultation.professional_council_id,
                "especialidade": consultation.specialty,
            },
            "queixa_principal": consultation.chief_complaint,
            "historia_doenca_atual": consultation.history_present_illness,
        }

        if consultation.vital_signs:
            vs = consultation.vital_signs
            data["sinais_vitais"] = {
                "pa_sistolica": vs.systolic_bp,
                "pa_diastolica": vs.diastolic_bp,
                "frequencia_cardiaca": vs.heart_rate,
                "frequencia_respiratoria": vs.respiratory_rate,
                "temperatura": vs.temperature_celsius,
                "saturacao_o2": vs.oxygen_saturation,
                "escala_dor": vs.pain_scale,
                "peso_kg": vs.weight_kg,
                "altura_cm": vs.height_cm,
            }

        if consultation.current_medications:
            data["medicamentos"] = [
                {
                    "principio_ativo": m.active_ingredient,
                    "dosagem": m.dosage,
                    "frequencia": m.frequency.value,
                    "via": m.route.value,
                }
                for m in consultation.current_medications
            ]

        if consultation.allergies:
            data["alergias"] = [
                {
                    "alergeno": a.allergen,
                    "tipo": a.reaction_type,
                    "gravidade": a.severity,
                    "confirmada": a.confirmed,
                }
                for a in consultation.allergies
            ]

        data["antecedentes_pessoais"] = consultation.past_medical_history
        data["antecedentes_familiares"] = consultation.family_history
        data["historia_social"] = consultation.social_history

        data["exame_fisico"] = consultation.physical_examination

        data["plano_tratamento"] = consultation.treatment_plan

        data["observacoes"] = consultation.additional_notes

        prompt = f"""Reorganize os seguintes dados de consulta médica em um resumo estruturado.

LEMBRE-SE: Apenas reorganize os dados. NÃO faça inferências ou diagnósticos.

DADOS DA CONSULTA:
{json.dumps(data, ensure_ascii=False, indent=2)}

Retorne APENAS o JSON com as seções, sem texto adicional."""

        return prompt

    def _parse_response(self, response_text: str) -> list[SummarySection]:
        """
        Parse defensivo da resposta do LLM.

        Args:
            response_text: Texto da resposta.

        Returns:
            Lista de seções.

        Raises:
            LLMError: Se o parse falhar.
        """
        try:
            text = response_text.strip()
            if text.startswith("```"):
                text = re.sub(r"^```(?:json)?\n?", "", text)
                text = re.sub(r"\n?```$", "", text)

            data = json.loads(text)

            if not isinstance(data, dict) or "sections" not in data:
                raise LLMError(
                    "Formato de resposta inválido",
                    reason="Response missing 'sections' key",
                )

            sections: list[SummarySection] = []
            for idx, section_data in enumerate(data["sections"]):
                if not all(k in section_data for k in ("title", "code", "content")):
                    self._add_warning(
                        "LLM_SECTION_INCOMPLETE",
                        WarningLevel.LOW,
                        f"Seção {idx} incompleta, ignorada",
                    )
                    continue

                sections.append(
                    SummarySection(
                        title=str(section_data["title"])[:100],
                        code=str(section_data["code"])[:50].lower().replace(" ", "_"),
                        content=str(section_data["content"])[:3000],
                        order=int(section_data.get("order", idx + 1)),
                    )
                )

            if not sections:
                raise LLMError(
                    "Nenhuma seção válida na resposta",
                    reason="No valid sections parsed",
                )

            return sections

        except json.JSONDecodeError as e:
            raise LLMError(
                "Resposta não é JSON válido",
                reason=f"JSON parse error: {e}",
            )
        except LLMError:
            raise
        except Exception as e:
            raise LLMError(
                f"Erro no parse: {e}",
                reason=f"Parse error: {type(e).__name__}: {e}",
            )

    def _apply_guardrails(
        self, sections: list[SummarySection]
    ) -> list[SummarySection]:
        """
        Aplica guardrails de segurança nas seções.

        Verifica e remove termos diagnósticos proibidos.

        Args:
            sections: Seções geradas pelo LLM.

        Returns:
            Seções filtradas.

        Raises:
            LLMError: Se termos críticos forem detectados.
        """
        filtered_sections: list[SummarySection] = []
        violations_found = False

        for section in sections:
            content_lower = section.content.lower()

            found_terms: list[str] = []
            for term in FORBIDDEN_DIAGNOSTIC_TERMS:
                if term in content_lower:
                    found_terms.append(term)

            if found_terms:
                violations_found = True
                self._add_warning(
                    "LLM_DIAGNOSTIC_TERMS_DETECTED",
                    WarningLevel.HIGH,
                    f"Termos diagnósticos detectados na seção '{section.title}': {', '.join(found_terms[:3])}",
                    field=f"sections.{section.code}",
                )

                cleaned_content = section.content
                for term in found_terms:
                    pattern = re.compile(re.escape(term), re.IGNORECASE)
                    cleaned_content = pattern.sub("[REMOVIDO]", cleaned_content)

                section = SummarySection(
                    title=section.title,
                    code=section.code,
                    content=cleaned_content,
                    order=section.order,
                )

            filtered_sections.append(section)

        if violations_found:
            self._add_warning(
                "LLM_GUARDRAILS_TRIGGERED",
                WarningLevel.MEDIUM,
                "Guardrails acionados - termos diagnósticos foram removidos",
            )

        return filtered_sections

    def _build_full_text(self, sections: list[SummarySection]) -> str:
        """Monta texto completo a partir das seções."""
        parts: list[str] = []

        for section in sorted(sections, key=lambda s: s.order):
            header = f"=== {section.title.upper()} ==="
            parts.append(header)
            parts.append(section.content)
            parts.append("")

        return "\n".join(parts).strip()

    def _execute_fallback(
        self, consultation: ConsultationCreate, error_reason: str
    ) -> SummarizerResult:
        """
        Executa fallback para rule_based.

        Args:
            consultation: Dados da consulta.
            error_reason: Motivo do fallback.

        Returns:
            SummarizerResult do fallback.
        """
        self._add_warning(
            "LLM_FALLBACK_ACTIVATED",
            WarningLevel.INFO,
            f"Fallback para rule_based ativado: {error_reason[:100]}",
        )

        fallback_result = self._fallback.summarize(consultation)

        all_warnings = self._warnings + fallback_result.warnings

        return SummarizerResult(
            sections=fallback_result.sections,
            full_text=fallback_result.full_text,
            warnings=all_warnings,
            strategy_used=self.FALLBACK_STRATEGY_NAME,
        )

    def _add_warning(
        self,
        code: str,
        level: WarningLevel,
        message: str,
        field: str | None = None,
    ) -> None:
        """Adiciona um warning à lista."""
        self._warnings.append(
            ConsultationWarning(
                code=code,
                level=level,
                message=message,
                field=field,
                value=None,
            )
        )
