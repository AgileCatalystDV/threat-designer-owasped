# Lokale stack — threat-designer-owasped

> Fork met **Docker Compose**, **DynamoDB Local**, **MinIO**, **FastAPI**, **threat-designer agent** en **Sentry**.  
> LLM: **Ollama + Qwen** (of ander model) op de **host** — niet in de container (GPU op Apple Silicon).

---

## 1. Workflow: hier (Cursor) scherp → zelf model vraag/antwoord via Ollama

We doen dit bewust in twee fasen — **KISS**, bewust **geen** MCP of technische “backloop” naar het Cursor-interne model.

| Fase | Waar | Wat |
|------|------|-----|
| **A — Hier in Cursor** | Chat met de **IDE-agent** (zoals nu) | **Jij** voert het gesprek: prompts, STRIDE-vragen, verwacht gedrag, edge cases. Geen zware GPU, geen Ollama nodig voor dit denkwerk. |
| **B — Lokale Qwen (Ollama)** | Host + containers | **Jij** triggert echte inference: threat-designer / Sentry via de stack, LLM gaat naar **Ollama** op de host (`INFERENCE_BASE_URL` → `http://host.docker.internal:11434/v1`). Dat is het echte **model vraag/antwoord** — niet geautomatiseerd vanuit Cursor naar jouw app. |

**Waarom zo?**

- Minder trial-and-error tegen een groot lokaal model.
- Sneller feedback op *wat* je vraagt voordat je *hoe* het model antwoordt meet.
- Optioneel: zelfde logica testen met **pytest** + mocks — zonder LLM.

> **Nullius in verba**: check zelf of je stack draait (sectie 3); Cursor-chat vervangt geen contract- of integratietest.

---

## 2. Vereisten (host)

- **Docker** + Docker Compose  
- **Node.js** + **npm** — voor de **frontend** (niet in Compose): `npm install` en `npm run dev` in de projectroot; Vite draait typisch op **http://localhost:5173** en praat met de API op **:8000** (zie `.env.development`).  
- **Ollama** op de host (aanbevolen voor Qwen), bijv.:

  ```bash
  brew install ollama
  ollama serve
  ollama pull qwen3:32b
  ```

- Project-root: **kopieer** [`../.env.local.example`](../.env.local.example) naar **`.env.local`** (gitignored):

  ```bash
  cp .env.local.example .env.local
  ```

  Belangrijk voor LLM: `MODEL_PROVIDER=ollama`, `INFERENCE_BASE_URL=http://host.docker.internal:11434/v1`, `LOCAL_MODEL=qwen3:32b` (of jouw modelnaam) — staan in het voorbeeldbestand.

---

## 3. Rooktest (Docker)

Vanaf de **repository root**:

**Aanbevolen (npm — zelfde als `docker compose` hieronder):**

```bash
npm run stack:up
```

**Zonder Sentry** (default): API + agent + storage — geen AI-assistent op :8090.

```bash
docker compose -f docker-compose.local.yml up --build
```

**Met Sentry** (AI-assistent op **8090**):

```bash
npm run stack:up:full
# of:
docker compose -f docker-compose.local.yml --profile full up --build
```

Compose-profiel **`full`** start de `sentry`-service; zonder profiel draait die **niet** (bewust lichter).

Wacht tot `dynamodb-init` en `minio-init` klaar zijn en services stabiel draaien.

### 3.1 Poorten (default)

| Service | Poort | Check |
|---------|-------|--------|
| **app** (FastAPI) | 8000 | API gateway vervanger |
| **threat-designer** | 8080 | Agent HTTP (`/invocations`, health) |
| **sentry** | 8090 | Alleen met `--profile full` / `npm run stack:up:full` |
| **MinIO** | 9000 (API), 9001 (console) | S3-compat |
| **DynamoDB Local** | Host **8001** → container **8000** | Vanaf je Mac: `localhost:8001`. Tussen containers: `dynamodb-local:8000` (niet `:8001`). |
| **Ollama** (host) | 11434 | Niet in Compose; wel `extra_hosts` naar host |

**Belangrijk:** `dynamodb-init` en alle backend-services gebruiken in Compose **`http://dynamodb-local:8000`**. Poort **8001** is alleen de mapping op je host; binnen het Docker-netwerk luistert de service op **8000**. Verkeerde poort → `dynamodb-init` blijft wachten en eindigt met exit 1.

### 3.2 Minimale checks

**Storage alleen** (DynamoDB + MinIO) kun je al testen zonder API te draaien.

**Standaard stack** (`npm run stack:up` zonder profiel) — **app** (8000), **threat-designer** (8080), storage; **geen** Sentry op 8090.

**Met Sentry** — gebruik `npm run stack:up:full` of `docker compose … --profile full up`. Daarna is **8090** bereikbaar. Zonder `full` faalt `curl` naar `8090` — **verwacht**; geen netwerkfout.

```bash
# DynamoDB Local leeft (400 op auth = OK — geen echte credentials)
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8001/

# MinIO health
curl -sf http://localhost:9000/minio/health/live && echo " MinIO OK"

# API — alleen als container 'app' draait
curl -sf "http://localhost:8000/threat-designer/all" | head -c 200; echo

# Sentry — alleen met stack:up:full / --profile full (GET /ping → {"status":"Healthy"})
curl -sf "http://localhost:8090/ping" && echo
```

Pas URL’s aan als je app andere routes gebruikt; doel is: **HTTP 200** op health/list endpoints (behalve DynamoDB: **400 is OK**).

### 3.2a Testen zonder Sentry

