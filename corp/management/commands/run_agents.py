from django.core.management.base import BaseCommand
from corp.models import Task, Agent
from corp.agent_workflow import create_agent_workflow, AgentState
import time
from langgraph.errors import GraphRecursionError
from django.db.utils import OperationalError, ProgrammingError
import json # JSON 출력을 위해 추가

class Command(BaseCommand):
    help = 'Runs the AI agents to process tasks in the queue.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting agent runner..."))
        
        # DB 대기 로직 (그대로 유지)
        self.stdout.write("Waiting for Database tables to be ready...")
        while True:
            try:
                Task.objects.exists()
                self.stdout.write(self.style.SUCCESS("Database is ready!"))
                break
            except (OperationalError, ProgrammingError):
                self.stdout.write(self.style.WARNING("Database not ready yet. Retrying in 2 seconds..."))
                time.sleep(2)

        agent_workflow = create_agent_workflow()

        while True:
            tasks = Task.objects.filter(status=Task.TaskStatus.THINKING, assignee__is_active=True).select_related('assignee')
            
            if not tasks.exists():
                self.stdout.write(self.style.SUCCESS("No tasks in THINKING state. Waiting..."))
                time.sleep(10) 
                continue

            for task in tasks:
                self.stdout.write(self.style.SUCCESS(f"Processing task: {task.title} (Agent: {task.assignee.name})"))
                
                final_state = None
                try:
                    self.stdout.write(f"▶ Agent {task.assignee.name} started workflow...")
                    
                    initial_state = AgentState(
                        task_title=task.title,
                        task_description=task.description,
                        chat_history=[],
                        plan="",
                        scratchpad="",
                        tool_calls=[],
                        ollama_response="",
                        model="qwen3:8b",
                        revision_feedback=task.feedback,
                        critic_feedback="",
                        agent_id=task.assignee.id
                    )

                    # ▼▼▼ [핵심 수정] 스트리밍 로그 출력 ▼▼▼
                    # LangGraph가 한 턴(노드)을 돌 때마다 state_chunk를 뱉습니다.
                    step_count = 0
                    for state_chunk in agent_workflow.stream(initial_state, config={"recursion_limit": 15}):
                        step_count += 1
                        final_state = state_chunk
                        
                        # 현재 실행된 노드의 이름과 결과를 가져옵니다.
                        for node_name, node_output in state_chunk.items():
                            # self.stdout.write는 기본적으로 flush를 시도하지만, 확실하게 하기 위해 print 사용 권장
                            print(f"\n--- [Step {step_count}: {node_name}] ---", flush=True)
                            
                            # 전체 딕셔너리 구조 확인용 (디버깅)
                            # print(f"DEBUG CHUNK: {node_output}", flush=True) 

                            if "plan" in node_output and node_output["plan"]:
                                print(f"📝 Plan Updated: {node_output['plan'][:100]}...", flush=True)
                            
                            if "scratchpad" in node_output and node_output["scratchpad"]:
                                last_tool_log = node_output["scratchpad"].split('\n')[-1]
                                print(f"🛠️ Tool Output: {last_tool_log[:150]}...", flush=True)

                            if "critic_feedback" in node_output and node_output["critic_feedback"]:
                                print(f"🧐 Critic Said: {node_output['critic_feedback'][:100]}...", flush=True)

                            if "ollama_response" in node_output:
                                print(f"🤖 Thought: {node_output['ollama_response'][:100]}...", flush=True)
                    # ▲▲▲ [수정 끝] ▲▲▲

                    # 결과 저장 로직 (이하 동일)
                    last_node_name = list(final_state.keys())[-1]
                    final_response = final_state[last_node_name].get("ollama_response", "No final result.")
                    
                    task.result = final_response
                    task.status = Task.TaskStatus.WAIT_APPROVAL
                    task.save()
                    self.stdout.write(self.style.SUCCESS(f"✅ Task '{task.title}' finished successfully."))

                except GraphRecursionError:
                    self.stdout.write(self.style.WARNING(f"🚫 Recursion limit reached for task {task.title}."))
                    
                    # [수정] 실패 시점의 모든 정보를 긁어모으는 로직
                    error_report = "🛑 [System] Recursion Limit Reached (Loop detected).\n"
                    error_report += "The agent failed to produce a FINAL_RESULT within the limit.\n"
                    error_report += "Here is the last known state:\n"

                    if final_state:
                        # final_state는 {'node_name': {key: value}} 형태입니다.
                        for node_name, node_data in final_state.items():
                            error_report += f"\n--- Last Node: {node_name} ---\n"
                            
                            if "plan" in node_data and node_data["plan"]:
                                error_report += f"[Plan]:\n{node_data['plan']}\n"
                            
                            if "scratchpad" in node_data and node_data["scratchpad"]:
                                error_report += f"\n[Tool Outputs]:\n{node_data['scratchpad']}\n"
                            
                            if "critic_feedback" in node_data and node_data["critic_feedback"]:
                                error_report += f"\n[Critic Feedback]:\n{node_data['critic_feedback']}\n"
                                
                            if "ollama_response" in node_data and node_data["ollama_response"]:
                                error_report += f"\n[Last Thought]:\n{node_data['ollama_response']}\n"
                    else:
                        error_report += "\n(No state was captured before the error.)"

                    # DB 저장
                    task.result = error_report
                    task.status = Task.TaskStatus.WAIT_APPROVAL
                    task.feedback = "System: Recursion limit reached. Please review the partial result above."
                    task.save()

                except Exception as e:
                    import traceback
                    self.stdout.write(self.style.ERROR(f"💥 Error: {e}"))
                    self.stdout.write(traceback.format_exc()) # 상세 에러 로그 출력
                    
                    task.status = Task.TaskStatus.REJECTED
                    task.feedback = f"System Error: {e}"
                    task.save()
            
            time.sleep(5)