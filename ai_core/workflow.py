import os
from django.utils import timezone
from typing import TypedDict, List, Annotated
from langchain_core.messages import BaseMessage, SystemMessage, ToolMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_ollama import ChatOllama
from corp.services.comm_service import get_active_announcement

GLOBAL_MODEL_NAME = os.getenv("LLM_MODEL", "gemma4-ex-llmfan46:26b")

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
    
    llm = ChatOllama(model=GLOBAL_MODEL_NAME, temperature=0)
    
    prompt = f"""당신은 한국 기업의 AI 상급 매니저인 '{state['manager_name']}'입니다.
당신의 부하 에이전트 '{state['subordinate_name']}'이(가) 다음과 같은 업무 결과 및 기획안을 제출하며 승인을 요청했습니다.

[결재 요청 업무 정보]
제목: {state['task_title']}
내용: {state['task_description']}

[부하 에이전트가 제출한 결재안 / 제안서]
{state['proposed_result']}

[심사 지침 및 언어 규칙]
1. 제출된 결재안을 면밀히 검토하십시오.
   - 목표에 부합하고 구체적이면 APPROVE로 승인하십시오.
   - 결과물이 영어로 작성되었거나, 내용이 부실하고 위험한 경우 REJECT로 반려하고 '100% 한국어로 상세히 재작성하여 보고하세요'라고 피드백하십시오.
2. [절대 언어 규칙] 심사평(FEEDBACK)은 반드시 100% 정갈하고 자연스러운 한국어로만 작성하십시오.

[응답 출력 형식]
반드시 아래 형식을 엄격히 지켜서 출력하십시오:
DECISION: [APPROVE | REJECT]
FEEDBACK: [한국어로 작성한 구체적인 심사평 및 피드백]
"""
    
    response = llm.invoke(prompt).content
    
    # 파싱
    decision = "REJECT"
    feedback = response
    
    if "DECISION: APPROVE" in response or "DECISION:APPROVE" in response or "DECISION: [APPROVE]" in response:
        decision = "APPROVE"
    elif "DECISION: REJECT" in response or "DECISION:REJECT" in response or "DECISION: [REJECT]" in response:
        decision = "REJECT"
    elif "APPROVE" in response and "REJECT" not in response:
        decision = "APPROVE"
        
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
    task_status: str
    prev_result: str
    task_id: int
    subordinates: List[dict]
    history_context: str

