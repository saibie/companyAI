---
type: howto
title: Knowledge & AST Graph Sync Playbook
description: Standard operating procedure for querying Graphify, navigating OKF, and synchronizing artifacts upon code changes.
updated_at: 2026-09-23
tags:
  - howto
  - graphify
  - okf
  - sync
  - norms
---

# 🛠️ Knowledge & AST Graph Sync Playbook

## 1. The Pre-Modification Workflow (수정 전 절차)
Before writing or modifying any source code in companyAI:

### Step 1: Check OKF (도메인 & 아키텍처 의도 확인)
1. Open [okf/index.md](../index.md) to locate the relevant functional domain.
2. Read the corresponding concept, architecture, or ADR documents.
3. Validate that your planned changes do not violate core constraints (e.g., Local-First Ollama, fail-safe firing, or gatekeeper approval).

### Step 2: Check Graphify (AST 의존성 및 호출 흐름 확인)
Query the AST knowledge graph to understand impact and relationships:
```bash
# Query nodes connected to a model or function:
graphify query "Agent"
graphify query "Task"
graphify query "workflow"

# Find relationships between two entities:
graphify path "create_agent_workflow" "OllamaClient"

# Inspect architectural overview:
cat graphify-out/GRAPH_REPORT.md
```

---

## 2. The Post-Modification Workflow (수정 후 절차)
After modifying or adding files:

### Step 1: Update OKF Documentation
- If models or schemas changed, update `okf/concepts/` or `okf/architecture/`.
- If new architectural directions were decided, add an ADR under `okf/decisions/`.
- If new endpoints or runbooks were created, update `okf/howtos/`.

### Step 2: Re-synchronize Graphify Graph
Run the automated update script to refresh AST nodes and clusters:
```bash
./scripts/update_knowledge.sh
```
Or directly via the CLI:
```bash
graphify extract . --code-only
graphify cluster-only .
```
This updates `graphify-out/graph.json`, `graphify-out/GRAPH_REPORT.md`, and `graphify-out/graph.html`.
