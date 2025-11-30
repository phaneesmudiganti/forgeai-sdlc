# ForgeAI SDLC Web UI

> LLM-driven SDLC workflow that generates, reviews, and writes software artifacts from natural-language requirements.

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![Status](https://img.shields.io/badge/status-experimental-orange)]()
[![License](https://img.shields.io/badge/license-Unspecified-lightgrey)]()

<!-- Note: build/CI badges are intentionally not shown because no CI config was detected. Add a GitHub Actions workflow to enable status badges. -->

## Table of Contents

- [Project Overview](#project-overview)
- [Elevator Pitch](#elevator-pitch)
- [Features](#features)
- [Architecture & Design Overview](#architecture--design-overview)
- [Folder Structure](#folder-structure)
- [Installation](#installation)
- [Configuration / Environment Variables](#configuration--environment-variables)
- [Usage](#usage)
  - [Run Locally (development)](#run-locally-development)
  - [API Endpoints](#api-endpoints)
  - [Example Run (curl)](#example-run-curl)
- [Examples & Output Artifacts](#examples--output-artifacts)
- [Deployment Guidance](#deployment-guidance)
- [Testing](#testing)
- [Troubleshooting & Common Issues](#troubleshooting--common-issues)
- [Roadmap & Future Directions](#roadmap--future-directions)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgments](#acknowledgments)

---

## Project Overview

ForgeAI SDLC Web UI is a small FastAPI application that orchestrates an LLM-driven software development lifecycle (SDLC) pipeline. Given a plain-text requirements file, the system runs through roles (Business Analyst → Architect → Backend → Frontend → QA → Review → DevOps), generates code/test/infra artifacts and writes them using semantic filenames.

The project demonstrates:
- LLM orchestration for software engineering tasks
- Artifact extraction from LLM outputs (via `# file:` markers)
- A lightweight local web UI / API to manage runs and inspect results

---

## Elevator Pitch

This project provides a developer-facing tool to produce end-to-end software artifacts from human requirements using LLMs. It automates specification refinement, architecture design, backend/frontend code generation, testing, code review, and DevOps scaffold generation — then writes artifacts to an output directory with sensible draft/fix/final naming.

---

## Features

- Orchestrates multi-step SDLC pipeline using LLMs (fast/smart models).
- Node-based workflow (BA → Architect → Backend → Frontend → QA → Review → DevOps).
- Artifact parsing from LLM outputs using `# file: <path>` markers.
- Semantic artifact naming ─ draft/fix/final names based on approval.
- FastAPI HTTP API to start runs, poll status, and inspect generated files.
- Modular workflow implementation for testability and extension.

---

## Architecture & Design Overview

High-level flow:
1. A run is started with a natural-language requirements file path.
2. The `StateGraph` (via `langgraph`) drives ordered node execution.
3. Nodes are LLM-backed functions. There are two LLM types:
   - `fast_llm` — for quick/smaller tasks (e.g., BA, QA)
   - `smart_llm` — for heavier reasoning (e.g., architecture, backend code)
4. Node outputs are stored in an `SDLCState` and later parsed into artifact files.
5. A review step returns a JSON status (`APPROVED` / `CHANGES_REQUIRED`) that decides branching to DevOps or back to Backend for fixes.
6. Artifacts are written to a run output directory with semantic filenames.

Design patterns & notable choices:
- Modular nodes in `src/workflow/nodes/` — each node has a single responsibility and is testable in isolation.
- `state.py` centralizes state shape (`SDLCState`) and conversion helpers.
- `tools/artifacts.py` contains artifact parsing and safe file-writing semantics.
- FastAPI provides the minimal web API + static UI served from `static/index.html`.

Technologies:
- Python 3.10+ (uses `|` union types)
- FastAPI + Uvicorn
- LangChain/ChatOpenAI adapter (via `langchain_openai` import in `src/config.py`)
- `langgraph` for state-graph orchestration
- `python-dotenv` for local configuration
- Core modules are pure Python for easy extension

---

## Folder Structure

Root (key files)
- `README.md` — this file
- `requirements.txt` — Python dependencies
- `static/index.html` — small web UI frontend

Source (`src/`)
- `src/server/main.py` — FastAPI app, run management, API endpoints.
- `src/config.py` — LLM model selection and creation helpers; reads environment variables.
- `src/tools/artifacts.py` — parse `# file:` blocks; semantic file naming; writes artifacts.
- `src/workflow/` — modular workflow implementation:
  - `state.py` — `SDLCState` dataclass and helpers.
  - `llms.py` — LLM instantiation wrapper (fast & smart).
  - `utils.py` — helpers (safe state attribute extraction, path sanitization).
  - `graph_builder.py` — builds the `StateGraph` and contains `review_decision`.
  - `graph.py` — compatibility shim re-exporting `build_graph` and `SDLCState`.
  - `nodes/` — each node implemented as a small module:
    - `business_analyst.py`, `architect.py`, `backend.py`, `frontend.py`, `qa.py`, `review.py`, `devops.py`

---

## Installation

Prerequisites
- Python 3.10 or newer is required.
- Git (optional)
- An OpenAI-compatible LLM client or equivalent adapter expected by `langchain_openai.ChatOpenAI`. The repository uses `langchain_openai` in `src/config.py` — configure credentials accordingly.

Install dependencies:
```bash
python -m venv .venv
. .venv/Scripts/activate      # Windows PowerShell
pip install -r requirements.txt
```

(If you use a different OS/shell substitute activation command accordingly.)

---

## Configuration / Environment Variables

The project reads .env variables via `python-dotenv`. Create a `.env` in the project root or set these environment variables directly.

Key variables (see `src/config.py`):
- `FAST_MODEL` — model name used by the fast LLM (default: `qwen2.5-coder:1.5b` in code).
- `SMART_MODEL` — model name used by smart LLM (defaults to `FAST_MODEL` if not set).
- `LLM_TEMPERATURE` — float controlling LLM temperature (default: `0.2`).

Example `.env`:
```
FAST_MODEL=qwen2.5-coder:1.5b
SMART_MODEL=gpt-4o
LLM_TEMPERATURE=0.2
OPENAI_API_KEY=sk-...         # if required by your LLM adapter
```

Note: the project uses an adapter (`langchain_openai.ChatOpenAI`) — ensure your environment variables and credentials match the adapter you're using.

---

## Usage

### Run Locally (development)

Start the FastAPI server with Uvicorn from the repository root:
```powershell
. .venv/Scripts/activate
uvicorn src.server.main:app --reload --port 8000
```

- The web UI is served at `http://127.0.0.1:8000/` (static `index.html`).
- API endpoints are available under `/api/...`.

### API Endpoints

- `POST /api/run` — start a new run  
  Request JSON:
  ```json
  {
    "requirements_path": "C:\\path\\to\\requirements.txt",
    "output_dir": "C:\\path\\to\\output_root"
  }
  ```
  Response: `{ "run_id": "<uuid>" }`

- `GET /api/run/{run_id}` — get run status, steps log, and results if completed.

- `GET /api/files/{run_id}` — list artifact files for a completed run.

- `GET /api/file/{run_id}?file_path=<relative_path>` — retrieve a specific artifact file content.

### Example Run (curl)

Start a run (replace paths and host/port if needed):
```powershell
curl -X POST "http://127.0.0.1:8000/api/run" -H "Content-Type: application/json" -d "{\"requirements_path\":\"C:\\\\tmp\\\\requirements.txt\",\"output_dir\":\"C:\\\\tmp\\\\out\"}"
```

Poll status:
```powershell
curl "http://127.0.0.1:8000/api/run/<run_id>"
```

List files:
```powershell
curl "http://127.0.0.1:8000/api/files/<run_id>"
```

Retrieve file:
```powershell
curl "http://127.0.0.1:8000/api/file/<run_id>?file_path=backend/main.final.py"
```

---

## Examples & Output Artifacts

- Nodes produce outputs that include `# file: path` markers. `src/tools/artifacts.py` extracts these blocks and writes files under the run output folder.
- Semantic filenames:
  - If `approved`: files are named `stem.final<suffix>` (e.g., `main.final.py`).
  - If not approved and no draft exists: `stem.draft<suffix>`.
  - Subsequent fixes use `stem.fixN<suffix>` with incremented N.

Artifacts are written inside `output_root/run_<run_id>/...` so multiple runs do not clash.

---

## Deployment Guidance

The app is a standard FastAPI service and can be containerized easily.

Docker (recommended minimal pattern):
- Create a Dockerfile that installs dependencies from `requirements.txt`, copies source, and runs Uvicorn. Ensure secrets (LLM keys) are provided via environment variables or secret management.

Example Dockerfile sketch:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "src.server.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

CI/CD:
- No CI configured in this repository. Recommended:
  - GitHub Actions to run linters, tests, and build a container image.
  - Use environment secrets for LLM credentials.
  - Add integration tests that mock LLMs or use a test LLM endpoint.

Platform specifics:
- For cloud deployment, use a container orchestrator (ECS, GKE, AKS) or serverless containers.
- If using GPUs or special LLM hosting, attach the appropriate network/access.

---

## Testing

This repository does not ship formal unit tests yet. Recommended tests to add:
- Unit tests for `src/tools/artifacts.py`:
  - `parse_file_blocks()` edge cases (CRLF, missing closing fences, multiple markers).
  - `_next_semantic_name()` behavior when drafts/fixes/final exist.
  - Path sanitization to prevent directory traversal.
- Node-level tests:
  - Mock `fast_llm` and `smart_llm` to exercise each node function.
- Integration tests:
  - Start a TestClient against FastAPI and simulate a run while patching LLM calls to deterministic outputs.

Run (if tests added):
```bash
pip install pytest
pytest
```

---

## Troubleshooting & Common Issues

- Attribute errors on final state (e.g., `'AddableValuesDict' object has no attribute 'approved'`):  
  The workflow has nodes returning mapping-like objects. The code converts or safely extracts attributes; if you see this error, ensure your `langgraph`/graph node returns a type compatible with `SDLCState` or check the compatibility shim in `src/workflow/graph.py` and `src/workflow/state.py`.

- LLM instantiation failures:
  - Ensure credentials/environment variables required by your LLM adapter are set (for `langchain_openai` / `ChatOpenAI` or other adapters).
  - Check `src/config.py` for `FAST_MODEL`, `SMART_MODEL`, and `LLM_TEMPERATURE`.

- Path traversal or unsafe writes:
  - The artifact writer expects `# file:` markers to contain safe relative paths. If you expose the service to untrusted inputs, audit `src/tools/artifacts.py` and consider adding stricter sanitization and a whitelist for extensions.

- Threading & concurrency:
  - The application manages run state in a module-level `RUNS` dict. In high concurrency scenarios, consider protecting modifications with a lock or migrating to a proper background task system and persistent storage.

If you encounter other errors, inspect logs (the application logs at DEBUG level). The FastAPI log lines include function names for quick tracing.

---

## Roadmap & Future Directions

(Inferred / recommended items based on code)
- Add robust unit & integration tests, especially for artifact parsing and node behavior.
- Harden security: path sanitization, credential handling, token limits, LLM output validation.
- Add CI (GitHub Actions) for linting, testing, and container build.
- Add multi-run persistence (DB) instead of in-memory `RUNS`.
- Allow pluggable LLM adapters and rate-limiting.
- Add a clearer frontend UI for interactive review and approvals.

---

## Contributing

Contributions are welcome. Suggested workflow:
1. Fork the repository.
2. Create a branch per feature/fix: `feature/<short-name>` or `fix/<ticket>`.
3. Implement changes and add tests.
4. Ensure `black`/`ruff`/`flake8` style and run tests locally.
5. Open a PR with a clear description and link to issues.

Coding standards & style:
- Keep functions short and single-responsibility.
- Use type annotations where helpful (project targets Python 3.10+).
- Use the modular structure under `src/workflow/` to place node logic.

PR reviewers will expect:
- Tests for new logic (especially around artifact parsing).
- No leaking of secrets in PRs.
- Clear changelog entry or PR description.

---

## License

No license file was detected in the repository. If you intend to open-source the project, add an explicit license (e.g., MIT, Apache-2.0). Until a license is added, the repository is effectively "All rights reserved".

---

## Acknowledgments

- The project integrates with LangChain/LangGraph for workflow orchestration.
- Pattern inspired by agentic development workflows and rapid LLM-driven prototyping.