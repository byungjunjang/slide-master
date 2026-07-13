# diagram-design — 업스트림 온보딩 / 독립 HTML 출력 플로우 (legacy)

> ⚠️ **Upstream context only — slide-svg에서는 실행하지 않는다.** 원본 diagram-design
> 라이브러리의 온보딩/HTML 출력 플로우 기록 보존용. 아래 본문은 이 스킬의 `SKILL.md`에서
> verbatim으로 옮겨온 업스트림 원문이며, 섹션 번호(§0 / §5 / §6 / §7 / §8 / §10 / §11)와
> 상호 참조(§9 taste gate 등)는 업스트림 SKILL.md 기준이다. slide-svg에서 다이어그램
> 슬라이드는 `/slide` Executor가 `slide/references/diagram-types.md`를 통해 네이티브
> DrawingML SVG로 그린다 — 이 문서의 스타일 가이드 게이트, URL 온보딩, HTML 템플릿/출력
> 플로우는 따르지 말 것.

---

**Upstream intro line:**

Create visual diagrams as self-contained HTML files with inline SVG and CSS, following an opinionated editorial design system.

---

## 0. First-time setup — style guide gate

**Before generating your first diagram in a new project, verify the style guide has been customized.**

Open [`references/style-guide.md`](references/style-guide.md) and check the default tokens. If they're still the shipped defaults (paper `#faf7f2`, ink `#1c1917`, accent `#b5523a` rust), **pause and ask the user**:

> *"This is your first Schematic in this project. The style guide is still at the default (neutral stone + rust). Do you want to customize it to match your brand first? Options: (a) run onboarding — I'll pull colors and fonts from your website, (b) paste your tokens manually, (c) proceed with the default for now."*

Then branch:
- **(a)** → follow [`references/onboarding.md`](references/onboarding.md) to fetch the site, extract palette + fonts, propose a diff, and write `style-guide.md`.
- **(b)** → accept the user's tokens and write them into `style-guide.md` under a new "Custom tokens" section.
- **(c)** → proceed; optionally remind the user they can run onboarding later.

**Once the style guide has been customized** (or the user explicitly opted for default), skip this gate on subsequent runs. A simple way to detect customization: if the `accent` value in `style-guide.md` differs from `#b5523a`, assume custom.

Don't silently ship default-skinned diagrams into a branded project — that's the failure mode this gate exists to prevent.

---

## 5. Design System

**The design system is skinnable.** All colors, typography, and tokens live in a single source of truth — [`references/style-guide.md`](references/style-guide.md). This file describes semantic roles (`paper`, `ink`, `muted`, `accent`, `link`, …). The default skin is a cool editorial palette (white-smoke paper, jet-black ink, atomic-tangerine accent, blue-slate muted, silver hairlines); to apply your own brand, either edit `style-guide.md` directly or run the URL-based flow described in [`references/onboarding.md`](references/onboarding.md).

> When specs below or in type references mention "ink", "accent", "muted", etc., look up the current hex value in `style-guide.md`.

### Semantic roles (at a glance)

| Role | Purpose |
|---|---|
| `paper`, `paper-2` | Page bg and container bg |
| `ink` | Primary text / stroke |
| `muted`, `soft` | Secondary text, default arrows, sublabels |
| `rule`, `rule-solid` | Hairline borders |
| `accent`, `accent-tint` | 1–2 focal elements per diagram |
| `link` | HTTP/API calls, external arrows |

**Focal rule:** `accent` goes on 1–2 elements max. Everything else is `ink` / `muted` / `soft`. If you're tempted to accent 4 things, you haven't decided what's focal yet.

### Node type → treatment

| Type | Fill | Stroke |
|---|---|---|
| **Focal** (1–2 max) | `accent-tint` | `accent` |
| **Backend / API / Step** | white | `ink` |
| **Store / State** | `ink @ 0.05` | `muted` |
| **External / Cloud** | `ink @ 0.03` | `ink @ 0.30` |
| **Input / User** | `muted @ 0.10` | `soft` |
| **Optional / Async** | `ink @ 0.02` | `ink @ 0.20` dashed `4,3` |
| **Security / Boundary** | `accent @ 0.05` | `accent @ 0.50` dashed `4,4` |

