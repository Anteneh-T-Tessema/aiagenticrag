import os
from dotenv import load_dotenv

load_dotenv()

def get_model(ollama_model: str = "qwen2.5-coder:7b"):
    groq_key = os.getenv("GROQ_API_KEY")
    hf_token = os.getenv("HF_TOKEN")

    if groq_key:
        # Groq: fast, free tier, OpenAI-compatible
        from langchain_groq import ChatGroq
        return ChatGroq(
            api_key=groq_key,
            model=os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile"),
            temperature=0.01,
            max_tokens=1024,
        )
    elif hf_token:
        # HF Inference Providers (requires credits)
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            base_url="https://router.huggingface.co/novita/v3/openai/",
            api_key=hf_token,
            model=os.getenv("HF_MODEL", "qwen/qwen-2.5-72b-instruct"),
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

logic_llm = get_model("qwen2.5-coder:7b")
routing_llm = get_model("llama3.2:3b")
