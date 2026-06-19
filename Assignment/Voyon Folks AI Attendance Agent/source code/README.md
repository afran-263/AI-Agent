# Voyon Attendance Agent

An AI-powered attendance assistant for the **Voyon Folks HRMS** platform.
Built with **Python**, **FastAPI**, **LangGraph**, and **Azure OpenAI** — it connects
directly to the existing Voyon HRMS REST APIs and answers attendance questions in
natural language through a chat UI.

---

## Features

| Capability | Example query | Result |
|------------|---------------|--------|
| **Who is present today?** | "Who is present today?" | Table of present employees (ID + Name) |
| **Who is absent today?** | "Who didn't come to office on 2026-06-15?" | Table of absent employees (ID + Name) |
| **Team attendance summary** | "Show attendance summary for today" | Present / absent / leave / holiday counts |
| **Full team roster** | "Get the list of employees" | Every team member (ID + Name) |
| **Monthly attendance history** | "Show attendance history for Greeshma this month" | Date \| Status table with summary counts |
| **Month-to-date summary** | "Show my attendance summary for this month till now" | Status \| Days table, limited to today |
| **Employee attendance details** | "Show attendance details for Kanchana today" | Status, check-in/out, worked hours |
| **My attendance today** | "What is my attendance today?" | Personal check-in / check-out status |
| **Employee search** | "Find employee named Sarah" | Matching employees (ID + Name) |
| **Scope & error handling** | "What is my salary?" | Politely declines; handles API/auth failures |

Conversational follow-ups are supported via session memory — e.g. after discussing
an employee you can ask *"show her history this month"*.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.11+ |
| Web Framework | FastAPI |
| Agent Orchestration | **LangGraph** 0.2+ |
| LLM | Azure OpenAI (GPT-4 / GPT-4.1) |
| HRMS Integration | httpx (async REST client) |
| Frontend | Jinja2 templates + Vanilla JS |
| Session Management | itsdangerous signed cookies |

---

## Project Structure

```
voyonattenagent/
├── src/
│   ├── main.py                    # FastAPI entry point + root/health routes
│   ├── config.py                  # Settings loaded from .env
│   ├── agent/
│   │   ├── graph.py               # LangGraph workflow + run_agent()
│   │   ├── nodes.py               # Intent, params, enrichment, routing, response
│   │   ├── tools.py               # HRMS attendance tools + response formatters
│   │   ├── state.py               # Agent state schema (TypedDict)
│   │   └── prompt_loader.py       # Loads systemprompt.txt
│   ├── api/
│   │   └── hrms_client.py         # Async HRMS REST client
│   ├── models/
│   │   └── schemas.py             # Pydantic request/response models
│   ├── routers/
│   │   ├── auth_router.py         # Login / logout + session store
│   │   └── chat_router.py         # /api/chat, /api/me endpoints
│   └── templates/
│       ├── login.html             # Login page
│       └── index.html             # Main chat UI
├── scripts/
│   └── generate_eval_report.py    # Builds structured evaluation reports
├── tests/
│   ├── test_tools.py              # Unit tests (tools, formatters, routing)
│   ├── test_evaluation_dataset.py # Dataset-driven routing & pipeline tests
│   ├── eval_helpers.py            # Dataset loaders, matchers, mocks
│   ├── eval_runner.py             # Shared evaluation execution helpers
│   └── conftest.py                # Pytest markers and CLI options
├── docs/
│   ├── architecture_diagram.md
│   ├── agent_design_document.md
│   ├── api_mapping_document.md
│   ├── evaluation_dataset.json    # 22 evaluation scenarios
│   ├── evaluation_report.json     # Generated report (JSON)
│   ├── evaluation_report.md       # Generated report (Markdown)
│   └── test_results.md
├── systemprompt.txt               # LLM system prompt
├── requirements.txt               # Python dependencies
├── pytest.ini                     # Pytest config (markers, asyncio mode)
└── .env.example                   # Environment variable template
```

---

## Quick Start

### Prerequisites

- Python 3.11+
- Access to a Voyon HRMS instance
- Azure OpenAI resource (GPT-4 / GPT-4.1 deployment)

### 1. Create a virtual environment

```powershell
cd voyonattenagent
python -m venv .venv
```

### 2. Install dependencies

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 3. Configure environment

```powershell
copy .env.example .env
# Edit .env with your HRMS URL and Azure OpenAI credentials
```

### 4. Start the server

```powershell
.\.venv\Scripts\python.exe -m uvicorn src.main:app --host 0.0.0.0 --port 8080 --reload
```

Open **http://localhost:8080** and sign in with your HRMS credentials.

---

## Testing

Automated tests read scenarios from `docs/evaluation_dataset.json`. The default tier
runs entirely offline (mocked LLM + HRMS); live tiers require credentials in `.env`.

