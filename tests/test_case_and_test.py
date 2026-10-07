"""The business case behaves as its definition says, and the test design and decision rule work."""
import copy

import pytest

import business_case
import config as C
import experiment


def test_npv_is_linear_in_uplift_and_zero_at_breakeven(bc):
    be = bc["breakeven_uplift"]
    npv = lambda u: business_case.model({**copy.deepcopy(C.BET), "uplift": u})["npv"]
    assert abs(npv(be)) < 1.0
    assert npv(0.02) - npv(0.01) == pytest.approx(npv(0.01) - npv(0.0), rel=1e-9)
    assert 0 < be < C.BET["uplift"]


def test_year_lines_add_up(bc):
    y = bc["model"]["years"]
    assert ((y["gross_profit"] - y["sales_cost"] - y["outreach_cost"] - y["build_cost"]) - y["contribution"]).abs().max() < 1e-6
    assert list(y["weight"].round(4)) == [0.5, 0.5 + C.BET["retention"], 0.5 + C.BET["retention"] + C.BET["retention"] ** 2]


def test_sensitivity_moves_the_right_way(bc):
    s = bc["sensitivity"].set_index("driver")
    for d in ("uplift", "entry_acv_share", "retention", "gross_margin", "upgrades_per_ae"):
        assert s.loc[d, "npv_high"] > s.loc[d, "npv_base"] > s.loc[d, "npv_low"]
    assert s.loc["outreach_cost", "npv_high"] < s.loc["outreach_cost", "npv_low"]


def test_sample_size_formula():
    # (z.975 + z.80)^2 x (p0q0 + p1q1) / d^2 for 10% against 12%
    n = experiment.sample_size(0.10, 0.12)
    assert n == 3839
    assert experiment.sample_size(0.10, 0.12, one_sided=True) < n
    assert experiment.sample_size(0.10, 0.14) < n


def test_designs_compare_need_with_supply(ex):
    d = ex["designs"]
    assert (d["feasible"] == (d["needed"] <= d["available"])).all()
    assert d["feasible"].any() and not d["feasible"].all()


def test_rule_rarely_scales_a_bet_that_does_not_work():
    oc = experiment.operating_characteristics(runs=60, uplifts=(0.0, C.BET["uplift"]))
    assert oc.loc[0].get("Scale", 0.0) <= 0.02
    assert oc.loc[1].get("Scale", 0.0) >= 0.6


def test_broken_split_stops_the_test():
    counts = {"control": [9000, 70, 500], "treatment": [11000, 120, 600]}
    assert experiment.readout(counts, 180, C.BET["uplift"])["decision"].startswith("Stop: the split is broken")


def test_guardrail_blocks_a_harmful_uplift():
    counts = {"control": [10000, 80, 600], "treatment": [10000, 160, 900]}
    assert experiment.readout(counts, 180, 0.001)["decision"].startswith("Do not scale")


def test_value_of_information_holds_together(ex):
    for name, v in ex["voi"].items():
        t = v["table"]
        assert t["probability"].sum() == pytest.approx(1.0)
        # linearity: launching now is worth the NPV at the prior's mean uplift
        mean_npv = business_case.model({**C.BET, "uplift": v["prior_mean"]})["npv"]
        assert v["launch_now"] == pytest.approx(mean_npv, rel=1e-9)
        assert 0 <= v["value_of_test"] + max(v["launch_now"], 0) - v["test_first"] + 1e-6
        assert v["value_of_test"] <= v["evpi"] + 1e-6          # no test beats perfect information
        assert (t["p_scale"].diff().dropna() >= 0).all()      # more uplift, more often scaled
    assert ex["voi"]["sceptical"]["best"] == "Test first" and ex["voi"]["optimistic"]["best"] == "Launch now"
