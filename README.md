# AI Multi-Agent Self-Healing DevOps System

> B.Tech Major Project — Autonomous infrastructure that detects errors, analyzes root causes, generates fixes, validates, and deploys — without human intervention.

## Overview

A production-grade self-healing pipeline where AI agents collaborate to resolve application failures in under 60 seconds.

```
app.log → Monitor → Analysis → Fix → Validation → Deploy → HEALED
```

## Tech Stack

|Layer         |Technologies                                          |
|--------------|------------------------------------------------------|
|Backend       |FastAPI, LangGraph, LangChain, SQLAlchemy, Uvicorn    |
|AI/LLM        |Ollama (llama3 / codellama), FAISS                    |
|Infrastructure|PostgreSQL (Supabase), Redis (Upstash), Docker Compose|
|Frontend      |React.js, WebSocket                                   |
|Deployment    |Render, Vercel, Supabase, Upstash, Ngrok              |

All technologies are **100% free and open-source**.

## Architecture

```
┌─────────────────────────────────────────────┐
│  Buggy Flask App  →  app.log                │
├─────────────────────────────────────────────┤
│  Monitor Agent  →  Redis Queue              │
├─────────────────────────────────────────────┤
│  LangGraph Orchestrator  (FastAPI)          │
├─────────────────────────────────────────────┤
│  Analysis → Fix → Validation → Deploy       │
├─────────────────────────────────────────────┤
│  PostgreSQL  |  FAISS  |  Redis             │
└─────────────────────────────────────────────┘
```

## Agents

|Agent         |Role                                                                          |
|--------------|------------------------------------------------------------------------------|
|**Monitor**   |Tails `app.log` every 5s, detects errors via regex, pushes to Redis           |
|**Analysis**  |Calls Ollama to extract error type, file, line, root cause, severity          |
|**Fix**       |Calls Ollama to generate `fixed_code` with FAISS context from past fixes      |
|**Validation**|Syntax check (`ast.parse`) + pytest subprocess (30s timeout)                  |
|**Deploy**    |Copies fix to `/sandbox/`, verifies, embeds in FAISS, broadcasts via WebSocket|

## Setup

### Prerequisites

- Python 3.10+
- Docker + Docker Compose
- [Ollama](https://ollama.ai) installed

### 1. Clone & Install

```bash
git clone <repo-url>
cd ai-self-healing-devops
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Pull LLM Model (~4.7GB)

```bash
ollama pull llama3
# or for faster CPU-only machines:
ollama pull mistral
```

### 3. Configure Environment

```bash
cp .env.example .env
```

Edit `.env`:

```env
DATABASE_URL=postgresql+asyncpg://user:pass@host/dbname
REDIS_URL=redis://localhost:6379
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
```

### 4. Run with Docker Compose

```bash
docker compose up --build
```

Or run services individually:

```bash
# Terminal 1 — FastAPI backend
uvicorn main:app --reload

# Terminal 2 — Monitor Agent
python agents/monitor_agent.py

# Terminal 3 — React dashboard
cd frontend && npm install && npm start
```

### 5. Trigger a Bug (Demo)

```bash
curl http://localhost:5000/divide?a=10&b=0
```

Watch the dashboard at `http://localhost:3000` as the pipeline auto-heals.

## Database Schema

|Table              |Purpose                                         |
|-------------------|------------------------------------------------|
|`logs`             |Raw log entries from the buggy app              |
|`detected_errors`  |Parsed errors with severity and lifecycle status|
|`fix_suggestions`  |All fix attempts (including retries)            |
|`agent_outputs`    |Full audit trail per agent invocation           |
|`execution_history`|Summary of each complete heal cycle             |

## Cloud Deployment

|Service          |Provider                        |Notes                             |
|-----------------|--------------------------------|----------------------------------|
|Backend (FastAPI)|[Render](https://render.com)    |Free tier, auto-deploy from GitHub|
|Frontend (React) |[Vercel](https://vercel.com)    |Set `REACT_APP_API_URL` env var   |
|PostgreSQL       |[Supabase](https://supabase.com)|Free 500MB                        |
|Redis            |[Upstash](https://upstash.com)  |10k commands/day free             |
|Ollama (demo)    |Ngrok tunnel                    |`ngrok http 11434`                |

## Project Status

**Current Phase: Phase 1 — Setup & Foundation** (April 2026)

|Phase                                 |Status       |
|--------------------------------------|-------------|
|Phase 1: Setup & Foundation           |🔄 In Progress|
|Phase 2: Core Agent Pipeline          |⏳ Upcoming   |
|Phase 3: Memory, Robustness & Frontend|⏳ Upcoming   |
|Phase 4: Deployment & Polish          |⏳ Upcoming   |

## Milestones

|Milestone             |Target|Deliverable                                   |
|----------------------|------|----------------------------------------------|
|M1: Foundation        |Week 1|Folder structure, buggy app, logs, Ollama     |
|M2: MVP Pipeline      |Week 2|End-to-end heal for `ZeroDivisionError`       |
|M3: Multi-bug + Memory|Week 3|All bug types, FAISS, retry logic, PostgreSQL |
|M4: Full System + UI  |Week 4|React dashboard, Docker, deployed on free tier|

## Risks

|Risk                    |Mitigation                                             |
|------------------------|-------------------------------------------------------|
|Ollama slow on CPU      |Use `mistral`; set `max_tokens=512`                    |
|LLM returns invalid JSON|`try/except` + strip markdown fences + retry           |
|Validation too strict   |Skip pytest if confidence > 0.8 and no test file exists|
|Live demo failure       |Pre-record screen capture; Docker Compose fallback     |

## License

Academic project — B.Tech Major Project, April 2026.