"""
voice_agent.py — wake word "potato" + a conversational window, with VAD so it
captures WHOLE utterances (records from when you start talking until you pause —
no fixed cutoff that chops your sentence).

  SLEEP  : waits for "hey potato".
  AWAKE  : after the wake beep, just say what to look for ("animals", "more story",
           "people working") — each command extends the window; silence past
           --cooldown returns to SLEEP.

Runs on the LAPTOP mic, alongside live_loop.py (they share preference.txt).

Setup:  pip install sounddevice openai-whisper numpy
Run:    python3 voice_agent.py     # --wake potato --cooldown 20 --silence 0.8 --level 0.02
"""

import argparse
import re
import subprocess
import time
from pathlib import Path

import numpy as np
import sounddevice as sd
import whisper

PREF = Path(__file__).parent / "preference.txt"
SR = 16000

FILLERS = {"hmm", "hm", "mm", "mhm", "uh", "um", "oh", "ah", "no", "yeah", "yes", "ok",
           "okay", "hi", "hey", "huh", "what", "the", "a", "an", "and", "so", "well", "you", "sorry"}


def beep(name):
    try:
        subprocess.run(["afplay", f"/System/Library/Sounds/{name}.aiff"], timeout=3)
    except Exception:
        print("\a", end="", flush=True)


def listen(onset_timeout, max_secs, gap, thresh):
    """VAD capture: wait up to onset_timeout for speech to start, then record until
    `gap` seconds of silence (or max_secs). Returns float32 audio, or None if no speech."""
    blk = int(0.1 * SR)
    pre = 2                                  # 0.2s pre-roll so we keep the first syllable
    ring, buf = [], []
    started = False; idle = 0.0; quiet = 0.0; total = 0.0
    with sd.InputStream(samplerate=SR, channels=1, dtype="float32", blocksize=blk) as st:
        while True:
            data, _ = st.read(blk)
            data = data[:, 0]
            lvl = float(np.max(np.abs(data)))
            if not started:
                ring.append(data); ring = ring[-pre:]
                idle += 0.1
                if lvl > thresh:
                    started = True; buf = list(ring); buf.append(data); total = 0.0
                elif idle >= onset_timeout:
                    return None
            else:
                buf.append(data); total += 0.1
                quiet = quiet + 0.1 if lvl < thresh else 0.0
                if quiet >= gap or total >= max_secs:
                    break
    return np.concatenate(buf) if buf else None


def as_preference(text):
    t = text.lower()
    t = re.sub(r"[^a-z0-9'\s]", " ", t)                  # punctuation -> space ("hey, potato" too)
    t = re.sub(r"\b(hey|hi|ok|okay)\b", " ", t)          # drop greeting anywhere
    t = re.sub(r"\bpotato\b", " ", t)                    # drop wake word anywhere
    t = re.sub(r"^\s*(i\s+)?(love|like|want(?:\s+to\s+see)?|notice|look\s+for|care\s+about|show\s+me)\s+",
               " ", t)
    t = " ".join(t.split())
    if not t or len(t) < 2 or all(w in FILLERS for w in t.split()):
        return None
    return t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--wake", default="potato")
    ap.add_argument("--cooldown", type=float, default=20.0)
    ap.add_argument("--silence", type=float, default=0.8, help="pause that ends an utterance")
    ap.add_argument("--max", type=float, default=8.0, help="max utterance length")
    ap.add_argument("--level", type=float, default=0.02, help="speech loudness threshold")
    ap.add_argument("--model", default="base")
    ap.add_argument("--lang", default="en")
    args = ap.parse_args()

    print(f"loading whisper '{args.model}'...")
    model = whisper.load_model(args.model)
    kw = {"fp16": False}
    if args.lang:
        kw["language"] = args.lang

    def transcribe(audio):
        return model.transcribe(audio, **kw)["text"].strip()

    def set_pref(p):
        PREF.write_text(p); beep("Glass")
        print(f'  -> set to: "{p}"')

    state = "sleep"; awake_until = 0.0
    print(f'SLEEPING — say "hey {args.wake}". (Ctrl+C to stop)')
    while True:
        if state == "sleep":
            u = listen(onset_timeout=3.0, max_secs=args.max, gap=args.silence, thresh=args.level)
            if u is None:
                continue
            text = transcribe(u)
            if args.wake in text.lower():
                state = "awake"; awake_until = time.time() + args.cooldown
                beep("Tink")
                print(f'AWAKE ({int(args.cooldown)}s) — say what to look for. heard: "{text}"')
                p = as_preference(text)              # "hey potato animals" in one breath
                if p:
                    set_pref(p); awake_until = time.time() + args.cooldown
        else:  # awake
            remaining = awake_until - time.time()
            if remaining <= 0:
                state = "sleep"; beep("Submarine")
                print(f'(window closed) SLEEPING — say "hey {args.wake}".')
                continue
            u = listen(onset_timeout=remaining, max_secs=args.max, gap=args.silence, thresh=args.level)
            if u is None:                            # no speech before the window expired
                state = "sleep"; beep("Submarine")
                print(f'(window closed) SLEEPING — say "hey {args.wake}".')
                continue
            text = transcribe(u)
            p = as_preference(text)
            if p:
                set_pref(p); awake_until = time.time() + args.cooldown
            else:
                print(f'  (heard "{text}" — ignored)')


if __name__ == "__main__":
    main()
