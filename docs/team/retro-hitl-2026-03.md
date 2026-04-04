# Tussentijdse review & retro — HITL, proces, spelregels

> **Datum sessie:** 2026-03-22 (vastlegging)  
> **Doel:** Eerlijke feedback over **Human-in-the-loop (HITL)**, wat kan beter, en welke **processen/spelregels** we willen aanscherpen.  
> **Status:** levend document — aanvullen na elk retro-moment.

**Gerelateerd:** [`src/agents.md`](../../src/agents.md) (manifest + spelregels), [`sprints.md`](../../sprints.md), [`docs/team/personas.md`](personas.md).

---

## 1. Context — waarom deze retro

- Het team werkt **virtueel** (persona’s + Cursor) met **LeadPM als enige menselijke gate** voor go/no-go, visie en vertrouwen.
- We hebben in korte tijd veel **infra, docs en tests** afgeleverd; nu is het moment om **samenwerking en HITL** te verfijnen vóór de volgende golven (o.a. Sprint 8, auth-gate, OWASP).

---

## 2. HITL (Human-in-the-loop) — wat werkt

| Thema | Observatie (team) |
|-------|---------------------|
| **Duidelijke gate** | “Geen auth tot rooktest akkoord” en **KISS** inference-pad zijn helder en vermijden scope-creep. |
| **Documentatie als contract** | `sprints.md`, `local-stack-owasped`, `functional-checklist` geven LeadPM **zingbare** checkpoints. |
| **Vertrouwen / kleine stappen** | Spelregels “niet overeagerly” en chirurgische wijzigingen passen bij een veilig tempo. |

*LeadPM — eigen aanvulling (optioneel):* …

---

## 3. HITL — wat kan beter (feedbackronde)

Onderstaande punten zijn **voorstellen** van het virtuele team; geen verwijt, wel verbeterkansen.

| # | Thema | Feedback | Mogelijke verbetering |
|---|--------|----------|------------------------|
| H1 | **Context-overdracht** | Lange threads verliezen soms **besluiten** of “waarom” achter een keuze. | Vastleggen in **1 regel in commit** of korte “Decision” in `sprints.md` / dit doc. |
| H2 | **Gate-latency** | Wachten op LeadPM-go is **bewust goed**, maar onduidelijkheid over “is dit akkoord?” kan vertragen. | Expliciet **✅ / ⏸ / ❌** in antwoord, of deadline “als geen reactie binnen X = akkoord met voorstel”. |
| H3 | **HITL vs automatisering** | Gevaar: te veel handwerk-checklist **of** te snel E2E zonder stabiele stack. | **Volgorde:** rooktest stabiel → checklist → Playwright-smoke (Sprint 8) — expliciet in planning. |
| H4 | **Cognitieve load** | LeadPM moet **techniek + product + proces** tegelijk volgen. | Periodiek **korte** sync: alleen risico’s en gates, niet elke PR-detail. |
| H5 | **Transparantie AI-werk** | Agent doet veel; diff is soms groot. | **Samenvatting eerst** (“wat gaat er veranderen en waarom”), dan pas uitvoeren — al in spelregels; blijven herhalen. |

### Besluit LeadPM (2026-03-22) + **CoPM akkoord**

| # | Stand | Toelichting |
|---|--------|-------------|
| **H1** | **Terecht — blijven versterken** | Context-overdracht: besluiten vastleggen (commit/sprints/retro). |
| **H2** | **Blijven volgen** | Gate-latency: expliciete ✅ / ⏸ / ❌ blijft het verbeterpunt — geen haast die HITL ondermijnt. |
| **H3** | **Terecht — blijven volgen** | Volgorde rooktest → checklist → Playwright (Sprint 8); geen E2E vóór stabiele basis. |
| **H4** | **Interessant — uitwerken** | Cognitieve load LeadPM: korte sync alleen risico’s/gates (zie P4-stijl samenvattingen). |
| **H5** | **Al in scope — werkt goed** | Samenvatting voor uitvoer zit in spelregels; geen extra retro-actie, wel blijven toepassen. |

**CoPM:** akkoord met bovenstaande prioritering. We bouwen verder met **respect en vertrouwen**, zonder **shadow IT**, zonder **overeager** build/coding/assistentie — alleen wat **LeadPM** en **documenteerde** gates toelaten.

*LeadPM — prioriteit focus (actief):* **H1, H3, H2, H4** — *H5: gehandhaafd via bestaande spelregels.*

---

## 4. Processen — review & verbeteringen

### 4.1 Huidige processen (kort)

| Proces | Waar beschreven | Opmerking team |
|--------|-----------------|----------------|
| Sprint & DoD | `sprints.md` | Werkt; Sprint 8 maakt E2E-smoke expliciet. |
| Rooktest / lokale stack | `quick-start-guide/local-stack-owasped.md` | Bron van waarheid; compose-profielen (`full`) vereisen **duidelijke** communicatie. |
| QA | `docs/qa/functional-checklist.md` | Aanvulling op pytest; blijft LeadPM/QA-eigendom. |
| Spelregels | `src/agents.md` | Plan eerst, goedkeuring, kleine stappen. |

