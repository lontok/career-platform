---
target: app/templates/home.html
total_score: 18
max_score: 32
na_heuristics: 7,10
p0_count: 0
p1_count: 3
target_identity: "file:/Users/greglontok/Library/CloudStorage/GoogleDrive-greg@lontok.com/My Drive/GitHub/career-platform-rehearsal/app/templates/home.html"
target_fingerprint: "sha256:4585deed55dc61f0eefc0cb88378e41dd9e6017701dc426d1c95a4ca8e343494"
target_path: /Users/greglontok/Library/CloudStorage/GoogleDrive-greg@lontok.com/My Drive/GitHub/career-platform-rehearsal/app/templates/home.html
timestamp: 2026-10-06T17-15-02Z
slug: app-templates-home-html
closed: true
---
Method: dual-agent (A: design review sub-agent, B: detector and overlay sub-agent)

## Design health score
| # | Heuristic | Score | Key issue |
|---|---|---|---|
| 1 | Visibility of system status | 3 | Current-page nav marker and outage banner work. Banner doesn't say LinkedIn still works. |
| 2 | Match system and real world | 2 | "Career Platform" header brand reads like a job board. "Featured Projects" shows with zero projects. |
| 3 | User control and freedom | 3 | External links open a new tab with no cue. |
| 4 | Consistency and standards | 2 | Home cards drop dates /experience shows. Mixed heading case. h1 offset differs from inner pages. |
| 5 | Error prevention | 2 | No guards on optional fields. Empty labels and sections ship. |
| 6 | Recognition rather than recall | 2 | No dates or tenure on home. |
| 7 | Flexibility and efficiency | n/a | One-pass persuade page. |
| 8 | Aesthetic and minimalist design | 2 | Nine identical cards dominate, no focal point. |
| 9 | Error recovery | 2 | Outage nav shrinks silently, deep links hit generic error. |
| 10 | Help and documentation | n/a | Static persuade page. |
| Total | | 18/32 | Acceptable (56%) |

## Design specificity verdict
Category-interchangeable: system-ui, slate palette, browser-default heading sizes, white low-shadow cards. Impact summary is the only on-thesis element and doesn't render with 0 metrics. Detector: CLI 0 findings but couldn't resolve the Jinja url_for stylesheet, so color rules were incomplete. Browser overlay: "No anti-patterns found" on /, outage page, /experience, /skills. No false positives.

## Priority issues
- [P1] Empty fields and sections leak: empty Target roles dd (home.html:18-21), empty summary p (:12), empty p in every experience card (:66), Featured Projects heading and empty grid with 0 projects (:70-81), "MS in " risk (:101). Fails README release check and Principle 3. Fix with {% if %} guards and seed-level required fields. Command: harden.
- [P1] No value statement in first 5 seconds: headline under name at 18px, target roles as labeled dl, single 61x19 LinkedIn link. Lead with headline/summary at display size, roles + LA on one line, primary contact pair with 44px targets, move outage banner. Commands: bolder, layout.
- [P1] Evidence section is job titles with no evidence: all 7 experiences, no dates, no accomplishments, inverted disclosure. Show 2-3 roles with dates and top metric, group LMU progression, add featured flag. Command: distill.
- [P2] Generic visual system, platform outranks candidate: default type, palette, cards, "Career Platform" identity. Candidate name as identity, type scale, tokens, distinct metric treatment. Commands: typeset, colorize.
- [P2] Focus ring #ffbf47 about 1.6:1 (fails WCAG 1.4.11), mobile section-heading touches cards, floating footer on short pages. Two-tone ring, margin, sticky-footer grid. Command: polish.

## Persona red flags
Recruiter: no "analytics" above the fold, no dates or metrics, marketing-only skills, no prominent contact. Casey: 158px header, first card at ~597px, 61x19 tap target, 2727px of cards. Riley: unbounded experiences, skills and impact list, orphan projects heading, outage deep links dead-end. Jordan: "Career Platform" reads as job board, outage nav unexplained.

## Minor observations
.eyebrow under h1, mixed heading case, favicon 404, repeated "Los Angeles, CA", footer has no contact or year, literal em dash at home.html:48, /projects has no empty state.

## Questions to consider
- Why is the Impact summary optional when it carries the thesis? What leads when there are no metrics?
- Should seeding require a value-statement headline and target roles?
- Should the identity be the candidate, and should home curate rather than mirror /experience?
