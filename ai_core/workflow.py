import os
from typing import TypedDict, List, Annotated
from langchain_core.messages import BaseMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_ollama import ChatOllama
from corp.services.comm_service import get_active_announcement

GLOBAL_MODEL_NAME = os.getenv("LLM_MODEL", "qwen3:8b")

# ==============================================================================
# 2. 상태(State) 및 노드(Nodes) 정의
# ==============================================================================

class ReviewState(TypedDict):
    task_title: str
    task_description: str
    proposed_result: str # 부하직원이 올린 결재안
    manager_name: str
    subordinate_name: str
    decision: str # APPROVE or REJECT
    feedback: str

def manager_review_node(state: ReviewState):
    """매니저가 부하직원의 결재안을 검토하는 노드"""
    print(f"🧐 Manager {state['manager_name']} is reviewing task from {state['subordinate_name']}...")
    
    llm = ChatOllama(model=GLOBAL_MODEL_NAME, temperature=0) # 또는 qwen2.5 등
    
    prompt = f"""You are {state['manager_name']}, a manager AI.
    Your subordinate, {state['subordinate_name']}, has submitted a task for your approval.
    
    [Task Info]
    Title: {state['task_title']}
    Description: {state['task_description']}
    
    [Proposed Action/Result by Subordinate]
    {state['proposed_result']}
    
    [Your Job]
    Evaluate the proposal.
    1. If it looks good and aligns with the goal, APPROVE it.
    2. If it is wrong, dangerous, or incomplete, REJECT it with constructive feedback.
    
    [Output Format]
    You MUST output in this exact format:
    DECISION: [APPROVE | REJECT]
    FEEDBACK: [Your reasoning and instructions]
    """
    
    response = llm.invoke(prompt).content
    
    # 파싱
    decision = "REJECT"
    feedback = response
    
    if "DECISION: APPROVE" in response:
        decision = "APPROrove"
    elif "DECISION: REJECT" in response:
        decision = "REJECT"
        
    return {"decision": decision, "feedback": feedback}

def create_review_workflow():
    workflow = StateGraph(ReviewState)
    workflow.add_node("manager_review", manager_review_node)
    workflow.set_entry_point("manager_review")
    workflow.add_edge("manager_review", END)
    return workflow.compile()

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], lambda x, y: x + y]
    task_title: str
    task_description: str
    agent_name: str
    agent_id: int
    task_status: str # [추가] 현재 태스크 상태 (THINKING, APPROVED 등)
    prev_result: str # [추가] 이전에 작성했던 결과(제안서)
    task_id: int
    subordinates: List[dict]
    history_context: str

