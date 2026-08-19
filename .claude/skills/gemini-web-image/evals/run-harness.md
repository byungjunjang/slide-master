# Run Harness — gemini-web-image

Repeatable procedure for checking that this skill still teaches its own
rules. Run it after changing SKILL.md or the script.

```bash
# one plan per scenario, written by an agent whose only authority is the skill
python3 .claude/skills/gemini-web-image/evals/score.py <dir-of-plans>
```

Every check encodes a failure that actually happened while building this
path. A plan that passes is one that would not repeat it.

> Read a failing plan before changing the skill. Three calibration rounds in
> a row, the first reading blamed the skill for a fault in the checks: a grep
> over free prose scores phrasing as much as understanding.

## Input

Five scenarios, `S1`–`S5`, in `scenarios.json`. Each is a situation the skill
must handle. Scenarios are fixed across experiments so scores stay comparable.

| Id | Scenario | What it probes |
|---|---|---|
| S1 | 4 pending rows, mixed 16:9 and 4:3, daemon up, browser signed in | The normal path |
| S2 | 2 rows already `Generated`, 3 pending | Idempotence — must not resubmit finished rows |
| S3 | WebBridge daemon not answering | Must stop at the precondition, not improvise |
| S4 | An unrelated Gemini conversation is open alongside the run's own | Must not map by position or guess |
| S5 | One conversation's image never decodes (`naturalWidth` stays 0) | Must leave the row pending, not loop on it |

## Execution

**One subagent per scenario.** Batching several scenarios into one agent
makes their plans correlated — a single misreading fails every plan that
agent wrote — and only its first plan is a cold read, which is the
condition this suite is meant to measure. Dispatch one subagent per
scenario with:

- the full text of `.claude/skills/gemini-web-image/SKILL.md`
- the full text of `.claude/skills/gemini-web-image/scripts/gemini_web_image.py`
- the scenario description
- the instruction: *"Write the exact execution plan you would follow — every
  command in order, and every decision point with the branch you take. Do not
  execute anything. Do not consult outside knowledge; the skill is the only
  authority."*

The subagent's plan text is the run output. It is saved to
`runs/exp-N/<scenario-id>.md`.

Plan scoring measures whether the skill *teaches* the right procedure. That is
exactly the "no trial and error" goal, and it costs no image quota.

## Live check

Every third experiment, additionally run the real script against a two-row
manifest and record the result in `runs/exp-N/live.md`. This catches a skill
that scores well on plans while the script itself has drifted.

## Output capture

```
runs/exp-N/
├── S1.md … S5.md      # one plan per scenario
├── scores.json        # per-eval results
└── live.md            # only on every third experiment
```
