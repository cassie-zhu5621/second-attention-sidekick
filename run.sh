#!/bin/bash
# One-tap launcher for the Second Attention collector.
# It activates the Python virtualenv, then runs the collector.
#
# Usage:   ./run.sh            (first time: chmod +x run.sh)
#          ./run.sh --thresh 6 --min-gap 3      (pass any collector flags)
#
# If your virtualenv lives elsewhere, edit VENV below. To make a fresh one:
#   python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt

VENV="$HOME/Documents/Claude/Projects/Spatial_Camera/.venv"

if [ -f "$VENV/bin/activate" ]; then
    source "$VENV/bin/activate"
else
    echo "venv not found at $VENV — edit VENV in run.sh, or create one (see comment above)."
    exit 1
fi

python3 "$(dirname "$0")/sidekick_collector.py" "$@"
