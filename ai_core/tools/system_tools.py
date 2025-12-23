from langchain_core.tools import tool
from corp.models import Agent, Task

@tool
def request_tool_access(agent_name: str, tool_name: str, reason: str) -> str:
    """
    Use this tool to request access to a restricted tool (Tier 1) from the CEO.
    This will create a formal request task on the CEO's dashboard.
    
    Args:
        agent_name: Your name.
        tool_name: The name of the tool you need (e.g., 'search_web', 'python_repl').
        reason: Why you need this tool for the current task.
    """
    try:
        agent = Agent.objects.get(name=agent_name)
        
        # [핵심] CEO가 승인 버튼을 누를 수 있도록 'WAIT_APPROVAL' 상태의 태스크 생성
        # result 필드에 'REQUEST_TOOL:' 마커를 심어 뷰(View)에서 식별하게 함
        task = Task.objects.create(
            title=f"🛒 [PURCHASE REQUEST] Tool License: {tool_name}",
            description=f"Requestor: {agent_name}\nTarget Tool: {tool_name}\nReason: {reason}",
            assignee=agent,       # 요청자 본인
            creator=None,         # 시스템 생성
            status=Task.TaskStatus.WAIT_APPROVAL, # CEO 대시보드 노출 트리거
            result=f"REQUEST_TOOL:{tool_name}",   # 백엔드 식별용 마커
            feedback=""
        )
        
        return f"✅ Request submitted successfully (Task ID: {task.id}). Please wait for CEO approval."
        
    except Exception as e:
        return f"❌ Error submitting request: {str(e)}"