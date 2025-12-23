from langchain_core.tools import tool
from corp.models import Agent, Task
from ai_core.tools.registry import TIER_1_REGISTRY

@tool
def request_tool_access(agent_name: str, tool_name: str, reason: str) -> str:
    """
    Request access to a tool.
    If the tool exists but is locked, it asks for a license.
    If the tool DOES NOT exist, it asks the CEO to develop it (Feature Request).
    """
    agent = Agent.objects.get(name=agent_name)
    
    # [핵심 로직] 존재하는 도구인가?
    if tool_name in TIER_1_REGISTRY:
        # Case A: 존재하는 도구 -> 라이선스 구매 요청
        task_title = f"🛒 [PURCHASE] Tool License: {tool_name}"
        marker = f"REQUEST_TOOL:{tool_name}"
        response_msg = f"✅ Request submitted. Waiting for license approval for '{tool_name}'."
    else:
        # Case B: 없는 도구 -> 기능 개발 요청 (Feature Request)
        task_title = f"✨ [DEV REQUEST] New Feature: {tool_name}"
        marker = f"REQUEST_DEV:{tool_name}" # 마커 구분
        response_msg = f"🚧 Feature request submitted. The CEO (Developer) needs to implement '{tool_name}' first."

    # 태스크 생성
    Task.objects.create(
        title=task_title,
        description=f"Requestor: {agent_name}\nTarget: {tool_name}\nReason: {reason}\n\n[System Note]\nChoose 'Approve' to confirm you will build/grant this.",
        assignee=agent,
        creator=None,
        status=Task.TaskStatus.WAIT_APPROVAL,
        result=marker
    )
    
    return response_msg