---
name: Career Platform resume site
description: A resume set as a strategy-firm document, with action titles over captioned, sourced exhibits.
colors:
  paper: "#ffffff"
  wash: "#f2f5f8"
  ink: "#0b1f3a"
  ink-soft: "#34475e"
  muted: "#566679"
  rule: "#cdd5df"
  rule-strong: "#0b1f3a"
  data: "#0b7a77"
  data-soft: "#d5ecea"
  bar-other: "#76869a"
  action: "#c2410c"
  action-hover: "#9a3412"
  note-wash: "#fff4e5"
  note-rule: "#e2b071"
  note-ink: "#6b3300"
typography:
  display:
    fontFamily: "Archivo, Helvetica Neue, Arial, sans-serif"
    fontSize: "clamp(2.25rem, 1.3rem + 3.6vw, 4.25rem)"
    fontWeight: 760
    lineHeight: 1.02
    letterSpacing: "-0.025em"
    fontVariation: "'wdth' 82"
  headline:
    fontFamily: "Archivo, Helvetica Neue, Arial, sans-serif"
    fontSize: "clamp(1.75rem, 1.25rem + 1.9vw, 2.625rem)"
    fontWeight: 720
    lineHeight: 1.12
    letterSpacing: "-0.015em"
    fontVariation: "'wdth' 85"
  finding:
    fontFamily: "Archivo, Helvetica Neue, Arial, sans-serif"
    fontSize: "clamp(1.375rem, 1.1rem + 0.9vw, 1.75rem)"
    fontWeight: 400
    lineHeight: 1.3
    fontVariation: "'wdth' 100"
  title:
    fontFamily: "Archivo, Helvetica Neue, Arial, sans-serif"
    fontSize: "1.25rem"
    fontWeight: 680
    lineHeight: 1.12
    fontVariation: "'wdth' 92"
  lede:
    fontFamily: "Archivo, Helvetica Neue, Arial, sans-serif"
    fontSize: "1.25rem"
    fontWeight: 400
    lineHeight: 1.5
    fontVariation: "'wdth' 100"
  body:
    fontFamily: "Archivo, Helvetica Neue, Arial, sans-serif"
    fontSize: "1.0625rem"
    fontWeight: 400
    lineHeight: 1.55
    fontVariation: "'wdth' 100"
  label:
    fontFamily: "Archivo, Helvetica Neue, Arial, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 680
    lineHeight: 1.55
  meta:
    fontFamily: "Archivo, Helvetica Neue, Arial, sans-serif"
    fontSize: "0.9375rem"
    fontWeight: 400
    lineHeight: 1.55
    fontFeature: "'tnum' 1, 'lnum' 1"
  axis:
    fontFamily: "Archivo, Helvetica Neue, Arial, sans-serif"
    fontSize: "0.8125rem"
    fontWeight: 400
    lineHeight: 1.3
    fontFeature: "'tnum' 1"
rounded:
  bar: "1px"
  focus: "2px"
  control: "4px"
spacing:
  "1": "0.25rem"
  "2": "0.5rem"
  "3": "0.75rem"
  "4": "1rem"
  "5": "1.5rem"
  "6": "2rem"
  "7": "3rem"
  "8": "4.5rem"
  "9": "6rem"
  shell: "76rem"
  label-width: "16rem"
  column-gap: "2rem"
  gutter: "clamp(1rem, 4vw, 2.5rem)"
components:
  button-primary:
    backgroundColor: "{colors.action}"
    textColor: "{colors.paper}"
    rounded: "{rounded.control}"
    padding: "0.5rem 1.5rem"
    height: "2.75rem"
  button-primary-hover:
    backgroundColor: "{colors.action-hover}"
    textColor: "{colors.paper}"
  button-quiet:
    backgroundColor: "transparent"
    textColor: "{colors.action}"
    rounded: "{rounded.control}"
    padding: "0.5rem 1.5rem"
    height: "2.75rem"
  button-quiet-hover:
    backgroundColor: "{colors.wash}"
    textColor: "{colors.action-hover}"
  nav-link:
    textColor: "{colors.ink-soft}"
    padding: "0.5rem 0"
  nav-link-current:
    textColor: "{colors.ink}"
  exhibit:
    backgroundColor: "{colors.wash}"
    textColor: "{colors.ink}"
    padding: "1.5rem 1.5rem 1rem"
  exhibit-source:
    textColor: "{colors.muted}"
    typography: "{typography.label}"
  timeline-bar-featured:
    backgroundColor: "{colors.data}"
    rounded: "{rounded.bar}"
    height: "1.125rem"
  timeline-bar-other:
    backgroundColor: "{colors.bar-other}"
    rounded: "{rounded.bar}"
    height: "1.125rem"
  status-note:
    backgroundColor: "{colors.note-wash}"
    textColor: "{colors.note-ink}"
    rounded: "{rounded.control}"
    padding: "0.75rem 1rem"
---

# Design System: Career Platform resume site

## Overview

**Creative North Star: "The Strategy Deck"**

