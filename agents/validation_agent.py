import ast
import subprocess
import os
from core.state import AgentState

TEST_DIR = os.getenv("TEST_DIR", "tests")

def syntax_check(code: str) -> tuple[bool, str]:
    try:
        ast.parse(code)
        return True, "Syntax OK"
    except SyntaxError as e:
        return False, f"SyntaxError at line {e.lineno}: {e.msg}"

def run_pytest(file_path: str) -> tuple[bool, str]:
    test_file = os.path.join(
        TEST_DIR,
        "test_" + os.path.basename(file_path)
    )
    if not os.path.exists(test_file):
        return True, "No test file found — skipping pytest"

    try:
        result = subprocess.run(
            ["pytest", test_file, "-v", "--tb=short"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        passed = result.returncode == 0
        output = result.stdout + result.stderr
        return passed, output
    except subprocess.TimeoutExpired:
        return False, "pytest timed out after 30s"
    except Exception as e:
        return False, f"pytest error: {str(e)}"

async def validation_agent(state: AgentState) -> AgentState:
    state["current_agent"] = "validation"

    fixed_code = state.get("fixed_code", "")
    if not fixed_code:
        state["validation_passed"] = False
        state["validation_message"] = "No fixed_code provided"
        state["retry_count"] += 1
        return state

    syntax_ok, syntax_msg = syntax_check(fixed_code)
    if not syntax_ok:
        state["validation_passed"] = False
        state["validation_message"] = syntax_msg
        state["retry_count"] += 1
        return state

    pytest_ok, pytest_msg = run_pytest(state.get("file_path", ""))
    state["validation_passed"] = pytest_ok
    state["validation_message"] = pytest_msg

    if not pytest_ok:
        state["retry_count"] += 1

    if state["retry_count"] >= 3:
        state["pipeline_status"] = "MANUAL_REVIEW"

    return state