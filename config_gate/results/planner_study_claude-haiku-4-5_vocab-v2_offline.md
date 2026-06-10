# Planner preliminary study — claude-haiku-4-5 (OFFLINE PLUMBING RUN — numbers meaningless)

k=2 runs per scenario per temperature per grammar; context-only (no frame). Grammar arms: restricted, free.

| grammar | scenario | T | viol. | agree | Jaccard | ops beyond AND | missing | modal entries | why (modal) |
|---|---|---|---|---|---|---|---|---|---|
| restricted | assembly | 0.0 | 0% | 100% | 1.00 | — | 0/2 | 4+10 ([offline] combo) | [offline] Two of us are assembling a robot arm at  |
| restricted | assembly | 0.7 | 0% | 100% | 1.00 | — | 0/2 | 4+10 ([offline] combo) | [offline] Two of us are assembling a robot arm at  |
| restricted | guest | 0.0 | 0% | 100% | 1.00 | — | 0/2 | 6+10 ([offline] combo); single: 11 | [offline] I'm expecting a guest to arrive at the s |
| restricted | guest | 0.7 | 0% | 100% | 1.00 | — | 0/2 | 6+10 ([offline] combo); single: 11 | [offline] I'm expecting a guest to arrive at the s |
| restricted | solo-work | 0.0 | 0% | 100% | 1.00 | — | 0/2 | 1+2 ([offline] combo); single: 10 | [offline] I'm working alone on my thesis. Only peo |
| restricted | solo-work | 0.7 | 0% | 100% | 1.00 | — | 0/2 | 1+2 ([offline] combo); single: 10 | [offline] I'm working alone on my thesis. Only peo |
| restricted | lunch | 0.0 | 0% | 100% | 1.00 | — | 0/2 | 3+7 ([offline] combo); single: 4 | [offline] It's lunch break; people drift in and ou |
| restricted | lunch | 0.7 | 0% | 100% | 1.00 | — | 0/2 | 3+7 ([offline] combo); single: 4 | [offline] It's lunch break; people drift in and ou |
| restricted | demo-day | 0.0 | 0% | 100% | 1.00 | — | 0/2 | 1+11 ([offline] combo); single: 10 | [offline] Open-lab demo day: visitors walk around  |
| restricted | demo-day | 0.7 | 0% | 100% | 1.00 | — | 0/2 | 1+11 ([offline] combo); single: 10 | [offline] Open-lab demo day: visitors walk around  |
| restricted | pair-prog | 0.0 | 0% | 100% | 1.00 | — | 0/2 | 3+10 ([offline] combo); single: 2 | [offline] My labmate and I are pair-programming at |
| restricted | pair-prog | 0.7 | 0% | 100% | 1.00 | — | 0/2 | 3+10 ([offline] combo); single: 2 | [offline] My labmate and I are pair-programming at |
| restricted | entrance | 0.0 | 0% | 100% | 1.00 | — | 0/2 | 5+6 ([offline] combo); single: 7 | [offline] Watch the entrance and tell me when some |
| restricted | entrance | 0.7 | 0% | 100% | 1.00 | — | 0/2 | 5+6 ([offline] combo); single: 7 | [offline] Watch the entrance and tell me when some |
| restricted | fragile | 0.0 | 0% | 100% | 1.00 | — | 0/2 | 2+11 ([offline] combo); single: 4 | [offline] I left a fragile prototype on the desk;  |
| restricted | fragile | 0.7 | 0% | 100% | 1.00 | — | 0/2 | 2+11 ([offline] combo); single: 4 | [offline] I left a fragile prototype on the desk;  |
| restricted | rehearsal | 0.0 | 0% | 100% | 1.00 | — | 0/2 | 5+9 ([offline] combo); single: 8 | [offline] We're rehearsing a presentation: one per |
| restricted | rehearsal | 0.7 | 0% | 100% | 1.00 | — | 0/2 | 5+9 ([offline] combo); single: 8 | [offline] We're rehearsing a presentation: one per |
| restricted | quiet | 0.0 | 0% | 100% | 1.00 | — | 0/2 | 3+7 ([offline] combo); single: 8 | [offline] A quiet reading corner in the evening; n |
| restricted | quiet | 0.7 | 0% | 100% | 1.00 | — | 0/2 | 3+7 ([offline] combo); single: 8 | [offline] A quiet reading corner in the evening; n |
| free | assembly | 0.0 | 0% | 100% | 1.00 | — | 0/2 | 1+8 ([offline] combo); single: 2 | [offline] Two of us are assembling a robot arm at  |
| free | assembly | 0.7 | 0% | 100% | 1.00 | — | 0/2 | 1+8 ([offline] combo); single: 2 | [offline] Two of us are assembling a robot arm at  |
| free | guest | 0.0 | 0% | 100% | 1.00 | — | 0/2 | 3+4 ([offline] combo) | [offline] I'm expecting a guest to arrive at the s |
| free | guest | 0.7 | 0% | 100% | 1.00 | — | 0/2 | 3+4 ([offline] combo) | [offline] I'm expecting a guest to arrive at the s |
| free | solo-work | 0.0 | 0% | 100% | 1.00 | not:2,then:2 | 0/2 | then(7→8) not(5) ([offline] sequence); single: 5 | [offline] I'm working alone on my thesis. Only peo |
| free | solo-work | 0.7 | 0% | 100% | 1.00 | not:2,then:2 | 0/2 | then(7→8) not(5) ([offline] sequence); single: 5 | [offline] I'm working alone on my thesis. Only peo |
| free | lunch | 0.0 | 0% | 100% | 1.00 | not:2,then:2 | 0/2 | then(6→11) not(1) ([offline] sequence); single: 1 | [offline] It's lunch break; people drift in and ou |
| free | lunch | 0.7 | 0% | 100% | 1.00 | not:2,then:2 | 0/2 | then(6→11) not(1) ([offline] sequence); single: 1 | [offline] It's lunch break; people drift in and ou |
| free | demo-day | 0.0 | 0% | 100% | 1.00 | not:2,then:2 | 0/2 | then(4→7) not(5) ([offline] sequence); single: 5 | [offline] Open-lab demo day: visitors walk around  |
| free | demo-day | 0.7 | 0% | 100% | 1.00 | not:2,then:2 | 0/2 | then(4→7) not(5) ([offline] sequence); single: 5 | [offline] Open-lab demo day: visitors walk around  |
| free | pair-prog | 0.0 | 0% | 100% | 1.00 | — | 0/2 | 4+11 ([offline] combo); single: 10 | [offline] My labmate and I are pair-programming at |
| free | pair-prog | 0.7 | 0% | 100% | 1.00 | — | 0/2 | 4+11 ([offline] combo); single: 10 | [offline] My labmate and I are pair-programming at |
| free | entrance | 0.0 | 0% | 100% | 1.00 | — | 0/2 | 8+9 ([offline] combo); single: 10 | [offline] Watch the entrance and tell me when some |
| free | entrance | 0.7 | 0% | 100% | 1.00 | — | 0/2 | 8+9 ([offline] combo); single: 10 | [offline] Watch the entrance and tell me when some |
| free | fragile | 0.0 | 0% | 100% | 1.00 | — | 0/2 | 6+10 ([offline] combo); single: 11 | [offline] I left a fragile prototype on the desk;  |
| free | fragile | 0.7 | 0% | 100% | 1.00 | — | 0/2 | 6+10 ([offline] combo); single: 11 | [offline] I left a fragile prototype on the desk;  |
| free | rehearsal | 0.0 | 0% | 100% | 1.00 | — | 0/2 | 5+10 ([offline] combo); single: 9 | [offline] We're rehearsing a presentation: one per |
| free | rehearsal | 0.7 | 0% | 100% | 1.00 | — | 0/2 | 5+10 ([offline] combo); single: 9 | [offline] We're rehearsing a presentation: one per |
| free | quiet | 0.0 | 0% | 100% | 1.00 | not:2,then:2 | 0/2 | then(9→11) not(10) ([offline] sequence); single: 10 | [offline] A quiet reading corner in the evening; n |
| free | quiet | 0.7 | 0% | 100% | 1.00 | not:2,then:2 | 0/2 | then(9→11) not(10) ([offline] sequence); single: 10 | [offline] A quiet reading corner in the evening; n |

## Coverage probe — 'missing' relations named by the model

None named — empirical support that the 10-row vocabulary covers these scenarios.

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
