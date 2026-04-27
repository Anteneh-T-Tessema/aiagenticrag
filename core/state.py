from typing import Annotated, TypedDict, List, Dict
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    # Messages in the conversation
    messages: Annotated[List[Dict], add_messages]
    # The original user request
    query: str
    # The current step-by-step research plan
    plan: List[str]
    # Raw context retrieved by the Retriever
    raw_context: List[Dict]
    # Verified citations and facts
    verified_context: List[Dict]
    # Reports of missing or invalid data from the Verifier
    deficiencies: List[str]
    # Current recursion depth to prevent infinite loops
    step_count: int
    # Final response from the synthesizer
    final_response: str
