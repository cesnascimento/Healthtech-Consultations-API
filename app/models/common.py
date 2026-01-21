"""
Enums e tipos compartilhados para a API de Consultas.

Este módulo define enumerações e tipos base utilizados em múltiplos
modelos da aplicação, garantindo consistência e validação em todo o sistema.
"""

from enum import Enum


class BiologicalSex(str, Enum):
    """
    Sexo biológico do paciente.

    Utilizado para validações clínicas específicas (ex: gravidez)
    e cálculos de referência para sinais vitais.

    **Importante**: Este campo refere-se ao sexo biológico atribuído
    ao nascimento, não à identidade de gênero do paciente.
    """

    MALE = "male"

    FEMALE = "female"

    INTERSEX = "intersex"


class BloodType(str, Enum):
    """
    Tipo sanguíneo do paciente no sistema ABO/Rh.

    Informação crítica para procedimentos que envolvam
    transfusões ou cirurgias.
    """

    A_POSITIVE = "A+"
    A_NEGATIVE = "A-"
    B_POSITIVE = "B+"
    B_NEGATIVE = "B-"
    AB_POSITIVE = "AB+"
    AB_NEGATIVE = "AB-"
    O_POSITIVE = "O+"
    O_NEGATIVE = "O-"


class MedicationFrequency(str, Enum):
    """
    Frequência de administração de medicamentos.

    Códigos padronizados para prescrição médica,
    compatíveis com sistemas de prontuário eletrônico.
    """

    ONCE_DAILY = "1x/day"

    TWICE_DAILY = "2x/day"

    THREE_TIMES_DAILY = "3x/day"

    FOUR_TIMES_DAILY = "4x/day"

    EVERY_6_HOURS = "q6h"

    EVERY_8_HOURS = "q8h"

    EVERY_12_HOURS = "q12h"

    AS_NEEDED = "prn"

    ONCE_WEEKLY = "1x/week"

    CONTINUOUS = "continuous"


class MedicationRoute(str, Enum):
    """
    Via de administração de medicamentos.

    Define como o medicamento deve ser administrado ao paciente.
    """

    ORAL = "oral"

    SUBLINGUAL = "sublingual"

    INTRAVENOUS = "iv"

    INTRAMUSCULAR = "im"

    SUBCUTANEOUS = "sc"

    TOPICAL = "topical"

    INHALATION = "inhalation"

    OPHTHALMIC = "ophthalmic"

    OTIC = "otic"

    NASAL = "nasal"

    RECTAL = "rectal"

    TRANSDERMAL = "transdermal"


class SummarizerStrategy(str, Enum):
    """
    Estratégia utilizada para geração do resumo clínico.

    Define qual algoritmo será utilizado para processar
    os dados da consulta e gerar o resumo estruturado.

    ## Estratégias Disponíveis

    - **rule_based**: Processamento determinístico baseado em regras.
      Sempre disponível, previsível e auditável.

    - **llm_based**: Processamento com auxílio de LLM (IA).
      Opcional, requer configuração adicional. Em caso de falha,
      automaticamente utiliza fallback para `rule_based`.
    """

    RULE_BASED = "rule_based"
    """
    Resumo baseado em regras determinísticas.

    - Não utiliza inteligência artificial
    - Resultado 100% previsível e reproduzível
    - Não infere diagnósticos ou hipóteses clínicas
    - Reorganiza e normaliza os dados fornecidos
    """

    LLM_BASED = "llm_based"
    """
    Resumo com auxílio de Large Language Model.

    - Utiliza IA para estruturação do texto
    - Possui guardrails contra inferência diagnóstica
    - Fallback automático para rule_based em caso de falha
    - Requer configuração de API key
    """


class WarningLevel(str, Enum):
    """
    Nível de severidade dos warnings gerados durante o processamento.

    Warnings são alertas não-bloqueantes que indicam possíveis
    inconsistências ou pontos de atenção nos dados.

    **Nota**: Warnings nunca bloqueiam o processamento da consulta.
    São informativos e destinados à revisão humana.
    """

    INFO = "info"

    LOW = "low"

    MEDIUM = "medium"
    
    HIGH = "high"
