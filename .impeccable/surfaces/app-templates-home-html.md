---
version: 1
slug: "app-templates-home-html"
primary_target: "app/templates/home.html"
related_targets: ["app/templates/base.html","app/static/styles.css"]
---

# Home page surface brief

## Scope and mode

Persuade. The public home page of the resume site, plus the shared base layout and stylesheet every inner page inherits. Whole-site reach: inner pages take the same exhibit grammar.

## Audience, job, action

A recruiter or hiring manager for LA analytics and technical roles, scanning many candidates on a laptop in office daylight. In seconds they should know the target roles, the value statement, and the evidence, and take the action: open LinkedIn or GitHub.

## Proof and constraints

Every claim comes from a published database record. Derived headline numbers (role counts, year spans) are computed from records, never typed into templates. Highlights come from accomplishment metrics. The design must degrade to the fallback profile cleanly and omit every empty field. Web fonts from a CDN and JavaScript are allowed. Failure order to avoid: template look, then flashy, then hard for students to copy.

## Direction contract

THESIS: The resume as a strategy-firm document. Every section opens with an action title, a full sentence stating a finding computed from the data, and the evidence sits under it as an exhibit with a caption and a source line naming the database records it came from. It refuses the name hero over equal cards and skill pills.

OWN-WORLD: White paper, deep navy ink, cool gray rules, and a pale exhibit wash. One teal data ink marks emphasis inside exhibits. One burnt-orange action color is reserved for links and buttons only. Archivo throughout, with width contrast: semi-condensed heavy action titles, regular-width body, tabular figures everywhere numbers align. Hairline rules, no cards, no shadows.

STORY: The visitor reads one sentence about what this person does for a business, sees the target roles and Los Angeles, scans an executive summary of measured results, reads a career timeline drawn to scale, and closes on a next-steps block with the contact actions.

FIRST VIEWPORT: Candidate name as the site identity at top left with quiet nav at right. Below, the headline set as the page's action title at display size across eight of twelve columns, then a byline of target roles and location, then the summary at reading size, then LinkedIn and GitHub as two burnt-orange buttons. The executive summary findings start inside the fold as full-width rows: statement at large reading size, metric inline in teal, organization as the source at right.

FORM: Consulting exhibit page, position 1 on the ordered list, taken as the pick card. Seed key 8a785448. Raises kept: action color only on what you can press; one strict column grid with tabular figures; no bare row, every role row carries a result or summary.

SIGNATURE: The career timeline exhibit, a Gantt drawn to scale from real start and end dates. Featured roles in teal, others in gray. Each bar draws once from the left as it enters view, visible by default without JavaScript and static under reduced motion.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance

## Open decisions

- Greg's local test profile has no summary, target roles, or metrics, so the executive summary will not render for it until that data is filled in.
