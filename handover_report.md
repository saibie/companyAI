# AI 계층형 조직 관리 시스템 - 기술 인수인계서

**문서 버전:** v1.0
**작성일:** 2025-12-10
**작성자:** Gemini AI Assistant

---

## 1. 프로젝트 개요 (Overview)

본 문서는 Django, Ollama, LangGraph 기반의 'AI 계층형 조직 관리 시스템'의 현재 개발 상태와 향후 계획을 기술한 인수인계서입니다.

**프로젝트 목표:** 사용자가 가상의 AI 기업 CEO가 되어, 로컬 LLM(Ollama)을 기반으로 하는 계층적 AI 에이전트 조직을 구성하고 관리하며 복잡한 업무를 자동화하는 시뮬레이션 및 자동화 플랫폼을 구축합니다.

**현재 상태:** 핵심 MVP(Minimum Viable Product) 기능 구현이 완료되었습니다. 사용자는 웹 대시보드를 통해 AI 에이전트와 작업을 생성하고, 작업 처리 과정을 모니터링하며, 결과물을 승인/반려하는 Human-in-the-Loop 프로세스를 수행할 수 있습니다. 백그라운드에서는 LangGraph로 정의된 워크플로에 따라 AI 에이전트가 작업을 자율적으로 처리합니다.

---

## 2. 프로젝트 실행 방법 (How to Run)

### 사전 요구사항
- Docker 및 Docker Compose
- `uv` (Python 패키지 관리자)
- **(Windows 사용자) Ollama 데스크톱 애플리케이션:** Windows 호스트에서 Ollama가 실행 중이어야 합니다.

### 실행 절차
1.  **Ollama 호스트 IP 설정 (WSL 사용자):**
    WSL 환경에서 Docker를 사용하는 경우, 컨테이너가 Windows 호스트의 Ollama에 접근할 수 있도록 IP 주소를 설정해야 합니다.
    -   WSL 터미널에서 다음 명령어를 실행하여 Windows 호스트 IP를 확인합니다.
        ```bash
        ip route | awk '/default/ {print $3}'
        ```
    -   프로젝트 루트의 `docker-compose.yml` 파일을 열어 `web` 서비스의 `environment` 섹션에 있는 `OLLAMA_HOST` 값을 확인된 IP 주소로 수정합니다. (예: `http://172.26.144.1:11434`)

2.  **Docker 컨테이너 실행:**
    프로젝트 루트 디렉토리에서 다음 명령어를 실행하여 Docker 컨테이너를 빌드하고 백그라운드에서 실행합니다.
    ```bash
    docker-compose up --build -d
    ```

3.  **관리자 계정 생성 (최초 실행 시):**
    웹 애플리케이션에 접근하기 전, Django 관리자 계정을 생성해야 합니다.
    ```bash
    docker exec -it ai_corp_web python manage.py createsuperuser
    ```
    -   Username, Email, Password를 순서대로 입력하여 계정을 생성합니다.

4.  **애플리케이션 접근:**
    -   **메인 대시보드:** `http://localhost:8000/corp/dashboard/`
    -   **Django 관리자 페이지:** `http://localhost:8000/admin/`

---

## 3. 기술 스택 및 주요 구성 요소 (Tech Stack & Core Components)

| Component      | Technology                  | 역할 및 설명                                                                                   |
| :------------- | :-------------------------- | :--------------------------------------------------------------------------------------------- |
| **Container**  | Docker Compose              | Django, PostgreSQL 등 서비스의 실행 환경을 오케스트레이션합니다.                             |
| **Backend**    | Django 5.x+                 | 핵심 비즈니스 로직, ORM, 템플릿 렌더링을 담당합니다.                                           |
| **Database**   | PostgreSQL 16+              | `Agent`, `Task` 등 관계형 데이터를 저장합니다.                                               |
| **Vector DB**  | pgvector                    | `AgentMemory`의 임베딩을 저장하고 유사도 검색을 수행합니다.                                    |
| **AI Engine**  | Ollama (외부 연동)          | 로컬 환경에서 LLM 추론을 수행합니다. (현재는 Windows 호스트에서 실행)                         |
| **AI Workflow**| LangGraph                   | AI 에이전트의 작업 처리 흐름을 상태 머신(State Machine) 그래프로 정의하고 실행합니다.         |
| **Frontend**   | Django Templates + HTMX     | 서버 사이드 렌더링 기반의 동적 UI/UX를 구현하여 SPA와 유사한 경험을 제공합니다.             |
| **Packages**   | uv                          | `uv.lock` 파일을 통해 Python 의존성을 관리합니다.                                              |

