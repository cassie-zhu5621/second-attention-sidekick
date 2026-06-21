# Related work for the HRI full-paper target — reading list + bar assessment

11 papers to skim, 3 to read closely, and an honest read on whether this project can reach an HRI
full-paper bar and how. Columns: **Relevance** (why it matters) · **Our difference** (what we add
that they don't) · **Borrow** (method/framing to take).

## A. "Should the robot act / what is worth flagging" — same core question as ours

**To Help or Not to Help? An Expanded Framework for Deciding Socially Appropriate Robot Assistance** (ACM THRI). https://dl.acm.org/doi/10.1145/3797264
- Relevance: the closest *conceptual sibling* — a framework for WHEN a robot should help, weighing relative skill, social value, and cost; validated with a large online study.
- Our difference: their criterion is a designed/fixed model; ours is **user-compiled in plain language** (VLM-as-compiler) and about *noticing*, not task help.
- Borrow: how to frame "appropriateness of acting" as a contribution; the large rated-scenario study design. *(summarized from abstract; full text behind ACM paywall.)*

**Longitudinal Proactive Robot Assistance** (HRI '23 companion). https://dl.acm.org/doi/10.1145/3568294.3579982
- Relevance: proactivity studied over time (not one-shot).
- Our difference: we proactively *report worth-noticing moments*, not pre-empt tasks.
- Borrow: longitudinal study framing.

**Proactive Robot Assistance via Spatio-Temporal Object Modeling** (arXiv 2211.15501). https://arxiv.org/pdf/2211.15501
- Relevance: predicts what to attend to from the scene's spatio-temporal structure — kin to our relation graph / gate.
- Our difference: ours is steered by a VLM-compiled taste + theory-grounded relations, not learned object dynamics alone.
- Borrow: how a structured-scene signal is evaluated.

**PACT: Proactive Asking for Continual Task Assistance** (arXiv 2605.24350). https://arxiv.org/html/2605.24350
- Relevance: "ask-or-act" — deciding when uncertainty warrants interrupting.
- Our difference: ours decides when a *moment is worth reporting*, gated cheaply then VLM-confirmed.
- Borrow: the interrupt-vs-stay-quiet decision framing (maps to our gate + cooldown).

**How Does Delegation in Social Interaction Evolve Over Time? Navigation with a Robot for Blind People** (CHI '26, cond. accepted). https://arxiv.org/pdf/2601.19851
- Relevance: the rare paper that studies *delegation itself* — how blind users hand decision-making to a robot and how that delegation **shifts over time** (some delegate from the start, others resist then come to rely on it). Directly names our core verb.
- Our difference: they study delegating *navigation/decisions* for accessibility; ours delegates *noticing* — a user-set, rewritable attentional taste, with the robot reporting rather than acting on the user's behalf.
- Borrow: their longitudinal lens on how delegation is *negotiated and re-calibrated* over repeated use — a ready-made study frame for "how does a user's trust in the sidekick's noticing evolve?"

**Proact-VL: A Proactive VideoLLM for Real-Time AI Companions** (arXiv 2026). https://arxiv.org/pdf/2603.03447
- Relevance: a VideoLLM that, instead of answering only when prompted, **autonomously decides when to speak** via a lightweight per-second triggering head (FLAG hidden state → score → threshold τ). This is almost exactly our "cheap gate decides, then VLM speaks" architecture, in the companion setting.
- Our difference: their trigger is a learned end-to-end head; ours is a *theory-grounded relational gate* (gaze/joint-attention geometry) compiled from a user's plain-language taste — interpretable and steerable, not a black-box score.
- Borrow: the framing of "proactive = a thresholded triggering signal layered on a passive VLM"; cite as the timely VLM-side precedent for our gate + cooldown, and contrast learned-vs-relational triggering.

**YETI (YET to Intervene): Proactive Interventions by Multimodal AI Agents in AR Tasks** (arXiv 2501.09355). https://arxiv.org/pdf/2501.09355
- Relevance: detects *when* a multimodal agent should proactively intervene, computing lightweight on-the-fly features for fast frame-level "intervene now?" decisions — the same cheap-perception-gates-expensive-reasoning move as ours, for timely assistance.
- Our difference: YETI intervenes to *help with a task* in AR; ours decides when a *moment in a shared space is worth reporting* (noticing, not assisting), gated by social-spatial relations rather than task progress.
- Borrow: their lightweight frame-level interruptability signal as a baseline/comparison for our gate; their evaluation of intervention *timeliness*.

## B. Autonomous "capture the worth-capturing moment" robots — closest ARTIFACT analogs

**Designing Social Interactions with a Humorous Robot Photographer** (HRI '20, Yale). https://interactive-machines.com/assets/papers/adamson-HRI20.pdf
- Relevance: a robot that *autonomously decides when a moment is worth capturing* + interacts socially. Nearest artifact to ours.
- Our difference: it captures *portraits on offer*; we **delegate noticing** — a user-set, rewritable taste over a live space, reporting moments you'd have missed (no posing, no fixed trigger).
- Borrow: human-centered design process (interview photographers → design); lab eval of a single social behavior with a clean comparison.

**PhotoBot: Reference-Guided Interactive Photography via Natural Language** (arXiv 2024). https://arxiv.org/html/2401.11061v3
- Relevance: VLM/LLM + photography + **natural-language steering** — closest to our "compile language into what to capture."
- Our difference: PhotoBot matches a reference for one shot; ours compiles an *ongoing, rewritable taste* that gates continuous noticing.
- Borrow: how they wire a VLM into a capture decision + language control.

**An Autonomous Robot Photographer** (IEEE). https://ieeexplore.ieee.org/document/1249268/
- Relevance: the classic root of "robot that roams and decides when to shoot."
- Our difference: composition-driven vs taste/relevance-driven + delegation framing.
- Borrow: baseline framing for "autonomous capture."

## C. Attention / joint attention social behavior — theory + how to MEASURE it

**Are You Looking At Me? Perception of Robot Attention is Mediated by Gaze Type and Group Size** (HRI '13, Admoni et al., Yale). https://scazlab.yale.edu/sites/default/files/files/hri13.pdf
- Relevance: how people *perceive* a robot is attending, and how to measure it rigorously.
- Our difference: we use perceived-attention behavior (orient/nod) as a *legibility cue for delegated noticing*, in a real multi-person space.
- Borrow: their **measurement method** (see deep-read below) — detection-accuracy of "who is being attended to," manipulating gaze type + group size.

**Responsive Joint Attention in Human-Robot Interaction** (DiVA). https://www.diva-portal.org/smash/get/diva2:1391479/FULLTEXT01.pdf
- Relevance: robot responding to/establishing joint attention — your #6 relation.
- Our difference: ours *joins* human joint attention as the trigger to report, not for task hand-off.
- Borrow: operational definitions of responsive joint attention.

## D. Steerability + LLM-era positioning

**End-User Development for HRI** (arXiv 2402.17878). https://arxiv.org/pdf/2402.17878
- Relevance: how end users define what a robot does — maps to our editable taste.
- Our difference: ours steers *what to notice* via conversation, not task programming.
- Borrow: framing the "see=teach" loop as end-user steering.

**How Do We Research HRI in the Age of LLMs? A Systematic Review** (arXiv 2602.15063). https://arxiv.org/pdf/2602.15063
- Relevance: positions LLM/VLM-in-HRI; names potential AND pitfalls.
- Our difference: we use the VLM as a *gated compiler/confirmer*, not a per-frame controller — a direct answer to a stated pitfall.
- Borrow: cite to position the contribution + pre-empt reviewer concerns.

## E. Ambient / "cohabitant" presences — the non-assistant framing (near-neighbor)

**The Stochastic Parrot: a physical AI Cohabitant** (MIT Media Lab, Quincy / Ethan Chang, 2026). https://www.media.mit.edu/projects/the-stochastic-parrot/overview/
- Relevance: coins **"AI Cohabitant"** — a physical agent framed as a *roommate / house-pet* with its **own personality and narrative**, autonomous, ambient, continuously present; explicitly **reverses the subservient assistant dynamic** (observes, learns, "subtly participates" on its own rhythm rather than waiting for commands). The strongest available citation for "this is **not** a voice-assistant, it's an ambient placed presence."
- Our difference: their contribution is **characterful autonomy — the AI's *own* attention/agenda**. Ours is the **opposite vector: *delegated, steerable* noticing** — the criterion of what's worth attention is the **user's**, given in plain words, **rewritable**, and the robot **reports** it. *Cohabitant = the AI's own attention; our sidekick = the user's attention, delegated & embodied.* Both are ambient non-assistant presences; the **delegation + the relational grammar** is ours.
- Borrow: the "AI Cohabitant" umbrella term to justify the non-assistant, persistent-presence stance; their framing of "ambient autonomy vs engagement-maximizing assistant."

---

## Deep read 1 — "Are You Looking At Me?" (Admoni et al., HRI '13)
**What they did:** built cheap programmable robots (MyKeepon + Arduino, USB serial — same shape as your rig) and ran a 3×4 study (group size 4/6/8 × fixation 0/1/3/6 s). Participants pick which robot is attending to them; measure = detection accuracy + confidence.
**Findings:** **multiple short glances beat one long stare** for conveying attention (signif.); accuracy drops as the crowd grows. They argue it's the *transition into fixation* (a "fixation event"), not the stare, that reads as attention.
**Why it matters for you:** (1) directly justifies designing your robot's LOOK as **short, frequent glances**, not long stares — and your nod as a discrete "fixation event." (2) Gives you a **rigorous, citable way to measure "perceived attention"** (detection accuracy among distractors) — usable for your "did people read it as noticing?" question. (3) Precedent that a *cheap, imprecise* rig is acceptable at HRI if the study is clean.

## Deep read 2 — "Humorous Robot Photographer" (Adamson et al., HRI '20)
**What they did:** human-centered design (interviewed pro + amateur photographers) → built a robot portrait photographer that uses humor to elicit spontaneous smiles → lab eval comparing humor vs no-humor (measured smile spontaneity + appreciation).
**Findings:** humor elicited more spontaneous smiles and was appreciated; design insights for social robot photographers.
**Why it matters for you:** this is the **template for your paper's shape** — (design process → artifact → clean comparison of ONE behavior → design insights). Your equivalent comparison could be steerable-taste vs fixed, or legible-movement vs none. Also marks your **white space**: they capture *posed portraits on request*; nobody has done *delegated, rewritable noticing over a live space* — that's your novelty in one sentence.

## Deep read 3 — "To Help or Not to Help?" (THRI)
**What they did (from abstract):** a framework for deciding when robot help is socially appropriate, factoring relative skill, social value, and cost; validated with a large online rated-scenario study.
**Why it matters for you:** the field already treats "**should the robot act?**" as a first-class, publishable question — that legitimizes "**is this moment worth reporting?**" as your core contribution. Borrow their move of formalizing appropriateness + validating with rated scenarios. *(Read the full PDF yourself — I only had the abstract.)*

---

## Bar assessment — can this reach an HRI full paper, and how?
**Yes — these are your peers, not a higher tier.** The genre ("a robot autonomously decides what's
worth doing/capturing/reporting", evaluated with a human study) is established and accepted. Your
project is already *differentiated* on three axes none of them combine:
1. **Delegation** — the criterion is the user's, **compiled from plain language** (vs fixed models).
2. **VLM-as-compiler + cheap confirmed perception** — timely, and a direct answer to the "LLM-in-HRI pitfalls" review.
3. **Theory-grounded relational moments** (joint attention, gaze) — rigor the photographer line lacks.

**The gap to close (where to spend the extra work):**
- A **rigorous study**, not a one-shot demo: a controlled comparison (steerable taste vs fixed; legible movement vs none; embodied rig vs static camera) and/or a multi-week deployment.
- **Measure the right constructs**: perceived attentiveness (use Admoni's detection method), trust, usefulness, **agreement between what it flagged and what the user themselves valued** (precision/recall of worth-noticing), and how people appropriate the taste.
- **Multi-person, real space** so the joint-attention claim holds.
- Lead the writing with **concept + findings**; keep VLM+CV+servos as method, or reviewers reduce it to "robot photographer + LLM."

**Bottom line:** height is reachable; novelty is already in hand; success hinges on study rigor +
measuring the right things, not on more engineering.

---

## Auto-scan log
- 2026-06-21: no new items (web search tool was unavailable — 8 attempts across all project angles all failed; recent-session check found only hardware/channel-design work, no new references). Will retry on the next scan.
- 2026-06-21 (retry, search restored): added 3 items to §A: "How Does Delegation in Social Interaction Evolve Over Time?" (CHI '26), "Proact-VL: A Proactive VideoLLM for Real-Time AI Companions", "YETI: Proactive Interventions by Multimodal AI Agents in AR Tasks". Skipped egocentric "what-did-I-miss" assistants (EgoLife/EgoSelf — wearable, not placed robots) and ambient-AI products (Lenovo Qira etc., commercial, cohabitant angle already covered).
