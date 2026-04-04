# Functionele testchecklist — threat-designer-owasped

> **Doel:** handmatig afvinken na **relevante wijzigingen** (backend, Compose, frontend).  
> **Niet** vervangen door: `pytest` (die blijft op CI / lokaal draaien).  
> **Basis:** [`quick-start-guide/local-stack-owasped.md`](../../quick-start-guide/local-stack-owasped.md)

**Uitvoer:** LeadPM / QA  
**Datum / build / commit:** _________________________

---

## 0. Voorbereiding

| # | Stap | OK | Opmerking |
|---|------|----|-----------|
| 0.1 | Repo up-to-date; eventueel `docker compose … down` voor schone start | [ ] | |
| 0.1b | `.env.local` aanwezig: `cp .env.local.example .env.local` (indien nog niet) | [ ] | Zie `docker-compose.local.yml` |
| 0.2 | **Docker:** `npm run stack:up` (of `docker compose -f docker-compose.local.yml up --build`) — `dynamodb-init` **completed**, `minio` **healthy** | [ ] | Standaard **zonder** Sentry |
| 0.3 | **Frontend:** `npm install` (eenmalig); `npm run dev` — browser op URL die Vite toont (meestal **http://localhost:5173**) | [ ] | |
| 0.4 | `.env.development` → `VITE_APP_ENDPOINT=http://localhost:8000` | [ ] | |
| 0.5 | (Optioneel LLM) Ollama op host: `ollama serve` + model ge-pull’d | [ ] | Zonder Ollama: geen volledige AI-run |

---

## 1. Technische rooktest (API / storage)

| # | Check | Verwacht | OK | Opmerking |
|---|--------|----------|----|-----------|
| 1.1 | `GET http://localhost:8000/health` | `{"status":"ok"}` of vergelijkbaar | [ ] | |
| 1.2 | `GET http://localhost:8080/ping` (threat-designer) | Healthy JSON | [ ] | |
| 1.3 | DynamoDB op host: `curl` naar `http://localhost:8001/` | JSON met auth-fout / MissingAuthenticationToken = **levend** | [ ] | |
| 1.4 | MinIO: `GET http://localhost:9000/minio/health/live` | 200 | [ ] | |
| 1.5 | (Optioneel) Sentry: `GET http://localhost:8090/ping` | 200 + JSON | [ ] | Alleen na `npm run stack:up:full` / `--profile full`; zonder profiel: **verwacht** geen connect |

---

## 2. Frontend laadt

| # | Check | OK | Opmerking |
|---|--------|----|-----------|
| 2.1 | App opent zonder wit scherm / build error | [ ] | Intel Mac: Rollup `darwin-x64` bij problemen |
| 2.2 | Geen **CORS**-blokkade op calls naar `:8000` (DevTools → Network) | [ ] | Bij 500 eerst API-log: `docker compose logs app` |

---

## 3. Threat model — aanmaken (happy path)

| # | Check | OK | Opmerking |
|---|--------|----|-----------|
| 3.1 | “Submit threat model” / wizard opent | [ ] | |
| 3.2 | Titel + geldig diagram (png/jpeg) + minimaal verplichte stappen | [ ] | |
| 3.3 | **Start threat modeling** — Network: `POST …/threat-designer/upload` → geen `ERR_CONNECTION_REFUSED` | [ ] | App-container moet op :8000 luisteren |
| 3.4 | Na start: redirect of navigatie naar threat model **id**-route | [ ] | URL bevat UUID |

---

## 4. Threat model — pagina (lock & API)

| # | Check | OK | Opmerking |
|---|--------|----|-----------|
| 4.1 | `POST …/threat-designer/{id}/lock` geen **500** door ontbrekende env (Compose moet `LOCKS_TABLE`, … hebben) | [ ] | |
| 4.2 | Geen valse **CORS**-melding ten gevolge van 500 (eerst statuscode in Network) | [ ] | |
| 4.3 | Processing / stepper toont verwachte stappen (geen oneindige spinner zonder fout) | [ ] | |
| 4.4 | Console: geen kritieke React-warnings (bijv. `clickable` op DOM — opgelost met `$clickable`) | [ ] | |

---

## 5. Restore (verwacht gedrag)

| # | Check | OK | Opmerking |
|---|--------|----|-----------|
| 5.1 | `PUT …/threat-designer/restore/{id}` **zonder** `backup` in DynamoDB → **404** (geen blote 500 door verkeerde exception handler) | [ ] | Productiecode: `ViewError` niet slikken |
| 5.2 | Met echte backup (als scenario beschikbaar): restore slaagt of duidelijke fout | [ ] | |

---

## 6. Optioneel — Sentry & LLM

| # | Check | OK | Opmerking |
|---|--------|----|-----------|
| 6.1 | Sentry UI/flow: **`td-sentry`** draait (`stack:up:full`) + Vite **`VITE_SENTRY_ENABLED=true`** en **`VITE_SENTRY_BASE_URL=http://localhost:8090`** (lokaal); zonder `VITE_SENTRY_BASE_URL` verwacht de UI AWS Bedrock | [ ] | |
| 6.2 | Threat run voltooit met **Ollama** (model bereikbaar op host) | [ ] | Zonder Ollama: failure verwacht op agent |

---

## 7. Afronding

| # | Stap | OK |
|---|------|----|
| 7.1 | Bevindingen genoteerd (Git issue / sprintnotitie) | [ ] |
| 7.2 | Bij regressie: `pytest test/app/…` relevante subset gedraaid | [ ] |

---

## Bekende valkuilen (kort)

- **`ERR_CONNECTION_REFUSED` op :8000** → `app` draait niet of compose niet volledig.
- **DynamoDB init faalt** → tussen containers: `dynamodb-local:8000`, niet `:8001`.
- **Restore 500** → vaak ontbrekende `backup`; verwacht **404** met duidelijke payload na fix.
- **Sentry** → optioneel; geen blocker voor core submit/lock.

---

*Versie 1 — LeadPM goedgekeurd om checklist te gebruiken | CoPM + QA*
