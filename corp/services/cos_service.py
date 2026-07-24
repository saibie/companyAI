import json
from corp.models import Agent, Task, GatekeeperRequest, ImmutableAuditLog
from ai_core.llm_gateway import OllamaClient
import os

GLOBAL_MODEL_NAME = os.getenv("LLM_MODEL", "gemma4-ex-llmfan46:26b")

def get_economic_simulation_metrics(user):
    """
    Economic Window & Theater of Economic Context용 시뮬레이션 지표를 계산합니다.
    """
    agents = Agent.objects.filter(owner=user, is_active=True)
    all_tasks = Task.objects.filter(assignee__owner=user)

    total_agents = agents.count()
    active_tasks_count = all_tasks.filter(status__in=[Task.TaskStatus.THINKING, Task.TaskStatus.WAIT_APPROVAL]).count()
    done_tasks_count = all_tasks.filter(status=Task.TaskStatus.DONE).count()
    escalated_count = all_tasks.filter(status=Task.TaskStatus.ESCALATED).count()
    gatekeeper_pending = GatekeeperRequest.objects.filter(agent__owner=user, status=GatekeeperRequest.RequestStatus.PENDING).count()

    # 시장 기회 포착 수치 및 확률 장 (Probability Field) 산출
    opportunity_score = min(100, 45 + done_tasks_count * 10 + active_tasks_count * 5)
    expected_roi = round(12.5 + (done_tasks_count * 3.2), 1)
    risk_index = round(min(95.0, 5.0 + (escalated_count * 15.0) + (gatekeeper_pending * 10.0)), 1)

    # 에이전트별 시뮬레이션 확률 투사 데이터
    agent_simulations = []
    for ag in agents:
        ag_tasks = all_tasks.filter(assignee=ag)
        ag_active = ag_tasks.filter(status=Task.TaskStatus.THINKING).exists()
        prob = min(98, 60 + ag_tasks.filter(status=Task.TaskStatus.DONE).count() * 8)
        
        agent_simulations.append({
            'id': str(ag.id),
            'name': ag.name,
            'role': ag.role,
            'depth': ag.depth,
            'is_active': ag_active,
            'probability': prob,
            'projected_value': f"${(prob * 150):,}",
            'status_label': 'THINKING' if ag_active else 'READY'
        })

    return {
        'total_agents': total_agents,
        'active_tasks_count': active_tasks_count,
        'done_tasks_count': done_tasks_count,
        'escalated_count': escalated_count,
        'gatekeeper_pending': gatekeeper_pending,
        'opportunity_score': opportunity_score,
        'expected_roi': expected_roi,
        'risk_index': risk_index,
        'agent_simulations': agent_simulations,
    }


def generate_executive_briefing(user):
    """
    Cognitive Shield: 수석 보좌관(Chief of Staff) AI가 전사 현황을 압축하여 제공하는 총괄 브리핑
    """
    metrics = get_economic_simulation_metrics(user)
    escalated_tasks = Task.objects.filter(assignee__owner=user, status=Task.TaskStatus.ESCALATED)
    pending_gatekeepers = GatekeeperRequest.objects.filter(agent__owner=user, status=GatekeeperRequest.RequestStatus.PENDING)

    lines = []
    lines.append(f"🫡 **[Chief of Staff AI Executive Briefing]**")
    lines.append(f"현재 로컬 LLM엔진 **`{GLOBAL_MODEL_NAME}`** 기반으로 {metrics['total_agents']}명의 AI 에이전트가 가동 중입니다.")
    lines.append(f"시장 기회 지수 **{metrics['opportunity_score']} pts** | 예상 ROI **+{metrics['expected_roi']}%** | 전사 리스크 지수 **{metrics['risk_index']}%**")

    if pending_gatekeepers.exists():
        lines.append(f"⚠️ **[보안 샌드박스 경고]**: CEO 직속 승인 대기 중인 고위험 안건이 **{pending_gatekeepers.count()}건** 있습니다.")

    if escalated_tasks.exists():
        lines.append(f"🚨 **[무한 루프/에스컬레이션 방지]**: 한계 시도 횟수를 초과하거나 루프가 감지되어 에스컬레이션된 업무가 **{escalated_tasks.count()}건** 있습니다.")

    if not pending_gatekeepers.exists() and not escalated_tasks.exists():
        lines.append(f"✅ 모든 오케스트레이션이 기술적 노이즈 없이 원활하게 집행되고 있습니다.")

    return "\n\n".join(lines)


def dispatch_ceo_directive(user, directive_text):
    """
    CEO의 자연어 전략 지시를 수석 보좌관(CoS)이 부서별 최상위 에이전트 업무로 분할 배치
    """
    executives = Agent.objects.filter(owner=user, manager__isnull=True, is_active=True)
    if not executives.exists():
        # 임원 에이전트가 없으면 CEO 직속 기본 에이전트 생성
        executive = Agent.objects.create(
            owner=user,
            name="General Chief Operating Officer",
            role="Chief Operating Officer (COO)",
            ollama_model_name=GLOBAL_MODEL_NAME,
            can_hire=True,
            can_fire=True
        )
        executives = [executive]

    created_tasks = []
    # 지시문 전달
    main_exec = executives[0]
    task = Task.objects.create(
        creator=None, # Human CEO
        assignee=main_exec,
        title=f"[CEO Strategic Directive] {directive_text[:50]}...",
        description=f"CEO Directive from Economic Window:\n{directive_text}\n\nDecompose and assign to appropriate department heads.",
        status=Task.TaskStatus.THINKING
    )
    created_tasks.append(task)
    return created_tasks
