# Sprint Planning — threat-designer-owasped

**Project**: Fork van awslabs/threat-designer → lokale OWASP variant  
**LeadPM**: Dirk  
**Werkwijze**: Agile, kleine werkende increments, plan eerst → goedkeuring → implementatie  

---

## Sprint Status Overzicht

| Sprint | Thema | Status | Periode |
|--------|-------|--------|---------|
| Sprint 1 | Voorbereiding + Lokale Infra | ✅ Afgerond | 2026-03-12 |
| Sprint 2 | Backend → FastAPI | ✅ Afgerond | 2026-03-12 |
| Sprint 3 | Ollama LLM Integratie | ✅ Afgerond | 2026-03-12 |
| Sprint 4 | Frontend Amplify → lokaal | ✅ Afgerond | 2026-03-12 |
| Sprint 5 | DynamoDB Tabel Initialisatie | ✅ Afgerond | 2026-03-12 |
| Sprint 6 | Sentry AI Assistant (lokaal) | ✅ Afgerond | 2026-03-12 |
| Sprint 7 | Testcode Modernisering | ✅ Afgerond | 2026-03-12 |
| Sprint 7b | Test Failure Fixes | ✅ Afgerond | 2026-03-12 |
| **Sprint 8** | **Lokale dev-scripts + UI smoke (Playwright)** | 🔄 Gepland | — |

### Huidige focus (Sprint 8 — gestart)

