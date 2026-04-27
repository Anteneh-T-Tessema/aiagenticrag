# 🎓 LexiSwarm: Step-by-Step Tutorial

This tutorial guides you through the process of setting up, extending, and deploying the LexiSwarm Legal Intelligence ecosystem.

---

## 🛠️ Phase 1: Environment Setup

LexiSwarm requires a specialized environment to handle the Model Context Protocol (MCP) and heavy reasoning models.

1.  **Python 3.10+**: Ensure you are using Python 3.10 or higher.
    ```bash
    python3.10 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```
2.  **Ollama Configuration**: Pull the logic-heavy models.
    ```bash
    ollama pull qwen2.5-coder:7b
    ollama create LegalReasoner -f local_inference/LegalReasoner.Modelfile
    ```

---

## 🧠 Phase 2: Understanding Orchestration

![Orchestration](docs/img/orchestration.png)

The **Orchestrator** is the brain of the swarm. It uses a **Stateful Graph** (LangGraph) to plan research.

### How to modify the logic:
- Edit `agents/prompts.py` to change the **ORCHESTRATOR_PROMPT**.
- You can add new jurisdictions or legal domains (e.g., Intellectual Property) by updating the system prompt's constraints.

---

## 🔌 Phase 3: Extending Retrieval (MCP)

![Retrieval](docs/img/retrieval.png)

LexiSwarm uses the **Model Context Protocol (MCP)** to talk to external data.

### To add a new data source:
1.  Open `mcp_servers/courtlistener_mcp.py`.
2.  Define a new `@mcp.tool()` function.
3.  Restart the swarm. The agents will automatically see the new tool and decide when to use it based on their plan.

---

## 🔍 Phase 4: The Forensic Audit Loop

![Audit](docs/img/audit.png)

This is the most critical part of LexiSwarm. The **Verifier Agent** audits every claim.

### How it works:
1.  The Retriever provides **Raw Context**.
2.  The Verifier checks if the **Pinpoint Citations** exist and support the claim.
3.  If they don't, it returns a **Deficiency Report**.
4.  The Swarm **loops back** to the Orchestrator for a retry.

**Tutorial Task**: Try asking the swarm for a case that doesn't exist (e.g., *"What was the ruling in Batman v. Superman?"*). Watch the "Discovery Log" in the UI as the Verifier catches and rejects the hallucination.

---

## 🌐 Phase 5: Cloud Deployment

### 1. Backend (Railway/Render)
- Connect your GitHub repo.
- Railway will detect the `Dockerfile`.
- Add your `COURTLISTENER_API_KEY` to the environment variables.

### 2. Frontend (GitHub Pages)
- Enable **GitHub Actions** for your repository.
- Your frontend will automatically deploy to `https://<username>.github.io/<repo>/`.
- **Note**: Ensure the `VITE_BACKEND_URL` in your frontend settings points to your cloud backend.
