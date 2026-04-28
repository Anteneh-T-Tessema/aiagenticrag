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

def _safe_dumps(obj) -> str:
    """JSON-serialize obj; fall back to a string representation on failure."""
    try:
        return json.dumps(obj, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"Serialization failed: {e}"})


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
                    print(f"[graph] event: {list(event.keys())}", flush=True)
                    await queue.put(("event", event))
            except asyncio.CancelledError:
                print("[graph] cancelled", flush=True)
            except BaseException as e:
                print(f"[graph] error: {e}", flush=True)
                await queue.put(("error", str(e)))
            finally:
                await queue.put(("done", None))

        task = asyncio.create_task(run_graph())
        try:
            while True:
                try:
                    kind, payload = await asyncio.wait_for(queue.get(), timeout=10.0)
                except asyncio.TimeoutError:
                    yield ": heartbeat\n\n"
                    continue

                if kind == "done":
                    break
                elif kind == "error":
                    yield f"data: {_safe_dumps({'error': payload})}\n\n"
                    break
                else:
                    yield f"data: {_safe_dumps(payload)}\n\n"
        finally:
            if not task.done():
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