**Status: in uitvoering** — zie [**Sprint 8**](#sprint-8--lokale-dev-scripts--ui-smoke-playwright) (PVA DevOps + QA).

- **Lokale stack**: `docker compose` / `npm run stack:up` + rooktest. **Gids:** [`quick-start-guide/local-stack-owasped.md`](quick-start-guide/local-stack-owasped.md).
- **Cursor (hier)**: co-creatief prompts/flows — géén vervanging voor pytest/E2E.
- **Model vraag/antwoord (zelf)**: Ollama op host — **KISS:** geen MCP-backloop naar Cursor-intern model.
- **Geen authenticatie (Cognito/JWT)** tot LeadPM de rooktest-/E2E-gate akkoord geeft.
- OWASP LLM Top 10 STRIDE-templates **na** stabiele lokale basis + Sprint 8 smoke.

#### QA — functionele testen ✅ checklist + Sprint 8 automatisering

- **Handmatig**: [`docs/qa/functional-checklist.md`](docs/qa/functional-checklist.md) (blijft gelden).
- **Geautomatiseerd (Sprint 8)**: Playwright-smoke tegen UI (`localhost:5173`), eerste scope **zonder** zware LLM-flow; CI-optioneel.
- **Koppeling**: rooktest = technische basis; checklist = product-laag; Playwright = **regressie/smoke** bovenop.

### Planning check (team) — 2026-04-04

| Onderdeel | Stand |
|-----------|--------|
| **Sprint 1–7** | ✅ Afgerond (zie tabel hierboven). |
| **Sprint 8** | 🔄 **Actief / niet afgerond** — PVA-taken **S8-D01 … S8-Q04** en **Definition of Done** staan nog open; focus: **lokale dev-workflow + Playwright UI-smoke** (zonder zware LLM-flow in v1-E2E). |
| **LLM / assets (lokale modellen)** | Geen aparte sprint; **verwacht formaat + backlog** vastgelegd in [`docs/llm-assets-format-and-improvements.md`](docs/llm-assets-format-and-improvements.md). Opvolging: **LeadPM-prioriteit** — kan door **Dev** parallel aan Sprint 8, **niet** blokkerend voor S8-smoke. |
| **Auth / OWASP LLM Top 10 templates** | Zoals eerder: **na** stabiele rooktest + Sprint 8-gate (zie huidige focus hierboven). |
| **Docs / repo (2026-04-04)** | Sync: Sentry **Vite** (`VITE_SENTRY_BASE_URL`), `add_threats` coercion + `THREAT_AGENT_MAX_ADD_THREATS_SCHEMA_ERRORS`, pytest-paden `test/threat_designer/`, QA-notes onder `docs/qa/`. |


---

## Sprint 1 — Voorbereiding + Lokale Infra

**Datum**: 2026-03-12  
**Status**: ✅ Afgerond — 2026-03-12  
**Scope**: Fase 0 (repo-analyse) + Fase 1 (DynamoDB Local + MinIO)  
**Effort**: ~1 dag  

### Doel

Na deze sprint kunnen we de backend verbinden met lokale storage (DynamoDB Local + MinIO) zonder AWS. De Lambda-handlers zelf worden nog niet vervangen — alleen de storage layer.

### Input per Persona

| Persona | Inbreng |
|---------|---------|
| **Dev** | Identificeer alle `boto3` calls in `backend/app/` en `backend/threat_designer/` die DynamoDB of S3 aanspreken |
| **DevOps** | `docker-compose.local.yml` aanmaken met DynamoDB Local + MinIO + MinIO init bucket |
| **Sec** | Review: welke data gaat naar S3 (architectuurdiagrammen) — sensitief? Bucket-policies nodig? |
| **QA** | Controleer `test/app/conftest.py` en `test_infrastructure.py` — welke tests testen storage direct? |
| **CoPM** | Documenteer alle gevonden AWS dependencies in een overzichtstabel |

### Taken

#### Fase 0 — Repo-analyse (Dev + CoPM)

- [x] **S1-01** `backend/app/` scannen op AWS SDK calls (`boto3`, `botocore`, `@aws_lambda_powertools`)
- [x] **S1-02** `backend/threat_designer/` scannen op DynamoDB + S3 referenties  
- [x] **S1-03** `backend/sentry/` scannen — scope voor Sprint 6
- [x] **S1-04** `src/` (frontend) scannen op `@aws-amplify` imports — scope voor Sprint 4
- [x] **S1-05** Dependencies overzicht vastleggen (tabel in dit document)

#### Fase 1a — docker-compose.local.yml (DevOps)

- [x] **S1-06** `docker-compose.local.yml` aanmaken:
  - DynamoDB Local (poort 8001)
  - MinIO (poort 9000 + 9001)
  - MinIO init container (bucket aanmaken)
- [x] **S1-07** `.env.local` aanmaken met lokale endpoint variabelen
- [x] **S1-08** Smoke test: beide services draaien, DynamoDB Local op `localhost:8001`, MinIO healthy op `localhost:9000`

#### Fase 1b — Backend storage aanpassen (Dev)

- [x] **S1-09** `backend/threat_designer/constants.py` — `ENV_DYNAMODB_ENDPOINT`, `ENV_S3_ENDPOINT` toegevoegd
- [x] **S1-10** `backend/threat_designer/aws_clients.py` aangemaakt — centrale boto3 factory met lokale endpoint support
- [x] **S1-11** `utils.py`, `agent.py`, `workflow_attack_tree.py` aangepast — `get_dynamodb_resource()` / `get_s3_client()` i.p.v. inline boto3 calls

#### Verificatie (QA)

- [x] **S1-12** Smoke test: DynamoDB Local reageert op `localhost:8001` (400 auth = alive)
- [x] **S1-13** Smoke test: MinIO healthy op `localhost:9000`, `threat-designer-bucket` aangemaakt

### Definition of Done Sprint 1

- [x] `docker compose -f docker-compose.local.yml up` start zonder errors
- [x] DynamoDB Local bereikbaar op `localhost:8001`
- [x] MinIO bereikbaar op `localhost:9000` en `localhost:9001`
- [x] `threat-designer-bucket` bestaat in MinIO na startup
- [x] Backend boto3 calls gebruiken `DYNAMODB_ENDPOINT` + `S3_ENDPOINT` env vars via `aws_clients.py`
- [x] Geen hardcoded AWS endpoints in `backend/threat_designer/`

---

## Sprint 2 — Backend Lambda → FastAPI

**Datum**: 2026-03-12  
**Status**: ✅ Afgerond — 2026-03-12  
**Scope**: Fase 2 — `backend/app/` van Lambda/APIGateway naar FastAPI containeriseren  
**Effort**: ~1 dag  

### Stand van zaken (SVZ)

| Aspect | Status |
|--------|--------|
| **Planning** | In [Sprint Status Overzicht](#sprint-status-overzicht): ✅ afgerond. |
| **Code** | `backend/app/` = **FastAPI** + `aws_clients` + **httpx** naar `THREAT_DESIGNER_URL/invocations`; geen `aws_lambda_powertools` / `APIGatewayRestResolver` in deze tree. |
| **Nog te bespreken / nu niet** | Geen herimplementatie Sprint 2 nodig. **Volgende focus:** rooktest + [`docs/qa/functional-checklist.md`](docs/qa/functional-checklist.md); **auth (Cognito)** bewust **na** stabiele lokale gate (`sprints.md` — huidige focus). |
| **Naamgeving** | API gebruikt nog endpoints/naam `list_cognito_users` / `get_username_from_cognito` voor **compatibiliteit**; onder water = stubs / `local-user` — geen boto3 Cognito-client. |

**Taken hieronder:** als checklist t.o.v. repo; alles **[x]** = uitgevoerd (niet “optioneel nog eens doen”).

### Doel

Na deze sprint draait de API laag als FastAPI container zonder `aws_lambda_powertools`, zonder Cognito en zonder Bedrock AgentCore. De `threat-designer` agent (al FastAPI) wordt via HTTP aangeroepen i.p.v. via Lambda invocatie.

### Sleutelbevindingen

| Oud | Nieuw | Strategie |
|-----|-------|-----------|
| `APIGatewayRestResolver` | `FastAPI()` | Framework swap |
| `aws_lambda_powertools Router` | `fastapi.APIRouter` | Drop-in compatible routes |
| `Cognito authorizer` user_id | `"local-user"` constant | No-auth mode |
| `agent_core_client.invoke_agent_runtime()` | `httpx.post(THREAT_DESIGNER_URL/invocations)` | HTTP naar bestaande FastAPI container |
| `boto3.resource("dynamodb")` | `get_dynamodb_resource()` | Zelfde als Sprint 1 |
| `boto3.client("s3")` presigned URL | MinIO presigned (localhost:9000) | `S3_PUBLIC_ENDPOINT` env var |
| `cognito_client.list_users()` | Stub → `["local-user"]` | No-auth mode |

### Taken

#### S2-01: `backend/app/aws_clients.py` aanmaken (Dev)
- [x] Zelfde factory patroon als `backend/threat_designer/aws_clients.py`
- [x] Extra: `get_s3_presign_client()` voor MinIO presigned URLs op publiek adres

#### S2-02: `backend/app/index.py` → FastAPI (Dev)
- [x] `APIGatewayRestResolver` → `FastAPI()`
- [x] `CORSConfig` → `CORSMiddleware`
- [x] Security headers → FastAPI middleware
- [x] Exception handlers → `@app.exception_handler()`
- [x] `lambda_handler()` → `uvicorn.run(app)` startup
- [x] Include routes als FastAPI routers

#### S2-03: Routes → FastAPI APIRouter (Dev)
- [x] `threat_designer_route.py`: `Router` → `APIRouter`
- [x] `router.current_event.request_context.authorizer.get("user_id")` → `"local-user"`
- [x] `router.current_event.json_body` → Pydantic request body
- [x] `router.current_event.query_string_parameters` → FastAPI `Query` params
- [x] `attack_tree_route.py`: zelfde patroon

#### S2-04: Services — boto3 local clients (Dev)
- [x] `threat_designer_service.py`: boto3 → `get_dynamodb_resource()` / `get_s3_client()`
- [x] `attack_tree_service.py`: boto3 → lokale clients
- [x] `lock_service.py`: boto3 → lokale clients
- [x] `collaboration_service.py`: boto3 → lokale clients

#### S2-05: Services — AgentCore + Lambda → HTTP (Dev)
- [x] `invoke_lambda()` stap 3: `agent_core_client.invoke_agent_runtime()` → `httpx.AsyncClient.post(THREAT_DESIGNER_URL/invocations)`
- [x] `agent_core_client.stop_runtime_session()` → no-op stub
- [x] `lambda_client.invoke()` referenties verwijderen

#### S2-06: Services — Cognito stubs (Dev)
- [x] `lock_service.get_username_from_cognito()` → `return user_id` (user_id IS username in no-auth)
- [x] `collaboration_service.list_cognito_users()` → return `[{"Username": "local-user", "Attributes": []}]`
- [x] `cognito_client.list_users()` → verwijderen

#### S2-07: Utils opschonen (Dev)
- [x] `utils/utils.py`: `aws_lambda_powertools` Logger/Tracer/Router → `structlog` / Python logging
- [x] `utils/utils.py`: `boto3.resource("dynamodb")` → `get_dynamodb_resource()`
- [x] `utils/authorization.py`: `aws_lambda_powertools Logger` → Python logging

#### S2-08: `backend/app/requirements.txt` updaten (Dev)
- [x] Toevoegen: `fastapi`, `uvicorn[standard]`, `httpx`, `pydantic`, `structlog`
- [x] Verwijderen: `aws_lambda_powertools` (of behouden als er andere dependencies zijn)

#### S2-09: `backend/app/Dockerfile.local` aanmaken (DevOps)
- [x] Python 3.12-slim, FastAPI/uvicorn startup

#### S2-10: `docker-compose.local.yml` app service (DevOps)
- [x] `app` service met poort 8000, env vars, depends_on threat-designer + dynamodb-local + minio

### Definition of Done Sprint 2

- [x] `docker compose -f docker-compose.local.yml up` start `app` en `threat-designer` services
- [x] `GET http://localhost:8000/threat-designer/all` retourneert 200 (lege lijst)
- [x] Geen `aws_lambda_powertools` imports in `backend/app/`
- [x] Geen `cognito_client` calls
- [x] `invoke_lambda` → HTTP POST naar `threat-designer:8080/invocations`

---

## Sprint 3 — Ollama LLM Integratie

**Datum**: 2026-03-12  
**Status**: ✅ Afgerond — 2026-03-12  
**Scope**: Fase 3 — derde LLM provider `"ollama"` via OpenAI-compatibele API  
**Effort**: ~0.5 dag  

### Stand van zaken (SVZ)

| Aspect | Status |
|--------|--------|
| **Code** | `MODEL_PROVIDER_OLLAMA`, `_initialize_ollama_models()` in `backend/threat_designer/`; routing in `initialize_models()`; `model_service` behandelt Ollama. |
| **Runtime** | Ollama draait **op de host** (`INFERENCE_BASE_URL` → o.a. `host.docker.internal:11434/v1`) — niet in deze repo; stack kan opstarten, maar **zonder bereikbare Ollama-endpoint** geen echte modelcalls. |
| **Nog te bespreken / nu niet** | Andere modellen: enkel `LOCAL_MODEL` / env; geen extra sprintwerk tenzij provider uitbreiden (Bedrock/OpenAI blijven optioneel in code). |

**Taken hieronder:** alles **[x]** — codepad aanwezig.

### Doel

Na deze sprint draait de threat-designer agent met een lokaal Ollama-model (qwen3:32b of ander model). Geen Bedrock, geen OpenAI API key nodig.

### Aanpak

Het codebase ondersteunt al `MODEL_PROVIDER=openai` via `langchain_openai.ChatOpenAI`. Ollama exposeert dezelfde OpenAI-compatibele API maar ondersteunt **niet** `use_responses_api=True`. We voegen een derde provider `"ollama"` toe die:

- Dezelfde `ChatOpenAI` class gebruikt
- `base_url=INFERENCE_BASE_URL` instelt (bijv. `http://host.docker.internal:11434/v1`)
- `api_key=INFERENCE_API_KEY` (dummy waarde `"ollama"`)
- Geen `use_responses_api` — Ollama ondersteunt dat niet
- `LOCAL_MODEL` env var voor alle rollen (één model voor alles)
- Geen reasoning budget — Ollama gebruikt gewone tool calling

### Taken

- [x] **S3-01** `constants.py` — `MODEL_PROVIDER_OLLAMA`, `ENV_INFERENCE_BASE_URL`, `ENV_INFERENCE_API_KEY`, `ENV_LOCAL_MODEL` toevoegen
- [x] **S3-02** `model_utils.py` — `_initialize_ollama_models()` aanmaken; routing in `initialize_models()`
- [x] **S3-03** `model_service.py` — Ollama tool_choice: behandel als OpenAI (by class name)
- [x] **S3-04** `.env.local` bijwerken met `LOCAL_MODEL=qwen3:32b`, `MODEL_PROVIDER=ollama`

### Definition of Done Sprint 3

- [x] `MODEL_PROVIDER=ollama` + `LOCAL_MODEL=qwen3:32b` opgestart zonder errors
- [x] `initialize_models()` retourneert 8 model instances via Ollama endpoint
- [x] Geen `aws_lambda_powertools` of Bedrock-imports nodig voor Ollama path
- [x] `.env.local` bevat volledige Ollama configuratie  

---

## Sprint 4 — Frontend Amplify → lokaal

**Datum**: 2026-03-12  
**Status**: ✅ Afgerond — 2026-03-12  
**Scope**: Fase 4 — `aws-amplify`, `@aws-amplify/auth`, `@aws-amplify/ui-react` verwijderen uit React frontend  
**Effort**: ~1 dag  

### Stand van zaken (SVZ)

| Aspect | Status |
|--------|--------|
| **Code** | No-auth in `src/services/Auth/auth.js`; geen `Amplify.configure` in bootstrap; axios zonder `fetchAuthSession`. |
| **Dependencies** | `package.json`: geen `aws-amplify` / `@aws-amplify/*` (zoals DoD). |
| **Config** | `VITE_APP_ENDPOINT` → backend (zie `.env.development` / docs). |
| **Nog te bespreken / nu niet** | **Echte** login/Cognito = aparte sprint **na** auth-gate; UI-routes kunnen nog “legacy” namen hebben. |

**Taken hieronder:** alles **[x]**.

### Doel

Na deze sprint kan de frontend opstarten zonder Cognito en zonder Amplify. `getUser()` retourneert direct een lokale gebruiker — de loginpagina wordt nooit getoond.

### Aanpak

`App.jsx` bepaalt of de loginpagina getoond wordt via `authUser ? <App> : <LoginPageInternal>`. Als `getUser()` altijd een lokale gebruiker retourneert, slaan we de login over. Alle AWS packages worden daarna verwijderd uit `package.json`.

**No-auth patroon**: alle `fetchAuthSession()` interceptors worden verwijderd; de backend (Sprint 2) verwacht toch geen JWT.

### Taken

- [x] **S4-01** `src/services/Auth/auth.js` → no-auth stub (hardcoded `local-user`)
- [x] **S4-02** `src/config.js`: `@aws-amplify/ui-react/styles.css` + `amplifyConfig` verwijderen
- [x] **S4-03** `src/bootstrap.jsx`: `Amplify.configure()` verwijderen
- [x] **S4-04** `src/pages/Landingpage/Landingpage.jsx`: Amplify imports verwijderen
- [x] **S4-05** `src/components/Auth/LoginForm.jsx`: Amplify auth stubs
- [x] **S4-06** Axios interceptors: `stats.jsx`, `attackTreeService.js`, `lockService.js` — `fetchAuthSession` verwijderen
- [x] **S4-07** Overige: `useAttackTreeMetadata.js`, `SharingModal.jsx`, `Agent/context/utils.js`
- [x] **S4-08** `package.json`: `aws-amplify`, `@aws-amplify/auth`, `@aws-amplify/ui-react`, `@aws-sdk/client-ssm` verwijderen
- [x] **S4-09** `.env.development` aanmaken met `VITE_APP_ENDPOINT=http://localhost:8000`

### Definition of Done Sprint 4

- [x] `npm run dev` start zonder Amplify-gerelateerde errors
- [x] App laadt direct als `local-user` zonder loginpagina
- [x] Geen `aws-amplify` of `@aws-amplify/*` imports meer in actieve code
- [x] `package.json` bevat geen AWS Amplify packages meer

---

## Sprint 5 — DynamoDB Tabel Initialisatie

**Datum**: 2026-03-12  
**Status**: ✅ Afgerond — 2026-03-12  
**Scope**: Fase 5 — init-script dat alle DynamoDB Local tabellen aanmaakt bij opstart  
**Effort**: ~0.5 dag  

### Stand van zaken (SVZ)

| Aspect | Status |
|--------|--------|
| **Code** | `scripts/init_dynamo.py` (idempotent); `dynamodb-init` in `docker-compose.local.yml`. |
| **Netwerk** | Binnen Docker: **`dynamodb-local:8000`** (container-poort 8000) — niet verwarren met host-map `8001:8000`. Zie [`quick-start-guide/local-stack-owasped.md`](quick-start-guide/local-stack-owasped.md). |
| **Nog te bespreken / nu niet** | Schema-wijzigingen = script + compose-env voor `app`/`threat-designer` tabellen synchroon houden. |

**Taken hieronder:** alles **[x]**.

### Doel

Na deze sprint start `docker compose up` met alle 6 DynamoDB tabellen correct aangemaakt, inclusief GSIs en TTL. Geen handmatige AWS CLI commando's meer nodig.

### Tabelschema (uit `infra/dynamodb.tf`)

| Env var | Naam | PK | SK | GSIs |
|---------|------|----|----|------|
| `AGENT_STATE_TABLE` | `threat-designer-agent-state` | `job_id` (S) | — | `owner-job-index` (owner, job_id) |
| `JOB_STATUS_TABLE` | `threat-designer-job-status` | `id` (S) | — | — |
| `AGENT_TRAIL_TABLE` | `threat-designer-agent-trail` | `id` (S) | — | — |
| `ATTACK_TREE_TABLE` | `threat-designer-attack-trees` | `attack_tree_id` (S) | — | `threat_model_id-index` |
| `LOCKS_TABLE` (`LOCK_TABLE` in `init_dynamo.py`) | `threat-designer-locks` | `threat_model_id` (S) | — | TTL op `ttl` |
| `SHARING_TABLE` | `threat-designer-sharing` | `threat_model_id` (S) | `user_id` (S) | `owner-index`, `user-index` |

### Taken

- [x] **S5-01** `scripts/init_dynamo.py` aanmaken — idempotent, maakt alle 6 tabellen aan
- [x] **S5-02** `docker-compose.local.yml` — `dynamodb-init` service (Python script als one-shot container)

### Definition of Done Sprint 5

- [x] `docker compose up` start zonder errors mbt DynamoDB tabellen
- [x] Alle 6 tabellen aanwezig inclusief GSIs en TTL
- [x] Script is idempotent: herhaalde runs gooien geen errors

---

## Sprint 6 — Sentry AI Assistant (lokaal)

**Datum**: 2026-03-12  
**Status**: ✅ Afgerond — 2026-03-12  
**Scope**: Fase 6 — Sentry AI agent losmaken van AWS Bedrock AgentCore + lokale checkpointer  
**Effort**: ~1 dag  

### Stand van zaken (SVZ)

| Aspect | Status |
|--------|--------|
| **Code** | `backend/sentry/`: `MemorySaver`, lokale DynamoDB + MinIO clients, `X-Session-Id`, lege MCP-config waar van toepassing. |
| **Compose** | Service `sentry` — host **`localhost:8090`** → container `8080` (`8090:8080`). **Profiel `full`:** `docker compose --profile full up` of `npm run stack:up:full` — standaard `stack:up` start **zonder** Sentry (lichter). |
| **Nog te bespreken / nu niet** | Cloud Bedrock/AgentCore niet nodig voor lokale flow; optionele verbeteringen = product-backlog, geen Sprint 6 heropening. |

**Taken hieronder:** alles **[x]**.

### Doel

Na deze sprint draait Sentry als lokale FastAPI container met Ollama-model, LangGraph `MemorySaver` checkpointer, DynamoDB Local voor sessie-mapping en MinIO voor diagram opslag. Geen `langgraph-checkpoint-aws`, geen `bedrock-agent-runtime`.

### Aanpak

| Component | Was | Wordt |
|-----------|-----|-------|
| LLM | `ChatBedrockConverse` | `ChatOpenAI` (Ollama compat) |
| Checkpointer | `AsyncBedrockSessionSaver` (AgentCore) | `MemorySaver` (in-memory, geen extra dep) |
| Session creatie | `sync_checkpointer.session_client.create_session()` | `uuid.uuid4()` |
| Session opslag | DynamoDB cloud | DynamoDB Local |
| Session delete | `bedrock-agent-runtime` `end_session()` | cache cleanup |
| S3/diagram | AWS S3 | MinIO endpoint |
| Header | `X-Amzn-Bedrock-AgentCore-Runtime-Session-Id` | `X-Session-Id` |
| JWT auth | Cognito JWT validatie | no-auth (`local-user`) |
| MCP | AWS Knowledge MCP (cloud) | leeg `{}` |

### Taken

- [x] **S6-01** `config.py`: `MemorySaver` + `ollama` provider, verwijder `langgraph-checkpoint-aws` imports
- [x] **S6-02** `session_manager.py`: DynamoDB Local + `uuid4` i.p.v. AgentCore
- [x] **S6-03** `history_manager.py`: `bedrock-agent-runtime` verwijderen
- [x] **S6-04** `tools.py` + `utils.py`: lokale DynamoDB + MinIO clients
- [x] **S6-05** `agent.py`: `X-Session-Id` header + no-auth stub
- [x] **S6-06** `mcp_config.json` leeg + `requirements.txt` updaten
- [x] **S6-07** `docker-compose.local.yml`: sentry service activeren (poort 8090)

### Definition of Done Sprint 6

- [x] `docker compose up` start `sentry` op poort 8090 zonder errors
- [x] `GET http://localhost:8090/ping` retourneert `{"status": "Healthy"}`
- [x] Geen `langgraph-checkpoint-aws` of `bedrock-agent-runtime` imports
- [x] Sentry accepteert `X-Session-Id` header zonder JWT

---

## Dependency Overzicht (Sprint 1 — afgerond; geen open actie)

Sprint 1 taken **S1-01 … S1-05** hebben de AWS-touchpoints in kaart gebracht; migratie is uitgevoerd in Sprints 1–6 (lokale endpoints, stubs, verwijderde Amplify). Dit overzicht is **historisch** — actuele wiring staat in `backend/threat_designer/aws_clients.py`, `backend/app/aws_clients.py`, `docker-compose.local.yml`.

### Backend AWS Dependencies

| Bron | Opmerking |
|------|-----------|
| DynamoDB / S3 | Via **lokale** endpoints + tabellen (Sprint 5 init); geen cloud verplicht voor dev. |
| Agent / LLM | HTTP naar `threat-designer` + Ollama optioneel (Sprint 3). |

### Frontend AWS Dependencies

| Bron | Opmerking |
|------|-----------|
| Amplify / Cognito | **Verwijderd** uit actieve frontend (Sprint 4). |

---

## Beslissingen Log

| Datum | Beslissing | Door |
|-------|-----------|------|
| 2026-03-12 | Geen auth voor nu — later toevoegen (Optie A) | LeadPM |
| 2026-03-12 | **Geen auth bouwen tot lokale Docker/E2E rooktest door LeadPM akkoord** — eerst lokaal stack testen (`docker-compose.local.yml`), daarna pas auth-sprint overwegen | LeadPM |
| 2026-03-12 | **KISS inference-pad**: Cursor hier voor concept/prompts; echte model Q/A via eigen stack + Ollama/Qwen op host — **geen** MCP-backloop naar Cursor-intern model | LeadPM |
| 2026-03-12 | Sentry tijdelijk via extern model, geen lokale Ollama installatie | LeadPM |
| 2026-03-12 | Start met Fase 1 (storage) als eerste sprint | LeadPM |
| 2026-03-12 | Cursor rules: carte blanche aan AI team | LeadPM |
| 2026-03-12 | **Retro & HITL:** tussentijdse review vastgelegd in [`docs/team/retro-hitl-2026-03.md`](docs/team/retro-hitl-2026-03.md) — feedback proces/spelregels; LeadPM vult open velden / prioriteiten | LeadPM + team |
| 2026-03-22 | **Retro follow-up:** H1/H3 terecht; H2 blijven volgen; H4 uitwerken; H5 in scope via spelregels. P2–P4 akkoord. `agents.md` uitgebreid (geen shadow IT, geen overeager assistentie). CoPM akkoord | LeadPM |

---

## Sprint 7 — Testcode Modernisering (2026-03-12)

**Doel**: Alle testbestanden bijwerken na Sprints 1-6 (AWS-decoupling). Verouderde mocks en fixtures verwijderen, testcode uitlijnen met de lokale stack.

### Stand van zaken (SVZ)

| Aspect | Status |
|--------|--------|
| **Planning** | Afgerond; onderstaande **Scope & Aanpak**-tabel beschrijft wat er gebeurd is (niet “nog te doen”). |
| **Code** | Tests: `httpx` naar agent, `get_dynamodb_resource`, `THREAT_DESIGNER_URL` / `LOCAL_USER`; JWT authorizer-test verwijderd. |
| **Verificatie** | Na wijzigingen in `backend/app/`: relevante `pytest`-subset of volledige suite. |
| **Nog te bespreken / nu niet** | Nieuwe features → nieuwe tests; **geen** heropening Sprint 7 tenzij grote regressie in teststrategie. |

**Taken hieronder:** alles **[x]**.

### Scope & Aanpak

| Bestand | Actie |
|---------|-------|
| `test/authorizer/test_index.py` | **Verwijderd** — JWT Lambda Authorizer bestaat niet meer |
| `test/app/conftest.py` | Verwijder `mock_lambda_client`, `mock_bedrock_client`, `mock_cognito_client`, `mock_lambda_context`, `sample_cognito_user`, `sample_api_event`, `sample_lambda_payload`; update `mock_environment` met lokale vars |
| `test/app/routes/conftest.py` | Verwijder Lambda/Bedrock/Cognito mocks; update env vars naar `THREAT_DESIGNER_URL` / `LOCAL_USER` |
| `test/app/test_infrastructure.py` | Verwijder tests voor verwijderde fixtures |
| `test_threat_designer_service.py` | `TestInvokeLambda`: `httpx.post` mock i.p.v. `agent_core_client.invoke_agent_runtime`; voeg timeout-test toe |
| `test_attack_tree_service.py` | `TestInvokeAttackTreeAgent`: `httpx.post` mock i.p.v. `agent_core_client`; property-based tests geüpdate |
| `test_collaboration_service.py` | `TestGetCollaborators`: Cognito patches verwijderd (user_id = username); `TestListCognitoUsers` → `TestListUsersLocal` |
| `test_lock_service.py` | `TestGetUsernameFromCognito`: herschreven als passthrough test |
| `test_utils.py` | `TestCreateDynamoDBItem`: `@patch("utils.utils.boto3.resource")` → `@patch("utils.utils.get_dynamodb_resource")` |
| `test_fetch_all_pagination.py` | Verwijder verouderde env vars; voeg `THREAT_DESIGNER_URL` toe |
| `test_pagination_infrastructure.py` | Verwijder verouderde env vars; voeg `THREAT_DESIGNER_URL` toe |
| `test_threat_designer_route.py` | Update env vars: verwijder `THREAT_MODELING_AGENT`, `COGNITO_USER_POOL_ID` |

### Taken Sprint 7

- [x] **S7-01** `test/authorizer/test_index.py` verwijderen
- [x] **S7-02** `test/app/conftest.py` opschonen
- [x] **S7-03** `test/app/routes/conftest.py` opschonen
- [x] **S7-04** `test/app/test_infrastructure.py` bijwerken
- [x] **S7-05** `test_threat_designer_service.py` — `TestInvokeLambda` herschreven
- [x] **S7-06** `test_attack_tree_service.py` — `TestInvokeAttackTreeAgent` herschreven
- [x] **S7-07** `test_collaboration_service.py` — `TestGetCollaborators` + `TestListUsersLocal`
- [x] **S7-08** `test_lock_service.py` — `TestGetUsernameFromCognito` passthrough
- [x] **S7-09** `test_utils.py` — `get_dynamodb_resource` patch pad gecorrigeerd
- [x] **S7-10** Resterende env var noise opgeschoond in paginering en route tests

### Definition of Done Sprint 7

- [x] Geen `agent_core_client`, `invoke_agent_runtime`, `THREAT_MODELING_AGENT`, `cognito_client`, `COGNITO_USER_POOL_ID` meer in testcode
- [x] `TestInvokeLambda` en `TestInvokeAttackTreeAgent` testen `httpx.post` → `THREAT_DESIGNER_URL/invocations`
- [x] `TestListUsersLocal` valideert de no-auth stub voor gebruikerslijst
- [x] `TestGetUsernameFromCognito` bevestigt de passthrough (user_id = username)
- [x] `TestCreateDynamoDBItem` patchet correct pad `utils.utils.get_dynamodb_resource`

---

## Sprint 7b — Test Failure Fixes (2026-03-12)

**Doel**: Resterende test failures na Sprint 7 oplossen. Gevonden 9 falende tests door twee root causes: (1) productiebug `boto3` niet geïmporteerd in `delete_s3_object`, (2) hypothesis tests misten `dynamodb` mock.

### Stand van zaken (SVZ)

| Aspect | Status |
|--------|--------|
| **Planning** | Afgerond; root causes + patches in tabel hieronder. |
| **Code** | `delete_s3_object` → `get_s3_client()`; mocks op juiste patch-targets; Hypothesis + DynamoDB stub. |
| **Verificatie** | `pytest` volledige suite groen houden; **260/260** was het doel bij afronding — actueel aantal met `pytest test/ -q` (uitbreidingen kunnen teller verhogen). |
| **Nog te bespreken / nu niet** | Toekomstige falende tests = normale bugfix-workflow; geen vaste “Sprint 7c” tenzij LeadPM dat afspreekt. |

**Taken hieronder:** alles **[x]**.

### Root Causes & Fixes

| # | Root Cause | Affected Tests | Fix |
|---|-----------|----------------|-----|
| 1 | **Productiebug**: `delete_s3_object()` in `threat_designer_service.py` gebruikte `boto3.client("s3")` direct maar `boto3` was niet geïmporteerd na Sprint 2 migratie | `TestHelperFunctions::test_delete_s3_object_*`, `TestCascadeDeletion` (3x), `TestDeleteThreatModel` | `boto3.client("s3")` vervangen door `get_s3_client()` (al beschikbaar via `aws_clients` import) |
| 2 | **Test mock mismatch**: Tests patchten `boto3.client` maar `delete_s3_object` gebruikt nu `get_s3_client` | `test_delete_s3_object_calls_s3_correctly`, `test_delete_s3_object_handles_errors`, `TestCascadeDeletion` (3x) | Patch target gewijzigd naar `services.threat_designer_service.get_s3_client` |
| 3 | **Verkeerde assertie**: `test_delete_tm_owner_can_delete` verwachtte `require_owner.call_count == 2` maar attack tree cascade gebruikt `require_access` (niet `require_owner`) | `TestDeleteThreatModel::test_delete_tm_owner_can_delete` | Assertie gecorrigeerd naar `call_count == 1` |
| 4 | **Hypothesis tests**: `TestSingleDownloadAuthorizationProperty` en `TestSufficientAccessGrantsPresignedURLsProperty` misten `dynamodb` mock — `generate_presigned_download_url` doet eerst DynamoDB lookup | 5 hypothesis tests (hangende runs) | `patch.object(tds_module, "dynamodb")` toegevoegd aan alle `with` context managers; `mock_extract` (nu unused) vervangen; DynamoDB response geconfigureerd |

### Taken Sprint 7b

- [x] **S7b-01** Productiebug: `boto3.client("s3")` → `get_s3_client()` in `threat_designer_service.py:delete_s3_object`
- [x] **S7b-02** `test_delete_s3_object_*`: patch target van `boto3.client` naar `services.threat_designer_service.get_s3_client`
- [x] **S7b-03** `TestCascadeDeletion` (3 tests): idem patch target fix
- [x] **S7b-04** `test_delete_tm_owner_can_delete`: `require_owner.call_count` assertie `2 → 1` gecorrigeerd
- [x] **S7b-05** `TestSingleDownloadAuthorizationProperty` (2 hypothesis tests): `dynamodb` mock toegevoegd, `mock_extract` vervangen
- [x] **S7b-06** `TestSufficientAccessGrantsPresignedURLsProperty` (3 hypothesis tests): `dynamodb` mock toegevoegd, `mock_extract` vervangen, `Key` assertie gecorrigeerd naar `s3_location`

### Definition of Done Sprint 7b

- [x] `delete_s3_object` gebruikt `get_s3_client()` (MinIO-compatible) — geen directe `boto3` import nodig
- [x] Alle 6 oorspronkelijke failures groen
- [x] Alle 5 hypothesis presigned URL tests groen (geen hangs meer)
- [x] **260/260 tests groen** (`test/app/services/`, `test/app/exceptions/`, `test/app/utils/`, `test/app/test_infrastructure.py`)

---

## Sprint 8 — Lokale dev-scripts + UI smoke (Playwright)

**Status**: 🔄 Gepland / in uitvoering  
**Scope**: Na Sprint 7b — **één duidelijke lokale workflow** (DevOps) + **eerste geautomatiseerde UI-smoke** (QA), passend bij het afgesproken PVA.

### Doel

- **DevOps**: ontwikkelaars starten backend + frontend **voorspelbaar** (documentatie en/of korte scripts), zonder de bestaande `stack:*`-commando’s te dupliceren.
- **QA**: **Playwright** draait minimaal **1–3 smoke-tests** in de browser (app laadt, geen wit scherm, eventueel zichtbare shell/navigatie); **geen** volledige threat-model LLM-run in v1 (flaky i.v.m. Ollama/timing) — optioneel later als `@slow` of handmatig via checklist.

### PVA — taken

#### DevOps

- [ ] **S8-D01** Korte **dev workflow** in docs: `cp .env.local.example` → `.env.local`, `npm run stack:up`, tweede terminal `npm run dev` — verwijs naar [`quick-start-guide/local-stack-owasped.md`](quick-start-guide/local-stack-owasped.md) (geen tweede “waarheid” naast Compose).
- [ ] **S8-D02** Optioneel: `scripts/` of root **README-sectie** “twee terminals” / link naar `package.json` `stack:*` — **KISS**, geen verplichte `concurrently` tenzij team dat wil.
- [ ] **S8-D03** **CI**: compose blijft zoals [`.github/workflows/docker-compose.yml`](.github/workflows/docker-compose.yml); Playwright in CI **optioneel** in deze sprint (aparte job of follow-up).

#### QA

- [ ] **S8-Q01** **Playwright** toevoegen (`@playwright/test`), config baseren op `http://localhost:5173` (baseURL via env).
- [ ] **S8-Q02** Minimaal **één smoke-spec**: app opent, **no-auth** pad (geen login-blokkade), assertie op root/landings-UI (stabiele selector of `getByRole` waar mogelijk).
- [ ] **S8-Q03** `npm run test:e2e` (of `test:ui`) script + korte sectie in [`docs/qa/README.md`](docs/qa/README.md) (hoe lokaal draaien: stack + Vite verplicht).
- [ ] **S8-Q04** [`docs/qa/functional-checklist.md`](docs/qa/functional-checklist.md): regel toevoegen dat E2E-smoke **aanvult** checklist, niet vervangt.

### Definition of Done Sprint 8

- [ ] Documentatie + (optioneel) scripts: **één** heldere “start lokaal”-flow; geen conflicterende instructies met `docker-compose.local.yml`.
- [ ] Playwright smoke **groen** lokaals tegen draaiende **app (8000) + Vite (5173)**.
- [ ] Geen harde afhankelijkheid van Ollama in de eerste E2E-tests (rooktest blijft apart).
- [ ] LeadPM kan gate gebruiken: handmatige checklist **of** geautomatiseerde smoke als onderdeel van “lokale kwaliteit”.

### Input per persona

| Persona | Inbreng |
|---------|---------|
| **DevOps** | Scripts/docs, CI-grenzen, geen dubbele compose-“magie”. |
| **QA** | Playwright-scope, selectors, documentatie `test:e2e`. |
| **LeadPM** | Go/no-go na eerste groene smoke + bestaande rooktest/checklist. |

### Backlog — LLM assets (niet in Sprint 8 DoD)

Zie [`docs/llm-assets-format-and-improvements.md`](docs/llm-assets-format-and-improvements.md) (prompt/tool-uitlijning, `tool_choice`, fallbacks, tests). Geen verplichte S8-taken; wel input voor een vervolgsprint of incrementele PR’s.

---

*Bijgehouden door CoPM — laatste update: planning check + LLM-backlog link (2026-04-04); Sprint 8 PVA (2026-03-12)*
