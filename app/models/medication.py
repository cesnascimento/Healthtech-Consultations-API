"""
Modelos relacionados a Medicamentos e Alergias.

Este módulo contém os schemas Pydantic para representação
de medicamentos em uso e alergias conhecidas do paciente.
"""

from datetime import date
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from app.models.common import MedicationFrequency, MedicationRoute


class Medication(BaseModel):
    """
    Medicamento em uso pelo paciente.

    Representa um medicamento que o paciente está utilizando,
    seja de uso contínuo ou temporário.

    ## Informações Importantes

    - O campo `active_ingredient` deve conter o princípio ativo,
      não o nome comercial (ex: "paracetamol", não "Tylenol")
    - A dosagem deve incluir a unidade (ex: "500mg", "10ml")
    - Datas de início/fim ajudam a contextualizar o tratamento

    **Nota**: Esta informação é fornecida pelo paciente ou cuidador
    e deve ser confirmada com fontes oficiais quando necessário.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "active_ingredient": "losartana potássica",
                "commercial_name": "Cozaar",
                "dosage": "50mg",
                "frequency": "1x/day",
                "route": "oral",
                "start_date": "2023-01-15",
                "end_date": None,
                "prescriber": "Dr. Carlos Mendes",
                "notes": "Tomar pela manhã em jejum",
            }
        },
    )

    active_ingredient: Annotated[
        str,
        Field(
            min_length=2,
            max_length=200,
            description=(
                "Princípio ativo do medicamento (DCB/DCI). "
                "Preferir nomenclatura padronizada. "
                "Exemplo: 'losartana potássica', não 'Cozaar'."
            ),
            examples=["losartana potássica", "metformina", "omeprazol"],
        ),
    ]

    commercial_name: Annotated[
        str | None,
        Field(
            default=None,
            max_length=200,
            description=(
                "Nome comercial/marca do medicamento. "
                "Opcional, mas útil para identificação pelo paciente."
            ),
            examples=["Cozaar", "Glifage", "Losec"],
        ),
    ]

    dosage: Annotated[
        str,
        Field(
            min_length=1,
            max_length=50,
            description=(
                "Dosagem do medicamento com unidade. "
                "Formato livre para acomodar diferentes apresentações."
            ),
            examples=["50mg", "500mg", "10ml", "2 comprimidos", "1 ampola"],
        ),
    ]

    frequency: Annotated[
        MedicationFrequency,
        Field(
            description=(
                "Frequência de administração do medicamento. "
                "Utiliza códigos padronizados compatíveis com "
                "sistemas de prescrição eletrônica."
            ),
        ),
    ]

    route: Annotated[
        MedicationRoute,
        Field(
            description=(
                "Via de administração do medicamento. "
                "Define como o medicamento é administrado ao paciente."
            ),
        ),
    ]

    start_date: Annotated[
        date | None,
        Field(
            default=None,
            description=(
                "Data de início do uso do medicamento (ISO-8601). "
                "Útil para avaliar tempo de tratamento."
            ),
            examples=["2023-01-15", "2024-06-01"],
        ),
    ]

    end_date: Annotated[
        date | None,
        Field(
            default=None,
            description=(
                "Data prevista ou efetiva de término (ISO-8601). "
                "`null` indica uso contínuo sem previsão de término."
            ),
            examples=["2024-01-15", None],
        ),
    ]

    prescriber: Annotated[
        str | None,
        Field(
            default=None,
            max_length=200,
            description=(
                "Nome do profissional que prescreveu o medicamento. "
                "Útil para rastreabilidade e contato."
            ),
            examples=["Dr. Carlos Mendes", "Dra. Ana Paula"],
        ),
    ]

    notes: Annotated[
        str | None,
        Field(
            default=None,
            max_length=500,
            description=(
                "Observações adicionais sobre o uso. "
                "Ex: horário específico, restrições alimentares, "
                "interações conhecidas."
            ),
            examples=[
                "Tomar pela manhã em jejum",
                "Evitar exposição ao sol",
                "Tomar com alimentos",
            ],
        ),
    ]


class Allergy(BaseModel):
    """
    Alergia ou intolerância conhecida do paciente.

    Representa uma reação adversa documentada a substâncias,
    medicamentos, alimentos ou outros agentes.

    ## Tipos de Reação

    - **Alérgica**: Reação imunomediada (ex: anafilaxia, urticária)
    - **Intolerância**: Reação não-imunomediada (ex: intolerância à lactose)
    - **Adversa**: Efeito colateral conhecido (ex: náusea com antibiótico)

    **Atenção**: Alergias a medicamentos devem ser destacadas
    e verificadas antes de qualquer prescrição.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "allergen": "penicilina",
                "reaction_type": "allergic",
                "severity": "severe",
                "reaction_description": "Edema de glote e urticária generalizada",
                "diagnosed_date": "2018-05-20",
                "confirmed": True,
            }
        },
    )

    allergen: Annotated[
        str,
        Field(
            min_length=2,
            max_length=200,
            description=(
                "Substância causadora da reação. "
                "Pode ser medicamento, alimento, substância química, etc."
            ),
            examples=[
                "penicilina",
                "dipirona",
                "frutos do mar",
                "látex",
                "contraste iodado",
            ],
        ),
    ]

    reaction_type: Annotated[
        str,
        Field(
            pattern=r"^(allergic|intolerance|adverse)$",
            description=(
                "Tipo de reação apresentada. "
                "`allergic` = reação imunomediada, "
                "`intolerance` = reação não-imunomediada, "
                "`adverse` = efeito colateral."
            ),
            examples=["allergic", "intolerance", "adverse"],
        ),
    ]

    severity: Annotated[
        str,
        Field(
            pattern=r"^(mild|moderate|severe|life_threatening)$",
            description=(
                "Gravidade da reação. "
                "`mild` = leve (ex: coceira local), "
                "`moderate` = moderada (ex: urticária), "
                "`severe` = grave (ex: edema de glote), "
                "`life_threatening` = risco de vida (ex: anafilaxia)."
            ),
            examples=["mild", "moderate", "severe", "life_threatening"],
        ),
    ]

    reaction_description: Annotated[
        str | None,
        Field(
            default=None,
            max_length=500,
            description=(
                "Descrição detalhada da reação apresentada. "
                "Incluir sintomas, tempo de início, duração."
            ),
            examples=[
                "Edema de glote e urticária generalizada",
                "Náuseas e vômitos após 30 minutos",
                "Prurido local e vermelhidão",
            ],
        ),
    ]

    diagnosed_date: Annotated[
        date | None,
        Field(
            default=None,
            description=(
                "Data do diagnóstico ou primeira ocorrência (ISO-8601). "
                "Útil para histórico temporal."
            ),
            examples=["2018-05-20", "2020-11-03"],
        ),
    ]

    confirmed: Annotated[
        bool,
        Field(
            default=False,
            description=(
                "Indica se a alergia foi confirmada por teste diagnóstico. "
                "`true` = confirmada por exame, "
                "`false` = relatada pelo paciente sem confirmação laboratorial."
            ),
        ),
    ]