---

## 4. 구현된 기능 상세 (Detailed Implemented Features)

### 4.1. 인프라 및 데이터베이스
- **Docker 기반 환경:** `docker-compose.yml`을 통해 `web`(Django), `postgres`(DB), `pgadmin`(DB 관리 툴) 서비스를 한 번에 실행할 수 있습니다.
- **pgvector 통합:** `AgentMemory` 모델에 `VectorField`를 사용하며, 마이그레이션 시 `VectorExtension`이 자동으로 활성화되도록 설정되었습니다.
- **Django 모델 정의:** `corp/models.py`에 `Agent` (Self-Referencing), `Task`, `AgentMemory` 모델이 `guidelines.md`에 따라 구현되었습니다.

### 4.2. 백엔드 및 관리자 페이지
- **Django Admin:** `corp/admin.py`에 모든 핵심 모델이 등록되어 있어, 관리자 페이지에서 데이터를 쉽게 조회하고 수정할 수 있습니다.
- **Ollama 클라이언트:** `corp/ollama_client.py`에 `OllamaClient` 클래스를 구현하여 Ollama API(generate, list, pull 등)와 상호작용합니다.

### 4.3. 프론트엔드 (대시보드)
- **메인 대시보드 (`/corp/dashboard/`):**
    -   Ollama 서버 상태(Online/Offline) 및 사용 가능한 모델 목록을 표시합니다.
    -   전체 에이전트 목록과 현재 승인 대기 중인 작업 목록을 표시합니다.
- **에이전트 상세 페이지 (`/corp/agent/<id>/detail/`):**
    -   특정 에이전트의 상세 정보, 생성/할당된 작업, 저장된 메모리를 조회할 수 있습니다.
- **HTMX 기반 비동기 UI:**
    -   **에이전트/작업 생성:** 페이지 새로고침 없이 폼 제출 시 실시간으로 목록이 업데이트됩니다.
    -   **Ollama 모델 풀링:** 모델 이름을 입력하여 원격으로 모델을 다운로드하고 진행 상태를 UI에 표시합니다.
    -   **작업 승인/반려:** "Tasks Waiting Approval" 목록에서 버튼 클릭으로 작업을 즉시 승인하거나, 피드백과 함께 반려할 수 있습니다.

### 4.4. AI 워크플로 및 백그라운드 처리
- **백그라운드 워커:** `run_agents` Django 관리자 명령이 `web` 컨테이너 실행 시 백그라운드에서 자동으로 실행됩니다. 이 워커는 10초마다 `THINKING` 상태의 작업을 탐색하여 처리합니다.
- **LangGraph 기반 워크플로 (`corp/agent_workflow.py`):**
    -   **상태 정의 (`AgentState`):** 작업 설명, 피드백, 계획, 중간 결과 등을 포함하는 에이전트의 상태를 정의합니다.
    -   **다중 노드:** `generate_plan`(계획 생성), `revise_plan`(계획 수정), `use_tools`(도구 사용), `reflect_and_respond`(최종 결과 생성) 노드로 구성됩니다.
    -   **조건부 로직:**
        -   **진입점 분기:** 작업에 피드백이 있으면 `revise_plan` 노드에서, 없으면 `generate_plan` 노드에서 워크플로를 시작합니다.
        -   **반복/종료 분기:** 최종 결과물이 기준(키워드 'FINAL_RESULT' 포함 여부)에 미치지 못하면, 다시 `revise_plan`으로 돌아가 작업을 재시도합니다.
    -   **Mock Tools:** `search_web`, `execute_code`와 같은 도구가 `langchain_core.tools` 기반의 목업(mock)으로 구현되어 있어, 실제 도구로 쉽게 교체할 수 있습니다.

---

## 5. 주요 소스코드 구조 (Key Source Code Structure)

