---
type: howto
title: Development & Execution Runbook
description: Operational steps to spin up Docker containers, run database migrations, create superusers, and launch background agents.
updated_at: 2026-09-23
tags:
  - howto
  - runbook
  - docker
  - migrations
  - background-worker
---

# 🛠️ Development & Execution Runbook

## 1. Prerequisites
- Docker & Docker Compose installed.
- Local **Ollama** running on the host system with required models pulled:
  ```bash
  ollama pull llama3:8b
  ollama pull nomic-embed-text
  ```

---

## 2. Docker Setup
Build and launch the web and database containers:
```bash
docker-compose up --build -d
```

Check running container logs:
```bash
docker-compose logs -f web
```

---

## 3. Database Migrations & Admin Account
Apply Django migrations (ensuring pgvector extension is enabled):
```bash
docker exec -it ai_corp_web python manage.py migrate
```

Create the initial Human CEO account:
```bash
docker exec -it ai_corp_web python manage.py createsuperuser
```

Access points:
- **CEO Dashboard**: `http://localhost:8000/corp/dashboard/`
- **Django Admin**: `http://localhost:8000/admin/`

---

## 4. Running the Agent Execution Worker
In a dedicated terminal or background service, start the task execution loop:
```bash
# Inside docker:
docker exec -it ai_corp_web python manage.py run_agents

# Or locally within uv environment:
uv run python manage.py run_agents
```
This loop continuously picks up tasks in `TODO` / `THINKING` status, executes LangGraph nodes, updates state, and logs audit events.
