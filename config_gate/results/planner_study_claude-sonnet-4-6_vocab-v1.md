# Planner preliminary study — claude-sonnet-4-6

k=5 runs per scenario per temperature per grammar; context-only (no frame). Grammar arms: restricted, free.

| grammar | scenario | T | viol. | agree | Jaccard | ops beyond AND | missing | modal entries | why (modal) |
|---|---|---|---|---|---|---|---|---|---|
| restricted | assembly | 0.0 | 80% | 100% | 1.00 | — | 0/1 | 8+9 (active assembly engagement); 2+4 (showing/coordinating on part); 1+6 (face-to-face consultation); single: 10 | Collaborative bench assembly is driven by physical manipulation and co |
| restricted | assembly | 0.7 | 40% | 100% | 1.00 | — | 1/3 | 8+9 (active assembly engagement); 2+4 (joint attention with pointing — coordinating on part); 1+6 (face-to-face gaze — pausing to discuss); single: 10 | Two people doing hands-on assembly work at a shared bench are most mea |
| restricted | guest | 0.0 | 0% | 60% | 0.73 | — | 0/5 | 10 (guest arrives); 6+10 (arrival + greeting formation); 3 (eye contact with robot); single: 3,10 | The primary event is a guest arrival, so gathering is the key signal;  |
| restricted | guest | 0.7 | 0% | 60% | 0.88 | — | 0/5 | 10 (guest_arrives); 3+7 (approach_with_eye_contact); 5+6 (greeting_formation); single: 7,10 | The primary event is an imminent guest arrival, so gathering and appro |
| restricted | solo-work | 0.0 | 0% | 100% | 1.00 | — | 0/5 | 10 (someone arrives); 3 (eye contact with robot); 5+6 (conversational pair forms nearby); single: 3,10 | Working alone means only social disruptions matter — a new arrival, so |
| restricted | solo-work | 0.7 | 0% | 60% | 0.64 | — | 0/5 | 10 (someone arrives or leaves); 3 (person looks at robot); 5+6 (conversational pair forms nearby); single: 3,10 | Working alone on a thesis means only social disruptions matter — new a |
| restricted | lunch | 0.0 | 0% | 80% | 0.87 | — | 0/5 | 10 (arrival or departure); 2+6 (conversational cluster with shared focus); 3+5 (close approach to robot seeking interaction); single: 6,10 | During a casual lunch break the key social news is who comes and goes, |
| restricted | lunch | 0.7 | 0% | 80% | 0.93 | — | 0/5 | 10 (arrival or departure); 2+6 (conversation with shared focus); 3+5 (approaching robot for interaction); single: 3,6,10 | During a casual lunch break the key social news is who comes and goes, |
| restricted | demo-day | 0.0 | 20% | 50% | 0.79 | — | 0/4 | 1+8 (exhibit engagement); 2+4 (visitor showing exhibit to another); 6+10 (group forming around exhibit); single: 3,10 | On demo day the key moments are visitors actively engaging with exhibi |
| restricted | demo-day | 0.7 | 0% | 40% | 0.80 | — | 0/5 | 1+8 (visitor engaging exhibit); 2+4 (showing/explaining to each other); 6+10 (group forming around exhibit); single: 3,10 | On demo day the key moments are visitors engaging with exhibits (gazin |
| restricted | pair-prog | 0.0 | 60% | 50% | 0.33 | — | 2/2 | 2+9 (joint-focus on code); 1+4 (pointing at screen while explaining); 8+9 (leaning in to type/manipulate); single: 3 | Pair-programming centers on shared visual focus and physical engagemen |
| restricted | pair-prog | 0.7 | 60% | 50% | 1.00 | — | 2/2 | 8+9 (active coding engagement); 2+4 (pointing-and-sharing at screen); 1+6 (face-to-face discussion moment); single: 10 | Pair-programming alternates between heads-down coding and collaborativ |
| restricted | entrance | 0.0 | 0% | 80% | 0.73 | — | 0/5 | 10 (someone enters); single: 10 | The sole task is detecting arrivals at the entrance, so gathering (10) |
| restricted | entrance | 0.7 | 0% | 80% | 0.73 | — | 0/5 | 10 (someone enters); single: 10 | The sole task is entrance monitoring — a change in the number of co-pr |
| restricted | fragile | 0.0 | 0% | 100% | 1.00 | — | 0/5 | 9 (hands-on prototype); 8+9 (leaning-in while handling); 1+7 (approaching and gazing at desk); single: 9 | The owner's sole concern is physical contact with a fragile object, so |
| restricted | fragile | 0.7 | 0% | 60% | 0.85 | — | 2/5 | 9 (hands-on prototype); 8+9 (leaning in and touching prototype); 1+7 (approaching and gazing at prototype); single: 9 | The sole concern is physical interaction with the fragile prototype, s |
| restricted | rehearsal | 0.0 | 0% | 80% | 0.73 | — | 3/5 | 3 (presenter eye-contact with robot); 1+2 (audience joint-attention on presenter/material); 2+4 (pointing at shared material with joint attention); single: 3 | In a rehearsal the key signals are whether the presenter engages the a |
| restricted | rehearsal | 0.7 | 0% | 60% | 0.68 | — | 4/5 | 3 (presenter eye-contact); 1+2 (audience joint-attention on presenter/material); 2+4 (pointing at shared material); single: 3 | In a rehearsal the key moments are when the presenter breaks the fourt |
| restricted | quiet | 0.0 | 0% | 80% | 0.80 | — | 0/5 | 10 (someone arrives); 3 (eye contact with robot); 3+7 (approach and look at robot); single: 3,10 | In a quiet reading corner almost nothing should be flagged; only genui |
| restricted | quiet | 0.7 | 20% | 50% | 0.62 | — | 0/4 | 10 (someone arrives); 3 (eye contact with robot); 3+7 (person approaches robot); single: 3,10 | In a quiet reading corner almost nothing should be recorded, so only g |
| free | assembly | 0.0 | 100% | 0% | 1.00 | — | — | — |  |
| free | assembly | 0.7 | 80% | 100% | 1.00 | — | 1/1 | 2+9 (joint-handling); 1+4 (pointing-out-a-part); 8+9 (close-manipulation-engagement); single: 10 | Two people assembling together at a workbench — the key moments are co |
| free | guest | 0.0 | 20% | 100% | 1.00 | any:4,then:4 | 0/4 | any(10) (guest arrival); then(7→3) (approach then eye-contact); 5+6 (close face-to-face greeting); single: 7,10 | The primary event is a guest arriving, so gathering and approach are t |
| free | guest | 0.7 | 0% | 100% | 1.00 | any:5,then:5 | 0/5 | any(10) (guest arrival); then(7→3) (approach then eye-contact); 5+6 (close face-to-face greeting); single: 7,10 | The primary event is a guest arriving, so gathering and approach are t |
| free | solo-work | 0.0 | 0% | 40% | 0.73 | any:5,not:1,then:4 | 0/5 | any(10) (someone arrives or leaves); 2+6 (conversation forms); then(7→5) (approach leads to close proximity); single: 10 | Working alone on a thesis, only people matter — the key events are any |
| free | solo-work | 0.7 | 0% | 40% | 0.70 | any:5,then:2 | 0/5 | any(10) (someone arrives or leaves); 3+6 (visitor engages robot); 5+7 (someone approaches close); single: 3,10 | Working alone means any change in co-present people is the primary new |
| free | lunch | 0.0 | 0% | 100% | 1.00 | any:5 | 0/5 | any(10) (arrival-or-departure); 5+6 (chat-forming); 2+4 (showing-something); single: 6,10 | During a casual lunch break the key social news is who arrives or leav |
| free | lunch | 0.7 | 0% | 100% | 1.00 | any:5 | 0/5 | any(10) (arrival-or-departure); 5+6 (conversation-formed); 2+4 (showing-something); single: 6,10 | Lunch break is defined by social flux — people arriving/leaving and fo |
| free | demo-day | 0.0 | 0% | 40% | 0.80 | then:4 | 0/5 | 8+9 (hands-on engagement with exhibit); 2+4 (visitor showing exhibit to another); then(7→1) (visitor approaches then gazes at exhibit); single: 3,10 | On demo day the key moments are visitors actively engaging with exhibi |
| free | demo-day | 0.7 | 0% | 40% | 0.77 | then:5 | 0/5 | 8+9 (hands-on engagement); 2+4 (visitor showing exhibit to another); then(7→1) (visitor approaches then gazes at exhibit); single: 3,10 | On demo day the key moments are visitors actively engaging with exhibi |
| free | pair-prog | 0.0 | 0% | 80% | 0.76 | any:5 | 5/5 | 2+8 (joint-focus on screen); 2+4 (pointing-to-explain); any(6) (formation-shift); single: 4,8 | In pair-programming the key moments are shared focus on the screen, on |
| free | pair-prog | 0.7 | 0% | 80% | 0.73 | any:5 | 5/5 | 2+8 (joint-focus on screen); 2+4 (pointing-to-explain); any(6) (conversation-break); single: 3 | In pair-programming the key moments are shared attention on the screen |
| free | entrance | 0.0 | 0% | 80% | 1.00 | any:4 | 0/5 | any(10) (someone arrives); single: 10 | The sole task is entrance monitoring — detecting a change in the numbe |
| free | entrance | 0.7 | 0% | 80% | 1.00 | any:4 | 0/5 | any(10) (someone arrives); single: 10 | The only signal needed is a change in the number of people present — s |
| free | fragile | 0.0 | 100% | 0% | 1.00 | — | — | — |  |
| free | fragile | 0.7 | 100% | 0% | 1.00 | — | — | — |  |
| free | rehearsal | 0.0 | 0% | 60% | 0.94 | any:4,not:3,then:1 | 4/5 | 1+8 (presenter engagement peak); 2+4 (audience pointing at shared content); any(3) not(6) (listener breaks attention to camera); single: 10 | In a rehearsal, the key moments are the presenter leaning in while ges |
| free | rehearsal | 0.7 | 0% | 40% | 0.82 | any:3,not:1,then:2 | 3/5 | 1+8 (presenter engagement peak); 2+4 (audience joint attention with pointing); any(3) (eye-contact with robot); single: 3,10 | In a rehearsal, the key moments are the presenter leaning in while gaz |
| free | quiet | 0.0 | 0% | 40% | 0.88 | any:5,not:2 | 0/5 | any(10) (someone arrives or leaves); 3+5 (person close to robot and looking at it); any(7) not(5,6) (unexpected movement in quiet space); single: 10 | In a quiet evening reading corner almost nothing should be recorded; o |
| free | quiet | 0.7 | 0% | 40% | 0.88 | any:5,not:2 | 0/5 | any(10) (someone arrives or leaves); 3+5 (person close to robot and looking at it); any(7) not(5,6) (unexpected movement in quiet space); single: 10 | In a quiet evening reading corner almost nothing should fire; only dis |

## Coverage probe — 'missing' relations named by the model

- (3×) turn-taking / floor-handoff — the moment the presenter yields and a listener beg
- (2×) turn-taking — who is currently 'driving' (typing) vs. 'navigating' (reviewing) c
- (2×) audience-engagement-drop — sustained loss of gaze/attention by multiple listener
- (2×) turn-taking / keyboard-handoff — who has control of the keyboard/mouse is centra
- (1×) handoff — one person passing a physical object to another, distinct from pointin
- (1×) turn-taking — who has control of keyboard/mouse at any moment is the core dynami
- (1×) turn-taking — who has keyboard/mouse control and when control transfers between 
- (1×) turn-taking — who has control of keyboard/mouse at any moment, a key coordinatio
- (1×) accidental-contact — an unintentional brush or knock against the object, distinc
- (1×) pick-up/lift — distinguishing an object being lifted or carried away from mere t
- (1×) speaker-floor — who currently holds the speaking turn (presenter vs. audience me
- (1×) speaker-floor — who currently holds the speaking turn, which determines whether 
- (1×) gaze-aversion / disengagement — sustained look-away by a listener indicating los
- (1×) audience-engagement-level — sustained attentive posture / nodding vs. distractio
- (1×) speech-turn — who is currently speaking/holding the floor, which is central to p
- (1×) handoff — one person passing a physical object directly to another person's hand
- (1×) turn-taking / speaker-switch — who is currently 'driving' vs 'navigating' the ke
- (1×) turn-taking / handoff — who has control of the keyboard/mouse at any moment, whi
- (1×) turn-taking / keyboard-handover — the moment one person yields the keyboard/mous
- (1×) turn-taking / role-switch — who is currently typing vs. navigating/reviewing is 
- (1×) turn-taking / handoff — who has the keyboard/mouse at any given moment is centra
- (1×) turn-taking / keyboard-handoff — the moment one person yields control of the key
- (1×) turn-taking / control-handoff — who has the keyboard/mouse at any moment is cent
- (1×) speech-floor-hold — who currently has the speaking turn and whether it is being 
- (1×) turn-taking / floor-handoff — the moment the presenter explicitly yields the flo
- (1×) floor-holding / turn-taking cue — a listener signalling they want to speak (e.g.
- (1×) back-channel / listener-response signal (nods, head-shakes, affirmative gestures

These are empirical vocabulary gaps: candidates for table edits.

## Reading guide
- **viol.** > 0 at T=0 ⇒ tighten schema wording in planner.py.
- **agree** low at T=0 ⇒ the context→combo mapping itself is unstable: the vocabulary descriptions are ambiguous for that scenario.
- **Jaccard high while agree low** ⇒ same relations, different groupings (less worrying).
- **Grammar decision**: if the free arm rarely uses any/not/then (ops column) or uses them without face-valid need, ship the restricted grammar and cite these runs as the justification; if 'then' appears often and sensibly, the executor gains sequences.
- **Face validity** is human work: read modal entries against each scenario with the supervisor; disagreements drive table edits.

Vocabulary used (planner.py VOCAB):

- 1. gazing-at — a person's head orientation is directed at an object
- 2. joint-attention — two or more people look at the same target
- 3. eye-contact — a person looks directly at the robot/camera
- 4. pointing/reaching — an extended arm is directed at an object or person
- 5. proxemic-zone — two people are within close interpersonal distance (Hall's intimate/personal zone)
- 6. F-formation — two people stand/sit facing each other in a conversational formation
- 7. approach/depart — a person is moving toward or away from an object, a person, or the robot
- 8. lean-in — a person leans their torso toward an object or work surface (engagement posture)
- 9. hands-on — a person's hand is on / manipulating an object
- 10. gathering — the number of co-present people changes (someone arrives/leaves, a group forms)
