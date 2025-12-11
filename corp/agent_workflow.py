from typing import TypedDict, List, Annotated
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langchain_core.tools import tool
from corp.ollama_client import OllamaClient
# [추가] 모델 접근을 위해 Agent, Task 모델 import
from corp.models import Agent, Task
from langchain_community.tools import DuckDuckGoSearchRun
import json
import re

class AgentState(TypedDict):
    task_title: str
    task_description: str
    chat_history: Annotated[List[BaseMessage], lambda x, y: x + y]
    agent_id: int
    plan: str 
    scratchpad: str 
    tool_calls: List[dict] 
    ollama_response: str
    model: str
    revision_feedback: str 
    critic_feedback: str

# --- Tools Definition (Interface Only) ---
# 에이전트에게 보여줄 도구 명세입니다. 실제 로직은 use_tools 메서드 안에서 처리합니다.

@tool
def search_web(query: str) -> str:
    """Searches the real web using DuckDuckGo."""
    print(f"---REAL TOOL: Searching web for: {query}---")
    try:
        search = DuckDuckGoSearchRun()
        return search.invoke(query)
    except Exception as e:
        return f"Search failed: {e}"

@tool
def execute_code(code: str) -> str:
    """Executes the given Python code in a local environment."""
    print(f"---MOCK TOOL: Executing code: {code}---")
    return f"Mock code execution result for '{code}': Code executed successfully."

@tool
def create_sub_agent(name: str, role: str) -> str:
    """Hires a new sub-agent."""
    return "Agent created."

@tool
def assign_task(assignee_name: str, task_title: str, task_desc: str) -> str:
    """Assigns a new task to a specific sub-agent."""
    return "Task assigned."

@tool
def fire_sub_agent(name: str, reason: str) -> str:
    """Fires a sub-agent. Their subordinates will be transferred."""
    return "Agent fired."

