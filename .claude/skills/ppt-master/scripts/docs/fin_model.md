# fin_model.py

Compute one roll-up (buy-and-build) investment model from an assumptions JSON: yearly P&L, an EBIT bridge, exit valuation, returns (MOIC, IRR) and named stress scenarios. Optionally write an `.xlsx` whose P&L, valuation, MOIC and IRR cells are formulas, so Excel recomputes every number from the input cells.

Every finance number a deck shows comes from this output, never from a hand calculation, and enters the number ledger as a `계산` or `가정` row (§7).

## 1. Usage

```bash
python3 .claude/skills/ppt-master/scripts/fin_model.py <project_path>/analysis/fin_assumptions.json \
    --json <project_path>/analysis/fin_model.json \
    --xlsx <project_path>/analysis/fin_model.xlsx
```

| Argument | Behavior |
|---|---|
| `<assumptions.json>` | Model input (§3). UTF-8, BOM tolerated |
| `--json <path>` | Write the model output (§5). Omitted → print it to stdout |
| `--xlsx <path>` | Also write the formula workbook (§6). Needs `openpyxl` |

Exit `0` on success. Exit `1` with every problem listed on stderr when the file is missing, is not JSON, or has missing, unknown (typo) or inconsistent keys; nothing is written then.

**When to run**: investment proposals, valuation pages, and multi-year plan or budget decks whose numbers fit the shape in §2. Run it in Step 4 before writing §IX numbers, and again after any assumption change. A single-company plan is one acquisition row in the first year.

**Files**: the Strategist writes `analysis/fin_assumptions.json`; `fin_model.json` and `fin_model.xlsx` are derived — re-run the script instead of editing them.

---

## 2. Model Shape

| Part | Rule |
|---|---|
| Companies | Each `acquisitions` row is `count` companies bought at the start of `year`; the first row is the base company. Every company earns `revenue_per_company` in the first acquisition year and grows `revenue_growth_pct` a year from then, acquired or not |
| Consolidation | The P&L holds 100% of every acquired company (control stake); the stake applies only to entry price and exit value |
| EBIT margin | `entry_margin_pct` + the sum of each lever's `uplift_pp` for the years since entry (uplift_pp[0] in year 1, …; flat after the last listed year) |
| EBITDA | EBIT × `ebitda_to_ebit` |
| Entry price | count × entry-year revenue × entry margin × `ebitda_to_ebit` × `entry_multiple` × `stake_pct` |
| Investment | Entry price in the acquisition year + `platform_investment[year]`, paid at the start of the year (t = year − first year) |
| Exit | End of `exit_year` (t = exit_year − first year + 1). EV = exit-year EBITDA × multiple; equity = max(EV − `net_debt_at_exit`, 0); stake value = equity × `stake_pct` |
| Returns | MOIC = stake value ÷ total investment. IRR = annual IRR of the dated cash flows, by bisection on (−99%, 1000%); `null` when NPV never changes sign |
| EBIT bridge | Base case, first-year EBIT → each later acquisition (entry-year revenue × entry margin) → organic growth (revenue growth × entry margin) → each margin lever → exit-year EBIT. Reconciles exactly |
| Stress | A shock changes operations and the exit multiple only. Entry prices and investment stay at the base plan |

**Out of scope** — debt schedules, interest, taxes, dividends, fees and carry, different sizes per acquisition, monthly timing. When a deck needs one of these, tell the user; do not force the numbers into this shape.

---

## 3. Assumption Schema

All keys are required; unknown keys are rejected. Percentages are in percent (`4` = 4%), margin changes in percentage points.

| Key | Type | Meaning |
|---|---|---|
| `unit` | string | Money unit of every amount, e.g. `"억 원"` |
| `exit_year` | int | Year whose EBITDA is valued; exit at its end. ≥ last acquisition year |
| `revenue_per_company` | number > 0 | Revenue of one company in the first acquisition year |
| `revenue_growth_pct` | number > −100 | Annual revenue growth |
| `entry_margin_pct` | number > 0 | EBIT margin at entry (year 0) |
| `margin_levers` | list | `{"name", "uplift_pp": [year 1, year 2, …]}`; may be empty |
| `ebitda_to_ebit` | number ≥ 1 | EBITDA ÷ EBIT (below 1 means the ratio is inverted) |
| `acquisitions` | list, ≥ 1 | `{"year", "count"}`; one row per year |
| `stake_pct` | 0 < number ≤ 100 | Stake bought in every company |
| `entry_multiple` | number > 0 | Entry EV/EBITDA |
| `platform_investment` | object | `{"<year>": amount ≥ 0}` for years inside the model span; may be `{}` |
| `exit_multiple` | number > 0 | Base exit EV/EBITDA |
| `net_debt_at_exit` | number | Subtracted from EV |
| `valuation_multiples` | list of numbers > 0 | Exit multiples for the valuation table; may be `[]` |
| `stress` | list | `{"name", …shocks}` with at least one shock key below |

| Shock key | Effect |
|---|---|
| `revenue_pct` | Revenue × (1 + value/100) in every year (> −100) |
| `margin_pp` | Added to the EBIT margin in every year (operating leverage, new costs) |
| `lever_scale` | Multiplies every lever uplift (0.5 = half the effect) |
| `exit_multiple` | Replaces the exit multiple |

Full example — deck B (`20261118_mobility_ax_rollup_bench`, roll-up of eight dealers):