class AgentNodes:
    def __init__(self, tools):
        # [설정] 사용할 Ollama 모델명 (Tool Calling 지원 모델 필수: llama3.1, mistral-nemo 등)
        # 1. ChatOllama 초기화
        self.llm = ChatOllama(model=GLOBAL_MODEL_NAME, temperature=0)
        
        # 2. bind_tools: 모델에게 도구 명세 주입 (Native Tool Calling 활성화)
        self.llm_with_tools = self.llm.bind_tools(tools)

    def agent_reasoning(self, state: AgentState):
        task_status = state.get("task_status", "THINKING")
        prev_result = state.get("prev_result", "")
        history_context = state.get("history_context", "")
        
        # 1. 현재 에이전트 및 하위 조직 정보 조회
        current_agent_name = state.get("agent_name", "Unknown")
        subordinates = state.get("subordinates", [])
        subordinates_text = "None (You have no subordinates)"
        
        if subordinates:
            # [수정] ID를 포함하여 출력 (동명이인 구분 및 디버깅 용이)
            sub_list = [f"- [ID: {s['id']}] {s['name']} ({s['role']})" for s in subordinates]
            subordinates_text = "\n".join(sub_list)

        # 2. 태스크 의도 파악
        task_context = (state['task_title'] + " " + state['task_description']).lower()
        is_firing_task = any(word in task_context for word in ['fire', 'layoff', 'dismiss', 'remove', 'delete'])
        is_hiring_task = any(word in task_context for word in ['hire', 'recruit', 'create', 'new agent'])

        # 3. 상태에 따른 프롬프트 분기
        if task_status == "APPROVED":
            # --- [집행 단계] ---
            instruction_prompt = f"""
            [STATUS: APPROVED - EXECUTION PHASE]
            Your proposal has been APPROVED.
            
            [Your Approved Plan]
            {prev_result}
            
            [ACTION REQUIRED]
            Now, you must EXECUTE the plan using the appropriate tools.
            Do NOT just say "I did it". actually USE THE TOOLS.
            """

            if is_firing_task:
                if subordinates:
                    instruction_prompt += f"""
                    [REALITY CHECK: FIRING]
                    Look at [Your Team Status]. There are still {len(subordinates)} subordinates listed.
                    This means they are NOT fired yet.
                    You MUST use 'fire_sub_agent' tool for each person you planned to fire.
                    MAKE SURE to use the exact name displayed in [Your Team Status].
                    """
                else:
                    instruction_prompt += "\n[REALITY CHECK] Your team is empty. It seems you have successfully fired everyone."

            elif is_hiring_task:
                instruction_prompt += """
                [REALITY CHECK: HIRING]
                To hire someone, you MUST call 'create_sub_agent'. 
                If you haven't called it yet, do it now.
                """
                
        else:
            # --- [기획/제안 단계] ---
            instruction_prompt = f"""
            [STATUS: PLANNING / PROPOSAL]
            You are analyzing the task.
            
            [Instructions]
            1. If the task involves sensitive actions (Hiring, Firing):
               - DO NOT execute the tool yet.
               - Write a proposal: "I propose to [Action] because..."
               - This will be sent to your manager for approval.
            2. For safe tasks, use tools immediately.
            """

        # [수정] 4. 최종 시스템 프롬프트 조립 부분
        
        # CEO 공지사항 가져오기 (DB 조회)
        broadcast_msg = get_active_announcement()
        
        system_prompt_text = f"""You are {current_agent_name}, a capable AI manager.
        [Current Task Info]
        Task ID: {state['task_id']}
        Title: {state['task_title']}
        Description: {state['task_description']}
        
        {broadcast_msg}  <-- [여기 추가됨: CEO 공지사항이 있으면 최우선 표시]

        [Your Team Status]
        {subordinates_text}
        
        {instruction_prompt}

        {history_context}
        
        [Rules for Delegation]
        - If you assign a task to a subordinate, you MUST pass the 'current_task_id' ({state['task_id']}) to the 'assign_task' tool.
        - After assigning, your status will automatically change to WAIT_SUBTASK. Do not output "FINAL RESULT" yet.
        """
        
        messages = [SystemMessage(content=system_prompt_text)] + state["messages"]
        response = self.llm_with_tools.invoke(messages)
        
        return {"messages": [response]}


# ==============================================================================
# 3. 워크플로 그래프(Graph) 구성
# ==============================================================================

def create_agent_workflow(tools):
    nodes = AgentNodes(tools)
    workflow = StateGraph(AgentState)

    # 노드 추가
    workflow.add_node("agent", nodes.agent_reasoning)
    
    # [핵심] LangGraph가 제공하는 ToolNode 사용
    # 모델이 도구 사용을 요청하면, 이 노드가 자동으로 함수를 실행하고 결과를 반환합니다.
    workflow.add_node("tools", ToolNode(tools))

    # 진입점 설정
    workflow.set_entry_point("agent")
    
    # 조건부 엣지 (Conditional Edges)
    # agent 노드가 끝나면, tools_condition 함수가 다음을 결정합니다:
    # 1. tool_calls가 있으면 -> "tools" 노드로 이동
    # 2. tool_calls가 없으면 -> END (종료)
    workflow.add_conditional_edges(
        "agent",
        tools_condition, 
    )
    
    # 엣지 연결: 도구 실행 후에는 다시 에이전트가 결과를 확인하도록 순환
    workflow.add_edge("tools", "agent")

    return workflow.compile()
