---
type: decision
title: "ADR 0003: Multi-Company Architecture, Corporate Lore Injection & Hierarchical LLM Selection"
description: Architectural decision transitioning from 1:1 User-Company to 1:N Multi-Company with AI lore synthesis and model inheritance.
updated_at: 2026-09-23
status: accepted
tags:
  - adr
  - multi-company
  - lore
  - model-selection
---

# ⚖️ ADR 0003: Multi-Company Architecture, Corporate Lore Injection & Hierarchical LLM Selection

## Context
Originally, companyAI assumed a 1:1 relationship where each Django `User` operated exactly one corporate workspace. However, users frequently need to experiment with multiple business concepts (e.g., a cybersecurity firm vs. a game studio), each requiring distinct organizational lore, separate agent hierarchies, and different default LLM models based on task complexity.

## Decision
1. **1:N Multi-Company Hierarchy**:
   - Introduce `Company` as the primary grouping entity owned by `User`.
   - Agents, Corporate Memories, Channels, and Announcements belong directly to a `Company`.
   - The UI provides an active company session switcher in the top navigation bar.
2. **AI-Powered Corporate Lore Generation**:
   - Provide a feature where CEO enters minimal keywords, and Ollama generates comprehensive corporate lore, mission, and industry framing.
   - Inject corporate lore directly into `AgentNodes.agent_reasoning` prompts to align agent behaviors with company philosophy.
3. **Hierarchical Model Inheritance**:
   - Companies specify `default_llm_model` populated dynamically from local Ollama tags (`/api/tags`).
   - Individual agents can inherit the company default or override it with a specialized model.

## Consequences
- **Positive**: Complete domain isolation between different AI ventures, realistic multi-organization management for CEOs, customizable corporate culture and reasoning contexts, and granular hardware/model resource allocation.
- **Negative**: Requires session-based active company tracking and careful filtering in queries.
