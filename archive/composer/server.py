"""
server.py — Interestingness Composer (Part 2)
---------------------------------------------
FastAPI backend for the slider-composer UI. Today (P1D1) this is just a
health endpoint plus the plumbing the next days will hang things on.

Run:
    export ANTHROPIC_API_KEY=sk-ant-...
    uvicorn server:app --reload --port 8000

Then:
    curl http://localhost:8000/health
    # → {"status":"ok","phase":"P1D1","cache_entries":121}
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import asyncio

from fastapi import FastAPI, File, Form, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from pydantic import BaseModel
from typing import Optional

from vlm_client import score_one
import prompt_library
import combiner

# Where on disk things live. Stays consistent with Section 6 of the build plan.
PROJECT_ROOT       = Path(__file__).resolve().parent
IMAGES_DIR         = PROJECT_ROOT / "images"
TEMPLATES_DIR      = PROJECT_ROOT / "templates"
SCORES_CACHE_PATH  = PROJECT_ROOT / "scores_cache.json"
PROMPTS_PATH       = PROJECT_ROOT / "prompts.json"  # written on P1D2

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s: %(message)s")
log = logging.getLogger("composer")

app = FastAPI(
    title="Interestingness Composer",
    description="Real-time interactive composition of personal image interestingness.",
    version="0.1.0-P1D1",
)

# Static mounts — images served from /images/<filename>, templates from /static/.
# (Both directories already exist from the scaffold step.)
if IMAGES_DIR.exists():
    app.mount("/images", StaticFiles(directory=IMAGES_DIR), name="images")
if TEMPLATES_DIR.exists():
    app.mount("/static", StaticFiles(directory=TEMPLATES_DIR), name="static")


# ---------------------------------------------------------------------------
# /health — verifies the server is up and reports a couple of useful counters.
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    cache_entries = 0
    if SCORES_CACHE_PATH.exists():
        try:
            cache_entries = len(json.loads(SCORES_CACHE_PATH.read_text()))
        except json.JSONDecodeError:
            cache_entries = -1  # corrupt cache; useful to see

    image_count = sum(1 for p in IMAGES_DIR.glob("*") if p.is_file()) if IMAGES_DIR.exists() else 0

    prompt_count = len(prompt_library.list_prompts())

    return JSONResponse(
        {
            "status": "ok",
            "phase": "P1D5",
            "cache_entries": cache_entries,
            "image_count": image_count,
            "prompt_count": prompt_count,
        }
    )


# ---------------------------------------------------------------------------
# /prompts — CRUD over the prompt library. Backed by prompt_library.py.
# Each prompt has {id, name, text, n_scored}. n_scored is auto-counted from
# the live cache, so it reflects reality even if scores were written by a
# different process (e.g. CLI tools).
# ---------------------------------------------------------------------------

class NewPrompt(BaseModel):
    name: str
    text: str


@app.get("/prompts")
def get_prompts():
    """All prompts in the library, with up-to-date n_scored counts."""
    return prompt_library.list_prompts()


@app.get("/prompts/{prompt_id}")
def get_one_prompt(prompt_id: str):
    p = prompt_library.get_prompt(prompt_id)
    if p is None:
        raise HTTPException(404, f"No prompt with id {prompt_id!r}")
    return p


@app.post("/prompts", status_code=201)
def post_prompt(payload: NewPrompt):
    """Add a prompt. The id is auto-slugged from `name`."""
    try:
        return prompt_library.add_prompt(payload.name, payload.text)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.delete("/prompts/{prompt_id}")
def delete_prompt(prompt_id: str):
    """Remove from library. Cached scores are preserved on disk."""
    if not prompt_library.remove_prompt(prompt_id):
        raise HTTPException(404, f"No prompt with id {prompt_id!r}")
    return {"removed": prompt_id}


# ---------------------------------------------------------------------------
# /images — list the corpus. Filenames only; the static mount at /images/
# serves the actual bytes. Useful for the eventual /compose UI on Day 5.
# ---------------------------------------------------------------------------

@app.get("/images")
def get_images():
    filenames = prompt_library.list_image_filenames()
    return {"count": len(filenames), "filenames": filenames}


# ---------------------------------------------------------------------------
# /score_all/{prompt_id} — bulk pre-scoring of the corpus on one prompt.
# Long-running (~1 min/prompt at concurrency 8). Runs as a FastAPI
# BackgroundTask; client polls /score_all/status to follow progress.
# ---------------------------------------------------------------------------

# In-memory job table. Module-level so it survives across requests in a single
# uvicorn process. (--reload restarts the process and wipes this — fine, the
# scores are persisted to scores_cache.json anyway.)
_jobs: dict[str, dict] = {}


async def _run_bulk_score(prompt_id: str):
    """Wrapper that updates _jobs[prompt_id] as bulk_score_for_prompt runs."""
    def progress(snapshot: dict):
        _jobs[prompt_id].update(snapshot)
    try:
        await prompt_library.bulk_score_for_prompt(
            prompt_id, concurrency=8, progress_callback=progress
        )
    except Exception as e:
        log.exception("bulk job crashed for %s", prompt_id)
        _jobs[prompt_id]["error"] = f"{type(e).__name__}: {e}"
        _jobs[prompt_id]["completed"] = True


@app.post("/score_all/{prompt_id}", status_code=202)
async def post_score_all(prompt_id: str, background_tasks: BackgroundTasks):
    """Kick off bulk scoring for one prompt. Returns immediately; poll status."""
    if prompt_library.get_prompt(prompt_id) is None:
        raise HTTPException(404, f"No prompt with id {prompt_id!r}")

    # Reject if a job for this prompt is already in flight.
    existing = _jobs.get(prompt_id)
    if existing and not existing.get("completed"):
        raise HTTPException(409, f"A job for {prompt_id!r} is already running")

    # Initial state — populated more fully by the first progress callback.
    _jobs[prompt_id] = {
        "prompt_id": prompt_id,
        "completed": False,
        "scored":    0,
        "to_score":  None,   # filled in once bulk_score has counted
        "started_at": None,
        "error":     None,
    }
    background_tasks.add_task(_run_bulk_score, prompt_id)
    return {"status": "started", "prompt_id": prompt_id}


@app.get("/score_all/status")
def get_all_statuses():
    """All known jobs (running + completed)."""
    return _jobs


@app.get("/score_all/status/{prompt_id}")
def get_status(prompt_id: str):
    if prompt_id not in _jobs:
        raise HTTPException(404, f"No job ever started for {prompt_id!r}")
    return _jobs[prompt_id]


# ---------------------------------------------------------------------------
# /compose/ranking — THE headline endpoint.
#
# Accepts the current slider state, returns the corpus sorted by composed
# score. Pure arithmetic (combiner.compose) — fast enough to run on every
# slider drag (~5ms for 220 images).
# ---------------------------------------------------------------------------

class ComposeRequest(BaseModel):
    weights: dict[str, float]
    limit: Optional[int] = None  # if None, return everything


@app.post("/compose/ranking")
def post_compose_ranking(payload: ComposeRequest):
    """Return the corpus sorted by composed score under the given weights."""
    cache = prompt_library._load_cache()  # ok — same process, same module
    results = combiner.compose(cache, payload.weights)
    if payload.limit is not None:
        results = results[: payload.limit]
    return {
        "count":   len(results),
        "weights": payload.weights,
        "results": results,
    }


# ---------------------------------------------------------------------------
# Dev verification UI (added P1D1 evening — not in the formal plan but cheap).
# /test is a one-image-at-a-time tool: upload JPEG, type a prompt, see a score.
# Replaces the CLI `python vlm_client.py <path> <prompt>` flow during dogfood.
# Will be superseded by /compose on P1D5 but stays for quick smoke-tests.
# ---------------------------------------------------------------------------

@app.get("/test", response_class=HTMLResponse)
def test_page():
    """Serve templates/test.html as-is. Edit the file and refresh — no restart needed."""
    test_html = TEMPLATES_DIR / "test.html"
    if not test_html.exists():
        raise HTTPException(500, f"Missing template: {test_html}")
    return HTMLResponse(test_html.read_text())


@app.get("/scoring", response_class=HTMLResponse)
def scoring_page():
    """Bulk-scoring dashboard. Live progress bars, one row per prompt."""
    p = TEMPLATES_DIR / "scoring.html"
    if not p.exists():
        raise HTTPException(500, f"Missing template: {p}")
    return HTMLResponse(p.read_text())


@app.get("/compose", response_class=HTMLResponse)
def compose_page():
    """The headline UI — slider composer + live image ranking."""
    p = TEMPLATES_DIR / "compose.html"
    if not p.exists():
        raise HTTPException(500, f"Missing template: {p}")
    return HTMLResponse(p.read_text())


@app.post("/score_one")
async def score_one_endpoint(
    image: UploadFile = File(...),
    prompt_text: str = Form(...),
):
    """Score one uploaded image on one prompt. Returns the float + a bit of metadata."""
    if not prompt_text.strip():
        raise HTTPException(400, "prompt_text cannot be empty")

    jpeg_bytes = await image.read()
    if not jpeg_bytes:
        raise HTTPException(400, "Uploaded image is empty")

    try:
        import time
        t0 = time.perf_counter()
        score = score_one(jpeg_bytes, prompt_text)
        latency_ms = round((time.perf_counter() - t0) * 1000, 1)
    except RuntimeError as e:
        # Most common: ANTHROPIC_API_KEY not set.
        raise HTTPException(500, str(e))
    except Exception as e:
        log.exception("score_one failed")
        raise HTTPException(500, f"{type(e).__name__}: {e}")

    return {
        "score": score,
        "latency_ms": latency_ms,
        "prompt_text": prompt_text,
        "filename": image.filename,
        "size_bytes": len(jpeg_bytes),
    }


# ---------------------------------------------------------------------------
# Stubs to be filled in over the next days. Keeping them as TODOs in this
# one file so the shape of the API is visible up front.
# ---------------------------------------------------------------------------

# P1D2 — POST /prompts, GET /prompts, DELETE /prompts/{id} (prompt_library.py)
# P1D3 — POST /score_all/{prompt_id} (background-task bulk scoring)
# P1D4 — GET /compose/ranking?weights=...  (combiner.compose)
# P1D5 — GET /compose (HTML page with the three-panel UI)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
