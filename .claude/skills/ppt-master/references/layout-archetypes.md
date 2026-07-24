# Layout Archetypes — fill-in SVG skeletons (SPEED PATH)

> **What this is.** Ready-to-instantiate page skeletons with the geometry already
> solved, for the **free-design flat** route on a **1280×720 (PPT 16:9)** canvas.
> The first instance of each new layout pattern is the expensive part of a deck;
> these remove the per-pattern geometry re-derivation. Copy a block, fill the
> `{{TOKENS}}`, delete unused rows.
>
> **These encode geometry, NOT skin.** Re-skin every color/font from `spec_lock.md`
> (tokens below name the role, e.g. `{{ACCENT}}`, `{{TITLE_STACK}}`). Sizes shown
> are the `balanced` ramp (body 24); if the deck's `body` differs, scale the ramp.
> **Run `text_fit.py` ONCE per page as a `--batch` page object** (blocks +
> obstacles; §4 of the cheat-card) covering the filled risk lines — not one
> call per line, and skip trivially-short lines. For another canvas size,
> scale coordinates from the `viewBox`.
> These are authoring aids you hand-edit — never generate pages from them by script.

Token legend (pull HEX/stacks from `spec_lock.md`): `{{BG}}` bg · `{{PRIMARY}}`
· `{{ACCENT}}` · `{{TEXT}}` body text · `{{TEXT_2}}` secondary · `{{TEXT_3}}`
tertiary · `{{BORDER}}` hairline · `{{TITLE_STACK}}` title_family ·
`{{BODY_STACK}}` font_family. Sizes: title 40, subtitle 30, lead 28, subheading
26, body 24, annotation 18, kicker 15, footnote 14, cover_title 72, hero 46.

---

## 0. Shared chrome (header + footer) — paste into every `content` page

```xml
<g id="header">
  <text x="72" y="88" font-family="{{TITLE_STACK}}" font-size="15" font-weight="600" letter-spacing="2" fill="{{ACCENT}}">{{KICKER}}</text>
  <text x="72" y="140" font-family="{{TITLE_STACK}}" font-size="40" font-weight="600" fill="{{PRIMARY}}">{{TITLE}}</text>
  <line x1="72" y1="166" x2="1208" y2="166" stroke="{{BORDER}}" stroke-width="1.5"/>
</g>
<!-- ... content groups (y 196–660) ... -->
<g id="footer">
  <line x1="72" y1="680" x2="1208" y2="680" stroke="{{BORDER}}" stroke-width="1"/>
  <text x="72" y="702" font-family="{{BODY_STACK}}" font-size="14" fill="{{TEXT_3}}">{{DECK_LABEL}}</text>
  <text x="1208" y="702" text-anchor="end" font-family="{{BODY_STACK}}" font-size="14" fill="{{TEXT_3}}">{{NN}} / {{TOTAL}}</text>
</g>
```
Content zone: **x 72 → 1208 (width 1136), y ~196 → 660.** Safe margins 72 / 56.

---

## A. Cover / Closing poster (`anchor`, role `cover` / `ending`)

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" data-pptx-page-role="cover">
  <rect x="0" y="0" width="1280" height="720" fill="{{BG}}"/>
  <g id="kicker">
    <rect x="72" y="112" width="52" height="4" fill="{{ACCENT}}"/>
    <text x="72" y="168" font-family="{{TITLE_STACK}}" font-size="18" font-weight="600" letter-spacing="3" fill="{{ACCENT}}">{{KICKER}}</text>
  </g>
  <g id="headline">
    <text x="70" y="336" font-family="{{TITLE_STACK}}" font-size="72" font-weight="700" fill="{{PRIMARY}}">{{LINE_1}}</text>
    <text x="70" y="432" font-family="{{TITLE_STACK}}" font-size="72" font-weight="700" fill="{{ACCENT}}">{{LINE_2}}</text>
  </g>
  <g id="subhead">
    <text x="72" y="508" font-family="{{BODY_STACK}}" font-size="30" font-weight="500" fill="{{TEXT_2}}">{{SUBTITLE}}</text>
  </g>
  <g id="meta">
    <line x1="72" y1="628" x2="1208" y2="628" stroke="{{BORDER}}" stroke-width="1.5"/>
    <text x="72" y="670" font-family="{{BODY_STACK}}" font-size="18" fill="{{TEXT_2}}">{{META_LEFT}}</text>
    <text x="1208" y="670" text-anchor="end" font-family="{{BODY_STACK}}" font-size="18" fill="{{TEXT_3}}">{{META_RIGHT}}</text>
  </g>
