# Planner preliminary study — claude-sonnet-4-6

k=5 runs per scenario per temperature per grammar; context-only (no frame). Grammar arms: restricted, free.

| grammar | scenario | T | viol. | agree | Jaccard | ops beyond AND | missing | modal entries | why (modal) |
|---|---|---|---|---|---|---|---|---|---|
| restricted | assembly | 0.0 | 0% | 60% | 0.74 | — | 0/5 | 9+11 (tool/part handoff); 1+8 (focused engagement with assembly); 5+6 (close collaborative stance); single: 9,11 | Two people assembling together at a workbench makes hands-on manipulat |
| restricted | assembly | 0.7 | 0% | 60% | 0.79 | — | 0/5 | 9+11 (tool/part handoff); 1+8 (focused engagement with workpiece); 5+6 (close collaborative stance); single: 9,11 | Two people assembling together at a bench makes hands-on manipulation, |
| restricted | guest | 0.0 | 0% | 40% | 0.75 | — | 0/5 | 7 (guest approaching); 10 (group forming at entry); 3 (guest seeks eye contact); single: 3,7,10 | Guests are expected to arrive, so the robot should watch for people mo |
| restricted | guest | 0.7 | 0% | 60% | 0.76 | — | 0/5 | 7 (guest approaching); 10 (group forming at entry); 3 (guest seeks eye contact); single: 3,7,10 | The robot should watch for arrivals — people moving toward the space,  |
| restricted | solo-work | 0.0 | 0% | 100% | 1.00 | — | 0/5 | 3 (eye-contact with robot); 7 (person approaches); 10 (group forms); single: 3,7,10 | Working alone means only person-level events matter: someone looking a |
| restricted | solo-work | 0.7 | 0% | 100% | 1.00 | — | 0/5 | 3 (eye-contact with robot); 7 (person approaches); 10 (someone enters space); single: 3,7,10 | Working alone means any person entering, approaching, or engaging the  |
| restricted | lunch | 0.0 | 0% | 60% | 0.83 | — | 0/5 | 5+6 (chat pair forming); 6+10 (group gathers to chat); 3+7 (person approaches robot); single: 7,10 | During a social lunch break the key moments are conversational cluster |
| restricted | lunch | 0.7 | 0% | 60% | 0.74 | — | 0/5 | 5+6 (chat pair forming); 6+10 (group gathers to chat); 3+7 (person approaches robot); single: 7,10 | During a social lunch break the key moments are conversational cluster |
| restricted | demo-day | 0.0 | 0% | 40% | 0.95 | — | 0/5 | 2+4 (visitor pointing out exhibit); 1+7 (visitor approaching and engaging exhibit); 6+10 (group forming around exhibit); single: 3,10 | On demo day visitors browse, cluster, and gesture at exhibits, so the  |
| restricted | demo-day | 0.7 | 0% | 60% | 0.82 | — | 0/5 | 2+4 (visitor showing exhibit to another); 1+7 (visitor approaches and engages exhibit); 6+10 (group forms around exhibit); single: 3,10 | On demo day visitors circulate and cluster, so the richest signals are |
| restricted | pair-prog | 0.0 | 0% | 60% | 0.77 | — | 0/5 | 11 (control handoff); 8+9 (active engagement with screen/input); 2+6 (mutual focus in conversation); single: 2,11 | Two collaborators at one screen will most meaningfully signal coordina |
| restricted | pair-prog | 0.7 | 0% | 60% | 0.80 | — | 0/5 | 11 (control handoff); 8+9 (active manipulation); 2+6 (shared focus moment); single: 2,11 | Two collaborators at one screen means the key events are who controls  |
| restricted | entrance | 0.0 | 0% | 60% | 0.80 | — | 0/5 | 7 (person enters); 10 (group forms at entrance); single: 7,10 | The core request is to detect anyone arriving through the entrance, wh |
| restricted | entrance | 0.7 | 0% | 80% | 0.80 | — | 0/5 | 7 (person enters); 10 (group forms at entrance); single: 7,10 | The core request is to detect anyone arriving through the entrance, wh |
| restricted | fragile | 0.0 | 0% | 80% | 0.90 | — | 0/5 | 9 (hands-on prototype); 8+9 (leaning-in while handling); 7 (approach to desk); single: 7,9 | The owner's sole concern is anyone touching the prototype, so hands-on |
| restricted | fragile | 0.7 | 0% | 60% | 0.85 | — | 0/5 | 9 (prototype touched); 8+9 (leaning in and handling prototype); 7 (person approaches desk); single: 7,9 | The owner cares about anyone interacting with the prototype, so hands- |
| restricted | rehearsal | 0.0 | 0% | 80% | 0.83 | — | 5/5 | 3 (presenter eye-contact with camera); 1+2 (faculty joint attention on presenter); 5+6 (faculty huddle / side discussion); single: 2,3 | In presentation practice the key moments are the presenter engaging th |
| restricted | rehearsal | 0.7 | 0% | 20% | 0.68 | — | 5/5 | 3+8 (presenter engaging camera/audience); 1+2 (faculty joint attention on presenter or slide); 1+4 (pointing at slide/content while gazing); single: 6 | In presentation practice the key moments are the presenter holding aud |
| restricted | quiet | 0.0 | 0% | 100% | 1.00 | — | 0/5 | 3 (someone looks at robot); 7 (someone approaches); 10 (group forms); single: 3,7,10 | In a quiet evening corner almost nothing is expected, so only the most |
| restricted | quiet | 0.7 | 0% | 100% | 1.00 | — | 0/5 | 3 (someone looks at robot); 7 (someone approaches); 10 (group forms); single: 3,7,10 | In a quiet evening corner almost nothing is expected, so only the most |
| free | assembly | 0.0 | 0% | 80% | 0.93 | — | 0/5 | 9+11 (tool/part handoff); 1+4 (pointing out a part or step); 8+9 (close engagement with workpiece); single: 11 | Two people collaboratively assembling at a workbench makes turn-taking |
| free | assembly | 0.7 | 0% | 60% | 0.84 | — | 0/5 | 9+11 (tool/part handoff); 1+4 (pointing out a part or step); 8+9 (close engagement with workpiece); single: 11 | Two people collaboratively assembling at a workbench makes turn-taking |
| free | guest | 0.0 | 0% | 100% | 1.00 | then:5 | 0/5 | then(7→3) (guest_arrives_and_notices_robot); 6+10 (group_forms_face_to_face); then(7→5) (guest_approaches_host); single: 7,10 | Guests arriving means the key signals are people approaching the space |
| free | guest | 0.7 | 20% | 75% | 1.00 | then:4 | 0/4 | then(7→3) (guest_arrives_and_notices_robot); 6+10 (group_forms_face_to_face); then(7→5) (guest_approaches_host); single: 7,10 | Guests arriving means the key signals are people moving toward the spa |
| free | solo-work | 0.0 | 0% | 40% | 1.00 | any:5,not:2,then:2 | 0/5 | any(7) not(10) (person approaches); 5+6 (two people close and face-to-face); any(10) (group size changes); single: 3,7,10 | Working alone means any person entering, nearing, or grouping near me  |
| free | solo-work | 0.7 | 20% | 50% | 1.00 | any:4,not:1,then:1 | 0/4 | any(7,10) (person arrives or group changes); 5+6 (close conversational pair); 3 (person addresses robot); single: 3,7,10 | Working alone means only people entering, leaving, grouping, or intera |
| free | lunch | 0.0 | 0% | 60% | 0.80 | any:5,then:1 | 0/5 | any(10) (group-size-change); 5+6 (chat-pair-formed); 2+4 (showing-something); single: 3,7 | During a social lunch break the key dynamics are people arriving/leavi |
| free | lunch | 0.7 | 0% | 40% | 0.75 | any:3,then:2 | 0/5 | 6+10 (group-forms-and-chats); 5+6 (face-to-face-close-conversation); 7+10 (someone-joins-or-leaves-group); single: 3,10 | During a casual lunch break the socially meaningful moments are groups |
| free | demo-day | 0.0 | 0% | 60% | 0.80 | then:1 | 0/5 | 1+5 (visitor engages exhibit closely); 2+4 (visitors pointing out exhibit to each other); 6+10 (group forms around exhibit); single: 3,8 | On demo day visitors browse exhibits, so the key moments are close eng |
| free | demo-day | 0.7 | 0% | 60% | 0.95 | then:2 | 0/5 | 2+4 (visitor showing exhibit to another); 1+7 (visitor approaches and engages exhibit); 6+10 (group forms around exhibit); single: 3 | On demo day the key social moments are visitors engaging exhibits (app |
| free | pair-prog | 0.0 | 0% | 100% | 1.00 | — | 0/5 | 1+11 (handoff with gaze shift); 2+8 (joint focus on screen with lean-in); 2+4 (pointing at shared screen together); single: 3,11 | Two collaborators at one screen means the key moments are turn-taking  |
| free | pair-prog | 0.7 | 0% | 40% | 0.74 | — | 0/5 | 1+11 (handoff with gaze shift); 2+8 (joint focus with lean-in engagement); 2+4 (pointing while jointly attending screen); single: 3,11 | Two collaborators sharing one screen makes turn-taking over the input  |
| free | entrance | 0.0 | 0% | 100% | 1.00 | — | 0/5 | 7 (person enters); single: 7 | The sole task is detecting someone arriving at the entrance, which is  |
| free | entrance | 0.7 | 0% | 80% | 1.00 | then:1 | 0/5 | 7 (person enters); single: 7 | The sole goal is detecting someone arriving at the entrance, which is  |
| free | fragile | 0.0 | 80% | 100% | 1.00 | — | 0/1 | 7+9 (approach-then-handle); 8+9 (lean-and-manipulate); 4+9 (point-and-touch); single: 9 | The owner cares about anyone touching the prototype, so hands-on conta |
| free | fragile | 0.7 | 100% | 0% | 1.00 | — | — | — |  |
| free | rehearsal | 0.0 | 0% | 40% | 0.69 | not:1,then:4 | 5/5 | 3+6 (presenter seeks faculty feedback); 2+4 (faculty pointing at shared content); then(8→1) (faculty lean-in and gaze — engaged critique); single: 3,10 | In presentation practice the key moments are the presenter checking fa |
| free | rehearsal | 0.7 | 0% | 20% | 0.69 | not:1,then:3 | 5/5 | 3 (presenter seeks eye-contact with robot/audience); 2+4 (faculty joint-attention with pointing — collaborative critique); then(7→3) (faculty approaches presenter then makes eye-contact — direct feedback moment); single: 3,6 | In presentation practice the key moments are the presenter engaging th |
| free | quiet | 0.0 | 0% | 60% | 0.76 | any:5 | 0/5 | any(3,7) (unexpected_presence); 5+6 (quiet_encounter); any(10) (group_forms); single: 3 | In a quiet evening corner almost nothing is expected, so only genuinel |
| free | quiet | 0.7 | 0% | 40% | 0.71 | any:5 | 0/5 | any(3) (eye-contact with robot); any(10) (group forms); 5+7 (person approaches close); single: 3,10 | In an expected-quiet evening corner almost nothing should fire, so onl |

## Coverage probe — 'missing' relations named by the model

- (2×) presenter-to-slide gaze-shift — a relation tracking when the presenter turns awa
- (2×) floor-holding / turn-to-speak — who currently has the presenter role is not expr
- (1×) presenter-to-audience gaze sweep — a deliberate scan across multiple listeners t
- (1×) presenter-gesture — a speaker's illustrative hand/body gesture directed at slide
- (1×) presenter-feedback-gesture — a faculty member nodding, shaking head, or raising 
- (1×) speaker-floor / turn-taking between presenter and faculty during Q&A feedback (t
- (1×) gesture-feedback — a faculty member's nodding, head-shaking, or other evaluative
- (1×) presenter-to-slide gaze-shift — alternating attention between notes/slides and a
- (1×) presenter-feedback-turn — a faculty member taking over the floor to give verbal 
- (1×) presenter-to-slide gaze tracking — knowing whether the student is reading from s
- (1×) floor-holding / speaking-turn — who currently has the presenter role (speaking v
- (1×) floor-hold / turn-taking-speech — the vocabulary has turn-taking only for shared
- (1×) floor-transfer-cue — a signal that one presenter has finished and the next is ab
- (1×) presenter-to-audience gaze sweep — a deliberate scan of multiple listeners by th
- (1×) presenter-turn — a discrete signal that a new student has taken the floor as the
- (1×) presenter-turn — a signal that identifies which individual currently holds the f
- (1×) floor-holding / speaker-turn signal — who currently has the floor as presenter v
- (1×) floor-holding / turn-yielding between presenter and questioner during Q&A (disti

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
- 10. gathering — the NUMBER of co-present people changes / a group forms (use this for group size, NOT for one person; for a single person coming toward a place or object, use approach(7))
- 11. turn-taking — control of a shared artifact (keyboard, tool, object) passes from one person to another
