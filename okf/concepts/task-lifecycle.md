---
type: concept
title: Task State Machine & Lifecycle
description: Task status enum transitions, delegation, approval workflows, and feedback loops.
updated_at: 2026-09-23
tags:
  - task
  - state-machine
  - lifecycle
  - workflow
related_files:
  - corp/models.py
  - corp/services/task_service.py
  - ai_core/workflow.py
---

# 📋 Task State Machine & Lifecycle

## 1. Task Status Enum Definition
Tasks in companyAI ([Task](file:///home/saibie1677/projects/companyAI/corp/models.py#L104)) transition through a deterministic finite state machine defined by `TaskStatus`:

```
                 [ TODO ]
                    |
                    v
             [ THINKING ] <------------------------+
              /    |     \                         |
             /     |      \                        |
            v      |       v                       |
   [ WAIT_SUBTASK ]|   [ WAIT_ANSWER ]             | Re-think
                   v                               | with feedback
           [ WAIT_APPROVAL ] ----------------------+
             /           \
            v             v
       [ APPROVED ]   [ REJECTED ]
            |
            v
        [ DONE ]
```

| Status | Code Value | Meaning & Behavior |
| :--- | :--- | :--- |
| **TODO** | `TODO` | Newly created or reset task awaiting agent assignment and processing. |
| **THINKING** | `THINKING` | Active execution state. LangGraph agent loop runs inference, planning, or tool calls. |
| **WAIT_SUBTASK** | `WAIT_SUBTASK` | Parent task decomposes into child tasks (`parent_task=self`) and waits for completion. |
| **WAIT_APPROVAL** | `WAIT_APPROVAL` | Agent produced a final draft/result and submitted it to its manager or CEO for review. |
| **WAIT_ANSWER** | `WAIT_ANSWER` | Agent paused while awaiting clarification from a manager or colleague. |
| **APPROVED** | `APPROVED` | Manager or CEO accepted the deliverable. Ready for archival or finalization. |
| **DONE** | `DONE` | Deliverable completed, corporate memories committed, and task closed. |
| **REJECTED** | `REJECTED` | Reviewer rejected the result with constructive feedback. Reset to `TODO` for retry. |
| **ESCALATED** | `ESCALATED` | Deadlocked or blocked task escalated to the Chief of Staff (CoS) for triage. |

---

## 2. Parent-Child Task Decomposition
- When a task requires multiple sub-deliverables, the `assignee` agent can create sub-tasks with `parent_task=self`.
- The parent task transitions into `WAIT_SUBTASK`.
- Once all sub-tasks reach `DONE`, the parent task awakens back into `THINKING` to synthesize the overall final report.

---

## 3. Review & Feedback Loop
- **Deliverable Submission**: Agent writes output into `Task.result` and switches status to `WAIT_APPROVAL`.
- **Reviewer Action**:
  - If manager is an Agent, LangGraph `supervisor_review_node` evaluates the output against task criteria.
  - If manager is Human (or direct CEO task), it appears in the CEO's **Task Inbox** (`DashboardView`).
- **Rejection**: Reviewer sets `Task.feedback = "<Reason>"`. `Task.attempt_count` increments, and status resets so the agent can improve its output based on feedback.
