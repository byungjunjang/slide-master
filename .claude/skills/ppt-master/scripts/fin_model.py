#!/usr/bin/env python3
"""
PPT Master - Roll-up Financial Model

Compute one buy-and-build (roll-up) investment model from an assumptions JSON:
yearly P&L, an EBIT bridge, exit valuation, returns (MOIC, IRR by bisection)
and named stress scenarios. Optionally write an .xlsx whose P&L, valuation,
MOIC and IRR cells are formulas, so Excel recomputes every number from the
input cells. Deck tables and charts take their numbers from the output JSON;
each one is a 계산 (output) or 가정 (input) row in the number ledger.

Usage:
    python3 scripts/fin_model.py <assumptions.json> [--json <out.json>] [--xlsx <out.xlsx>]

Examples:
    python3 scripts/fin_model.py projects/<name>/analysis/fin_assumptions.json
    python3 scripts/fin_model.py <assumptions.json> --json fin_model.json --xlsx fin_model.xlsx

Dependencies:
    openpyxl (only for --xlsx)

See scripts/docs/fin_model.md for the assumption schema, the outputs and the
ledger rules.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional

try:
    from openpyxl import Workbook
    from openpyxl.utils import get_column_letter
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False

from console_encoding import configure_utf8_stdio

_TOP_KEYS = (
    "unit",
    "exit_year",
    "revenue_per_company",
    "revenue_growth_pct",
    "entry_margin_pct",
    "margin_levers",
    "ebitda_to_ebit",
    "acquisitions",
    "stake_pct",
    "entry_multiple",
    "platform_investment",
    "exit_multiple",
    "net_debt_at_exit",
    "valuation_multiples",
    "stress",
)
# Stress shock keys and their numeric bounds (passed to _check_number).
_SHOCK_LIMITS = {
    "revenue_pct": {"above": -100},
    "margin_pp": {},
    "lever_scale": {"minimum": 0},
    "exit_multiple": {"above": 0},
}
_SHOCK_KEYS = tuple(_SHOCK_LIMITS)


# --- validation ------------------------------------------------------------

def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _check_number(errors: list[str], label: str, value: Any, *,
                  above: Optional[float] = None, minimum: Optional[float] = None,
                  maximum: Optional[float] = None) -> None:
    if not _is_number(value):
        errors.append(f"{label} must be a number, got {value!r}")
    elif above is not None and value <= above:
        errors.append(f"{label} must be > {above}, got {value}")
    elif minimum is not None and value < minimum:
        errors.append(f"{label} must be >= {minimum}, got {value}")
    elif maximum is not None and value > maximum:
        errors.append(f"{label} must be <= {maximum}, got {value}")


def _objects(errors: list[str], label: str, value: Any,
             keys: tuple[str, ...], required: tuple[str, ...]) -> list[dict]:
    """Return the well-formed objects of a list; report the rest."""
    if not isinstance(value, list):
        errors.append(f"{label} must be a list")
        return []
    good = []
    for i, item in enumerate(value):
        if not isinstance(item, dict):
            errors.append(f"{label}[{i}] must be an object")
            continue
        bad = [f"{label}[{i}]: missing key '{k}'" for k in required if k not in item]
        bad += [f"{label}[{i}]: unknown key '{k}'" for k in item if k not in keys]
        errors.extend(bad)
        if not bad:
            good.append(item)
    return good


def _check_names(errors: list[str], label: str, items: list[dict]) -> None:
    names = [item["name"] for item in items]
    for i, name in enumerate(names):
        if not isinstance(name, str) or not name.strip():
            errors.append(f"{label}[{i}].name must be a non-empty string")
    for name in sorted({n for n in names if isinstance(n, str) and names.count(n) > 1}):
        errors.append(f"{label}: name '{name}' is used twice")


def validate(a: Any) -> list[str]:
    """Return every problem in the assumptions; an empty list means the model can run."""
    if not isinstance(a, dict):
        return ["the file must hold one JSON object"]
    errors = [f"missing key '{k}'" for k in _TOP_KEYS if k not in a]
    errors += [f"unknown key '{k}' (typo?)" for k in a if k not in _TOP_KEYS]
    if errors:
        return errors

    if not isinstance(a["unit"], str) or not a["unit"].strip():
        errors.append('unit must be a non-empty string such as "억 원"')
    _check_number(errors, "revenue_per_company", a["revenue_per_company"], above=0)
    _check_number(errors, "revenue_growth_pct", a["revenue_growth_pct"], above=-100)
    _check_number(errors, "entry_margin_pct (the entry price is multiple x EBITDA)",
                  a["entry_margin_pct"], above=0)
    _check_number(errors, "ebitda_to_ebit (EBITDA / EBIT; below 1 means it is inverted)",
                  a["ebitda_to_ebit"], minimum=1)
    _check_number(errors, "stake_pct", a["stake_pct"], above=0, maximum=100)
    _check_number(errors, "entry_multiple", a["entry_multiple"], above=0)
    _check_number(errors, "exit_multiple", a["exit_multiple"], above=0)
    _check_number(errors, "net_debt_at_exit", a["net_debt_at_exit"])

    levers = _objects(errors, "margin_levers", a["margin_levers"],
                      ("name", "uplift_pp"), ("name", "uplift_pp"))
    _check_names(errors, "margin_levers", levers)
    for i, lever in enumerate(levers):
        uplift = lever["uplift_pp"]
        if not isinstance(uplift, list) or not uplift or not all(map(_is_number, uplift)):
            errors.append(f"margin_levers[{i}].uplift_pp must be a non-empty list of numbers "
                          "(pp added in year 1, 2, ... after entry)")

    acquisitions = _objects(errors, "acquisitions", a["acquisitions"],
                            ("year", "count"), ("year", "count"))
    if a["acquisitions"] == []:
        errors.append("acquisitions must hold at least the base company {year, count}")
    years = []
    for i, acq in enumerate(acquisitions):
        if _is_int(acq["year"]):
            years.append(acq["year"])
        else:
            errors.append(f"acquisitions[{i}].year must be an integer year")
        if not _is_int(acq["count"]) or acq["count"] < 1:
            errors.append(f"acquisitions[{i}].count must be an integer >= 1")
    for year in sorted({y for y in years if years.count(y) > 1}):
        errors.append(f"acquisitions: year {year} is listed twice; merge the counts")

    if not _is_int(a["exit_year"]):
        errors.append("exit_year must be an integer year")
    elif years and a["exit_year"] < max(years):
        errors.append(f"exit_year {a['exit_year']} is before the last acquisition ({max(years)})")

    platform = a["platform_investment"]
    if not isinstance(platform, dict):
        errors.append('platform_investment must be an object such as {"2027": 100}')
    else:
        for key, amount in platform.items():
            span_known = years and _is_int(a["exit_year"])
            if span_known and not (key.isdigit() and str(int(key)) == key
                                   and min(years) <= int(key) <= a["exit_year"]):
                errors.append(f"platform_investment year '{key}' must be a year "
                              f"from {min(years)} to {a['exit_year']}")
            _check_number(errors, f"platform_investment['{key}']", amount, minimum=0)

    if not isinstance(a["valuation_multiples"], list):
        errors.append("valuation_multiples must be a list of exit multiples such as [4.2, 8.0]")
    else:
        for i, multiple in enumerate(a["valuation_multiples"]):
            _check_number(errors, f"valuation_multiples[{i}]", multiple, above=0)

    shocks = _objects(errors, "stress", a["stress"], ("name",) + _SHOCK_KEYS, ("name",))
    _check_names(errors, "stress", shocks)
    for i, shock in enumerate(shocks):
        if not any(k in shock for k in _SHOCK_KEYS):
            errors.append(f"stress[{i}] needs at least one of {', '.join(_SHOCK_KEYS)}")
        for key, limit in _SHOCK_LIMITS.items():
            if key in shock:
                _check_number(errors, f"stress[{i}].{key}", shock[key], **limit)
    return errors


# --- model -----------------------------------------------------------------

def _first_year(a: dict) -> int:
    return min(acq["year"] for acq in a["acquisitions"])


def _company_revenue(a: dict, year: int) -> float:
    """Base-plan revenue of one company in a year, acquired or not."""
    growth = 1 + a["revenue_growth_pct"] / 100
    return a["revenue_per_company"] * growth ** (year - _first_year(a))


def _lever_uplift(lever: dict, age: int) -> float:
    return sum(lever["uplift_pp"][:age])


def _margin_pct(a: dict, age: int, lever_scale: float) -> float:
    uplift = sum(_lever_uplift(lever, age) for lever in a["margin_levers"])
    return a["entry_margin_pct"] + lever_scale * uplift


def _entry_price(a: dict, acq: dict) -> float:
    """Price of the stake in one acquisition row; shocks never change it."""
    ebitda = (_company_revenue(a, acq["year"]) * a["entry_margin_pct"] / 100
              * a["ebitda_to_ebit"])
    return acq["count"] * ebitda * a["entry_multiple"] * a["stake_pct"] / 100


def _pnl(a: dict, shock: dict) -> list[dict]:
    """Consolidated yearly P&L (100% of every acquired company) under one shock."""
    volume = 1 + shock.get("revenue_pct", 0) / 100
    scale = shock.get("lever_scale", 1)
    rows = []
    for year in range(_first_year(a), a["exit_year"] + 1):
        revenue = ebit = 0.0
        companies = 0
        for acq in a["acquisitions"]:
            if year < acq["year"]:
                continue
            sales = acq["count"] * _company_revenue(a, year) * volume
            margin = _margin_pct(a, year - acq["year"], scale) + shock.get("margin_pp", 0)
            revenue += sales
            ebit += sales * margin / 100
            companies += acq["count"]
        spend = sum(_entry_price(a, acq) for acq in a["acquisitions"] if acq["year"] == year)
        platform = a["platform_investment"].get(str(year), 0)
        rows.append({
            "year": year,
            "companies": companies,
            "revenue": revenue,
            "ebit": ebit,
            "ebit_margin_pct": ebit / revenue * 100,
            "ebitda": ebit * a["ebitda_to_ebit"],
            "acquisition_spend": spend,
            "platform_investment": platform,
            "investment": spend + platform,
        })
    return rows


def _irr(flows: list[float]) -> Optional[float]:
    """Annual IRR by bisection on (-99%, 1000%); None when NPV never changes sign."""
    def npv(rate: float) -> float:
        return sum(cf / (1 + rate) ** t for t, cf in enumerate(flows))

    lo, hi = -0.99, 10.0
    npv_lo = npv(lo)
    if npv_lo * npv(hi) > 0:
        return None
    for _ in range(200):
        mid = (lo + hi) / 2
        npv_mid = npv(mid)
        if npv_lo * npv_mid <= 0:
            hi = mid
        else:
            lo, npv_lo = mid, npv_mid
    return (lo + hi) / 2


def _exit(a: dict, rows: list[dict], multiple: float) -> dict:
    """Value the exit-year EBITDA and return the investor cash flows."""
    ev = rows[-1]["ebitda"] * multiple
    equity = max(ev - a["net_debt_at_exit"], 0.0)
    stake_value = equity * a["stake_pct"] / 100
    invested = sum(row["investment"] for row in rows)
    cash_flows = [{"t": t, "date": f"{row['year']}-01-01", "amount": -row["investment"]}
                  for t, row in enumerate(rows)]
    cash_flows.append({"t": len(rows), "date": f"{rows[-1]['year']}-12-31",
                       "amount": stake_value})
    irr = _irr([cf["amount"] for cf in cash_flows])
    return {
        "valuation": {
            "exit_year": rows[-1]["year"],
            "exit_ebitda": rows[-1]["ebitda"],
            "multiple": multiple,
            "ev": ev,
            "net_debt": a["net_debt_at_exit"],
            "equity": equity,
            "stake_pct": a["stake_pct"],
            "stake_value": stake_value,
        },
        "returns": {
            "cash_flows": cash_flows,
            "invested": invested,
            "proceeds": stake_value,
            "moic": stake_value / invested,
            "irr_pct": None if irr is None else irr * 100,
        },
    }


def _ebit_bridge(a: dict, rows: list[dict]) -> dict:
    """Split the base EBIT change into acquisitions, organic growth and each lever."""
    last = rows[-1]["year"]
    entry = a["entry_margin_pct"] / 100
    end_revenue = _company_revenue(a, last)
    later = [acq for acq in a["acquisitions"] if acq["year"] > rows[0]["year"]]
    drivers = [{"driver": "acquisition", "year": acq["year"], "count": acq["count"],
                "value": acq["count"] * _company_revenue(a, acq["year"]) * entry}
               for acq in later]
    drivers.append({"driver": "organic_growth", "value": sum(
        acq["count"] * (end_revenue - _company_revenue(a, acq["year"])) * entry
        for acq in a["acquisitions"])})
    for lever in a["margin_levers"]:
        drivers.append({"driver": "margin_lever", "name": lever["name"], "value": sum(
            acq["count"] * end_revenue * _lever_uplift(lever, last - acq["year"]) / 100
            for acq in a["acquisitions"])})
    start, end = rows[0]["ebit"], rows[-1]["ebit"]
    gap = start + sum(d["value"] for d in drivers) - end
    if abs(gap) > 1e-6 * max(1.0, abs(end)):
        raise RuntimeError(f"EBIT bridge does not reconcile (gap {gap})")
    return {"from_year": rows[0]["year"], "to_year": last, "start": start,
            "drivers": drivers, "end": end}


def run_model(a: dict) -> dict:
    """Compute every output section from validated assumptions."""
    base = _pnl(a, {})
    plateau = max((len(lever["uplift_pp"]) for lever in a["margin_levers"]), default=0)
    stress = []
    for shock in a["stress"]:
        rows = _pnl(a, shock)
        stress.append({
            "name": shock["name"],
            "shock": {k: shock[k] for k in _SHOCK_KEYS if k in shock},
            "margin_by_age_pct": [
                _margin_pct(a, age, shock.get("lever_scale", 1)) + shock.get("margin_pp", 0)
                for age in range(plateau + 1)],
            "exit_ebit": rows[-1]["ebit"],
            "exit_ebit_margin_pct": rows[-1]["ebit_margin_pct"],
            "pnl": rows,
            **_exit(a, rows, shock.get("exit_multiple", a["exit_multiple"])),
        })
    spend = sum(row["acquisition_spend"] for row in base)
    platform = sum(row["platform_investment"] for row in base)
    return {
        "unit": a["unit"],
        "assumptions": a,
        "margin_by_age_pct": [_margin_pct(a, age, 1) for age in range(plateau + 1)],
        "acquisitions": [{"year": acq["year"], "count": acq["count"],
                          "revenue_per_company": _company_revenue(a, acq["year"]),
                          "price": _entry_price(a, acq)} for acq in a["acquisitions"]],
        "investment_total": {"acquisitions": spend, "platform": platform,
                             "total": spend + platform},
        "pnl": base,
        "ebit_bridge": _ebit_bridge(a, base),
        **_exit(a, base, a["exit_multiple"]),
        "valuation_cases": [{"multiple": m, **_exit(a, base, m)}
                            for m in a["valuation_multiples"]],
        "stress": stress,
    }


def _rounded(value: Any) -> Any:
    if isinstance(value, float):
        return round(value, 6)
    if isinstance(value, dict):
        return {k: _rounded(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_rounded(v) for v in value]
    return value


# --- xlsx ------------------------------------------------------------------

def _write_sheet(ws: Any, title: str, a: dict, shock: dict, multiples: list) -> None:
    """Lay out one case: inputs as values, every computed cell as a formula."""
    col = get_column_letter
    acquisitions = a["acquisitions"]
    years = list(range(_first_year(a), a["exit_year"] + 1))
    plateau = max((len(lever["uplift_pp"]) for lever in a["margin_levers"]), default=0)
    ws.column_dimensions["A"].width = 44
    ws["A1"] = title
    ws["B1"] = f"unit: {a['unit']} - values are inputs, every other cell is a formula"

    inputs = (
        ("Revenue per company, first year", a["revenue_per_company"]),
        ("Revenue growth %", a["revenue_growth_pct"]),
        ("Entry EBIT margin %", a["entry_margin_pct"]),
        ("EBITDA / EBIT", a["ebitda_to_ebit"]),
        ("Stake %", a["stake_pct"]),
        ("Entry EV/EBITDA", a["entry_multiple"]),
        ("Exit EV/EBITDA", shock.get("exit_multiple", a["exit_multiple"])),
        ("Net debt at exit", a["net_debt_at_exit"]),
        ("Shock: revenue %", shock.get("revenue_pct", 0)),
        ("Shock: EBIT margin pp", shock.get("margin_pp", 0)),
        ("Shock: lever scale", shock.get("lever_scale", 1)),
    )
    for row, (label, value) in enumerate(inputs, start=3):
        ws.cell(row, 1, label)
        ws.cell(row, 2, value)
    (rev, growth, entry_m, ratio, stake, entry_x, exit_x, net_debt,
     shock_rev, shock_m, scale) = (f"$B${r}" for r in range(3, 3 + len(inputs)))

    age_row = 4 + len(inputs)
    ws.cell(age_row, 1, "Years since entry")
    for age in range(plateau + 1):
        ws.cell(age_row, 3 + age, age)
    for i, lever in enumerate(a["margin_levers"], start=1):
        ws.cell(age_row + i, 1, f"Lever uplift pp: {lever['name']}")
        for age, pp in enumerate(lever["uplift_pp"], start=1):
            ws.cell(age_row + i, 3 + age, pp)
    margin_row = age_row + len(a["margin_levers"]) + 1
    ws.cell(margin_row, 1, "EBIT margin % by years since entry")
    for age in range(plateau + 1):
        uplift = (f"+{scale}*SUM($D${age_row + 1}:${col(3 + age)}${margin_row - 1})"
                  if age else "")
        ws.cell(margin_row, 3 + age, f"={entry_m}{uplift}+{shock_m}")
    margins = f"$C${margin_row}:${col(3 + plateau)}${margin_row}"

    acq_first = margin_row + 3
    acq_last = acq_first + len(acquisitions) - 1
    acq_years, acq_counts = f"$A${acq_first}:$A${acq_last}", f"$B${acq_first}:$B${acq_last}"
    ws.cell(acq_first - 1, 1, "Acquisition year")
    ws.cell(acq_first - 1, 2, "Companies")
    ws.cell(acq_first - 1, 3, "Stake price")
    for r, acq in enumerate(acquisitions, start=acq_first):
        ws.cell(r, 1, acq["year"])
        ws.cell(r, 2, acq["count"])
        ws.cell(r, 3, f"=B{r}*{rev}*(1+{growth}/100)^(A{r}-MIN({acq_years}))"
                      f"*{entry_m}/100*{ratio}*{entry_x}*{stake}/100")

    year_row = acq_last + 2
    rev_first = year_row + 1
    ebit_first = rev_first + len(acquisitions)
    total = ebit_first + len(acquisitions)
    labels = ("Companies", "Revenue", "EBIT", "EBIT margin %", "EBITDA",
              "Acquisition spend", "Platform investment", "Investment")
    (companies_r, revenue_r, ebit_r, margin_r, ebitda_r,
     spend_r, platform_r, invest_r) = range(total, total + len(labels))
    ws.cell(year_row, 1, "Year")
    for i, acq in enumerate(acquisitions):
        ws.cell(rev_first + i, 1, f"Revenue: acquired {acq['year']}")
        ws.cell(ebit_first + i, 1, f"EBIT: acquired {acq['year']}")
    for i, label in enumerate(labels):
        ws.cell(total + i, 1, label)
    for j, year in enumerate(years):
        c = col(3 + j)
        ws.cell(year_row, 3 + j, f"=MIN({acq_years})" if j == 0 else f"={col(2 + j)}{year_row}+1")
        for i in range(len(acquisitions)):
            r = acq_first + i
            ws.cell(rev_first + i, 3 + j,
                    f"=IF({c}${year_row}>=$A${r},$B${r}*{rev}*(1+{growth}/100)"
                    f"^({c}${year_row}-$C${year_row})*(1+{shock_rev}/100),0)")
            ws.cell(ebit_first + i, 3 + j,
                    f"=IF({c}${year_row}>=$A${r},{c}{rev_first + i}*INDEX({margins},"
                    f"MIN({c}${year_row}-$A${r},{plateau})+1)/100,0)")
        ws.cell(companies_r, 3 + j, f'=SUMIF({acq_years},"<="&{c}${year_row},{acq_counts})')
        ws.cell(revenue_r, 3 + j, f"=SUM({c}{rev_first}:{c}{ebit_first - 1})")
        ws.cell(ebit_r, 3 + j, f"=SUM({c}{ebit_first}:{c}{total - 1})")
        ws.cell(margin_r, 3 + j, f"={c}{ebit_r}/{c}{revenue_r}*100")
        ws.cell(ebitda_r, 3 + j, f"={c}{ebit_r}*{ratio}")
        ws.cell(spend_r, 3 + j,
                f"=SUMIF({acq_years},{c}${year_row},$C${acq_first}:$C${acq_last})")
        ws.cell(platform_r, 3 + j, a["platform_investment"].get(str(year), 0))
        ws.cell(invest_r, 3 + j, f"={c}{spend_r}+{c}{platform_r}")

    last_c, flow_c = col(2 + len(years)), col(3 + len(years))
    t_row = invest_r + 2
    ws.cell(t_row, 1, "t (years from the first investment)")
    ws.cell(t_row + 1, 1, "Date")
    for j in range(len(years) + 1):
        ws.cell(t_row, 3 + j, j)
        date = f"{years[j]}-01-01" if j < len(years) else f"{years[-1]}-12-31"
        ws.cell(t_row + 1, 3 + j, date)

    row = t_row + 3
    for label, multiple in [("base", f"={exit_x}")] + [(f"{m:g}x", m) for m in multiples]:
        ws.cell(row, 1, f"Exit {label}")
        block = ("Exit EV/EBITDA", "Exit EBITDA", "EV", "Equity (EV - net debt, floor 0)",
                 "Stake value", "Cash flow", "MOIC", "IRR %")
        for i, name in enumerate(block, start=1):
            ws.cell(row + i, 1, name)
        m_r, e_r, ev_r, eq_r, sv_r, cf_r, moic_r, irr_r = range(row + 1, row + 1 + len(block))
        ws.cell(m_r, 2, multiple)
        ws.cell(e_r, 2, f"={last_c}{ebitda_r}")
        ws.cell(ev_r, 2, f"=B{e_r}*B{m_r}")
        ws.cell(eq_r, 2, f"=MAX(B{ev_r}-{net_debt},0)")
        ws.cell(sv_r, 2, f"=B{eq_r}*{stake}/100")
        for j in range(len(years)):
            ws.cell(cf_r, 3 + j, f"=-{col(3 + j)}{invest_r}")
        ws.cell(cf_r, 3 + len(years), f"=B{sv_r}")
        ws.cell(moic_r, 2, f"=B{sv_r}/SUM(C{invest_r}:{last_c}{invest_r})")
        ws.cell(irr_r, 2, f"=IRR(C{cf_r}:{flow_c}{cf_r})*100")
        row = irr_r + 2


def write_xlsx(a: dict, path: Path) -> None:
    """Write the base case and every stress case as formula sheets."""
    if not HAS_OPENPYXL:
        raise RuntimeError("--xlsx needs openpyxl: pip install openpyxl")
    workbook = Workbook()
    base = workbook.active
    base.title = "Base"
    _write_sheet(base, "Base case", a, {}, a["valuation_multiples"])
    for i, shock in enumerate(a["stress"], start=1):
        _write_sheet(workbook.create_sheet(f"Stress {i}"), f"Stress: {shock['name']}",
                     a, shock, [])
    workbook.save(path)


# --- CLI -------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Roll-up financial model: assumptions JSON -> model JSON (+ formula xlsx).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Schema and ledger rules: scripts/docs/fin_model.md",
    )
    parser.add_argument("assumptions", type=Path, help="assumptions JSON file")
    parser.add_argument("--json", type=Path, help="write the model JSON here (default: stdout)")
    parser.add_argument("--xlsx", type=Path, help="also write a formula workbook here")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    configure_utf8_stdio()
    args = build_parser().parse_args(argv)
    try:
        assumptions = json.loads(args.assumptions.read_text(encoding="utf-8-sig"))
    except OSError as exc:
        print(f"Error: cannot read {args.assumptions}: {exc}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"Error: {args.assumptions} is not valid JSON: {exc}", file=sys.stderr)
        return 1
    errors = validate(assumptions)
    if errors:
        print(f"Error: {len(errors)} problem(s) in {args.assumptions} "
              "(schema: scripts/docs/fin_model.md):", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    text = json.dumps(_rounded(run_model(assumptions)), ensure_ascii=False, indent=2) + "\n"
    try:
        if args.json:
            args.json.write_text(text, encoding="utf-8")
            print(f"[fin_model] wrote {args.json}", file=sys.stderr)
        else:
            sys.stdout.write(text)
        if args.xlsx:
            write_xlsx(assumptions, args.xlsx)
            print(f"[fin_model] wrote {args.xlsx}", file=sys.stderr)
    except (OSError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
