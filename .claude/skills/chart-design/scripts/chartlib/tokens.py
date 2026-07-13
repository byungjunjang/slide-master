"""Token resolver — maps ppt-master deck tokens onto the chart style contract.

slide-master (ppt-master) variant. Unlike slide-svg's global theme file, the
color/typography authority here is **per-deck**: `<project_path>/spec_lock.md`
("Values not listed here must NOT appear in SVGs"). This resolver parses the
project's spec_lock `## colors` / `## typography` sections and derives the
ChartStyle contract the renderers consume, so charts always match the deck
that embeds them.

Hard-fail policy: if spec_lock.md is missing or lacks the required locks
(bg / text / accent-or-primary / font family / body size), raise
TokenResolutionError. Never invent a palette — a chart with off-spec colors
violates ppt-master's SPEC_LOCK discipline.

Derived values: spec_lock locks fewer roles than the chart contract needs
(no soft/ink accents, no neutral ladder). Missing roles are DERIVED from the
locked hexes by alpha-blending — tints/shades of locked colors, never new
hues. Semantic positive/negative/warning fall back to conventional data-vis
hues only when the deck does not lock its own (`- positive: #...` overrides).
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

# Conventional data-semantics fallbacks (growth/decline/caution) — used ONLY
# when the deck's spec_lock does not lock positive/negative/warning itself.
_SEMANTIC_FALLBACK = {"positive": "#059669", "negative": "#E11D48",
                      "warning": "#D97706"}

# T4 single-accent opacity ladder (anti-slop-theme.md Rule T4).
# Position in the ladder = series index. >4 series is a judgment error upstream.
SERIES_ALPHA_LADDER = (0.85, 0.60, 0.40, 0.25)
MAX_SERIES = len(SERIES_ALPHA_LADDER)

_HEX_RE = re.compile(r"^#([0-9A-Fa-f]{6})([0-9A-Fa-f]{2})?$")

# Token names chartlib depends on. Checked eagerly so a contract drift fails
# loudly at resolve time, not deep inside a renderer.
_REQUIRED_COLORS = (
    "bg", "surface", "surface-alt", "text", "text-secondary", "text-tertiary",
    "border", "border-strong", "accent", "accent-soft", "accent-ink",
    "positive", "positive-soft", "negative", "negative-soft",
    "warning", "warning-soft",
)
_REQUIRED_TYPE_ROLES = ("display-sm", "headline", "title", "body", "caption", "label")
_REQUIRED_STROKES = ("icon", "divider", "emphasis")
_REQUIRED_RADII = ("xs", "sm", "md")


class TokenResolutionError(RuntimeError):
    """Raised when slide-svg theme tokens cannot be resolved. Never swallowed."""


def _parse_hex(value: str, token_name: str) -> tuple[int, int, int]:
    m = _HEX_RE.match(value or "")
    if not m:
        raise TokenResolutionError(
            f"Token colors.{token_name} is not a hex color: {value!r}"
        )
    rgb = m.group(1)
    return int(rgb[0:2], 16), int(rgb[2:4], 16), int(rgb[4:6], 16)


def _to_hex(rgb: tuple[int, int, int]) -> str:
    return "#{:02X}{:02X}{:02X}".format(*rgb)


def blend_over(fg_hex: str, bg_hex: str, alpha: float) -> str:
    """Alpha-blend fg over bg, returning a solid hex.

    Solid fills survive every SVG→DrawingML converter identically, unlike
    rgba()/fill-opacity which some paths flatten differently. Charts sit on
    the slide background, so blending over colors.bg reproduces the T4
    opacity-ladder appearance exactly.
    """
    fr, fg_, fb = _parse_hex(fg_hex, "blend.fg")
    br, bg_, bb = _parse_hex(bg_hex, "blend.bg")
    a = max(0.0, min(1.0, alpha))
    return _to_hex((
        round(fr * a + br * (1 - a)),
        round(fg_ * a + bg_ * (1 - a)),
        round(fb * a + bb * (1 - a)),
    ))


def relative_luminance(hex_color: str) -> float:
    r, g, b = (c / 255.0 for c in _parse_hex(hex_color, "luminance"))
    def lin(c: float) -> float:
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


class TypeScale:
    __slots__ = ("size", "weight", "line_height", "letter_spacing", "transform")

    def __init__(self, raw: dict[str, Any], role: str):
        try:
            self.size = float(raw["size"])
            self.weight = int(raw["weight"])
            self.line_height = float(raw["line-height"])
        except (KeyError, TypeError, ValueError) as exc:
            raise TokenResolutionError(
                f"Theme typography.{role} is missing size/weight/line-height"
            ) from exc
        self.letter_spacing = float(raw.get("letter-spacing", 0.0))
        self.transform = raw.get("transform", "none")


class ChartStyle:
    """The style contract every renderer consumes. Built only from tokens."""

    def __init__(self, theme: dict[str, Any], source_path: Path):
        self.source_path = source_path
        self.theme_name = theme.get("name", "?")

        colors = theme.get("colors")
        if not isinstance(colors, dict):
            raise TokenResolutionError(
                f"Theme has no colors object (file: {source_path})")
        missing = [k for k in _REQUIRED_COLORS if not colors.get(k)]
        if missing:
            raise TokenResolutionError(
                f"Theme colors missing required tokens {missing} (file: {source_path}). "
                "Run theme-init to regenerate a contract-valid theme; chart-design "
                "does not substitute defaults.")
        for k in _REQUIRED_COLORS:
            _parse_hex(colors[k], k)  # validate eagerly
        self.color: dict[str, str] = {k: colors[k] for k in colors if isinstance(colors[k], str)}

        typo = theme.get("typography")
        if not isinstance(typo, dict) or not typo.get("font-chain"):
            raise TokenResolutionError(
                f"Theme typography.font-chain missing (file: {source_path})")
        self.font_chain: str = typo["font-chain"]
        self.type: dict[str, TypeScale] = {}
        for role in _REQUIRED_TYPE_ROLES:
            if role not in typo:
                raise TokenResolutionError(
                    f"Theme typography.{role} missing (file: {source_path})")
            self.type[role] = TypeScale(typo[role], role)

        stroke = theme.get("stroke") or {}
        for k in _REQUIRED_STROKES:
            if not isinstance(stroke.get(k), (int, float)):
                raise TokenResolutionError(
                    f"Theme stroke.{k} missing (file: {source_path})")
        self.stroke: dict[str, float] = {k: float(stroke[k]) for k in _REQUIRED_STROKES}

        radius = theme.get("radius") or {}
        for k in _REQUIRED_RADII:
            if not isinstance(radius.get(k), (int, float)):
                raise TokenResolutionError(
                    f"Theme radius.{k} missing (file: {source_path})")
        self.radius: dict[str, float] = {
            k: float(v) for k, v in radius.items() if isinstance(v, (int, float))}

        spacing = theme.get("spacing") or {}
        if not spacing:
            raise TokenResolutionError(f"Theme spacing missing (file: {source_path})")
        self.spacing: dict[str, float] = {
            k: float(v) for k, v in spacing.items() if isinstance(v, (int, float))}

        self.palette_mode: str = theme.get("palette_mode", "chromatic")
        self.card_style: str = (theme.get("surface") or {}).get("card_style", "hairline")

        # Pre-derived roles used across renderers.
        self.muted_fill = blend_over(self.color["text-secondary"], self.color["bg"], 0.30)
        self.grid_stroke = self.color["border"]
        self.axis_stroke = self.color["border-strong"]
        # Which contract roles are literally locked (spec_lock source). A theme
        # JSON (--theme) locks everything it declares.
        self.locked_colors = set(theme.get("_locked_colors", self.color.keys()))

    def neutral_paint(self, role: str, fallback_base: str,
                      fallback_alpha: float) -> tuple[str, float | None]:
        """(hex, opacity|None) for a neutral role.

        Locked role → its solid hex. Unlocked (derived) role → the locked
        fallback_base hex + opacity, so every literal hex in output exists in
        spec_lock (drift-scan clean) while looking identical on the page bg.
        """
        if role in self.locked_colors:
            return (self.color[role], None)
        return (self.color[fallback_base], fallback_alpha)

    # -- palette derivation (the ONLY sources of series color) ----------------

    def series_paints(self, n: int) -> list[tuple[str, float]]:
        """T4 single-accent opacity ladder as (token_hex, opacity) paints.

        Multi-hue palettes are forbidden by slide-svg's anti-slop discipline;
        series are distinguished by opacity steps of the one accent token.
        Emitting the literal accent hex + fill-opacity keeps every color in the
        SVG a theme-palette hex, so svg_quality_checker's off-theme scan passes.
        """
        if n < 1:
            raise ValueError("series count must be >= 1")
        if n > MAX_SERIES:
            raise TokenResolutionError(
                f"{n} series requested but the single-accent ladder supports at "
                f"most {MAX_SERIES} (anti-slop Rule T4). Aggregate minor series "
                "(e.g. top-3 + '기타') or split the chart.")
        base = self.color["accent"]
        return [(base, a) for a in SERIES_ALPHA_LADDER[:n]]

    def series_palette(self, n: int) -> list[str]:
        """Ladder flattened to solid hex over bg — for contrast math and docs."""
        return [blend_over(hex_, self.color["bg"], a)
                for hex_, a in self.series_paints(n)]

    def paint_solid(self, paint: tuple[str, float]) -> str:
        """Visual result of a paint on the slide background (for contrast)."""
        return blend_over(paint[0], self.color["bg"], paint[1])

    @property
    def muted_paint(self) -> tuple[str, float]:
        """Non-focus fill per the rhetorical styling lock (text-secondary tint)."""
        return (self.color["text-secondary"], 0.30)

    def sequential_fill(self, t: float) -> str:
        """Intensity fill for heatmaps: accent alpha scaled by normalized t∈[0,1]."""
        a = 0.06 + max(0.0, min(1.0, t)) * 0.84
        return blend_over(self.color["accent"], self.color["bg"], a)

    def sequential_alpha(self, t: float) -> float:
        return 0.06 + max(0.0, min(1.0, t)) * 0.84

    def semantic(self, kind: str) -> str:
        """positive/negative/warning — only when color encodes data meaning."""
        if kind not in ("positive", "negative", "warning"):
            raise ValueError(f"unknown semantic color: {kind}")
        return self.color[kind]

    def contrast_text(self, fill_hex: str) -> str:
        """Pick readable text color (text vs surface) for a given fill."""
        return (self.color["surface"] if relative_luminance(fill_hex) < 0.35
                else self.color["text"])


# --------------------------------------------------------------------------
# spec_lock.md parsing (ppt-master per-deck contract)
# --------------------------------------------------------------------------

_SECTION_RE = re.compile(r"(?ms)^##[ \t]+([A-Za-z_]+)[ \t]*\r?\n(.*?)(?=^##[ \t]+|\Z)")
_KV_RE = re.compile(r"(?m)^-[ \t]+([A-Za-z0-9_]+)[ \t]*:[ \t]*(.+?)[ \t]*$")


def _parse_spec_lock(path: Path) -> dict[str, dict[str, str]]:
    text = path.read_text(encoding="utf-8")
    sections: dict[str, dict[str, str]] = {}
    for m in _SECTION_RE.finditer(text):
        entries = {k: v for k, v in _KV_RE.findall(m.group(2))}
        sections[m.group(1).lower()] = entries
    return sections


def _is_hex(value: str) -> bool:
    return bool(_HEX_RE.match(value or ""))


def _theme_from_spec_lock(project: Path) -> dict[str, Any]:
    """Build a chart-contract theme dict from a deck's spec_lock.md.

    Locked values are used verbatim; contract roles ppt-master does not lock
    are derived by blending locked hexes (tints/shades, never new hues).
    """
    lock_path = project / "spec_lock.md"
    if not lock_path.is_file():
        raise TokenResolutionError(
            f"spec_lock.md not found: {lock_path}\n"
            "chart-design inherits ALL style from the deck's execution lock and "
            "has no built-in palette. Generate the project through the ppt-master "
            "Strategist flow first (spec_lock.md is written at confirmation), or "
            "pass --theme <contract.json> for testing.")
    sections = _parse_spec_lock(lock_path)
    colors_raw = sections.get("colors", {})
    typo_raw = sections.get("typography", {})

    c = {k.replace("_", "-"): v for k, v in colors_raw.items() if _is_hex(v)}
    missing = [k for k in ("bg", "text", "text-secondary", "border") if k not in c]
    accent = c.get("accent") or c.get("primary")
    if missing or not accent:
        need = missing + ([] if accent else ["accent (or primary)"])
        raise TokenResolutionError(
            f"spec_lock.md colors section is missing required locks {need} "
            f"(file: {lock_path}). Charts label with text_secondary and grid "
            "with border, so these must be locked (the spec_lock skeleton "
            "includes them). Fix via the Strategist / update_spec.py — "
            "chart-design does not substitute colors.")
    bg, text = c["bg"], c["text"]

    def tint(fg: str, alpha: float) -> str:
        return blend_over(fg, bg, alpha)

    colors: dict[str, str] = {
        "bg": bg,
        "surface": c.get("surface", bg),
        "surface-alt": c.get("surface-alt") or c.get("secondary-bg") or tint(text, 0.05),
        "text": text,
        "text-secondary": c["text-secondary"],
        "text-tertiary": c.get("text-tertiary") or tint(text, 0.45),
        "border": c["border"],
        "border-strong": c.get("border-strong") or tint(text, 0.26),
        "accent": accent,
        "accent-soft": c.get("accent-soft") or tint(accent, 0.14),
        "accent-ink": c.get("accent-ink") or blend_over("#000000", accent, 0.28),
    }
    for kind, fallback in _SEMANTIC_FALLBACK.items():
        colors[kind] = c.get(kind, fallback)
        colors[f"{kind}-soft"] = c.get(f"{kind}-soft") or tint(colors[kind], 0.12)

    font_chain = typo_raw.get("body_family") or typo_raw.get("font_family")
    if font_chain:
        # ppt-master SVG convention: double-quoted attributes, single-quoted
        # family names inside the stack (spec_lock md uses double quotes).
        font_chain = font_chain.replace('"', "'")
    if not font_chain:
        raise TokenResolutionError(
            f"spec_lock.md typography lacks font_family/body_family (file: {lock_path}).")

    def px(key: str) -> float | None:
        try:
            return float(typo_raw[key])
        except (KeyError, TypeError, ValueError):
            return None

    body = px("body")
    if body is None:
        raise TokenResolutionError(
            f"spec_lock.md typography lacks the required `body` px anchor "
            f"(file: {lock_path}).")
    caption = px("chart_annotation") or px("annotation") or round(body * 0.75)
    label = px("footnote") or round(caption * 0.9)
    title = px("subtitle") or round(body * 1.33)
    headline = px("title") or round(body * 1.75)
    display_sm = px("hero_number") or round(body * 2.0)

    def scale(size: float, weight: int, lh: float) -> dict[str, Any]:
        return {"size": size, "weight": weight, "line-height": lh,
                "letter-spacing": 0.0, "transform": "none"}

    # Contract roles whose hex literally appears in spec_lock — renderers emit
    # only these as solid fills; unlocked roles are emitted as locked-hex +
    # opacity paints so svg_quality_checker's spec_lock-drift scan stays clean.
    locked = {k for k in colors if colors[k] in set(c.values())}
    return {
        "version": "1.0",
        "name": project.name,
        "colors": colors,
        "_locked_colors": sorted(locked),
        "typography": {
            "font-chain": font_chain,
            "display": scale(round(display_sm * 1.4), 800, 1.08),
            "display-sm": scale(display_sm, 800, 1.1),
            "headline": scale(headline, 700, 1.2),
            "title": scale(title, 600, 1.3),
            "body": scale(body, 400, 1.6),
            "caption": scale(caption, 500, 1.4),
            "label": scale(label, 600, 1.4),
        },
        # Structural geometry tokens ppt-master does not lock — engine constants.
        "radius": {"xs": 4, "sm": 8, "md": 12, "lg": 12, "xl": 20, "pill": 9999},
        "stroke": {"icon": 2, "divider": 1, "emphasis": 2},
        "spacing": {"1": 4, "2": 8, "3": 12, "4": 16, "5": 20, "6": 24,
                    "8": 32, "10": 40, "12": 48, "14": 56, "16": 64},
        "assets": {"icon-pack-default": "tabler-outline"},
        "voice": {"tone": "", "pov": "", "register": ""},
        "surface": {"card_style": "hairline"},
        "palette_mode": "chromatic",
    }


def resolve_style(theme_path: str | Path | None = None,
                  project: str | Path | None = None) -> ChartStyle:
    """Build the chart style contract for a ppt-master deck.

    project: deck project directory containing spec_lock.md (normal path).
    theme_path: a contract-shaped theme JSON — testing/preview only.
    """
    if theme_path:
        path = Path(theme_path)
        if not path.is_file():
            raise TokenResolutionError(f"theme JSON not found: {path}")
        try:
            theme = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise TokenResolutionError(
                f"Failed to parse theme tokens at {path}: {exc}") from exc
        if not isinstance(theme, dict):
            raise TokenResolutionError(f"Theme root is not an object (file: {path})")
        return ChartStyle(theme, path)

    if not project:
        raise TokenResolutionError(
            "No token source given. In slide-master, chart style comes from the "
            "deck's execution lock: pass --project <project_path> so chart-design "
            "reads <project_path>/spec_lock.md (colors + typography). There are "
            "no built-in defaults by design.")
    proj = Path(project)
    theme = _theme_from_spec_lock(proj)
    return ChartStyle(theme, proj / "spec_lock.md")
