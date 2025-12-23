from django.core.management.base import BaseCommand
from corp.models import Task, Agent, TaskLog
from ai_core.workflow import create_agent_workflow, create_review_workflow, AgentState, ReviewState
from ai_core.tools.web_search import search_web
from ai_core.tools.org_tools import create_plan
from ai_core.tools.kms_tools import search_wiki_tool
from ai_core.tools.math_tools import calculator_tool
from ai_core.tools.web_search import search_web, fetch_web_content_tool
from ai_core.tools.comm_tools import post_to_channel_tool, read_channel_tool, ask_manager_tool, reply_to_subordinate_tool
from ai_core.tools.registry import TIER_0_TOOLS, get_authorized_tools
from ai_core.tools.system_tools import request_tool_access
from corp.services import agent_service, kms_service
import time
from datetime import datetime
from django.utils import timezone
from langgraph.errors import GraphRecursionError
from langchain_core.tools import tool

# ==============================================================================
# 1. 도구(Tools) 정의
# ==============================================================================

# ai_core.tools와 corp.services를 합쳐서 LangGraph에 전달할 도구 목록 생성
# `tool` 데코레이터를 사용하여 Django ORM을 사용하는 함수를 LangChain 도구로 변환
@tool
def create_sub_agent_tool(manager_name: str, name: str, role: str, grant_hire: bool = False, grant_fire: bool = False) -> str:
    """
    Creates a new subordinate agent (Hiring).
    Args:
        manager_name: Your name.
        name: Name of the new agent.
        role: Role of the new agent.
        grant_hire: (Optional) Set True to allow this new agent to hire their own subordinates later.
        grant_fire: (Optional) Set True to allow this new agent to fire their subordinates.
    """
    # 서비스 호출 시 새로운 인자 전달
    return agent_service.create_sub_agent(manager_name, name, role, grant_hire, grant_fire)

@tool
def fire_sub_agent_tool(manager_name: str, target_name: str, reason: str) -> str:
    """
    Fires a subordinate agent. You can fire your direct reports OR any agent below them (skip-level firing).
    The fired agent's team is NOT dissolved; they are reassigned to the fired agent's manager.
    
    Args:
        manager_name: Your name.
        target_name: The name of the agent to fire (must be in your hierarchy).
        reason: Reason for firing.
    """
    return agent_service.fire_sub_agent(manager_name, target_name, reason)

@tool
def assign_task_tool(manager_name: str, assignee_name: str, title: str, description: str, current_task_id: str) -> str:
    """Assigns a task to a subordinate."""
    return agent_service.assign_task(manager_name, assignee_name, title, description, current_task_id)

BASE_TOOLS = [
    search_web, 
    fetch_web_content_tool,
    calculator_tool,
    ask_manager_tool,
    create_plan, 
    assign_task_tool, 
    search_wiki_tool,
    post_to_channel_tool,
    read_channel_tool,
    reply_to_subordinate_tool
]

