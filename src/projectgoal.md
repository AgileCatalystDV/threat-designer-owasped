# Threat Model Local — Ruwe Spec & Implementatieplan

**Auteur**: Co-PM Intelligence  
**Datum**: 2026-03-08  
**Status**: Concept — persoonlijk gebruik + mogelijk OWASP bijdrage  
**Basis**: [awslabs/threat-designer](https://github.com/awslabs/threat-designer) (Apache 2.0)

---

## Visie

> *"Bestaande AI threat modeling tool bevrijd van cloud vendor lock-in, uitgebreid met LLM security modeling, aangeboden aan de community."*

Een volledig lokale, containerized variant van threat-designer die:
- **Geen data naar externe cloud stuurt** — architectuurdiagrammen blijven lokaal
- **Lokale LLM inference** gebruikt (Ollama + Qwen3/Llama/Mistral)
- **LLM-specifieke STRIDE templates** toevoegt (OWASP LLM Top 10)
- **Minimale AWS-dependencies** heeft — chirurgische verwijdering, niet een herschrijf

---

## Context — Waarom dit waardevol is

### Het probleem met threat-designer vandaag

Threat-designer (awslabs) is een sterke tool maar heeft een fundamenteel spanningsveld:
- Je analyseert **gevoelige architectuurdiagrammen** (trust boundaries, dataflows, systeem-topologie)
- Die data gaat naar **AWS Bedrock of OpenAI** — externe cloud
- Voor EU-organisaties, overheidsinstellingen en security-bewuste teams is dit onacceptabel

### De gap in het OWASP ecosysteem

OWASP heeft een Threat Modeling project maar geen:
- Geïntegreerde AI-tool die volledig lokaal draait
- Tool die LLM-specifieke bedreigingen modelleert (OWASP LLM Top 10)
- Docker-first, vendor-agnostic implementatie

### Licentie — volledig correct

- threat-designer: **Apache 2.0** — fork, modificeer, distribueer ✅
- Ollama: **MIT** ✅
- DynamoDB Local: **Apache 2.0** ✅
- MinIO: **AGPL-3.0** (self-hosted gebruik OK voor OWASP tool) ✅
- Qwen3 gewichten: **Qwen License** — community gebruik zonder commercieel oogmerk OK ✅

---

## Hardware Vereisten

**Referentie setup**: MacBook Pro M4 Pro/Max (2024), 48GB UMA

Apple Silicon UMA = CPU en GPU delen geheugen → uitstekende lokale inference buiten dedicated GPU-servers.

### Klein (< 8GB) — voor snelle iteraties / ontwikkeling

| Model | VRAM | Sterk in | Geschikt voor TM? |
|-------|------|----------|-------------------|
| `gemma3:4b` (QAT) | ~3GB | Redeneren, 128K context | ⚠️ Basis — eenvoudige threats |
| `phi4-mini-reasoning` | ~3GB | Multi-step logica | ⚠️ Verrassend sterk voor de grootte |
| `phi4-reasoning` (14B) | ~9GB | Complex redeneren, overtreft 70B | ✅ Goed voor STRIDE stappen |
| `deepseek-r1:8b` distill | ~5GB | Redeneren, logica | ⚠️ Zwakke safety alignment* |

### Medium (8–20GB) — balans kwaliteit/snelheid

| Model | VRAM | Sterk in | Geschikt voor TM? |
|-------|------|----------|-------------------|
| `mistral-nemo:12b` | ~8GB | Instructie volgen, veilig, EU-origine | ✅ Goed |
| `gemma3:12b` | ~8GB | Redeneren, 128K context | ✅ Goed |
| `gemma3:27b` | ~18GB | Beste Gemma kwaliteit | ✅ Sterk |
| `deepseek-r1:14b` distill | ~9GB | Sterk redeneren | ⚠️ Safety* |

### Groot (20GB+) — beste kwaliteit

| Model | VRAM | Geschikt voor TM? |
|-------|------|-------------------|
| `qwen3:32b` | ~20GB | ✅ **Aanbevolen voor productie** |
| `qwen3:30b-a3b` (MoE) | ~18GB | ✅ Sneller, vergelijkbare kwaliteit |
| `llama3.3:70b` | ~40GB | ✅ Beste open source kwaliteit |
| Mistral Large 2 | ~70GB+ | ❌ Te groot voor 48GB |

### Aanbeveling per use case

| Use case | Model |
|----------|-------|
| Snel testen / ontwikkelen | `gemma3:12b` of `phi4-reasoning` |
| Dagelijks gebruik threat modeling | `qwen3:32b` (aanbevolen) |
| Maximale kwaliteit | `llama3.3:70b` |
| EU-origine voorkeur | `mistral-nemo:12b` (Mistral, Frans) of `gemma3` (Google DeepMind) |

### ⚠️ Security noot — DeepSeek R1 distills

> *"Distilled reasoning models display poorer safety performance than safety-aligned base models. Stronger reasoning correlates with greater potential harm."*

DeepSeek-R1 distill modellen hebben **zwakkere safety alignment** dan Llama of Gemma equivalenten. Voor OWASP-bijdrage zijn `gemma3`, `phi4-reasoning` of `qwen3` veiliger te positioneren.

### Ollama pull commando's

```bash
ollama pull gemma3:12b          # goede balans, snel
ollama pull phi4-reasoning      # sterk redeneren, compact
ollama pull qwen3:32b           # productie aanbevolen
ollama pull mistral-nemo        # EU-origine, veilig
ollama pull llama3.3:70b        # maximale kwaliteit
```

### LM Studio als alternatief voor Ollama

[LM Studio](https://lmstudio.ai/) is een GUI-first alternatief dat ook een **OpenAI-compatibele lokale server** exposeert — dezelfde integratiemethode als Ollama, dus minimale code wijziging nodig.

**Voordelen t.o.v. Ollama:**
- Grafische interface voor model management (download, laden, wisselen)
- Fijnere controle over inference parameters (temperature, context length, GPU layers)
- Ingebouwde chat UI voor snel testen van modellen
- Ondersteunt GGUF modellen rechtstreeks van HuggingFace

**Nadelen t.o.v. Ollama:**
- GUI-only voor model beheer (minder scriptbaar)
- Minder geschikt voor headless/CI omgevingen
- Geen `docker pull` equivalent — modellen manueel downloaden via UI

**LM Studio lokale server starten:**

```bash
# Via UI: Developer tab → Start Server (default port 1234)
# Of via CLI (LM Studio 0.3+):
lms server start --port 1234
lms load qwen3-32b  # model naam zoals getoond in LM Studio
```

**Integratie in threat-designer-local** — identiek aan Ollama, alleen `base_url` en poort verschilt:

```python
# Ollama:
client = OpenAI(base_url="http://host.docker.internal:11434/v1", api_key="ollama")

# LM Studio:
client = OpenAI(base_url="http://host.docker.internal:1234/v1", api_key="lm-studio")
```

**Configuratie via environment variable (aanbevolen):**

```yaml
# docker-compose.local.yml
backend:
  environment:
    - INFERENCE_BASE_URL=http://host.docker.internal:1234/v1  # LM Studio
    # - INFERENCE_BASE_URL=http://host.docker.internal:11434/v1  # Ollama
    - INFERENCE_API_KEY=local
    - LOCAL_MODEL=qwen3-32b-instruct
```

**Aanbeveling:** Ollama voor headless/productie gebruik, LM Studio voor experimenten en model evaluatie. Beide werken met dezelfde backend code dankzij OpenAI-compatibele API.

---

## Architectuur — Huidig vs. Lokaal

### Huidig (AWS-native)

```
Frontend (Amplify) → Cognito (auth) → API Gateway → Lambda (Python)
                                                         ↓
                                              DynamoDB + S3 + Bedrock
```

### Target (volledig lokaal)

```
Frontend (Vite/nginx) → [geen auth / simpele JWT] → FastAPI (Python)
                                                         ↓
                                         DynamoDB Local + MinIO + Ollama
```

---

## Duale Track Aanpak

### Track 1 — Chirurgische AWS-dependency verwijdering (prioriteit)

Minimale wijzigingen, maximaal resultaat. Één service per keer vervangen.

### Track 2 — LLM Threat Modeling templates (intellectuele bijdrage)

OWASP LLM Top 10 STRIDE templates — het onderscheid t.o.v. de AWS-variant.

---

## Track 1 — Implementatieplan (chirurgische precisie)

### Fase 0 — Voorbereiding (0.5 dag)

```bash
git clone https://github.com/awslabs/threat-designer.git threat-designer-local
cd threat-designer-local
```

- Lees `backend/` structuur — identificeer alle AWS SDK calls
- Lees `src/` (frontend) — identificeer alle `@aws-amplify` imports
- Maak `docker-compose.local.yml` aan (naast bestaande infra/)
- Zet Sentry **uit** (`ENABLE_SENTRY=false`) — grootste AWS-afhankelijkheid, laatste prioriteit

### Fase 1 — Storage (0.5 dag) ✦ Laagste effort

**DynamoDB → DynamoDB Local** (drop-in compatible, zelfde SDK)

```yaml
# docker-compose.local.yml
dynamodb-local:
  image: amazon/dynamodb-local:latest
  ports: ["8001:8000"]
  command: "-jar DynamoDBLocal.jar -inMemory"
```

Wijziging backend: alleen `endpoint_url` aanpassen:
```python
# Van:
dynamodb = boto3.resource('dynamodb')
# Naar:
dynamodb = boto3.resource('dynamodb', endpoint_url='http://dynamodb-local:8001')
```

**S3 → MinIO** (S3-compatible API, zelfde boto3 calls)

```yaml
minio:
  image: minio/minio:latest
  ports: ["9000:9000", "9001:9001"]
  environment:
    MINIO_ROOT_USER: minioadmin
    MINIO_ROOT_PASSWORD: minioadmin
  command: server /data --console-address ":9001"
```

Wijziging backend: `endpoint_url` + credentials:
```python
s3 = boto3.client('s3',
    endpoint_url='http://minio:9000',
    aws_access_key_id='minioadmin',
    aws_secret_access_key='minioadmin'
)
```

### Fase 2 — Backend containeriseren (1 dag)

Lambda handlers → FastAPI endpoints. Patroon is consistent:

```python
# Lambda handler patroon:
def handler(event, context):
    body = json.loads(event['body'])
    result = process(body)
    return {'statusCode': 200, 'body': json.dumps(result)}

# FastAPI equivalent:
@app.post("/analyze")
async def analyze(request: AnalyzeRequest):
    result = process(request.dict())
    return result
```

```yaml
# docker-compose.local.yml
backend:
  build:
    context: ./backend
    dockerfile: Dockerfile.local
  ports: ["8000:8000"]
  environment:
    - DYNAMODB_ENDPOINT=http://dynamodb-local:8001
    - S3_ENDPOINT=http://minio:9000
    - OLLAMA_BASE_URL=http://host.docker.internal:11434
  depends_on:
    - dynamodb-local
    - minio
```

### Fase 3 — LLM inference via Ollama (0.5 dag)

Ollama exposeert een **OpenAI-compatibele API** — minimale code wijziging:

```python
# Van (OpenAI provider in threat-designer):
client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

# Naar (Ollama lokaal):
client = OpenAI(
    base_url="http://host.docker.internal:11434/v1",
    api_key="ollama"  # dummy, niet gebruikt
)
model = os.environ.get('LOCAL_MODEL', 'qwen3:32b')
```

> **Note**: Ollama op macOS best **buiten Docker** draaien voor Apple Metal GPU access.
> `brew install ollama && ollama serve`

### Fase 4 — Auth vereenvoudigen (1 dag)

Cognito + Amplify auth → bypassen voor localhost.

**Optie A — Geen auth (simpelste, voor persoonlijk gebruik)**:
```javascript
// src/auth/index.js — vervang Amplify auth
export const getCurrentUser = () => ({ username: 'local-user', userId: 'local' });
export const signIn = () => Promise.resolve();
export const signOut = () => Promise.resolve();
```

**Optie B — Simpele JWT** (voor multi-user/OWASP release):
- FastAPI + `python-jose` voor JWT
- Simpele login form, geen externe identity provider

### Fase 5 — Frontend containeriseren (0.5 dag)

```dockerfile
# Dockerfile.frontend
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
ENV VITE_API_URL=http://localhost:8000
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.local.conf /etc/nginx/conf.d/default.conf
```

### Fase 6 — Sentry lokaal (1-2 dagen, optioneel)

Sentry gebruikt Bedrock AgentCore Runtime — meest complexe vervanging. Aanpak:
- Vervang AgentCore door een eenvoudige agent loop in Python
- Zelfde Ollama endpoint als de hoofdapplicatie
- DynamoDB Local voor sessie-opslag

**Prioriteit: laag — begin zonder Sentry.**

---

## docker-compose.local.yml — Volledig overzicht

```yaml
version: '3.8'

services:
  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports: ["3000:80"]
    depends_on: [backend]

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.local
    ports: ["8000:8000"]
    environment:
      - DYNAMODB_ENDPOINT=http://dynamodb-local:8001
      - S3_ENDPOINT=http://minio:9000
      - S3_ACCESS_KEY=minioadmin
      - S3_SECRET_KEY=minioadmin
      - OLLAMA_BASE_URL=http://host.docker.internal:11434
      - LOCAL_MODEL=qwen3:32b
      - AUTH_MODE=local
    depends_on: [dynamodb-local, minio]

  dynamodb-local:
    image: amazon/dynamodb-local:latest
    ports: ["8001:8000"]
    command: "-jar DynamoDBLocal.jar -inMemory"

  minio:
    image: minio/minio:latest
    ports: ["9000:9000", "9001:9001"]
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    command: server /data --console-address ":9001"
    volumes: ["minio_data:/data"]

volumes:
  minio_data:

# Ollama: draai lokaal buiten Docker voor Apple Silicon GPU access
# brew install ollama && ollama serve
# ollama pull qwen3:32b
```

---

## Track 2 — LLM Threat Modeling Templates

De intellectuele bijdrage die dit onderscheidt van de AWS-fork.

### OWASP LLM Top 10 STRIDE mapping

| LLM Top 10 | STRIDE categorie | Voorbeeld bedreiging |
|------------|-----------------|---------------------|
| LLM01: Prompt Injection | Tampering | Gebruiker manipuleert model via input |
| LLM02: Insecure Output Handling | Tampering / Info Disclosure | Model output niet gesanitized → XSS |
| LLM03: Training Data Poisoning | Tampering | Gemanipuleerde trainingsdata |
| LLM04: Model Denial of Service | Denial of Service | Resource exhaustion via complexe prompts |
| LLM06: Sensitive Info Disclosure | Information Disclosure | Model lekt training data |
| LLM08: Excessive Agency | Elevation of Privilege | Model heeft te veel autonomie/permissies |
| LLM09: Overreliance | Repudiation | Geen human-in-the-loop validatie |

### Template structuur (JSON)

```json
{
  "template_id": "llm-app",
  "name": "LLM Application",
  "description": "STRIDE threats voor applicaties die LLMs gebruiken",
  "threats": [
    {
      "id": "LLM-T01",
      "category": "Tampering",
      "owasp_ref": "LLM01",
      "title": "Prompt Injection",
      "description": "Aanvaller manipuleert model gedrag via kwaadaardige input",
      "mitigations": ["Input sanitization", "Output validation", "Sandboxing"]
    }
  ]
}
```

---

## OWASP Bijdrage Pad

| Stap | Actie | Timing |
|------|-------|--------|
| **1** | Fork + lokale Docker variant werkend | Sprint 8–9 |
| **2** | LLM STRIDE templates toevoegen | Parallel |
| **3** | README + quick-start voor lokale setup | Bij werkende demo |
| **4** | OWASP Slack `#project-threat-modeling` contacteren | Na demo |
| **5** | Indienen als OWASP Lab Project | Bij volwassenheid |

**OWASP Lab Project** instap is laagdrempelig: werkende tool + documentatie. Geen formeel reviewproces.

---

## Effort Schatting

| Fase | Beschrijving | Dagen |
|------|-------------|-------|
| 0 | Voorbereiding, repo analyse | 0.5 |
| 1 | DynamoDB Local + MinIO | 0.5 |
| 2 | Backend → FastAPI containers | 1.0 |
| 3 | Ollama LLM integratie | 0.5 |
| 4 | Auth vereenvoudigen | 1.0 |
| 5 | Frontend containeriseren | 0.5 |
| **Totaal Track 1** | **Werkende lokale variant** | **4 dagen** |
| Track 2 | LLM STRIDE templates | 1–2 dagen |
| Fase 6 | Sentry lokaal (optioneel) | 1–2 dagen |

**MVP zonder Sentry: ~4 dagen** met AI-team ondersteuning.

---

## Principes

- **Chirurgische precisie** — vervang één AWS service per keer, raak de business logic niet aan
- **Ollama OpenAI-compat** — minimale code wijzigingen via drop-in API compatibiliteit
- **Sentry last** — grootste AWS-afhankelijkheid, begin zonder
- **KISS** — geen over-engineering; werkende lokale tool is het doel
- **OWASP-first** — open source, community, geen vendor lock-in

---

## Referenties

- [awslabs/threat-designer](https://github.com/awslabs/threat-designer) — bronproject (Apache 2.0)
- [OWASP Threat Modeling Project](https://owasp.org/www-project-threat-modeling/)
- [OWASP LLM Top 10](https://owasp.org/www-project-top-10-for-large-language-model-applications/)
- [Ollama OpenAI compatibility](https://ollama.com/blog/openai-compatibility)
- [amazon/dynamodb-local](https://hub.docker.com/r/amazon/dynamodb-local)
- [MinIO Docker](https://hub.docker.com/r/minio/minio)

---

## Appendix — Starter Threat Modeling Prompts (STRIDE)

Vijf prompts om lokaal te testen — kopieer, plak, verfijn. Vervang `[SYSTEEM]` door jouw architectuur beschrijving of diagram.

**Aanbevolen volgorde voor een echte TM sessie**: Prompt 2 → Prompt 1 → Prompt 4 → Prompt 3 → Prompt 5  
*(Trust boundaries eerst, dan STRIDE, dan attack trees, dan LLM-specifiek, dan quick wins)*

---

### Prompt 1 — Volledige STRIDE analyse

```
Je bent een senior security architect met expertise in threat modeling.

Analyseer het volgende systeem en genereer een volledige STRIDE threat model:

SYSTEEM:
[Plak hier je architectuurbeschrijving, diagram of component lijst]

AANNAMES:
- Dreigingsactor: [extern / insider / authenticated user / nation-state]
- Buiten scope: [bijv. fysieke beveiliging, supply chain, onderliggende cloud infra]
- Omgeving: [productie / staging / intern]

Geef voor elke STRIDE categorie:
- Spoofing: Welke identiteiten kunnen worden nagebootst?
- Tampering: Welke data of processen kunnen worden gemanipuleerd?
- Repudiation: Welke acties kunnen worden ontkend bij gebrek aan logging?
- Information Disclosure: Welke gevoelige data kan lekken?
- Denial of Service: Welke componenten zijn kwetsbaar voor uitputting?
- Elevation of Privilege: Waar kan een aanvaller meer rechten verkrijgen?

Per bedreiging: geef een korte beschrijving, aanvalsvector, en concrete mitigatie.
Gebruik een tabel per STRIDE categorie.

Geef de output ook als JSON array met velden:
id, stride_category, title, description, likelihood, impact, mitigation
```

---

### Prompt 2 — Trust Boundary analyse *(start hier)*

```
Je bent een security architect gespecialiseerd in trust boundary analyse.

Gegeven dit systeem:
[Architectuurbeschrijving]

AANNAMES:
- Dreigingsactor: [extern / insider / authenticated user]
- Buiten scope: [bijv. fysieke beveiliging]

Identificeer alle trust boundaries (punten waar data of controle van de ene
vertrouwenszone naar de andere overgaat).

Geef per trust boundary:
1. Naam en locatie
2. Welke data / commando's de grens passeren
3. Welke authenticatie en autorisatie controls aanwezig zijn
4. Welke STRIDE bedreigingen hier het meest relevant zijn
5. Aanbevolen aanvullende controls

Focus op de meest risico-volle boundaries eerst (prioriteer op impact × kans).

Geef de output ook als JSON array met velden:
id, boundary_name, data_crossing, existing_controls, stride_threats, recommended_controls
```

---

### Prompt 3 — LLM-specifieke bedreigingen (OWASP LLM Top 10)

```
Je bent een AI security specialist met kennis van de OWASP LLM Top 10.

Analyseer de volgende LLM-gebaseerde applicatie op security bedreigingen:

SYSTEEM:
[Beschrijving van de LLM applicatie: input bronnen, output kanalen,
tools/plugins, gebruikersrollen, dataopslag, gebruikte modelgewichten en herkomst]

AANNAMES:
- Dreigingsactor: [extern / insider / geautomatiseerde aanvaller]
- Buiten scope: [bijv. training pipeline, onderliggende hardware]

Geef voor elk relevant OWASP LLM Top 10 risico:
- LLM01 Prompt Injection
- LLM02 Insecure Output Handling
- LLM04 Model Denial of Service
- LLM05 Supply Chain (inclusief modelgewichten herkomst)
- LLM06 Sensitive Information Disclosure
- LLM07 Insecure Plugin Design
- LLM08 Excessive Agency
- LLM09 Overreliance

Per risico: concrete aanvalsscenario's voor DIT systeem + specifieke mitigaties.
Geef ook een prioritering (Hoog/Medium/Laag) op basis van de architectuur.

Geef de output ook als JSON array met velden:
id, owasp_ref, stride_category, title, description, likelihood, impact, mitigation
```

---

### Prompt 4 — Attack Tree voor specifieke asset

```
Je bent een penetration tester die een attack tree opstelt.

Doelwit (de asset die beschermd moet worden):
[Bijv. "de PostgreSQL database met gebruikersdata"]

Dreigingsactor: [script kiddie / insider / nation-state / geautomatiseerde scanner]

Systeem context:
[Architectuurbeschrijving]

AANNAMES:
- Aanvaller heeft: [geen toegang / read-only toegang / authenticated user rechten]
- Buiten scope: [bijv. fysieke toegang tot servers]

Stel een attack tree op:
- Root: "Aanvaller krijgt ongeautoriseerde toegang tot [ASSET]"
- Toon alle aanvalspaden (AND/OR nodes)
- Geef per blad-node: aanvalstechniek (MITRE ATT&CK referentie indien van toepassing)
- Identificeer de 3 meest waarschijnlijke paden voor de gedefinieerde dreigingsactor
- Geef voor elk pad de zwakste schakel en de meest impactvolle mitigatie

Maak de tree leesbaar als genummerde hiërarchie.

Geef de output ook als JSON met velden:
root_goal, actor, paths: [{id, steps, weakest_link, mitigation, mitre_ref}]
```

---

### Prompt 5 — Snelle risico-prioritering (voor sprint planning)

```
Je bent een pragmatische security engineer die werkt met KISS-principes.

Gegeven dit systeem in PRODUCTIE:
[Architectuurbeschrijving]

AANNAMES:
- Dreigingsactor: [extern / insider]
- Budget voor mitigatie: [klein / medium — geen grote refactors]
- Tijdshorizon: 6 maanden

Geef een geprioriteerde lijst van de TOP 5 security risico's die:
1. De hoogste kans hebben in de komende 6 maanden
2. De grootste business impact hebben bij exploitatie
3. Met relatief weinig effort gemitigeerd kunnen worden (quick wins)

Per risico:
- Omschrijving in één zin
- Kans (Hoog/Medium/Laag) + motivatie
- Impact (Hoog/Medium/Laag) + motivatie
- Geschatte effort om te mitigeren (uren)
- Concrete eerste stap die morgen gezet kan worden

Sluit af met: welke 2 acties zou je als security engineer vandaag nog doen?

Geef de output ook als JSON array met velden:
id, title, likelihood, impact, effort_hours, first_action
```

---

### Tips voor betere resultaten

- **Volgorde**: Prompt 2 → 1 → 4 → 3 → 5 voor een complete TM sessie
- **Aannames altijd invullen**: scope en dreigingsactor bepalen 80% van de outputkwaliteit
- **JSON output**: gebruik voor integratie met threat-designer of eigen tooling
- **Itereer**: gebruik Prompt 5 eerst voor quick wins als tijd beperkt is
- **Qwen3/Phi4-reasoning**: zet reasoning aan voor complexe analyses (`/think` prefix in sommige Ollama versies)
- **Temperature**: gebruik 0.3–0.5 voor consistente, reproduceerbare output; 0.7+ voor creatievere aanvalspaden
- **LLM05 Supply Chain**: vergeet modelgewichten herkomst niet — Qwen3 (Alibaba) vs. Mistral (EU) vs. Llama (Meta) heeft verschillende supply chain risico-profielen

---

*Co-PM Intelligence — Threat Model Local Spec — 2026-03-08*  
*"Bestaande tool bevrijd van vendor lock-in, aangeboden aan de community."*
