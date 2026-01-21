"""
Modelos de Request e Response para o endpoint de Consultas.

Este módulo contém os schemas principais para:
- ConsultationCreate: Payload de entrada (request)
- ConsultationSummary: Resposta estruturada (response)
- Modelos auxiliares de metadados e warnings
"""

from datetime import date, datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.common import BiologicalSex, SummarizerStrategy, WarningLevel
from app.models.medication import Allergy, Medication
from app.models.patient import Patient, VitalSigns


class ConsultationCreate(BaseModel):
    """
    Payload para criação de resumo de consulta médica.

    Este é o schema de entrada principal do endpoint `POST /consultations`.
    Contém todos os dados estruturados coletados durante uma consulta médica.

    ## Estrutura dos Dados

    O payload é organizado em seções lógicas:

    1. **Identificação**: Dados do paciente e profissional
    2. **Contexto**: Data, local, tipo de atendimento
    3. **Anamnese**: Queixa, história, antecedentes
    4. **Exame**: Sinais vitais e achados físicos
    5. **Conduta**: Plano terapêutico proposto

    ## Campos Obrigatórios

    - `patient`: Dados do paciente
    - `consultation_date`: Data da consulta
    - `chief_complaint`: Queixa principal
    - `professional_name`: Nome do profissional

    ## Validações Automáticas

    O sistema valida automaticamente:
    - Faixas de valores para sinais vitais
    - Consistência entre campos (ex: gravidez vs sexo biológico)
    - Formato de datas (ISO-8601)
    - Tamanho máximo de textos

    **Nota**: Campos extras não declarados são rejeitados (`extra="forbid"`).
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "patient": {
                    "full_name": "Maria Silva Santos",
                    "cpf": "123.456.789-00",
                    "birth_date": "1985-03-15",
                    "biological_sex": "female",
                    "blood_type": "O+",
                    "is_pregnant": False,
                },
                "consultation_date": "2024-01-15",
                "consultation_type": "follow_up",
                "chief_complaint": "Dor de cabeça persistente há 3 dias",
                "history_present_illness": (
                    "Paciente refere cefaleia holocraniana de intensidade "
                    "moderada (6/10) iniciada há 3 dias. Piora no final do dia. "
                    "Nega náuseas, vômitos ou fotofobia. Associa início dos "
                    "sintomas com período de estresse no trabalho."
                ),
                "vital_signs": {
                    "systolic_bp": 130,
                    "diastolic_bp": 85,
                    "heart_rate": 78,
                    "respiratory_rate": 16,
                    "temperature_celsius": 36.5,
                    "oxygen_saturation": 98,
                    "pain_scale": 6,
                },
                "current_medications": [
                    {
                        "active_ingredient": "losartana potássica",
                        "dosage": "50mg",
                        "frequency": "1x/day",
                        "route": "oral",
                    }
                ],
                "allergies": [
                    {
                        "allergen": "dipirona",
                        "reaction_type": "allergic",
                        "severity": "moderate",
                        "reaction_description": "Urticária generalizada",
                        "confirmed": True,
                    }
                ],
                "past_medical_history": ["Hipertensão arterial sistêmica (2018)"],
                "family_history": ["Mãe: AVC aos 65 anos", "Pai: Diabetes tipo 2"],
                "social_history": "Não tabagista. Etilismo social. Sedentária.",
                "physical_examination": (
                    "BEG, corada, hidratada, anictérica, acianótica. "
                    "ACV: RCR 2T BNF sem sopros. "
                    "AR: MV+ bilateral sem RA. "
                    "Neurológico: Glasgow 15, pupilas isocóricas e fotorreagentes."
                ),
                "professional_name": "Dr. João Pedro Oliveira",
                "professional_council_id": "CRM-SP 123456",
                "specialty": "Clínica Médica",
                "treatment_plan": (
                    "1. Orientações sobre higiene do sono\n"
                    "2. Paracetamol 750mg VO 6/6h se dor\n"
                    "3. Retorno em 7 dias se persistência dos sintomas"
                ),
                "strategy": "rule_based",
            }
        },
    )

    # === IDENTIFICAÇÃO DO PACIENTE ===

    patient: Annotated[
        Patient,
        Field(
            description=(
                "Dados completos do paciente. "
                "Inclui identificação, dados demográficos e informações "
                "clínicas básicas como tipo sanguíneo e status gestacional."
            ),
        ),
    ]

    # === CONTEXTO DA CONSULTA ===

    consultation_date: Annotated[
        date,
        Field(
            description=(
                "Data em que a consulta foi realizada (ISO-8601). "
                "Não pode ser data futura."
            ),
            examples=["2024-01-15", "2024-02-28"],
        ),
    ]

    consultation_type: Annotated[
        str,
        Field(
            default="first_visit",
            pattern=r"^(first_visit|follow_up|emergency|telemedicine|routine)$",
            description=(
                "Tipo de consulta realizada. "
                "`first_visit` = primeira consulta, "
                "`follow_up` = retorno, "
                "`emergency` = emergência, "
                "`telemedicine` = teleconsulta, "
                "`routine` = rotina/check-up."
            ),
            examples=["first_visit", "follow_up", "emergency"],
        ),
    ]

    facility_name: Annotated[
        str | None,
        Field(
            default=None,
            max_length=200,
            description=(
                "Nome do estabelecimento de saúde onde a consulta ocorreu. "
                "Opcional para consultórios individuais."
            ),
            examples=["Hospital São Lucas", "Clínica Vida", "UBS Centro"],
        ),
    ]

    # === ANAMNESE ===

    chief_complaint: Annotated[
        str,
        Field(
            min_length=5,
            max_length=500,
            description=(
                "Queixa principal do paciente em suas próprias palavras. "
                "Deve ser breve e direta, indicando o motivo da consulta. "
                "**Campo obrigatório**."
            ),
            examples=[
                "Dor de cabeça persistente há 3 dias",
                "Tosse seca há 1 semana",
                "Dor no peito ao esforço",
            ],
        ),
    ]

    history_present_illness: Annotated[
        str | None,
        Field(
            default=None,
            max_length=5000,
            description=(
                "História da doença atual (HDA). "
                "Descrição detalhada da evolução dos sintomas: "
                "início, duração, intensidade, fatores de melhora/piora, "
                "sintomas associados. "
                "Texto será truncado se exceder 2000 caracteres no resumo."
            ),
            examples=[
                (
                    "Paciente refere cefaleia holocraniana de intensidade "
                    "moderada (6/10) iniciada há 3 dias. Piora no final do dia."
                )
            ],
        ),
    ]

    # === SINAIS VITAIS E EXAME FÍSICO ===

    vital_signs: Annotated[
        VitalSigns | None,
        Field(
            default=None,
            description=(
                "Sinais vitais medidos durante a consulta. "
                "Valores fora das faixas de referência geram warnings. "
                "Todos os campos são opcionais individualmente."
            ),
        ),
    ]

    physical_examination: Annotated[
        str | None,
        Field(
            default=None,
            max_length=5000,
            description=(
                "Achados do exame físico. "
                "Descrição sistematizada por aparelhos/sistemas. "
                "Recomenda-se seguir ordem: geral, cabeça/pescoço, "
                "cardiovascular, respiratório, abdominal, neurológico, etc."
            ),
            examples=[
                (
                    "BEG, corada, hidratada. ACV: RCR 2T BNF sem sopros. "
                    "AR: MV+ bilateral sem RA."
                )
            ],
        ),
    ]

    # === HISTÓRICO E MEDICAMENTOS ===

    current_medications: Annotated[
        list[Medication],
        Field(
            default_factory=list,
            max_length=50,
            description=(
                "Lista de medicamentos em uso atual pelo paciente. "
                "Inclui medicamentos contínuos e temporários. "
                "Máximo de 50 medicamentos por consulta."
            ),
        ),
    ]

    allergies: Annotated[
        list[Allergy],
        Field(
            default_factory=list,
            max_length=30,
            description=(
                "Alergias e intolerâncias conhecidas do paciente. "
                "Incluir medicamentos, alimentos e outras substâncias. "
                "**Crítico**: Verificar antes de prescrições."
            ),
        ),
    ]

    past_medical_history: Annotated[
        list[str],
        Field(
            default_factory=list,
            max_length=50,
            description=(
                "Antecedentes patológicos pessoais. "
                "Lista de doenças e condições prévias relevantes. "
                "Incluir ano do diagnóstico quando conhecido."
            ),
            examples=[
                ["Hipertensão arterial sistêmica (2018)", "Apendicectomia (2010)"]
            ],
        ),
    ]

    family_history: Annotated[
        list[str],
        Field(
            default_factory=list,
            max_length=30,
            description=(
                "Antecedentes familiares relevantes. "
                "Incluir parentesco e idade de início quando conhecido."
            ),
            examples=[["Mãe: AVC aos 65 anos", "Pai: Diabetes tipo 2"]],
        ),
    ]

    social_history: Annotated[
        str | None,
        Field(
            default=None,
            max_length=1000,
            description=(
                "História social do paciente. "
                "Incluir: tabagismo, etilismo, atividade física, "
                "ocupação, condições de moradia quando relevante."
            ),
            examples=["Não tabagista. Etilismo social. Sedentária."],
        ),
    ]

    # === PROFISSIONAL E CONDUTA ===

    professional_name: Annotated[
        str,
        Field(
            min_length=3,
            max_length=200,
            description=(
                "Nome completo do profissional responsável pela consulta. "
                "**Campo obrigatório**."
            ),
            examples=["Dr. João Pedro Oliveira", "Dra. Maria Santos"],
        ),
    ]

    professional_council_id: Annotated[
        str | None,
        Field(
            default=None,
            max_length=50,
            pattern=r"^(CRM|CRO|COREN|CRF|CREFITO)-[A-Z]{2}\s?\d{4,8}$",
            description=(
                "Registro no conselho profissional. "
                "Formato: CONSELHO-UF NÚMERO. "
                "Ex: CRM-SP 123456, COREN-RJ 12345."
            ),
            examples=["CRM-SP 123456", "COREN-RJ 12345"],
        ),
    ]

    specialty: Annotated[
        str | None,
        Field(
            default=None,
            max_length=100,
            description="Especialidade médica do profissional.",
            examples=["Clínica Médica", "Cardiologia", "Pediatria"],
        ),
    ]

    treatment_plan: Annotated[
        str | None,
        Field(
            default=None,
            max_length=5000,
            description=(
                "Plano terapêutico proposto. "
                "Incluir orientações, prescrições e encaminhamentos. "
                "**Nota**: Este campo descreve conduta proposta, "
                "não representa diagnóstico."
            ),
            examples=[
                "1. Orientações sobre higiene do sono\n"
                "2. Paracetamol 750mg VO 6/6h se dor\n"
                "3. Retorno em 7 dias"
            ],
        ),
    ]

    additional_notes: Annotated[
        str | None,
        Field(
            default=None,
            max_length=2000,
            description=(
                "Observações adicionais livres. "
                "Informações que não se encaixam em outros campos."
            ),
        ),
    ]

    # === ESTRATÉGIA DE PROCESSAMENTO ===

    strategy: Annotated[
        SummarizerStrategy,
        Field(
            default=SummarizerStrategy.RULE_BASED,
            description=(
                "Estratégia para geração do resumo clínico. "
                "\n\n"
                "**rule_based** (padrão): Processamento determinístico baseado "
                "em regras. Sempre disponível, 100% previsível.\n\n"
                "**llm_based**: Processamento com auxílio de IA. "
                "Requer configuração. Fallback automático para rule_based "
                "em caso de falha."
            ),
        ),
    ]

    @field_validator("past_medical_history", "family_history", mode="after")
    @classmethod
    def validate_history_items(cls, v: list[str]) -> list[str]:
        """Remove itens vazios e normaliza espaços."""
        return [item.strip() for item in v if item and item.strip()]

    @model_validator(mode="after")
    def validate_pregnancy_consistency(self) -> "ConsultationCreate":
        """Valida consistência entre gravidez e sexo biológico."""
        if self.patient.is_pregnant and self.patient.biological_sex == BiologicalSex.MALE:
            raise ValueError(
                "Inconsistência: is_pregnant=true não é válido para biological_sex=male"
            )

        if self.patient.is_pregnant and self.patient.gestational_weeks is None:
            raise ValueError(
                "gestational_weeks é obrigatório quando is_pregnant=true"
            )

        return self


class ConsultationWarning(BaseModel):
    """
    Warning gerado durante o processamento da consulta.

    Warnings são alertas não-bloqueantes que indicam possíveis
    inconsistências ou pontos de atenção nos dados fornecidos.

    **Importante**: Warnings nunca impedem o processamento.
    São informativos e destinados à revisão humana posterior.

    ## Exemplos de Warnings

    - Sinais vitais fora da faixa de referência
    - Campos de texto truncados
    - Duplicatas removidas
    - Dados opcionais ausentes
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "code": "VITAL_SIGNS_OUT_OF_RANGE",
                "level": "medium",
                "message": "Pressão arterial sistólica (180 mmHg) acima do esperado",
                "field": "vital_signs.systolic_bp",
                "value": "180",
            }
        },
    )

    code: Annotated[
        str,
        Field(
            description=(
                "Código único do warning para identificação programática. "
                "Formato: CATEGORIA_DESCRICAO em SCREAMING_SNAKE_CASE."
            ),
            examples=[
                "VITAL_SIGNS_OUT_OF_RANGE",
                "TEXT_TRUNCATED",
                "DUPLICATE_REMOVED",
                "MISSING_OPTIONAL_FIELD",
            ],
        ),
    ]

    level: Annotated[
        WarningLevel,
        Field(
            description=(
                "Nível de severidade do warning. "
                "Indica a importância relativa para revisão humana."
            ),
        ),
    ]

    message: Annotated[
        str,
        Field(
            max_length=500,
            description=(
                "Mensagem descritiva do warning em português. "
                "Deve ser clara e acionável."
            ),
            examples=[
                "Pressão arterial sistólica (180 mmHg) acima do esperado",
                "Campo 'history_present_illness' truncado para 2000 caracteres",
            ],
        ),
    ]

    field: Annotated[
        str | None,
        Field(
            default=None,
            description=(
                "Caminho do campo relacionado ao warning (dot notation). "
                "`null` se o warning for geral."
            ),
            examples=[
                "vital_signs.systolic_bp",
                "patient.birth_date",
                "current_medications[0].dosage",
            ],
        ),
    ]

    value: Annotated[
        str | None,
        Field(
            default=None,
            max_length=200,
            description=(
                "Valor que gerou o warning (convertido para string). "
                "Útil para debugging e auditoria."
            ),
            examples=["180", "2024-01-15", "null"],
        ),
    ]


