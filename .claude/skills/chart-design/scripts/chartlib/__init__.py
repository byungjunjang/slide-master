"""chartlib — pure-stdlib SVG chart engines for the chart-design skill.

Three engines share one style contract resolved from the active slide-svg theme:
  cartesian.py — scales, axes, gridlines, label thinning (12 chart types)
  polar.py     — angle/radius math, arc paths (4 chart types)
  layout.py    — coordinate-free placement logic (5 chart types)

No network calls, no chart libraries. Colors/typography come exclusively from
slide-svg design tokens via tokens.py — hardcoding style values here is a bug.
"""

__version__ = "1.0.0"
