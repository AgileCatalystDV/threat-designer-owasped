# Cursor / Composer — notitie voor het team

> **Doel:** één plek met **feitelijke** context over de IDE-assistent (Cursor) versus het **product** (threat-designer-owasped + Ollama op de host).  
> **Geen** vervanging van officiële Cursor-documentatie.

---

## Composer 2 en Kimi K2.5

- **Cursor** documenteert **Composer 2** als coding model; zie de officiële modelpagina:  
  **[Composer 2 — Cursor Docs](https://cursor.com/docs/models/cursor-composer-2)**.
- In de publieke berichtgeving (o.a. na bevestiging door Cursor) wordt **Composer 2** in verband gebracht met **Kimi K2.5** (Moonshot AI, open-source model). Cursor beschrijft **eigen training** bovenop een basis — exacte details en benchmarks volgen uit **Cursor**, niet uit deze repo.
- **Licenties en leveranciers** van de IDE-modellen zijn een afspraak tussen **jou / je organisatie** en **Cursor**; dit projectrepo hoeft dat niet te dupliceren.

---

## Scheiding met dit project (belangrijk)

| Laag | Wat het is |
|------|------------|
| **Cursor / Composer** | Assistent in de IDE voor prompts, edits, refactors — **externe** dienst van Cursor. |
| **threat-designer stack** | Jouw **lokale** app: Docker, FastAPI, **Ollama op de host** voor echte threat-model inference — zie [`quick-start-guide/local-stack-owasped.md`](../../quick-start-guide/local-stack-owasped.md). |

Het **projectdoel** blijft: **KISS**, **geen MCP-backloop** van de product-stack naar het Cursor-interne model — zie [`src/agents.md`](../../src/agents.md) en [`sprints.md`](../../sprints.md).

---

## Changelog

| Datum | Wijziging |
|-------|-----------|
| 2026-03-23 | Eerste versie — tooling-notitie op verzoek team (transparantie IDE vs product). |

---

*CoPM — link vanuit [`docs/README.md`](../README.md) en [`src/agents.md`](../../src/agents.md).*