### Typography (summary — full spec in style-guide.md)

- **Title** — Instrument Serif, 1.75rem, 400 — H1 only
- **Node name** — Geist (sans), 12px, 600 — human-readable labels
- **Sublabel** — Geist Mono, 9px — ports, URLs, field types
- **Eyebrow / tag** — Geist Mono, 7–8px, uppercase, tracked — type tags, axis labels
- **Arrow label** — Geist Mono, 8px — annotation on arrows
- **Editorial aside** — Instrument Serif *italic*, 14px — callouts only

**Mono is for technical content.** Names are Geist sans. Page title is Instrument Serif. Italic Instrument Serif is reserved for annotation callouts. Never JetBrains Mono as a blanket "dev" font.

```html
<link href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Geist:wght@400;500;600&family=Geist+Mono:wght@400;500;600&display=swap" rel="stylesheet">
```

---

## 6. Core SVG Primitives

Universal building blocks. Type-specialized primitives (lifeline, activation bar, region) live in the relevant `references/type-*.md`. Optional primitives:
- Editorial callouts → [primitive-annotation.md](references/primitive-annotation.md)
- Hand-drawn variant → [primitive-sketchy.md](references/primitive-sketchy.md)

### Background

**Default: clean paper, no dot pattern.** Single `<rect>` filled with `paper`. Don't wrap the diagram in a secondary container background — the diagram sits directly on the page.

```svg
<rect width="100%" height="100%" fill="#f5f5f5"/>
```

**Optional: dotted paper variant.** When a long-form editorial diagram benefits from textured ground (essays, hero diagrams on a dedicated page), opt in by adding the `dots` pattern and a second rect:

```svg
<defs>
  <pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse">
    <circle cx="1" cy="1" r="0.9" fill="rgba(45,49,66,0.10)"/>
  </pattern>
</defs>
<rect width="100%" height="100%" fill="#f5f5f5"/>
<rect width="100%" height="100%" fill="url(#dots)" opacity="0.6"/>
```

Don't use the dot pattern when the diagram sits inside a product page, slide, or card — the texture compounds with surrounding chrome and reads as noise.

### Arrow markers (define all three, always)

```svg
<marker id="arrow" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
  <polygon points="0 0, 8 3, 0 6" fill="#4f5d75"/>
</marker>
<marker id="arrow-accent" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
  <polygon points="0 0, 8 3, 0 6" fill="#eb6c36"/>
</marker>
<marker id="arrow-link" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
  <polygon points="0 0, 8 3, 0 6" fill="#2e5aa8"/>
</marker>
```

| Arrow | Stroke | When |
|---|---|---|
| Default | muted `#4f5d75` | Internal, generic |
| Accent | coral `#eb6c36` | Primary / highlighted / headline |
| Link-blue | `#2e5aa8` | HTTP/API calls, external systems |
| Dashed | `stroke-dasharray="5,4"` + any color | Optional, passive, return, async |

**Draw arrows before boxes** so z-order puts lines behind nodes.

### Node box — full pattern

```svg
<!-- 1. Opaque paper mask — prevents arrows bleeding through transparent fills -->
<rect x="X" y="Y" width="W" height="H" rx="6" fill="#f5f5f5"/>
<!-- 2. Styled box -->
<rect x="X" y="Y" width="W" height="H" rx="6" fill="FILL" stroke="STROKE" stroke-width="1"/>
<!-- 3. Rectangular type tag (rx=2, NOT a pill) -->
<rect x="X+8" y="Y+6" width="28" height="12" rx="2" fill="transparent" stroke="STROKE@0.40" stroke-width="0.8"/>
<text x="X+22" y="Y+15" fill="STROKE@0.8" font-size="7" font-family="'Geist Mono', monospace"
      text-anchor="middle" letter-spacing="0.08em">API</text>
<!-- 4. Node name (Geist sans — human-readable) -->
<text x="CX" y="CY+2" fill="#2d3142" font-size="12" font-weight="600"
      font-family="'Geist', sans-serif" text-anchor="middle">Node Name</text>
<!-- 5. Technical sublabel (Geist Mono) -->
<text x="CX" y="CY+18" fill="#4f5d75" font-size="9"
      font-family="'Geist Mono', monospace" text-anchor="middle">tech:port</text>
```