The site reads like a document from a strategy firm. Each section opens with an action title, which is a full sentence stating a finding computed from the database. The evidence sits under it as an exhibit with a caption and a source line naming the records it came from. The reader should be able to skim the titles alone and still get the argument.

The page is white paper with deep navy ink, cool gray hairline rules, and a pale wash behind each exhibit. Two colors have narrow jobs. Teal marks emphasis inside exhibits, and burnt orange marks the things you can press. Archivo carries every word, and its width axis does the work that a second typeface would do elsewhere. Titles run semi-condensed and heavy, while body text runs at regular width.

Density is moderate and editorial. Rules separate rows, a 3px navy rule closes the title block, and nothing floats. The build rejects the old default look: system-ui type, slate palette, cards, pills, and a name hero over equal tiles.

**Key Characteristics:**
- Computed action titles, never labels, on every section that has data
- Exhibits with a caption on top and a "Source:" line at the foot
- One shared first column for dates, timeline labels, and figures
- Archivo width contrast, with titles at wdth 82 to 92 and body at 100
- Tabular, lining figures wherever numbers align
- Hairline rules and a flat wash, with no cards, shadows, or pills

## Colors

A cool navy-on-white document palette with one teal data ink and one burnt-orange action color.

### Primary
- **Burnt Orange Action** (action): The only filled color on the page. It appears on buttons and inline links and nowhere else. Hover darkens to **Rust** (action-hover). It is also the page `accent-color`.

### Secondary
- **Exhibit Teal** (data): Emphasis inside exhibits. It colors featured timeline bars, their key swatch, and metric figures set in bold. **Pale Teal** (data-soft) is the text-selection highlight.

### Tertiary
- **Advisory Amber** (note-wash, note-rule, note-ink): The status note for outage and fallback messages.

### Neutral
- **Paper** (paper): Page background and button text.
- **Exhibit Wash** (wash): The flat fill behind every exhibit.
- **Deep Navy Ink** (ink): Headings, body text, the focus ring, and the "today" marker. Rule-strong carries the same navy for the 3px title rule, the exhibit top edge, and skill-column heads.
- **Slate Ink** (ink-soft): Bylines, ledes, record meta, nav links at rest.
- **Muted Slate** (muted): Dates, source lines, axis ticks, and dt labels. It holds 5.37:1 on the wash.
- **Hairline Gray** (rule): Row dividers, byline dividers, gridlines, and header and footer borders.
- **Bar Gray** (bar-other): Non-featured timeline bars and their key swatch.

### Named Rules
**The Pressable Orange Rule.** Burnt orange goes only on things you can press, such as buttons, inline links, and link hovers. A heading, figure, or rule in orange is a bug.

**The Teal Lives In Exhibits Rule.** Teal marks emphasis inside an exhibit or a result line, and it never decorates chrome, headings, or links.

**The Ink Carries Structure Rule.** Text and rules are navy or its softer steps. Hierarchy comes from weight, width, and size, not from extra hues.

## Typography

**Display Font:** Archivo variable (wdth 62 to 125, wght 100 to 900, from Google Fonts), with Helvetica Neue and Arial as fallbacks
**Body Font:** The same Archivo, at regular width

**Character:** One family with two voices. The condensed heavy cut reads like a consulting slide title, and the regular width reads like a report paragraph.

### Hierarchy
- **Display** (760, wdth 82, step 4 clamp, 1.02): The home action title, capped at 48rem. Headlines over 72 characters drop to step 3 with the max width at 56rem.
- **Headline** (720, wdth 85, step 3 clamp, 1.12): Section action titles, capped at 30ch. Inner page h1s use step 3 at weight 760, wdth 82, and line height 1.02.
- **Finding** (400, step 2 clamp, 1.3): Executive-summary statements, capped at 52ch, with the metric inline in teal.
- **Title** (680, wdth 92, 1.25rem): Record titles for roles, projects, and schools.
- **Lede** (400, 1.25rem, 1.5): Summaries and the byline. Both drop to body size under 48rem.
- **Body** (400, wdth 100, 1.0625rem, 1.55): Running text, with paragraphs capped at 68ch.
- **Label** (680, 0.875rem): Exhibit captions. Source lines and dt labels use the same size in muted slate.
- **Meta** (0.9375rem, tabular): Record periods, nav links, tags, and timeline role names.
- **Axis** (0.8125rem, tabular): Timeline ticks and timeline meta lines.

### Named Rules
**The Width Contrast Rule.** Titles use the width axis between 82 and 92, and running text stays at 100. Never add a second family to get contrast.

**The Aligned Figures Rule.** Any number that sits in a column or a run of dates uses tabular figures. Metric figures use tabular and lining figures together.

## Layout

The page is one centered shell, 76rem wide, with a fluid gutter. Header, main, and footer sit in a three-row grid so the footer stays at the bottom on short pages.

Every section follows the same grammar. A computed action title comes first, with an optional text link at right in the section head. The exhibit or record list follows. Sections are spaced 4.5rem apart, and items inside a section are spaced 1.5rem apart.

