from typing import TypedDict, Optional, List

class AgentState(TypedDict):
    raw_log: str
    log_id: str
    error_type: Optional[str]
    file_path: Optional[str]
    line_number: Optional[int]
    stack_trace: Optional[str]
    root_cause: Optional[str]
    severity: Optional[str]
    original_code: Optional[str]
    fixed_code: Optional[str]
    fix_explanation: Optional[str]
    validation_passed: Optional[bool]
    validation_message: Optional[str]
    retry_count: int
    current_agent: str
    pipeline_status: str
    errors: List[str]
    execution_id: str