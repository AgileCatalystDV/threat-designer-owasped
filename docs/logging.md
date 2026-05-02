# Logging — lezen en niveaus

Applicatiecode gebruikt de Python **`logging`**-module (`logger.info`, `logger.error`, `LOG.exception`, enz.) in plaats van `print()`, zodat uitvoer te filteren en te aggregeren is (Docker, CI, log-aggregators).

## Niveaus (kort)

| Niveau | Wanneer |
|--------|---------|
| **DEBUG** | Details voor troubleshooting (o.a. ruwe LLM-responses als `LOG_LEVEL=DEBUG`). |
| **INFO** | Normale lifecycle (requests, state-updates, init-stappen). |
| **WARNING** | Afwijkend maar niet fataal. |
| **ERROR** | Fouten; vaak met `exc_info=True` voor stack traces. |

## Omgevingsvariabelen

| Variabele | Dienst | Effect |
|-----------|--------|--------|
| **`LOG_LEVEL`** | **threat-designer** (LangGraph agent) | Standaard `INFO`. Zet op `DEBUG` voor uitgebreide agent/LLM-logs (zie `backend/threat_designer/monitoring.py`). |
| (standaard) | **FastAPI `app`** | Gebruikt `logging` via module-loggers; configureer via uvicorn of container logging. |

## Logs bekijken (Docker Compose)

Vanuit de projectroot, met [`docker-compose.local.yml`](../docker-compose.local.yml):

```bash
# Alle services (follow)
docker compose -f docker-compose.local.yml logs -f

# Eén service
docker compose -f docker-compose.local.yml logs -f app
docker compose -f docker-compose.local.yml logs -f threat-designer

# Met Sentry-profiel
docker compose -f docker-compose.local.yml --profile full logs -f sentry

# Laatste N regels
docker compose -f docker-compose.local.yml logs app --tail 100
```

Zelfde flow via npm (zie [`package.json`](../package.json)): `npm run stack:up` — logs verschijnen in het terminalvenster waar `compose up` draait, of gebruik `docker compose … logs` hierboven.

## Init-script (`scripts/init_dynamo.py`)

Draait vaak als one-shot container. Output gaat naar stdout via `logging` met een eenvoudig format (`[init_dynamo] …`). Bekijk met:

```bash
docker compose -f docker-compose.local.yml logs dynamodb-init
```

(Service heet `dynamodb-init` in [`docker-compose.local.yml`](../docker-compose.local.yml); check met `docker compose -f docker-compose.local.yml ps`.)

## MCP-server

De MCP-server (`mcp-server/`) logt met `logging.getLogger(__name__)`. Afhankelijk van hoe je de server start (stdio vs. file), verschijnen berichten op stderr of in de IDE MCP-console.

## Tip

Zoek in logs op `ERROR`, `Exception`, of een `job_id` om een run te volgen. Voor de threat-designer agent: bij problemen eerst **`LOG_LEVEL=DEBUG`** op de **threat-designer**-service zetten en container opnieuw starten.
