# LLMOps Gateway

LLMOps Gateway is a recruiter-friendly AI gateway and LLMOps platform inspired by Portkey and Langfuse. It demonstrates a production-style FastAPI service, model routing, API-key management, usage and cost tracking, prompt versioning, Redis rate limiting, PostgreSQL persistence, React dashboards, monitoring, Docker, Kubernetes, CI/CD, and AWS-ready deployment patterns.

The project runs without paid LLM provider keys because the default provider is a realistic mock client. You can later add OpenAI, Anthropic, Gemini, or Ollama credentials through environment variables.

## Architecture

```mermaid
flowchart LR
    Client["Client / SDK"] --> Gateway["FastAPI Gateway"]
    Dashboard["React Dashboard"] --> AdminAPI["Admin APIs"]
    Gateway --> Auth["API Key Middleware"]
    Auth --> RateLimit["Redis Rate Limiter"]
    RateLimit --> Router["Model Router"]
    Router --> OpenAI["OpenAI-Compatible"]
    Router --> Gemini["Gemini-Compatible"]
    Router --> Claude["Claude-Compatible"]
    Router --> Ollama["Local Llama / Ollama"]
    Gateway --> Postgres["PostgreSQL Usage, Keys, Prompts"]
    Gateway --> Prometheus["/metrics Prometheus"]
    Prometheus --> Grafana["Grafana Dashboard"]
```

## Features

- OpenAI-style endpoint: `POST /v1/chat/completions`
- API-key creation, hashing, validation, disabling, and usage attribution
- Model routing by priority, cost, latency, provider, model, and fallback chain
- Fallback chain example: `gpt-4o-mini -> gemini-1.5-flash -> claude-3-haiku -> llama3-local`
- Request usage logs with tokens, latency, provider, model, status, fallback, and cost
- Prompt version CRUD with template variable rendering
- Redis-backed requests-per-minute and tokens-per-day rate limits
- Sensitive prompt and response payloads excluded by default
- Prometheus metrics at `/metrics`
- Grafana dashboard provisioning
- React dashboard for overview, keys, usage logs, cost analytics, prompts, and provider health
- Docker Compose stack with backend, frontend, PostgreSQL, Redis, Prometheus, and Grafana
- Kubernetes manifests for deployments, services, ConfigMap, Secret, Ingress, PostgreSQL, Redis, and HPA
- GitHub Actions workflow for tests, linting, Docker builds, Compose tests, and an AWS EKS deployment placeholder

## Quick Start

```bash
cd llmops-gateway
cp .env.example .env
docker compose -f infra/docker-compose.yml up --build
```

Services:

- Backend: `http://localhost:8000`
- Dashboard: `http://localhost:5173`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000` with `admin` / `admin`

The backend seeds a demo API key on first startup and prints it to the backend logs. For a controlled key, use the admin API:

```bash
curl -X POST http://localhost:8000/api/admin/api-keys \
  -H "X-Admin-Token: change-me-admin-token" \
  -H "Content-Type: application/json" \
  -d '{"name":"demo-user","rpm_limit":60,"tpd_limit":10000}'
```

## Chat API Example

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer llmops_your_key_here" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "route_strategy": "priority",
    "messages": [
      {"role": "user", "content": "Summarize why LLM gateways matter."}
    ]
  }'
```

Prompt version reference:

```json
{
  "model": "gpt-4o-mini",
  "prompt": {
    "prompt_id": "support-assistant",
    "version": "v1",
    "variables": {
      "company": "Acme AI"
    }
  },
  "messages": [
    {
      "role": "user",
      "content": "How do I rotate an API key?"
    }
  ]
}
```

## Backend Development

```bash
cd llmops-gateway/backend
python -m venv .venv
. .venv/Scripts/activate
pip install -r requirements.txt
pytest
uvicorn app.main:app --reload
```

Local defaults use SQLite and in-memory rate limiting. Compose uses PostgreSQL and Redis.

## Frontend Development

```bash
cd llmops-gateway/frontend
npm install
npm run dev
```

Set `VITE_API_BASE_URL=http://localhost:8000` when running the dashboard separately.

## Configuration

Important environment variables:

- `DATABASE_URL`: PostgreSQL or SQLite SQLAlchemy URL
- `REDIS_URL`: Redis URL for rate limiting
- `RATE_LIMIT_BACKEND`: `redis` or `memory`
- `ADMIN_TOKEN`: token required for `/api/admin/*`
- `DEFAULT_PROVIDER`: `mock`, `openai`, `anthropic`, `gemini`, or `ollama`
- `STORE_PROMPTS_DEFAULT`: stores prompt and response payloads only when enabled
- `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`: provider credentials
- `OLLAMA_BASE_URL`: local Ollama endpoint

## Kubernetes

```bash
kubectl apply -f infra/k8s/namespace.yaml
kubectl apply -f infra/k8s/
```

For real production use, replace the placeholder image names in `infra/k8s/backend.yaml` and `infra/k8s/frontend.yaml`, move secrets into your cloud secret manager, and use managed PostgreSQL and Redis instead of the included in-cluster examples.

## AWS Deployment Guide

1. Build backend and frontend images in CI.
2. Push images to Amazon ECR.
3. Create an EKS cluster with managed node groups or Fargate profiles.
4. Use Amazon RDS PostgreSQL for `DATABASE_URL`.
5. Use Amazon ElastiCache Redis for `REDIS_URL`.
6. Install the AWS Load Balancer Controller for the ALB Ingress.
7. Store API keys, provider credentials, and admin token in AWS Secrets Manager.
8. Ship logs and container metrics to CloudWatch.
9. Apply Kubernetes manifests with environment-specific image tags and secret references.
10. Attach HPA to CPU metrics and add custom Prometheus metrics later for cost-aware autoscaling.

## Testing

The test suite covers:

- API-key hashing and extraction
- Model routing and fallback behavior
- Cost calculation
- Rate limiting
- Prompt version rendering

```bash
cd llmops-gateway/backend
pytest
```

## Dashboard Screenshots

Place screenshots in `docs/screenshots/` after launching the Compose stack:

- `overview.png`
- `api-keys.png`
- `usage-logs.png`
- `cost-analytics.png`
- `prompt-versions.png`
- `provider-health.png`

## Resume Bullets

- Built an AI gateway with FastAPI supporting OpenAI-style chat completions, API-key auth, provider routing, fallback logic, and standardized responses.
- Implemented LLMOps telemetry with PostgreSQL usage logs, cost estimation, prompt versioning, Redis rate limits, Prometheus metrics, and Grafana dashboards.
- Shipped a full-stack dashboard in React with Docker Compose, Kubernetes manifests, CI/CD, and AWS EKS/RDS/ElastiCache deployment guidance.

## Project Structure

```text
llmops-gateway/
  backend/
    app/
      api/
      core/
      db/
      middleware/
      models/
      routers/
      schemas/
      services/
    tests/
    Dockerfile
    requirements.txt
  frontend/
    src/
    Dockerfile
    package.json
  infra/
    docker-compose.yml
    grafana/
    k8s/
    prometheus/
  .github/workflows/ci.yml
  .env.example
  README.md
```


## Roadmap

- [ ] Add real Anthropic provider client
- [ ] Add real Gemini provider client
- [ ] Add Ollama/local model integration
- [ ] Add Alembic database migrations
- [ ] Add SDK examples for Python and JavaScript
- [ ] Add frontend authentication
- [ ] Add provider retry policies
- [ ] Add distributed request tracing
- [ ] Add CSV export for usage logs
- [ ] Add Helm chart for Kubernetes deployment
- [ ] Add Terraform AWS deployment