Records, case tables, and detail tables share one first column, the label width of 16rem, then a 2rem gap and the content. Exhibits are padded by 1.5rem, so content inside them uses an exhibit label that is 1.5rem narrower and still lands on the same left edge. Between 48rem and 64rem the label width tightens to 11rem. Under 48rem every two-column row stacks into one column and the header nav wraps below the name.

The career timeline keeps its own label column. It matches the exhibit label up to 64rem and widens to 20rem above that, because role titles plus dates need more room than a date column.

Skills sit in auto-fit columns with a 10.5rem minimum on the home page and 18rem on the skills page. Executive-summary findings get a 14rem right-aligned source column from 48rem up.

**The Shared Edge Rule.** Dates, timeline labels, and figures all start on one first column, set by the label width. A new row type takes that column or spans the full width. It never invents a third edge.

**The Omit Empty Rule.** A section, field, or label with no data is not rendered. There are no "Not provided" placeholders and no headings over empty lists. The fallback profile shows only the title block.

## Elevation & Depth

The system is flat. No element casts a shadow. Depth comes from the exhibit wash against white paper and from rule weight, with 1px hairlines between rows and a 1px navy line along each exhibit's top edge. A 3px navy rule closes the title block, page heads, and the closing block.

**The Flat Paper Rule.** No shadows, glows, or blur anywhere. If something needs separation, it gets a rule or the wash.

## Shapes

Corners are nearly square. Buttons and the status note take a 4px radius, timeline bars take 1px, and the focus ring takes 2px. Rules are the main form language. Hairlines divide rows and byline items, and the navy rule weight marks a document boundary. Key swatches are small flat rectangles, 1.25rem by 0.5rem, and the "today" marker is a 2px dotted navy line.

## Components

### Buttons
Solid and plain, like the one call to action on a slide.
- **Shape:** Slightly squared corners (4px), at least 2.75rem tall, with a 0.5rem by 1.5rem pad and weight 620.
- **Primary:** Burnt orange fill and border with paper text. External links carry an inline SVG arrow at 16px and a visually hidden "(opens in a new tab)".
- **Hover / Focus:** The fill and border shift to rust over 160ms on the ease-out curve. Focus shows a 3px navy outline with a 3px offset.
- **Quiet:** Transparent fill with an orange border and text. Hover fills with the amber wash. It serves as the secondary project link.

### Text links
Inline links are burnt orange, underlined at 0.07em with a 0.2em offset. Hover darkens to rust and thickens the underline to 0.12em. Section-head links ("All projects") use weight 600 and do not wrap. Record titles that link stay navy with a gray underline and turn orange on hover.

### Navigation
The candidate's name sits at top left (step 1, weight 760, wdth 88). Nav links sit at right in slate ink at 0.9375rem and weight 520. Hover turns them navy with a gray 2px underline. The current page is navy with a navy 2px underline. Under 48rem the nav drops below the name at 0.875rem.

### Exhibit
The signature container. It has a pale wash fill, a 1px navy top edge, and a 1.5rem pad. A caption in bold label type sits at top, with an optional key at right. A "Source:" line in muted label type sits at the foot above a hairline, naming the records and, where it applies, the count (n=).

### Record row
A two-column row of a period in muted tabular meta, then a body of title, meta line, and one result or summary. Rows divide on hairlines. Every role row carries a result or summary, so no row is bare.

### Career timeline
A Gantt drawn to scale from real start and end dates, inside an exhibit. Featured roles are teal and others are bar gray. Year gridlines are hairlines, and a dotted navy line marks today. Each label links to the role on the experience page.

Bars are visible by default. When JavaScript runs and reduced motion is not requested, each bar draws once from the left as the exhibit enters view, using a 900ms ease-out with a 70ms stagger per row. Under reduced motion or without JavaScript the bars render at full length.

### Status note
A full-width amber note with a 4px radius and an amber hairline, used for outage and fallback messages. It is announced with role="status".

### Static assets
Stylesheet and script URLs carry a 10-character SHA-256 content hash of the two files as a query string, so each deploy busts the browser cache.

## Do's and Don'ts

### Do:
- Do write each section title as a sentence computed from records, such as "4 measured results from 4 organizations."
- Do put evidence in an exhibit with a caption and a "Source:" line that names the records.
- Do start every row on the shared label column, and give the timeline its own 20rem column at 64rem and up.
- Do set metrics in bold teal with tabular, lining figures.
- Do keep titles at wdth 82 to 92 and body text at wdth 100.
- Do omit any section, field, or label whose data is empty.
- Do keep the timeline visible without JavaScript, draw it once, and keep it static under reduced motion.
- Do version static files by content hash.

### Don't:
- Don't use burnt orange on anything that can't be pressed.
- Don't use teal outside an exhibit or a result line.
- Don't use cards, drop shadows, or rounded panels. Use rules and the wash.
- Don't render skills as pills or tags. Use plain lists under a navy-ruled category head.
- Don't put an eyebrow or kicker label above a heading. The action title opens the section.
- Don't type derived numbers, such as counts or year spans, into templates. Compute them from records.
- Don't add a second typeface or swap back to system-ui.