class SummarySection(BaseModel):
    """
    Seção individual do resumo clínico estruturado.

    O resumo é dividido em seções padronizadas para facilitar
    a leitura e integração com outros sistemas.

    ## Seções Padrão

    1. **identification**: Identificação do paciente
    2. **complaint_history**: Queixa e história da doença
    3. **vital_signs**: Sinais vitais formatados
    4. **background**: Antecedentes pessoais, familiares e alergias
    5. **physical_exam**: Exame físico (quando presente)
    6. **assessment**: Avaliação clínica (sem diagnóstico)
    7. **plan**: Plano terapêutico (quando presente)
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "title": "Sinais Vitais",
                "code": "vital_signs",
                "content": (
                    "PA: 130x85 mmHg | FC: 78 bpm | FR: 16 irpm | "
                    "Tax: 36.5°C | SpO2: 98% | Dor: 6/10"
                ),
                "order": 3,
            }
        },
    )

    title: Annotated[
        str,
        Field(
            max_length=100,
            description="Título da seção em português para exibição.",
            examples=[
                "Identificação",
                "Queixa e História",
                "Sinais Vitais",
                "Antecedentes",
            ],
        ),
    ]

    code: Annotated[
        str,
        Field(
            pattern=r"^[a-z_]+$",
            description=(
                "Código da seção para identificação programática. "
                "Formato: snake_case."
            ),
            examples=[
                "identification",
                "complaint_history",
                "vital_signs",
                "background",
            ],
        ),
    ]

    content: Annotated[
        str,
        Field(
            max_length=3000,
            description=(
                "Conteúdo textual da seção. "
                "Formatado para leitura humana."
            ),
        ),
    ]

    order: Annotated[
        int,
        Field(
            ge=1,
            le=20,
            description=(
                "Ordem de exibição da seção no resumo. "
                "Permite ordenação consistente."
            ),
        ),
    ]


class SummaryMetadata(BaseModel):
    """
    Metadados de auditoria do processamento da consulta.

    Contém informações técnicas sobre como o resumo foi gerado,
    permitindo rastreabilidade e auditoria completa.

    ## Campos de Auditoria

    - `request_id`: Identificador único da requisição
    - `strategy_used`: Estratégia efetivamente utilizada
    - `rule_engine_version`: Versão do motor de regras
    - `processed_at`: Timestamp do processamento
    - `processing_time_ms`: Tempo de processamento

    **Nota**: Se `strategy_used` = "llm_fallback", indica que
    a estratégia LLM falhou e o sistema utilizou rule_based.
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "request_id": "550e8400-e29b-41d4-a716-446655440000",
                "strategy_used": "rule_based",
                "strategy_requested": "rule_based",
                "rule_engine_version": "1.0.0",
                "processed_at": "2024-01-15T14:30:00Z",
                "processing_time_ms": 45,
                "llm_model": None,
                "fallback_reason": None,
            }
        },
    )

    request_id: Annotated[
        UUID,
        Field(
            description=(
                "Identificador único da requisição (UUIDv4). "
                "Gerado automaticamente para rastreabilidade."
            ),
        ),
    ]

    strategy_used: Annotated[
        str,
        Field(
            pattern=r"^(rule_based|llm_based|llm_fallback)$",
            description=(
                "Estratégia efetivamente utilizada no processamento. "
                "`llm_fallback` indica que LLM falhou e rule_based foi usado."
            ),
            examples=["rule_based", "llm_based", "llm_fallback"],
        ),
    ]

    strategy_requested: Annotated[
        SummarizerStrategy,
        Field(
            description="Estratégia originalmente solicitada na requisição.",
        ),
    ]

    rule_engine_version: Annotated[
        str,
        Field(
            pattern=r"^\d+\.\d+\.\d+$",
            description=(
                "Versão do motor de regras utilizado. "
                "Segue versionamento semântico (SemVer)."
            ),
            examples=["1.0.0", "1.2.3"],
        ),
    ]

    processed_at: Annotated[
        datetime,
        Field(
            description=(
                "Timestamp UTC do momento do processamento (ISO-8601). "
                "Formato: YYYY-MM-DDTHH:MM:SSZ."
            ),
        ),
    ]

    processing_time_ms: Annotated[
        int,
        Field(
            ge=0,
            description="Tempo de processamento em milissegundos.",
            examples=[45, 120, 2500],
        ),
    ]

    llm_model: Annotated[
        str | None,
        Field(
            default=None,
            description=(
                "Modelo de LLM utilizado (quando strategy_used = llm_based). "
                "`null` se rule_based foi utilizado."
            ),
            examples=["gemini-1.5-flash", "gemini-1.5-pro", None],
        ),
    ]

    fallback_reason: Annotated[
        str | None,
        Field(
            default=None,
            max_length=500,
            description=(
                "Motivo do fallback para rule_based (quando aplicável). "
                "`null` se não houve fallback."
            ),
            examples=[
                "LLM timeout after 10000ms",
                "LLM response failed JSON validation",
                "Diagnostic terms detected in LLM output",
                None,
            ],
        ),
    ]