class AgentNodes:
    def __init__(self, tools):
        self.llm = ChatOllama(model=GLOBAL_MODEL_NAME, temperature=0)
        self.llm_with_tools = self.llm.bind_tools(tools)

    def agent_reasoning(self, state: AgentState):
        task_status = state.get("task_status", "THINKING")
        prev_result = state.get("prev_result", "")
        history_context = state.get("history_context", "")
        
        # 1. 현재 에이전트 및 하위 조직 정보 조회
        current_agent_name = state.get("agent_name", "Unknown")
        subordinates = state.get("subordinates", [])
        subordinates_text = "없음 (현재 직속 부하직원이 없습니다)"
        
        if subordinates:
            sub_list = [f"- [ID: {s['id']}] {s['name']} ({s['role']})" for s in subordinates]
            subordinates_text = "\n".join(sub_list)

        # 2. 태스크 의도 파악
        task_context = (state['task_title'] + " " + state['task_description']).lower()
        is_firing_task = any(word in task_context for word in ['fire', 'layoff', 'dismiss', 'remove', 'delete', '해고', '방출'])
        is_hiring_task = any(word in task_context for word in ['hire', 'recruit', 'create', 'new agent', '고용', '채용'])

        # 3. 상태에 따른 프롬프트 분기 (100% 한국어 프롬프트)
        if task_status == "APPROVED":
            # --- [집행 단계] ---
            instruction_prompt = f"""
            [현재 상태: 승인 완료 - 실행 단계 (EXECUTION PHASE)]
            귀하가 제출한 기획안이 최종 승인되었습니다.
            
            [승인된 실행 계획]
            {prev_result}
            
            [필수 행동 지침]
            이제 필요한 도구(Tools)를 실제로 호출하여 승인된 계획을 추진하십시오.
            말만 작성하지 말고 반드시 적절한 도구 함수를 직접 실행하십시오.
            """

            if is_firing_task:
                if subordinates:
                    instruction_prompt += f"""
                    [실행 상태 확인: 해고 작업]
                    팀원 현황에 아직 {len(subordinates)}명의 부하직원이 남아있습니다.
                    'fire_sub_agent' 도구를 호출하여 대상 직원을 해고 처리하십시오.
                    """
                else:
                    instruction_prompt += "\n[실행 완료] 현재 부하직원 팀원 목록이 비어 있습니다."

            elif is_hiring_task:
                instruction_prompt += """
                [실행 상태 확인: 신규 채용]
                신규 에이전트를 고용하기 위해 'create_sub_agent' 도구를 반드시 호출하십시오.
                """
                
        else:
            # --- [기획/제안 단계] ---
            instruction_prompt = f"""
            [현재 상태: 기획 및 제안 단계 (PLANNING / PROPOSAL)]
            주어진 업무 요구사항을 분석하고 구체적인 실행 계획 및 제안서를 작성하십시오.
            
            [필수 작성 규칙]
            1. 민감 업무(인사 고용/해고 등)의 경우 도구를 바로 실행하지 말고, 상세한 기획 제안서("제시된 업무를 위해 ~를 추진하고자 합니다...")를 작성하십시오.
            2. 모든 작성 내용은 반드시 100% 정갈하고 완성도 높은 한국어로만 작성해야 합니다. 영어를 절대 섞어 쓰지 마십시오.
            """

        # 4. 최종 시스템 프롬프트 조립 (100% 한국어 지정)
        broadcast_msg = get_active_announcement()
        
        current_time = timezone.localtime()
        current_time_str = current_time.strftime("%Y년 %m월 %d일 %H시 %M분 %S초")
        system_prompt_text = f"""당신은 한국 기업의 능숙한 AI 임원/직원인 '{current_agent_name}'입니다.
        
        [현재 시각]
        {current_time_str}
        
        [현재 담당 업무]
        업무 ID: {state['task_id']}
        제목: {state['task_title']}
        상세 내용: {state['task_description']}
        
        {broadcast_msg}

        [소속 팀원 현황]
        {subordinates_text}
        
        {instruction_prompt}

        {history_context}
        
        [최우선 절대 언어 지침 - CRITICAL LANGUAGE MANDATE]
        - 모든 보고서, 기획안, 제안서, 피드백, 답변 및 대화 내용은 100% 자연스럽고 전문적인 한국어(Korean)로만 작성하십시오.
        - 절대로 영어나 타 국적 언어로 답변을 작성하지 마십시오. 영어가 포함된 경우 즉시 한국어로 번역하여 최종 답변을 완성하십시오.

        [업무 위임 규칙]
        - 부하 직원에게 업무를 하달할 경우 'assign_task' 도구에 current_task_id ({state['task_id']})를 반드시 전달하십시오.
        """
        
        has_tool_response = any(isinstance(m, ToolMessage) or getattr(m, 'type', None) == 'tool' for m in state["messages"])
        
        messages = [SystemMessage(content=system_prompt_text)] + state["messages"]
        
        if has_tool_response:
            response = self.llm.invoke(messages)
        else:
            response = self.llm_with_tools.invoke(messages)
        
        return {"messages": [response]}


# ==============================================================================
# 3. 워크플로 그래프(Graph) 구성
# ==============================================================================

def create_agent_workflow(tools):
    nodes = AgentNodes(tools)
    workflow = StateGraph(AgentState)

    workflow.add_node("agent", nodes.agent_reasoning)
    workflow.add_node("tools", ToolNode(tools))

    workflow.set_entry_point("agent")
    
    workflow.add_conditional_edges(
        "agent",
        tools_condition, 
    )
    
    workflow.add_edge("tools", "agent")

    return workflow.compile()
