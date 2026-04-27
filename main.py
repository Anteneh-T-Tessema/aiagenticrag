import sys
from core.graph import app
from dotenv import load_dotenv

load_dotenv()

def run_swarm(query: str):
    """
    Run the Legal Swarm with the given query and stream the state changes.
    """
    print(f"\n{'='*50}")
    print(f"⚖️ LEGAL DISCOVERY SWARM: {query}")
    print(f"{'='*50}\n")

    initial_state = {
        "query": query,
        "messages": [],
        "step_count": 0,
        "deficiencies": []
    }

    # Stream the events from the graph
    for event in app.stream(initial_state):
        for node, data in event.items():
            print(f"\n🔹 Agent: {node.upper()}")
            
            if "plan" in data:
                print(f"📝 New Plan: {data['plan'][0][:100]}...")
            
            if "deficiencies" in data and data["deficiencies"]:
                print(f"🚨 Deficiency Found: {data['deficiencies'][0]}")
            
            if "final_response" in data:
                print(f"\n📜 FINAL VERIFIED MEMO:\n{data['final_response']}")

def main():
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = input("Enter your legal research query: ")
    
    try:
        run_swarm(query)
    except Exception as e:
        print(f"\n❌ Error running swarm: {e}")
        print("Tip: Ensure Ollama is running and you have configured .env")

if __name__ == "__main__":
    main()
