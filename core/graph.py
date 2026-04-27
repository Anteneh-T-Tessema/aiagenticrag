from typing import Dict, List
from langgraph.graph import StateGraph, END
from core.state import AgentState
from core.llm import logic_llm
from agents.prompts import ORCHESTRATOR_PROMPT, RETRIEVER_PROMPT, VERIFIER_PROMPT, SYNTHESIZER_PROMPT
from langchain_core.messages import SystemMessage, HumanMessage

def orchestrator_node(state: AgentState):
    """Lead Legal Researcher: Plans the research."""
    print("--- ORCHESTRATOR: Planning ---")
    
    # Construct the prompt
    system_msg = SystemMessage(content=ORCHESTRATOR_PROMPT)
    user_msg = HumanMessage(content=f"Query: {state['query']}\nCurrent Plan: {state.get('plan', [])}\nDeficiencies: {state.get('deficiencies', [])}")
    
    response = logic_llm.invoke([system_msg, user_msg])
    
    # In a real app, we'd parse the plan into a list. For now, we'll store the text.
    return {
        "plan": [response.content],
        "step_count": state.get("step_count", 0) + 1,
        "deficiencies": [] # Clear deficiencies once we've replanned
    }

def retriever_node(state: AgentState):
    """Retriever Agent: Calls CourtListener MCP tools."""
    print("--- RETRIEVER: Fetching Precedents ---")
    
    # This node would typically use tool-calling logic. 
    # For the showcase, we'll simulate the tool response or use the logic_llm to "decide" the search terms.
    system_msg = SystemMessage(content=RETRIEVER_PROMPT)
    user_msg = HumanMessage(content=f"Plan: {state['plan'][-1]}")
    
    # Simulation: We'll pretend the agent found a case.
    # In the final version, this will be: `mcp_client.call_tool("search_opinions", ...)`
    mock_context = [
        {"source": "345 U.S. 123", "content": "The Fourth Amendment protects against unreasonable searches..."}
    ]
    
    return {"raw_context": mock_context}

def verifier_node(state: AgentState):
    """Forensic Verifier: Audits citations."""
    print("--- VERIFIER: Auditing Citations ---")
    
    system_msg = SystemMessage(content=VERIFIER_PROMPT)
    user_msg = HumanMessage(content=f"Query: {state['query']}\nRetrieved Context: {state['raw_context']}")
    
    response = logic_llm.invoke([system_msg, user_msg])
    
    # If the response contains keywords like "invalid" or "deficiency", we trigger a loop
    if "deficiency" in response.content.lower() or "invalid" in response.content.lower():
        return {"deficiencies": [response.content]}
    else:
        return {"verified_context": state['raw_context']}

def synthesizer_node(state: AgentState):
    """Synthesizer: Writes the IRAC memo."""
    print("--- SYNTHESIZER: Generating Memo ---")
    
    system_msg = SystemMessage(content=SYNTHESIZER_PROMPT)
    user_msg = HumanMessage(content=f"Verified Context: {state['verified_context']}")
    
    response = logic_llm.invoke([system_msg, user_msg])
    
    return {"final_response": response.content}

def route_verification(state: AgentState):
    """Decides loop or synthesis."""
    if state.get("deficiencies") and state.get("step_count", 0) < 3:
        print("--- ROUTER: Deficiency found. Retrying... ---")
        return "orchestrator"
    return "synthesizer"

# Build Graph
workflow = StateGraph(AgentState)
workflow.add_node("orchestrator", orchestrator_node)
workflow.add_node("retriever", retriever_node)
workflow.add_node("verifier", verifier_node)
workflow.add_node("synthesizer", synthesizer_node)

workflow.set_entry_point("orchestrator")
workflow.add_edge("orchestrator", "retriever")
workflow.add_edge("retriever", "verifier")
workflow.add_conditional_edges("verifier", route_verification, {"orchestrator": "orchestrator", "synthesizer": "synthesizer"})
workflow.add_edge("synthesizer", END)

app = workflow.compile()