class ConsultationSummary(BaseModel):
    """
    Resposta do endpoint de processamento de consulta.

    Contém o resumo clínico estruturado, warnings gerados
    durante o processamento e metadados de auditoria.

    ## Estrutura da Resposta

    ```json
    {
      "summary": {
        "sections": [...],      // Seções do resumo
        "full_text": "..."      // Texto completo concatenado
      },
      "warnings": [...],        // Alertas gerados
      "metadata": {...}         // Auditoria
    }
    ```

    ## Garantias

    - O resumo **nunca** contém diagnósticos inferidos
    - O resumo **apenas** reorganiza dados fornecidos
    - Warnings são informativos, nunca bloqueantes
    - Metadata permite auditoria completa
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "summary": {
                    "sections": [
                        {
                            "title": "Identificação",
                            "code": "identification",
                            "content": (
                                "Paciente: Maria Silva Santos | "
                                "CPF: 123.456.789-00 | "
                                "Nascimento: 15/03/1985 (38 anos) | "
                                "Sexo: Feminino | "
                                "Tipo sanguíneo: O+"
                            ),
                            "order": 1,
                        },
                        {
                            "title": "Queixa e História",
                            "code": "complaint_history",
                            "content": (
                                "Queixa principal: Dor de cabeça persistente há 3 dias\n\n"
                                "HDA: Paciente refere cefaleia holocraniana de intensidade "
                                "moderada (6/10) iniciada há 3 dias. Piora no final do dia. "
                                "Nega náuseas, vômitos ou fotofobia."
                            ),
                            "order": 2,
                        },
                        {
                            "title": "Sinais Vitais",
                            "code": "vital_signs",
                            "content": (
                                "PA: 130x85 mmHg | FC: 78 bpm | FR: 16 irpm | "
                                "Tax: 36.5°C | SpO2: 98% | Dor: 6/10"
                            ),
                            "order": 3,
                        },
                    ],
                    "full_text": (
                        "=== IDENTIFICAÇÃO ===\n"
                        "Paciente: Maria Silva Santos | CPF: 123.456.789-00\n\n"
                        "=== QUEIXA E HISTÓRIA ===\n"
                        "Queixa principal: Dor de cabeça persistente há 3 dias\n\n"
                        "=== SINAIS VITAIS ===\n"
                        "PA: 130x85 mmHg | FC: 78 bpm"
                    ),
                },
                "warnings": [
                    {
                        "code": "BLOOD_PRESSURE_ELEVATED",
                        "level": "low",
                        "message": "Pressão arterial levemente elevada (130x85 mmHg)",
                        "field": "vital_signs.systolic_bp",
                        "value": "130",
                    }
                ],
                "metadata": {
                    "request_id": "550e8400-e29b-41d4-a716-446655440000",
                    "strategy_used": "rule_based",
                    "strategy_requested": "rule_based",
                    "rule_engine_version": "1.0.0",
                    "processed_at": "2024-01-15T14:30:00Z",
                    "processing_time_ms": 45,
                    "llm_model": None,
                    "fallback_reason": None,
                },
            }
        },
    )

    summary: Annotated[
        "SummaryContent",
        Field(
            description=(
                "Resumo clínico estruturado gerado a partir dos dados da consulta. "
                "Contém seções organizadas e texto completo concatenado."
            ),
        ),
    ]

    warnings: Annotated[
        list[ConsultationWarning],
        Field(
            default_factory=list,
            description=(
                "Lista de warnings gerados durante o processamento. "
                "Warnings são informativos e não bloqueiam o processamento. "
                "Lista vazia indica processamento sem alertas."
            ),
        ),
    ]

    metadata: Annotated[
        SummaryMetadata,
        Field(
            description=(
                "Metadados de auditoria do processamento. "
                "Contém informações técnicas para rastreabilidade."
            ),
        ),
    ]


class SummaryContent(BaseModel):
    """
    Conteúdo do resumo clínico.

    Agrupa as seções estruturadas e o texto completo
    para flexibilidade de consumo.

    ## Formatos Disponíveis

    - **sections**: Lista de seções para renderização estruturada
    - **full_text**: Texto único para visualização simples ou cópia
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    sections: Annotated[
        list[SummarySection],
        Field(
            description=(
                "Lista de seções do resumo em ordem de exibição. "
                "Cada seção tem título, código, conteúdo e ordem."
            ),
        ),
    ]

    full_text: Annotated[
        str,
        Field(
            max_length=15000,
            description=(
                "Texto completo do resumo com todas as seções concatenadas. "
                "Formato legível para cópia/impressão."
            ),
        ),
    ]
