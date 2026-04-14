import uuid
from core.state import AgentState
from core.ollama_client import call_ollama_json
from database.schema import get_db, DetectedError

ANALYSIS_PROMPT = """You are a Python error analysis expert.
Analyze the following error log and return ONLY a JSON object with no explanation.

Error Log:
{raw_log}

Similar past errors for context:
{faiss_context}

Return this exact JSON structure:
{{
  "error_type": "ExceptionClassName",
  "file_path": "path/to/file.py",
  "line_number": 42,
  "stack_trace": "full traceback here",
  "root_cause": "one sentence explanation of why this error occurred",
  "severity": "LOW|MEDIUM|HIGH|CRITICAL"
}}"""

async def query_faiss(raw_log: str, top_k: int = 3) -> str:
    try:
        from core.faiss_store import faiss_store
        results = faiss_store.search(raw_log, top_k=top_k)
        if not results:
            return "No similar past errors found."
        return "\n".join([f"- {r}" for r in results])
    except Exception:
        return "No similar past errors found."

async def analysis_agent(state: AgentState) -> AgentState:
    state["current_agent"] = "analysis"

    try:
        faiss_context = await query_faiss(state["raw_log"])
        prompt = ANALYSIS_PROMPT.format(
            raw_log=state["raw_log"],
            faiss_context=faiss_context,
        )
        result = await call_ollama_json(prompt, temperature=0.1)

        state["error_type"] = result.get("error_type")
        state["file_path"] = result.get("file_path")
        state["line_number"] = result.get("line_number")
        state["stack_trace"] = result.get("stack_trace")
        state["root_cause"] = result.get("root_cause")
        state["severity"] = result.get("severity", "MEDIUM")

        async with get_db() as db:
            record = DetectedError(
                id=str(uuid.uuid4()),
                log_id=state["log_id"],
                error_type=state["error_type"],
                file_path=state["file_path"],
                line_number=state["line_number"],
                stack_trace=state["stack_trace"],
                severity=state["severity"],
                status="DETECTED",
            )
            db.add(record)
            await db.commit()

    except Exception as e:
        state["errors"].append(f"analysis_agent: {str(e)}")
        state["pipeline_status"] = "FAILED"

    return state