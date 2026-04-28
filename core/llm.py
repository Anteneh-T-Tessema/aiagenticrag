import os
from dotenv import load_dotenv

load_dotenv()

# HF router base URL (Novita backend, supports Qwen models)
_HF_BASE_URL = "https://router.huggingface.co/novita/v3/openai/"
# Novita-formatted model name for Qwen2.5-72B
_HF_DEFAULT_MODEL = "qwen/qwen-2.5-72b-instruct"

def get_model(ollama_model: str = "qwen2.5-coder:7b"):
    hf_token = os.getenv("HF_TOKEN")

    if hf_token:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            base_url=_HF_BASE_URL,
            api_key=hf_token,
            model=os.getenv("HF_MODEL", _HF_DEFAULT_MODEL),
            temperature=0.01,
            max_tokens=1024,
        )
    else:
        from langchain_ollama import ChatOllama
        return ChatOllama(
            model=ollama_model,
            temperature=0,
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        )

# Both agents share the same cloud model; differentiate locally via ollama_model arg
logic_llm = get_model("qwen2.5-coder:7b")
routing_llm = get_model("llama3.2:3b")
