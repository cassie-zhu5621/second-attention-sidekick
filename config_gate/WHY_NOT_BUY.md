# Why Not Just Buy a Stack-chan (or Jibo) and Code on It?

The honest answer to the recurring worry: *if my robot is "just" a pan-tilt head, why build one
instead of buying a Stack-chan / Jibo / screen-face pan-tilt robot and writing my code into it?*
Last updated: June 2026.

The short version, up front, because it should relieve a burden you've been carrying:

> **You should NOT try to justify custom hardware. Your hardware is not your contribution, and
> claiming it is would be a losing argument. The contribution is the *interaction concept*
> (Notice Delegation), the *relational grammar*, and the *find-and-share* relationship. The body
> is a deliberately minimal, mostly off-the-shelf instrument for studying that. There is exactly
> **one** design commitment that you genuinely cannot buy — *the eye is the camera* — and that
> one thing is enough.**

---

## 1. Stop defending the hardware — that's not where the value is

In HRI and research-through-design (RtD), the recognized contribution is "**making the right
thing**" — figuring out *what* to design and showing it matters — not "making the thing right"
(the best servos/chassis). Off-the-shelf platforms are explicitly encouraged, especially for
researchers without an engineering background, precisely so the *concept and study* can be the
focus. Your professor's "freeze the hardware, no new joints" is the same message: **the body is
settled; spend your effort on the interaction.**

So reframe the question. "Why didn't you buy one?" is only a damning question if you're claiming
the robot is a novel *device*. You're not. The correct answer is: *"The platform is intentionally
minimal and off-the-shelf. The contribution is the delegated-noticing interaction and its
grammar — studied on the simplest honest body that supports it."* That turns a perceived weakness
into a clear scoping statement, and it's the truthful one.

---

## 2. The one thing you can't buy: an *honest eye*

Here is the concrete, defensible difference — and it's a **concept requirement**, not a hardware
flex. Stack-chan and Jibo present their face on a **screen**: drawn cartoon eyes. The camera
(Stack-chan has one) is a **separate** part, somewhere else on the body. So on those robots:

> **The gaze you *read* (the drawn eyes) and the direction the robot actually *senses* (the
> camera) are two different things.** Their gaze is **decorative** — the eyes can "look at the
> bottle" on screen while the camera points at the wall, or at you. The face is, for perceptual
> purposes, a **lie.**

Your entire expressive logic depends on the opposite (see `GRAMMAR_EMBODIMENT.md`): *refer, don't
mime; the eye sees from where it looks; gaze = the actual direction of attention.* The whole
reason a person can trust "it noticed *that*" is that its regard **is** its perception. A
screen-face robot **structurally cannot** do honest noticing — when it "shows you the blue
bottle," its drawn eyes and its camera disagree.

So your build makes the **camera itself the eye**: one physical axis is both *where it looks* and
*what it sees*. That is the thing you can't get off the shelf from a Stack-chan or a Jibo, and it
is exactly what your concept needs. **That is the meaning of building your own** — not novel
joints, but an *honest* eye.

---

## 3. "Build vs buy" is a false binary — you're already buying

Look at what your rig actually is: an **off-the-shelf M5 camera**, **hobby servos**, a **printed
pan-tilt bracket**, an Arduino. You are not machining custom hardware — you're *assembling
commodity parts*, exactly like someone building a Stack-chan kit. So the honest description isn't
"I built a robot from scratch," it's:

> *"I assembled the **minimum honest instrument** — a camera-as-eye on a pan-tilt — from
> commodity parts. The only thing I deliberately did **not** buy is a fake screen-face, because
> my concept needs the eye to be the camera."*

That's both true and unattackable. You could even go further and **adopt the open Stack-chan
platform** (it's open-source, ESP32, pan-tilt, has a camera) and simply **make the camera the
eye instead of the screen** — get the de-risked hardware *and* keep the honest-eye commitment.
Either path is fine; the *meaning* is identical.

---

## 4. The comparison, plainly

| | Stack-chan / Jibo (screen-face pan-tilt) | This sidekick |
|---|---|---|
| **The "eye"** | drawn on a screen; camera is a separate part | **the camera *is* the eye** — gaze = sensing axis |
| **Gaze honesty** | decorative — eyes and camera can disagree | **honest** — it sees exactly where it looks |
| **What it's *for*** | conversation, companionship, a cute display | **delegated noticing** — watch-for-X, find it, show you |
| **Intelligence** | TTS / chat / scripted expressions | VLM-compiled **relational grammar**, steered by your words |
| **What it is** | a product | a **research probe** for a new relationship (Notice Delegation) |
| **Hardware claim** | (it's the product) | **none** — minimal, off-the-shelf, on purpose |

The two left-column traits (screen face, conversation) are exactly what your concept must *avoid*.
You're not failing to be a Stack-chan; you're deliberately not one.

---

## 5. The answer for the professor / reviewer (say this)

> "I'm not claiming novel hardware — the platform is intentionally minimal and off-the-shelf
> (a camera, two servos, a bracket). I could have used a Stack-chan, with one exception: its
> face is a screen, so its gaze is decorative and can disagree with where its camera points. My
> concept requires the opposite — the eye **is** the camera, so the robot's regard is its
> perception and 'it noticed *that*' is honest. That single commitment is why I build a
> camera-as-eye rather than buy a screen-face robot. The contribution isn't the body; it's the
> delegated-noticing interaction and the relational grammar it runs."

---

## 6. What this means for the thesis (research-through-design)
- Frame the work as **RtD**: the designed artifact is an *argument* about a new human–robot
  relationship (you delegate the act of noticing). The contribution is **design knowledge** — how
  to make delegated noticing legible and shareable — plus the grammar and the study, not the servos.
- The minimal body is a **feature**: it isolates the variable you're studying (the interaction)
  from hardware confounds, and it's honest about what it is (not a CCTV, not a companion-chatbot —
  see the novelty framing in `FORM_DECISION.md` / `GRAMMAR_EMBODIMENT.md`).
- So the recurring anxiety ("why this body, why not buy one") has a permanent answer now: **the
  body is the minimum honest instrument; the eye-is-the-camera is the one thing you can't buy;
  everything else is, and should be, off the shelf.**

---

## Sources
- Stack-chan — open-source M5Stack super-kawaii robot: **2.0" touchscreen animated face** + camera
  + 2 pan-tilt servos. https://github.com/stack-chan/stack-chan ·
  https://shop.m5stack.com/products/stackchan-kawaii-co-created-open-source-ai-desktop-robot
- *Championing Research Through Design in HRI* (2019) — RtD = "making the right thing" (what to
  design), not only "making the thing right." https://arxiv.org/pdf/1908.07572
- *Lessons Learned… HRI Experts* / *On the Death of NAO* — off-the-shelf vs custom platform
  trade-offs; contribution isn't the hardware. https://www.frontiersin.org/journals/robotics-and-ai/articles/10.3389/frobt.2021.772141/full
- Project internal: `GRAMMAR_EMBODIMENT.md` (the eye sees from where it looks; refer-don't-mime),
  `FORM_DECISION.md` (novelty is the interaction/grammar), `FIND_AND_SHARE.md` (the relationship).
