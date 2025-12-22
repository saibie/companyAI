# 🚀 Future Feature Requirements: AI Company Operation System
**Version:** 1.2 (Updated)
**Context:** Local Hierarchical AI Corp (Django + Ollama + LangGraph)

본 문서는 현재의 '지휘 통제(Command & Control)' 중심 MVP 모델을 넘어, 실제 기업처럼 유기적이고 지속 가능한 운영이 가능한 시스템으로 발전시키기 위한 필수 기능 명세입니다.

---

## 1. 지식 관리 시스템 (Knowledge Management System - KMS) ✅ [Implemented]
**목표:** 개별 에이전트의 기억(AgentMemory)에 의존하지 않고, 조직 전체의 자산이 되는 지식 저장소를 구축합니다.

### A. 사내 위키 (Company Wiki / SOP) (완료)
* **개요:** 퇴사(삭제)와 무관하게 유지되는 중앙 벡터 저장소입니다.
* **구현 내용:**
    * `CorporateMemory` 모델 신설.
    * 태스크 완료(`DONE`) 시 결과물 자동 아카이빙 및 벡터화.
    * `search_wiki` 도구를 통한 작업 착수 전 선행 지식 검색.

### B. 에러 로그 및 트러블슈팅 DB (완료)
* **개요:** 실패 사례를 공유하여 동일한 실수 반복을 방지합니다.
* **구현 내용:**
    * `TaskLog` 활용 및 반려 피드백 데이터화.

---

## 2. 수평적 커뮤니케이션 (Horizontal Communication) ✅ [Implemented]
**목표:** 수직적(상명하복) 소통 구조를 보완하여, 부서 간 협업과 전사적 정보 공유를 가능하게 합니다.

### A. 공용 워크스페이스 (Shared Workspace) (완료)
* **개요:** 서로 다른 매니저를 둔 에이전트끼리 정보를 교환할 수 있는 채널입니다.
* **구현 내용:**
    * `Channel`, `ChannelMessage` 모델 도입.
    * `post_message`, `read_channel` 도구 제공.

### B. 전사 공지 (Broadcast System) (완료)
* **개요:** CEO가 전체 에이전트에게 정책 변경이나 긴급 지시를 내립니다.
* **구현 내용:**
    * `Announcement` 모델 및 시스템 프롬프트(System Prompt) 동적 주입 로직 구현.

---

## 3. 인사 및 권한 관리 (HR & Authority Management) ✅ [Implemented]
**목표:** 무분별한 에이전트 증식을 막고, 체계적인 위임 전결 규정을 수립합니다.

### A. 계층적 고용 통제 (Hierarchical Hiring Control)
* **개요:** 조직의 깊이(Depth)와 권한을 제어합니다.
* **구현 내용:**
    * **Depth Limit:** `MAX_AGENT_DEPTH`(예: 5)를 설정하여, 그 이상 하위 조직 생성을 차단.
    * **Permission System:** `can_hire`, `can_fire` 권한 필드 도입. 상위 에이전트가 하위 에이전트 생성 시 권한 위임 여부 결정.

### B. 직권 해고 (Skip-Level Firing)
* **개요:** 상위 관리자가 직속 부하뿐만 아니라, 자신의 하위 라인(Descendant)에 속한 모든 에이전트를 해고할 수 있습니다.
* **구현 내용:**
    * `is_descendant_of` 로직을 통해 하위 조직 검증.
    * 중간 관리자 해고 시, 그 하위 조직은 해체되지 않고 해고자의 직속 상관(Grandparent)에게 자동 승계(Adoption)됨.
    * *Note: '연좌제(팀 전체 해체)' 기능은 데이터 안전 및 자산 보호를 위해 제외됨.*

### C. (보류) 정량적 성과 지표 (KPIs)
* *Note: 동일한 LLM 모델 환경에서 단순 수치 비교의 실효성 문제로 인해, 권한 관리(Authority Management) 중심으로 방향 전환됨.*

---

## 4. 운영 자동화 (Operational Automation)
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

---

## 5. 자원 및 예산 관리 (Resource & Budget Management)
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