### Arrow labels — always mask

Every arrow label needs an opaque rect behind it. Without one it bleeds through the line.

```svg
<rect x="MID_X-18" y="ARROW_Y-12" width="36" height="12" rx="2" fill="#f5f5f5"/>
<text x="MID_X" y="ARROW_Y-3" fill="#7a8399" font-size="8"
      font-family="'Geist Mono', monospace" text-anchor="middle" letter-spacing="0.06em">WRITE</text>
```

Rules: ≤14 characters, all-caps, centered on segment midpoint, 8–10px above line. Never `writing-mode` vertical.

### Legend — horizontal strip at the bottom

**Never put the legend inside the diagram area.** Place as a horizontal strip after all nodes, with a hairline separator:

```svg
<line x1="30" y1="LEGEND_Y-8" x2="VIEWBOX_W-30" y2="LEGEND_Y-8"
      stroke="rgba(45,49,66,0.10)" stroke-width="0.8"/>
<text x="30" y="LEGEND_Y+8" fill="#4f5d75" font-size="8" font-family="'Geist Mono', monospace"
      letter-spacing="0.14em">LEGEND</text>
<!-- Items — horizontal row, ~160px apart -->
```

Expand SVG `viewBox` height by ~60px.

---

## 7. Layout & Spacing — excerpt (standalone HTML page layout)

### Page layout

1. **Header** — eyebrow (Geist Mono), title (Instrument Serif), optional subtitle (Geist muted).
2. **Diagram container** — default: **clean, borderless**, no background — the SVG sits directly on the page paper. Optional *framed* variant (for card-heavy layouts or hero placements): `paper-2` bg + 1px `rule` border + 8px radius + `1.5rem` padding + `overflow-x: auto`.
3. **Summary cards** — 2–3 col grid with *varied* widths (e.g., `1.1fr 1fr 0.9fr`).
4. **Footer** — colophon in Geist Mono, muted, hairline top border.

---

## 8. Summary Card Pattern

Don't use 3 identical generic cards. Vary the treatment:

```html
<div class="card">
  <p class="eyebrow">SECTION LABEL</p>
  <div class="card-header">
    <span class="card-dot coral"></span>
    <h3>Card Title</h3>
  </div>
  <ul><li>Item</li></ul>
</div>
```

Rules:
- `background: #ffffff` (not paper — slight lift without shadow)
- `border: 1px solid rgba(45,49,66,0.12)`
- `border-radius: 6px`, `padding: 1.25rem`
- **No `box-shadow`**
- Card dots: 7px, `border-radius: 50%` — ink / muted / coral / link / soft variants

---

## 10. Templates & Variants

Every diagram ships in three variants (see `assets/`):

| Variant | File pattern | When to use |
|---|---|---|
| **Minimal light** (default) | `template.html`, `example-<type>.html` | Screenshot-ready. Diagram + title. Warm paper. |
| **Minimal dark** | `template-dark.html`, `example-<type>-dark.html` | Dark mode sites, slides, high-contrast posts. |
| **Full editorial** | `template-full.html`, `example-<type>-full.html` | Long-form posts where the diagram is the hero. |
| **Consultant special** (quadrant only) | `example-quadrant-consultant.html` | BCG/McKinsey-style 2×2 scenario matrix. Clinical sans-serif, white bg, bold blue double-ended axes, named scenario cells. See [type-quadrant.md](references/type-quadrant.md#consultant-special-2x2-scenario-matrix). |

**Sketchy variant** (optional, applied to any of the above) — see [primitive-sketchy.md](references/primitive-sketchy.md). SVG turbulence filter wobbles strokes for a hand-drawn feel. Good for essays, not for technical docs.

### To create a new diagram

1. Copy the variant closest to what you want (`template.html` for minimal, `template-full.html` for cards).
2. Load the matching `references/type-<name>.md` for layout conventions.
3. Replace the eyebrow, h1, and SVG body.
4. Run the §9 taste gate.

---

## 11. Output

Always produce a single self-contained `.html` file:
- Embedded CSS (no external except Google Fonts)
- Inline SVG (no external images)
- No JavaScript required

Renders correctly in any modern browser.
