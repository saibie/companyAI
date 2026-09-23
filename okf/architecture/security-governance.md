---
type: architecture
title: Security, Governance & Human-in-the-Loop Safeguards
description: Cryptographic audit trails, risk sandboxing, and CEO approval mechanisms.
updated_at: 2026-09-23
tags:
  - security
  - governance
  - audit
  - gatekeeper
  - human-in-the-loop
related_files:
  - corp/models.py
  - corp/services/audit_service.py
  - corp/services/safeguard_service.py
---

# 🛡️ Security, Governance & Human-in-the-Loop Safeguards

## 1. Immutable Audit Logging (`ImmutableAuditLog`)

To prevent tampering with AI actions, all LLM interactions and agent decisions are logged into a **cryptographic hash chain** in PostgreSQL:

- **Entity**: [ImmutableAuditLog](file:///home/saibie1677/projects/companyAI/corp/models.py#L220)
- **Attributes**:
  - `prompt_digest`: Hash/snippet of input prompt.
  - `response_digest`: Hash/snippet of generated completion.
  - `token_count`: Estimated or reported tokens used.
  - `risk_score`: Heuristic score evaluating prompt danger.
  - `is_flagged` & `flag_reason`: Flagged if prompt violates corporate policies or safety heuristics.
  - `previous_hash`: SHA-256 hash of the immediate predecessor record (default `"GENESIS"`).
  - `current_hash`: SHA-256(`previous_hash` + `prompt_digest` + `response_digest` + `created_at`).

> [!IMPORTANT]
> The audit log is append-only. Modifying or deleting any historical log record breaks the SHA-256 chain integrity, which can be verified at any time via [audit_service.py](file:///home/saibie1677/projects/companyAI/corp/services/audit_service.py).

---

## 2. Gatekeeper Sandbox (`GatekeeperRequest`)

Certain actions performed by autonomous agents carry high financial, systemic, or reputational risks. When an agent attempts such an action, execution is intercepted and frozen into a **Gatekeeper Request**:

- **Entity**: [GatekeeperRequest](file:///home/saibie1677/projects/companyAI/corp/models.py#L239)
- **High-Risk Action Types**:
  1. `FINANCIAL`: Budget allocations, fund transfers, contract commitments.
  2. `DEPLOYMENT`: Code deployments, production server restarts.
  3. `HIERARCHY_CHANGE`: Hiring, firing, or manager reassignments.
  4. `HIGH_RISK_TOOL`: Calling sensitive system tools or destructive scripts.
- **Workflow**:
  1. Agent requests high-risk tool via [system_tools.py](file:///home/saibie1677/projects/companyAI/ai_core/tools/system_tools.py).
  2. [safeguard_service.py](file:///home/saibie1677/projects/companyAI/corp/services/safeguard_service.py) intercepts and creates a `GatekeeperRequest` with `status='PENDING'`.
  3. Task transitions to `WAIT_APPROVAL` or pauses.
  4. The CEO approves or rejects the request from the Dashboard UI.
  5. Upon approval, the payload executes; upon rejection, the agent receives a feedback rejection notice.

---

## 3. Human-in-the-Loop (CEO) Protocol

The human user sits at the apex of the hierarchy as the **CEO**:
- Any agent directly reporting to the CEO (`manager=None`) submits final deliverables directly to the CEO Dashboard inbox.
- CEO can:
  - **Approve**: Task status transitions to `APPROVED` -> `DONE`.
  - **Reject**: CEO enters rejection feedback -> Task status resets to `TODO` -> Agent re-thinks with feedback.
  - **Escalate / Reassign**: Send task to Chief of Staff (CoS) or reassign to another agent.
