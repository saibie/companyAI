import os, datetime
import django
from django.utils import timezone
from typing import TypedDict, List, Annotated
from langchain_core.messages import BaseMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langchain_community.tools import DuckDuckGoSearchRun

# Django 모델 접근
from corp.models import Agent, Task 

GLOBAL_MODEL_NAME = os.getenv("LLM_MODEL", "qwen3:8b")
# ==============================================================================
# 1. 도구(Tools) 정의 - Script MCP 스타일
# ==============================================================================

@tool
def search_web(query: str) -> str:
    """
    Use this tool to search the internet for current events or specific information.
    Args:
        query: The search keywords.
    """
    print(f"🔍 [Tool] Searching web for: {query}")
    try:
        search = DuckDuckGoSearchRun()
        # DuckDuckGo 실행 (인터넷 연결 필요)
        result = search.invoke(query)
        return f"Search Result: {result}"
    except Exception as e:
        return f"Search failed: {str(e)}"

@tool
def create_sub_agent(manager_name: str, name: str, role: str) -> str:
    """
    Creates a new subordinate agent (Hiring).
    Args:
        manager_name: The name of the agent calling this tool (YOUR name).
        name: The name of the new agent to hire.
        role: The role/job title of the new agent.
    """
    print(f"👥 [Tool] Creating agent: {name} under {manager_name}")
    try:
        # 1. 매니저(나) 찾기
        manager = Agent.objects.filter(name=manager_name).first()
        if not manager:
            return f"Error: Manager agent '{manager_name}' not found. Cannot create sub-agent."

        # 2. 하위 에이전트 생성 (Django ORM 사용)
        # create_sub_agent 메서드는 models.py에 정의되어 있다고 가정
        new_agent = manager.create_sub_agent(name=name, role=role)
        return f"Success: Hired {new_agent.name} ({new_agent.role}) as a subordinate of {manager.name}."
    except Exception as e:
        return f"Error creating agent: {str(e)}"

@tool
def fire_sub_agent(manager_name: str, target_name: str, reason: str) -> str:
    """
    Fires a subordinate agent.
    Args:
        manager_name: The name of the agent calling this tool (YOUR name).
        target_name: The name of the subordinate to fire.
        reason: The reason for firing.
    """
    # [수정] 입력값 공백 제거로 매칭 정확도 향상
    manager_name = manager_name.strip()
    target_name = target_name.strip()
    
    print(f"🔥 [Tool] Attempting to fire: '{target_name}' by '{manager_name}'")
    
    try:
        # 1. 권한 확인
        manager = Agent.objects.filter(name=manager_name).first()
        if not manager:
            msg = f"Error: Manager '{manager_name}' not found."
            print(f"❌ [Tool Error] {msg}") # [추가] 에러 로그 출력
            return msg

        # 2. 대상 찾기 (자신의 직속 부하만)
        target = Agent.objects.filter(name=target_name, manager=manager).first()
        
        if not target:
            # 디버깅을 위해 현재 부하 직원 명단을 로그에 남김
            current_subs = list(manager.subordinates.values_list('name', flat=True))
            msg = f"Error: Agent '{target_name}' is not found under manager '{manager_name}'. (Current subs: {current_subs})"
            print(f"❌ [Tool Error] {msg}") # [추가] 에러 로그 출력
            return msg

        # 3. 해고 실행
        target.delete()
        success_msg = f"Success: Fired '{target_name}'. Reason: {reason}"
        print(f"✅ [Tool Success] {success_msg}") # [추가] 성공 로그 출력
        return success_msg
        
    except Exception as e:
        error_msg = f"Error firing agent: {str(e)}"
        print(f"❌ [Tool Exception] {error_msg}") # [추가] 예외 로그 출력
        return error_msg

@tool
def assign_task(manager_name: str, assignee_name: str, title: str, description: str, current_task_id: int) -> str:
    """
    Assigns a task to a subordinate.
    Args:
        manager_name: The name of the agent calling this tool.
        assignee_name: The name of the subordinate.
        title: Task title.
        description: Detailed instructions.
        current_task_id: The ID of the task YOU are currently working on.
    """
    print(f"📨 [Tool] Assigning task '{title}' to {assignee_name} (Parent Task: {current_task_id})")
    try:
        manager = Agent.objects.filter(name=manager_name).first()
        assignee = Agent.objects.filter(name=assignee_name).first()
        
        # 현재 수행 중인(부모) 태스크 조회
        parent_task = Task.objects.filter(id=current_task_id).first()

        if not manager or not assignee or not parent_task:
            return "Error: Manager, Assignee, or Current Task not found."

        # 1. 하위 태스크 생성 (parent_task 연결)
        sub_task = Task.objects.create(
            title=title,
            description=description,
            creator=manager,
            assignee=assignee,
            parent_task=parent_task,  # [핵심] 부모 태스크 연결
            status=Task.TaskStatus.THINKING
        )
        
        # 2. 부모 태스크 상태 변경 (대기 상태로 전환)
        parent_task.status = Task.TaskStatus.WAIT_SUBTASK
        parent_task.save()

        return f"Success: Task assigned to {assignee_name}. I am now waiting for their report."
    except Exception as e:
        return f"Error assigning task: {str(e)}"

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

