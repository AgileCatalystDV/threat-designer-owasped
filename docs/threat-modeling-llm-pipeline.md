# Threat modeling: LLM-pipeline, routes en fasen (owasped fork)

> **Doel van dit document:** in één plek zien *waar* de code een LLM vraagt, *hoe* de request van de API tot de graph loopt, welke *fasen* de tekening doorloopt, en hoe je **offline** test- of finetune-data kunt opbouwen.  
> Diep technische achtergrond en STRIDE-details: [threat_designer_agent.md](threat_designer_agent.md) · tool/JSON-format: [llm-assets-format-and-improvements.md](llm-assets-format-and-improvements.md)

---

## 1. Centrale laag (alle modelcalls)

| Laag | Bestand | Rol |
|------|---------|-----|
| Model-aanroepen | `backend/threat_designer/model_service.py` | `invoke_structured_model`, `generate_summary`, `get_model_with_tools` → `bind_tools` + `invoke` |
| Clients per rol | `backend/threat_designer/model_utils.py` | `initialize_models()` — o.a. `assets_model`, `flows_model`, `threats_model`, `threats_agent_model`, `gaps_model`, `summary_model`, `struct_model` · endpoints via `INFERENCE_BASE_URL` / provider |
| Structured retry | `backend/threat_designer/utils.py` | `_retry_with_structure` — extra call om output te structureren |
| Promptteksten (klassieke stappen) | `backend/threat_designer/prompts.py` | o.a. `summary_prompt`, `asset_prompt`, `flow_prompt`, `threats_prompt`, `threats_improve_prompt`, `gap_prompt`, `create_agent_system_prompt` |
| Attack tree prompts | `backend/threat_designer/attack_tree_prompts.py` | Systeem + human voor attack-tree agent |

**Config:** Docker gebruikt `env_file: .env.local` (zie `docker-compose.local.yml`) — o.a. `INFERENCE_BASE_URL`, `INFERENCE_API_KEY`, `MODEL_PROVIDER`, `LOCAL_MODEL`.

---

## 2. HTTP: van UI/API naar de agent

De **FastAPI-app** (`backend/app`) roept de agent **niet** direct als OpenAI-client aan; het stuurt HTTP naar de threat-designer container.

| Entry | Wat | Agent-endpoint |
|-------|-----|----------------|
| `POST /threat-designer` (en `/threat-designer/mcp` variant) | Start threat model job → o.a. `httpx.post` naar agent | `{THREAT_DESIGNER_URL}/invocations` |
| Attack tree flows (via `attack_tree_service`) | Aparte job | Zelfde `/invocations` met `type: "attack_tree"` in de payload |

**Agent** (`backend/threat_designer/agent.py`):

- `POST /invocations` — `type == "attack_tree"` → `workflow_attack_tree` · anders → hoofd-`agent` graph + `_initialize_state` (S3 → base64, `iteration`, `replay`, `instructions`, …).

Zie ook: `backend/app/services/threat_designer_service.py` (payload naar `/invocations`).

---

## 3. Hoofd-LangGraph (high level)

Bestand: `backend/threat_designer/workflow.py`

| Node (concept) | Code / service | LLM? |
|----------------|----------------|------|
| `image_to_base64` | `SummaryService.generate_summary` | Ja — samenvatting diagram + context |
| `assets` | `AssetDefinitionService` | Ja — `model_assets` |
| `flows` | `FlowDefinitionService` | Ja — `model_flows` |
| `threats` (lege router) + routing | `route_threats_by_iteration` | — |
| `threats_agentic` | Subgraph `workflow_threats.threats_subgraph` | Ja — multi-turn + tools |
| `threats_traditional` | `ThreatDefinitionService.define_threats` | Ja — structured threats / loop |
| `finalize` | `WorkflowFinalizationService` | Nee (persist / status) |

**Router na `flows` (en replay):** `state["iteration"] == 0` → **agentisch** subgraph; anders → **traditioneel** node.

- `iteration` komt uit de invocation payload (default in code: `0` = auto / agentisch).

**Replay** (`replay: true`): state uit DynamoDB; graph start na summary-node op de threats-router — assets/flows/summary-stap wordt overgeslagen t.o.v. volledige “nieuwe” run (zie `route_replay` in `workflow.py` + `_handle_replay_state` in `agent.py`).

---

## 4. Fasen: tekening interpreteren en “vragen” per stap

