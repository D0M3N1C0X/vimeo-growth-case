"""
The bet: find the Self-Serve teams that already behave like Enterprise buyers and route them to
sales. Three years, one cohort of upgrades per year, mid-year timing. Every line has a twin formula
in the workbook (build_workbook.py).

    model()        year-by-year P&L of the bet and its net present value
    breakeven()    the uplift at which the bet pays for itself: the bar the test has to clear
    sensitivity()  net present value at the low and high value of each driver
"""
import copy
import functools
import math

import pandas as pd

import analysis
import config as C


def model(bet: dict | None = None, base: dict | None = None) -> dict:
    b = C.BET if bet is None else bet
    base = analysis.baseline() if base is None else base
    eligible = base["self_serve_subscribers"] * b["eligible_share"]
    upgrades = eligible * b["uplift"]                       # per year, a new cohort each year
    acv = base["enterprise_arpu"] * b["entry_acv_share"]
    lost = base["self_serve_arpu"] if b["cannibalised_self_serve"] else 0.0
    aes = math.ceil(eligible * b["planned_uplift"] / b["upgrades_per_ae"] - 1e-9)   # hired to plan
    rows = []
    for t in range(1, b["years"] + 1):
        # cohort c (1..t) pays half in its first year (mid-year upgrades), then retention each year after
        weight = sum(0.5 if c == t else b["retention"] ** (t - c) for c in range(1, t + 1))
        enterprise = upgrades * acv * weight
        cannibalised = upgrades * lost * sum(0.5 if c == t else 1.0 for c in range(1, t + 1))
        net_revenue = enterprise - cannibalised
        gross_profit = net_revenue * b["gross_margin"]
        sales_cost = aes * b["ae_cost"]
        outreach = eligible * b["outreach_cost"]
        build = b["build_cost"] if t == 1 else 0.0
        contribution = gross_profit - sales_cost - outreach - build
        rows.append({"year": t, "upgrades": upgrades, "weight": weight, "enterprise_revenue": enterprise,
                     "cannibalised": cannibalised, "net_revenue": net_revenue, "gross_profit": gross_profit,
                     "account_executives": aes, "sales_cost": sales_cost, "outreach_cost": outreach,
                     "build_cost": build, "contribution": contribution,
                     "discount": 1 / (1 + b["discount_rate"]) ** t})
    y = pd.DataFrame(rows)
    y["cumulative"] = y["contribution"].cumsum()
    y["present_value"] = y["contribution"] * y["discount"]
    return {"eligible": eligible, "upgrades": upgrades, "acv": acv, "years": y, "npv": y["present_value"].sum(),
            "year3_net_revenue": y["net_revenue"].iloc[-1], "payback_year": next(
                (int(r.year) for r in y.itertuples() if r.cumulative >= 0), None)}


@functools.cache
def breakeven(field: str = "uplift", lo: float = 0.0, hi: float = 0.2) -> float:
    """Value of one driver at which the net present value is zero, by bisection."""
    def npv(x) -> float:
        b = copy.deepcopy(C.BET)
        b[field] = x
        return model(b)["npv"]
    assert npv(lo) < 0 < npv(hi)
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if npv(mid) < 0 else (lo, mid)
    return (lo + hi) / 2


def breakeven_for(bet: dict, lo: float = 0.0, hi: float = 1.0) -> float:
    """Break-even uplift for any set of assumptions, by bisection (no closed form assumed)."""
    npv = lambda x: model({**bet, "uplift": x})["npv"]
    if not npv(lo) < 0 < npv(hi):
        raise ValueError("break-even not bracketed")
    for _ in range(100):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if npv(mid) < 0 else (lo, mid)
    return (lo + hi) / 2


def sensitivity() -> pd.DataFrame:
    base_npv = model()["npv"]
    rows = []
    for field, (low, high) in C.SENSITIVITY.items():
        out = {}
        for label, v in (("low", low), ("high", high)):
            b = copy.deepcopy(C.BET)
            b[field] = v
            out[label] = model(b)["npv"]
        rows.append({"driver": field, "low_value": low, "base_value": C.BET[field], "high_value": high,
                     "npv_low": out["low"], "npv_base": base_npv, "npv_high": out["high"],
                     "swing": abs(out["high"] - out["low"])})
    return pd.DataFrame(rows).sort_values("swing", ascending=False).reset_index(drop=True)


def run() -> dict:
    m = model()
    return {"model": m, "breakeven_uplift": breakeven(), "sensitivity": sensitivity()}


if __name__ == "__main__":
    pd.set_option("display.width", 200)
    o = run()
    m = o["model"]
    print({k: v for k, v in m.items() if k != "years"})
    print(m["years"].round(0).T)
    print("break-even uplift", round(o["breakeven_uplift"], 5))
    print(o["sensitivity"].round(0))
