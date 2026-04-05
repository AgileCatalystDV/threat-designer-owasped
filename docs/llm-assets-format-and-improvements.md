# LLM assets: verwacht formaat & mogelijke verbeteringen

> Doel: één plek voor **wat de code verwacht** (structured tools) versus **wat prompts beschrijven** (vrije tekst), plus een **backlog** van verbeteringen. Zie implementatie in `backend/threat_designer/` (`state.py`, `prompts.py`, `model_service.py`, `utils.py`, `nodes.py`).

---

## Verwachte datastructuur (canonical)

De bron van waarheid is **Pydantic** in `state.py`:

| Veld | Type / waarden |
|------|----------------|
| `AssetsList.assets` | Lijst van `Assets` |
| Elk `Assets` | `type`: exact `"Asset"` of `"Entity"` · `name` · `description` · `criticality`: `"Low"` \| `"Medium"` \| `"High"` |

Runtime wordt dit via LangChain **`bind_tools([AssetsList])`** aan het model gepresenteerd als **OpenAI-compat function / tool call** met JSON-args die exact dit schema volgen.

---

## Wat de code na `invoke()` verwacht

In `model_service._process_structured_response` wordt het antwoord verwerkt als:

- `AIMessage.tool_calls` **niet leeg**
- `tool_calls[0]["args"]` = dict die **`AssetsList` valideert** (na eventuele string-sanitization).

**Platte tekst alleen** in `message.content` (bijv. `Type: … Name: …`) **zonder** bijbehorende `tool_calls` leidt tot een fout (o.a. lege `tool_calls` → geen `[0]`).

---

## Spanning met het prompt (`asset_prompt`)

In `prompts.py` beschrijft `<output_format>` een **menselijk leesbaar** blok per item:

```text
Type: [Asset | Entity]
Name: …
Description: …
Criticality: [Low | Medium | High]
```

Dat is **niet** hetzame als de JSON-tool-args; lokale modellen (LM Studio / Ollama) volgen vaak dit tekstformaat en **vullen geen tool_calls in**. De prompt en de technische binding zijn daardoor **niet uitgelijnd** tenzij het model expliciet tool-calling gebruikt.

---

## Retry-pad (structured output)

Bij een fout in de eerste parse roept `handle_asset_error` (als **reasoning / “thinking”** in de config aan staat) `_retry_with_structure` aan: ruwe tekst uit het antwoord gaat naar `structure_prompt`, daarna **`with_structured_output(AssetsList)`** op het struct-model.

Als **reasoning uit** staat, valt deze retry weg → bij lege `tool_calls` blijft het een harde fout.

---

## Mogelijke verbeteringen (backlog)

Prioriteit en planning: **LeadPM / CoPM**; technische uitvoering **Dev** (agent), evt. **Sec** voor prompt-lekken / logging.

| # | Verbetering | Doel |
|---|-------------|------|
| 1 | **Prompt uitlijnen met tools** — in `asset_prompt` expliciet vereisen dat het antwoord via de **`AssetsList`-tool** komt (geen alleen-vrije-tekst als bron van waarheid). | Minder “alleen tekst” zonder `tool_calls`. |
| 2 | **`tool_choice` voor lokale provider** — voor `MODEL_PROVIDER_OLLAMA` / LM Studio: geforceerde tool (na teambesluit: dict vs. string vs. `required`) zodat het model niet “alleen chat” teruggeeft. | Betrouwbaardere `tool_calls` lokaal. |
| 3 | **Fallback bij lege `tool_calls`** — als `content` wel tekst heeft: altijd (of alleen lokaal) hetzelfde pad als `_retry_with_structure` proberen, **ongeacht** `reasoning`. | Minder crashes; wel extra LLM-call + kosten. |
| 4 | **Parser voor het tekstformaat** — `asset_text_blocks.extract_asset_dicts_from_text` (regex + thinking-strip, geen zware deps); `asset_text_parser.parse_assets_list_from_text` bouwt `AssetsList`. Fallback in `model_service._process_structured_response` als `tool_class is AssetsList` en tool-args ontbreken of falen. Voorbeeldantwoord: `docs/qa/assetresponseqwen.md`. Tests: `test/threat_designer/test_asset_text_parser.py` (unit op extract, zonder langgraph). | Robuustheid zonder tweede modelcall. |
| 5 | **Logging / debug** — `LOG_LEVEL=DEBUG`, `llm_raw_response` (zie `model_service`) blijven gebruiken tot het gedrag stabiel is; daarna documenteren wat productie-log mag. | Observability, geen PII in logs. |
| 6 | **Tests** — unit test voor `sanitize_tool_invocation_args` / `extract_text_from_base_message`; optioneel integration mock voor lege `tool_calls`. | Regressie voorkomen. |

---

## Gerelateerde bestanden

| Bestand | Rol |
|---------|-----|
| `backend/threat_designer/state.py` | `Assets`, `AssetsList` |
| `backend/threat_designer/prompts.py` | `asset_prompt`, `structure_prompt` |
| `backend/threat_designer/model_service.py` | `invoke_structured_model`, `_process_structured_response`, debug-log |
| `backend/threat_designer/asset_text_blocks.py` | Plain-text extractie (`Type:` / `Name:` / …) |
| `backend/threat_designer/asset_text_parser.py` | Dicts → `AssetsList` (Pydantic) |
| `backend/threat_designer/utils.py` | `handle_asset_error`, `_retry_with_structure`, tekstextractie / sanitization |
| `backend/threat_designer/nodes.py` | `define_assets` → `invoke_structured_model(..., [AssetsList], ..., "model_assets")` |

---

*Toegevoegd: 2026-04-04 — backlog kan in `sprints.md` worden opgenomen bij een sprint of als aparte follow-up.*

---

## Optioneel: `[TOOL_REQUEST]` … `[END_TOOL_REQUEST]` (kleine modellen)

Sommige modellen zetten intros **vóór** de gestructureerde payload. Als de ruwe `content` het volgende patroon bevat, gebruikt `tool_request_markers.normalize_text_for_structured_fallback` alleen het segment **tussen** de markers (exacte strings: `[TOOL_REQUEST]` en `[END_TOOL_REQUEST]`). Alles ervoor en erna wordt niet aan de plain-text parsers gegeven.

- **Zonder** deze markers: gedrag ongewijzigd t.o.v. de bestaande Qwen/tekst-fallbacks (`parse_*_from_text`).
- Implementatie: `backend/threat_designer/tool_request_markers.py`, aangeroepen vanuit `model_service._process_structured_response` vóór `parse_assets_list_from_text` / flows / threats / gap.

### JSON tool-wrapper (Gemma / LM Studio)

Na marker-normalisatie kan de inhoud **JSON** zijn in de vorm ``{"name": "AssetsList", "arguments": {"assets": [...]}}`` (OpenAI-tool-stijl). ``structured_tool_json`` + ``parse_assets_list_from_text`` valideren dat via Pydantic. Bekende typo: verkeerde key ``"、name"`` → wordt gerepareerd vóór ``json.loads``. Zie ``docs/qa/assetresponsegemma4.md`` en ``test_structured_tool_json_gemma.py``.

Zelfde patroon voor **FlowsList** en **ThreatsList** in ``flows_text_parser`` / ``threats_text_parser`` (tool-naam ``FlowsList`` / ``ThreatsList``, ``arguments`` met de verwachte velden).

