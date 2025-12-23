from langchain_core.tools import tool
from corp.services import comm_service, agent_service

@tool
def post_to_channel_tool(agent_name: str, channel_name: str, content: str) -> str:
    """
    Post a message to a shared communication channel.
    Useful for sharing findings with other teams or asking for help.
    Args:
        agent_name: Your name.
        channel_name: Target channel (e.g., '#general', '#dev-team').
        content: The message to post.
    """
    return comm_service.post_message(agent_name, channel_name, content)

@tool
def read_channel_tool(channel_name: str) -> str:
    """
    Read recent messages from a shared communication channel.
    Args:
        channel_name: Target channel name.
    """
    return comm_service.read_channel(channel_name)

@tool
def ask_manager_tool(agent_name: str, current_task_id: str, question: str) -> str:
    """
    Ask your manager (human) a question when instructions are ambiguous.
    Your status will change to WAIT_APPROVAL until the manager responds.
    Args:
        agent_name: Your name.
        current_task_id: The ID of the task you are working on.
        question: The question you want to ask.
    """
    return agent_service.ask_manager(agent_name, current_task_id, question)

@tool
def reply_to_subordinate_tool(manager_name: str, subordinate_task_id: str, answer: str) -> str:
    """
    Reply to a subordinate's question.
    This will send your answer to the subordinate and wake them up to continue working.
    Args:
        manager_name: Your name.
        subordinate_task_id: The Task ID provided in your 'Answer Request' task description.
        answer: Detailed answer or guidance.
    """
    return agent_service.reply_to_subordinate(manager_name, subordinate_task_id, answer)