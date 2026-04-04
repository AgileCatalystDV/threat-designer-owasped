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
| (later) E2E | Optioneel Playwright — alleen na KISS-checklist stabiel |

## Basis

- Technische rooktest: [`../../quick-start-guide/local-stack-owasped.md`](../../quick-start-guide/local-stack-owasped.md)
- Sprintfocus: [`../../sprints.md`](../../sprints.md) — sectie *QA — functionele testen*

---

*Checklist v1 goedgekeurd door LeadPM — onderhoud door CoPM / QA.*
