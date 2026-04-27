import os
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
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

        # Stream the graph events
        async for event in app.astream(initial_state):
            # Format event for SSE
            yield f"data: {json.dumps(event)}\n\n"
            await asyncio.sleep(0.1)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(server, host="0.0.0.0", port=8000)
