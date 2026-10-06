"""The transcription of the filings holds together, and the revenue bridge adds up."""
import pytest

import analysis
import config as C


def test_categories_add_up_to_reported_revenue(a):
    t = a["transcription"]
    sums = t[t["check"] == "categories add up to total revenue"]
    assert len(sums) == 10
    assert (sums["reported"] - sums["computed"]).abs().max() < 0.5        # thousands of dollars


def test_arpu_times_subscribers_reproduces_revenue(a):
    t = a["transcription"]
    r = t[t["check"] == "revenue = ARPU x average subscribers"]
    assert len(r) == 12 + 18          # 4 years x 3 categories, 6 quarters x 3 categories
    assert r["gap"].abs().max() < C.ARPU_TOLERANCE


def test_bridge_adds_up_and_rounding_is_explained(a):
    """The bridge residual is the published rounding of both periods, no more."""
    b, t = a["bridge"], a["transcription"]
    assert (b["volume"] + b["price"] + b["rounding"] - b["change"]).abs().max() < 1e-9
    gap = t.set_index(["period", "segment"])
    for r in b.itertuples(index=False):
        g0, g1 = gap.loc[(r[0], r.segment)], gap.loc[(r.to, r.segment)]
        allowed = (abs(g0["computed"] - g0["reported"]) + abs(g1["computed"] - g1["reported"])) / 1000
        assert abs(r.rounding) <= allowed + 1e-9, (r[0], r.to, r.segment)


def test_two_bases_are_never_joined(a):
    b = a["bridge"]
    old = b[b["to"].str.len() == 4]
    new = b[b["to"].str.len() > 4]
    assert set(old["segment"]) == set(C.OLD.values()) and set(new["segment"]) == set(C.NEW.values())


def test_quarter_lengths():
    assert analysis.days("2024Q1") == (91, 366) and analysis.days("2025Q1") == (90, 365)
    assert analysis.days("2025Q3") == (92, 365) and analysis.days("2024") == (366, 366)


def test_headline_facts(a):
    p, base = a["pnl"], a["baseline"]
    assert p.loc["2024", "revenue"] == pytest.approx(417.006)
    assert p.loc["2024", "gross_margin"] == pytest.approx(1 - 90.731 / 417.006)
    assert base["self_serve_subscribers"] == 1_127_900 and base["enterprise_arpu"] == 24_567
