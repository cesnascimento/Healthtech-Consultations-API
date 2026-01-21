"""
Endpoint de health check.

Fornece verificação de saúde da aplicação para
monitoramento e orquestração de containers.
"""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.core.constants import RULE_ENGINE_VERSION

router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    """
    Resposta do health check.

    Indica o status da aplicação e informações básicas
    para monitoramento.
    """

    status: Annotated[
        str,
        Field(
            description="Status da aplicação. 'healthy' indica funcionamento normal.",
            examples=["healthy"],
        ),
    ]

    version: Annotated[
        str,
        Field(
            description="Versão da aplicação.",
            examples=["1.0.0"],
        ),
    ]

    rule_engine_version: Annotated[
        str,
        Field(
            description="Versão do motor de regras para resumos.",
            examples=["1.0.0"],
        ),
    ]

    timestamp: Annotated[
        datetime,
        Field(
            description="Timestamp UTC da verificação.",
        ),
    ]

    summarizer_strategy: Annotated[
        str,
        Field(
            description="Estratégia de resumo configurada.",
            examples=["rule_based", "llm_based"],
        ),
    ]

    llm_enabled: Annotated[
        bool,
        Field(
            description="Indica se o LLM está habilitado e configurado.",
        ),
    ]


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Verificação de saúde da API",
    description="""
Verifica se a aplicação está funcionando corretamente.

## Uso

Este endpoint deve ser utilizado para:
- Health checks de load balancers
- Probes de Kubernetes (liveness/readiness)
- Monitoramento de disponibilidade

## Resposta

Retorna informações sobre:
- Status da aplicação
- Versão do sistema
- Configuração atual do summarizer
- Timestamp da verificação

**Nota**: Este endpoint não requer autenticação.
""",
    responses={
        200: {
            "description": "Aplicação saudável",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "version": "1.0.0",
                        "rule_engine_version": "1.0.0",
                        "timestamp": "2024-01-15T14:30:00Z",
                        "summarizer_strategy": "rule_based",
                        "llm_enabled": False,
                    }
                }
            },
        }
    },
)
async def health_check() -> HealthResponse:
    """
    Retorna status de saúde da aplicação.

    Returns:
        HealthResponse com status e metadados.
    """
    settings = get_settings()

    return HealthResponse(
        status="healthy",
        version=settings.APP_VERSION,
        rule_engine_version=RULE_ENGINE_VERSION,
        timestamp=datetime.now(UTC),
        summarizer_strategy=settings.SUMMARIZER_STRATEGY,
        llm_enabled=settings.is_llm_enabled,
    )
