import os
import re
import asyncio
import requests
from langgraph.graph import StateGraph, END
from core.state import AgentState
from core.llm import logic_llm
from agents.prompts import ORCHESTRATOR_PROMPT, VERIFIER_PROMPT, SYNTHESIZER_PROMPT
from langchain_core.messages import SystemMessage, HumanMessage

_CL_BASE = "https://www.courtlistener.com/api/rest/v4"


def _fetch_opinion_text(cluster_id: int, headers: dict) -> str:
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
                text = re.sub(r"<[^>]+>", " ", text).strip()
                return text[:1200] if text else ""
    except Exception:
        pass
    return ""


def _search_courtlistener(query: str, limit: int = 3) -> list[dict]:
    api_key = os.getenv("COURTLISTENER_API_KEY")
    if not api_key:
        return [{"source": "mock", "content": "CourtListener API key not configured."}]
    headers = {"Authorization": f"Token {api_key}"}
    federal_courts = ["scotus", "ca1", "ca2", "ca3", "ca4", "ca5", "ca6", "ca7", "ca8", "ca9", "ca10", "ca11", "cadc", "cafc"]
    params = [
        ("q", query),
        ("type", "o"),
        ("stat_Precedential", "on"),
        ("order_by", "score desc"),
        ("page_size", str(limit)),
    ] + [("court", c) for c in federal_courts]
    try:
        resp = requests.get(f"{_CL_BASE}/search/", headers=headers, params=params, timeout=20)
        print(f"--- RETRIEVER: CourtListener status={resp.status_code} url={resp.url[:120]}")
        resp.raise_for_status()
        results = resp.json().get("results", [])
        enriched = []
        for r in results[:limit]:
            snippet = (r.get("snippet") or "").strip()
            cluster_id = r.get("cluster_id")
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


async def orchestrator_node(state: AgentState):
    print("--- ORCHESTRATOR: Planning ---")
    system_msg = SystemMessage(content=ORCHESTRATOR_PROMPT)
    user_msg = HumanMessage(content=f"Query: {state['query']}\nCurrent Plan: {state.get('plan', [])}\nDeficiencies: {state.get('deficiencies', [])}")
    response = await logic_llm.ainvoke([system_msg, user_msg])
    return {
        "plan": [response.content],
        "step_count": state.get("step_count", 0) + 1,
        "deficiencies": [],
    }


async def retriever_node(state: AgentState):
    print("--- RETRIEVER: Fetching Precedents ---")
    # Use the original user query directly — most reliable signal for CourtListener
    search_query = state["query"].strip()
    print(f"--- RETRIEVER: Searching CourtListener for: {search_query!r}")
    context = await asyncio.get_event_loop().run_in_executor(
        None, lambda: _search_courtlistener(search_query, limit=5)
    )
    return {"raw_context": context}


async def verifier_node(state: AgentState):
    print("--- VERIFIER: Auditing Citations ---")
    system_msg = SystemMessage(content=VERIFIER_PROMPT)
    user_msg = HumanMessage(content=f"Query: {state['query']}\nRetrieved Context: {state['raw_context']}")
    response = await logic_llm.ainvoke([system_msg, user_msg])
    if "deficiency" in response.content.lower() or "invalid" in response.content.lower():
        return {"deficiencies": [response.content]}
    return {"verified_context": state["raw_context"]}


async def synthesizer_node(state: AgentState):
    print("--- SYNTHESIZER: Generating Memo ---")
    context = state.get("verified_context") or state.get("raw_context", [])
    system_msg = SystemMessage(content=SYNTHESIZER_PROMPT)
    user_msg = HumanMessage(content=f"Verified Context: {context}")
    response = await logic_llm.ainvoke([system_msg, user_msg])
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
