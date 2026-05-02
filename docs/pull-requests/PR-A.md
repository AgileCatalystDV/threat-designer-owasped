# PR-A — Agent / parser — increment (code + tests)

Doel: **één reviewbare code-PR** (KISS) zonder grote QA-markdown-bijlagen. Hoeft niet alles in één zin te verklaren; per bestand of thema: **wat** is gewijzigd en **waarom**.

Gebruik dit document als **GitHub PR-beschrijving** (copy-paste) of als checklijst voor reviewers.

---

## Samenvatting (elevator pitch)

- **LangGraph** op een versie die past bij de geïmporteerde prebuilt-pakketten (voorkomt `ImportError` bij agent-start).
- **Gemma-compat**: tool-output kan `<channel|>[TOOL_REQUEST]` bevatten en meerdere blokken in één transcript; we nemen het **laatste** relevante fragment en parsen daarna pas JSON.
- **FlowsList JSON-varianten**: sommige modellen leveren `threat_actors` i.p.v. `threat_sources`, of `examples` (lijst) i.p.v. `example` — normaliseren vóór Pydantic-validatie.
- **Logging**: `print` vervangen door **structured logging** op foutpaden (backend service, init-script, MCP), zodat stack traces en context in logs landen i.p.v. stdout-ruis.

---

## Bestand-per-bestand (wat / waarom)

### Dependencies

| Bestand | Wat | Waarom |
|---------|-----|--------|
| `backend/threat_designer/requirements.txt` | `langgraph==1.0.10`, toevoeging `langgraph-prebuilt==1.0.8` | Aligneren met elkaar; lost typische `ExecutionInfo` / import-fouten op bij het laden van de agent-graaf. |
| `backend/sentry/requirements.txt` | `langgraph==1.0.10` | Zelfde graaf-versie als de threat-designer-module die Sentry naast draait (één waarheid, geen mismatch tussen containers). |

### Threat designer — parser & markers

| Bestand | Wat | Waarom |
|---------|-----|--------|
| `backend/threat_designer/tool_request_markers.py` | Constante `GEMMA_CHANNEL_TOOL_SUFFIX`, functie `slice_from_last_gemma_channel_tool_request` | Gemma plakt soms kanaal-syntax vóór `[TOOL_REQUEST]`. Er kunnen **meerdere** tool-blokken in de tekst staan (prompt-voorbeelden); alleen het **laatste** `<channel|>[TOOL_REQUEST]…` is de echte model-output. |
| `backend/threat_designer/flows_text_parser.py` | `_normalize_flows_list_arguments`, `_normalize_threat_source_dict`, `_coerce_example_field`, `_json_has_flows_list_shape` | LLM’s wijken af van het strakke schema: alias `threat_actors` → `threat_sources`, `examples` als lijst → één `example`-string, enz. Zonder normalisatie faalt `FlowsList.model_validate` terwijl de inhoud semantisch klopt. |
| `backend/threat_designer/model_service.py` | Voor `FlowsList`: eerst `slice_from_last_gemma_channel_tool_request` op de ruwe tekst, daarna `normalize_text_for_structured_fallback` | De volgorde is cruciaal: eerst het juiste transcriptfragment, dan marker-normalisatie en parsing. |
| `backend/threat_designer/attack_tree_models.py` | `logging` i.p.v. `print` in `__main__` demo | Geen ruis op stdout in voorbeeld-run; consistent met rest. |
| `backend/threat_designer/tools.py` | Docstring-voorbeelden: geen `print` in doctest-blokken; assertions i.p.v. uitvoer vergelijken | Voorkomt dat voorbeelden impliciet “run output” verwachten; blijft copy-paste-vriendelijk voor developers. |

### Backend API-service

| Bestand | Wat | Waarom |
|---------|-----|--------|
| `backend/app/services/threat_designer_service.py` | `LOG.error` / `LOG.exception` met `exc_info=True` i.p.v. `print` bij S3/Dynamo/status/trail-fouten | Productiepad: fouten moeten **gelogd** worden met stack trace en context (`job_id`, keys), niet onzichtbaar op stdout verdwijnen. |

### Scripts & MCP

| Bestand | Wat | Waarom |
|---------|-----|--------|
| `scripts/init_dynamo.py` | `logging`-module, `basicConfig`, `logger.info` / `logger.error` i.p.v. `print` | Init-script is onderdeel van dev/CI-flow; gelijk gedrag met rest van backend (zoekbaar, niveau’s, geen gemixte stderr-prints). |
| `mcp-server/threat_designer_mcp/server.py` | `logger.error(..., exc_info=True)` bij poll-fouten | Zelfde reden: fouten tijdens status-polling moeten traceerbaar zijn. |

### Tests

| Bestand | Wat | Waarom |
|---------|-----|--------|
| `test/threat_designer/test_tool_request_markers.py` | Tests voor `slice_from_last_gemma_channel_tool_request` (met/zonder punt, geen match) | Regressie op Gemma-suffix en fallback gedrag. |
| `test/threat_designer/test_flows_text_blocks.py` | `test_parse_flows_list_json_threat_actors_and_examples_alias` | Vergrendelt normalisatie van `threat_actors` + `examples` (lijst). |
| `test/threat_designer/test_structured_tool_json_gemma.py` | End-to-end parsing op **capture-fixtures** + synthetische varianten | Bewijs dat echte Gemma-vorm (channel + laatste tool-call + FlowsList JSON) parseert; fixtures staan **onder** `test/threat_designer/fixtures/` zodat PR-A **niet** afhangt van `docs/qa/*.md` (die gaan naar PR-B). |

### Nieuwe test-fixtures

| Pad | Wat | Waarom |
|-----|-----|--------|
| `test/threat_designer/fixtures/gemma4_asset_capture.md` | Snapshot van Gemma 4 **AssetsList**-achtige output | Zelfde inhoud als bedoelde QA-doc in `docs/qa/`; hier als **bron voor pytest** zodat CI/review geen geünificeerde docs-PR nodig heeft. |
| `test/threat_designer/fixtures/gemma4_dataflow_capture.md` | Snapshot van Gemma 4 **FlowsList** (data flows + boundaries + threat sources) | Idem; bevat o.a. `Format as requested.<channel|>[TOOL_REQUEST]` zodat slice-logica getest is. |

**Afspraak met PR-B:** de onderliggende captures kunnen **ook** in `docs/qa/` gezet worden voor menselijke leesbaarheid; inhoud **sync houden** met fixtures of expliciet vermelden dat docs een kopie zijn.

---

## Hoe te verifiëren (reviewer / QA)

```bash
export PYTHONPATH=backend/threat_designer
python3 -m pytest test/threat_designer/ -v --tb=short
```

Optioneel vollediger:

```bash
python3 -m pytest test/ -q
```

**Docker** (agent): image herbouwen na requirements-wijziging; container-start mag geen `ImportError` meer geven op LangGraph.

---

## Wat zit **niet** in PR-A

- Wijzigingen uitsluitend in `docs/qa/*` (lange Qwen/Gemma narrative dumps, checklistteksten) → **PR-B**.

---

## Titelvoorstel (GitHub)

`feat(agent): LangGraph pins, Gemma FlowsList parsing + logging (PR-A)`
