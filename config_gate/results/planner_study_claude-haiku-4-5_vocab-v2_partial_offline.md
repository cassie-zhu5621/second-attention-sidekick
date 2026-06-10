# Planner preliminary study — claude-haiku-4-5 (OFFLINE PLUMBING RUN — numbers meaningless)

k=1 runs per scenario per temperature per grammar; context-only (no frame). Grammar arms: restricted, free.

| grammar | scenario | T | viol. | agree | Jaccard | ops beyond AND | missing | modal entries | why (modal) |
|---|---|---|---|---|---|---|---|---|---|
| restricted | guest | 0.0 | 0% | 100% | 1.00 | — | 0/1 | 6+10 ([offline] combo); single: 11 | [offline] I'm expecting a guest to arrive at the s |
| restricted | guest | 0.7 | 0% | 100% | 1.00 | — | 0/1 | 6+10 ([offline] combo); single: 11 | [offline] I'm expecting a guest to arrive at the s |
| free | guest | 0.0 | 0% | 100% | 1.00 | — | 0/1 | 3+4 ([offline] combo) | [offline] I'm expecting a guest to arrive at the s |
| free | guest | 0.7 | 0% | 100% | 1.00 | — | 0/1 | 3+4 ([offline] combo) | [offline] I'm expecting a guest to arrive at the s |

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
