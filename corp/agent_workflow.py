from typing import TypedDict, List, Annotated
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langchain_core.tools import tool
from corp.ollama_client import OllamaClient
import json

class AgentState(TypedDict):
    task_description: str
    chat_history: Annotated[List[BaseMessage], lambda x, y: x + y]
    plan: str 
    scratchpad: str 
    tool_calls: List[dict] 
    ollama_response: str
    model: str
    revision_feedback: str # Feedback for plan revision

# --- Mock Tools ---
@tool
def search_web(query: str) -> str:
    """Searches the web for the given query and returns the results."""
    print(f"---MOCK TOOL: Searching web for: {query}---")
    return f"Mock search result for '{query}': Example data from a mock web search."

@tool
def execute_code(code: str) -> str:
    """Executes the given Python code in a local environment."""
    print(f"---MOCK TOOL: Executing code: {code}---")
    return f"Mock code execution result for '{code}': Code executed successfully."

@tool
def create_sub_agent(name: str, role: str, ollama_model_name: str = None, context_window_size: int = None) -> str:
    """Creates a new sub-agent under the current agent."""
    print(f"---MOCK TOOL: Creating sub-agent {name} with role {role}...")
    return f"Sub-agent {name} created successfully."

class AgentNodes:
    def __init__(self):
        self.ollama_client = OllamaClient()

    def generate_plan(self, state: AgentState) -> AgentState:
        print("---GENERATE PLAN NODE---")
        model = state["model"]
        task_description = state["task_description"]
        
        prompt = f"""You are a helpful AI assistant. Based on the following task: '{task_description}',
        create a detailed, step-by-step plan to achieve the goal. 
        Consider what tools might be useful (e.g., search_web, execute_code) and when to use them.
        Output your plan in a structured format, e.g., a numbered list.
        """
        
        try:
            response_data = self.ollama_client.generate(model=model, prompt=prompt)
            plan = response_data.get("response", "No plan generated.")
        except Exception as e:
            plan = f"Error generating plan: {e}"

        return {"plan": plan, "chat_history": [HumanMessage(content=f"Generate plan for: {task_description}"), AIMessage(content=plan)]}

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
        
        tool_outputs = []
        if "search_web" in plan.lower():
            mock_query = "important topic from task"
            tool_output = search_web.invoke({"query": mock_query})
            tool_outputs.append(f"Web Search Output: {tool_output}")
        
        if "execute_code" in plan.lower():
            mock_code = "print('hello from mock code')"
            tool_output = execute_code.invoke({"code": mock_code})
            tool_outputs.append(f"Code Execution Output: {tool_output}")
        
        if "create_sub_agent" in plan.lower():
            # Extract parameters from the plan (simplified for mock)
            name = "sub_agent_1"
            role = "task_specialist"
            ollama_model_name = "llama3.1:8b"
            context_window_size = 8192
            tool_output = create_sub_agent.invoke({
                "name": name,
                "role": role,
                "ollama_model_name": ollama_model_name,
                "context_window_size": context_window_size
            })
            tool_outputs.append(f"Sub-agent Created: {tool_output}")
            
        new_scratchpad = scratchpad + "\n" + "\n".join(tool_outputs) if tool_outputs else scratchpad
        return {"scratchpad": new_scratchpad, "chat_history": [AIMessage(content=f"Used tools: {tool_outputs}")]}

    def reflect_and_respond(self, state: AgentState) -> AgentState:
        print("---REFLECT AND RESPOND NODE---")
        model = state["model"]
        task_description = state["task_description"]
        plan = state["plan"]
        scratchpad = state["scratchpad"]

        prompt = f"""You have completed the following task: '{task_description}'
        Based on your plan:
        {plan}
        And any observations/tool outputs:
        {scratchpad}
        Provide a concise final result for the task. If you believe the result is complete and satisfactory, include the keyword 'FINAL_RESULT' in your response.
        """
        try:
            response_data = self.ollama_client.generate(model=model, prompt=prompt)
            final_response = response_data.get("response", "No final response.")
        except Exception as e:
            final_response = f"Error reflecting and responding: {e}"
        
        return {"ollama_response": final_response, "chat_history": [HumanMessage(content="Final Reflection"), AIMessage(content=final_response)]}

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
    workflow.add_node("reflect_and_respond", agent_nodes.reflect_and_respond)

    workflow.set_conditional_entry_point(
        should_start_with_revision,
        {
            "generate_plan": "generate_plan",
            "revise_plan": "revise_plan",
        },
    )
    workflow.add_edge("generate_plan", "use_tools")
    workflow.add_edge("revise_plan", "use_tools")
    workflow.add_edge("use_tools", "reflect_and_respond")
    
    workflow.add_conditional_edges(
        "reflect_and_respond",
        should_continue,
        {
            "end": END,
            "revise": "revise_plan",
        },
    )

    return workflow.compile()
