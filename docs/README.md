# Documentatie Overzicht — threat-designer-owasped

> Fork van [awslabs/threat-designer](https://github.com/awslabs/threat-designer) (Apache 2.0).  
> Volledig lokale, containerized AI threat modeling tool — AWS-vrij, privacy-first, OWASP-bijdrage.

---

## Snelle Links

| Document | Beschrijving |
|----------|-------------|
| [**Lokale stack & rooktest**](../quick-start-guide/local-stack-owasped.md) | Docker Compose, `.env.local.example` → `.env.local`, `npm run stack:up` / `stack:up:full` (Sentry), curl-checks |
| [Quick Start index](../quick-start-guide/quick-start.md) | Upstream guides-index + link naar lokale fork-doc |
| [Project Goal](../src/projectgoal.md) | Volledige projectvisie, tech spec, OWASP plan |
| [Sprints](../sprints.md) | Sprint history, taken, Definition of Done, huidige focus |
| [Team & Agents](../src/agents.md) | Team manifest, spelregels, werkwijze |

---

## Team

| Document | Beschrijving |
|----------|-------------|
| [Team Personas & Skills](team/personas.md) | Skills matrix per AI-persona, escalatie matrix |
| [QA — functionele tests](qa/README.md) | Index + [`functional-checklist.md`](qa/functional-checklist.md) |

---

## Architecture

> Onderstaande docs beschrijven de **huidige lokale stack** (na AWS-decoupling Sprints 1-6).  
> Sommige secties verwijzen nog naar AWS-concepten — die zijn vervangen door lokale equivalenten.

| Document | Beschrijving | Status |
|----------|-------------|--------|
| [Architecture Overview](architecture.md) | API structuur, service interacties, data flows | Upstream — gedeeltelijk bijgewerkt |
| [Authentication](authentication.md) | Auth mechanismen — **no-auth mode actief** voor lokaal gebruik | Upstream — zie opmerking¹ |
| [Collaboration System](collaboration_system.md) | Samenwerking, toegangsniveaus (OWNER/EDIT/READ_ONLY) | Actueel |
| [Lock Mechanism](lock_mechanism.md) | Optimistic locking voor concurrent editing | Actueel |
| [Sentry Design](sentry_design.md) | AI agent orchestratie (Sentry service, poort 8090) | Actueel |
| [Threat Designer Agent](threat_designer_agent.md) | LLM agent loop, STRIDE analyse, threat generatie | Actueel |

> ¹ **Auth opmerking**: Cognito/JWT authenticatie is uitgeschakeld voor lokaal gebruik. `user_id` fungeert als `username`. Zie `LOCAL_USER` env var in `docker-compose.local.yml`.

---

## Lokale Stack (na Sprint 1-6)

| AWS Dienst | Lokale Vervanger | Poort |
|------------|-----------------|-------|
| Amazon DynamoDB | DynamoDB Local | 8001 |
| Amazon S3 | MinIO | 9000 (API) / 9001 (Console) |
| AWS Lambda | FastAPI app | 8000 |
| AWS Bedrock / OpenAI | Ollama | 11434 |
| Bedrock AgentCore | Sentry service | 8090 (alleen met compose-profiel **`full`**) |
| Amazon Cognito | No-auth stub (`LOCAL_USER`) | — |

---

## Testing

| Bestand | Beschrijving |
|---------|-------------|
| `test/app/services/` | Unit tests voor alle service functies |
| `test/app/routes/` | API route tests (FastAPI TestClient) |
| `test/app/utils/` | Utility & authorization tests |
| `test/app/exceptions/` | Exception class tests |
| `test/app/test_infrastructure.py` | Fixture validatie |

**Test run** (lokaal):
```bash
# Activeer venv met dependencies
source /tmp/testenv/bin/activate

# Alle tests
pytest test/app/ -v

# Alleen services
pytest test/app/services/ -v
```

Zie Sprint 7 + 7b in [`sprints.md`](../sprints.md) voor test modernisering history.

---

## Cursor Rules

| Rule | Beschrijving |
|------|-------------|
| [project-core.mdc](../.cursor/rules/project-core.mdc) | Kernprincipes, stack, AWS-aanpak |
| [workflow-agile.mdc](../.cursor/rules/workflow-agile.mdc) | Agile werkwijze, persona's, spelregels |
| [backend-python.mdc](../.cursor/rules/backend-python.mdc) | Python/FastAPI coding standards |
| [docker-local.mdc](../.cursor/rules/docker-local.mdc) | Docker Compose lokale setup regels |

---

*Laatste update: 2026-03-12 | Beheerd door CoPM*