class AgentNodes:
    def __init__(self):
        self.ollama_client = OllamaClient()

    def generate_plan(self, state: AgentState) -> AgentState:
        print("---GENERATE PLAN NODE---")
        model = state["model"]
        task_title = state.get("task_title", "Untitled Task")
        task_description = state["task_description"]
        agent_id = state["agent_id"]

        # 1. 메모리 검색 (RAG)
        memories_text = ""
        try:
            # 질문을 임베딩 벡터로 변환
            embedding_resp = self.ollama_client.embeddings(model="nomic-embed-text", prompt=task_description)
            query_embedding = embedding_resp.get('embedding')
            
            if query_embedding and agent_id:
                # DB에서 현재 에이전트 객체 가져오기 (동기 호출)
                from corp.models import Agent
                from corp.memory_manager import MemoryManager
                
                current_agent = Agent.objects.get(id=agent_id)
                memory_manager = MemoryManager(current_agent)
                
                # 유사한 기억 검색
                found_memories = memory_manager.search_memory(query_embedding, top_k=3)
                
                if found_memories:
                    memories_list = [f"- {m.content} ({m.type})" for m in found_memories]
                    memories_text = "\n".join(memories_list)
                    print(f"🧠 Found {len(found_memories)} relevant memories.")
                else:
                    memories_text = "No relevant memories found."
                    
        except Exception as e:
            print(f"⚠️ Memory retrieval warning: {e}")
            memories_text = "Memory system unavailable."

        # 프롬프트에 메모리 주입 (위에서 수정한 프롬프트 앞부분에 추가)
        prompt = f"""You are a smart AI Manager and Assistant. 
        
        [Context from Memories]
        {memories_text}
        
        [Current Task]
        Title: {task_title}
        Details: {task_description}

        Create a detailed plan to solve this task.
        
        [Available Tools]
        1. **Search**: search_web("query")
        2. **Code**: execute_code("print('hello')")
        3. **Hire**: create_sub_agent("Name", "Role") - Use this if you need more hands.
        4. **Delegate**: assign_task("Agent_Name", "Task_Title", "Task_Details") - Assign work to your team.
        5. **Fire**: fire_sub_agent("Agent_Name", "Reason") - Remove underperforming agents.

        IMPORTANT: 
        - If the task is large, break it down and delegate parts to sub-agents using 'assign_task'.
        - If you don't have a suitable agent, 'create_sub_agent' first.
        
        Output a structured plan.
        """
        
        try:
            response_data = self.ollama_client.generate(model=model, prompt=prompt)
            plan = response_data.get("response", "No plan generated.")
        except Exception as e:
            plan = f"Error generating plan: {e}"

        return {"plan": plan, "chat_history": [HumanMessage(content=task_description), AIMessage(content=plan)]}

    def revise_plan(self, state: AgentState) -> AgentState:
        print("---REVISE PLAN NODE---")
        model = state["model"]
        task_description = state["task_description"]
        feedback = state["revision_feedback"]
        
        prompt = f"""You are a helpful AI assistant. Your previous attempt to complete the task '{task_description}' was not sufficient.
        Based on the feedback: '{feedback}', please create a new, revised plan.
        """
        
        try:
            response_data = self.ollama_client.generate(model=model, prompt=prompt)
            plan = response_data.get("response", "No revised plan generated.")
        except Exception as e:
            plan = f"Error revising plan: {e}"

        return {"plan": plan, "chat_history": [HumanMessage(content=f"Revise plan based on feedback: {feedback}"), AIMessage(content=plan)]}


    def use_tools(self, state: AgentState) -> AgentState:
        print("---USE TOOLS NODE---")
        plan = state["plan"]
        scratchpad = state["scratchpad"]
        agent_id = state.get("agent_id")
        tool_outputs = []
        
        import re  # 정규표현식 사용을 위해 필요

        # 1. [Web Search] 실제 검색어 추출 로직
        if "search_web" in plan.lower():
            # 예: search_web("latest ai trends") 에서 검색어 추출
            match = re.search(r'search_web\("([^"]+)"\)', plan) or re.search(r"search_web\('([^']+)'\)", plan)
            query = match.group(1) if match else state['task_title']
            try:
                res = search_web.invoke({"query": query})
            except: res = "Search failed."
            tool_outputs.append(f"🔍 Search: {res}")

        # 2. Code Execution
        if "execute_code" in plan.lower():
            # 여기도 추후엔 re.search로 실제 코드를 뽑아낼 수 있습니다.
            mock_code = "print('hello from mock code')"
            tool_output = execute_code.invoke({"code": mock_code})
            tool_outputs.append(f"Code Execution Output: {tool_output}")
        
        # 3. [Create Sub Agent] 하위 에이전트 생성 (중요!)
        if "create_sub_agent" in plan.lower():
            print("---DETECTED SUB AGENT CREATION (REAL DB WRITE)---")
            
            # 정규식으로 파라미터 추출
            match = re.search(r'create_sub_agent\("([^"]+)",\s*"([^"]+)"\)', plan)
            if match:
                name = match.group(1)
                role = match.group(2)
                
                try:
                    # [핵심 변경] State에 있는 agent_id를 이용해 부모 에이전트를 찾고, 하위 에이전트 생성
                    current_agent_id = state.get("agent_id")
                    if current_agent_id:
                        parent_agent = Agent.objects.get(id=current_agent_id)
                        new_agent = parent_agent.create_sub_agent(name=name, role=role)
                        tool_output = f"SUCCESS: Created new agent '{new_agent.name}' (ID: {new_agent.id}) under manager '{parent_agent.name}'."
                    else:
                        tool_output = "ERROR: Current Agent ID not found in state."
                except Exception as e:
                    tool_output = f"ERROR creating agent: {str(e)}"
            else:
                tool_output = "ERROR: Failed to parse create_sub_agent arguments."

            tool_outputs.append(f"Sub-agent Creation Output: {tool_output}")
            
        
        # 4. [Delegate] Assign Task (NEW)
        if "assign_task" in plan:
            # 파싱: assign_task("Name", "Title", "Desc")
            match = re.search(r'assign_task\("([^"]+)",\s*"([^"]+)",\s*"([^"]+)"\)', plan)
            if match and agent_id:
                target_name, t_title, t_desc = match.groups()
                try:
                    parent = Agent.objects.get(id=agent_id)
                    # 이름으로 하위 에이전트 찾기 (본인 하위 조직 내에서)
                    # 간단함을 위해 전체 검색 후 매니저 확인, 혹은 이름만으로 검색
                    target = Agent.objects.filter(name=target_name).first()
                    
                    if target:
                        Task.objects.create(
                            title=t_title,
                            description=t_desc,
                            creator=parent,
                            assignee=target,
                            status=Task.TaskStatus.THINKING # 즉시 작업 시작
                        )
                        tool_outputs.append(f"📨 Delegated: Task '{t_title}' assigned to {target_name}.")
                    else:
                        tool_outputs.append(f"❌ Delegate Failed: Agent '{target_name}' not found.")
                except Exception as e:
                    tool_outputs.append(f"❌ Delegate Error: {e}")

        # 5. [Fire] Fire Sub Agent (NEW)
        if "fire_sub_agent" in plan:
            match = re.search(r'fire_sub_agent\("([^"]+)",\s*"([^"]+)"\)', plan)
            if match and agent_id:
                target_name, reason = match.groups()
                try:
                    target = Agent.objects.filter(name=target_name).first()
                    if target:
                        # models.py의 delete() 로직이 실행되어 부하 직원 승계 및 알림 태스크 생성됨 [cite: 166-172]
                        target.delete() 
                        tool_outputs.append(f"🔥 Fired: Agent '{target_name}' has been removed. (Reason: {reason})")
                    else:
                        tool_outputs.append(f"❌ Fire Failed: Agent '{target_name}' not found.")
                except Exception as e:
                    tool_outputs.append(f"❌ Fire Error: {e}")

        # 결과 합치기
        new_scratchpad = scratchpad + "\n" + "\n".join(tool_outputs) if tool_outputs else scratchpad
        return {
            "scratchpad": new_scratchpad, 
            "chat_history": [AIMessage(content=f"Tools Result: {tool_outputs}")]
        }

    def critic_review(self, state: AgentState) -> AgentState:
        print("---CRITIC REVIEW NODE---")
        model = state["model"]
        task_description = state["task_description"]
        plan = state["plan"]
        scratchpad = state["scratchpad"]

        # 검증자(Critic) 페르소나 주입
        prompt = f"""You are a Critical Quality Assurance (QA) Analyst.
        Your job is to strictly evaluate the work done by another AI agent.

        [Task Goal]
        {task_description}

        [Agent's Plan]
        {plan}

        [Agent's Execution Results]
        {scratchpad}

        Evaluate the results based on these criteria:
        1. Accuracy: Did the agent find the actual answer? Or is it hallucinating?
        2. Completeness: Did they follow the plan completely?
        3. Quality: Is the result actually useful for the CEO?

        OUTPUT FORMAT:
        - If the work is perfect and complete, output ONLY the word: "APPROVE"
        - If there are issues, provide a short, bulleted list of what is missing or wrong. (Do NOT output 'APPROVE' if there are issues).
        """

        try:
            # 검증은 조금 더 똑똑한 모델이 하면 좋지만, 일단 같은 모델 사용
            response_data = self.ollama_client.generate(model=model, prompt=prompt)
            critic_response = response_data.get("response", "No critique generated.")
        except Exception as e:
            critic_response = f"Error during critique: {e}"
        
        print(f"🧐 Critic's Verdict: {critic_response[:100]}...") # 로그 확인용
        return {"critic_feedback": critic_response}
    
    def reflect_and_respond(self, state: AgentState) -> AgentState:
        print("---REFLECT AND RESPOND NODE---")
        model = state["model"]
        task_description = state["task_description"]
        plan = state["plan"]
        scratchpad = state["scratchpad"]
        
        # [변경] 상태에서 비평(critic_feedback)을 가져옴
        critic_feedback = state.get("critic_feedback", "No critique available.")

        prompt = f"""You have executed the plan and received a review from the QA team.
        
        [Task]
        {task_description}
        
        [Execution Results]
        {scratchpad}
        
        [QA Critic's Feedback]
        {critic_feedback}
        
        Analyze the QA Feedback carefully.
        
        1. If the QA feedback says "APPROVE":
           - You can now finalize the task.
           - Provide the final detailed answer.
           - YOU MUST include the keyword 'FINAL_RESULT' in your response.
           
        2. If the QA feedback points out errors or missing parts:
           - DO NOT include 'FINAL_RESULT'.
           - Instead, acknowledge the mistake and explain what you will do next to fix it based on the feedback.
           - This text will be used to revise your plan in the next step.
        """
        
        try:
            response_data = self.ollama_client.generate(model=model, prompt=prompt)
            final_response = response_data.get("response", "No response generated.")
        except Exception as e:
            final_response = f"Error during reflection: {e}"
        
        updates = {
            "ollama_response": final_response, 
            "chat_history": [HumanMessage(content="Reflect on results"), AIMessage(content=final_response)]
        }
        
        # FINAL_RESULT가 없으면 루프를 돌림
        if "FINAL_RESULT" not in final_response:
            print(f"🔄 LOOP TRIGGERED: Critic rejected the result.")
            updates["revision_feedback"] = f"Critic Feedback: {critic_feedback} \n\n Agent's Reflection: {final_response}"
            
        return updates

