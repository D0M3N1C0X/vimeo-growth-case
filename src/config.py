"""
Every assumption in one place. Figures from Vimeo's filings live in data/; everything here that is
not a path is a judgement, labelled as such, and the workbook's Inputs sheet is written from it.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
FINANCIALS = DATA / "sec_financials.csv"
METRICS = DATA / "operating_metrics.csv"
DELIVERABLES = ROOT / "deliverables"
REPORT = ROOT / "report"

REVENUE = "RevenueFromContractWithCustomerExcludingAssessedTax"
YEARS = ["2021", "2022", "2023", "2024"]
QUARTERS = ["Q1", "Q2", "Q3"]
OLD = {"self": "Self-Serve & Add-Ons", "ent": "Vimeo Enterprise", "other": "Other"}
NEW = {"self": "Self-Serve", "ent": "Vimeo Enterprise", "ott": "OTT"}
# Transcription check: revenue ≈ ARPU × average subscribers. ARPU is published to the dollar and
# Enterprise average subscribers to the hundred, so the gap can reach about 2%.
ARPU_TOLERANCE = 0.02

# ---- The bet: route Self-Serve teams that look like Enterprise buyers to sales ----------------------
# Base and Enterprise economics are taken from the Q3 2025 10-Q (see analysis.baseline()). The rest are
# assumptions, set conservatively and stress-tested in the sensitivity table.
BET = {
    # share of the Self-Serve base that shows team-level signals (seats, SSO interest, bandwidth, domains)
    "eligible_share": 0.02,
    # extra upgrades to Enterprise per eligible account per year, caused by outreach (the test measures it)
    "uplift": 0.010,
    # first-year contract value as a share of the average Enterprise ARPU: upgrades start small
    "entry_acv_share": 0.50,
    # annual net revenue retention of upgraded accounts after year one
    "retention": 0.90,
    # each upgrade stops paying its Self-Serve plan
    "cannibalised_self_serve": True,
    # fully loaded cost of one account executive per year, USD, and how many upgrades one can close;
    # the team is hired for the planned uplift before the real one is known, so it is a fixed cost
    "ae_cost": 180_000,
    "upgrades_per_ae": 40,
    "planned_uplift": 0.010,
    # outreach to every eligible account each year: sales development, in-product prompts, tooling
    "outreach_cost": 30,
    # gross margin on Enterprise revenue, close to the company's 78% in 2024
    "gross_margin": 0.78,
    # one-off build of the scoring and routing, USD
    "build_cost": 400_000,
    "years": 3,
    "discount_rate": 0.10,
}
SENSITIVITY = {          # low and high for each driver, everything else at base
    "eligible_share": (0.01, 0.04),
    "uplift": (0.004, 0.020),
    "entry_acv_share": (0.30, 0.70),
    "retention": (0.75, 1.05),
    "upgrades_per_ae": (20, 60),
    "outreach_cost": (15, 60),
    "gross_margin": (0.70, 0.82),
}

# ---- The test --------------------------------------------------------------------------------------
TEST = {
    "alpha": 0.05,
    "power": 0.80,
    "baseline_upgrade_rate": 0.004,     # organic upgrades per eligible account in the 90-day window
    "window_days": 90,
    "guardrail_churn": 0.03,            # Self-Serve cancellations in the window; must not rise by more than
    "guardrail_margin": 0.005,          # half a point
    "seed": 2025,
}

# ---- Is the test worth running? ------------------------------------------------------------------
# A prior on the real uplift: what we believe before any test. Judgement, and two of them, so the
# conclusion can be checked against the belief. Probabilities add up to 1.
PRIORS = {
    "sceptical": {0.0: 0.25, 0.004: 0.20, 0.007: 0.20, 0.010: 0.20, 0.015: 0.15},
    "optimistic": {0.0: 0.10, 0.004: 0.10, 0.007: 0.20, 0.010: 0.30, 0.015: 0.30},
}
# While the test runs: outreach to the treatment half and one account executive for the window.
TEST_STAFF = 1
VOI_RUNS = 300            # simulated tests per uplift scenario