class Command(BaseCommand):
    help = 'Runs the AI agents loop.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting AI Corp Runner (Dynamic Tools Enabled)..."))
        
        # [변경] System Tool(요청 도구)은 기본 소양에 포함시킴
        BASE_INHERENT_TOOLS = TIER_0_TOOLS + [request_tool_access]

        # Review Workflow는 공통이므로 밖에서 생성
        review_workflow = create_review_workflow()

        while True:
            # ==================================================================
            # Case A: [Subordinate] Do Work (THINKING or APPROVED)
            # ==================================================================
            active_tasks = Task.objects.filter(
                status__in=[Task.TaskStatus.THINKING, Task.TaskStatus.APPROVED],
                assignee__is_active=True
            ).select_related('assignee')

            for task in active_tasks:
                self.stdout.write(f"▶ Agent {task.assignee.name} working on '{task.title}' (State: {task.status})...")
                
                try:
                    current_agent_tools = BASE_INHERENT_TOOLS.copy()
                    
                    authorized_tools = get_authorized_tools(task.assignee.allowed_tools)
                    current_agent_tools.extend(authorized_tools)
                    
                    if task.assignee.can_hire:
                        current_agent_tools.append(create_sub_agent_tool)
                    if task.assignee.can_fire:
                        current_agent_tools.append(fire_sub_agent_tool)
                    
                    agent_workflow = create_agent_workflow(current_agent_tools)
                    
                    prev_result = task.result if task.result else ""

                    # 에이전트 정보 조회
                    agent = task.assignee
                    subordinates = list(agent.subordinates.filter(is_active=True).values('id', 'name', 'role'))

                    # 히스토리 컨텍스트 생성
                    logs = task.logs.all().order_by('created_at')
                    history_context = ""
                    if logs.exists():
                        history_context = "\n[⚠️ HISTORY OF PAST FAILURES]\n"
                        history_context += "You have attempted this task before but were REJECTED. Review the feedback carefully:\n"
                        
                        for i, log in enumerate(logs, 1):
                            short_result = log.result[:200] + "..." if len(log.result) > 200 else log.result
                            history_context += f"\n--- Attempt #{i} ---\n"
                            history_context += f"My Output: {short_result}\n"
                            history_context += f"Manager Feedback: {log.feedback}\n"
                        
                        history_context += "\nIMPORTANT: Do NOT repeat the mistakes from above. Improve your plan based on the feedback.\n"
                    
                    initial_state = AgentState(
                        messages=[],
                        task_title=task.title,
                        task_description=task.description,
                        agent_id=task.assignee.id,
                        agent_name=task.assignee.name,
                        task_status=task.status,
                        prev_result=prev_result,
                        task_id=task.id,
                        subordinates=subordinates,
                        history_context=history_context
                    )

                    final_state = agent_workflow.invoke(initial_state)
                    final_response = final_state["messages"][-1].content
                    
                    task.refresh_from_db()
                    
                    task.result = final_response
                    
                    if task.status == Task.TaskStatus.APPROVED:
                        # [변경] 위키 저장 성공 여부에 따라 상태 결정
                        wiki_saved = False
                        try:
                            # 2. 성공한 태스크 지식 자산화 (Auto-Archiving)
                            saved_memory = kms_service.add_knowledge(
                                owner=task.assignee.owner,
                                subject=f"Result of: {task.title}",
                                content=task.result,
                                source_task_id=task.id
                            )
                            
                            if saved_memory:
                                self.stdout.write(self.style.SUCCESS(f"   ↳ 💾 Saved to Corporate Wiki."))
                                wiki_saved = True
                            else:
                                # None이 반환되면 (모델 다운로드 실패 등) 저장이 안 된 것임
                                self.stdout.write(self.style.ERROR(f"   ↳ ❌ Failed to save to Wiki. Task remains APPROVED to retry."))
                                
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f"   ↳ ❌ Error saving to Wiki: {e}"))
                        
                        # [핵심] 위키 저장이 성공했을 때만 DONE으로 변경
                        if wiki_saved:
                            task.status = Task.TaskStatus.DONE
                            self.stdout.write(self.style.SUCCESS(f"✅ Task '{task.title}' COMPLETED."))
                        else:
                            # 실패 시 상태를 APPROVED로 유지 (다음 루프에서 재시도하게 됨)
                            pass
                    
                    elif task.status == Task.TaskStatus.WAIT_SUBTASK:
                        # [핵심 수정] 도구(assign_task)가 이미 상태를 바꿨음 -> 건드리지 않고 대기
                        self.stdout.write(self.style.WARNING(f"⏳ Task '{task.title}' delegated. Waiting for sub-tasks..."))
                        
                    elif task.status == Task.TaskStatus.THINKING:
                        # [수정] 여기가 핵심입니다!
                        # 매니저가 부하직원 지원(Help Subordinate) 업무를 성공적으로 수행했다면,
                        # '결재 대기'로 보내지 않고 즉시 '완료(DONE)' 처리합니다.
                        if "Help Subordinate" in task.title and "Success:" in str(task.result):
                            task.status = Task.TaskStatus.DONE
                            self.stdout.write(self.style.SUCCESS(f"✅ Manager replied to subordinate automatically. (Task DONE)"))
                        else:
                            # 그 외 일반적인 기획/보고 업무는 기존대로 결재 요청(WAIT_APPROVAL) 상태로 변경
                            task.status = Task.TaskStatus.WAIT_APPROVAL
                            self.stdout.write(self.style.SUCCESS(f"📝 Task '{task.title}' sent for CEO/Manager APPROVAL."))
                    
                    task.save()

                except Exception as e:
                    print(f"Error in execution: {e}")
                    # 에러 시 일단 유지

            # ------------------------------------------------------------------
            # Case B: [Manager] Review Work (WAIT_APPROVAL)
            # ------------------------------------------------------------------
            # 상사(Manager)가 있는 경우에만 AI 자동 결재 진행
            # 상사가 없으면(CEO 직속) Dashboard에 남아 사람을 기다림
            review_tasks = Task.objects.filter(
                status=Task.TaskStatus.WAIT_APPROVAL,
                assignee__manager__isnull=False  # 상사가 있는 경우만
            ).select_related('assignee', 'assignee__manager')

            for task in review_tasks:
                manager = task.assignee.manager
                self.stdout.write(f"👮‍♂️ Manager {manager.name} reviewing '{task.title}' from {task.assignee.name}...")
                
                try:
                    review_state = ReviewState(
                        task_title=task.title,
                        task_description=task.description,
                        proposed_result=task.result,
                        manager_name=manager.name,
                        subordinate_name=task.assignee.name,
                        decision="",
                        feedback=""
                    )
                    
                    final_review = review_workflow.invoke(review_state)
                    decision = final_review["decision"]
                    feedback = final_review["feedback"]
                    
                    if decision == "APPROVE":
                        task.status = Task.TaskStatus.APPROVED
                        task.feedback = f"[Manager Approved]: {feedback}"
                        self.stdout.write(self.style.SUCCESS(f"👌 Approved by {manager.name}."))
                    else:
                        TaskLog.objects.create(
                            task=task,
                            result=task.result,  # 부하가 낸 답안
                            feedback=feedback,   # 상사의 꾸지람
                            status='REJECTED'
                        )
                        
                        task.status = Task.TaskStatus.THINKING # 다시 생각하게 반려
                        task.feedback = f"[Manager Rejected]: {feedback}"
                        self.stdout.write(self.style.WARNING(f"❌ Rejected by {manager.name}."))
                    
                    task.save()
                    
                except Exception as e:
                    print(f"Error in review: {e}")
                    
            # ------------------------------------------------------------------
            # [NEW] Case C: Check Waiting Managers (Bottom-up Reporting)
            # ------------------------------------------------------------------
            # 하위 업무가 다 끝났는지 확인하고, 끝났으면 상사를 깨운다.
            waiting_tasks = Task.objects.filter(status=Task.TaskStatus.WAIT_SUBTASK)
            
            for parent_task in waiting_tasks:
                # 이 태스크에 연결된 하위 태스크들 조회
                sub_tasks = Task.objects.filter(parent_task=parent_task)
                
                # 모든 하위 태스크가 완료(DONE)되었는지 확인
                # (주의: 만약 하위 태스크가 REJECTED라면 다시 THINKING일 것이므로 DONE 아님)
                if sub_tasks.exists() and not sub_tasks.exclude(status=Task.TaskStatus.DONE).exists():
                    
                    self.stdout.write(self.style.SUCCESS(f"🔔 All sub-tasks for '{parent_task.title}' are DONE. Waking up manager..."))
                    
                    # 1. 하위 보고서 취합
                    reports = []
                    for st in sub_tasks:
                        reports.append(f"- Sub-agent {st.assignee.name} Report on '{st.title}':\n{st.result}")
                    
                    combined_report = "\n\n".join(reports)
                    
                    # 2. 상급자 태스크의 '이전 결과' 필드나 로그에 보고서 내용 추가
                    # (여기서는 result 필드에 임시로 붙이거나, 다음 턴의 Prompt에 주입하기 위해 result에 저장)
                    parent_task.result = (parent_task.result or "") + f"\n\n[SUBORDINATE REPORTS]\n{combined_report}\n[INSTRUCTION]\nSynthesize these reports and create the final output."
                    
                    # 3. 상태를 다시 THINKING으로 변경 -> Agent가 깨어나서 종합 보고서 작성 시작
                    parent_task.status = Task.TaskStatus.THINKING
                    parent_task.save()

            # ==================================================================
            # [NEW] Case D: Escalation (질문 -> 상사의 업무로 변환)
            # ==================================================================
            # 상사가 있는 에이전트가 질문(WAIT_ANSWER)을 했는데,
            # 아직 상사한테 "답변해달라"는 태스크가 안 만들어진 경우를 찾음.
            
            pending_questions = Task.objects.filter(
                status=Task.TaskStatus.WAIT_ANSWER,
                assignee__manager__isnull=False
            )

            for q_task in pending_questions:
                manager = q_task.assignee.manager
                
                # 이미 이 질문에 대해 상사가 작업 중인 태스크가 있는지 확인 (중복 생성 방지)
                # (단순하게 제목에 Task ID를 포함시켜서 구분)
                existing_manager_task = Task.objects.filter(
                    assignee=manager,
                    description__contains=f"Target Task ID: {q_task.id}"
                ).exists()

                if not existing_manager_task:
                    # 상사에게 새로운 업무 할당
                    Task.objects.create(
                        title=f"Help Subordinate: {q_task.assignee.name}",
                        description=(
                            f"Your subordinate '{q_task.assignee.name}' has asked a question.\n"
                            f"[Question]: {q_task.result}\n\n"
                            f"Action Required:\n"
                            f"1. Analyze the question (use tools if needed).\n"
                            f"2. Use 'reply_to_subordinate_tool' to send the answer.\n"
                            f"3. Target Task ID: {q_task.id}"
                        ),
                        assignee=manager,
                        creator=q_task.assignee, # 발의자는 부하직원
                        status=Task.TaskStatus.THINKING # 상사를 깨움
                    )
                    self.stdout.write(self.style.WARNING(f"🔔 Question from {q_task.assignee.name} escalated to Manager {manager.name}."))
            
            time.sleep(5)
