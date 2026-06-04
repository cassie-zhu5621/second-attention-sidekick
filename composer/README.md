# composer/ — the live-instruction web server

The Composer: a web tool that **scores the dataset on named dimensions and lets you add
instructions / slide weights in real time** and see the photo ranking update. This is the
"give it instructions on the dataset" interface — all by typing/clicking, no mic.

## Run it
```
cd composer
pip3 install -r requirements.txt        # one-time: fastapi, uvicorn, anthropic, numpy, pillow, python-multipart
python3 -m uvicorn server:app --reload --port 8000
```
Then in a browser:
- **http://localhost:8000/health** → should show `cache_entries: 220, prompt_count: 9` (loaded OK)
- **http://localhost:8000/compose** → drag the weight sliders → ranking updates **live from the cache (no API call)**

## Two modes
- **Reweighting (offline, free):** sliding the 9 existing dimensions → instant re-rank. No API key needed.
- **Adding a new instruction (costs API):** type a new dimension name + grading description → it scores all 220 images on it. Needs `export ANTHROPIC_API_KEY=sk-...` first (~$0.20).

## How it relates to `../brain/`
Same `worth = Σ wₐ·sₐ` taste underneath.
- **composer/** = sliders + add-a-prompt, with a web UI (Layer-1 instruction on the dataset).
- **brain/** = the same taste plus the two layers the server doesn't have (passive keep/skip + long-term memory), in a typed terminal demo.

## Note for git
`images/` (12 MB, 220 photos) and `scores_cache.json` are included so it runs out-of-the-box.
If you don't want them in the repo, add to `.gitignore`:
```
composer/images/
composer/scores_cache.json
brain/scores_cache.json
brain/taste_profile_*.json
```
