---
type: index
title: companyAI Open Knowledge Format (OKF) Master Index
description: Entrypoint and navigation manifest for companyAI architecture, domain concepts, workflows, ADRs, and playbooks.
updated_at: 2026-09-23
tags:
  - okf
  - index
  - manifest
  - companyAI
---

# 📚 companyAI Knowledge Base (OKF Bundle)

Welcome to the **Open Knowledge Format (OKF)** bundle for **companyAI (Local Hierarchical AI Corp)**.

This knowledge repository serves as the **deterministic source of truth** for human developers and AI coding agents. Before planning or implementing any code changes, agents must consult this bundle alongside the AST-level [Graphify knowledge graph](../graphify-out/graph.json).

---

## 🏛️ Architecture & Governance
High-level system design, infrastructure topology, security boundaries, and auditing systems.

- [System Overview](./architecture/system-overview.md): Local-first AI Corp architecture, Django 5/6, Ollama, LangGraph, and PostgreSQL + pgvector.
- [Security & Governance](./architecture/security-governance.md): Immutable hash-chain audit logging (`ImmutableAuditLog`), gatekeeper sandbox (`GatekeeperRequest`), and Human-in-the-Loop CEO approval.

---

## 💡 Core Domain Concepts
Core business entities, state machines, and algorithmic patterns.

- [Multi-Company Architecture & Corporate Lore](./concepts/company-entity.md): 1:N multi-company structure, AI lore generation, resource isolation, and hierarchical LLM resolution.
- [Agent Hierarchy & Lifecycle](./concepts/agent-hierarchy.md): Self-referencing recursive tree, depth management, permissions (`can_hire`, `can_fire`), and fail-safe firing with grandparent adoption.
- [Task State Machine & Lifecycle](./concepts/task-lifecycle.md): 9-state task lifecycle (`TODO`, `THINKING`, `WAIT_APPROVAL`, `APPROVED`, etc.), delegation, and escalation.
- [LangGraph Agent Workflow](./concepts/langgraph-workflow.md): StateGraph execution nodes, LLM gateway, tool registry, and memory integration.
- [Memory & Vector Store (pgvector)](./concepts/memory-pgvector.md): `AgentMemory` vs `CorporateMemory`, `nomic-embed-text` (768d) embeddings, and cosine similarity retrieval.
- [Corporate Communication Channels](./concepts/communication-channels.md): Internal channels, agent-to-agent messaging, and broadcast announcements.

---

## ⚖️ Architecture Decision Records (ADRs)
Immutable architectural choices, context, rationale, and consequences.

- [ADR 0001: Local-First Inference with Ollama](./decisions/0001-local-first-ollama.md): Strict zero-cost, privacy-first local LLM execution.
- [ADR 0002: Django Templates + HTMX over Heavy SPA](./decisions/0002-htmx-reactive-ui.md): Lightweight reactive UI without Node/React build pipeline.
- [ADR 0003: Multi-Company Tenant Model & AI Lore Injection](./decisions/0003-multi-company-tenant-model.md): Multi-company architecture, lore generation, and model inheritance.

---

## 🛠️ How-To Guides & Playbooks
Operational runbooks for developing, running, and maintaining the system.

- [Development & Execution Runbook](./howtos/development-workflow.md): Docker orchestration, migrations, background workers (`run_agents`), and CEO admin setup.
- [Knowledge & AST Graph Sync Playbook](./howtos/knowledge-workflow.md): Running `graphify`, querying AST relationships, and maintaining the OKF bundle.