```json
{
  "unit": "억 원",
  "exit_year": 2031,
  "revenue_per_company": 1200,
  "revenue_growth_pct": 4,
  "entry_margin_pct": 2.0,
  "margin_levers": [{"name": "AX 온보딩", "uplift_pp": [1.0, 1.0, 1.0]}],
  "ebitda_to_ebit": 1.6421052631578947,
  "acquisitions": [
    {"year": 2027, "count": 2},
    {"year": 2028, "count": 3},
    {"year": 2029, "count": 3}
  ],
  "stake_pct": 51,
  "entry_multiple": 5.0,
  "platform_investment": {"2027": 100, "2028": 100, "2029": 100},
  "exit_multiple": 8.0,
  "net_debt_at_exit": 0,
  "valuation_multiples": [4.2, 8.0, 10.0],
  "stress": [
    {"name": "거래량 −15%", "revenue_pct": -15, "margin_pp": -0.8},
    {"name": "AX 효과 절반", "lever_scale": 0.5},
    {"name": "규제 비용 −0.5%p", "margin_pp": -0.5},
    {"name": "멀티플 4.2x", "exit_multiple": 4.2},
    {"name": "복합 하방", "revenue_pct": -15, "margin_pp": -1.3, "lever_scale": 0.5, "exit_multiple": 4.2}
  ]
}
```

> Note: write a ratio derived from facts at full precision (`1248 / 760` = `1.6421052631578947`). A rounded `1.64` moves 2031 EBITDA from 853 to 852.

---

## 4. Errors

| Message pattern | Fix |
|---|---|
| `missing key 'x'` / `unknown key 'x' (typo?)` | Add the key or correct its spelling (§3) |
| `x must be a number` / `must be > n` | Use a JSON number in range |
| `exit_year … is before the last acquisition` | Move the exit or the acquisition |
| `platform_investment year 'y' must be a year from a to b` | Keep investment years inside the model span |
| `acquisitions: year y is listed twice` | Merge the rows into one count |
| `stress[i] needs at least one of …` / `name … is used twice` | Give each stress a unique name and a shock |

---

## 5. Output JSON

Floats are rounded to 6 decimals; amounts are in `unit`.

| Key | Content |
|---|---|
| `assumptions` | The input, echoed |
| `margin_by_age_pct` | Base EBIT margin by years since entry, `[year 0, …, plateau]` |
| `acquisitions` | Per row: `year`, `count`, `revenue_per_company` at entry, `price` (stake) |
| `investment_total` | `acquisitions`, `platform`, `total` |
| `pnl` | Per year: `companies`, `revenue`, `ebit`, `ebit_margin_pct`, `ebitda`, `acquisition_spend`, `platform_investment`, `investment` |
| `ebit_bridge` | `from_year`, `to_year`, `start`, `drivers[]` (`acquisition` / `organic_growth` / `margin_lever` with `value`), `end` |
| `valuation` | Base exit: `exit_ebitda`, `multiple`, `ev`, `net_debt`, `equity`, `stake_pct`, `stake_value` |
| `returns` | Base: `cash_flows[]` (`t`, `date`, `amount`), `invested`, `proceeds`, `moic`, `irr_pct` |
| `valuation_cases` | One entry per `valuation_multiples` value: `multiple`, `valuation`, `returns` |
| `stress` | Per scenario: `name`, `shock`, `margin_by_age_pct`, `exit_ebit`, `exit_ebit_margin_pct`, `pnl`, `valuation`, `returns` |

---

## 6. Formula Workbook

Sheet `Base` holds the base case and one exit block per `valuation_multiples` value; sheet `Stress N` holds stress scenario N (its name in `A1`). Each sheet lists the inputs (column B, the lever, acquisition and platform rows) as values; the margin-by-age row, every P&L row, entry prices, EV, equity, stake value, cash flows, MOIC (`=stake/SUM(investment)`) and IRR (`=IRR(cash flows)`) are formulas. Change an input cell and Excel recomputes the case. The workbook recomputes the model; the JSON stays the source the deck reads.

---

## 7. Feeding the Deck — Number Ledger

**Hard rule**: tables, charts and text take model numbers from `fin_model.json`. Do not retype a number from a console print, and do not compute a model number by hand.

| Number shown | Ledger type | `formula or source/URL` column |
|---|---|---|
| An input, e.g. growth 4%, entry 5.0x | `가정` | `fin_assumptions: revenue_growth_pct` |
| An input derived from facts, e.g. EBITDA ÷ EBIT 1.64 | `계산` | the fact formula, e.g. `케이카 2025 EBITDA 1,248 ÷ 영업이익 760` |
| An output, e.g. 2031 EBIT 519, MOIC 1.6배 | `가정` (it inherits the assumptions — strategist.md §6.3) | `fin_model: <section>[<key>].<field>` |
| A difference of two outputs, e.g. +3.0%p | `가정` | both paths, e.g. `fin_model: margin_by_age_pct[3] − margin_by_age_pct[0]` |

Path keys: `pnl[2031].ebit`, `valuation.stake_value`, `returns.irr_pct`, `valuation_cases[4.2].returns.moic`, `stress[AX 효과 절반].returns.moic`, `ebit_bridge.drivers[AX 온보딩].value`.

```markdown
| id | shown as | type | formula or source/URL | pages |
|---|---|---|---|---|
| fin-ebit-2031 | 519억 원 | 가정 | fin_model: pnl[2031].ebit | P14, P16 |
| fin-moic-base | 3.1배 | 가정 | fin_model: returns.moic | P02, P15, P17 |
| fin-growth | 연 4% | 가정 | fin_assumptions: revenue_growth_pct | P14 |
```

**Display rounding**: round the full JSON value half-up to the shown precision, once. Never round an already rounded value — deck B printed MOIC 3.0509 as `3.05`, then showed `3.0배`; the correct one-decimal value is `3.1배`.

**Tags**: model outputs and inputs carry the page tag of their ledger type (`계산` / `가정`), per the ledger rules in `templates/design_spec_reference.md`.
