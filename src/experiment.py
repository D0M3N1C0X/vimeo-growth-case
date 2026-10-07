"""
How to test the bet before hiring for it. The question the test answers is the one the business
case cannot: does outreach cause upgrades, and how many?

    sample_size()   accounts per arm to detect a difference in upgrade rates (two proportions)
    designs()       four ways to run the test, against the accounts actually available
    simulate()      one run of the chosen design on simulated accounts, analysed as the real one would be

The simulation is not evidence about Vimeo: it shows the readout and the decision rule working on
data whose truth is known.
"""
import functools
import math
import random
from statistics import NormalDist

import pandas as pd

import business_case
import config as C

Z = NormalDist()


def sample_size(p0: float, p1: float, alpha: float = C.TEST["alpha"], power: float = C.TEST["power"],
                one_sided: bool = False) -> int:
    """Per arm, normal approximation with unpooled variances."""
    za = Z.inv_cdf(1 - alpha / (1 if one_sided else 2))
    zb = Z.inv_cdf(power)
    return math.ceil((za + zb) ** 2 * (p0 * (1 - p0) + p1 * (1 - p1)) / (p1 - p0) ** 2)


def per_window(yearly: float, window_days: int) -> float:
    return yearly * window_days / 365


def designs(bet: dict | None = None, test: dict | None = None) -> pd.DataFrame:
    """The bar is the break-even uplift: a test that cannot see it cannot decide anything."""
    test = C.TEST if test is None else test
    available = business_case.model(bet)["eligible"]
    be = business_case.breakeven() if bet is None else business_case.breakeven_for(bet)
    base_rate_90 = test["baseline_upgrade_rate"]
    rows = []
    for name, window, one_sided, eligible_mult in (
            ("90 days, two-sided", 90, False, 1.0),
            ("90 days, one-sided", 90, True, 1.0),
            ("180 days, one-sided", 180, True, 1.0),
            ("90 days, one-sided, eligibility doubled", 90, True, 2.0)):
        p0 = base_rate_90 * window / 90
        # doubling eligibility brings in weaker accounts: assume the uplift per account halves
        uplift = be / eligible_mult
        p1 = p0 + per_window(uplift, window)
        n = sample_size(p0, p1, alpha=test["alpha"], power=test["power"], one_sided=one_sided)
        rows.append({"design": name, "window_days": window, "one_sided": one_sided,
                     "control_rate": p0, "treatment_rate_at_breakeven": p1, "per_arm": n, "needed": 2 * n,
                     "available": available * eligible_mult, "feasible": 2 * n <= available * eligible_mult})
    return pd.DataFrame(rows)


def chosen_design() -> dict:
    d = designs()
    ok = d[d["feasible"]]
    return ok.iloc[0].to_dict() if len(ok) else d.iloc[-1].to_dict()


def simulate(true_uplift: float | None = None, seed: int = C.TEST["seed"]) -> dict:
    """Accounts randomised 50/50; upgrades and Self-Serve cancellations drawn at known rates."""
    design = chosen_design()
    be = business_case.breakeven()
    true_uplift = C.BET["uplift"] if true_uplift is None else true_uplift
    rng = random.Random(seed)
    n = int(round(design["available"]))
    window = design["window_days"]
    p0 = design["control_rate"]
    p1 = p0 + per_window(true_uplift, window)
    churn = C.TEST["guardrail_churn"] * window / 90
    counts = {"control": [0, 0, 0], "treatment": [0, 0, 0]}        # accounts, upgrades, cancellations
    for _ in range(n):
        arm = "treatment" if rng.random() < 0.5 else "control"
        c = counts[arm]
        c[0] += 1
        u = rng.random()
        if u < (p1 if arm == "treatment" else p0):
            c[1] += 1
        elif u > 1 - churn:
            c[2] += 1
    return {"design": design, "true_uplift": true_uplift, "breakeven_uplift": be, **readout(counts, window, be)}