| Fase | Inhoud / input | Wat het model krijgt (kort) | Prompts / builders |
|------|------------------|----------------------------|--------------------|
| 0. Inladen | S3-key → base64; `description`, `assumptions`, `application_type`, `instructions` | — | `agent.py` state init · `MessageBuilder` |
| 1. Samenvatting | Eerste brede interpretatie | System + multimodal human (woordlimiet) | `summary_prompt()` |
| 2. Assets | Componenten, stores, entiteiten | `asset_prompt(application_type)` + plaat/tekst | `nodes.py` · `message_builder.py` |
| 3. Dataflows | Stromen + grenzen + threat sources o.b.v. assets | `flow_prompt` + embedded assets | idem |
| 4a. Threats **agentisch** | Zelfde context in elke beurt; ReAct + tools | `create_agent_system_prompt` + `create_threat_agent_message` | `workflow_threats.py` · `tools.py` |
| 4b. Threats **traditioneel** | Structured threat lists / improve loops | `threats_prompt` / `threats_improve_prompt` | `ThreatDefinitionService` in `nodes.py` |
| 5. Gap-analyse (praktijk) | Vooral in **agentische** modus via tool `gap_analysis` | `gap_prompt` + huidige catalogus | `tools.py` (`gap_analysis`) |

**Opmerking:** In `nodes.py` bestaat ook `GapAnalysisService` voor een klassieke graph-node `"gap_analysis"`. De **statische** graph in `workflow.py` registreert die node niet als aparte stap; in de **standaard flow** (`iteration == 0`) ga je naar de agentische subgraph, waar **gap** vooral via de **`gap_analysis`-tool** loopt. Voor exact gedrag na wijzigingen: zie de actuele `Command(goto=...)`-logica in `ThreatDefinitionService` / `GapAnalysisService` en de gecompileerde graph.

---

## 5. Subgraphs en attack tree

| Onderdeel | Bestand | Patroon | Modelrol |
|-----------|---------|---------|----------|
| Threats agent | `workflow_threats.py` | `agent` → `tools` → `agent` / `continue` → parent `finalize` | `model_threats_agent` (tools) |
| Attack tree | `workflow_attack_tree.py` | Zelfde idee: agent + tools + continue | `model_attack_tree_agent` (vast reasoning-budget in `agent.py`) |

---

## 6. Sentry (optioneel, andere use case)

Diagram-/threatmodel-assistent in de browser: `backend/sentry/*` — eigen `ChatOpenAI` config (`sentry/config.py`) en streaming (`streaming.py`). Niet dezelfde graph als `workflow.py`; zie [sentry_design.md](sentry_design.md).

---

## 7. Offline teststructuur en finetune-denken

**Doel:** vaste invoer → verwachte output per fase, zonder verrassingen in productie of voor supervised finetuning / eval.

1. **Scenario-fixture** (`scenario_id`): `description`, `assumptions`, `application_type`, `instructions`, pad naar **afbeelding**, en expliciet `iteration` + `replay`.
2. **Golden files per fase** (JSON): `summary` → `assets` → `flows` → `threats` (en eventueel tool-trace als JSONL voor agentisch).
3. **Bestaande parsers** hergebruiken als contract: `asset_text_blocks` / `flows_text_parser` / `threats_text_parser` / `gap_analysis_text_parser` (zie tests onder `test/threat_designer/`).
4. **Integratie:** DynamoDB Local + MinIO + upload testobject → `POST /invocations` → vergelijk state/trail met golden; of **mock** `ChatOpenAI` die vaste tool-returns levert.
5. **Finetune-records (instruction tuning):** per fase: `instruction` = system + context; `input` = (tekst van) human message; `output` = genormaliseerd JSON volgens Pydantic-tool schema.

Rooktest-checklist: [qa/functional-checklist.md](qa/functional-checklist.md).

---

## 8. Gerelateerde bestanden (snel zoeken)

| Onderwerp | Pad |
|-----------|-----|
| Invocations handler | `backend/threat_designer/agent.py` |
| Graph | `backend/threat_designer/workflow.py` |
| Threats subgraph | `backend/threat_designer/workflow_threats.py` |
| Services per node | `backend/threat_designer/nodes.py` |
| Tools (o.a. `gap_analysis`, `add_threats`) | `backend/threat_designer/tools.py` |
| API → agent | `backend/app/services/threat_designer_service.py` · `attack_tree_service.py` |
| Routes | `backend/app/routes/threat_designer_route.py` · `attack_tree_route.py` |

---

*Laatst bijgewerkt als navigatiehulp voor de owasped-fork; bij twijfel de broncode en `threat_designer_agent.md` leidend.*
