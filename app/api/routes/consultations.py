from fastapi import APIRouter, HTTPException, status

from app.models.common import SummarizerStrategy
from app.models.consultation import (
    ConsultationCreate,
    ConsultationSummary,
    SummaryContent,
)
from app.services.summarizers import get_summarizer
from app.utils.audit import AuditGenerator
from pydantic import BaseModel, Field

router = APIRouter(prefix="/consultations", tags=["Consultas"])


class ValidationErrorDetail(BaseModel):
    loc: list[str | int] = Field(description="Localização do erro no payload")
    msg: str = Field(description="Mensagem de erro")
    type: str = Field(description="Tipo do erro")


class ValidationErrorResponse(BaseModel):
    detail: list[ValidationErrorDetail] = Field(
        description="Lista de erros de validação"
    )


class ErrorResponse(BaseModel):
    detail: str = Field(description="Mensagem de erro")
    code: str = Field(description="Código do erro")


@router.post(
    "",
    response_model=ConsultationSummary,
    status_code=status.HTTP_200_OK,
    summary="Processa consulta médica e gera resumo clínico",
    description="""
Recebe dados estruturados de uma consulta médica e gera um resumo clínico
organizado em seções padronizadas.

## Funcionalidade

Este endpoint:
1. **Valida** rigorosamente o payload de entrada
2. **Processa** os dados usando a estratégia selecionada
3. **Gera** um resumo estruturado em seções
4. **Retorna** warnings e metadados de auditoria

## Estratégias de Resumo

### rule_based (padrão)
- Processamento 100% determinístico
- Não utiliza inteligência artificial
- Não infere diagnósticos ou hipóteses clínicas
- Apenas reorganiza e normaliza os dados fornecidos
- **Sempre disponível**

### llm_based (opcional)
- Utiliza LLM (Gemini) para estruturação
- Possui guardrails contra inferência diagnóstica
- **Fallback automático** para rule_based em caso de falha
- Requer configuração de API key no servidor

## Seções do Resumo

O resumo é organizado nas seguintes seções:

| Ordem | Seção | Descrição |
|-------|-------|-----------|
| 1 | Identificação | Dados do paciente e da consulta |
| 2 | Queixa e História | Queixa principal e HDA |
| 3 | Sinais Vitais | Medições vitais formatadas |
| 4 | Antecedentes | Alergias, medicamentos, histórico |
| 5 | Exame Físico | Achados do exame (se presente) |
| 6 | Avaliação | Contexto clínico (sem diagnóstico) |
| 7 | Plano | Conduta proposta (se presente) |

## Warnings

Warnings são alertas **não-bloqueantes** gerados durante o processamento:
- Valores fora das faixas de referência
- Inconsistências nos dados
- Campos truncados ou duplicados
- Dados importantes ausentes

**Importante**: Warnings nunca impedem o processamento.

## Auditoria

Cada resposta inclui metadados para rastreabilidade:
- `request_id`: UUID único da requisição
- `strategy_used`: Estratégia efetivamente utilizada
- `processed_at`: Timestamp do processamento
- `processing_time_ms`: Tempo de processamento

## Campos Sensíveis (LGPD)

Os seguintes campos contêm dados sensíveis:
- `patient.cpf`: Documento de identificação
- `patient.full_name`: Nome completo
- `patient.birth_date`: Data de nascimento

Trate esses dados conforme a LGPD.

## Exemplo de Uso

```bash
curl -X POST "http://localhost:8000/consultations" \\
  -H "Content-Type: application/json" \\
  -d '{
    "patient": {
      "full_name": "Maria Silva",
      "cpf": "123.456.789-00",
      "birth_date": "1985-03-15",
      "biological_sex": "female"
    },
    "consultation_date": "2024-01-15",
    "chief_complaint": "Dor de cabeça há 3 dias",
    "professional_name": "Dr. João Oliveira"
  }'
```
""",
    response_description="Resumo clínico estruturado com warnings e metadados",
    responses={
        200: {
            "description": "Resumo gerado com sucesso",
            "content": {
                "application/json": {
                    "example": {
                        "summary": {
                            "sections": [
                                {
                                    "title": "Identificação",
                                    "code": "identification",
                                    "content": "Paciente: Maria Silva | CPF: 123.456.789-00 | Nascimento: 15/03/1985 (38 anos) | Sexo biológico: Feminino",
                                    "order": 1,
                                },
                                {
                                    "title": "Queixa e História",
                                    "code": "complaint_history",
                                    "content": "Queixa principal: Dor de cabeça há 3 dias",
                                    "order": 2,
                                },
                            ],
                            "full_text": "=== IDENTIFICAÇÃO ===\nPaciente: Maria Silva...",
                        },
                        "warnings": [],
                        "metadata": {
                            "request_id": "550e8400-e29b-41d4-a716-446655440000",
                            "strategy_used": "rule_based",
                            "strategy_requested": "rule_based",
                            "rule_engine_version": "1.0.0",
                            "processed_at": "2024-01-15T14:30:00Z",
                            "processing_time_ms": 12,
                            "llm_model": None,
                            "fallback_reason": None,
                        },
                    }
                }
            },
        },
        422: {
            "description": "Erro de validação no payload",
            "model": ValidationErrorResponse,
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["body", "patient", "cpf"],
                                "msg": "String should match pattern '^\\d{3}\\.\\d{3}\\.\\d{3}-\\d{2}$'",
                                "type": "string_pattern_mismatch",
                            }
                        ]
                    }
                }
            },
        },
        500: {
            "description": "Erro interno do servidor",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Erro interno ao processar consulta",
                        "code": "INTERNAL_ERROR",
                    }
                }
            },
        },
    },
)
async def create_consultation_summary(
    consultation: ConsultationCreate,
) -> ConsultationSummary:
    """
    Processa uma consulta médica e retorna resumo estruturado.

    Args:
        consultation: Dados completos da consulta médica.

    Returns:
        ConsultationSummary com resumo, warnings e metadata.

    Raises:
        HTTPException: Em caso de erro de processamento.
    """
    start_time = AuditGenerator.start_timer()
    request_id = AuditGenerator.generate_request_id()

    try:
        summarizer = get_summarizer(consultation.strategy)

        result = summarizer.summarize(consultation)

        strategy_used = result.strategy_used

        fallback_reason = None
        llm_model = None

        if strategy_used == "llm_fallback":
            for warning in result.warnings:
                if warning.code == "LLM_FALLBACK_ACTIVATED":
                    fallback_reason = warning.message
                    break

        if strategy_used == "llm_based":
            from app.core.config import get_settings
            settings = get_settings()
            llm_model = settings.GEMINI_MODEL

        metadata = AuditGenerator.create_metadata(
            request_id=request_id,
            strategy_requested=consultation.strategy,
            strategy_used=strategy_used,
            processing_start_ns=start_time,
            llm_model=llm_model,
            fallback_reason=fallback_reason,
        )

        return ConsultationSummary(
            summary=SummaryContent(
                sections=result.sections,
                full_text=result.full_text,
            ),
            warnings=result.warnings,
            metadata=metadata,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao processar consulta",
        )
