# Contributing to LLMOps Gateway

Thanks for your interest in contributing!

## Local Setup

```bash
git clone https://github.com/vikramanand05/llmops-gateway.git
cd llmops-gateway
cp .env.example .env
docker compose -f infra/docker-compose.yml up --build