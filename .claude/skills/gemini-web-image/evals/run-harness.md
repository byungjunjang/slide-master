# Run Harness — gemini-web-image

Repeatable procedure for checking that this skill still teaches its own
rules. Run it after changing SKILL.md or the script.

```bash
# one plan per scenario, written by an agent whose only authority is the skill
python3 .claude/skills/gemini-web-image/evals/score.py <dir-of-plans>
```

Every check encodes a failure that actually happened while building this
path. A plan that passes is one that would not repeat it.

> Read a failing plan before changing the skill. Five calibration rounds in
> a row, the first reading blamed the skill for a fault in the checks: a grep
> over free prose scores phrasing as much as understanding.

## Known limits of the checks

Recorded 2026-08-20, after exp-4 and exp-5, so the next round starts where this
one left off instead of rediscovering it.

- **B5 and B8 reward restating what the script automates.** Both fire on
  vocabulary — the ratio prefix, the eager/decode remedy — that a plan only uses
  when it narrates the script's internals. exp-5's S1 and S2 were the most
  operationally detailed plans of either round and lost these two points for
  spending their words on the operator's decisions instead. Treat a B5/B8 failure
  as a prompt to read the plan, never as evidence on its own.
- **B5's subject has since changed.** The rule it was written against told the
  manifest's author to put the ratio in the prompt's first line; the script does
  that itself, and doing both sent the sentence to the page twice. What is worth
  checking now is whether a plan knows the manifest prompt must *not* carry that
  line. Rewriting B5 that way is work for exp-6 — the exp-4 and exp-5 plans were
  written against the old rule and cannot be scored against the new one.
- **Three checker faults were fixed on 2026-08-20**, all of them the same
  mistake in different clothes: reading a line without the thing that qualifies
  it. `flatten` stripped underscores, so every snake_case identifier a check
  named was unmatchable — B1 had never once fired in its life. Hard-wrapped
  prose split quotations across lines. Prohibitions stated in a table header or
  a section heading did not reach the rows beneath them.

## Input

Seven scenarios, `S1`–`S7`, in `scenarios.json`. Each is a situation the skill
must handle. Scenarios are fixed across experiments so scores stay comparable.

| Id | Scenario | What it probes |
|---|---|---|
| S1 | 4 pending rows, mixed 16:9 and 4:3, daemon up, browser signed in | The normal path |
| S2 | 2 rows already `Generated`, 3 pending | Idempotence — must not resubmit finished rows |
| S3 | WebBridge daemon not answering | Must stop at the precondition, not improvise |
| S4 | An unrelated Gemini conversation is open alongside the run's own | Must not map by position or guess |
| S5 | One conversation's image never decodes (`naturalWidth` stays 0) | Must force the decode rather than call the row dead |
| S6 | The download control reports success and no file arrives | Must verify the effect, and still finish the row |
| S7 | Row 3 of a 4-row batch has to be read | Must address the tab by its recorded slot, never by search |

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
├── S1.md … S7.md      # one plan per scenario
├── scores.json        # per-eval results
└── live.md            # only on every third experiment
```
