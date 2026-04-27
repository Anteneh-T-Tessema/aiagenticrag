import os
from langchain_ollama import ChatOllama
from dotenv import load_dotenv

load_dotenv()

def get_model(model_name: str = "qwen2.5-coder:7b"):
    """
    Initialize the Ollama model.
    """
    return ChatOllama(
        model=model_name,
        temperature=0,
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    )

# Logic Model (Strong Reasoning)
logic_llm = get_model("qwen2.5-coder:7b")

# Routing Model (Fast/Smaller)
routing_llm = get_model("llama3.2:3b")
