---
type: concept
title: Multi-Company Architecture, Corporate Lore & Model Inheritance
description: 1:N user-to-company structure, company-scoped resources, AI lore generation, and hierarchical LLM resolution.
updated_at: 2026-09-23
tags:
  - company
  - multi-company
  - multi-tenant
  - lore
  - llm-model
related_files:
  - corp/models.py
  - corp/services/company_service.py
  - ai_core/workflow.py
---

# 🏢 Multi-Company Architecture, Corporate Lore & Model Inheritance

## 1. 1 User : N Companies (Multi-Tenant Architecture)
In companyAI, a single human user (CEO) can found, own, and administer multiple independent AI corporations:

```
                      [ User (Human CEO) ]
                                |
             +------------------+------------------+
             |                                     |
     [ Company A: 핀테크 AI ]             [ Company B: 우주 물류 AI ]
     (Default: llama3:8b)                (Default: gemma4:26b)
             |                                     |
     +-------+-------+                     +-------+-------+
     |               |                     |               |
 [Agent A1]     [Agent A2]             [Agent B1]     [Agent B2]
 (inherits)     (qwen2.5:7b)           (inherits)     (inherits)
```

### Resource Scoping & Partitioning
All operational and intellectual assets are strictly scoped to the active `Company`:
- **`Agent.company`**: All agents belong to a specific company. When sub-agents are created, `company` is automatically inherited down the reporting hierarchy.
- **`CorporateMemory.company`**: The corporate wiki and vector memories are partitioned per company.
- **`Channel.company` & `Announcement.company`**: Internal communication channels and executive broadcasts are company-private.
- **`Task`**: Scoped via `task.assignee.company`.

---

## 2. Company Lore & Background (AI Generated or Manual)
Each `Company` possesses a rich business identity:
- `name`: Corporation title.
- `industry`: Sector / domain focus (e.g. "양자 암호 보안", "자율 우주 화물").
- `description`: Comprehensive corporate lore, mission statement, business goals, and behavioral philosophy.

### AI Lore Generation ([company_service.py](file:///home/saibie1677/projects/companyAI/corp/services/company_service.py))
Users can provide a simple keyword or theme (e.g., "AI 헬스케어 스타트업") and invoke `generate_company_lore_with_ai()`. Local Ollama synthesizes:
1. Refined brand name
2. Precise industry categorization
3. In-depth 2-3 paragraph corporate narrative and agent behavioral tenets.

### Context Injection into Agent Reasoning
During task execution ([ai_core/workflow.py](file:///home/saibie1677/projects/companyAI/ai_core/workflow.py)), the company's background is dynamically injected into the system prompt:
```
[소속 기업 세계관 및 미션 (Corporate Background)]
- 기업명: 넥스트호라이즌 퀀텀랩
- 산업 분야: 양자 암호화 및 차세대 네트워크 보안
- 배경 및 미션: ...
(귀하는 이 기업의 핵심 미션과 비즈니스 철학에 완벽히 부합하도록 모든 업무를 기획하고 수행해야 합니다.)
```

---

## 3. Hierarchical LLM Model Resolution
The language model powering agent reasoning and manager review is resolved hierarchically:

1. **Tier 1 (Agent Override)**: `agent.ollama_model_name` (if explicitly assigned).
2. **Tier 2 (Company Default)**: `agent.company.default_llm_model` (e.g. `llama3:8b`).
3. **Tier 3 (System Global Fallback)**: `GLOBAL_MODEL_NAME` (from `LLM_MODEL` environment variable).

This allows companies to run on standard models while selectively assigning larger/specialized models to critical executive agents.
