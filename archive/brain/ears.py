"""
ears.py — turn what the person SAYS into a structured update of the taste.

utterance -> {weight_delta: {dim: +/-}, spatial_target: str|None, valence: +/-/None}

Two modes:
  - OFFLINE (default here): rule-based keyword parse, runs with no API — enough to
    test the learning loop by typing.
  - LLM: set an API key + remove the offline guard to use a model for robust parsing.

Test by typing:  python ears.py
"""
import os, re, json
from taste import DIM_NAMES

# crude keyword -> dimension hints for offline parsing
KEYWORDS = {
    "novelty": ["new", "novel", "unusual", "unexpected", "different"],
    "complexity": ["busy", "complex", "detailed", "rich"],
    "conflict": ["clutter", "messy", "chaos", "conflict", "cluttered"],
    "surprise": ["surprise", "surprising", "sudden"],
    "coherence": ["clean", "tidy", "organized", "coherent"],
    "mystery": ["mysterious", "hidden", "curious", "intriguing"],
    "aesthetic": ["beautiful", "pretty", "gorgeous", "aesthetic", "nice shot"],
    "decisive_moment": ["moment", "action", "gesture", "caught", "happening"],
    "story_potential": ["story", "people", "someone", "conversation", "together", "social"],
    # craft extras present in your real set can be added similarly (color_harmony, tension...)
    "color_harmony": ["color", "colour", "light", "warm", "golden"],
}
POS = ["love", "like", "more", "want", "keep", "yes", "great", "good", "nice"]
NEG = ["no", "not", "less", "stop", "ugh", "hate", "don't", "dont", "boring", "skip"]
TARGETS = ["door", "window", "table", "desk", "whiteboard", "entrance", "couch", "plant"]


def parse_offline(utterance: str) -> dict:
    u = utterance.lower()
    # NEG takes precedence so "not / ugh / don't" flips intent even if "more" appears
    valence = -1 if any(w in u for w in NEG) else (+1 if any(w in u for w in POS) else +1)
    delta = {}
    for dim, kws in KEYWORDS.items():
        if dim not in DIM_NAMES:  # only emit dims the taste actually has
            continue
        if any(k in u for k in kws):
            delta[dim] = float(valence)
    target = next((t for t in TARGETS if t in u), None)
    return {"weight_delta": delta, "spatial_target": target, "valence": valence}


def parse_llm(utterance: str) -> dict:
    import anthropic
    client = anthropic.Anthropic()
    prompt = ("Map this utterance to a JSON object {weight_delta:{dim:+1/-1}, "
              f"spatial_target:str|null, valence:+1/-1}}. Valid dims: {DIM_NAMES}. "
              f"Utterance: {utterance!r}. Return ONLY JSON.")
    msg = client.messages.create(model=os.environ.get("SECONDATTN_MODEL", "claude-sonnet-4-6"),
                                 max_tokens=200, messages=[{"role": "user", "content": prompt}])
    t = msg.content[0].text.strip()
    if t.startswith("```"): t = t.split("```")[1].replace("json", "", 1).strip()
    return json.loads(t)


def parse(utterance: str) -> dict:
    if os.environ.get("SECONDATTN_OFFLINE", "1") == "1":
        return parse_offline(utterance)
    return parse_llm(utterance)


if __name__ == "__main__":
    import taste
    w = taste.default_weights()
    print("Type things you'd say to the sidekick (blank line to quit). e.g.:")
    print("  'I love when people are working together at the table'")
    print("  'ugh not more cluttered shots'\n")
    for line in iter(lambda: input("you> "), ""):
        parsed = parse(line)
        w = taste.ema_update(w, parsed["weight_delta"], lr=0.3)
        print("  parsed:", parsed)
        print("  taste now:", {k: round(v, 2) for k, v in w.items() if abs(v-1.0) > 1e-6} or "(unchanged)")
