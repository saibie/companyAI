---
type: concept
title: LangGraph Workflow & Agent Execution Engine
description: StateGraph orchestration, agent thinking nodes, supervisor reviews, and Ollama client integration.
updated_at: 2026-09-23
tags:
  - langgraph
  - ai_core
  - workflow
  - ollama
  - statemachine
related_files:
  - ai_core/workflow.py
  - ai_core/llm_gateway.py
  - ai_core/tools/registry.py
  - corp/management/commands/run_agents.py
---

# ⚙️ LangGraph Workflow & Agent Execution Engine

## 1. Overview
The execution brain of companyAI resides in [ai_core/workflow.py](file:///home/saibie1677/projects/companyAI/ai_core/workflow.py). Rather than single-shot prompt calls, agents operate inside a structured **LangGraph StateGraph** loop that coordinates memory recall, reasoning, tool execution, and managerial supervision.

---

## 2. State Definitions

### `AgentState`
Typed dictionary passing execution state between graph nodes:
- `task_id`: UUID string of the active `Task`.
- `agent_id`: UUID string of the executing `Agent`.
- `task_title` & `task_description`: The problem statement.
- `memories`: Relevant observations and SOPs retrieved from `AgentMemory` / `CorporateMemory`.
- `feedback`: Past rejection remarks from the CEO or manager.
- `current_step`: Iteration index within the graph.
- `messages`: Chronological list of LangChain messages (`HumanMessage`, `AIMessage`, `ToolMessage`).
- `draft_result`: The proposed output ready for review.

---

## 3. Workflow Graph Topology

```
                  [ START ]
                      |
                      v
             [ recall_memory_node ]
                      |
                      v
             [ agent_think_node ] <--------+
                   /      \                |
     (needs tools)/        \(draft ready)  |
                 v          v              |
         [ tool_node ]  [ review_node ] ---+ (if rejected)
                 |          |
                 +----------+ (if approved)
                            v
                         [ END ]
```

1. **`recall_memory_node`**:
   - Queries `AgentMemory` and `CorporateMemory` using `MemoryManager` with `nomic-embed-text` cosine similarity.
   - Injects historical lessons, mistakes to avoid, and domain guidelines into state.
2. **`agent_think_node`**:
   - Constructs the system prompt incorporating role, hierarchy depth, memories, and feedback.
   - Calls [OllamaClient](file:///home/saibie1677/projects/companyAI/ai_core/llm_gateway.py) with tool bindings.
3. **`tool_node`**:
   - Executes registered tools ([ai_core/tools/registry.py](file:///home/saibie1677/projects/companyAI/ai_core/tools/registry.py)) authorized in `agent.allowed_tools`.
4. **`review_node`**:
   - Simulates managerial oversight if manager is an AI agent, or marks the task as `WAIT_APPROVAL` if manager is the CEO.

---

## 4. Background Execution Worker
The background orchestrator is invoked via:
```bash
python manage.py run_agents
```
- Implemented in [corp/management/commands/run_agents.py](file:///home/saibie1677/projects/companyAI/corp/management/commands/run_agents.py).
- Continuously polls for tasks in `TODO` or `THINKING` state.
- Instantiates the agent's workflow, runs the graph, updates task state, and logs execution to `TaskLog` and `ImmutableAuditLog`.
