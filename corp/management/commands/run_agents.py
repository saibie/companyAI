from django.core.management.base import BaseCommand
from corp.models import Task, Agent
from corp.ollama_client import OllamaClient
from corp.memory_manager import MemoryManager
from corp.agent_workflow import create_agent_workflow, AgentState
import time

class Command(BaseCommand):
    help = 'Runs the AI agents to process tasks in the queue.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting agent runner..."))
        ollama_client = OllamaClient()
        agent_workflow = create_agent_workflow()

        while True:
            tasks = Task.objects.filter(status=Task.TaskStatus.THINKING, assignee__is_active=True).select_related('assignee')
            
            if not tasks.exists():
                self.stdout.write(self.style.SUCCESS("No tasks in THINKING state. Waiting..."))
                time.sleep(10) 
                continue

            for task in tasks:
                self.stdout.write(self.style.SUCCESS(f"Processing task: {task.title} (Agent: {task.assignee.name})"))
                
                try:
                    agent = task.assignee
                    self.stdout.write(f"Agent {agent.name} is thinking about task {task.title} using LangGraph...")
                    
                    # Initialize AgentState for LangGraph
                    initial_state = AgentState(
                        task_description=task.description,
                        chat_history=[],
                        plan="",
                        scratchpad="",
                        tool_calls=[],
                        ollama_response="",
                        model="qwen:8b", # Use the specified model
                        revision_feedback=task.feedback # Pass feedback for revision
                    )

                    # Run the LangGraph workflow
                    final_state = agent_workflow.invoke(initial_state)
                    
                    task.result = final_state.get("ollama_response", "No final result from LangGraph.") # Use ollama_response from the final state
                    task.status = Task.TaskStatus.WAIT_APPROVAL # Set to wait for approval
                    task.save()
                    
                    self.stdout.write(self.style.SUCCESS(f"Task '{task.title}' processed by {agent.name}. Result generated and waiting for approval."))

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error processing task {task.title}: {e}"))
                    task.status = Task.TaskStatus.REJECTED
                    task.feedback = f"Error: {e}"
                    task.save()
            
            time.sleep(5) 
