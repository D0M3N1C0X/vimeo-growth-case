"""
Writes the inputs of the interactive model (web/inputs.json) and the vectors its JavaScript is
tested against (tests/fixtures/js_vectors.json): random sets of assumptions, each computed here in
Python. tests/js/check_model.mjs recomputes them with web/model.js and fails on any difference.
"""
import json
import random

import analysis
import business_case
import config as C
import experiment

WEB = C.ROOT / "web"
VECTORS = C.ROOT / "tests" / "fixtures" / "js_vectors.json"
SLIDERS = {   # key: (min, max, step) shown on the page
    "eligible_share": (0.005, 0.05, 0.0005), "uplift": (0.0, 0.03, 0.0005), "planned_uplift": (0.002, 0.03, 0.0005),
    "entry_acv_share": (0.2, 1.0, 0.05), "retention": (0.6, 1.1, 0.01), "outreach_cost": (0, 100, 1),
    "upgrades_per_ae": (10, 80, 1), "gross_margin": (0.6, 0.9, 0.01),
}
TEST_SLIDERS = {"baseline_upgrade_rate": (0.001, 0.015, 0.0005)}


def write_inputs() -> dict:
    base = analysis.baseline()
    out = {"base": base, "bet": C.BET, "test": C.TEST, "sliders": SLIDERS, "test_sliders": TEST_SLIDERS,
           "breakeven": business_case.breakeven(), "npv": business_case.model()["npv"]}
    WEB.mkdir(exist_ok=True)
    (WEB / "inputs.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return out


def write_vectors(n: int = 40, seed: int = 7) -> int:
    rng = random.Random(seed)
    base = analysis.baseline()
    cases = []
    while len(cases) < n:
        bet = dict(C.BET)
        test = dict(C.TEST)
        for k, (lo, hi, _) in SLIDERS.items():
            bet[k] = round(rng.uniform(lo, hi), 6)
        test["baseline_upgrade_rate"] = round(rng.uniform(*TEST_SLIDERS["baseline_upgrade_rate"][:2]), 6)
        bet["upgrades_per_ae"] = int(round(bet["upgrades_per_ae"]))
        try:
            be = business_case.breakeven_for(bet)
        except ValueError:
            continue
        m = business_case.model(bet, base)
        d = experiment.designs(bet, test)
        cases.append({"bet": bet, "test": test, "npv": m["npv"], "payback_year": m["payback_year"],
                      "eligible": m["eligible"], "acv": m["acv"], "years": m["years"].to_dict("records"),
                      "breakeven": be, "designs": d[["design", "per_arm", "feasible"]].to_dict("records")})
    VECTORS.parent.mkdir(parents=True, exist_ok=True)
    VECTORS.write_text(json.dumps({"base": base, "cases": cases}, indent=1, sort_keys=True, default=float) + "\n",
                       encoding="utf-8")
    return len(cases)


def main() -> None:
    write_inputs()
    print(f"web -> web/inputs.json; {write_vectors()} test vectors -> tests/fixtures/js_vectors.json")


if __name__ == "__main__":
    main()
