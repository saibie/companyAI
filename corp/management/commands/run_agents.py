from django.core.management.base import BaseCommand
from corp.models import Task, Agent
from corp.agent_workflow import create_agent_workflow, AgentState
import time
from langgraph.errors import GraphRecursionError

class Command(BaseCommand):
    help = 'Runs the AI agents to process tasks in the queue.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting agent runner..."))
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
                    self.stdout.write(f"Agent {task.assignee.name} is thinking about task {task.title} using LangGraph...")
                    
                    initial_state = AgentState(
                        task_description=task.description,
                        chat_history=[],
                        plan="",
                        scratchpad="",
                        tool_calls=[],
                        ollama_response="",
                        model="qwen3:8b", # Use the specified model (corrected)
                        revision_feedback=task.feedback 
                    )

                    # Iterate through the stream to capture the last state before any error
                    for state_chunk in agent_workflow.stream(initial_state, config={"recursion_limit": 10}):
                        final_state = state_chunk

                    # This code is reached only if the stream completes without error
                    task.result = final_state.get("ollama_response", "No final result from LangGraph.")
                    task.status = Task.TaskStatus.WAIT_APPROVAL
                    task.save()
                    self.stdout.write(self.style.SUCCESS(f"Task '{task.title}' processed successfully and is waiting for approval."))

                except GraphRecursionError:
                    self.stdout.write(self.style.WARNING(f"Recursion limit reached for task {task.title}. Saving last available state."))
                    if final_state:
                        # final_state holds the last successful state from the stream
                        last_node_name = list(final_state.keys())[-1]
                        last_ollama_response = final_state[last_node_name].get("ollama_response", "Result not available in the last state.")

                        task.result = f"RECURSION LIMIT REACHED. Last Response: {last_ollama_response}"
                        task.status = Task.TaskStatus.WAIT_APPROVAL
                        task.feedback = "Recursion limit reached. Review the partial result and provide feedback."
                        task.save()
                    else:
                        task.status = Task.TaskStatus.REJECTED
                        task.feedback = "GraphRecursionError occurred but no state was captured."
                        task.save()

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"An unexpected error occurred while processing task {task.title}: {e}"))
                    task.status = Task.TaskStatus.REJECTED
                    task.feedback = f"Unexpected Error: {e}"
                    task.save()
            
            time.sleep(5)