</svg>
```
Cover title 72px fits ≤ ~15 CJK chars per line before x=1208 — check with `text_fit.py "…" -s 72 --x 70`. Closing = same skeleton with role `ending` and an action line in `meta`.

---

## B. Numbered list / agenda (`dense` or `toc`) — N rows with hairlines

Each row: hairline above, accent index, label, optional right descriptor. Row pitch ~86px (5 rows) or ~96px (≤4 rows). Template for row N at baseline `Y` (hairline at `Y−50`):

```xml
<g id="item-{{i}}">
  <line x1="72" y1="{{Y-50}}" x2="1208" y2="{{Y-50}}" stroke="{{BORDER}}" stroke-width="1"/>
  <text x="72" y="{{Y}}" font-family="{{TITLE_STACK}}" font-size="26" font-weight="600" fill="{{ACCENT}}">{{NN}}</text>
  <text x="150" y="{{Y}}" font-family="{{TITLE_STACK}}" font-size="26" font-weight="600" fill="{{PRIMARY}}">{{LABEL}}</text>
  <text x="1208" y="{{Y}}" text-anchor="end" font-family="{{BODY_STACK}}" font-size="18" fill="{{TEXT_2}}">{{DESCRIPTOR}}</text>
</g>
```
5-row baselines: 256, 342, 428, 514, 600 (final hairline 636). 3-row baselines: 384, 480, 576.

---

## C. Two-column activity (`dense`) — concept left, 3 example rows right

Left panel x 72–470; vertical divider at x=516; right column x 560–1208 (**available 648** for body, verify with `text_fit.py -s 24 --x 560`).

```xml
<g id="concept">
  <use data-icon="{{ICON}}" x="72" y="212" width="56" height="56" fill="{{ACCENT}}"/>
  <text x="72" y="332" font-family="{{TITLE_STACK}}" font-size="26" font-weight="600" fill="{{PRIMARY}}">{{AREA_LABEL}}</text>
  <text x="72" y="392" font-family="{{BODY_STACK}}" font-size="24" fill="{{TEXT}}">{{DEF_L1}}<tspan x="72" dy="38">{{DEF_L2}}</tspan><tspan x="72" dy="38">{{DEF_L3}}</tspan></text>
</g>
<g id="divider-vert"><line x1="516" y1="196" x2="516" y2="648" stroke="{{BORDER}}" stroke-width="1.5"/></g>
<g id="ex-1">
  <line x1="560" y1="206" x2="1208" y2="206" stroke="{{BORDER}}" stroke-width="1"/>
  <text x="560" y="250" font-family="{{TITLE_STACK}}" font-size="24" font-weight="600" fill="{{ACCENT}}">{{ROW_LABEL_1}}</text>
  <text x="560" y="290" font-family="{{BODY_STACK}}" font-size="24" fill="{{TEXT}}">{{ROW_BODY_1}}</text>
