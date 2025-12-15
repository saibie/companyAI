# 🏢 로컬 계층형 AI 기업 (Local Hierarchical AI Corp)

> **로컬 우선, 비용 0원 AI 조직 시뮬레이터**
> **Ollama**, **Django**, **LangGraph**를 사용하여 로컬 환경에서 계층형 AI 에이전트 팀을 구축하고 관리하세요.

## 📖 개요 (Overview)

**Local Hierarchical AI Corp**는 사용자가 인간 CEO가 되어 재귀적인 구조를 가진 AI 에이전트들을 관리하는 시뮬레이션 플랫폼입니다. 평면적인(Flat) 멀티 에이전트 시스템과 달리, 이 프로젝트는 **지휘 통제(Command & Control)** 계층 구조를 강조합니다:

* **CEO (사용자):** 고차원적인 목표를 정의하고 결과를 승인/반려합니다.
* **관리자 (Managers):** 업무를 분해하고 하위 직원에게 위임합니다.
* **직원 (Subordinates):** 원자 단위의 작업(검색, 코딩, 계획)을 수행하거나 이슈를 보고합니다.

모든 AI 추론은 **Ollama**를 통해 로컬에서 수행되므로, 데이터 프라이버시가 보장되며 API 비용이 전혀 들지 않습니다.

---

## ✨ 핵심 기능 (Key Features)

### 🧠 지능형 에이전트 워크플로
* **계층적 로직:** 에이전트는 자신의 하위 직원을 고용(`create_sub_agent`), 해고(`fire_sub_agent`)하거나 업무를 위임(`assign_task`)할 수 있습니다.
* **네이티브 도구 호출 (Native Tool Calling):** 불안정한 정규표현식 파싱 대신, **LangGraph**와 Ollama의 Tool Calling API(MCP 스타일 스크립트)를 사용하여 정확도를 높였습니다.
* **재귀적 위임:** 업무는 위에서 아래로 분해되고, 결과는 아래에서 위로 보고됩니다.

### 🛠️ 기술 스택 및 아키텍처
* **백엔드:** Django 6.0 (알파 기능 시뮬레이션), Python 3.12.
* **AI 엔진:** **Ollama** (Llama 3.1, Mistral, Qwen 등).
* **오케스트레이션:** **LangGraph** (상태 기반 멀티 턴 에이전트 루프).
* **데이터베이스:** PostgreSQL 16 + **pgvector** (벡터 메모리 및 RAG).
* **프론트엔드:** Django Templates + **HTMX** (React/Vue 없는 동적 SPA 경험).
* **인프라:** Docker Compose (올인원 설치).

### 👁️ 휴먼 인 더 루프 (Human-in-the-Loop) 대시보드
* **재귀적 조직도:** 회사 전체의 계층 구조(CEO -> 관리자 -> 직원)를 트리 형태로 한눈에 시각화합니다.
* **업무 승인 시스템:** 에이전트의 산출물을 검토합니다. 승인하여 완료하거나, 피드백과 함께 반려하여 수정을 지시할 수 있습니다.
* **실시간 모니터링:** 백그라운드 워커를 통해 에이전트가 "생각"하고 도구를 사용하는 과정을 실시간으로 관찰할 수 있습니다.

---

## 🚀 시작하기 (Getting Started)

### 사전 요구사항
1.  **Docker & Docker Compose** 설치.
2.  **Ollama** 설치 및 호스트 머신(또는 접근 가능한 네트워크)에서 실행 중일 것.
3.  (선택 사항) 로컬 패키지 관리를 위한 `uv`.

### 설치 방법

1.  **저장소 클론:**
    ```bash
    git clone [https://github.com/your-username/local-ai-corp.git](https://github.com/your-username/local-ai-corp.git)
    cd local-ai-corp
    ```

2.  **환경 설정:**
    * `docker-compose.yml` 파일을 엽니다.
    * `OLLAMA_HOST`를 현재 머신의 IP 주소로 설정합니다 (예: `http://host.docker.internal:11434` 또는 실제 LAN IP).
    * *주의: Docker 내부에서 `localhost`는 컨테이너 자신을 의미하므로 호스트 머신을 가리키지 않습니다.*

3.  **Docker 실행:**
    ```bash
    docker-compose up --build -d
    ```

4.  **관리자 계정 생성:**
    ```bash
    docker exec -it ai_corp_web python manage.py createsuperuser
    ```

5.  **대시보드 접속:**
    * 브라우저에서 이동: `http://localhost:8000/`

---

## 🕹️ 사용 가이드

### 1. 첫 번째 매니저 고용
* 대시보드에서 **Create New Agent** 섹션으로 이동합니다.
* 이름(예: "Alice"), 역할(예: "CTO")을 입력하고 Manager는 "No Manager" (CEO 직속)로 둡니다.
* **Create Agent** 버튼을 클릭합니다.

### 2. 업무 할당
* **Create New Task** 섹션으로 이동합니다.
* 방금 만든 "Alice"를 담당자(Assignee)로 선택합니다.
* 제목: "시장 조사", 설명: "최신 에이전틱 AI 트렌드를 조사하고 계획안을 작성해."
* **Create Task** 버튼을 클릭합니다.

### 3. 마법 관전하기
* 백그라운드 워커(`run_agents`)가 작업을 가져갑니다.
* 에이전트는 다음을 수행합니다:
    * **계획:** `create_plan` 도구로 단계별 계획 수립.
    * **검색:** `search_web` 도구 사용.
    * **위임:** 업무가 너무 크면 "Researcher" 하위 에이전트를 고용하고 업무를 쪼개서 위임합니다!
* 대시보드를 새로고침하면 에이전트 트리가 동적으로 성장하는 것을 볼 수 있습니다.

### 4. 승인 또는 반려
* 작업이 완료되면 **Tasks Waiting Approval** 목록에 나타납니다.
* **Result(결과)**를 검토합니다.
    * ✅ **Approve:** 작업이 완료(DONE) 처리됩니다.
    * ❌ **Reject:** 피드백을 입력하여 반려합니다. 에이전트는 피드백을 반영하여 계획을 수정하고 다시 작업합니다.

---

## 📂 프로젝트 구조

```text
.
├── corp/
│   ├── agent_workflow.py    # 핵심 LangGraph 로직 및 Native Tool 정의
│   ├── models.py            # Agent, Task, AgentMemory (pgvector) 모델
│   ├── views.py             # 대시보드 및 HTMX 뷰
│   ├── management/
│   │   └── commands/
│   │       └── run_agents.py # AI 처리를 위한 백그라운드 워커
│   └── templates/           # UI 템플릿 (재귀적 에이전트 트리 포함)
├── docker-compose.yml       # 서비스 오케스트레이션
├── requirements.txt         # Python 의존성
└── README.md                # 본 파일
```

---

## 🛡️ 라이선스

이 프로젝트는 오픈 소스이며 MIT 라이선스 하에 배포됩니다.