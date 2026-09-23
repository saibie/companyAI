---
type: architecture
title: System Overview & Architecture Topology
description: Comprehensive architecture of companyAI local hierarchical AI corporate simulation system.
updated_at: 2026-09-23
tags:
  - architecture
  - django
  - ollama
  - langgraph
  - postgresql
  - pgvector
related_files:
  - source/settings.py
  - docker-compose.yml
  - Dockerfile
  - guidelines.md
---

# 🏛️ System Overview & Architecture Topology

## 1. High-Level Summary
**companyAI** is a local-first, zero-cost AI organization simulator where a human CEO manages a hierarchical network of autonomous AI agents. The backend is powered by **Django 5.x/6.0**, orchestrating multi-agent decision loops with **LangGraph**, persisting state in **PostgreSQL 16 + pgvector**, and running local LLMs via **Ollama**.

```
                   +-----------------------+
                   |  Human CEO (Browser)  |
                   +-----------+-----------+
                               |  HTTP / HTMX
                               v
                   +-----------------------+
                   |     Django 5.x/6.0    |
                   |  (corp, account, web) |
                   +-----+-----------+-----+
                         |           |
            +------------+           +------------+
            | ORM queries                         | LangGraph invoke
            v                                     v
+-----------------------+             +-----------------------+
|  PostgreSQL 16 +      |             |    LangGraph Engine   |
|  pgvector (Agents,    |             |  (AgentNode / State)  |
|  Tasks, Memories)     |             +-----------+-----------+
+-----------------------+                         |
                                                  | Local HTTP (REST)
                                                  v
                                      +-----------------------+
                                      |     Ollama Server     |
                                      | (Llama 3, Mistral...) |
                                      +-----------------------+
```

---

## 2. Core Pillars & Constraints

| Pillar | Principle | Implementation |
| :--- | :--- | :--- |
| **Local-First** | 100% offline inference. No external paid APIs (OpenAI, Anthropic) permitted. | [OllamaClient](file:///home/saibie1677/projects/companyAI/ai_core/llm_gateway.py) interacting with local Ollama (`http://localhost:11434` or Docker host). |
| **Hierarchical** | Recursive top-down task delegation and bottom-up reporting. | [Agent](file:///home/saibie1677/projects/companyAI/corp/models.py) self-referencing tree with automatic `depth` calculation. |
| **Human-in-the-Loop** | Critical milestones, high-risk tools, and task deliverables require CEO review. | `WAIT_APPROVAL` state, [GatekeeperRequest](file:///home/saibie1677/projects/companyAI/corp/models.py), and HTMX approval actions. |
| **Unified Storage** | Relational data + Vector embeddings reside in a single Postgres container. | PostgreSQL 16 with `pgvector.django.VectorField(dimensions=768)`. |

---

## 3. Directory Layout & Module Responsibilities

- **`corp/`**: Core business domain:
  - `models.py`: Data entities ([Agent], [Task], [AgentMemory], [CorporateMemory], [Channel], [ImmutableAuditLog], [GatekeeperRequest]).
  - `services/`: Encapsulated domain logic (`agent_service.py`, `human_service.py`, `cos_service.py`, `comm_service.py`, `audit_service.py`, `safeguard_service.py`, `kms_service.py`).
  - `views.py`: Django views + HTMX partial endpoints for reactive UI.
  - `management/commands/run_agents.py`: Background worker processing tasks via LangGraph.
- **`ai_core/`**: LangGraph workflow and LLM infrastructure:
  - `workflow.py`: `StateGraph` definition, agent execution node, supervisor review node.
  - `llm_gateway.py`: `OllamaClient` abstraction with fallback handling.
  - `tools/`: Built-in tools (`math_tools.py`, `web_search.py`, `comm_tools.py`, `kms_tools.py`, `system_tools.py`, `registry.py`).
- **`account/`**: User authentication and profile management for CEO accounts.
- **`source/`**: Django project settings, root URL configuration, and WSGI/ASGI handlers.
- **`templates/` & `static/`**: Server-rendered HTML templates with HTMX attributes and CSS styling.
- **`okf/`**: Open Knowledge Format deterministic documentation bundle.
- **`graphify-out/`**: AST code knowledge graph (`graph.json`, `GRAPH_REPORT.md`, `graph.html`).
