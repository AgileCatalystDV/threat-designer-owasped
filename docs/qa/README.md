# QA — Functionele tests (threat-designer-owasped)

> **Persona:** QA — zie [`../team/personas.md`](../team/personas.md).  
> **CoPM:** deze map is de plek voor **testmatrix / checklists**; inhoud vult QA na afstemming met LeadPM.

## Doel

- **pytest** dekt services/routes — zie `test/app/`.
- **Functioneel** dekt **wat de gebruiker doet** in browser + lokale Docker stack (`docker-compose.local.yml`, Vite op `:5173`).

## Artefacten

| Artefact | Beschrijving |
|----------|--------------|
| [**functional-checklist.md**](functional-checklist.md) | **Actief** — handmatig afvinken: happy paths + bekende foutpaden |
| [`*.md` in deze map](.) | Optionele **QA-captures** (request/response dumps, LLM-logs) — ter referentie; geen vervanging voor pytest |
| [assetresponsegemma4.md](assetresponsegemma4.md) | Gemma 4: `[TOOL_REQUEST]` + JSON `AssetsList` — unit test: `test_structured_tool_json_gemma.py` |
| [dataflowresponsegemma4.md](dataflowresponsegemma4.md) | Gemma 4: `[TOOL_REQUEST]` + JSON `FlowsList` (finale tool-blok na channel-marker) — zelfde testmodule |
| **E2E smoke (Playwright)** | `npm run test:e2e` — minimale UI-check (**geen** volledige threat-model/LLM-flow). Zie onder. |

### Playwright (Sprint 8)

- **Scripts:** `npm run test:e2e` · `npm run test:e2e:ui` · `npm run test:e2e:headed`
- **Config:** [`playwright.config.js`](../../playwright.config.js) — `PLAYWRIGHT_BASE_URL` (default `http://localhost:5173`). Ontbreekt een draaiende Vite-dev-server, dan start Playwright `npm run dev` automatisch (`reuseExistingServer` buiten CI).
- **Eerste install:** na `npm install` eenmalig `npx playwright install chromium`.
- **Specs:** [`e2e/smoke.spec.js`](../../e2e/smoke.spec.js) — landingspagina + primaire CTA; **vult de checklist aan**, vervangt ze niet.

## Basis

- Technische rooktest: [`../../quick-start-guide/local-stack-owasped.md`](../../quick-start-guide/local-stack-owasped.md)
- Sprintfocus: [`../../sprints.md`](../../sprints.md) — sectie *QA — functionele testen*

---

*Checklist v1 goedgekeurd door LeadPM — onderhoud door CoPM / QA.*
