# Bundled Fonts

## Pretendard (locked deck font on this install)

[Pretendard](https://github.com/orioncactus/pretendard) v1.3.9 — SIL Open Font License 1.1
(`Pretendard/LICENSE.txt`). Korean + Latin coverage in one family; the fixed typography
choice for every deck generated in this repo (see `references/strategist.md §g`
install-local font lock).

Bundled static cuts (OTF): Light(300) / Regular(400) / Medium(500) / SemiBold(600) /
Bold(700) / ExtraBold(800). The full 9-weight set is available from the upstream release.

### Family names as installed on Windows

| SVG `font-family` | Weight | Notes |
|---|---|---|
| `Pretendard` | 400 / 700 via `font-weight` | Regular and Bold fold into one family |
| `Pretendard Light` | use normal weight | separate installed family name |
| `Pretendard Medium` | use normal weight | separate installed family name |
| `Pretendard SemiBold` | use normal weight | separate installed family name |
| `Pretendard ExtraBold` | use normal weight | separate installed family name |

Recommended deck stack: `Pretendard, "Malgun Gothic", sans-serif` (tail is browser-preview
fallback only; the converter exports Pretendard into both the Latin and EA typeface slots —
registered in `scripts/svg_to_pptx/drawingml/utils.py DUAL_SCRIPT_FONTS`).

### Installing on another machine

PPTX files do **not** embed fonts. A deck opened on a machine without Pretendard falls back
to a system font. To install: select all files in `Pretendard/` → right-click → **Install**
(Windows), or download from https://github.com/orioncactus/pretendard (macOS/Linux
supported upstream). SIL OFL permits free redistribution with the license file.