def readout(counts: dict, window: int, breakeven_yearly: float) -> dict:
    nc, uc, cc = counts["control"]
    nt, ut, ct = counts["treatment"]
    # sample ratio mismatch: is the 50/50 split plausible?
    exp = (nc + nt) / 2
    chi2 = (nc - exp) ** 2 / exp + (nt - exp) ** 2 / exp
    srm_p = 2 * (1 - Z.cdf(math.sqrt(chi2)))
    rc, rt = uc / nc, ut / nt
    diff = rt - rc
    se = math.sqrt(rc * (1 - rc) / nc + rt * (1 - rt) / nt)
    z = diff / se
    p_one = 1 - Z.cdf(z)
    lower = diff - Z.inv_cdf(1 - C.TEST["alpha"]) * se       # one-sided 95% lower bound
    be_window = per_window(breakeven_yearly, window)
    # guardrail: Self-Serve cancellations must not rise by more than the margin (non-inferiority)
    kc, kt = cc / nc, ct / nt
    gse = math.sqrt(kc * (1 - kc) / nc + kt * (1 - kt) / nt)
    g_upper = (kt - kc) + Z.inv_cdf(1 - C.TEST["alpha"]) * gse
    guard_ok = g_upper < C.TEST["guardrail_margin"] * window / 90
    # order matters: a broken split invalidates everything; without an uplift there is nothing to protect
    if srm_p < 0.001:
        decision = "Stop: the split is broken, fix assignment and rerun"
    elif lower <= 0:
        decision = "Stop or redesign: no detectable uplift"
    elif not guard_ok:
        decision = "Do not scale: outreach may be pushing Self-Serve customers away"
    elif diff >= be_window:
        decision = "Scale: the uplift is real and above break-even"
    else:
        decision = "Iterate: the uplift is real but below break-even; cheaper outreach or better targeting first"
    return {"control": {"accounts": nc, "upgrades": uc, "rate": rc, "cancellations": cc},
            "treatment": {"accounts": nt, "upgrades": ut, "rate": rt, "cancellations": ct},
            "srm_p": srm_p, "difference": diff, "se": se, "z": z, "p_one_sided": p_one, "lower_bound": lower,
            "breakeven_window": be_window, "uplift_yearly_estimate": diff * 365 / window,
            "guardrail_difference": kt - kc, "guardrail_upper": g_upper, "guardrail_ok": guard_ok,
            "decision": decision}


def run() -> dict:
    return {"designs": designs(), "simulation": simulate(),
            "simulation_null": simulate(true_uplift=0.0, seed=C.TEST["seed"] + 1),
            "voi": {name: value_of_information(prior) for name, prior in C.PRIORS.items()}}


if __name__ == "__main__":
    pd.set_option("display.width", 200)
    o = run()
    print(o["designs"])
    for k in ("simulation", "simulation_null"):
        s = o[k]
        print(k, {x: (round(v, 5) if isinstance(v, float) else v) for x, v in s.items() if x != "design"})


def operating_characteristics(runs: int = 200, uplifts: tuple | None = None) -> pd.DataFrame:
    """How often the decision rule says what, at several true uplifts: the rule's error rates."""
    be = business_case.breakeven()
    uplifts = (0.0, be, C.BET["uplift"], 0.015) if uplifts is None else uplifts
    rows = []
    for u in uplifts:
        counts = {}
        for s in range(runs):
            d = simulate(true_uplift=u, seed=10_000 + s)["decision"].split(":")[0]
            counts[d] = counts.get(d, 0) + 1
        rows.append({"true_uplift": u, **{k: v / runs for k, v in counts.items()}})
    return pd.DataFrame(rows).fillna(0.0)


@functools.lru_cache(maxsize=None)
def p_scale(uplift: float, runs: int = C.VOI_RUNS) -> float:
    """Share of simulated tests at this true uplift that end in 'Scale'."""
    return sum(simulate(true_uplift=uplift, seed=50_000 + s)["decision"].startswith("Scale") for s in range(runs)) / runs


def value_of_information(prior: dict) -> dict:
    """Launch now, do nothing, or test first and decide on the rule. NPV is linear in the uplift, so
    each option's value under the prior is a weighted sum over the scenarios."""
    b = C.BET
    design = chosen_design()
    years = design["window_days"] / 365
    delay = 1 / (1 + b["discount_rate"]) ** years
    pv_build = b["build_cost"] / (1 + b["discount_rate"])
    eligible = business_case.model()["eligible"]
    test_cost = (eligible / 2 * b["outreach_cost"] * years + C.TEST_STAFF * b["ae_cost"] * years + b["build_cost"])
    rows = []
    for u, prob in prior.items():
        npv = business_case.model({**b, "uplift": u})["npv"]
        after_test = (npv + pv_build) * delay          # the build is paid for the test; the rest starts later
        ps = p_scale(u)
        rows.append({"uplift": u, "probability": prob, "npv_launch_now": npv, "p_scale": ps,
                     "value_after_test": after_test, "test_value": ps * after_test - test_cost})
    t = pd.DataFrame(rows)
    launch = (t["probability"] * t["npv_launch_now"]).sum()
    test = (t["probability"] * t["test_value"]).sum()
    perfect = (t["probability"] * t["npv_launch_now"].clip(lower=0)).sum()
    best_without = max(launch, 0.0)
    return {"table": t, "launch_now": launch, "do_nothing": 0.0, "test_first": test, "test_cost": test_cost,
            "evpi": perfect - best_without, "value_of_test": test - best_without,
            "best": max((("Launch now", launch), ("Do nothing", 0.0), ("Test first", test)), key=lambda x: x[1])[0],
            "prior_mean": float((t["uplift"] * t["probability"]).sum())}
