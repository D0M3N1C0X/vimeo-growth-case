# Assumptions and what they rest on

Everything not taken from Vimeo's filings is listed here. The filings data and their checks are in
[data/SOURCES.md](../data/SOURCES.md). Checked on **6 October 2026**.

**Status**

- **Filing**: read in a Vimeo 10-K or 10-Q.
- **Derived**: computed from filing figures, with the formula in the code and the workbook.
- **Judgement**: an assumption for the case, with its reason. Each one is in the sensitivity table.
- **Simulated**: produced by the simulation, not a fact about Vimeo.

## The starting point

| # | Figure | Value | Status |
|---|---|---|---|
| A01 | Self-Serve subscribers, 30 September 2025 | 1,127,900 | Filing (10-Q Q3 2025) |
| A02 | Self-Serve ARPU, Q3 2025, annualised | $204 | Filing |
| A03 | Vimeo Enterprise ARPU, Q3 2025, annualised | $24,567 | Filing |
| A04 | Enterprise is "often an upgrade from Vimeo's Self-Serve" | — | Filing (definitions in MD&A) |
| A05 | Gross margin 2024 | 78% | Derived (revenue and cost of revenue, XBRL) |

## The bet

| # | Assumption | Base | Range tested | Status and reason |
|---|---|---:|---|---|
| B01 | Share of Self-Serve accounts with team-level signals | 2% | 1–4% | Judgement: the accounts a sales team would call; to be set from past upgrade data |
| B02 | Extra upgrades per eligible account per year | 1.0% | 0.4–2.0% | Judgement: the unknown the test measures |
| B03 | First-year contract value, share of Enterprise ARPU | 50% | 30–70% | Judgement: upgrades start smaller than the average account |
| B04 | Net revenue retention after year one | 90% | 75–105% | Judgement |
| B05 | Account executive cost and capacity | $180k, 40 upgrades a year | 20–60 upgrades | Judgement; the team is hired for the plan, so it is a fixed cost |
| B06 | Outreach cost per eligible account per year | $30 | $15–60 | Judgement |
| B07 | Gross margin on the new revenue | 78% | 70–82% | Derived from A05 |
| B08 | Build of scoring and routing | $400k, once | — | Judgement |
| B09 | Discount rate | 10% | — | Judgement |

## The test

| # | Assumption | Value | Status |
|---|---|---:|---|
| T01 | Organic upgrades per eligible account in 90 days | 0.4% | Judgement: the first number to read from Vimeo's own data |
| T02 | Significance and power | 5%, 80% | Convention |
| T03 | Self-Serve cancellations in 90 days, and the largest rise accepted | 3%, 0.5 points | Judgement |
| T04 | Doubling eligibility halves the uplift per account | — | Judgement: the extra accounts are weaker |
| T05 | Counts in the readout sheet and the decision-rule error rates | — | Simulated, seeded |

## What this is not

- **Not inside information.** Every figure is public; nothing comes from Vimeo or Bending Spoons.
- **Not a view on decisions already taken**, such as pricing or headcount, beyond what the filings report.
- **Not investment advice**, and not affiliated with Vimeo or Bending Spoons.
