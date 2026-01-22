# Healthtech Consultations API

API para processamento de consultas médicas e geração de resumos clínicos estruturados.

## Visão Geral

Esta API permite:
- Receber dados estruturados de consultas médicas
- Validar rigorosamente os dados de entrada (Pydantic v2)
- Gerar resumos clínicos organizados em seções
- Fornecer warnings para inconsistências detectadas
- Rastrear processamento via metadados de auditoria

---

## Princípios de Design

### Segurança Clínica

| Princípio | Implementação |
|-----------|---------------|
| **Sem inferência diagnóstica** | O sistema NUNCA infere diagnósticos |
| **Dados estruturados** | Todos os dados são validados com Pydantic v2 |
| **Auditabilidade** | Cada requisição tem UUID, timestamp e metadados |
| **Fallback obrigatório** | IA nunca quebra o fluxo - sempre há fallback |

### Estratégias de Resumo

| Estratégia | Descrição | Disponibilidade |
|------------|-----------|-----------------|
| `rule_based` | Processamento 100% determinístico | **Sempre disponível** (padrão) |
| `llm_based` | Processamento com auxílio de IA (Gemini) | Opcional (requer configuração) |

**Importante**: O sistema funciona **100% sem IA**. A estratégia `rule_based` é sempre o padrão e fallback.

---

## Requisitos

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (gerenciador de pacotes)

---

## Instalação com uv

### 1. Instalar uv (se necessário)

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Via pip (alternativa)
pip install uv
```

### 2. Clonar e configurar o projeto

```bash
# Clonar o repositório
git clone https://github.com/cesnascimento/Healthtech-Consultations-API.git

# Navegar até o diretório do projeto
cd Healthtech-Consultations-API

# Criar ambiente virtual e instalar dependências
uv sync
```

### 3. Configurar variáveis de ambiente

```bash
# Copiar template
cp .env.example .env

# Editar conforme necessário
# vim .env
```

**Variáveis disponíveis:**

```bash
# === Aplicação ===
APP_NAME="Healthtech Consultations API"
APP_VERSION="1.0.0"
DEBUG=false

# === Summarizer ===
SUMMARIZER_STRATEGY=rule_based  # ou llm_based

# === LLM (Opcional) ===
GEMINI_API_KEY=your-api-key-here
GEMINI_MODEL=gemini-1.5-flash
LLM_TIMEOUT_SECONDS=10
```

### 4. Executar a API

```bash
# Desenvolvimento Local com fastapi-cli
uv run fastapi dev app/main.py

# Desenvolvimento (com hot reload)
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Produção
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

A API estará disponível em: `http://localhost:8000`

---

## Endpoints

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/` | Informações da API e links úteis |
| `GET` | `/health` | Health check |
| `POST` | `/consultations` | Processa consulta e gera resumo |
| `GET` | `/scalar` | **Documentação interativa (Scalar)** |
| `GET` | `/docs` | Swagger UI |
| `GET` | `/redoc` | ReDoc |
| `GET` | `/openapi.json` | Schema OpenAPI |

---

## Documentação da API

### Scalar (Recomendado)

A documentação interativa está disponível via **Scalar** integrado diretamente no FastAPI:

```
http://localhost:8000/scalar
```

O Scalar oferece uma interface moderna e interativa para explorar e testar a API.

### Outras opções

| Interface | URL | Descrição |
|-----------|-----|-----------|
| **Scalar** | http://localhost:8000/scalar | Interface moderna e interativa |
| Swagger UI | http://localhost:8000/docs | Interface clássica do FastAPI |
| ReDoc | http://localhost:8000/redoc | Documentação somente leitura |
| OpenAPI JSON | http://localhost:8000/openapi.json | Schema bruto para importação |

### Exportar OpenAPI para arquivo

```bash
# Exportar JSON formatado
uv run python -c "import json; from app.main import app; print(json.dumps(app.openapi(), indent=2))" > openapi.json
```

---

## Exemplos de Request/Response

### Health Check

**Request:**
```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "rule_engine_version": "1.0.0",
  "timestamp": "2024-01-15T14:30:00Z",
  "summarizer_strategy": "rule_based",
  "llm_enabled": false
}
```

---

### Consulta Simples (Mínimo Necessário)

**Request:**
```bash
curl -X POST http://localhost:8000/consultations \
  -H "Content-Type: application/json" \
  -d '{
    "patient": {
      "full_name": "Maria Silva Santos",
      "cpf": "123.456.789-00",
      "birth_date": "1985-03-15",
      "biological_sex": "female"
    },
    "consultation_date": "2024-01-15",
    "chief_complaint": "Dor de cabeça persistente há 3 dias",
    "professional_name": "Dr. João Pedro Oliveira"
  }'
