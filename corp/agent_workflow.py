import os
import django
from typing import TypedDict, List, Annotated
from langchain_core.messages import BaseMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langchain_community.tools import DuckDuckGoSearchRun

# Django 모델 접근
from corp.models import Agent, Task 

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
    print(f"🔥 [Tool] Firing agent: {target_name} by {manager_name}")
    try:
        # 1. 권한 확인 (내 직속 부하인가?)
        manager = Agent.objects.filter(name=manager_name).first()
        if not manager:
            return f"Error: Manager '{manager_name}' not found."

        # manager=manager 조건을 추가하여 자신의 직속 부하만 찾음
        target = Agent.objects.filter(name=target_name, manager=manager).first()
        
        if not target:
            return f"Error: Agent '{target_name}' is not your direct subordinate or does not exist."

        # 2. 해고 실행 (models.py의 delete 로직에 의해 승계 처리됨)
        target.delete()
        return f"Success: Fired {target_name}. Reason: {reason}"
    except Exception as e:
        return f"Error firing agent: {str(e)}"

@tool
def assign_task(manager_name: str, assignee_name: str, title: str, description: str) -> str:
    """
    Assigns a task to a subordinate.
    Args:
        manager_name: The name of the agent calling this tool (YOUR name).
        assignee_name: The name of the subordinate to receive the task.
        title: Task title.
        description: Detailed instructions.
    """
    print(f"📨 [Tool] Assigning task '{title}' to {assignee_name}")
    try:
        manager = Agent.objects.filter(name=manager_name).first()
        
        # 부하 직원 검색 (자신의 조직 내에서만 검색하는 것이 안전하나, 편의상 전체 검색 후 매니저 확인)
        assignee = Agent.objects.filter(name=assignee_name).first()
        
        if not manager:
            return "Error: calling agent (manager) not found."
        if not assignee:
            return f"Error: Assignee '{assignee_name}' not found."

        # 태스크 생성 (Django ORM)
        Task.objects.create(
            title=title,
            description=description,
            creator=manager,
            assignee=assignee,
            status=Task.TaskStatus.THINKING # 할당 즉시 생각 시작
        )
        return f"Success: Task '{title}' assigned to {assignee_name}."
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

class AgentState(TypedDict):
    # LangGraph가 메시지 흐름(Human -> AI -> Tool -> ToolOutput -> AI)을 자동 추적
    messages: Annotated[List[BaseMessage], lambda x, y: x + y]
    
    # Context Data
    task_title: str
    task_description: str
    agent_id: int 

class AgentNodes:
    def __init__(self):
        # [설정] 사용할 Ollama 모델명 (Tool Calling 지원 모델 필수: llama3.1, mistral-nemo 등)
        model_name = "qwen3:8b" 
        
        # 1. ChatOllama 초기화
        self.llm = ChatOllama(model=model_name, temperature=0)
        
        # 2. bind_tools: 모델에게 도구 명세 주입 (Native Tool Calling 활성화)
        self.llm_with_tools = self.llm.bind_tools(TOOLS)

    def agent_reasoning(self, state: AgentState):
        """
        에이전트의 사고(Reasoning) 단계.
        DB에서 최신 조직도를 조회하여 시스템 프롬프트에 주입하고,
        모델에게 도구를 사용할지 답변을 할지 결정하게 함.
        """
        # 1. 현재 에이전트 및 조직 정보 실시간 조회
        current_agent_id = state["agent_id"]
        current_agent_name = "Unknown Agent"
        subordinates_text = "None (You have no subordinates)"
        
        try:
            agent = Agent.objects.get(id=current_agent_id)
            current_agent_name = agent.name
            
            # 직속 부하 직원 명단 조회
            subs = agent.subordinates.filter(is_active=True)
            if subs.exists():
                sub_list = [f"- {s.name} (Role: {s.role})" for s in subs]
                subordinates_text = "\n".join(sub_list)
                
        except Agent.DoesNotExist:
            print(f"⚠️ Warning: Agent ID {current_agent_id} not found.")

        # 2. 시스템 프롬프트 구성 (가장 중요)
        system_prompt_text = f"""You are {current_agent_name}, a capable AI manager.

[Your Team Status]
Here is the list of your DIRECT subordinates. You can assign tasks to them or fire them:
{subordinates_text}

[Current Task]
Title: {state['task_title']}
Description: {state['task_description']}

[Instructions]
1. Analyze the task.
2. If you need external information, use 'search_web'.
3. If the task is too big, delegate it to your subordinates using 'assign_task'.
4. If you lack manpower, hire new agents using 'create_sub_agent'.
5. If a subordinate is underperforming or not needed, you can fire them using 'fire_sub_agent'.
6. When using tools that ask for 'manager_name', YOU MUST provide your own name: '{current_agent_name}'.
7. If you have completed the task yourself, provide the final answer clearly.
"""
        
        # 3. 메시지 히스토리 조립 (System Prompt + 대화 기록)
        # LangGraph는 state['messages']에 이전 대화(Tool 결과 포함)를 자동으로 누적합니다.
        messages = [SystemMessage(content=system_prompt_text)] + state["messages"]
        
        # 4. LLM 호출
        # 모델은 스스로 ToolMessage(도구 호출)를 반환할지, AIMessage(최종 답변)를 반환할지 결정합니다.
        print(f"🤖 Agent {current_agent_name} is thinking...")
        response = self.llm_with_tools.invoke(messages)
        
        # 결과 반환 (state 업데이트)
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