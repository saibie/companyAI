---
type: concept
title: Agent Hierarchy, Depth & Fail-Safe Firing
description: Recursive organizational tree, depth calculation, authority delegation, and grandparent inheritance logic.
updated_at: 2026-09-23
tags:
  - agent
  - hierarchy
  - tree
  - models
related_files:
  - corp/models.py
  - corp/services/agent_service.py
  - corp/services/human_service.py
---

# 👥 Agent Hierarchy, Depth & Fail-Safe Firing

## 1. Recursive Tree Structure
The [Agent](file:///home/saibie1677/projects/companyAI/corp/models.py#L8) model implements a self-referencing hierarchy:

- `manager`: ForeignKey to `'self'`, nullable.
  - If `manager is None`: Direct report to the Human CEO.
  - If `manager is not None`: Subordinate to another agent.
- `owner`: ForeignKey to `django.contrib.auth.models.User` (the CEO). All subordinates recursively inherit the creator's `owner`.
- `depth`: Integer automatically calculated in `save()`:
  - Root agents (`manager is None`) have `depth = 0`.
  - Subordinates have `depth = manager.depth + 1`.

```
           [ Human CEO ] (User)
                 |
          +------+------+
          |             |
     [ CTO (d=0) ]  [ CFO (d=0) ]
          |
    [ Dev Lead (d=1) ]
          |
    [ Junior Dev (d=2) ]
```

---

## 2. Authority & Permissions
- `can_hire` (bool): Whether this agent can spawn subordinate agents via `create_sub_agent()`.
- `can_fire` (bool): Whether this agent can terminate subordinate agents.
- `allowed_tools` (JSON list): List of tool keys this agent is authorized to invoke (e.g., `["calculator", "web_search", "kms_search"]`).
- `config` (JSON dict): Per-agent runtime settings (temperature, system prompt overrides).
- `ollama_model_name`: Local LLM model tag to use for this agent (e.g., `llama3:8b`, `mistral:7b`).

---

## 3. Fail-Safe Firing & Orphan Protection
When an agent with subordinates is deleted, an organization must not leave orphaned sub-agents adrift. In `Agent.delete()`:

1. **Grandparent Adoption**:
   - Subordinates (`self.subordinates.all()`) have their `manager` automatically reassigned to `self.manager` (the grandparent or `None` for CEO).
2. **Notification Task Generation**:
   - For every reassigned subordinate, an urgent reorganization notification task is created:
     ```python
     Task.objects.create(
         creator=grandparent or None,
         assignee=sub,
         title="[긴급] 조직 개편에 따른 업무 보고",
         description="직속 상사 '...'가 해고/삭제되었습니다. 현재 귀하는 '...' 직속으로 변경되었습니다...",
         status=Task.TaskStatus.THINKING
     )
     ```
3. **Ancestor Cycle Prevention**:
   - `is_descendant_of(potential_ancestor)` checks the ancestor chain to ensure circular reporting relationships are never created.
