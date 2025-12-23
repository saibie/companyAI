from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from corp.models import Agent, Task, TaskLog
from ai_core.tools.registry import TIER_1_REGISTRY

# ==============================================================================
# [Human CEO Only] 인사 관리 (HR)
# ==============================================================================

def hire_agent(user: User, name: str, role: str, manager_id: str = None) -> Agent:
    """사람(CEO)이 에이전트를 고용합니다."""
    manager = None
    if manager_id:
        # 내 소유의 에이전트 중에서만 매니저를 고를 수 있음 (보안)
        manager = get_object_or_404(Agent, id=manager_id, owner=user)
            
    agent = Agent.objects.create(
        owner=user, 
        name=name, 
        role=role, 
        manager=manager, 
        can_hire=True, 
        can_fire=True
    )
    
    # CEO 직속(Manager가 없는) Agent에게는 초기 셋팅으로 모든 Tier 1 도구 권한 부여
    if not manager:
        agent.allowed_tools = list(TIER_1_REGISTRY.keys())
        agent.save()
        
    return agent

def fire_agent(user: User, agent_id: str):
    """사람(CEO)이 에이전트를 해고합니다."""
    # 내 소유인지 확실히 검증
    agent = get_object_or_404(Agent, id=agent_id, owner=user)
    agent.delete() # 모델의 delete 메서드가 하위 조직 승계 로직 처리

# ==============================================================================
# [Human CEO Only] 업무 지시 및 결재 (Task & Approval)
# ==============================================================================

def create_task(user: User, title: str, description: str, assignee_id: str) -> Task:
    """사람(CEO)이 업무를 지시합니다."""
    assignee = get_object_or_404(Agent, id=assignee_id, owner=user)
    
    return Task.objects.create(
        title=title,
        description=description,
        assignee=assignee,
        creator=None, # creator가 None이면 'Human'이 만든 것
        status=Task.TaskStatus.THINKING
    )

def approve_task(user: User, task_id: str) -> Task:
    """사람(CEO)이 업무 결과를 승인합니다."""
    task = get_object_or_404(Task, id=task_id, assignee__owner=user)
    
    # [시스템 로직] 도구 사용 요청 승인 처리
    if task.result and task.result.startswith("REQUEST_TOOL:"):
        requested_tool = task.result.split(":")[1].strip()
        agent = task.assignee
        
        current_tools = agent.allowed_tools or []
        if requested_tool not in current_tools:
            current_tools.append(requested_tool)
            agent.allowed_tools = current_tools
            agent.save()
        task.feedback = f"[System] CEO approved purchase of '{requested_tool}' license."

    # [시스템 로직] 기능 개발 요청 승인 처리
    elif task.result and task.result.startswith("REQUEST_DEV:"):
        requested_feature = task.result.split(":")[1]
        task.feedback = (
            f"[System: DEVELOPER ACKNOWLEDGEMENT]\n"
            f"CEO has accepted feature request for '{requested_feature}'."
        )

    task.status = Task.TaskStatus.APPROVED
    task.save()
    return task

def reject_task(user: User, task_id: str, feedback: str) -> Task:
    """사람(CEO)이 업무를 반려합니다."""
    task = get_object_or_404(Task, id=task_id, assignee__owner=user)
    
    # 반려 기록 남기기
    TaskLog.objects.create(
        task=task,
        result=task.result,
        feedback=feedback,
        status='REJECTED'
    )
    
    task.status = Task.TaskStatus.THINKING
    task.feedback = feedback
    task.save()
    return task

def reply_question(user: User, task_id: str, answer: str) -> Task:
    """사람(CEO)이 질문에 답변합니다."""
    task = get_object_or_404(Task, id=task_id, assignee__owner=user)
    
    TaskLog.objects.create(
        task=task,
        result=task.result,
        feedback=f"[Manager's Answer] {answer}",
        status='ANSWERED'
    )
    
    task.status = Task.TaskStatus.THINKING
    task.feedback = answer
    task.save()
    return task

def mark_feature_deployed(user: User, task_id: str) -> Task:
    """사람(CEO/개발자)이 기능 배포 완료를 마킹합니다."""
    task = get_object_or_404(Task, id=task_id, assignee__owner=user)
    task.status = Task.TaskStatus.DONE
    task.result += "\n\n[System] ✅ Feature Deployed & Server Updated."
    task.save()
    return task

# ==============================================================================
# [Human CEO Only] 관리자 권한 강제 실행 (Admin Force Actions)
# ==============================================================================

def force_update_status(user: User, task_id: str, action: str) -> Task:
    task = get_object_or_404(Task, id=task_id, assignee__owner=user)
    
    if action == 'force_done':
        task.status = Task.TaskStatus.DONE
        task.result = (task.result or "") + "\n[Admin]: Forced Done."
    elif action == 'force_reject':
        task.status = Task.TaskStatus.THINKING
        task.feedback = "[Admin]: Forced Reset/Reject to retry."
        
    task.save()
    return task

def force_delete_task(user: User, task_id: str):
    task = get_object_or_404(Task, id=task_id, assignee__owner=user)
    task.delete()