```

**Response:**
```json
{
  "summary": {
    "sections": [
      {
        "title": "Identificação",
        "code": "identification",
        "content": "Paciente: Maria Silva Santos | CPF: 123.456.789-00 | Nascimento: 15/03/1985 (39 anos) | Sexo biológico: Feminino | Data da consulta: 15/01/2024 | Tipo: Primeira consulta | Profissional: Dr. João Pedro Oliveira",
        "order": 1
      },
      {
        "title": "Queixa e História",
        "code": "complaint_history",
        "content": "Queixa principal: Dor de cabeça persistente há 3 dias",
        "order": 2
      },
      {
        "title": "Antecedentes e Segurança",
        "code": "background",
        "content": "Alergias: Não informadas\nMedicamentos em uso: Nenhum informado\nAntecedentes pessoais: Não informados",
        "order": 4
      },
      {
        "title": "Avaliação",
        "code": "assessment",
        "content": "Consulta de first visit realizada em 15/01/2024.",
        "order": 6
      }
    ],
    "full_text": "=== IDENTIFICAÇÃO ===\nPaciente: Maria Silva Santos | CPF: 123.456.789-00 | Nascimento: 15/03/1985 (39 anos) | Sexo biológico: Feminino | Data da consulta: 15/01/2024 | Tipo: Primeira consulta | Profissional: Dr. João Pedro Oliveira\n\n=== QUEIXA E HISTÓRIA ===\nQueixa principal: Dor de cabeça persistente há 3 dias\n\n=== ANTECEDENTES E SEGURANÇA ===\nAlergias: Não informadas\nMedicamentos em uso: Nenhum informado\nAntecedentes pessoais: Não informados\n\n=== AVALIAÇÃO ===\nConsulta de first visit realizada em 15/01/2024."
  },
  "warnings": [
    {
      "code": "MISSING_VITAL_SIGNS",
      "level": "info",
      "message": "Sinais vitais não informados na consulta",
      "field": null,
      "value": null
    },
    {
      "code": "MISSING_FAMILY_HISTORY",
      "level": "info",
      "message": "Histórico familiar não informado",
      "field": "family_history",
      "value": "[]"
    },
    {
      "code": "MISSING_PAST_HISTORY",
      "level": "info",
      "message": "Antecedentes patológicos não informados",
      "field": "past_medical_history",
      "value": "[]"
    }
  ],
  "metadata": {
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "strategy_used": "rule_based",
    "strategy_requested": "rule_based",
    "rule_engine_version": "1.0.0",
    "processed_at": "2024-01-15T14:30:00Z",
    "processing_time_ms": 12,
    "llm_model": null,
    "fallback_reason": null
  }
}
```

---

### Consulta Completa

**Request:**
```bash
curl -X POST http://localhost:8000/consultations \
  -H "Content-Type: application/json" \
  -d '{
    "patient": {
      "full_name": "Maria Silva Santos",
      "cpf": "123.456.789-00",
      "birth_date": "1985-03-15",
      "biological_sex": "female",
      "blood_type": "O+",
      "is_pregnant": false
    },
    "consultation_date": "2024-01-15",
    "consultation_type": "follow_up",
    "facility_name": "Clínica Saúde Total",
    "chief_complaint": "Dor de cabeça persistente há 3 dias",
    "history_present_illness": "Paciente refere cefaleia holocraniana de intensidade moderada (6/10) iniciada há 3 dias. Piora no final do dia e após uso prolongado de telas. Nega náuseas, vômitos ou fotofobia. Associa início dos sintomas com período de estresse no trabalho. Já fez uso de paracetamol 750mg com melhora parcial.",
    "vital_signs": {
      "systolic_bp": 130,
      "diastolic_bp": 85,
      "heart_rate": 78,
      "respiratory_rate": 16,
      "temperature_celsius": 36.5,
      "oxygen_saturation": 98,
      "pain_scale": 6,
      "weight_kg": 68.5,
      "height_cm": 165
    },
    "current_medications": [
      {
        "active_ingredient": "losartana potássica",
        "commercial_name": "Cozaar",
        "dosage": "50mg",
        "frequency": "1x/day",
        "route": "oral",
        "start_date": "2023-01-15",
        "prescriber": "Dr. Carlos Mendes"
      }
    ],
    "allergies": [
      {
        "allergen": "dipirona",
        "reaction_type": "allergic",
        "severity": "moderate",
        "reaction_description": "Urticária generalizada após 30 minutos da administração",
        "confirmed": true
      }
    ],
    "past_medical_history": [
      "Hipertensão arterial sistêmica (2018)",
      "Enxaqueca sem aura (2015)"
    ],
    "family_history": [
      "Mãe: HAS e DM2",
      "Pai: IAM aos 62 anos"
    ],
    "social_history": "Não tabagista. Etilismo social esporádico. Sedentária. Trabalha em escritório com uso prolongado de computador.",
    "physical_examination": "BEG, corada, hidratada, anictérica, acianótica. ACV: RCR 2T BNF sem sopros. AR: MV+ bilateral sem RA. Neurológico: Glasgow 15, pupilas isocóricas e fotorreagentes, sem sinais meníngeos, força e sensibilidade preservadas.",
    "professional_name": "Dr. João Pedro Oliveira",
    "professional_council_id": "CRM-SP 123456",
    "specialty": "Clínica Médica",
    "treatment_plan": "1. Manter losartana 50mg 1x/dia\n2. Paracetamol 750mg VO até 6/6h se dor (máx 4g/dia)\n3. Orientações sobre higiene do sono e pausas no trabalho\n4. Reduzir tempo de tela antes de dormir\n5. Retorno em 7 dias se persistência ou piora dos sintomas\n6. Procurar emergência se cefaleia súbita intensa, febre ou alteração visual",
    "additional_notes": "Paciente orientada e sem sinais de alarme no momento.",
    "strategy": "rule_based"
  }'
