"""
Modelos relacionados ao Paciente e Sinais Vitais.

Este módulo contém os schemas Pydantic para representação
de dados do paciente e suas medições vitais durante a consulta.
"""

from datetime import date
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.common import BiologicalSex, BloodType


class VitalSigns(BaseModel):
    """
    Sinais vitais do paciente no momento da consulta.

    Representa as medições fisiológicas básicas coletadas
    durante a avaliação inicial do paciente.

    ## Faixas de Referência (Adultos)

    | Sinal | Normal | Atenção |
    |-------|--------|---------|
    | Pressão Sistólica | 90-120 mmHg | >140 ou <90 |
    | Pressão Diastólica | 60-80 mmHg | >90 ou <60 |
    | Freq. Cardíaca | 60-100 bpm | >100 ou <60 |
    | Freq. Respiratória | 12-20 irpm | >20 ou <12 |
    | Temperatura | 36.0-37.5°C | >38.0 ou <35.5 |
    | SpO2 | 95-100% | <94% |

    **Nota**: Faixas de referência variam por idade e condição clínica.
    Warnings são gerados automaticamente para valores fora do esperado.
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "systolic_bp": 120,
                "diastolic_bp": 80,
                "heart_rate": 72,
                "respiratory_rate": 16,
                "temperature_celsius": 36.5,
                "oxygen_saturation": 98,
                "pain_scale": 3,
            }
        },
    )

    systolic_bp: Annotated[
        int | None,
        Field(
            default=None,
            ge=40,
            le=300,
            description=(
                "Pressão arterial sistólica em mmHg. "
                "Valor máximo durante a contração cardíaca. "
                "Faixa normal adulto: 90-120 mmHg."
            ),
            examples=[120, 135, 90],
            json_schema_extra={"unit": "mmHg"},
        ),
    ]

    diastolic_bp: Annotated[
        int | None,
        Field(
            default=None,
            ge=20,
            le=200,
            description=(
                "Pressão arterial diastólica em mmHg. "
                "Valor mínimo durante o relaxamento cardíaco. "
                "Faixa normal adulto: 60-80 mmHg."
            ),
            examples=[80, 85, 60],
            json_schema_extra={"unit": "mmHg"},
        ),
    ]

    heart_rate: Annotated[
        int | None,
        Field(
            default=None,
            ge=20,
            le=300,
            description=(
                "Frequência cardíaca em batimentos por minuto (bpm). "
                "Faixa normal adulto em repouso: 60-100 bpm."
            ),
            examples=[72, 88, 65],
            json_schema_extra={"unit": "bpm"},
        ),
    ]

    respiratory_rate: Annotated[
        int | None,
        Field(
            default=None,
            ge=4,
            le=60,
            description=(
                "Frequência respiratória em incursões por minuto (irpm). "
                "Faixa normal adulto: 12-20 irpm."
            ),
            examples=[16, 18, 14],
            json_schema_extra={"unit": "irpm"},
        ),
    ]

    temperature_celsius: Annotated[
        float | None,
        Field(
            default=None,
            ge=30.0,
            le=45.0,
            description=(
                "Temperatura corporal em graus Celsius. "
                "Faixa normal: 36.0-37.5°C. "
                "Febre: ≥37.8°C. Hipotermia: <35.0°C."
            ),
            examples=[36.5, 37.2, 38.5],
            json_schema_extra={"unit": "°C"},
        ),
    ]

    oxygen_saturation: Annotated[
        int | None,
        Field(
            default=None,
            ge=50,
            le=100,
            description=(
                "Saturação de oxigênio (SpO2) em porcentagem. "
                "Medida por oximetria de pulso. "
                "Normal: ≥95%. Hipoxemia: <94%."
            ),
            examples=[98, 96, 92],
            json_schema_extra={"unit": "%"},
        ),
    ]

    pain_scale: Annotated[
        int | None,
        Field(
            default=None,
            ge=0,
            le=10,
            description=(
                "Escala numérica de dor de 0 a 10. "
                "0 = sem dor, 10 = pior dor imaginável. "
                "Baseado na Escala Visual Analógica (EVA)."
            ),
            examples=[0, 3, 7],
        ),
    ]

    weight_kg: Annotated[
        float | None,
        Field(
            default=None,
            ge=0.5,
            le=500.0,
            description="Peso do paciente em quilogramas.",
            examples=[70.5, 85.0, 62.3],
            json_schema_extra={"unit": "kg"},
        ),
    ]

    height_cm: Annotated[
        float | None,
        Field(
            default=None,
            ge=30.0,
            le=280.0,
            description="Altura do paciente em centímetros.",
            examples=[175.0, 162.5, 180.0],
            json_schema_extra={"unit": "cm"},
        ),
    ]

    @field_validator("systolic_bp", "diastolic_bp", mode="after")
    @classmethod
    def validate_bp_relationship(cls, v: int | None) -> int | None:
        """Valida que a pressão foi fornecida."""
        return v


class Patient(BaseModel):
    """
    Dados de identificação e características do paciente.

    Contém informações demográficas e clínicas básicas
    necessárias para contextualização da consulta.

    ## Campos Sensíveis (LGPD)

    Os seguintes campos são considerados dados sensíveis:
    - `cpf`: Documento de identificação pessoal
    - `birth_date`: Permite cálculo de idade
    - `full_name`: Identificação nominal

    **Atenção**: Todos os dados devem ser tratados conforme
    a Lei Geral de Proteção de Dados (LGPD).
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "full_name": "Maria Silva Santos",
                "cpf": "123.456.789-00",
                "birth_date": "1985-03-15",
                "biological_sex": "female",
                "blood_type": "O+",
                "is_pregnant": False,
                "gestational_weeks": None,
            }
        },
    )

    full_name: Annotated[
        str,
        Field(
            min_length=2,
            max_length=200,
            description=(
                "Nome completo do paciente conforme documento de identidade. "
                "Utilizado para identificação inequívoca no sistema."
            ),
            examples=["Maria Silva Santos", "João Pedro Oliveira"],
        ),
    ]

    cpf: Annotated[
        str,
        Field(
            pattern=r"^\d{3}\.\d{3}\.\d{3}-\d{2}$",
            description=(
                "CPF do paciente no formato XXX.XXX.XXX-XX. "
                "**Campo sensível (LGPD)**. "
                "Utilizado como identificador único do paciente."
            ),
            examples=["123.456.789-00", "987.654.321-00"],
        ),
    ]

    birth_date: Annotated[
        date,
        Field(
            description=(
                "Data de nascimento no formato ISO-8601 (YYYY-MM-DD). "
                "Utilizada para cálculo de idade e validações clínicas "
                "específicas por faixa etária."
            ),
            examples=["1985-03-15", "1990-07-22", "2010-12-01"],
        ),
    ]

    biological_sex: Annotated[
        BiologicalSex,
        Field(
            description=(
                "Sexo biológico atribuído ao nascimento. "
                "Utilizado para validações clínicas específicas "
                "(ex: impossibilidade de gravidez em sexo masculino) "
                "e referências de sinais vitais."
            ),
        ),
    ]

    blood_type: Annotated[
        BloodType | None,
        Field(
            default=None,
            description=(
                "Tipo sanguíneo no sistema ABO/Rh. "
                "Informação importante para procedimentos "
                "que envolvam transfusões."
            ),
        ),
    ]

    is_pregnant: Annotated[
        bool,
        Field(
            default=False,
            description=(
                "Indica se a paciente está gestante. "
                "**Validação**: Não pode ser `true` se `biological_sex` for `male`. "
                "Impacta prescrições e procedimentos contraindicados na gravidez."
            ),
        ),
    ]

    gestational_weeks: Annotated[
        int | None,
        Field(
            default=None,
            ge=1,
            le=45,
            description=(
                "Idade gestacional em semanas completas. "
                "Obrigatório se `is_pregnant` for `true`. "
                "Faixa válida: 1-45 semanas."
            ),
            examples=[12, 28, 36],
        ),
    ]

    @field_validator("full_name", mode="after")
    @classmethod
    def normalize_name(cls, v: str) -> str:
        """Normaliza o nome removendo espaços extras."""
        return " ".join(v.split())
