# 🤖 AGENTS.MD: companyAI Agent Development Charter & Norms

본 프로젝트(**companyAI - Local Hierarchical AI Corp**)에서 작업하는 모든 AI 에이전트 및 개발자는 아래의 **필수 개발 규범(Development Norms)**을 반드시 준수해야 합니다.

---

## 🛑 [규범 1] Pre-Flight Protocol (코드 수정 전 필수 절차)

코드를 작성하거나 수정하기 전, 에이전트는 반드시 다음 두 단계를 **순서대로** 수행해야 합니다.

### 1단계: OKF (Open Knowledge Format) 확인 (도메인 & 아키텍처 정렬)
- **엔트리포인트**: [okf/index.md](file:///home/saibie1677/projects/companyAI/okf/index.md)
- 수정하려는 영역과 관련된 도메인 문서, 아키텍처 제약사항, ADR(결정 기록)을 먼저 읽습니다.
  - 시스템 설계/제약: [okf/architecture/system-overview.md](file:///home/saibie1677/projects/companyAI/okf/architecture/system-overview.md)
  - 감사/보안 게이트키핑: [okf/architecture/security-governance.md](file:///home/saibie1677/projects/companyAI/okf/architecture/security-governance.md)
  - 에이전트 계층/상속: [okf/concepts/agent-hierarchy.md](file:///home/saibie1677/projects/companyAI/okf/concepts/agent-hierarchy.md)
  - 태스크 상태 머신: [okf/concepts/task-lifecycle.md](file:///home/saibie1677/projects/companyAI/okf/concepts/task-lifecycle.md)
  - LangGraph 워크플로: [okf/concepts/langgraph-workflow.md](file:///home/saibie1677/projects/companyAI/okf/concepts/langgraph-workflow.md)
  - pgvector 메모리: [okf/concepts/memory-pgvector.md](file:///home/saibie1677/projects/companyAI/okf/concepts/memory-pgvector.md)

### 2단계: Graphify 확인 (AST 종속성 및 파급 효과 분석)
- **아티팩트**: `graphify-out/graph.json`, `graphify-out/GRAPH_REPORT.md`
- 수정하려는 클래스/함수/모듈의 호출 관계와 종속성을 CLI로 조회합니다:
  ```bash
  graphify query "<수정_대상_심볼_또는_모듈>"
  # 예: graphify query "Agent"
  # 예: graphify query "create_agent_workflow"
  ```
- 두 컴포넌트 간 호출 경로 확인:
  ```bash
  graphify path "<NodeA>" "<NodeB>"
  ```
- 전체적인 의존 관계 및 God Node 파악을 위해 필요시 [graphify-out/GRAPH_REPORT.md](file:///home/saibie1677/projects/companyAI/graphify-out/GRAPH_REPORT.md)를 참조합니다.

---

## ⚙️ [규범 2] In-Flight Implementation Guidelines (구현 중 규범)

1. **Local-First 원칙 준수 (ADR 0001)**:
   - 외부 유료 API(OpenAI, Anthropic 등)를 직접 호출하는 코드는 일체 작성하지 않습니다.
   - 모든 추론 및 임베딩은 로컬 **Ollama**(`http://localhost:11434`, 모델: `llama3`, `nomic-embed-text`)를 통합니다.
2. **계층 구조 및 무결성 보존**:
   - `Agent` 계층 변경 시 `depth` 자동 계산 및 조부모 승계(fail-safe firing) 로직의 무결성을 깨뜨리지 않습니다.
3. **보안 게이트키핑 준수**:
   - 금융, 배포, 계층 변경, 고위험 도구 호출은 반드시 [GatekeeperRequest](file:///home/saibie1677/projects/companyAI/corp/models.py) 및 [safeguard_service.py](file:///home/saibie1677/projects/companyAI/corp/services/safeguard_service.py)를 경유합니다.
4. **가벼운 반응형 UI (ADR 0002)**:
   - 프론트엔드는 Django Templates + HTMX(`django-htmx`) 기반으로 구현하며, 무거운 JS 번들러 도입을 지양합니다.

---

## 🔄 [규범 3] Post-Flight Protocol (코드 수정 후 필수 절차)

코드 수정 및 테스트가 완료된 후, 에이전트는 반드시 다음 동기화 작업을 수행해야 합니다.

### 1단계: OKF 문서 갱신
- 모델, 서비스 로직, 워크플로, 상태 머신이 변경되거나 새 기능이 추가된 경우 해당 `okf/` 문서를 수정하거나 새 문서를 추가합니다.
- 새로운 아키텍처 결정이 내려진 경우 `okf/decisions/`에 ADR을 추가합니다.

### 2단계: Graphify 지식 그래프 최신화
- 다음 명령어를 실행하여 AST 그래프를 최신 상태로 동기화합니다:
  ```bash
  ./scripts/update_knowledge.sh
  ```
  또는
  ```bash
  graphify extract . --code-only && graphify cluster-only .
  ```
- `graphify-out/graph.json`과 `graphify-out/GRAPH_REPORT.md`가 갱신되었는지 확인합니다.