```

**Response (resumido):**
```json
{
  "summary": {
    "sections": [
      {
        "title": "Identificação",
        "code": "identification",
        "content": "Paciente: Maria Silva Santos | CPF: 123.456.789-00 | Nascimento: 15/03/1985 (39 anos) | Sexo biológico: Feminino | Tipo sanguíneo: O+ | Data da consulta: 15/01/2024 | Tipo: Retorno | Local: Clínica Saúde Total | Profissional: Dr. João Pedro Oliveira | Registro: CRM-SP 123456 | Especialidade: Clínica Médica",
        "order": 1
      },
      {
        "title": "Queixa e História",
        "code": "complaint_history",
        "content": "Queixa principal: Dor de cabeça persistente há 3 dias\n\nHDA: Paciente refere cefaleia holocraniana de intensidade moderada (6/10) iniciada há 3 dias. Piora no final do dia e após uso prolongado de telas. Nega náuseas, vômitos ou fotofobia. Associa início dos sintomas com período de estresse no trabalho. Já fez uso de paracetamol 750mg com melhora parcial.",
        "order": 2
      },
      {
        "title": "Sinais Vitais",
        "code": "vital_signs",
        "content": "PA: 130x85 mmHg | FC: 78 bpm | FR: 16 irpm | Tax: 36.5°C | SpO2: 98% | Dor: 6/10 | Peso: 68.5 kg | Altura: 165.0 cm | IMC: 25.2 kg/m²",
        "order": 3
      },
      {
        "title": "Antecedentes e Segurança",
        "code": "background",
        "content": "⚠️ ALERGIAS: dipirona (moderada) ✓\nMedicamentos em uso: losartana potássica 50mg 1x/day\nAntecedentes pessoais: Hipertensão arterial sistêmica (2018); Enxaqueca sem aura (2015)\nAntecedentes familiares: Mãe: HAS e DM2; Pai: IAM aos 62 anos\nHistória social: Não tabagista. Etilismo social esporádico. Sedentária. Trabalha em escritório com uso prolongado de computador.",
        "order": 4
      },
      {
        "title": "Exame Físico",
        "code": "physical_exam",
        "content": "BEG, corada, hidratada, anictérica, acianótica. ACV: RCR 2T BNF sem sopros. AR: MV+ bilateral sem RA. Neurológico: Glasgow 15, pupilas isocóricas e fotorreagentes, sem sinais meníngeos, força e sensibilidade preservadas.",
        "order": 5
      },
      {
        "title": "Avaliação",
        "code": "assessment",
        "content": "Consulta de follow up realizada em 15/01/2024. Observações: Paciente orientada e sem sinais de alarme no momento.",
        "order": 6
      },
      {
        "title": "Plano",
        "code": "plan",
        "content": "1. Manter losartana 50mg 1x/dia\n2. Paracetamol 750mg VO até 6/6h se dor (máx 4g/dia)\n3. Orientações sobre higiene do sono e pausas no trabalho\n4. Reduzir tempo de tela antes de dormir\n5. Retorno em 7 dias se persistência ou piora dos sintomas\n6. Procurar emergência se cefaleia súbita intensa, febre ou alteração visual",
        "order": 7
      }
    ],
    "full_text": "=== IDENTIFICAÇÃO ===\n..."
  },
  "warnings": [
    {
      "code": "SYSTOLIC_BP_HIGH",
      "level": "low",
      "message": "Pressão sistólica acima do esperado: 130 mmHg",
      "field": "vital_signs.systolic_bp",
      "value": "130"
    },
    {
      "code": "DIASTOLIC_BP_HIGH",
      "level": "low",
      "message": "Pressão diastólica acima do esperado: 85 mmHg",
      "field": "vital_signs.diastolic_bp",
      "value": "85"
    }
  ],
  "metadata": {
    "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "strategy_used": "rule_based",
    "strategy_requested": "rule_based",
    "rule_engine_version": "1.0.0",
    "processed_at": "2024-01-15T14:35:22Z",
    "processing_time_ms": 18,
    "llm_model": null,
    "fallback_reason": null
  }
}
```

---

### Usando Estratégia LLM (Opcional)

**Request:**
```bash
curl -X POST http://localhost:8000/consultations \
  -H "Content-Type: application/json" \
  -d '{
    "patient": {
      "full_name": "João Carlos Pereira",
      "cpf": "987.654.321-00",
      "birth_date": "1970-08-22",
      "biological_sex": "male"
    },
    "consultation_date": "2024-01-15",
    "chief_complaint": "Dor no peito ao esforço",
    "professional_name": "Dra. Ana Maria Costa",
    "strategy": "llm_based"
  }'