</g>
<!-- ex-2: hairline y=344, label y=388, body y=428 -->
<!-- ex-3: hairline y=482, label y=526, body y=566, closing hairline y=612 -->
```
Parallel-exposition tip (instructional mode): reuse the same three `{{ROW_LABEL}}` across sibling activity pages (e.g. 이렇게 말하면 → 이렇게 나온다 → 교사의 역할). Left `{{DEF}}` ≈ 3 lines at width ~400 (~16 CJK/line). Right body lines aim ≤ 27 CJK to stay one line.

> **Column-wrap gate note.** This archetype's `divider-vert` at x=516 spans y 196→648, so it bounds the **left** column's wrapped `{{DEF}}` lines (the checker sees the divider in their y-band → no false wrap warning). The **right** column has no shape on its right, so wrapped right-body blocks would be measured against the full canvas and flagged — keep right-column bodies to **one line each**, or add a right-edge rule. Pre-confirm any intended wrap with text_fit's checker-parity mode: `{"lines":[…],"font_size":24,"x":<x>,"right_bound":<bound>}`.

---

## D. Horizontal steps (`dense`) — 2–4 columns with arrows

3 columns at x 72 / 490 / 908 (each ~330 wide → per-column `--zone 330`); arrows between at x 430 / 848. Optional `{{LEAD}}` line at y≈238.

```xml
<g id="step-1">
  <line x1="72" y1="320" x2="402" y2="320" stroke="{{BORDER}}" stroke-width="1"/>
  <text x="72" y="404" font-family="{{TITLE_STACK}}" font-size="46" font-weight="700" fill="{{ACCENT}}">01</text>
  <text x="72" y="466" font-family="{{TITLE_STACK}}" font-size="26" font-weight="600" fill="{{PRIMARY}}">{{STEP_LABEL}}</text>
  <text x="72" y="512" font-family="{{BODY_STACK}}" font-size="24" fill="{{TEXT}}">{{STEP_L1}}<tspan x="72" dy="36">{{STEP_L2}}</tspan></text>
</g>
<g id="arrow-1"><use data-icon="{{ARROW_ICON}}" x="430" y="380" width="36" height="36" fill="{{TEXT_3}}"/></g>
<!-- step-2: x=490 (rule 490→820), arrow-2 x=848; step-3: x=908 (rule 908→1208) -->
```
Highlight the final/active step's rule with `stroke="{{ACCENT}}" stroke-width="2"`.

> **Column-wrap gate note.** The per-step top rules sit *above* the step body (different y-band), so they do **not** bound a wrapped body — the checker measures the body against the full canvas and flags a 2-line body that fits full-width. So keep each step's body to **one line** (shorten the copy), OR bound the columns with faint full-height vertical dividers between them spanning the body y-band. Confirm with text_fit checker-parity mode before writing.

---

## E. Breathing pull-quote (`breathing`) — hero + principle rows (NO cards)

```xml
<g id="kicker">
  <use data-icon="{{ICON}}" x="72" y="96" width="34" height="34" fill="{{ACCENT}}"/>
  <text x="118" y="122" font-family="{{TITLE_STACK}}" font-size="18" font-weight="600" letter-spacing="2" fill="{{ACCENT}}">{{KICKER}}</text>
</g>
<g id="pullquote">
  <text x="72" y="264" font-family="{{TITLE_STACK}}" font-size="52" font-weight="700" fill="{{PRIMARY}}">{{QUOTE_L1}}</text>
  <text x="72" y="340" font-family="{{TITLE_STACK}}" font-size="52" font-weight="700" fill="{{ACCENT}}">{{QUOTE_L2}}</text>
  <rect x="74" y="378" width="72" height="4" fill="{{ACCENT}}"/>
  <text x="72" y="430" font-family="{{BODY_STACK}}" font-size="24" fill="{{TEXT_2}}">{{STANDFIRST}}</text>
</g>
<g id="principle-1">
  <line x1="72" y1="486" x2="1208" y2="486" stroke="{{BORDER}}" stroke-width="1"/>
  <text x="72" y="530" font-family="{{TITLE_STACK}}" font-size="24" font-weight="600" fill="{{ACCENT}}">{{P_LABEL_1}}</text>
  <text x="212" y="530" font-family="{{BODY_STACK}}" font-size="24" fill="{{TEXT}}">{{P_BODY_1}}</text>
</g>
<!-- principle-2: hairline 562, text 606 ; principle-3: hairline 638, text 682 (keep last row ≤ y 700) -->
```
Pull-quote 52px is a breathing hero (in-band feature size, ~2.2× body). Keep principle bodies ≤ ~40 CJK at x=212 (verify `text_fit.py -s 24 --x 212`).

---

**Do NOT** default every deck to these. They are starting geometry for the common
free-design editorial patterns; break the grid, combine, or invent per the page's
`page_rhythm` and the locked visual style. The value is skipping geometry math on
repeat patterns — not turning every deck into the same five layouts.
