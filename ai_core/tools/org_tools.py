from typing import List
from langchain_core.tools import tool

@tool
def create_plan(steps: List[str]) -> str:
    """
    Use this tool to create a structured plan BEFORE executing actions.
    Args:
        steps: A list of detailed steps to complete the task.
    """
    # 실제로는 여기서 DB의 Task 모델에 plan 필드를 업데이트할 수도 있습니다.
    formatted_plan = "\n".join([f"{i+1}. {step}" for i, step in enumerate(steps)])
    
    print(f"📝 [Tool] Plan Created:\n{formatted_plan}")
    
    # 이 반환값은 에이전트의 기억(History)에 남게 되어, 
    # 에이전트가 이후 이 계획을 보며 작업을 수행하게 됩니다.
    return f"Plan saved successfully:\n{formatted_plan}"