**Standaard** start de stack **zonder** Sentry (lichter). Sentry is alleen de **assistent-chat** (8090); de rest van de stack hangt daar **niet** van af.

| Je wilt testen | Standaard `stack:up` (geen Sentry)? |
|----------------|-------------------------------------|
| DynamoDB + MinIO | ✅ ja |
| **app** FastAPI (8000) — threat models, locks, … | ✅ ja (als container `app` draait) |
| **threat-designer** agent (8080) — threat-model runs via `/invocations` | ✅ ja (als container `threat-designer` draait + Ollama voor echte LLM) |
| **Sentry** conversatie-UI/API | ❌ — gebruik `npm run stack:up:full` of `--profile full` |
| **pytest** (unit tests in `test/app/`) | ✅ ja — geen Docker/Sentry nodig |

Voorbeelden (containers **app** + **threat-designer** moeten draaien):

```bash
curl -sf "http://localhost:8000/health" && echo
curl -sf "http://localhost:8080/ping" && echo
curl -sf "http://localhost:8000/threat-designer/all" | head -c 300; echo
```

### 3.3 Troubleshooting: `curl` naar Sentry geeft niets / exit code 7

| Symptoom | Betekenis |
|----------|-----------|
| **Exit code 7** (`Failed to connect`) op **8090** | Je draait de **standaard** stack **zonder** profiel `full` → **geen** `sentry`-container. Gebruik `npm run stack:up:full` of `docker compose -f docker-compose.local.yml --profile full up --build`. |
| Zelfde na `stack:up:full` | Sentry crasht bij start → zie logs hieronder. |
| Geen output + `curl -sf` | `-f` faalt bij geen verbinding; je ziet weinig. |

**Check:**

```bash
docker compose -f docker-compose.local.yml --profile full ps
docker compose -f docker-compose.local.yml --profile full logs sentry --tail 80
```

Met **`full`**: `app`, `threat-designer`, `sentry` horen te draaien. Als `sentry` **Exited** is: build-fout, ontbrekende `.env.local`, of dependency — lees de logs.

### 3.4 Als Ollama niet draait

Containers die `INFERENCE_BASE_URL` naar `host.docker.internal:11434` gebruiken (**threat-designer**, **sentry**) krijgen pas echte antwoorden als **Ollama op de host** luistert. Zonder Ollama: storage/API-rooktest kan nog steeds slagen; **LLM-features falen** tot Ollama draait. *(Sentry **/ping** hoort óók zonder Ollama HTTP 200 te geven — alleen inference faalt dan.)*

---

## 4. Frontend (Vite — niet in Docker Compose)

Vanaf de **projectroot** (backend draait al op **:8000**):

```bash
npm install
npm run dev
```

Open de URL die Vite toont (meestal **http://localhost:5173**). API-base: `.env.development` → `VITE_APP_ENDPOINT=http://localhost:8000`.

### 4.1 Crash: `Cannot find module '@rollup/rollup-darwin-x64'`

**Oorzaak:** Rollup installeert een **platform-specifiek** binair pakket — op **Intel Mac** is dat `@rollup/rollup-darwin-x64`; op **Apple Silicon** `@rollup/rollup-darwin-arm64`. Soms mist `npm` die optional dependency ([npm issue](https://github.com/npm/cli/issues/4828)).

**Oplossing:**

```bash
rm -rf node_modules
rm -f package-lock.json
npm install
npm run dev
```

Blijft het fout? **Intel Mac:** `npm install @rollup/rollup-darwin-x64 --save-dev`. **Apple Silicon:** `npm install @rollup/rollup-darwin-arm64 --save-dev`, daarna `npm run dev`.

### 4.2 Browser: CORS op `/lock` terwijl de API op **:8000** draait

**Symptoom:** `blocked by CORS policy` + soms `500` op `POST …/threat-designer/…/lock`.

**Oorzaak:** Vaak **geen echte CORS-bug**, maar een **500** op de lock-route: ontbrekende env zoals `LOCKS_TABLE` / `AGENT_STATE_TABLE` in de `app`-container → crash → browser toont “geen `Access-Control-Allow-Origin`”. In `docker-compose.local.yml` staan die tabelnamen nu expliciet; **`TRUSTED_ORIGINS`** bevat `http://localhost:5173`.

**Actie:** `npm run stack:up` (of `docker compose -f docker-compose.local.yml up --build`) opnieuw. Check in DevTools **Network** de echte HTTP-status; bij 403/404/500 eerst **backend logs**: `docker compose -f docker-compose.local.yml logs app --tail 80`.

---

## 5. Auth

**Geen Cognito/JWT** in deze fork — `LOCAL_USER` / no-auth. Zie `sprints.md` en `docs/README.md` voor de beslissing: eerst lokale rooktest, **daarna** pas auth overwegen.

---

## 6. Meer lezen

- [`../docker-compose.local.yml`](../docker-compose.local.yml) — services, profielen (`full` = Sentry), env  
- [`../.env.local.example`](../.env.local.example) — template voor `.env.local`  
- [`../docs/README.md`](../docs/README.md) — documentatie-index  
- [`../docs/qa/functional-checklist.md`](../docs/qa/functional-checklist.md) — **functionele testchecklist** (browser + stack; na rooktest)  
- [`../src/projectgoal.md`](../src/projectgoal.md) — visie, Ollama/LM Studio  
- [`../sprints.md`](../sprints.md) — sprintstatus en “huidige focus”

---

*Laatste update: threat-designer-owasped — `.env.local.example`, dynamodb-init image, compose profile `full`, npm `stack:*`, CI compose*
