---
name: graphify-okf
description: Workflows for querying the Graphify AST knowledge graph and validating or navigating the Open Knowledge Format (OKF) bundle in companyAI.
---

# Graphify & OKF Skill

This skill guides you through querying codebase relationships via **Graphify** and accessing domain architecture and business rules via the **Open Knowledge Format (OKF)** bundle.

---

## 1. Querying the Graphify AST Knowledge Graph

Use the `graphify` CLI to investigate code structures before editing:

### Querying Nodes & Symbols
```bash
# Query a symbol, model, or view:
graphify query "Agent"
graphify query "Task"
graphify query "create_agent_workflow"
graphify query "GatekeeperRequest"
```
The query outputs the matched AST nodes, their community clusters, file locations, and inbound/outbound edges.

### Finding Shortest Path Between Components
```bash
# How does DashboardView talk to OllamaClient?
graphify path "DashboardView" "OllamaClient"

# How does Task trigger ImmutableAuditLog?
graphify path "Task" "ImmutableAuditLog"
```

### Explaining a Concept
```bash
graphify explain "workflow"
```

---

## 2. Navigating the OKF Bundle

The project's architectural concepts, domain models, and decision records reside in `okf/`:

1. **Master Catalog**: `okf/index.md`
2. **Architecture**:
   - `okf/architecture/system-overview.md`
   - `okf/architecture/security-governance.md`
3. **Concepts**:
   - `okf/concepts/agent-hierarchy.md`
   - `okf/concepts/task-lifecycle.md`
   - `okf/concepts/langgraph-workflow.md`
   - `okf/concepts/memory-pgvector.md`
   - `okf/concepts/communication-channels.md`
4. **Decisions**:
   - `okf/decisions/0001-local-first-ollama.md`
   - `okf/decisions/0002-htmx-reactive-ui.md`
5. **How-Tos**:
   - `okf/howtos/development-workflow.md`
   - `okf/howtos/knowledge-workflow.md`

---

## 3. Synchronizing After Code Changes

When you complete a set of modifications:
```bash
./scripts/update_knowledge.sh
```
This script re-extracts AST nodes, updates `graphify-out/graph.json` and `graphify-out/GRAPH_REPORT.md`, and confirms OKF bundle integrity.
