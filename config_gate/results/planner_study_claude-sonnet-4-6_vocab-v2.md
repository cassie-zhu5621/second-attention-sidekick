# Planner preliminary study — claude-sonnet-4-6

k=5 runs per scenario per temperature per grammar; context-only (no frame). Grammar arms: restricted, free.

| grammar | scenario | T | viol. | agree | Jaccard | ops beyond AND | missing | modal entries | why (modal) |
|---|---|---|---|---|---|---|---|---|---|
| restricted | assembly | 0.0 | 0% | 60% | 0.70 | — | 0/5 | 9+11 (tool/part handoff); 1+8 (focused inspection); 2+4 (pointing out a part); single: 11 | A two-person hands-on assembly session at a workbench is defined by co |
| restricted | assembly | 0.7 | 0% | 60% | 0.70 | — | 0/5 | 9+11 (tool/part handoff); 1+8 (focused assembly engagement); 5+6 (close collaborative stance); single: 9,11 | Two people doing hands-on mechanical assembly at a shared bench will p |
| restricted | guest | 0.0 | 0% | 40% | 0.68 | — | 0/5 | 10 (guest_arrival); 3 (eye_contact_with_robot); 1+6 (greeting_formation); single: 3,10 | The primary event is an expected guest arrival, so gathering is the to |
| restricted | guest | 0.7 | 0% | 80% | 0.84 | — | 0/5 | 10 (guest_arrival); 3 (eye_contact_with_robot); 5+6 (greeting_formation); single: 3,10 | The primary event is an expected guest arrival, so gathering is the to |
| restricted | solo-work | 0.0 | 0% | 100% | 1.00 | — | 0/5 | 10 (someone arrives); 3 (eye contact with robot); 7 (approach or depart); single: 3,7,10 | Solo thesis work means only people-level events matter — arrivals, dep |
| restricted | solo-work | 0.7 | 0% | 80% | 0.76 | — | 0/5 | 10 (someone arrives); 3 (eye contact with robot); 7 (approach or depart); single: 3,7,10 | Working alone means the only meaningful events are changes to social p |
| restricted | lunch | 0.0 | 0% | 60% | 0.91 | — | 0/5 | 6+10 (social cluster forms); 2+4 (showing something at table); 1+5 (close chat with shared focus); single: 7,10 | Lunch breaks are defined by fluid arrivals/departures and spontaneous  |
| restricted | lunch | 0.7 | 0% | 40% | 0.85 | — | 0/5 | 6+10 (chat cluster forms); 2+4 (showing something at table); 1+5 (close pair focused together); single: 7,10 | Lunch breaks are defined by fluid social grouping — people arriving/le |
| restricted | demo-day | 0.0 | 60% | 100% | 1.00 | — | 0/2 | 1+10 (visitor engaging exhibit); 2+4 (showing/pointing at exhibit); 2+6 (visitors discussing exhibit together); single: 3,10 | On demo day the key moments are visitors actively engaging with exhibi |
| restricted | demo-day | 0.7 | 20% | 50% | 0.81 | — | 0/4 | 1+6+10 (visitor engages exhibit together); 2+4 (pointing-out moment); 3+7 (visitor approaching robot); single: 10 | On demo day the key moments are visitors arriving and clustering (gath |
| restricted | pair-prog | 0.0 | 0% | 100% | 1.00 | — | 0/5 | 11 (keyboard handoff); 8+9 (active coding engagement); 2+4 (pointing at screen together); single: 6,11 | Pair-programming centers on who controls the keyboard/mouse and when t |
| restricted | pair-prog | 0.7 | 0% | 80% | 0.83 | — | 0/5 | 11 (keyboard handoff); 8+9 (active coding engagement); 2+4 (pointing at screen together); single: 6,11 | Pair-programming at one screen centers on who controls the keyboard/mo |
| restricted | entrance | 0.0 | 0% | 60% | 0.55 | — | 0/5 | 10 (arrival); single: 10 | The sole task is detecting when someone enters, which maps directly to |
| restricted | entrance | 0.7 | 0% | 60% | 0.55 | — | 0/5 | 10 (arrival); single: 10 | The sole objective is detecting when someone enters, which is exactly  |
| restricted | fragile | 0.0 | 0% | 40% | 0.75 | — | 0/5 | 9 (hands-on prototype); 8+9 (leaning-in while handling); 4+9 (reaching-for prototype); single: 9 | The sole concern is physical contact with a fragile object, so hands-o |
| restricted | fragile | 0.7 | 0% | 80% | 0.76 | — | 0/5 | 9 (hands-on prototype); 8+9 (leaning-in while handling); 4+9 (reaching then handling); single: 9 | The sole concern is physical contact with a fragile object, so hands-o |
| restricted | rehearsal | 0.0 | 0% | 40% | 0.73 | — | 0/5 | 3 (presenter seeks eye-contact); 1+6 (audience engaged in F-formation gaze); 1+8 (listener leans in and gazes at presenter); single: 3,6 | In a presentation rehearsal the key signals are whether the presenter  |
| restricted | rehearsal | 0.7 | 0% | 60% | 0.73 | — | 3/5 | 3 (presenter seeks eye-contact); 1+6 (audience engaged in formation); 1+8 (listener leans in and gazes); single: 3,10 | In a presentation rehearsal the key signals are whether the presenter  |
| restricted | quiet | 0.0 | 0% | 60% | 0.67 | — | 0/5 | 10 (gathering); 3 (eye-contact); 7 (approach-depart); single: 3,7,10 | In a quiet reading corner almost nothing should happen, so only the ra |
| restricted | quiet | 0.7 | 0% | 60% | 0.64 | — | 0/5 | 10 (gathering); 3 (eye-contact with robot); 7 (approach or depart); single: 3,7,10 | In a quiet reading corner almost nothing should happen, so only the ra |
| free | assembly | 0.0 | 0% | 40% | 0.83 | any:1 | 0/5 | 9+11 (tool/part handoff); 2+8 (joint focus on assembly point); 1+4 (pointing out a part or problem); single: 10 | Collaborative bench assembly is defined by who holds what and when con |
| free | assembly | 0.7 | 0% | 80% | 0.85 | — | 0/5 | 9+11 (tool/part handoff); 1+2 (joint attention on assembly); 8+9 (engaged manipulation at bench); single: 11 | Collaborative bench assembly is defined by who holds what, when contro |
| free | guest | 0.0 | 80% | 100% | 1.00 | then:1 | 0/1 | 3+10 (guest arrival + eye contact); then(7→6) (approach then face-to-face formation); 5+10 (arrival + close proximity); single: 10 | The primary event is a guest arriving, so gathering is the core signal |
| free | guest | 0.7 | 20% | 50% | 1.00 | any:2,not:1,then:2 | 0/4 | 3+10 (guest arrival + eye contact); then(7→6) (approach leads to conversation formation); 5+10 (arrival into close proximity); single: 10 | The primary event is a guest arriving, so gathering signals the news;  |
| free | solo-work | 0.0 | 20% | 50% | 0.80 | any:4,not:3 | 0/4 | any(10) (someone arrives or leaves); any(3) (person looks at robot); any(6) not(10) (conversational formation nearby); single: 3,10 | Working alone on a thesis means only unexpected human presence or soci |
| free | solo-work | 0.7 | 0% | 60% | 0.65 | any:5,not:5 | 0/5 | any(10) (someone arrives or leaves); any(3) (person looks at robot); any(6) not(10) (conversational formation nearby); single: 3,10 | Working alone on a thesis means any other person entering, leaving, or |
| free | lunch | 0.0 | 0% | 80% | 0.87 | any:5 | 0/5 | any(10) (group size change); 5+6 (conversational pair forms); 2+4 (showing something at table); single: 6,10 | Lunch break is defined by people arriving and leaving, casual conversa |
| free | lunch | 0.7 | 0% | 40% | 0.66 | any:5 | 0/5 | any(10) (arrivals and departures); 2+6 (conversational cluster with joint attention); 1+5 (close pair gazing together); single: 6,10 | Lunch breaks are defined by social flux — who comes and goes, who clus |
| free | demo-day | 0.0 | 0% | 40% | 0.82 | any:3 | 0/5 | 1+7 (visitor engages exhibit); 2+4 (visitors pointing and sharing attention); any(10) (group size change); single: 10 | On demo day the key moments are visitors stopping to engage with exhib |
| free | demo-day | 0.7 | 0% | 60% | 0.75 | any:2 | 0/5 | 1+7 (visitor engages exhibit); 2+4 (visitors pointing and sharing attention); 6+10 (group forms around exhibit); single: 10 | On demo day the key moments are visitors stopping to engage with exhib |
| free | pair-prog | 0.0 | 0% | 60% | 0.62 | any:5 | 0/5 | 8+11 (handoff with engagement); 2+4 (joint attention with pointing — explaining code); any(10) (third person arrives or one leaves); single: 10,11 | In pair-programming the key moments are control handoffs at the shared |
| free | pair-prog | 0.7 | 0% | 80% | 0.77 | any:5 | 0/5 | 8+11 (control-handoff with engagement); 2+4 (joint-attention with pointing — explaining code); any(10) (third person arrives or one leaves); single: 10,11 | In pair-programming the key moments are when keyboard/mouse control sw |
| free | entrance | 0.0 | 0% | 100% | 1.00 | any:5 | 0/5 | any(10) (someone arrives); single: 10 | The only event that matters is a change in the number of people presen |
| free | entrance | 0.7 | 0% | 100% | 1.00 | any:5 | 0/5 | any(10) (someone arrives); single: 10 | The sole instruction is to detect arrivals at the entrance, which is e |
| free | fragile | 0.0 | 0% | 100% | 1.00 | then:5 | 0/5 | 9 (hands-on prototype); then(7→9) (approach then handle); 8+9 (leaning in while handling); single: 9 | The owner's sole concern is physical contact with a fragile object, so |
| free | fragile | 0.7 | 0% | 100% | 1.00 | then:5 | 0/5 | 9 (hands-on prototype); then(7→9) (approach then touch); 8+9 (lean-in while handling); single: 9 | The owner's sole concern is physical contact with a fragile object, so |
| free | rehearsal | 0.0 | 0% | 20% | 0.56 | any:4,then:1 | 5/5 | 4+8 (presenter engagement peak); 2+4 (audience joint attention with pointing); any(10) (group composition change); single: 3,11 | In a presentation rehearsal the key moments are the presenter's engage |
| free | rehearsal | 0.7 | 20% | 25% | 0.54 | any:4,not:1,then:1 | 3/4 | 2+4 (presenter points + audience joint attention); 1+8 (presenter engages with material); any(10,11) (rehearsal disruption or role swap); single: 3,10 | In a presentation rehearsal the key moments are when the presenter dir |
| free | quiet | 0.0 | 0% | 40% | 0.77 | any:5,not:3 | 0/5 | any(10) (someone arrives); 3 (eye contact with robot); 5+6 (two people converge and face each other); single: 3,10 | In a quiet reading corner almost nothing should happen, so only genuin |
| free | quiet | 0.7 | 0% | 20% | 0.62 | any:5,not:3 | 0/5 | any(10) (someone arrives); 3 (eye contact with robot); 5+6 (two people converge and face each other); single: 3,10 | In a quiet reading corner almost nothing should be flagged; only genui |

## Coverage probe — 'missing' relations named by the model

- (3×) floor-hold / speaking-turn — who currently has the presenter role (distinct from
- (1×) delivery-feedback — a listener nods, shakes head, or gives verbal/gestural feedb
- (1×) presenter-gaze-sweep — the presenter deliberately scanning across multiple liste
- (1×) presenter-to-audience gaze sweep — tracking that the presenter deliberately scan
- (1×) presenter-floor — a signal that a specific person holds the speaking/presenting 
- (1×) gesture-emphasis — a presenter's deliberate rhetorical gesture (e.g. open-palm b
- (1×) delivery-quality cue — hesitation, filler words, or loss of eye-contact with the
- (1×) floor-hold / speaker-role signal — a relation indicating who currently holds the
- (1×) speaker-floor — who currently holds the presenter role (a role/turn token distin

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
- 11. turn-taking — control of a shared artifact (keyboard, tool, object) passes from one person to another
