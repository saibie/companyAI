from langchain_core.tools import tool
from corp.services import comm_service

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