```

**Response (se LLM configurado):**
```json
{
  "metadata": {
    "strategy_used": "llm_based",
    "strategy_requested": "llm_based",
    "llm_model": "gemini-1.5-flash",
    "fallback_reason": null
  }
}
```

**Response (se LLM falhar - fallback automático):**
```json
{
  "warnings": [
    {
      "code": "LLM_FALLBACK_ACTIVATED",
      "level": "info",
      "message": "Fallback para rule_based ativado: LLM timeout after 10000ms"
    }
  ],
  "metadata": {
    "strategy_used": "llm_fallback",
    "strategy_requested": "llm_based",
    "llm_model": null,
    "fallback_reason": "Fallback para rule_based ativado: LLM timeout after 10000ms"
  }
}
```

---

### Erro de Validação (422)

**Request inválido:**
```bash
curl -X POST http://localhost:8000/consultations \
  -H "Content-Type: application/json" \
  -d '{
    "patient": {
      "full_name": "Maria Silva",
      "cpf": "123456789",
      "birth_date": "1985-03-15",
      "biological_sex": "female"
    },
    "consultation_date": "2024-01-15",
    "chief_complaint": "Dor",
    "professional_name": "Dr. João"
  }'
```

**Response:**
```json
{
  "detail": [
    {
      "loc": ["body", "patient", "cpf"],
      "msg": "String should match pattern '^\\d{3}\\.\\d{3}\\.\\d{3}-\\d{2}$'",
      "type": "string_pattern_mismatch"
    }
  ]
}
```

---

## Estrutura do Projeto

```
healthtech-consultations/
├── app/
│   ├── __init__.py
│   ├── main.py                      # Entry point FastAPI
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py                  # Dependências injetáveis
│   │   ├── error_handlers.py        # Handlers globais de erro
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── consultations.py     # POST /consultations
│   │       └── health.py            # GET /health
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py                # Settings (Pydantic)
│   │   ├── constants.py             # Faixas clínicas, warnings
│   │   └── errors.py                # Exceções customizadas
│   ├── models/
│   │   ├── __init__.py
│   │   ├── common.py                # Enums compartilhados
│   │   ├── patient.py               # Patient, VitalSigns
│   │   ├── medication.py            # Medication, Allergy
│   │   └── consultation.py          # Request/Response schemas
│   ├── services/
│   │   ├── __init__.py
│   │   ├── summarizers/
│   │   │   ├── __init__.py
│   │   │   ├── base.py              # Protocol + SummarizerResult
│   │   │   ├── factory.py           # Factory para instanciação
│   │   │   ├── rule_based.py        # Estratégia determinística
│   │   │   └── llm_based.py         # Estratégia com IA (opcional)
│   │   └── validators/
│   │       ├── __init__.py
│   │       └── clinical.py          # Validador clínico
│   └── utils/
│       ├── __init__.py
│       ├── audit.py                 # Gerador de metadados
│       └── text.py                  # Processador de texto
├── tests/
│   └── ...
├── pyproject.toml                   # Configuração uv + dependências
├── .env.example                     # Template de variáveis
├── .gitignore
└── README.md
```

---

## Arquitetura

### Fluxo de Dados

```
POST /consultations
        │
        ▼