def should_continue(state: AgentState) -> str:
    print("---DECISION NODE: SHOULD CONTINUE?---")
    if "FINAL_RESULT" in state["ollama_response"]:
        print("Decision: End workflow.")
        return "end"
    else:
        print("Decision: Revise plan.")
        return "revise"

def should_start_with_revision(state: AgentState) -> str:
    print("---DECISION NODE: SHOULD START WITH REVISION?---")
    if state.get("revision_feedback"): # Check if revision feedback is present
        print("Decision: Start with revise_plan.")
        return "revise_plan"
    else:
        print("Decision: Start with generate_plan.")
        return "generate_plan"

def create_agent_workflow():
    agent_nodes = AgentNodes()
    workflow = StateGraph(AgentState)

    workflow.add_node("generate_plan", agent_nodes.generate_plan)
    workflow.add_node("revise_plan", agent_nodes.revise_plan)
    workflow.add_node("use_tools", agent_nodes.use_tools)
    
    # [추가] 검증자 노드 등록
    workflow.add_node("critic_review", agent_nodes.critic_review) 
    
    workflow.add_node("reflect_and_respond", agent_nodes.reflect_and_respond)

    # 진입점 설정 (동일)
    workflow.set_conditional_entry_point(
        should_start_with_revision,
        {
            "generate_plan": "generate_plan",
            "revise_plan": "revise_plan",
        },
    )

    # [수정] 엣지 연결 변경: use_tools -> critic_review -> reflect_and_respond
    workflow.add_edge("generate_plan", "use_tools")
    workflow.add_edge("revise_plan", "use_tools")
    
    # ▼▼▼ 변경된 부분 ▼▼▼
    workflow.add_edge("use_tools", "critic_review")          # 도구 사용 후 검증 받으러 감
    workflow.add_edge("critic_review", "reflect_and_respond") # 검증 결과 들고 성찰하러 감
    # ▲▲▲

    workflow.add_conditional_edges(
        "reflect_and_respond",
        should_continue,
        {
            "end": END,
            "revise": "revise_plan",
        },
    )

    return workflow.compile()