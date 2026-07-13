# Style Guide

**The single source of truth for colors, typography, and tokens.** Every diagram draws from this — not from hex values inlined in other reference files. If you want to change the visual skin of Schematic, change this file.

**slide-svg skin: the active theme (Jangpm).** This file is pre-skinned to the active theme — monochrome neutrals + a single `#4633E3` indigo accent, Pretendard typography. In slide-svg the operative reference is the bridge `slide/references/diagram-types.md`; this style guide records the token values that bridge resolves to. **Do NOT run `onboarding.md`** (URL skin extraction) — the theme is locked via `/theme-init`, not by this skill.

---

## Tokens

### Semantic roles

Every token is referred to by **semantic role**, not by its hex value. Type references (`type-*.md`) and SKILL.md say `accent`, not `#f7591f`.

| Role | Purpose | Value (active theme: Jangpm) | theme-active.json token |
|---|---|---|---|
| `paper` | Page / slide background | `#FAFAF9` | `bg` |
| `paper-2` | Container / secondary fill | `#F5F5F4` | `surface-alt` |
| `ink` | Primary text, primary stroke | `#1A1A1A` | `text` |
| `muted` | Secondary text, default arrow stroke | `#6B7280` | `text-secondary` |
| `soft` | Sublabels, boundary labels | `#9CA3AF` | `text-tertiary` |
| `rule` | Hairline borders | `#E5E7EB` | `border` |
| `rule-solid` | Stronger borders, baselines | `#D4D4D4` | `border-strong` |
| `accent` | Focal / 1–2 max per diagram | `#4633E3` | `accent` |
| `accent-tint` | Fill for accent-bordered boxes | `#E8E5FC` | `accent-soft` |
| `link` | "external / API" arrows — same hue, darker; **NOT a second hue** | `#2E1FB3` | `accent-ink` |
| `backend` node fill | white node fill | `#FFFFFF` | `surface` |

> **Brand source:** the active theme `slide/references/theme-active.json`. Per the slide-svg single-accent principle (CLAUDE.md 핵심 제약), only `accent` may carry the indigo hue — `link` is the accent's darker shade, not a separate blue, and no gradient/glow/rainbow is permitted on diagram nodes. The upstream dark-mode column is dropped: slide-svg renders diagrams on light slides only.

### Light-only

slide-svg renders diagrams on light slides only; the upstream dark-mode inversion rule is dropped.
Express opacity per element via `fill-opacity` / `stroke-opacity` (never `rgba(...)`), per `slide/references/shared-standards.md`.

---

## Typography

**Single-font lock (slide-svg).** All text uses the active font chain
`Pretendard, 'Apple SD Gothic Neo', 'Malgun Gothic', Arial, sans-serif`. The upstream
serif/sans/mono contrast collapses under the lock — recover hierarchy with size/weight/letter-spacing:

| Role | Family | Size | Weight | Tracking |
|---|---|---|---|---|
| `title` | Pretendard | 24–32px | 700 | -0.5 |
| `node-name` | Pretendard | 12–16px | 600 | 0 |
| `sublabel` | Pretendard | 9–11px | 500 | +0.4 |
| `eyebrow` | Pretendard | 8–10px | 600 | +0.64, uppercase |
| `arrow-label` | Pretendard | 8–10px | 500 | +0.3 |
| `callout` | Pretendard *italic* | 14px | 500 | 0 |

### Font stack

Every `<text>` carries the full chain inline — `font-family="Pretendard, 'Apple SD Gothic Neo', 'Malgun Gothic', Arial, sans-serif"`.

**Forbidden:** `@font-face`, Google Fonts `<link>`, and any web-font import — banned by `slide/references/shared-standards.md`. There is no `<link rel="stylesheet">`; diagrams are native SVG, not HTML.

---

## Stroke, radius, spacing

| Token | Value | Use |
|---|---|---|
| `stroke-thin` | `0.8` | Tag-box outlines, leaf nodes |
| `stroke-default` | `1` | Most strokes |
| `stroke-strong` | `1.2` | Emphasis strokes |
| `radius-sm` | `4` | Small tags |
| `radius-md` | `6` | Node boxes |
| `radius-lg` | `8` | Containers, rings |
| `grid` | `4` | Every coord, size, and gap is divisible by 4 (hard rule) |

---

## Node type → treatment

Semantic role combinations — reference these by name in type specs.

| Type | Fill | Stroke |
|---|---|---|
| `focal` (1–2 max) | `accent-tint` | `accent` |
| `backend` | `#ffffff` (white) | `ink` |
| `store` | `ink @ 0.05` | `muted` |
| `external` | `ink @ 0.03` | `ink @ 0.30` |
| `input` | `muted @ 0.10` | `soft` |
| `optional` | `ink @ 0.02` | `ink @ 0.20` dashed `4,3` |
| `security` | `accent @ 0.05` | `accent @ 0.50` dashed `4,4` |

---

## Customizing the skin

Three options:

1. **Run onboarding** — see [`onboarding.md`](onboarding.md). Drop a URL; the skill extracts the palette + fonts and rewrites this file.
2. **Edit by hand** — change the hex values in the tables above. Run the pre-output taste gate afterward to verify the accent still reads as "focal" against the new paper color.
3. **Brand handoff** — paste your existing design-token JSON into a new section here and map its tokens to the semantic roles above.

### Constraints (don't break these)

- **Contrast**: `ink` must hit WCAG AA on `paper`. `muted` must hit AA on `paper` for 11px+ text.
- **One accent**: pick one color for `accent`. Two accents erases the focal signal.
- **No rainbow palette**: if your brand ships 8 colors, pick 3 (paper, ink, accent). The rest become `muted` variants.
- **Single font (slide-svg lock)**: all text uses the active Pretendard chain — `@font-face` / Google Fonts are forbidden by `shared-standards.md`. Recover the serif/sans/mono hierarchy with size/weight/letter-spacing, not extra families.
- **Paper is warm-neutral, not pure white**: pure white turns the design sterile. Pick a cream, bone, or light grey with a hint of warmth.
- **Dot pattern is optional, not default**: the 22×22 dot pattern is an opt-in "dotted paper" variant (good for long-form editorial hero diagrams). The default background is a clean `paper` fill, no pattern. When the pattern is enabled, it should sit at ~10% opacity of `ink` on `paper` — visible but quiet.
- **Container is clean by default**: the diagram sits directly on the page paper, no secondary container background or border. A framed variant (`paper-2` bg + `rule` border + 8px radius + padding) is available as an opt-in for card-heavy layouts, but don't reach for it by default — the extra chrome fights the figure.
