# Graph Report - companyAI  (2026-09-23)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 338 nodes · 638 edges · 27 communities (12 shown, 15 thin omitted)
- Extraction: 86% EXTRACTED · 14% INFERRED · 0% AMBIGUOUS · INFERRED: 89 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `a2e7b937`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- run_agents.py
- Task
- Agent
- cos_service.py
- account/views.py
- workflow.py
- OllamaClient
- corp/tests.py
- AgentDetailView
- create_sub_agent_tool
- 0002_initial.py
- account/apps.py
- update_knowledge.sh
- company

## God Nodes (most connected - your core abstractions)
1. `Task` - 37 edges
2. `Agent` - 31 edges
3. `OllamaClient` - 19 edges
4. `GatekeeperRequest` - 12 edges
5. `CorporateMemory` - 9 edges
6. `ImmutableAuditLog` - 9 edges
7. `EconomicPlatformTests` - 9 edges
8. `AgentDetailView` - 9 edges
9. `DashboardView` - 9 edges
10. `TaskLog` - 8 edges

## Surprising Connections (you probably didn't know these)
- `request_tool_access()` --uses--> `Task`  [INFERRED]
  ai_core/tools/system_tools.py → corp/models.py
- `request_tool_access()` --uses--> `Agent`  [INFERRED]
  ai_core/tools/system_tools.py → corp/models.py
- `DashboardView` --uses--> `OllamaClient`  [INFERRED]
  corp/views.py → ai_core/llm_gateway.py
- `htmx_ollama_pull()` --uses--> `OllamaClient`  [INFERRED]
  corp/views.py → ai_core/llm_gateway.py
- `Command` --uses--> `AgentState`  [INFERRED]
  corp/management/commands/run_agents.py → ai_core/workflow.py

## Import Cycles
- None detected.

## Communities (27 total, 15 thin omitted)

### Community 0 - "run_agents.py"
Cohesion: 0.08
Nodes (41): ask_manager_tool(), post_to_channel_tool(), tool, Read recent messages from a shared communication channel. Args: channel_name:…, Ask your manager (human) a question when instructions are ambiguous. Your…, Reply to a subordinate's question. This will send your answer to the…, Post a message to a shared communication channel. Useful for sharing findings…, read_channel_tool() (+33 more)

### Community 1 - "Task"
Cohesion: 0.09
Nodes (46): Task, TaskLog, TaskStatus, dispatch_ceo_directive(), CEO의 자연어 전략 지시를 수석 보좌관(CoS)이 부서별 최상위 에이전트 업무로 분할 배치, approve_task(), create_task(), fire_agent() (+38 more)

### Community 2 - "Agent"
Cohesion: 0.08
Nodes (24): AgentAdmin, AgentMemoryAdmin, AnnouncementAdmin, ChannelAdmin, ChannelMessageAdmin, CorporateMemoryAdmin, TaskAdmin, TaskLogAdmin (+16 more)

### Community 3 - "cos_service.py"
Cohesion: 0.07
Nodes (26): collections, ActionType, GatekeeperRequest, 보안 게이트키핑 샌드박스 승인 요청 (Security Gatekeeping Sandbox), RequestStatus, generate_executive_briefing(), get_economic_simulation_metrics(), Cognitive Shield: 수석 보좌관(Chief of Staff) AI가 전사 현황을 압축하여 제공하는 총괄 브리핑 (+18 more)

### Community 4 - "account/views.py"
Cohesion: 0.08
Nodes (20): EmailOrUsernameModelBackend, 아이디(username) 또는 이메일(email) 모두 입력하여 로그인 가능하도록 지원, Meta, UserForm, HttpRequest, 회원가입 페이지. GET 요청시 회원가입 Form 페이지 렌더. POST 요청시 회원가입 절차 진행. Args: request…, signup(), django (+12 more)