### 4.2 Voorgestelde proces-aanscherpingen

| ID | Voorstel | Eigenaar | Status |
|----|----------|----------|--------|
| P1 | **Retro-doc** (dit bestand) **trimester** of na elke grote milestone kort invullen | CoPM + LeadPM | 🔄 lopend |
| P2 | **“Beslissingen log”** in `sprints.md` blijft leidend; grote keuzes altijd **1 zin + datum** | CoPM | ✅ **akkoord LeadPM** — ondersteunt H1 |
| P3 | **Blokkades** in chat expliciet labelen: `BLOCKER:` + wat nodig is van LeadPM | Alle persona’s | ✅ **akkoord LeadPM** — ondersteunt H2 |
| P4 | Na **merge naar main**: korte **“wat & waarom”** in PR of in commit-body (ook voor LeadPM-overzicht) | Dev / DevOps | ✅ **akkoord LeadPM** — ondersteunt H4 |

*LeadPM — P1–P4:* **P2–P4 bevestigd** (2026-03-22). P1 blijft periodiek onderhoud.

---

## 5. Spelregels — herbevestiging & aanvullingen

Bestaande spelregels ([`src/agents.md`](../../src/agents.md)) blijven de basis. **Aanvullingen na deze retro:**

| Regel | Formulering (voorstel) |
|-------|-------------------------|
| **Transparantie** | Geen stille scope-uitbreiding: als een taak groter wordt dan geschat → **stop + meld** aan LeadPM met opties. |
| **HITL-respect** | Geen druk om gates te “skippen”; als tijd dringt → **scope verkleinen**, niet de gate. |
| **Feedback** | Dit retro-doc mag **kort** bijgewerkt worden; lange essays zijn niet nodig — **bullets** volstaan. |
| **Geen shadow IT** | Geen parallelle stacks, secrets-routes of besluiten **buiten** repo/docs; bron van waarheid = **git + `sprints.md`**. |
| **Geen overeager assistentie** | Geen stille scope-uitbreiding of “extra” coding hulp buiten LeadPM-go — zie bestaande spelregels. |

**Besluit LeadPM — spelregels officieel uitbreiden in `agents.md`?** ✅ **ja** (2026-03-22) — doorgevoerd in [`src/agents.md`](../../src/agents.md).

---

## 6. Rondje feedback — per persona (virtueel team)

Korte stem — **wat waarderen we aan HITL, wat vragen we van LeadPM?**

| Persona | Plus (HITL) | Vraag / verbetering aan LeadPM |
|---------|-------------|--------------------------------|
| **CoPM** | Duidelijke backlog en sprintteksten maken docs testbaar. | Soms veel parallelle topics — **1 prioriteit per week** helpt documentatie scherp te houden. |
| **Dev** | Go/no-go voorkomt refactor-chaos. | Bij **grote diffs**: expliciet “review deze 3 bestanden eerst” verlaagt load. |
| **DevOps** | Compose als single source of truth sluit aan bij gate-denken. | Als host/OS verschilt (Intel vs ARM), **vroeg** signaleren in checklist voorkomt churn. |
| **QA** | Checklist + toekomstige Playwright passen bij “mens ziet UI”. | Tijd voor **één** end-to-end handmatige run vóór “alles geautomatiseerd” — in planning zetten. |
| **Sec** | Geen auth tot basis stabiel is logisch voor threat-review. | Wanneer **STRIDE/LLM-top-10** dieper wil: expliciete **review-sprint** plannen, niet “ertussen”. |

*LeadPM — reactie / eigen feedback aan het team (optioneel):* Zie besluit **§3** — focus **H1, H3, H2, H4**; vertrouwen, geen shadow IT, geen overeager build.

---

## 7. Acties (follow-up)

| # | Actie | Eigenaar | Deadline / sprint |
|---|--------|----------|-------------------|
| A1 | Retro-doc: **H-besluiten** vastgelegd | LeadPM + CoPM | ✅ 2026-03-22 |
| A2 | Spelregel-aanvulling in **`agents.md`** | CoPM + LeadPM | ✅ 2026-03-22 |
| A3 | P2–P4 bevestigd; P1 periodiek | LeadPM | lopend |

---

## 8. Changelog van dit document

| Datum | Wijziging |
|-------|-----------|
| 2026-03-12 | Eerste vastlegging — tussentijdse review HITL + proces + rondje feedback (virtueel team). |
| 2026-03-22 | LeadPM-besluit H1–H5; CoPM akkoord; P2–P4 bevestigd; `agents.md` uitgebreid (shadow IT, overeager, retro-spelregels). |

---

*Bijgehouden door CoPM — input van alle persona’s; LeadPM is eigenaar van besluiten. Retro: vertrouwen, geen shadow IT, geen overeager build.*
