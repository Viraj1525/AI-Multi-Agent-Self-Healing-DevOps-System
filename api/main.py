import json
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from database.schema import init_db
from core.graph import pipeline
from core.state import AgentState

connected_clients: List[WebSocket] = []

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(title="AI Self-Healing DevOps", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

async def broadcast(message: dict):
    for client in connected_clients.copy():
        try:
            await client.send_json(message)
        except Exception:
            connected_clients.remove(client)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        connected_clients.remove(websocket)

class TriggerRequest(BaseModel):
    raw_log: str

@app.post("/trigger")
async def trigger_pipeline(req: TriggerRequest):
    initial_state: AgentState = {
        "raw_log": req.raw_log,
        "log_id": str(uuid.uuid4()),
        "error_type": None,
        "file_path": None,
        "line_number": None,
        "stack_trace": None,
        "root_cause": None,
        "severity": None,
        "original_code": None,
        "fixed_code": None,
        "fix_explanation": None,
        "validation_passed": None,
        "validation_message": None,
        "retry_count": 0,
        "current_agent": "",
        "pipeline_status": "RUNNING",
        "errors": [],
        "execution_id": str(uuid.uuid4()),
    }

    await broadcast({"event": "pipeline_started", "execution_id": initial_state["execution_id"]})
    final_state = await pipeline.ainvoke(initial_state)
    await broadcast({"event": "pipeline_complete", "status": final_state["pipeline_status"], "state": final_state})

    return {"status": final_state["pipeline_status"], "execution_id": final_state["execution_id"]}

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/explain/{execution_id}")
async def explain(execution_id: str):
    from database.schema import get_db, AgentOutput
    from sqlalchemy import select
    async with get_db() as db:
        result = await db.execute(
            select(AgentOutput).where(AgentOutput.execution_id == execution_id)
        )
        outputs = result.scalars().all()
    return {"execution_id": execution_id, "steps": [
        {"agent": o.agent_name, "status": o.status, "duration_ms": o.duration_ms}
        for o in outputs
    ]}