┌─────────────────┐
│ FastAPI Router  │ ──► Validação Pydantic (422 se inválido)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Clinical        │ ──► Gera warnings não-bloqueantes
│ Validator       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│ Factory         │ ──► │ RuleBasedSum.   │ (sempre disponível)
│ get_summarizer()│     └─────────────────┘
└────────┬────────┘              │
         │                       ▼
         │              ┌─────────────────┐
         └────────────► │ LLMBasedSum.    │ (opcional)
                        │ + fallback      │
                        └────────┬────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │ SummarizerResult│
                        │ sections[]      │
                        │ warnings[]      │
                        └────────┬────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │ AuditGenerator  │ ──► request_id, timestamp
                        └────────┬────────┘
                                 │
                                 ▼
                        ConsultationSummary (Response)
```

### Decisões Arquiteturais

| Decisão | Justificativa |
|---------|---------------|
| **Protocol (typing)** | Duck typing pythônico, não força herança |
| **Pydantic Settings** | Integração nativa, validação de tipos |
| **Factory function** | Simplicidade; DI framework seria over-engineering |
| **Fallback no construtor** | LLMSummarizer sabe como se recuperar |
| **extra="forbid"** | Segurança; payload malformado deve falhar |
| **uv** | Performance, lockfile determinístico |

---

## Warnings

Warnings são alertas **não-bloqueantes** gerados durante o processamento.

### Níveis

| Nível | Descrição |
|-------|-----------|
| `info` | Informativo, sem impacto clínico |
| `low` | Baixa severidade, atenção recomendada |
| `medium` | Média severidade, revisar |
| `high` | Alta severidade, atenção imediata |

### Códigos Comuns

| Código | Descrição |
|--------|-----------|
| `SYSTOLIC_BP_HIGH` | Pressão sistólica elevada |
| `HEART_RATE_LOW` | Bradicardia |
| `OXYGEN_SATURATION_LOW` | Hipoxemia |
| `BP_INCONSISTENT` | Sistólica ≤ diastólica |
| `TEXT_TRUNCATED` | Texto excedeu limite |
| `MISSING_VITAL_SIGNS` | Sinais vitais ausentes |
| `SEVERE_ALLERGIES_PRESENT` | Alergias graves documentadas |
| `LLM_FALLBACK_ACTIVATED` | LLM falhou, usando rule_based |

---

## Desenvolvimento

### Instalar dependências de desenvolvimento

```bash
uv sync --extra dev
```

### Executar testes

```bash
uv run pytest

# Com cobertura
uv run pytest --cov=app --cov-report=html
```

### Linting e formatação

```bash
# Verificar
uv run ruff check .

# Corrigir automaticamente
uv run ruff check . --fix

# Formatar
uv run ruff format .
```

### Type checking

```bash
uv run mypy app
```

---

## Docker

### Build

```bash
docker build -t healthtech-consultations .
```

### Run

```bash
docker run -p 8000:8000 --env-file .env healthtech-consultations
```

### Docker Compose

```bash
docker-compose up -d
```

---

## Licença

Proprietário - Todos os direitos reservados.

---

## Contato

- **Email**: cesar@sofyaai.com
- **Documentação**: http://localhost:8000/docs