### Community 5 - "workflow.py"
Cohesion: 0.11
Nodes (20): tool, Request access to a tool. If the tool exists but is locked, it asks for a…, request_tool_access(), AgentNodes, AgentState, create_review_workflow(), manager_review_node(), 매니저가 부하직원의 결재안을 검토하는 노드 (+12 more)

### Community 6 - "OllamaClient"
Cohesion: 0.15
Nodes (9): OllamaClient, A client for interacting with the Ollama API., CorporateMemory, add_knowledge(), get_embedding(), Ollama를 통해 텍스트를 벡터로 변환합니다. 모델이 없으면 자동으로 Pull을 시도합니다., 질문과 유사한 위키 문서를 검색합니다., search_wiki() (+1 more)

### Community 7 - "corp/tests.py"
Cohesion: 0.13
Nodes (9): ImmutableAuditLog, 변경 불가능한 해시 체인 감사 로그 (Immutable Audit Log), audit_agent_action(), compute_hash(), 에이전트의 프롬프트와 생성 응답을 무결성 감사 로그에 기록합니다., EconomicPlatformTests, django_test, hashlib (+1 more)

### Community 8 - "AgentDetailView"
Cohesion: 0.17
Nodes (10): AgentDetailView, DashboardView, MonitorView, HttpRequest, 모니터링 화면 조회 (GET Only), 에이전트 상세 조회 (GET Only + Fire Action via standard POST if needed), WikiDetailView, WikiListView (+2 more)

### Community 9 - "create_sub_agent_tool"
Cohesion: 0.13
Nodes (15): assign_task_tool(), create_sub_agent_tool(), fire_sub_agent_tool(), tool, Creates a new subordinate agent (Hiring). Args: manager_name: Your name. name:…, Fires a subordinate agent. You can fire your direct reports OR any agent below…, Assigns a task to a subordinate., assign_task() (+7 more)

### Community 10 - "0002_initial.py"
Cohesion: 0.16
Nodes (9): Migration, Migration, Migration, Migration, django_conf, django_db, django_db_models_deletion, pgvector_django_vector (+1 more)

### Community 11 - "account/apps.py"
Cohesion: 0.29
Nodes (5): AccountConfig, AppConfig, CorpConfig, AppConfig, django_apps

## Knowledge Gaps
- **11 isolated node(s):** `TaskStatus`, `Migration`, `Migration`, `Migration`, `Migration` (+6 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 156 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **15 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Task` connect `Task` to `run_agents.py`, `Agent`, `cos_service.py`, `workflow.py`, `OllamaClient`, `corp/tests.py`, `AgentDetailView`?**
  _High betweenness centrality (0.148) - this node is a cross-community bridge._
- **Why does `Agent` connect `Agent` to `run_agents.py`, `Task`, `cos_service.py`, `workflow.py`, `corp/tests.py`, `AgentDetailView`, `create_sub_agent_tool`?**
  _High betweenness centrality (0.140) - this node is a cross-community bridge._
- **Why does `OllamaClient` connect `OllamaClient` to `run_agents.py`, `Task`, `cos_service.py`, `AgentDetailView`?**
  _High betweenness centrality (0.064) - this node is a cross-community bridge._
- **Are the 25 inferred relationships involving `Task` (e.g. with `request_tool_access()` and `Command`) actually correct?**
  _`Task` has 25 INFERRED edges - model-reasoned connections that need verification._
- **Are the 14 inferred relationships involving `Agent` (e.g. with `request_tool_access()` and `MemoryManager`) actually correct?**
  _`Agent` has 14 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `OllamaClient` (e.g. with `fetch_web_content_tool()` and `DashboardView`) actually correct?**
  _`OllamaClient` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `GatekeeperRequest` (e.g. with `generate_executive_briefing()` and `get_economic_simulation_metrics()`) actually correct?**
  _`GatekeeperRequest` has 4 INFERRED edges - model-reasoned connections that need verification._