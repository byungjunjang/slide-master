# Mode: paper-explainer

Research-paper information transfer. Reconstruct one paper's question, design,
evidence, and interpretation for an audience that has not read the source. This
mode explains the paper; it is not an independent appraisal or a generic lesson
about the field.

---

## 1. Narrative skeleton

**Orient early**: within the first two content pages, state what the paper asked,
what it found, and why the answer matters. Keep this short; the evidence still
has to earn the conclusion in the pages that follow.

**Follow the paper's reasoning**: move through problem and knowledge gap →
research question → study design and measurements → result groups → the authors'
interpretation and supported scope. Reorder sections only when it makes the same
logic easier to understand.

**Methods earn results**: explain only the design, materials or participants,
conditions, comparators, measurements, and analysis choices needed to interpret
the displayed results. Split methods across pages when one diagram cannot remain
legible; do not compress them into a procedural wall of text.

**Evidence before paraphrase**: use the paper's figure, table, image sequence, or
an editable reconstruction as the page anchor. Pair it with a short reading guide:
what to compare, the relevant unit or condition, and what changed. Do not replace
a quantitative result with a decorative illustration.

**Group, then synthesize**: each result group answers one sub-question. After two
or more related result pages, add a concise synthesis only when the relationship
would otherwise be unclear.

**End at the source-supported boundary**: close with the authors' main answer,
the conditions under which it holds, and the practical or scientific meaning
supported by the paper. Do not add funding, conflict-of-interest, registration,
independent criticism, or discussion questions unless the user explicitly asks
or the source makes one essential to understanding the result.

Titles state the page's source-backed finding or function in plain language.
Avoid generic labels such as "Results 1" when the result itself can be named.

---

## 2. Page-structure tendencies

- Use a study-question or system map before detailed methods when the audience
  needs orientation.
- Give source figures and readable reconstructions enough width to preserve axes,
  units, legends, and comparison conditions.
- Use diagrams for procedure and causal sequence; use charts or tables for
  quantitative evidence; use generated figures for the mechanisms the source
  argues in prose but never draws cleanly (§3).
- Alternate evidence-heavy pages with short synthesis or orientation pages so
  the deck does not become a sequence of identical figure cards.

> Figure, chart, table, and diagram geometry lives in the shared templates and
> authoring references. This mode decides the explanatory order and the evidence
> each page must make readable.

---

## 3. Two figure families

A paper deck carries two kinds of picture doing different work. Plan both; one
does not substitute for the other.

| Family | Carries | §VIII `Acquire Via` |
|---|---|---|
| Generated mechanism figure | The causal story the source argues in prose but never draws cleanly — pathway, regulatory balance, dose relation, failure mode, competing regimes | `ai` |
| Source figure | The authors' own evidence and their own synthesis, as published | `user` |

**Default — a mechanism page earns a generated figure (may override when the
source already visualizes that mechanism well)**: when the paper argues a
mechanism across several paragraphs and the deck gives it a page, anchor that
page with a generated figure rather than text alone. One figure carries one
mechanism claim — never montage the paper into a single image.

**Hard rule**: a generated figure never stands in for a quantitative result.
Values, distributions, and comparisons stay in a chart, a table, or the source
figure itself.

**Forbidden — fabricated evidence**: invented data points, error bars, axes,
micrographs, gel lanes, scans, or specimen photos. Generated figures show
structure and causality; anything readable as this study's own measurement is
out.

> Note: these rows follow [`image-generator.md`](../image-generator.md) §4.2
> prompt depth — 500–1000+ words per row, never a short generic illustration
> brief.

### 3.1 Source-figure pages

**Trigger**: the source's own figures are in `images/` and the confirmed
`image_usage` includes `provided`.

**Default — a load-bearing source figure gets its own page (may override when a
later page has already superseded it)**: anchor the page with the figure at the
largest size the canvas allows, and set a reading guide beside it that names
where to look and in what order, in the deck's language. The guide orients; it
is not a translated caption.

**Hard rule — attribution on the page**: author, journal, year, figure number,
and license, on the page that shows the figure.

**Hard rule — no-derivatives licenses**: under `CC BY-NC-ND` or an equivalent ND
term, place the figure whole — no cropping, panel extraction, recoloring,
relabeling, or redrawing. List the row in `spec_lock.md images` with `| no-crop`
and record the constraint in `spec_lock.md forbidden` so the Executor cannot
undo it.

**Forbidden — the same figure twice**: a figure with its own page never also
appears as a thumbnail on a neighboring page. Replace the thumbnail with a
one-line bridge to the page that carries it.

### 3.2 Ordering the two families

**Default — explain, then show the source (may override when the source figure
is the simpler entry point)**: the generated figure that decomposes a mechanism
comes first; the authors' own figure follows as the recap of how they assembled
it. Close a result group with its source figure rather than opening on it.

> Note: a dense multi-panel source figure loses label legibility at page scale.
> Carrying what the shrunk labels cannot is the reading guide's job.

---

## 4. Fidelity boundary

| Preserve | May simplify |
|---|---|
| Direction, comparator, units, sample or condition, uncertainty, and result scope | Background detail that does not change the study question or result reading |
| The distinction between observed result and author interpretation | Repeated prose once the same point is visible in a figure or table |
| Separate result groups that answer different questions | Repeated methodological detail already established on an earlier page |
| The authors' figures as published — crop, panel set, labels, and color untouched | Which figures earn a page, and how much of a caption the deck restates in its own words |

Do not manufacture a critique, implication, recommendation, or contradiction to
make the deck feel more analytical. When the paper itself states a limitation or
uncertainty that changes how a result should be read, present it beside that
result or in the final boundary statement.

---

## 5. Speaker-notes register

Notes are optional and generated only when requested. If requested, explain what
to look at before interpreting a figure, define unfamiliar terms at first use,
and state transitions between question, method, result, and meaning without
adding claims beyond the source.

---

## 6. Page skeleton examples

Result page:

```
Title:  "Pattern geometry redirected droplets but did not eliminate splash"
Body:   readable source figure or reconstruction → comparison cue → result meaning
Close:  one sentence connecting the result to the paper's next question
```

Mechanism page (generated figure):

```
Title:  "Why the redirected droplet still carries momentum"
Body:   generated figure carrying one causal claim → the steps it makes visible
Close:  one sentence handing off to the evidence that tests the claim
```

Source-figure page (§3.1):

```
Title:  "The authors' own map of the two mechanisms"
Body:   source figure whole, at maximum size → reading guide (where to look, in
        what order) → author / journal / year / figure number / license
Close:  one sentence naming what this figure adds beyond the previous page
```
