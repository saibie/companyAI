from django.core.management.base import BaseCommand
from corp.models import Task, Agent
from corp.agent_workflow import create_agent_workflow, AgentState
import time
from langgraph.errors import GraphRecursionError
import logging
import json
import signal

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
logger.addHandler(handler)

stop_running = False

def _signal_handler(signum, frame):
    global stop_running
    logger.info("Received signal %s, stopping agent runner...", signum)
    stop_running = True

signal.signal(signal.SIGINT, _signal_handler)
signal.signal(signal.SIGTERM, _signal_handler)


def deep_serialize(obj):
    """Recursively serialize an object to JSON-serializable primitives.
    - If object has a 'content' attribute (e.g., HumanMessage/AIMessage), use it.
    - For dict/list/tuple/set, recurse into elements.
    - For primitives, return as-is. Otherwise, fallback to str(o).
    """
    def _ser(o):
        # primitives
        if o is None or isinstance(o, (str, int, float, bool)):
            return o
        # objects with content attribute (e.g., BaseMessage subclasses)
        if hasattr(o, "content"):
            try:
                return o.content
            except Exception:
                return str(o)
        # dict
        if isinstance(o, dict):
            return {k: _ser(v) for k, v in o.items()}
        # list/tuple/set
        if isinstance(o, (list, tuple, set)):
            return [_ser(i) for i in o]
        # fallback
        try:
            # attempt to JSON-serialize via str()
            return str(o)
        except Exception:
            return repr(o)
    return _ser(obj)

class Command(BaseCommand):
    help = 'Runs the AI agents to process tasks in the queue.'

    def handle(self, *args, **options):
        global stop_running
        self.stdout.write(self.style.SUCCESS("Starting agent runner..."))
        agent_workflow = create_agent_workflow()

        while not stop_running:
            tasks = Task.objects.filter(status=Task.TaskStatus.THINKING, assignee__is_active=True).select_related('assignee')

            if not tasks.exists():
                self.stdout.write(self.style.SUCCESS("No tasks in THINKING state. Waiting..."))
                time.sleep(10)
                continue

            for task in tasks:
                if stop_running:
                    break
                self.stdout.write(self.style.SUCCESS(f"Processing task: {task.title} (Agent: {task.assignee.name})"))

                final_state = None
                last_serialized = None
                try:
                    self.stdout.write(f"Agent {task.assignee.name} is thinking about task {task.title} using LangGraph...")

                    initial_state = AgentState(
                        task_description=task.description,
                        chat_history=[],
                        plan="",
                        scratchpad="",
                        tool_calls=[],
                        ollama_response="",
                        model="qwen3:8b",
                        revision_feedback=task.feedback
                    )

                    for state_chunk in agent_workflow.stream(initial_state, config={"recursion_limit": 50}):
                        final_state = state_chunk
                        try:
                            serialized = deep_serialize(state_chunk)
                            last_serialized = serialized
                            logger.debug("State chunk: %s", json.dumps(serialized, ensure_ascii=False))
                        except Exception as e:
                            logger.exception("Failed to serialize state chunk: %s", e)

                    task.result = final_state.get("ollama_response", "No final result from LangGraph.")
                    # attach last chat_history for debugging
                    if last_serialized:
                        task.result += "\n\n---DEBUG CHAT HISTORY---\n" + json.dumps(last_serialized.get("chat_history", []), ensure_ascii=False, indent=2)
                    task.status = Task.TaskStatus.WAIT_APPROVAL
                    task.save()
                    self.stdout.write(self.style.SUCCESS(f"Task '{task.title}' processed successfully and is waiting for approval."))

                except GraphRecursionError:
                    self.stdout.write(self.style.WARNING(f"Recursion limit reached for task {task.title}. Saving last available state."))
                    if final_state:
                        if last_serialized is None:
                            try:
                                last_serialized = deep_serialize(final_state)
                            except Exception:
                                last_serialized = {"error": "failed to serialize_final_state"}
                        last_ollama_response = last_serialized.get("ollama_response", "Result not available in the last state.")
                        task.result = f"RECURSION LIMIT REACHED. Last Response: {last_ollama_response}\n\n---DEBUG LAST STATE---\n" + json.dumps(last_serialized, ensure_ascii=False, indent=2)
                        task.status = Task.TaskStatus.WAIT_APPROVAL
                        task.feedback = "Recursion limit reached. Review the partial result and provide feedback."
                        task.save()
                    else:
                        task.status = Task.TaskStatus.REJECTED
                        task.feedback = "GraphRecursionError occurred but no state was captured."
                        task.save()

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"An unexpected error occurred while processing task {task.title}: {e}"))
                    logger.exception("Unexpected error processing task %s", task.title)
                    # attach last_serialized if present
                    if last_serialized:
                        task.result = f"Unexpected Error: {e}\n\n---DEBUG LAST STATE---\n" + json.dumps(last_serialized, ensure_ascii=False, indent=2)
                    task.status = Task.TaskStatus.REJECTED
                    task.feedback = f"Unexpected Error: {e}"
                    task.save()

            time.sleep(5)
