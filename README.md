# AI-Multi-Agent-Self-Healing-DevOps-System

Log File / Buggy App
        │
        ▼
[Monitoring Agent]
  - Tails logs every N seconds
  - Pattern matches: ERROR, CRITICAL, Exception, Traceback
  - If anomaly → push to Redis queue
        │
        ▼ (Redis event)
[Orchestrator - LangGraph]
  - Receives event, initializes AgentState
  - Routes to Analysis Agent
        │
        ▼
[Analysis Agent]  ←── FAISS (similar past errors)
  - Sends log + stack trace to Ollama
  - Extracts: error_type, file, line, root_cause
  - Updates AgentState
        │
        ▼
[Fix Agent]  ←── FAISS (past successful fixes)
  - Sends root_cause to Ollama
  - Generates code fix + explanation
  - Saves to PostgreSQL
        │
        ▼
[Validation Agent]
  - Runs pytest on fix (in subprocess)
  - Checks syntax with ast.parse()
  - If valid → mark APPROVED
  - If invalid → retry Fix Agent (max 3x)
        │
        ▼
[Deployment Simulator]
  - Copies fix to /sandbox/ directory
  - Reruns the buggy script
  - Confirms error gone → marks HEALED
        │
        ▼
[PostgreSQL + WebSocket]
  - Saves full execution history
  - Pushes real-time update to React dashboard
