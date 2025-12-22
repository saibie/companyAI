# 🚀 Future Feature Requirements: AI Company Operation System
**Version:** 1.0 (Draft)
**Context:** Local Hierarchical AI Corp (Django + Ollama + LangGraph)

본 문서는 현재의 '지휘 통제(Command & Control)' 중심 MVP 모델을 넘어, 실제 기업처럼 유기적이고 지속 가능한 운영이 가능한 시스템으로 발전시키기 위한 필수 기능 명세입니다.
즉, 추후 개발해야할 내용을 정리한 것입니다.

---

## 1. 자원 및 예산 관리 (Resource & Budget Management)
**목표:** 무한정 리소스를 사용하는 에이전트에게 물리적/논리적 제약을 부여하여 현실적인 운영 환경을 조성합니다.

### A. 토큰 및 비용 예산 (Token Budgeting)
* **개요:** 로컬 LLM이라도 전력과 시간은 비용입니다. 부서(Manager Line)별 또는 에이전트별 토큰 사용량을 제한합니다.
* **구현 상세:**
    * `Agent` 모델에 `max_daily_tokens` 필드 추가.
    * `Task` 수행 시 소모된 토큰(Ollama API 응답 메타데이터 활용)을 카운팅.
    * 예산 초과 시 에이전트 상태를 `FROZEN`으로 변경하거나 CEO 승인 요청.

### B. 시간 제한 및 타임아웃 (Time Constraints)
* **개요:** 에이전트가 무한 루프(Thinking Loop)에 빠지는 것을 방지합니다.
* **구현 상세:**
    * `Task` 모델에 `deadline` (DateTime) 필드 추가.
    * LangGraph 워크플로 내 `step_timeout` 설정.
    * 마감 기한 임박 시, 현재까지의 내용을 바탕으로 강제 `Draft` 제출 로직 구현.

---

## 2. 수평적 커뮤니케이션 (Horizontal Communication)
**목표:** 수직적(상명하복) 소통 구조를 보완하여, 부서 간 협업과 전사적 정보 공유를 가능하게 합니다.

### A. 공용 워크스페이스 (Shared Workspace)
* **개요:** 서로 다른 매니저를 둔 에이전트끼리 정보를 교환할 수 있는 채널입니다.
* **구현 상세:**
    * `Channel` 모델 생성 (예: `#dev-team`, `#general`).
    * LangGraph 도구로 `post_message(channel, content)`, `read_channel(channel)` 추가.
    * 협업이 필요한 태스크(예: 개발팀이 기획팀의 문서를 봐야 할 때) 발생 시 활용.

### B. 전사 공지 (Broadcast System)
* **개요:** CEO가 전체 에이전트에게 정책 변경이나 긴급 지시를 내립니다.
* **구현 상세:**
    * CEO 전용 도구 `broadcast_announcement(message)`.
    * 모든 활성 에이전트의 `Context` 또는 `System Prompt`에 해당 공지사항이 일시적으로 주입됨(Injected).

---

## 3. 지식 관리 시스템 (Knowledge Management System - KMS)
**목표:** 개별 에이전트의 기억(AgentMemory)에 의존하지 않고, 조직 전체의 자산이 되는 지식 저장소를 구축합니다.

### A. 사내 위키 (Company Wiki / SOP)
* **개요:** 퇴사(삭제)와 무관하게 유지되는 중앙 벡터 저장소입니다.
* **구현 상세:**
    * `CorporateMemory` 모델 신설 (pgvector 활용, `AgentMemory`와 분리).
    * 성공한 프로젝트(`DONE` 태스크)의 결과물은 자동으로 요약되어 위키에 등재.
    * 작업 착수 전 위키 검색(`search_wiki`)을 의무화하여 시행착오 감소.

### B. 에러 로그 및 트러블슈팅 DB
* **개요:** 실패 사례를 공유하여 동일한 실수 반복을 방지합니다.
* **구현 상세:**
    * `REJECTED`된 태스크의 피드백과 원인을 별도 벡터 인덱싱.
    * 유사 태스크 발생 시 "과거에 이런 이유로 반려된 적이 있음"을 경고(Pre-warning).

---

## 4. 인사 및 성과 평가 (HR & Performance)
**목표:** 단순한 승인/반려를 넘어, 데이터를 기반으로 조직을 최적화합니다.

### A. 정량적 성과 지표 (KPIs)
* **개요:** 에이전트의 능력을 수치화합니다.
* **평가 항목:**
    * `Task Success Rate`: (승인된 태스크 / 전체 할당 태스크)
    * `Turnaround Time`: 태스크 할당부터 완료까지 걸린 시간.
    * `Feedback Loop Count`: 승인까지 몇 번의 반려(수정)가 있었는가.

### B. 승진 및 자동 해고 (Leveling & Auto-fire)
* **개요:** 성과에 따른 동적 조직 개편입니다.
* **구현 상세:**
    * KPI 우수 에이전트: `Level` 상승 (더 복잡한 모델 사용 권한 또는 하위 에이전트 고용 권한 부여).
    * 저성과 에이전트(KPI 하위 10% 지속): 경고 후 자동 해고(`fire_sub_agent`) 및 대체 인력 충원 프로세스 가동.

---

## 5. 운영 자동화 (Operational Automation)
**목표:** CEO가 개입하지 않아도 돌아가는 루틴 업무를 만듭니다.

### A. 정기 업무 스케줄링 (Cron Jobs)
* **개요:** 사람의 발의 없이 특정 시간에 자동으로 생성되는 태스크입니다.
* **구현 상세:**
    * Django 커스텀 커맨드 또는 Celery/Beat 활용.
    * 예시:
        * 매일 오전 9시: "최신 AI 뉴스 스크랩 및 요약 보고" 태스크 자동 생성 -> 리서치 팀 할당.
        * 매주 금요일: "주간 업무 성과 리포트" 생성 -> 각 팀장 할당.

### B. 사후 회고 (Post-Mortem) 프로세스
* **개요:** 프로젝트 종료 후 AI가 스스로 회고를 진행합니다.
* **구현 상세:**
    * 대형 태스크 완료 시, `Reviewer` 에이전트가 투입되어 과정의 적절성을 평가.
    * "다음에는 A 도구 대신 B 도구를 쓰는 게 좋았겠다"는 식의 교훈(Lesson Learned)을 KMS에 저장.