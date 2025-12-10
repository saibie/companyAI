# 프로젝트 기획 명세서: AI 계층형 조직 관리 시스템 (Local LLM Edition)

**문서 버전:** v0.3 (Ollama Integration)
**작성일:** 2024-XX-XX
**작성자:** CEO & AI Partner

## 1. 프로젝트 개요 (Overview)
본 프로젝트는 사용자가 가상의 AI 기업 CEO가 되어, 계층적(Hierarchical) 구조를 가진 AI Agent들을 고용, 관리하는 **조직 시뮬레이션 및 업무 자동화 플랫폼**이다.
**핵심 전략:** 고비용의 상용 API 대신 **Ollama 기반의 로컬 LLM**을 활용하며, 단일 로컬 모델의 성능 한계를 **계층적 업무 분담(Divide and Conquer)**과 **LangGraph의 정교한 오케스트레이션**으로 극복한다.

## 2. 핵심 사용자 (Target User)
* **Role:** CEO (최상위 의사결정권자)
* **Goal:** 로컬 환경(On-premise)에서 추가 비용 없이 나만의 AI 조직을 구축하여 복잡한 업무를 자동화하고자 함.

## 3. 핵심 기능 명세 (Functional Requirements)

### 3.1. 에이전트 및 조직 관리 (Organization Management)
* **CEO 권한:**
    * 직속 하위 에이전트(임원급) 생성/해고.
    * **[Update] 에이전트 생성 파라미터 (Ollama 최적화):**
        * `Name`, `Role`, `Persona`: 기존과 동일.
        * `Base Model`: **Ollama Model Tag** 지정 (예: `llama3.1:8b`, `gemma2:9b`, `mistral-nemo`, `phi3.5` 등).
        * `Temperature`: 역할에 따라 창의성 조절 (단순 작업은 0, 아이디어는 0.7).
* **Agent 권한:**
    * 하위 에이전트 생성/해고 권한.
    * **[Update] 리소스 제한 (Hardware Constraints):**
        * API 비용 제한 대신 **동시 실행 에이전트 수(Concurrency)** 제한.
        * 로컬 GPU VRAM 한계를 고려하여, 한 번에 추론(Inference) 가능한 에이전트 큐(Queue) 관리.
    * **[New] 하위 에이전트 생성 함수:** `create_sub_agent(name, role, ollama_model_name=None, context_window_size=None)` 메서드를 통해 하위 에이전트를 생성 가능. 매개변수는 `Name`, `Role`, 선택적 `Ollama Model`, `Context Window Size`로 구성.

### 3.2. 업무 보고 체계 (Hierarchical Reporting System)
* **상향식 보고 및 보정 (Bottom-up with Correction):**
    * 로컬 모델의 환각(Hallucination) 가능성을 보완하기 위해 **Cross-Check(상호 검증)** 단계를 강화.
    * **[Update] Review Step:** 하위 에이전트가 작성한 보고서는 상위 에이전트에게 가기 전, 동료 에이전트(Critic Role)가 1차 검수를 수행하도록 강제함.

### 3.3. 결재 시스템 (Approval System)
* **결재 및 Human-in-the-loop:**
    * CEO의 승인/반려/보류/위임 프로세스 유지.
    * **[Update] 로컬 모델 한계 극복:** 반려 시 CEO가 구체적인 예시(Few-shot prompting)를 피드백으로 제공하면, 해당 예시가 에이전트의 Context에 즉시 주입되도록 설계.

### 3.4. 업무 실행 및 결과 (Execution & Result)
* **Task 분해 (Decomposition):**
    * 로컬 모델은 긴 컨텍스트 처리에 약할 수 있으므로, 상위 에이전트는 Task를 **최대한 작은 단위(Atomic Task)**로 쪼개서 하위 에이전트에게 전달해야 함.
* **Agent Toolset:**
    * **Web Search:** (DuckDuckGo Search 등 무료/로컬 친화적 도구 권장).
    * **Local File System:** 로컬 PC의 특정 폴더에 접근하여 파일 읽기/쓰기.
    * **Local Code Execution:** 로컬 Python 환경에서 코드 실행.

---

## 4. 시스템 아키텍처 및 데이터 (Architecture & Data)

### 4.1. 에이전트 오케스트레이션 (LangGraph + Ollama)
* **Framework:** **LangGraph**
* **LLM Backend:** **Ollama** (via LangChain `ChatOllama`)
    * **Reasoning Strategy:** 로컬 모델의 부족한 추론 능력을 보완하기 위해 LangGraph의 Node 흐름을 더 잘게 쪼개어 단계별(Step-by-step) 사고를 강제함 (Chain of Thought).
    * **Structured Output:** JSON 출력을 잘 못하는 소형 모델을 위해 Pydantic Parser 등을 활용하여 출력 포맷을 엄격하게 제어하거나, 정규표현식(Regex)으로 후처리.

### 4.2. 메모리 및 지식 관리 (Memory & Knowledge)
* **Vector Store:** **ChromaDB** (로컬 파일 기반, 설치 용이).
* **Embedding Model:** **Ollama Embedding** (예: `mxbai-embed-large`, `nomic-embed-text`) 사용하여 임베딩 비용 또한 0으로 유지.
* **Legacy Handover:** 에이전트 해고 시 지식(Vector DB) 보존 정책 유지.

### 4.3. 데이터베이스 모델링 (Schema Draft)
* **Agents Table 추가 필드:**
    * `ollama_model_name` (varchar): `llama3.1`, `mistral` 등.
    * `context_window_size` (int): 모델별 허용 토큰 수 (로컬 모델마다 다르므로 관리 필요).
* **[Update] DB Validation:** `ollama_model_name` 필드는 생성 시 반드시 설정되어야 하며, 유효한 Ollama 모델 이름이어야 함.

---

## 5. UI/UX 요구사항 (User Interface)

* **상태 표시줄 (Status Bar):**
    * 현재 로컬 LLM 서버(Ollama)의 상태 (Online/Offline).
    * 현재 작업 대기열(Queue) 상태 (예: "Agent A 생각 중... (대기 2명)").
* **모델 선택 UI:**
    * 에이전트 생성 시, 현재 내 로컬 Ollama에 설치된 모델 리스트(`ollama list`)를 드롭다운으로 보여줌.

---

## 6. 비기능 요구사항 (Non-Functional Requirements)

* **Performance (Latency):**
    * 로컬 추론 속도는 GPU 성능에 의존하므로, 사용자에게 "생각 중"임을 보여주는 UI 인터랙션이 매우 중요함.
* **Installation:**
    * 사용자가 별도의 복잡한 서버 설정 없이 `Docker Compose` 등을 통해 한 번에 실행할 수 있어야 함.
