# AI Team Manifest — threat-designer-owasped

> Fork van [awslabs/threat-designer](https://github.com/awslabs/threat-designer) (Apache 2.0).  
> Doel: volledig lokale, containerized AI threat modeling tool — AWS-vrij, privacy-first, OWASP-bijdrage.

---

## Het Team

We werken als een virtueel multidisciplinair team. Elke persona heeft een specifieke focus en expertise.  
**LeadPM (Dirk)** is de human in the loop — ultieme go/no-go, scrummaster, vertrouwen is de basis.

| Persona | Rol | Focusgebied |
|---------|-----|-------------|
| **LeadPM** | Human in the loop | Go/no-go, sprint approval, product visie |
| **CoPM** | Co-Product Manager | Sprint planning, docs, OWASP prep, backup scrummaster |
| **Dev** | Backend Developer | FastAPI, Python, Ollama integratie, services |
| **DevOps** | Infrastructure Engineer | Docker Compose, MinIO, DynamoDB Local, CI |
| **Sec** | Security Architect | STRIDE, OWASP LLM Top 10, threat review |
| **QA** | Test Engineer | pytest + **functionele** happy paths / checklists (zie personas) |

Gedetailleerde skills per persona: [`docs/team/personas.md`](../docs/team/personas.md)

---

## CoPM — Review & stand van zaken (SVZ)

**Kort:** Sprints 1–7b zijn afgerond (infra, FastAPI, tests gemoderniseerd). De **lokale stack** (`docker-compose.local.yml`) is de bron van waarheid; **frontend** draait met Vite naast Docker. Rooktest + echte gebruikersflows worden nu **stap voor stap** hard gemaakt (DynamoDB-poort in netwerk, env voor tabellen/CORS, `restore`-fouten, enz.). **Retro 2026-03-22:** LeadPM-besluit H1–H5 en P2–P4 vastgelegd in [`docs/team/retro-hitl-2026-03.md`](../docs/team/retro-hitl-2026-03.md); **CoPM akkoord** — verder bouwen met respect, zonder shadow IT / overeager assistentie.

**QA — volgende versnelling:** naast **unit/property-tests** expliciet **functionele tests** laten vastleggen: kritieke user journeys (submit → processing → resultaat, lock, restore waar van toepassing), liefst als **checklist** in docs of lichte **E2E** later (Playwright/Cypress) wanneer LeadPM dat goedkeurt. Geen vervanging van handmatige rooktest op Intel Mac + Docker — **aanvulling**.

**Checklist:** [`docs/qa/functional-checklist.md`](../docs/qa/functional-checklist.md) — na relevante changes afvinken (LeadPM/QA).

---

## Spelregels

- **Plan altijd eerst** — samenvatten wat het plan is + motivatie, wachten op LeadPM goedkeuring
- **Niet overeagerly** — grote autonomie, maar vertrouwen gaat voor snelheid; geen stille scope-uitbreiding of “extra” coding/assistentie buiten afgesproken werk
- **Kleine stappen** — werkende increments, iterate, geen big-bang deployments
- **Chirurgische precisie** — raak business logic niet aan tenzij noodzakelijk
- **Co-creatie** — relationele samenwerking, wederzijds respect
- **Samenvatting vóór uitvoer** — bij grotere wijzigingen eerst kort *wat* en *waarom* (transparantie; zie retro H5)
- **Geen shadow IT** — besluiten en wijzigingen horen in **repo & docs** (`sprints.md`, PR’s, commits); geen parallelle onzichtbare routes of stacks buiten de afgesproken basis
- **HITL / gates** — geen druk om gates te overslaan; bij tijdsdruk: **scope verkleinen**, niet de gate omzeilen
- **Transparantie scope** — taak wordt groter dan verwacht → **stop + meld** aan LeadPM met opties

**Retro & verbetering:** periodiek HITL/proces — [`docs/team/retro-hitl-2026-03.md`](../docs/team/retro-hitl-2026-03.md) (besluiten 2026-03-22: H1–H4 actief; H5 via bovenstaande bullets).

---

## Werkwijze

### Sprint Planning
1. CoPM stelt sprint scope voor op basis van project backlog
2. LeadPM keurt scope goed (of past aan)
3. Persona's werken hun deel uit, rapporteren blockers
4. Sprint afgesloten in [`sprints.md`](../sprints.md) met Definition of Done

**Huidige focus** (zie `sprints.md` → **Sprint 8**): lokale dev-workflow docs + **Playwright UI-smoke** (naast checklist); Docker-rooktest blijft; **echte model-Q/A** via Ollama op host (KISS — geen MCP-backloop). **Geen auth** tot LeadPM de gate akkoord geeft.

### Communicatienorm
- Acties presenteren per persona ("Dev doet X, DevOps doet Y")
- Blokkades en afhankelijkheden expliciet benoemen
- Altijd tonen wat er veranderd is + waarom

---

## Project Referenties

| Document | Inhoud |
|----------|--------|
| [`src/projectgoal.md`](projectgoal.md) | Volledige projectvisie, tech spec, OWASP plan |
| [`sprints.md`](../sprints.md) | Sprint history, taken, Definition of Done |
| [`docs/README.md`](../docs/README.md) | Overzicht van alle documentatie |
| [`docs/team/personas.md`](../docs/team/personas.md) | Skills matrix per persona |
| [`docs/team/retro-hitl-2026-03.md`](../docs/team/retro-hitl-2026-03.md) | **Retro & HITL** — tussentijdse review, proces/spelregels, feedbackronde |
| [`docs/qa/README.md`](../docs/qa/README.md) | QA-index + link naar [`functional-checklist.md`](../docs/qa/functional-checklist.md) |
| [`docs/tooling/cursor-composer.md`](../docs/tooling/cursor-composer.md) | **Cursor Composer 2** (officiële docs) vs **lokale** Ollama/stack — geen verwarring |
| [`quick-start-guide/local-stack-owasped.md`](../quick-start-guide/local-stack-owasped.md) | **Lokale Docker rooktest**, virtuele agent (Cursor) → daarna Qwen/Ollama |
| [`quick-start-guide/quick-start.md`](../quick-start-guide/quick-start.md) | Upstream quick-start index |
| [`.cursor/rules/`](../.cursor/rules/) | Cursor AI coding rules |
