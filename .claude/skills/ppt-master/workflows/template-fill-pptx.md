---
description: MOVED — PPTX template fill is now the standalone ppt-template-fill skill; this file is a routing pointer only
---

# Template Fill (PPTX) — Moved

This workflow has been promoted to a standalone skill: **`ppt-template-fill`**.

**Hard rule**: do not execute template fill from this file. Read and follow [`.claude/skills/ppt-template-fill/SKILL.md`](../../ppt-template-fill/SKILL.md) — it owns the full pipeline (intake → fill plan → capacity check → apply → mandatory OfficeCLI verification loop).

| What | Where it lives now |
|---|---|
| Workflow authority | [`../../ppt-template-fill/SKILL.md`](../../ppt-template-fill/SKILL.md) |
| Executable scripts (unchanged) | `.claude/skills/ppt-master/scripts/template_fill_pptx.py` and `scripts/template_fill_pptx/` |
| Route trigger | Raw `.pptx` template plus new material/topic → `ppt-template-fill` skill (see [`routing.md`](./routing.md) §3) |

Existing cross-references to "template-fill Step N" map 1:1 — the skill kept the original step numbering (Step 1 Inputs … Step 7 Validate Output).
