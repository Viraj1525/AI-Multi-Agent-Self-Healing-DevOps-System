import re
import uuid
import json
import asyncio
import os
import redis.asyncio as aioredis
from core.state import AgentState

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
LOG_FILE = os.getenv("LOG_FILE", "buggy_app/app.log")
QUEUE_KEY = "selfhealing:events"
POLL_INTERVAL = 5

ERROR_PATTERNS = re.compile(
    r"(ERROR|CRITICAL|Traceback|Exception|Error:)", re.IGNORECASE
)

async def tail_log(path: str, callback):
    with open(path, "r") as f:
        f.seek(0, 2)
        buffer = []
        while True:
            line = f.readline()
            if line:
                buffer.append(line)
                if ERROR_PATTERNS.search(line):
                    await callback("".join(buffer))
                    buffer = []
            else:
                await asyncio.sleep(POLL_INTERVAL)

async def push_to_redis(raw_log: str):
    r = await aioredis.from_url(REDIS_URL)
    event = {
        "log_id": str(uuid.uuid4()),
        "raw_log": raw_log,
    }
    await r.rpush(QUEUE_KEY, json.dumps(event))
    await r.aclose()

async def monitor_agent(state: AgentState) -> AgentState:
    state["current_agent"] = "monitor"
    state["execution_id"] = str(uuid.uuid4())
    state["retry_count"] = 0
    state["errors"] = []
    state["pipeline_status"] = "RUNNING"

    raw_log = state.get("raw_log", "")
    if not raw_log:
        state["errors"].append("No log provided to monitor agent")
        state["pipeline_status"] = "FAILED"
        return state

    state["log_id"] = str(uuid.uuid4())
    await push_to_redis(raw_log)
    return state

async def start_monitoring():
    await tail_log(LOG_FILE, push_to_redis)