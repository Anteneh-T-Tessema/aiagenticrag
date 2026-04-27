import os
import requests
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

load_dotenv()

# Initialize FastMCP server
mcp = FastMCP("CourtListener")

COURTLISTENER_API_KEY = os.getenv("COURTLISTENER_API_KEY")
BASE_URL = "https://www.courtlistener.com/api/rest/v4"

@mcp.tool()
def search_opinions(query: str, semantic: bool = True, limit: int = 5) -> str:
    """
    Search for legal opinions on CourtListener.
    
    Args:
        query: The search keywords or legal issue.
        semantic: Whether to use semantic search (default True).
        limit: Number of results to return.
    """
    if not COURTLISTENER_API_KEY:
        return "Error: COURTLISTENER_API_KEY not found in environment."
    
    headers = {"Authorization": f"Token {COURTLISTENER_API_KEY}"}
    params = {
        "q": query,
        "type": "o",
        "semantic": str(semantic).lower(),
        "page_size": limit
    }
    
    response = requests.get(f"{BASE_URL}/search/", headers=headers, params=params)
    
    if response.status_code != 200:
        return f"Error: API returned status {response.status_code} - {response.text}"
    
    data = response.json()
    results = data.get("results", [])
    
    output = []
    for res in results:
        case_name = res.get("caseName", "Unknown Case")
        citation = res.get("citation", ["N/A"])[0]
        summary = res.get("snippet", "No snippet available.")
        opinion_id = res.get("id")
        output.append(f"### {case_name}\n**Citation:** {citation}\n**ID:** {opinion_id}\n**Summary:** {summary}\n")
    
    return "\n---\n".join(output) if output else "No results found."

@mcp.tool()
def get_opinion_details(opinion_id: str) -> str:
    """
    Retrieve full details for a specific opinion by its ID.
    """
    if not COURTLISTENER_API_KEY:
        return "Error: COURTLISTENER_API_KEY not found in environment."
    
    headers = {"Authorization": f"Token {COURTLISTENER_API_KEY}"}
    response = requests.get(f"{BASE_URL}/opinions/{opinion_id}/", headers=headers)
    
    if response.status_code != 200:
        return f"Error: API returned status {response.status_code}"
    
    return str(response.json().get("plain_text", "No text available."))

@mcp.tool()
def verify_citation(citation: str) -> str:
    """
    Verify if a legal citation is valid and exists in the CourtListener database.
    """
    if not COURTLISTENER_API_KEY:
        return "Error: COURTLISTENER_API_KEY not found in environment."
    
    headers = {"Authorization": f"Token {COURTLISTENER_API_KEY}"}
    params = {"q": citation, "type": "o"}
    
    response = requests.get(f"{BASE_URL}/search/", headers=headers, params=params)
    
    if response.status_code == 200:
        data = response.json()
        if data.get("count", 0) > 0:
            best_match = data["results"][0]
            return f"VALID: Found '{best_match.get('caseName')}' for citation {citation}."
    
    return f"INVALID or NOT FOUND: Citation {citation} could not be verified."

if __name__ == "__main__":
    mcp.run()
