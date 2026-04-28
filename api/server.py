import os
import asyncio
import json
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from core.graph import app

server = FastAPI(title="LexiSwarm API")

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
            "deficiencies": [],
        }

        queue: asyncio.Queue = asyncio.Queue()

        async def run_graph():
            try:
                async for event in app.astream(initial_state):
                    await queue.put(("event", event))
            except Exception as e:
                await queue.put(("error", str(e)))
            finally:
                await queue.put(("done", None))

        task = asyncio.create_task(run_graph())

        try:
            while True:
                try:
                    kind, payload = await asyncio.wait_for(queue.get(), timeout=20.0)
                except asyncio.TimeoutError:
                    # Send SSE comment to keep the proxy connection alive
                    yield ": heartbeat\n\n"
                    continue

                if kind == "done":
                    break
                elif kind == "error":
                    yield f"data: {json.dumps({'error': payload})}\n\n"
                    break
                else:
                    yield f"data: {json.dumps(payload)}\n\n"
        finally:
            task.cancel()

    return StreamingResponse(event_generator(), media_type="text/event-stream")

# Serve built React frontend (must come after API routes so /ask takes priority)
_frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if _frontend_dist.exists():
    server.mount("/", StaticFiles(directory=str(_frontend_dist), html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 7860))
    uvicorn.run(server, host="0.0.0.0", port=port)
