# Graph Report - companyAI  (2026-09-23)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 381 nodes · 723 edges · 31 communities (12 shown, 19 thin omitted)
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 95 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `b66761ca`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- corp/views.py
- run_agents.py
- corp/models.py
- workflow.py
- account/views.py
- Agent
- OllamaClient
- django_db
- corp/admin.py
- AgentDetailView
- EconomicPlatformTests
- account/apps.py
- manage.py
- update_knowledge.sh
- tool
- HttpRequest
- company
- User

## God Nodes (most connected - your core abstractions)
1. `Task` - 35 edges
2. `Agent` - 29 edges
3. `OllamaClient` - 21 edges
4. `Company` - 13 edges
5. `GatekeeperRequest` - 11 edges
6. `get_active_company()` - 11 edges
7. `EconomicPlatformTests` - 9 edges
8. `CorporateMemory` - 9 edges
9. `Channel` - 9 edges
10. `DashboardView` - 9 edges

## Surprising Connections (you probably didn't know these)
- `request_tool_access()` --uses--> `Agent`  [INFERRED]
  ai_core/tools/system_tools.py → corp/models.py
- `DashboardView` --uses--> `OllamaClient`  [INFERRED]
  corp/views.py → ai_core/llm_gateway.py
- `htmx_ollama_pull()` --uses--> `OllamaClient`  [INFERRED]
  corp/views.py → ai_core/llm_gateway.py
- `request_tool_access()` --uses--> `Task`  [INFERRED]
  ai_core/tools/system_tools.py → corp/models.py
- `Command` --uses--> `AgentState`  [INFERRED]
  corp/management/commands/run_agents.py → ai_core/workflow.py

## Import Cycles
- None detected.

## Communities (31 total, 19 thin omitted)

### Community 0 - "corp/views.py"
Cohesion: 0.07
Nodes (62): tool, Request access to a tool. If the tool exists but is locked, it asks for a…, request_tool_access(), Company, Task, TaskLog, TaskStatus, create_company() (+54 more)

### Community 1 - "run_agents.py"
Cohesion: 0.06
Nodes (46): ask_manager_tool(), post_to_channel_tool(), tool, Read recent messages from a shared communication channel. Args: channel_name:…, Ask your manager (human) a question when instructions are ambiguous. Your…, Reply to a subordinate's question. This will send your answer to the…, Post a message to a shared communication channel. Useful for sharing findings…, read_channel_tool() (+38 more)

### Community 2 - "corp/models.py"
Cohesion: 0.06
Nodes (36): bs4, collections, ActionType, GatekeeperRequest, ImmutableAuditLog, 변경 불가능한 해시 체인 감사 로그 (Immutable Audit Log), 보안 게이트키핑 샌드박스 승인 요청 (Security Gatekeeping Sandbox), RequestStatus (+28 more)

### Community 3 - "workflow.py"
Cohesion: 0.08
Nodes (29): get_authorized_tools(), 에이전트의 권한 목록(문자열 리스트)을 받아 실제 도구 객체 리스트를 반환합니다., AgentNodes, AgentState, create_review_workflow(), manager_review_node(), 매니저가 부하직원의 결재안을 검토하는 노드, ReviewState (+21 more)

### Community 4 - "account/views.py"
Cohesion: 0.08
Nodes (20): EmailOrUsernameModelBackend, 아이디(username) 또는 이메일(email) 모두 입력하여 로그인 가능하도록 지원, Meta, UserForm, HttpRequest, 회원가입 페이지. GET 요청시 회원가입 Form 페이지 렌더. POST 요청시 회원가입 절차 진행. Args: request…, signup(), django (+12 more)

### Community 5 - "Agent"
Cohesion: 0.10
Nodes (12): MemoryManager, Agent, AgentMemory, MemoryType, [Fail-safe Firing Logic] 에이전트 삭제 시 하위 에이전트를 조부모(Grandparent)에게 자동 승계합니다., create_sub_agent(), Creates a new subordinate agent with permission checks. Args: manager_name:…, dispatch_ceo_directive() (+4 more)

### Community 6 - "OllamaClient"
Cohesion: 0.13
Nodes (11): OllamaClient, A client for interacting with the Ollama API., CorporateMemory, get_available_ollama_models(), 로컬 Ollama 인스턴스에 설치된 모델 태그 목록을 조회합니다. Ollama 서버가 비활성화되어 있거나 오류 발생 시 기본 추천 모델 목록을…, add_knowledge(), get_embedding(), Ollama를 통해 텍스트를 벡터로 변환합니다. 모델이 없으면 자동으로 Pull을 시도합니다. (+3 more)

### Community 7 - "django_db"
Cohesion: 0.12
Nodes (12): Migration, Migration, Migration, Migration, Migration, Migration, django_conf, django_db (+4 more)

### Community 8 - "corp/admin.py"
Cohesion: 0.16
Nodes (14): AgentAdmin, AgentMemoryAdmin, AnnouncementAdmin, ChannelAdmin, ChannelMessageAdmin, CompanyAdmin, CorporateMemoryAdmin, TaskAdmin (+6 more)

### Community 9 - "AgentDetailView"
Cohesion: 0.16
Nodes (11): AgentDetailView, CompanyManageView, DashboardView, MonitorView, 에이전트 상세 조회 (GET Only + Fire Action via standard POST if needed), 모니터링 화면 조회 (GET Only), WikiDetailView, WikiListView (+3 more)

### Community 11 - "account/apps.py"
Cohesion: 0.29
Nodes (5): AccountConfig, AppConfig, CorpConfig, AppConfig, django_apps

### Community 12 - "manage.py"
Cohesion: 0.40
Nodes (4): main(), Django's command-line utility for administrative tasks., Run administrative tasks., sys

## Knowledge Gaps
- **14 isolated node(s):** `TaskStatus`, `ActionType`, `RequestStatus`, `Meta`, `MemoryType` (+9 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 176 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **19 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Task` connect `corp/views.py` to `run_agents.py`, `corp/models.py`, `workflow.py`, `Agent`, `OllamaClient`, `corp/admin.py`, `AgentDetailView`?**
  _High betweenness centrality (0.112) - this node is a cross-community bridge._
- **Why does `Agent` connect `Agent` to `corp/views.py`, `run_agents.py`, `corp/models.py`, `corp/admin.py`, `AgentDetailView`?**
  _High betweenness centrality (0.108) - this node is a cross-community bridge._
- **Why does `OllamaClient` connect `OllamaClient` to `corp/views.py`, `run_agents.py`, `corp/models.py`, `AgentDetailView`?**
  _High betweenness centrality (0.065) - this node is a cross-community bridge._
- **Are the 24 inferred relationships involving `Task` (e.g. with `request_tool_access()` and `Command`) actually correct?**
  _`Task` has 24 INFERRED edges - model-reasoned connections that need verification._
- **Are the 13 inferred relationships involving `Agent` (e.g. with `request_tool_access()` and `MemoryManager`) actually correct?**
  _`Agent` has 13 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `OllamaClient` (e.g. with `fetch_web_content_tool()` and `DashboardView`) actually correct?**
  _`OllamaClient` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `TaskStatus`, `ActionType`, `RequestStatus` to the rest of the system?**
  _14 weakly-connected nodes found - possible documentation gaps or missing edges._