# 에이전트가 사용할 도구 목록
TOOLS = [search_web, create_sub_agent, fire_sub_agent, assign_task, create_plan]


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
        decision = "APPROVE"
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
    agent_id: int
    task_status: str # [추가] 현재 태스크 상태 (THINKING, APPROVED 등)
    prev_result: str # [추가] 이전에 작성했던 결과(제안서)
    task_id: int

class AgentNodes:
    def __init__(self):
        # [설정] 사용할 Ollama 모델명 (Tool Calling 지원 모델 필수: llama3.1, mistral-nemo 등)
        # 1. ChatOllama 초기화
        self.llm = ChatOllama(model=GLOBAL_MODEL_NAME, temperature=0)
        
        # 2. bind_tools: 모델에게 도구 명세 주입 (Native Tool Calling 활성화)
        self.llm_with_tools = self.llm.bind_tools(TOOLS)

    def agent_reasoning(self, state: AgentState):
        current_agent_id = state["agent_id"]
        task_status = state.get("task_status", "THINKING")
        prev_result = state.get("prev_result", "")
        
        
        task_id = state.get("task_id")
        history_context = ""
        
        now = time
        
        if task_id:
            try:
                # 현재 수행 중인 태스크 객체 가져오기
                current_task = Task.objects.get(id=task_id)
                
                # Step 1에서 만든 related_name='logs'를 통해 로그 조회
                logs = current_task.logs.all().order_by('created_at')
                
                if logs.exists():
                    history_context = "\n[⚠️ HISTORY OF PAST FAILURES]\n"
                    history_context += "You have attempted this task before but were REJECTED. Review the feedback carefully:\n"
                    
                    for i, log in enumerate(logs, 1):
                        # 너무 길면 토큰 낭비니까 적당히 잘라서 보여줌
                        short_result = log.result[:200] + "..." if len(log.result) > 200 else log.result
                        history_context += f"\n--- Attempt #{i} ---\n"
                        history_context += f"My Output: {short_result}\n"
                        history_context += f"Manager Feedback: {log.feedback}\n"
                    
                    history_context += "\nIMPORTANT: Do NOT repeat the mistakes from above. Improve your plan based on the feedback.\n"
            except Task.DoesNotExist:
                pass
        
        # 1. 현재 에이전트 및 하위 조직 정보 조회
        current_agent_name = "Unknown"
        subordinates = [] 
        subordinates_text = "None (You have no subordinates)"
        
        try:
            agent = Agent.objects.get(id=current_agent_id)
            current_agent_name = agent.name
            subordinates = list(agent.subordinates.filter(is_active=True))
            if subordinates:
                # [수정] ID를 포함하여 출력 (동명이인 구분 및 디버깅 용이)
                sub_list = [f"- [ID: {s.id}] {s.name} ({s.role})" for s in subordinates]
                subordinates_text = "\n".join(sub_list)
        except Agent.DoesNotExist:
            pass

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

        # 4. 최종 시스템 프롬프트 조립
        system_prompt_text = f"""You are {current_agent_name}, a capable AI manager.
        
        [Current Task Info]
        Task ID: {state['task_id']}  <-- VERY IMPORTANT
        Title: {state['task_title']}
        Description: {state['task_description']}
        
        [Your Team Status]
        {subordinates_text}
        
        {instruction_prompt}
        
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

def create_agent_workflow():
    nodes = AgentNodes()
    workflow = StateGraph(AgentState)

    # 노드 추가
    workflow.add_node("agent", nodes.agent_reasoning)
    
    # [핵심] LangGraph가 제공하는 ToolNode 사용
    # 모델이 도구 사용을 요청하면, 이 노드가 자동으로 함수를 실행하고 결과를 반환합니다.
    workflow.add_node("tools", ToolNode(TOOLS))

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