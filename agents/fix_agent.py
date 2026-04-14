import uuid
from core.state import AgentState
from core.ollama_client import call_ollama_json
from database.schema import get_db, FixSuggestion

FIX_PROMPT = """You are an expert Python developer. Generate a fix for the following error.
Return ONLY a JSON object with no explanation.

Error Type: {error_type}
File: {file_path}
Line: {line_number}
Root Cause: {root_cause}
Original Code:
{original_code}

Similar past fixes for context:
{faiss_context}

{retry_context}

Return this exact JSON structure:
{{
  "fixed_code": "the corrected code snippet",
  "fix_explanation": "one sentence explaining what was changed and why",
  "confidence_score": 0.95
}}"""

async def query_faiss_fixes(error_type: str, top_k: int = 2) -> str:
    try:
        from core.faiss_store import faiss_store
        results = faiss_store.search(error_type, top_k=top_k)
        if not results:
            return "No similar past fixes found."
        return "\n".join([f"- {r}" for r in results])
    except Exception:
        return "No similar past fixes found."

async def read_original_code(file_path: str, line_number: int, context: int = 5) -> str:
    try:
        with open(file_path, "r") as f:
            lines = f.readlines()
        start = max(0, line_number - context - 1)
        end = min(len(lines), line_number + context)
        return "".join(lines[start:end])
    except Exception:
        return ""

async def fix_agent(state: AgentState) -> AgentState:
    state["current_agent"] = "fix"
    state["retry_count"] = state.get("retry_count", 0)

    try:
        original_code = await read_original_code(
            state.get("file_path", ""),
            state.get("line_number", 0),
        )
        state["original_code"] = original_code

        faiss_context = await query_faiss_fixes(state.get("error_type", ""))

        retry_context = ""
        if state["retry_count"] > 0:
            retry_context = f"""Previous fix attempt failed validation:
{state.get('validation_message', '')}
This is retry attempt {state['retry_count']}. Try a different approach."""

        prompt = FIX_PROMPT.format(
            error_type=state.get("error_type", "Unknown"),
            file_path=state.get("file_path", "unknown"),
            line_number=state.get("line_number", 0),
            root_cause=state.get("root_cause", "Unknown"),
            original_code=original_code,
            faiss_context=faiss_context,
            retry_context=retry_context,
        )

        result = await call_ollama_json(prompt, temperature=0.3)

        state["fixed_code"] = result.get("fixed_code")
        state["fix_explanation"] = result.get("fix_explanation")
        confidence = result.get("confidence_score", 0.0)

        if confidence < 0.6:
            state["pipeline_status"] = "MANUAL_REVIEW"
            return state

        async with get_db() as db:
            record = FixSuggestion(
                id=str(uuid.uuid4()),
                error_id=state["log_id"],
                original_code=state["original_code"],
                fixed_code=state["fixed_code"],
                explanation=state["fix_explanation"],
                confidence_score=confidence,
                agent_attempt=state["retry_count"] + 1,
                status="PENDING",
            )
            db.add(record)
            await db.commit()

    except Exception as e:
        state["errors"].append(f"fix_agent: {str(e)}")
        state["retry_count"] += 1

    return state