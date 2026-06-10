# Context-Elicitation Form (paste into Google Forms)

Purpose: collect ecologically valid instructions ("contexts") people would give a
noticing robot — to validate / replace the designed scenario set of the planner study.
ORDER MATTERS: open elicitation comes BEFORE the checklist, so answers are not anchored
on our designed scenarios. Target: 15–20 respondents, 2–4 prompts per setting.

---

## Intro (form description)

> We are designing a small camera robot that sits in a shared space. You tell it in a
> sentence what kinds of moments are worth noticing, and it quietly watches and records
> only those — like a considerate observer, not a surveillance camera.
>
> This form takes about 5 minutes. Your text answers will be used (anonymised) to design
> and evaluate the system. No camera data is involved.

(One demographic question: "Your role" — student / faculty / staff / other.)

---

## Page 1 — In your lab / school space  (OPEN — the real data)

> Imagine this robot is placed in your lab or studio. **In your own words, write the
> instructions you would actually give it.** One sentence each. Think of different days
> and situations (a normal working day, a deadline week, an event…).

- Instruction 1  (required, free text)
- Instruction 2  (required, free text)
- Instruction 3  (optional)
- Instruction 4  (optional)

## Page 2 — At home  (OPEN — the real data)

> Now imagine the robot is in your home. Same task: what would you tell it to watch for?

- Instruction 1  (required, free text)
- Instruction 2  (required, free text)
- Instruction 3  (optional)
- Instruction 4  (optional)

## Page 3 — Our scenarios (VALIDATION — shown only after the open part)

> Below are situations we wrote ourselves. For each: would you actually give the robot
> an instruction like this?
> (3-point scale per item: Often / Sometimes / Never)

1. Two of us are assembling something at the workbench this afternoon.
2. I'm expecting a guest to arrive within the next hour.
3. I'm working alone; only people matter, ignore objects.
4. It's lunch break; people drift in and out and chat.
5. Open-lab demo day: visitors walk around and look at exhibits.
6. My labmate and I are pair-programming at one screen.
7. Watch the entrance and tell me when someone comes in.
8. I left a fragile prototype on the desk; I care about anyone handling it.
9. We're rehearsing a presentation: one presents, the others listen.
10. A quiet reading corner in the evening; nothing much should happen.

Final open question (optional):
> Is there anything you'd want it to notice that feels hard to put into words?

---

## Analysis plan (for our records)

- Open prompts → translate if needed → cluster into scenario categories → cumulative
  novelty curve by respondent order (**saturation = the curve flattens**; this plot is
  the coverage evidence, not the N).
- Compare clusters against the 10 designed scenarios (which designed ones never appear
  in real answers? which real clusters have no designed counterpart?).
- Checklist ratings: which designed scenarios people would actually use (Often+Sometimes
  share) — validation of the designed set, kept separate from the elicitation data.
- Real prompts become the v3 test set for planner_study.py.
- Note on language: respondents may answer in Japanese/Chinese — fine; the planner can
  be tested on them as-is (a free multilingual-robustness check) and translations are
  used for clustering.
