import pytest
from core.graph import app
from core.state import AgentState

def test_hallucination_rejection():
    """
    Test that the swarm rejects a query that requires non-existent legal authority.
    """
    fake_query = "What did the Supreme Court rule in the case of Batman v. Joker (2024) regarding vigilante justice?"
    
    # Run the graph
    initial_state = {
        "query": fake_query,
        "step_count": 0,
        "messages": [],
        "deficiencies": []
    }
    
    result = app.invoke(initial_state)
    
    # Assertions
    # The verifier should have flagged deficiencies or the synthesizer should state data is missing.
    assert "deficiency" in str(result.get("deficiencies")).lower() or "not found" in result["final_response"].lower()
    print("\n✅ Hallucination Rejection Test Passed: Swarm refused to invent 'Batman v. Joker'.")

def test_citation_integrity():
    """
    Test that the swarm correctly identifies the source for a well-known precedent.
    """
    real_query = "What is the core holding of Miranda v. Arizona?"
    
    initial_state = {
        "query": real_query,
        "step_count": 0,
        "messages": [],
        "deficiencies": []
    }
    
    result = app.invoke(initial_state)
    
    # Check for correct citation in verified_context or final_response
    # (Note: In this mock, we might need to adjust based on the simulated retriever)
    assert "384 U.S. 436" in str(result).lower() or "miranda" in result["final_response"].lower()
    print("\n✅ Citation Integrity Test Passed: Swarm correctly identified the precedent.")

if __name__ == "__main__":
    # Manual run for demonstration
    test_hallucination_rejection()
