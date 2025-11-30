import uuid
import logging
import threading
from pathlib import Path
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.workflow.graph import build_graph, SDLCState
from src.tools.artifacts import write_artifact_files

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Dev Crew SDLC Dashboard")

# In-memory run registry (simple for local use)
RUNS: Dict[str, Dict[str, Any]] = {}

logger.info("main.py - initializing FastAPI application")
logger.debug("main.py - building SDLC workflow graph")
graph = build_graph()
logger.debug("main.py - workflow graph built successfully")

# Serve static frontend
logger.debug("main.py - mounting static files from /static directory")
app.mount("/static", StaticFiles(directory="static"), name="static")

class StartRunRequest(BaseModel):
    requirements_path: str
    output_dir: str

@app.get("/", response_class=HTMLResponse)
async def index():
    """Serve the main dashboard HTML page."""
    logger.debug("index() - GET / request received")
    html_path = Path("static/index.html")
    
    if not html_path.exists():
        logger.error(f"index() - dashboard HTML file not found at {html_path}")
        return HTMLResponse(content="<h1>Dashboard missing</h1>", status_code=500)
    
    try:
        html = html_path.read_text(encoding="utf-8")
        logger.info(f"index() - successfully served dashboard HTML ({len(html)} bytes)")
        return HTMLResponse(content=html)
    except Exception as e:
        logger.error(f"index() - failed to read HTML file: {e}", exc_info=True)
        return HTMLResponse(content="<h1>Error reading dashboard</h1>", status_code=500)

