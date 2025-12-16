from django.core.management.base import BaseCommand
from corp.models import Task, Agent
# 새로 추가한 Review Workflow 임포트
from corp.agent_workflow import create_agent_workflow, create_review_workflow, AgentState, ReviewState
import time
from langgraph.errors import GraphRecursionError

class Command(BaseCommand):
    help = 'Runs the AI agents loop.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting AI Corp Runner..."))
        
        agent_workflow = create_agent_workflow()
        review_workflow = create_review_workflow() # 매니저용

        while True:
            # ------------------------------------------------------------------
            # Case A: [Subordinate] Do Work (THINKING or APPROVED)
            # ------------------------------------------------------------------
            # THINKING: 처음 일을 받아서 기획/제안하는 단계
            # APPROVED: 승인받은 후 실제로 집행하는 단계
            active_tasks = Task.objects.filter(
                status__in=[Task.TaskStatus.THINKING, Task.TaskStatus.APPROVED],
                assignee__is_active=True
            ).select_related('assignee')

            for task in active_tasks:
                self.stdout.write(f"▶ Agent {task.assignee.name} working on '{task.title}' (State: {task.status})...")
                
                try:
                    # 이전 결과(제안 내용)를 가져옴
                    prev_result = task.result if task.result else ""
                    
                    initial_state = AgentState(
                        messages=[],
                        task_title=task.title,
                        task_description=task.description,
                        agent_id=task.assignee.id,
                        task_status=task.status,
                        prev_result=prev_result,
                        task_id=task.id
                    )

                    final_state = agent_workflow.invoke(initial_state)
                    final_response = final_state["messages"][-1].content
                    
                    # 결과 처리
                    task.result = final_response
                    
                    if task.status == Task.TaskStatus.APPROVED:
                        # 승인받은 후 실행까지 마쳤으면 -> DONE
                        task.status = Task.TaskStatus.DONE
                        self.stdout.write(self.style.SUCCESS(f"✅ Task '{task.title}' COMPLETED (Executed)."))
                    else:
                        # THINKING 상태였다면 -> 결재 대기(WAIT_APPROVAL)로 보냄
                        task.status = Task.TaskStatus.WAIT_APPROVAL
                        self.stdout.write(self.style.SUCCESS(f"📝 Task '{task.title}' sent for APPROVAL."))
                    
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
                        from corp.models import TaskLog
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

            time.sleep(5)