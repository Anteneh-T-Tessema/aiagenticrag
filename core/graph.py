import os
import requests
from langgraph.graph import StateGraph, END
from core.state import AgentState
from core.llm import logic_llm
from agents.prompts import ORCHESTRATOR_PROMPT, RETRIEVER_PROMPT, VERIFIER_PROMPT, SYNTHESIZER_PROMPT
from langchain_core.messages import SystemMessage, HumanMessage

_CL_BASE = "https://www.courtlistener.com/api/rest/v4"

def _fetch_opinion_text(cluster_id: int, headers: dict) -> str:
    """Fetch the first 1200 chars of opinion text for a given cluster."""
    try:
        resp = requests.get(
            f"{_CL_BASE}/opinions/",
            headers=headers,
            params={"cluster": cluster_id, "page_size": 1},
            timeout=12,
        )
        if resp.status_code == 200:
            ops = resp.json().get("results", [])
            if ops:
                text = ops[0].get("plain_text") or ops[0].get("html_with_citations") or ""
                # Strip HTML tags if present
                import re
                text = re.sub(r"<[^>]+>", " ", text).strip()
                return text[:1200] if text else ""
    except Exception:
        pass
    return ""


def _search_courtlistener(query: str, limit: int = 3) -> list[dict]:
    """Search CourtListener and enrich results with opinion text."""
    api_key = os.getenv("COURTLISTENER_API_KEY")
    if not api_key:
        return [{"source": "mock", "content": "CourtListener API key not configured."}]
    headers = {"Authorization": f"Token {api_key}"}
    params = {
        "q": query,
        "type": "o",
        "stat_Precedential": "on",
        "order_by": "score desc",
        "page_size": limit,
    }
    try:
        resp = requests.get(f"{_CL_BASE}/search/", headers=headers, params=params, timeout=20)
        resp.raise_for_status()
        results = resp.json().get("results", [])
        enriched = []
        for r in results[:limit]:
            snippet = (r.get("snippet") or "").strip()
            cluster_id = r.get("cluster_id")
            # Fetch full opinion text when snippet is absent
            if not snippet and cluster_id:
                snippet = _fetch_opinion_text(cluster_id, headers)
            enriched.append({
                "source": (r.get("citation") or ["Unknown"])[0],
                "case_name": r.get("caseName", "Unknown"),
                "content": snippet or r.get("caseName", "No text available."),
                "cluster_id": cluster_id,
            })
        return enriched or [{"source": "no results", "content": "No relevant cases found."}]
    except Exception as e:
        return [{"source": "error", "content": f"CourtListener API error: {e}"}]


def orchestrator_node(state: AgentState):
    print("--- ORCHESTRATOR: Planning ---")
    system_msg = SystemMessage(content=ORCHESTRATOR_PROMPT)
    user_msg = HumanMessage(content=f"Query: {state['query']}\nCurrent Plan: {state.get('plan', [])}\nDeficiencies: {state.get('deficiencies', [])}")
    response = logic_llm.invoke([system_msg, user_msg])
    return {
        "plan": [response.content],
        "step_count": state.get("step_count", 0) + 1,
        "deficiencies": [],
    }


def retriever_node(state: AgentState):
    print("--- RETRIEVER: Fetching Precedents ---")
    # Ask the LLM to extract a concise search query from the orchestrator's plan
    system_msg = SystemMessage(content=RETRIEVER_PROMPT)
    user_msg = HumanMessage(content=(
        f"Plan: {state['plan'][-1]}\n\n"
        "Extract the single most important search query from this plan (max 10 words) "
        "and respond with ONLY that query, nothing else."
    ))
    search_query = logic_llm.invoke([system_msg, user_msg]).content.strip().strip('"')
    print(f"--- RETRIEVER: Searching CourtListener for: {search_query!r}")
    context = _search_courtlistener(search_query, limit=5)
    return {"raw_context": context}


def verifier_node(state: AgentState):
    print("--- VERIFIER: Auditing Citations ---")
    system_msg = SystemMessage(content=VERIFIER_PROMPT)
    user_msg = HumanMessage(content=f"Query: {state['query']}\nRetrieved Context: {state['raw_context']}")
    response = logic_llm.invoke([system_msg, user_msg])
    if "deficiency" in response.content.lower() or "invalid" in response.content.lower():
        return {"deficiencies": [response.content]}
    return {"verified_context": state["raw_context"]}


def synthesizer_node(state: AgentState):
    print("--- SYNTHESIZER: Generating Memo ---")
    context = state.get("verified_context") or state.get("raw_context", [])
    system_msg = SystemMessage(content=SYNTHESIZER_PROMPT)
    user_msg = HumanMessage(content=f"Verified Context: {context}")
    response = logic_llm.invoke([system_msg, user_msg])
    return {"final_response": response.content}


def route_verification(state: AgentState):
    if state.get("deficiencies") and state.get("step_count", 0) < 2:
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
