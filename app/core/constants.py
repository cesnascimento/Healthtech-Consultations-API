"""
Constantes clínicas e de configuração do sistema.

Este módulo centraliza valores de referência utilizados para
validações e geração de warnings durante o processamento.

⚠️ IMPORTANTE: Estas faixas são para referência de adultos saudáveis.
Faixas pediátricas, geriátricas e condições específicas podem diferir.
"""

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True)
class VitalSignRange:
    """Faixa de referência para um sinal vital."""

    min_normal: float
    max_normal: float
    min_critical: float
    max_critical: float
    unit: str


# === FAIXAS DE SINAIS VITAIS (ADULTOS) ===

VITAL_SIGNS_RANGES: Final[dict[str, VitalSignRange]] = {
    "systolic_bp": VitalSignRange(
        min_normal=90,
        max_normal=120,
        min_critical=70,
        max_critical=180,
        unit="mmHg",
    ),
    "diastolic_bp": VitalSignRange(
        min_normal=60,
        max_normal=80,
        min_critical=40,
        max_critical=120,
        unit="mmHg",
    ),
    "heart_rate": VitalSignRange(
        min_normal=60,
        max_normal=100,
        min_critical=40,
        max_critical=150,
        unit="bpm",
    ),
    "respiratory_rate": VitalSignRange(
        min_normal=12,
        max_normal=20,
        min_critical=8,
        max_critical=30,
        unit="irpm",
    ),
    "temperature_celsius": VitalSignRange(
        min_normal=36.0,
        max_normal=37.5,
        min_critical=35.0,
        max_critical=40.0,
        unit="°C",
    ),
    "oxygen_saturation": VitalSignRange(
        min_normal=95,
        max_normal=100,
        min_critical=90,
        max_critical=100,
        unit="%",
    ),
}

# === LIMITES DE TEXTO ===

TEXT_LIMITS: Final[dict[str, int]] = {
    "history_present_illness": 2000,
    "physical_examination": 2000,
    "treatment_plan": 2000,
    "additional_notes": 1000,
    "section_content": 3000,
    "full_summary": 15000,
}

# === CÓDIGOS DE WARNING ===

WARNING_CODES: Final[dict[str, str]] = {
    # Sinais vitais
    "SYSTOLIC_BP_LOW": "Pressão arterial sistólica abaixo do esperado",
    "SYSTOLIC_BP_HIGH": "Pressão arterial sistólica acima do esperado",
    "SYSTOLIC_BP_CRITICAL_LOW": "Pressão arterial sistólica criticamente baixa",
    "SYSTOLIC_BP_CRITICAL_HIGH": "Pressão arterial sistólica criticamente elevada",
    "DIASTOLIC_BP_LOW": "Pressão arterial diastólica abaixo do esperado",
    "DIASTOLIC_BP_HIGH": "Pressão arterial diastólica acima do esperado",
    "HEART_RATE_LOW": "Frequência cardíaca abaixo do esperado (bradicardia)",
    "HEART_RATE_HIGH": "Frequência cardíaca acima do esperado (taquicardia)",
    "RESPIRATORY_RATE_LOW": "Frequência respiratória abaixo do esperado",
    "RESPIRATORY_RATE_HIGH": "Frequência respiratória acima do esperado",
    "TEMPERATURE_LOW": "Temperatura abaixo do esperado (hipotermia)",
    "TEMPERATURE_HIGH": "Temperatura acima do esperado (febre)",
    "OXYGEN_SATURATION_LOW": "Saturação de oxigênio abaixo do esperado (hipoxemia)",
    # Texto
    "TEXT_TRUNCATED": "Texto truncado para limite máximo",
    "DUPLICATE_REMOVED": "Entrada duplicada removida",
    # Dados
    "MISSING_VITAL_SIGNS": "Sinais vitais não informados",
    "MISSING_ALLERGIES_INFO": "Informações de alergias não fornecidas",
    "MEDICATION_WITHOUT_DOSAGE": "Medicamento sem dosagem especificada",
    # Inconsistências
    "BP_INCONSISTENT": "Pressão sistólica menor que diastólica",
    "AGE_VITAL_MISMATCH": "Sinais vitais atípicos para faixa etária",
}

# === SEÇÕES DO RESUMO ===

SUMMARY_SECTIONS: Final[list[dict[str, str | int]]] = [
    {"code": "identification", "title": "Identificação", "order": 1},
    {"code": "complaint_history", "title": "Queixa e História", "order": 2},
    {"code": "vital_signs", "title": "Sinais Vitais", "order": 3},
    {"code": "background", "title": "Antecedentes e Segurança", "order": 4},
    {"code": "physical_exam", "title": "Exame Físico", "order": 5},
    {"code": "assessment", "title": "Avaliação", "order": 6},
    {"code": "plan", "title": "Plano", "order": 7},
]

# === TERMOS DIAGNÓSTICOS PROIBIDOS (PARA GUARDRAIL LLM) ===

FORBIDDEN_DIAGNOSTIC_TERMS: Final[set[str]] = {
    # Português - Termos diagnósticos
    "diagnóstico",
    "diagnostico",
    "diagnosticado",
    "hipótese diagnóstica",
    "hipotese diagnostica",
    "suspeita de",
    "sugere",
    "indica",
    "compatível com",
    "compativel com",
    "provável",
    "provavel",
    "possível",
    "possivel",
    "confirma",
    "confirmado",
    "conclusão",
    "conclusao",
    # Português - Termos clínicos inferidos
    "parece ser",
    "aparenta ser",
    "quadro de",
    "quadro clínico de",
    "quadro clinico de",
    "característico de",
    "caracteristico de",
    "típico de",
    "tipico de",
    "condizente com",
    "sugestivo de",
    "indicativo de",
    "evidencia",
    "evidência de",
    "aponta para",
    "apresenta sinais de",
    "síndrome de",
    "sindrome de",
    "doença",
    "doenca",
    "patologia",
    "etiologia",
    "prognóstico",
    "prognostico",
    # Inglês (caso LLM responda em inglês)
    "diagnosis",
    "diagnosed",
    "suspected",
    "suggests",
    "indicates",
    "compatible with",
    "probable",
    "possible",
    "confirms",
    "confirmed",
    "conclusion",
    "consistent with",
    "suggestive of",
    "indicative of",
    "disease",
    "pathology",
    "etiology",
    "prognosis",
    "syndrome",
}

# === VERSÃO DO MOTOR DE REGRAS ===

RULE_ENGINE_VERSION: Final[str] = "1.0.0"
