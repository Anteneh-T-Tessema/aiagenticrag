# Agentic RAG Swarm: Legal Intelligence & Discovery

![LexiSwarm Hero](lexiswarm_hero_concept.png)

An autonomous, multi-agent ecosystem for high-precision legal research, case law analysis, and forensic citation verification. LexiSwarm moves beyond standard RAG by implementing a **Forensic Audit Loop** that eliminates hallucinations in high-stakes legal contexts.

---

## 🌐 Live Deployment

### 1. Frontend (GitHub Pages)
The Discovery Studio is deployed at: **`https://Anteneh-T-Tessema.github.io/aiagenticrag/`**

### 2. Backend (Cloud Deployment)
The backend is containerized and ready for cloud deployment. To host the backend:
1. **Connect to Railway/Render**: Connect your fork of this repository to [Railway.app](https://railway.app/).
2. **Environment Variables**: Add your `COURTLISTENER_API_KEY` to the service environment.
3. **Frontend Connection**: In the GitHub Actions settings for your frontend, add `VITE_BACKEND_URL` pointing to your new Railway URL.

---

## 🏗️ Swarm Architecture
LexiSwarm utilizes **LangGraph** to manage a stateful loop between specialized agents:
- **Orchestrator**: Plans the research jurisdictional strategy.
- **Retriever**: Standardized MCP-based data fetching from CourtListener.
- **Forensic Verifier**: Audits citations for accuracy and negative treatment.
- **Synthesizer**: Generates final verified legal memos in IRAC format.

---

## 🛠️ Local Development

### 1. Prerequisites
- **Ollama**: Running locally with `qwen2.5-coder:7b`.
- **Python 3.10+** (Required for MCP SDK).

### 2. Setup Environment
```bash
python3.10 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Launch the Swarm
```bash
# Start Backend
uvicorn api.server:server --port 8888

# Start Frontend Studio
cd frontend && npm run dev -- --port 3333
```

---

## 🧪 Documentation
For a deep dive into the swarm logic and data flow, see [ARCHITECTURE.md](ARCHITECTURE.md).
