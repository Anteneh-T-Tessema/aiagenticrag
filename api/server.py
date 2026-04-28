import os
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from core.graph import app
import json
import asyncio

server = FastAPI(title="LexiSwarm API")

# Enable CORS for the frontend
server.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@server.post("/ask")
async def ask_swarm(request: Request):
    data = await request.json()
    query = data.get("query")

    async def event_generator():
        initial_state = {
            "query": query,
            "messages": [],
            "step_count": 0,
            "deficiencies": []
        }

        try:
            async for event in app.astream(initial_state):
                yield f"data: {json.dumps(event)}\n\n"
                await asyncio.sleep(0.1)
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

# Serve built React frontend (must come after API routes so /ask takes priority)
_frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if _frontend_dist.exists():
    server.mount("/", StaticFiles(directory=str(_frontend_dist), html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 7860))
    uvicorn.run(server, host="0.0.0.0", port=port)