@app.post("/api/run")
async def start_run(payload: StartRunRequest):
    """Start a new SDLC workflow run with provided requirements.
    
    Validates input paths, initializes run state, and starts background workflow execution.
    """
    run_id = str(uuid.uuid4())
    logger.info(
        f"start_run() - new run started with run_id={run_id}, "
        f"requirements_path={payload.requirements_path}, output_dir={payload.output_dir}"
    )

    RUNS[run_id] = {
        "status": "running",
        "steps": [],
        "result": None,
        "error": None,
    }
    logger.debug(f"start_run() - initialized run state for {run_id}")

    def worker():
        """Background worker thread executing the SDLC workflow."""
        logger.debug(f"worker() - thread started for run_id={run_id}")
        
        try:
            # Validate and load requirements file
            req_path = Path(payload.requirements_path)
            if not req_path.exists():
                error_msg = f"Requirements file not found: {req_path}"
                logger.error(f"worker() - {error_msg}")
                raise FileNotFoundError(error_msg)
            
            logger.debug(f"worker() - loading requirements from {req_path}")
            requirements = req_path.read_text(encoding="utf-8")
            logger.info(f"worker() - successfully loaded requirements ({len(requirements)} chars)")

            # Initialize SDLC state
            logger.debug(f"worker() - creating SDLCState with requirements")
            state = SDLCState(requirements=requirements)

            # Stream graph execution step-by-step
            logger.debug(f"worker() - starting graph stream execution")
            step_count = 0
            for update in graph.stream(state):
                step_count += 1
                step_str = str(update)
                RUNS[run_id]["steps"].append(step_str)
                logger.debug(f"worker() - workflow step {step_count} executed: {step_str[:100]}...")

            logger.info(f"worker() - graph stream execution completed with {step_count} steps")

            # === Smart Resume Cache System ===
            import hashlib, json
            # Ensure output folder exists
            output_dir = Path(payload.output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

            # Now safely create the cache folder
            cache_root = output_dir / "_cache"
            cache_root.mkdir(parents=True, exist_ok=True)

            req_hash = hashlib.sha256(requirements.encode("utf-8")).hexdigest()
            cache_file = cache_root / f"{req_hash}.json"

            # If cache exists, skip full workflow and regenerate artifacts only
            if cache_file.exists():
                cached = json.loads(cache_file.read_text(encoding="utf-8"))
                run_output_dir = Path(payload.output_dir) / f"run_{run_id}"

                write_artifact_files(
                    run_output_dir=run_output_dir,
                    backend_code=cached.get("backend_code", ""),
                    frontend_code=cached.get("frontend_code", ""),
                    tests_code=cached.get("qa_results", ""),
                    devops_code=cached.get("devops_output", ""),
                    approved=cached.get("approved", False),
                )

                RUNS[run_id]["steps"].append("Smart resume: Loaded cached outputs, skipped workflow.")
                RUNS[run_id]["result"] = cached | {"output_dir": str(run_output_dir)}
                RUNS[run_id]["status"] = "completed"
                return


            # Final result
            logger.debug(f"worker() - invoking final graph state")
            raw = graph.invoke(state)
            logger.info("worker() - final graph invocation completed")

            # Convert raw dict back to SDLCState

            final_state = SDLCState(
                requirements=raw.get("requirements"),
                ba_output=raw.get("ba_output"),
                architecture=raw.get("architecture"),
                backend_code=raw.get("backend_code"),
                frontend_code=raw.get("frontend_code"),
                qa_results=raw.get("qa_results"),
                review_notes=raw.get("review_notes"),
                devops_output=raw.get("devops_output"),
                approved=raw.get("approved", False),
                meta=raw.get("meta", {})
            )
            logger.debug(f"worker() - final state constructed: approved={final_state.approved}")

            # Write artifacts to filesystem using semantic filenames
            run_output_dir = Path(payload.output_dir) / f"run_{run_id}"
            logger.debug(
                f"worker() - writing artifacts to {run_output_dir}, "
                f"approval_status={final_state.approved}"
            )
            
            try:
                write_artifact_files(
                    run_output_dir=run_output_dir,
                    backend_code=final_state.backend_code or "",
                    frontend_code=final_state.frontend_code or "",
                    tests_code=final_state.qa_results or "",
                    devops_code=final_state.devops_output or "",
                    approved=final_state.approved,
                )
                logger.info(f"worker() - artifacts successfully written to {run_output_dir}")
            except Exception as e:
                logger.error(f"worker() - artifact write failed: {e}", exc_info=True)
                raise

            # Store final results
            RUNS[run_id]["result"] = {
                "requirements": final_state.requirements,
                "ba_output": final_state.ba_output,
                "architecture": final_state.architecture,
                "backend_code": final_state.backend_code,
                "frontend_code": final_state.frontend_code,
                "qa_results": final_state.qa_results,
                "review_notes": final_state.review_notes,
                "devops_output": final_state.devops_output,
                "approved": final_state.approved,
                "output_dir": str(run_output_dir),
            }
            RUNS[run_id]["status"] = "completed"
            # Store successful output for future fast resume
            cache_file.write_text(json.dumps(RUNS[run_id]["result"], indent=2), encoding="utf-8")
            logger.info(f"worker() - run {run_id} completed successfully")
            
        except Exception as e:
            logger.error(f"worker() - workflow execution failed: {e}", exc_info=True)
            RUNS[run_id]["status"] = "error"
            RUNS[run_id]["error"] = str(e)

    # Start background worker thread
    logger.debug(f"start_run() - launching background worker thread for run_id={run_id}")
    threading.Thread(target=worker, daemon=True).start()
    
    logger.info(f"start_run() - returning run_id={run_id} to client")
    return {"run_id": run_id}

@app.get("/api/run/{run_id}")
async def get_run(run_id: str):
    """Retrieve the status and progress of a running SDLC workflow.
    
    Returns current run status, executed steps, result (if completed), and any errors.
    """
    logger.debug(f"get_run() - status check for run_id={run_id}")
    
    run = RUNS.get(run_id)
    if not run:
        logger.warning(f"get_run() - run_id={run_id} not found in registry")
        return JSONResponse(status_code=404, content={"error": "run not found"})
    
    logger.debug(f"get_run() - run status: {run.get('status')}, steps: {len(run.get('steps', []))}")
    return run

@app.get("/api/files/{run_id}")
async def list_files(run_id: str):
    """List artifact files generated by a completed run.
    
    Returns a tree structure of all files and folders in the output directory.
    """
    logger.debug(f"list_files() - file listing request for run_id={run_id}")
    
    run = RUNS.get(run_id)
    result = run.get("result") if run else None
    output_dir = result.get("output_dir") if result else None
    
    if not run or not output_dir:
        logger.warning(f"list_files() - run_id={run_id} not found or has no result artifacts")
        raise HTTPException(status_code=404, detail="Run or artifacts not found")

    root = Path(output_dir)
    logger.debug(f"list_files() - building file tree for {root}")

    def build_tree(path: Path):
        """Recursively build a tree structure of files and directories."""
        children = []
        try:
            for item in sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name.lower())):
                if item.is_file():
                    children.append({
                        "type": "file",
                        "name": item.name,
                        "path": str(item.relative_to(root)).replace('\\', '/')
                    })
                else:
                    children.append({
                        "type": "folder",
                        "name": item.name,
                        "children": build_tree(item)
                    })
        except Exception as e:
            logger.error(f"build_tree() - error traversing {path}: {e}", exc_info=True)
        return children

    tree = build_tree(root)
    logger.info(f"list_files() - successfully built file tree with {len(tree)} top-level items")
    return {"root": root.name, "tree": tree}


@app.get("/api/file/{run_id}")
async def get_file_content(run_id: str, file_path: str):
    """Retrieve the content of a specific artifact file.
    
    Returns the filename and full content of the requested file.
    """
    logger.debug(f"get_file_content() - content request for run_id={run_id}, file_path={file_path}")
    
    run = RUNS.get(run_id)
    result = run.get("result") if run else None
    output_dir = result.get("output_dir") if result else None
    
    if not run or not output_dir:
        logger.warning(f"get_file_content() - run_id={run_id} not found or has no result")
        raise HTTPException(status_code=404, detail="Run not found")

    root = Path(output_dir)
    file = root / file_path
    
    if not file.exists() or not file.is_file():
        logger.warning(f"get_file_content() - file not found at {file}")
        raise HTTPException(status_code=404, detail="File not found")

    try:
        content = file.read_text(encoding="utf-8")
        logger.info(f"get_file_content() - successfully retrieved {file.name} ({len(content)} chars)")
        return {"filename": file.name, "content": content}
    except Exception as e:
        logger.error(f"get_file_content() - failed to read file {file}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to read file")
