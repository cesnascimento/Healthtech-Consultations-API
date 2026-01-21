"""
Ponto de entrada da aplicação FastAPI.

Configura a aplicação, registra rotas e middleware,
e expõe a documentação OpenAPI com Scalar.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from scalar_fastapi import get_scalar_api_reference

from app.api.error_handlers import register_error_handlers
from app.api.routes import consultations_router, health_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
# Healthtech Consultations API

API para processamento de consultas médicas e geração de resumos clínicos estruturados.

## Visão Geral

Esta API permite:
- Receber dados estruturados de consultas médicas
- Validar rigorosamente os dados de entrada
- Gerar resumos clínicos organizados em seções
- Fornecer warnings para inconsistências detectadas
- Rastrear processamento via metadados de auditoria

## Princípios de Design

### Segurança Clínica
- **Sem inferência diagnóstica**: O sistema nunca infere diagnósticos
- **Dados estruturados**: Todos os dados são validados rigorosamente
- **Auditabilidade**: Cada requisição é rastreável

### Estratégias de Resumo

| Estratégia | Descrição | Disponibilidade |
|------------|-----------|-----------------|
| `rule_based` | Processamento determinístico baseado em regras | Sempre disponível |
| `llm_based` | Processamento com auxílio de IA | Opcional (requer configuração) |

**Importante**: A estratégia `rule_based` é sempre o padrão e fallback.
O sistema funciona 100% sem IA.

### Warnings

Warnings são alertas não-bloqueantes que indicam:
- Valores fora das faixas de referência
- Inconsistências nos dados
- Campos importantes ausentes

Warnings **nunca** impedem o processamento.

## Dados Sensíveis (LGPD)

Esta API processa dados sensíveis de saúde. Campos como CPF, nome
e data de nascimento devem ser tratados conforme a LGPD.
""",
    openapi_tags=[
        {
            "name": "Consultas",
            "description": "Processamento de consultas médicas e geração de resumos clínicos.",
        },
        {
            "name": "Health",
            "description": "Verificação de saúde e status da aplicação.",
        },
    ],
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    license_info={
        "name": "Proprietário",
        "url": "https://example.com/license",
    },
    contact={
        "name": "Healthtech Team",
        "email": "cesar@sofyaai.com",
    },
)

# === Middleware ===

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Error Handlers ===

register_error_handlers(app)

# === Rotas ===

app.include_router(health_router)
app.include_router(consultations_router)


# === Scalar API Reference ===

@app.get("/scalar", include_in_schema=False)
async def scalar_html():
    """Documentação interativa com Scalar."""
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title=app.title,
    )


# === Root Endpoint ===


@app.get(
    "/",
    include_in_schema=False,
)
async def root() -> dict[str, str]:
    """Redireciona para documentação."""
    return {
        "message": "Healthtech Consultations API",
        "docs": "/docs",
        "scalar": "/scalar",
        "openapi": "/openapi.json",
    }
