---
type: decision
title: "ADR 0001: Local-First Inference via Ollama"
description: Architectural decision mandating offline local LLM execution and strictly forbidding paid external APIs.
updated_at: 2026-09-23
status: accepted
tags:
  - adr
  - ollama
  - local-first
  - constraints
---

# ⚖️ ADR 0001: Local-First Inference via Ollama

## Context
Autonomous hierarchical multi-agent systems generate high volumes of LLM tokens (continuous reasoning loops, memory recall, supervisor reviews, and tool calls). Using commercial cloud APIs (OpenAI, Anthropic) introduces significant financial cost, vendor lock-in, rate limiting, and data privacy concerns.

## Decision
All model inference within companyAI **must run locally** using **Ollama**.
- **No external paid APIs**: Direct calls to OpenAI, Anthropic, or proprietary cloud endpoints are strictly prohibited.
- **Client implementation**: [OllamaClient](file:///home/saibie1677/projects/companyAI/ai_core/llm_gateway.py) wraps local Ollama REST endpoints (`/api/generate`, `/api/chat`, `/api/embeddings`).
- **Compatibility**: If LangChain abstractions require an OpenAI-compatible client, it must target the local Ollama compatibility port (`http://localhost:11434/v1`).

## Consequences
- **Positive**: Zero API usage costs, unlimited development iterations, 100% data privacy, predictable latency under local hardware.
- **Negative**: Limited by local GPU/CPU compute capability and smaller model parameters (7B–14B models vs frontier 100B+ models).
