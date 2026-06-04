"""
set_preference.py — write the sidekick's current preference (what it loves) to
preference.txt. live_loop.py re-reads that file every cycle, so the running loop
switches target immediately — no restart.

For now you type it; later voice_set.py (CamS3 mic + Whisper) writes the same file.

Usage:
    python3 set_preference.py "animals and people"
    python3 set_preference.py            # prompts you
"""
import sys
from pathlib import Path

PREF = Path(__file__).parent / "preference.txt"

text = " ".join(sys.argv[1:]).strip() or input("preference> ").strip()
if text:
    PREF.write_text(text)
    print(f"preference set to: {text!r}  ({PREF})")
else:
    print("nothing entered; preference unchanged")
