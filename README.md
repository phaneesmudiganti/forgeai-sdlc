# ForgeAI SDLC with Web Dashboard (LangGraph + FastAPI + OpenRouter)

This project implements a multi-role "development crew" that follows an SDLC-like
workflow using LangGraph and OpenRouter-backed open-source models.

Roles:
- Business Analyst
- Software Architect
- Backend Engineer
- Frontend Engineer
- QA Engineer
- Code Reviewer (with loop-back for fixes)
- DevOps Engineer

Features:
- LangGraph-based workflow (explicit nodes and edges)
- Hybrid model usage (FAST_MODEL vs SMART_MODEL)
- Web dashboard using FastAPI + a simple HTML/JS frontend
- Streaming-style execution: the dashboard can poll for step-by-step updates
- Artifacts persisted under an output run directory

## Quick start

1. Create and activate a virtual environment, then install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Ensure OpenRouter is installed and running, and pull at least one small model:

   ```bash
   OpenRouter pull qwen2.5-coder:1.5b
   ```

   Optionally also pull a "smart" model:

   ```bash
   OpenRouter pull deepseek-coder:1.3b
   ```

3. Copy `.env.example` to `.env` and adjust model names as needed.

4. Start the API + dashboard:

   ```bash
   uvicorn src.server.main:app --reload
   ```

5. Open the dashboard in your browser (default):

   - http://localhost:8000

6. Enter the path to a requirements text file and a desired output directory,
   then click "Start Run". The dashboard will show each step as it completes.