```powershell
# Default tier (no API keys): unit tests + routing + mocked pipeline
.\.venv\Scripts\python.exe -m pytest tests/ -v
# → 127 passed, 45 skipped (live tiers skipped without credentials)

# Structured report (input, expected vs actual intent/tools, answer) — JSON + Markdown
.\.venv\Scripts\python.exe scripts/generate_eval_report.py
# → docs/evaluation_report.json
# → docs/evaluation_report.md

# Live Azure OpenAI intent / parameter checks (needs Azure credentials in .env)
.\.venv\Scripts\python.exe -m pytest tests/test_evaluation_dataset.py -v --run-llm

# Live HRMS end-to-end (set EVAL_HRMS_USERNAME / EVAL_HRMS_PASSWORD in .env)
.\.venv\Scripts\python.exe -m pytest tests/test_evaluation_dataset.py -v --run-live-hrms
```

---

## Configuration (`.env`)

| Variable | Description | Default |
|----------|-------------|---------|
| `HRMS_BASE_URL` | Voyon HRMS server URL | `https://localhost:44360` |
| `HRMS_LOGIN_PATH` | HRMS login endpoint path | `/m/api/Login/LoginUser` |
| `HRMS_SSL_VERIFY` | Verify HRMS SSL certificate | `false` |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint URL | — |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI API key | — |
| `AZURE_OPENAI_DEPLOYMENT` | Deployment name | `gpt-4.1` |
| `AZURE_OPENAI_API_VERSION` | API version | `2024-08-01-preview` |
| `SYSTEM_PROMPT_FILE` | Path to system prompt | `systemprompt.txt` |
| `APP_SECRET_KEY` | Cookie signing secret | *(change in production)* |
| `APP_HOST` | Bind address | `0.0.0.0` |
| `APP_PORT` | Server port | `8080` |
| `APP_DEBUG` | Enable hot reload | `false` |
| `EVAL_HRMS_USERNAME` | HRMS login for live eval tests (optional) | — |
| `EVAL_HRMS_PASSWORD` | HRMS password for live eval tests (optional) | — |

---

## LangGraph Workflow

```
User Query
    │
    ▼
Intent Detection ───────► present_query / absent_query / summary_query /
    │                      team_list_query / history_query / employee_detail /
    │                      my_attendance / search_employee / unclear / out_of_scope
    ▼
Parameter Extraction ───► employee name/ID, date, month, year
    │
    ▼
Context Enrichment ─────► resolves follow-up references from session memory,
    │                      applies phrase-based intent overrides
    ▼
Tool Selection
    │
    ├── Direct Tools ────► deterministic single-tool execution (fast path)
    │                       for the common, unambiguous intents
    └── Agent (ReAct) ◄──► LLM picks & calls tools in a loop for the rest
    │
    ▼
Response Generation ────► deterministic formatters (tables / plain text) where
    │                      possible, else Azure OpenAI formats the API data
    ▼
Final Response
```

### Attendance Tools (`src/agent/tools.py`)

| Tool | HRMS API |
|------|----------|
| `get_present_employees` | `/m/api/Attendance/team-attendance` |
| `get_absent_employees` | `/m/api/Attendance/team-attendance` |
| `get_attendance_summary` | `/m/api/Attendance/team-attendance` |
| `get_team_employee_list` | `/m/api/Attendance/team-attendance` |
| `get_attendance_history` | `/m/api/Attendance/MonthlyAttendance` (+ day-by-day fallback) |
| `get_my_attendance_today` | `/m/api/Attendance/AttendanceBasedOnDate` |
| `get_employee_attendance_details` | `/m/api/Employee/search-employees` + `AttendanceBasedOnDate` |
| `search_employee` | `/m/api/Employee/search-employees` |

> Authentication (the JWT token and employee ID) is injected into every tool from
> the authenticated session — never taken from model arguments — to prevent
> prompt-injection from accessing another user's data.

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Redirect to chat (or login if unauthenticated) |
| `GET` | `/login` | Login page |
| `POST` | `/login` | Submit credentials |
| `POST` | `/logout` | Sign out |
| `POST` | `/api/chat` | Send a message to the agent |
| `GET` | `/api/me` | Current authenticated user info |
| `GET` | `/health` | Service health check |

---

## Documentation

| Document | Path |
|----------|------|
| Architecture Diagram | `docs/architecture_diagram.md` |
| Agent Design Document | `docs/agent_design_document.md` |
| API Mapping Document | `docs/api_mapping_document.md` |
| Evaluation Dataset | `docs/evaluation_dataset.json` |
| Evaluation Report (generated) | `docs/evaluation_report.json`, `docs/evaluation_report.md` |
| Test Results | `docs/test_results.md` |