-   `docker-compose.yml`, `Dockerfile`: 프로젝트 실행 환경 구성의 핵심 파일.
-   `source/settings/__init__.py`: Django 설정 파일. `INSTALLED_APPS` 및 `MIDDLEWARE`에 `pgvector`, `django_htmx` 등이 등록됨.
-   `corp/models.py`: 데이터베이스 스키마(모델) 정의.
-   `corp/views.py`: `DashboardView`, `AgentDetailView` 등 HTTP 요청을 처리하는 핵심 로직.
-   `corp/admin.py`: Django 관리자 페이지 구성.
-   `corp/urls.py`: `corp` 앱의 URL 라우팅.
-   `corp/templates/`: UI를 구성하는 Django 템플릿 파일.
    -   `corp/dashboard.html`: 메인 대시보드 템플릿.
    -   `corp/agent_detail.html`: 에이전트 상세 페이지 템플릿.
    -   `corp/partials/`: HTMX를 통해 동적으로 교체되는 부분 템플릿 모음.
-   **`corp/agent_workflow.py`**: **AI 로직의 핵심.** LangGraph 워크플로(상태, 노드, 엣지)가 정의된 파일.
-   `corp/management/commands/run_agents.py`: 백그라운드에서 주기적으로 실행되며 LangGraph 워크플로를 트리거하는 관리 명령.

---

## 6. 향후 개발 계획 (Future Development Plan)

### 1순위: 실제 도구(Tool) 통합
-   현재 `agent_workflow.py`에 정의된 `search_web`, `execute_code`는 목업(mock) 상태입니다.
-   **수행할 작업:**
    -   `duckduckgo-search` 또는 다른 검색 라이브러리를 사용하여 `search_web` 도구를 실제 웹 검색 기능으로 교체합니다.
    -   `subprocess` 모듈 등을 사용하여 `execute_code` 도구가 안전한 환경(예: Docker 컨테이너)에서 실제 Python 코드를 실행하고 결과를 반환하도록 구현합니다.

### 2순위: 메모리(RAG) 기능 통합
-   `MemoryManager` 클래스는 구현되었지만, 현재 LangGraph 워크플로에서 사용되지 않고 있습니다.
-   **수행할 작업:**
    -   LangGraph 워크플로에 "Search Memory" 노드를 추가합니다.
    -   `generate_plan` 또는 `revise_plan` 노드 실행 전에, 현재 작업 설명과 관련된 과거의 성공/실패 사례를 `AgentMemory`에서 벡터 검색(RAG)하여 `AgentState`에 추가합니다.
    -   LLM이 계획을 생성/수정할 때 이 메모리를 참고하도록 프롬프트를 수정하여, 에이전트가 시간이 지남에 따라 학습하고 개선되도록 만듭니다.

### 3순위: UI/UX 개선
-   **에이전트 설정 UI:** 에이전트 생성/수정 시 Ollama 모델(`qwen:8b`, `llama3.1` 등), `temperature` 값 등 LLM 파라미터를 UI에서 직접 설정할 수 있도록 기능을 추가합니다.
-   **Ollama 상태 상세 표시:** 현재 Online/Offline만 표시되는 상태를 넘어, `OllamaClient`를 확장하여 현재 로드된 모델, GPU 사용량 등 상세 정보를 대시보드에 표시합니다.

### 4순위: 고급 LangGraph 패턴 적용
-   `dev_plan.md`에 명시된 "Cross-Check(상호 검증)" 개념을 구현합니다.
-   **수행할 작업:**
    -   하나의 작업 결과를 다른 역할(예: 'Critic' 역할)을 가진 에이전트에게 전달하여 검토하고 피드백을 생성하는 노드를 추가합니다.
    -   이를 통해 단일 로컬 LLM의 환각(Hallucination)이나 오류 가능성을 보완하고 결과물의 품질을 높입니다.

---

## 7. 주의사항 및 팁 (Notes & Tips)

-   **WSL IP 주소:** WSL 환경에서는 재부팅 시 호스트 IP 주소가 변경될 수 있습니다. `docker-compose up` 실행 전 `OLLAMA_HOST` 값을 주기적으로 확인해야 합니다.
-   **백그라운드 워커 로그:** `run_agents` 관리 명령의 실행 로그(LangGraph 노드 진행 상황, 오류 등)는 `docker-compose logs -f web` 명령을 통해 실시간으로 확인할 수 있습니다.
-   **CEO 에이전트:** 작업 생성 시 `creator`로 사용되는 'CEO' 에이전트는 `get_or_create`를 통해 자동으로 생성됩니다.
-   **데이터베이스 초기화:** 데이터베이스를 완전히 초기화하고 싶을 경우, `docker-compose down -v` 명령을 사용하여 Docker 볼륨까지 삭제한 후 다시 `docker-compose up`을 실행하면 됩니다.

