import os
from dotenv import load_dotenv

load_dotenv()

def get_model(ollama_model: str = "qwen2.5-coder:7b", hf_model: str = "mistralai/Mistral-7B-Instruct-v0.3"):
    hf_token = os.getenv("HF_TOKEN")

    if hf_token:
        from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
        endpoint = HuggingFaceEndpoint(
            repo_id=os.getenv("HF_MODEL", hf_model),
            huggingfacehub_api_token=hf_token,
            temperature=0.01,
            max_new_tokens=1024,
        )
        return ChatHuggingFace(llm=endpoint)
    else:
        from langchain_ollama import ChatOllama
        return ChatOllama(
            model=ollama_model,
            temperature=0,
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        )

# Logic Model (Strong Reasoning)
logic_llm = get_model("qwen2.5-coder:7b", "mistralai/Mistral-7B-Instruct-v0.3")

# Routing Model (Fast/Smaller)
routing_llm = get_model("llama3.2:3b", "mistralai/Mistral-7B-Instruct-v0.3")
