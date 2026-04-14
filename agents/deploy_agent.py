import os
import shutil
import subprocess
import uuid
from core.state import AgentState
from database.schema import get_db, ExecutionHistory

SANDBOX_DIR = os.getenv("SANDBOX_DIR", "sandbox")

async def embed_to_faiss(state: AgentState):
    try:
        from core.faiss_store import faiss_store
        entry = f"ERROR: {state['error_type']} | CAUSE: {state['root_cause']} | FIX: {state['fix_explanation']}"
        faiss_store.add(entry)
    except Exception:
        pass

async def apply_fix_to_sandbox(state: AgentState) -> tuple[bool, str]:
    try:
        src = state.get("file_path", "")
        if not src or not os.path.exists(src):
            return False, f"Source file not found: {src}"

        os.makedirs(SANDBOX_DIR, exist_ok=True)
        dst = os.path.join(SANDBOX_DIR, os.path.basename(src))
        shutil.copy2(src, dst)

        with open(dst, "r") as f:
            lines = f.readlines()

        line_no = state.get("line_number", 0)
        fixed_code = state.get("fixed_code", "")
        context_lines = fixed_code.splitlines(keepends=True)

        start = max(0, line_no - 6)
        end = min(len(lines), line_no + 5)
        lines[start:end] = context_lines

        with open(dst, "w") as f:
            f.writelines(lines)

        result = subprocess.run(
            ["python", dst],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode != 0 and "Error" in result.stderr:
            return False, result.stderr

        return True, dst

    except Exception as e:
        return False, str(e)

async def deploy_agent(state: AgentState) -> AgentState:
    state["current_agent"] = "deploy"

    success, result = await apply_fix_to_sandbox(state)

    if not success:
        state["errors"].append(f"deploy_agent: {result}")
        state["pipeline_status"] = "FAILED"
        return state

    await embed_to_faiss(state)

    async with get_db() as db:
        record = ExecutionHistory(
            id=str(uuid.uuid4()),
            error_id=state["log_id"],
            pipeline_status="HEALED",
            retry_count=state["retry_count"],
            final_fix_id=state["execution_id"],
        )
        db.add(record)
        await db.commit()

    state["pipeline_status"] = "HEALED"
    return state