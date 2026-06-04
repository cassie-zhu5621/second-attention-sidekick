"""
prompt_library.py — manage the user's prompt vocabulary + lazy VLM scoring.
---------------------------------------------------------------------------
Backs `prompts.json` (the vocabulary) and `scores_cache.json` (per-(image,
prompt) scores). Both files persist on disk and survive restarts.

Public API:
    list_prompts()                              -> list[Prompt]
    get_prompt(prompt_id)                       -> Prompt | None
    add_prompt(name, text)                      -> Prompt              (POST  /prompts)
    remove_prompt(prompt_id)                    -> bool                (DELETE /prompts/{id})
    score_image_on_prompt(filename, prompt_id)  -> float               (cache-aware VLM call)
    list_image_filenames()                      -> list[str]
    get_score(filename, prompt_id)              -> float | None        (cache-only, no VLM call)

Design choices:
- prompt ids are slugified from the name on add — "Frame within frame" → "frame_within_frame".
  Slugs are unique; collisions append "_2", "_3", etc.
- Removing a prompt drops it from the library but PRESERVES its scores in
  scores_cache.json. Re-adding the same prompt name reuses cached scores.
  (This is why ids are name-derived rather than UUIDs — predictable re-use.)
- All disk writes are atomic (tmpfile + rename) so a Ctrl-C mid-write
  doesn't corrupt the JSON.
- The store keeps `n_scored` updated as new scores are written so the UI
  can show "Tension is scored on 187/200 images" without re-reading the cache.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
import threading
import time
from pathlib import Path
from typing import Callable, TypedDict

from vlm_client import score_one

log = logging.getLogger("prompt-library")

# ---------------------------------------------------------------------------
# Paths — anchored to the project root regardless of where the server is run from.
# ---------------------------------------------------------------------------

PROJECT_ROOT      = Path(__file__).resolve().parent
PROMPTS_PATH      = PROJECT_ROOT / "prompts.json"
SCORES_CACHE_PATH = PROJECT_ROOT / "scores_cache.json"
IMAGES_DIR        = PROJECT_ROOT / "images"

# A single lock serializes all file writes. Composer is single-user so this
# is plenty; if we ever need multi-tenant, swap for per-file locks.
_WRITE_LOCK = threading.Lock()


class Prompt(TypedDict):
    id: str
    name: str
    text: str
    n_scored: int


# ---------------------------------------------------------------------------
# Low-level: load / save / slug
# ---------------------------------------------------------------------------

def _load_prompts() -> list[Prompt]:
    if not PROMPTS_PATH.exists():
        return []
    return json.loads(PROMPTS_PATH.read_text())


def _save_prompts(prompts: list[Prompt]) -> None:
    """Atomic write — tmpfile + rename. Crash-safe."""
    tmp = PROMPTS_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(prompts, indent=2))
    tmp.replace(PROMPTS_PATH)


def _load_cache() -> dict[str, dict[str, float]]:
    if not SCORES_CACHE_PATH.exists():
        return {}
    return json.loads(SCORES_CACHE_PATH.read_text())


def _save_cache(cache: dict[str, dict[str, float]]) -> None:
    tmp = SCORES_CACHE_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(cache, indent=2))
    tmp.replace(SCORES_CACHE_PATH)


_SLUG_RE = re.compile(r"[^a-z0-9]+")


def _slugify(name: str) -> str:
    """'Frame within Frame!' → 'frame_within_frame'."""
    s = _SLUG_RE.sub("_", name.lower()).strip("_")
    return s or "prompt"


def _unique_id(base: str, existing: set[str]) -> str:
    if base not in existing:
        return base
    n = 2
    while f"{base}_{n}" in existing:
        n += 1
    return f"{base}_{n}"


def _count_cached(prompt_id: str, cache: dict[str, dict[str, float]] | None = None) -> int:
    """How many images in the cache have a score for this prompt."""
    if cache is None:
        cache = _load_cache()
    return sum(1 for img_scores in cache.values() if prompt_id in img_scores)


# ---------------------------------------------------------------------------
# Public: prompt CRUD
# ---------------------------------------------------------------------------

def list_prompts() -> list[Prompt]:
    """Return all prompts, with `n_scored` refreshed against the live cache."""
    prompts = _load_prompts()
    cache = _load_cache()
    for p in prompts:
        p["n_scored"] = _count_cached(p["id"], cache)
    return prompts


def get_prompt(prompt_id: str) -> Prompt | None:
    for p in list_prompts():
        if p["id"] == prompt_id:
            return p
    return None


def add_prompt(name: str, text: str) -> Prompt:
    """Create a new prompt. Returns it. Raises ValueError on empty input."""
    if not name.strip():
        raise ValueError("Prompt name cannot be empty")
    if not text.strip():
        raise ValueError("Prompt text cannot be empty")

    with _WRITE_LOCK:
        prompts = _load_prompts()
        existing_ids = {p["id"] for p in prompts}
        new_id = _unique_id(_slugify(name), existing_ids)

        new_prompt: Prompt = {
            "id":       new_id,
            "name":     name.strip(),
            "text":     text.strip(),
            "n_scored": _count_cached(new_id),  # > 0 only if re-adding a previously-removed prompt
        }
        prompts.append(new_prompt)
        _save_prompts(prompts)

    log.info("added prompt id=%s name=%r", new_id, name)
    return new_prompt


def remove_prompt(prompt_id: str) -> bool:
    """Drop a prompt from the library. Scores in cache are preserved."""
    with _WRITE_LOCK:
        prompts = _load_prompts()
        before = len(prompts)
        prompts = [p for p in prompts if p["id"] != prompt_id]
        if len(prompts) == before:
            return False
        _save_prompts(prompts)

    log.info("removed prompt id=%s (cache preserved)", prompt_id)
    return True


# ---------------------------------------------------------------------------
# Public: image listing
# ---------------------------------------------------------------------------

_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def list_image_filenames() -> list[str]:
    """All image filenames in images/, sorted. Used by the bulk-scoring endpoint."""
    if not IMAGES_DIR.exists():
        return []
    return sorted(
        p.name for p in IMAGES_DIR.iterdir()
        if p.is_file() and p.suffix.lower() in _IMAGE_EXTS
    )


# ---------------------------------------------------------------------------
# Public: cache-aware scoring
# ---------------------------------------------------------------------------

def get_score(filename: str, prompt_id: str) -> float | None:
    """Cached score if present, else None. Does NOT call the VLM."""
    return _load_cache().get(filename, {}).get(prompt_id)


def score_image_on_prompt(filename: str, prompt_id: str) -> float:
    """Return the score, calling the VLM only on a cache miss.

    Raises:
        FileNotFoundError if the image isn't in images/.
        KeyError if the prompt_id isn't in the library.
    """
    cached = get_score(filename, prompt_id)
    if cached is not None:
        return cached

    prompt = get_prompt(prompt_id)
    if prompt is None:
        raise KeyError(f"Unknown prompt_id: {prompt_id}")

    image_path = IMAGES_DIR / filename
    if not image_path.exists():
        raise FileNotFoundError(f"No such image: {image_path}")

    jpeg_bytes = image_path.read_bytes()
    score = score_one(jpeg_bytes, prompt["text"])

    # Persist the new score. Re-read the cache inside the lock so we don't
    # blow away scores written by a concurrent /score_all batch.
    with _WRITE_LOCK:
        cache = _load_cache()
        cache.setdefault(filename, {})[prompt_id] = score
        _save_cache(cache)

    log.debug("scored %s on %s → %.2f (cache miss)", filename, prompt_id, score)
    return score


# ---------------------------------------------------------------------------
# Bulk scoring — concurrent VLM calls with batched cache flush
# ---------------------------------------------------------------------------

async def bulk_score_for_prompt(
    prompt_id: str,
    concurrency: int = 8,
    progress_callback: Callable[[dict], None] | None = None,
) -> dict:
    """Score every uncached image in the corpus on one prompt, in parallel.

    Cache semantics:
      - Images already scored on this prompt are skipped (free).
      - New scores are accumulated in memory and flushed to disk once at end.
        This keeps a 200-image bulk run to ONE atomic cache write instead of 200.

    Concurrency:
      - `concurrency` workers in flight via asyncio.Semaphore.
      - Each worker runs sync vlm_client.score_one in a thread (anthropic
        SDK is synchronous; asyncio.to_thread keeps the event loop free).

    Progress:
      - `progress_callback` is called after each successful score with a copy
        of the running state dict.

    Returns the final state dict.
    """
    prompt = get_prompt(prompt_id)
    if prompt is None:
        raise KeyError(f"Unknown prompt_id: {prompt_id}")

    images = list_image_filenames()
    cache = _load_cache()
    need_score = [fn for fn in images
                  if cache.get(fn, {}).get(prompt_id) is None]

    state: dict = {
        "prompt_id":  prompt_id,
        "prompt_name": prompt["name"],
        "total":       len(images),
        "cached":      len(images) - len(need_score),
        "to_score":    len(need_score),
        "scored":      0,
        "errors":      0,
        "started_at":  time.time(),
        "finished_at": None,
        "completed":   False,
        "error":       None,
    }
    log.info("bulk_score start: prompt=%s to_score=%d cached=%d",
             prompt_id, state["to_score"], state["cached"])

    if not need_score:
        state.update(completed=True, finished_at=time.time())
        if progress_callback:
            progress_callback(dict(state))
        return state

    sem = asyncio.Semaphore(concurrency)
    new_scores: dict[str, float] = {}
    new_scores_lock = asyncio.Lock()

    async def worker(filename: str):
        async with sem:
            try:
                image_path = IMAGES_DIR / filename
                jpeg_bytes = image_path.read_bytes()
                # vlm_client.score_one is sync (anthropic SDK is sync). Run in
                # a worker thread so the event loop can keep dispatching.
                score = await asyncio.to_thread(score_one, jpeg_bytes, prompt["text"])
                async with new_scores_lock:
                    new_scores[filename] = score
                    state["scored"] += 1
                if progress_callback:
                    progress_callback(dict(state))
            except Exception as e:
                state["errors"] += 1
                log.warning("bulk_score: %s × %s failed: %s",
                            filename, prompt_id, e)

    try:
        await asyncio.gather(*(worker(fn) for fn in need_score))
    except Exception as e:
        log.exception("bulk_score crashed")
        state["error"] = f"{type(e).__name__}: {e}"

    # Single atomic flush. Re-read cache inside the lock so we don't blow
    # away anything written by a concurrent path.
    if new_scores:
        with _WRITE_LOCK:
            cache = _load_cache()
            for fn, s in new_scores.items():
                cache.setdefault(fn, {})[prompt_id] = s
            _save_cache(cache)
        log.info("bulk_score flushed %d new scores for prompt=%s",
                 len(new_scores), prompt_id)

    state["completed"]   = True
    state["finished_at"] = time.time()
    state["elapsed_s"]   = round(state["finished_at"] - state["started_at"], 1)
    if progress_callback:
        progress_callback(dict(state))
    return state


# ---------------------------------------------------------------------------
# CLI sanity check
#   python prompt_library.py list
#   python prompt_library.py score <filename> <prompt_id>
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python prompt_library.py list")
        print("  python prompt_library.py score <filename> <prompt_id>")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "list":
        for p in list_prompts():
            print(f"  {p['id']:24}  scored on {p['n_scored']:4} images  — {p['name']}")
    elif cmd == "score":
        filename, prompt_id = sys.argv[2], sys.argv[3]
        s = score_image_on_prompt(filename, prompt_id)
        print(f"{filename} × {prompt_id} = {s:.3f}")
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
