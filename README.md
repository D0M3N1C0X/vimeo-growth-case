# Vimeo Growth Case

An outside-in business analysis of **Vimeo** from its public SEC filings (2021 to Q3 2025): what is
driving revenue, three places growth could come from, a **business case** for the most promising one,
and the **experiment** that would decide it before anyone is hired for it.

[![CI](https://github.com/D0M3N1C0X/vimeo-growth-case/actions/workflows/ci.yml/badge.svg)](https://github.com/D0M3N1C0X/vimeo-growth-case/actions/workflows/ci.yml)
![python](https://img.shields.io/badge/python-3.12%2B-blue)
![data](https://img.shields.io/badge/data-SEC%20filings-f2a900)
![license](https://img.shields.io/badge/license-MIT-lightgrey)

> **Public data, labelled assumptions, simulated test.** Figures come from Vimeo's 10-K and 10-Q filings,
> each traced to its accession number. The business case rests on assumptions listed in
> [docs/assumptions.md](docs/assumptions.md); the test results are simulated. Not affiliated with Vimeo or
> Bending Spoons. Not investment advice.

### ▶ [Read the memo](https://d0m3n1c0x.github.io/vimeo-growth-case/) · [Try the interactive model](https://d0m3n1c0x.github.io/vimeo-growth-case/model/) · [Download the Excel model](https://github.com/D0M3N1C0X/vimeo-growth-case/raw/main/deliverables/vimeo_upgrade_case.xlsx)

---

## The answer

| | |
|---|---|
| **Self-Serve runs on price.** Subscribers fell 21% from 2021 to 2024 while ARPU rose 9%; in 2025 subscribers are down 11% a year in every quarter and ARPU growth has reached +13%. | **Enterprise carried the growth, and it is slowing.** Revenue went from $23.2M to $83.2M in three years, but bookings fell 2% in Q3 2025. |
| **The lever is between the two.** An Enterprise account pays about 120 times a Self-Serve one, and Vimeo's filings say Enterprise is often an upgrade from Self-Serve. | **The bet pays above 0.68% upgrades a year** per eligible account: $2.2M net present value at the 1% plan. A 180-day one-sided test on 20,982 of the 22,558 eligible accounts can tell. |

![Volume and price](report/figures/02_bridge.svg)

## Understand, ideate, execute, optimise

| Step | Question | Where |
|---|---|---|
| **Understand** | What is driving revenue, by category? Each category's revenue change split into a **volume** effect (subscribers) and a **price** effect (ARPU), annual 2021–2024 and quarterly 2025. | [memo §1](report/memo.md), `src/analysis.py`, sheets *Bridge* and *Segments* |
| **Ideate** | Where can growth come from? Three bets, sized from the filings: more price, Self-Serve to Enterprise routing, the Add-Ons decline. | [memo §2](report/memo.md) |
| **Execute** | Is the best bet worth it? A three-year **business case** with fixed sales capacity, its **break-even uplift** in closed form, and a sensitivity table. | [memo §3](report/memo.md), `src/business_case.py`, sheets *Business case* and *Sensitivity* |
| **Decide** | Is the test even worth running? Each option's expected value under a sceptical and an optimistic prior: the test is worth $0.57M if you doubt the bet, and not worth its cost if you already believe it. | [memo §5](report/memo.md), sheet *Value of test* |
| **Optimise** | How would we know? **Sample sizes** for four test designs against the accounts available, a **decision rule** with its error rates over 200 simulated tests, and a readout sheet to paste real counts into. | [memo §4](report/memo.md), `src/experiment.py`, sheets *Test design* and *Test readout* |

## What makes the numbers trustworthy

- **Every figure is traced.** Financials come from the SEC's XBRL facts; subscriber metrics are transcribed
  from each filing's MD&A, with accession numbers in [data/](data/).
- **The transcription is checked.** Categories add up to reported revenue to the dollar in all 10 periods,
  and ARPU × average subscribers reproduces each category's revenue within 2%.
- **Two bases are never joined.** Vimeo regrouped its categories in 2025; annual and quarterly series stay apart.
- **Two engines, one answer.** The Excel model recomputes everything with live formulas and is checked
  against Python on **186 values**; CI recalculates it with LibreOffice. The break-even uplift is a closed
  formula in Excel and a numerical search in Python, and the two must agree.
- **Three engines, one answer.** The interactive model's JavaScript is checked against Python on 1,200 values
  from 40 random scenarios in CI, including sample sizes to the unit: it uses the same inverse-normal algorithm.
- **The tests caught real mistakes**, including a leap-year quarter that leaked into the residual of the bridge.

## Run it

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
python src/run_all.py          # about ten seconds
pip install -r requirements-dev.txt && pytest
```

## What's inside

```
├── data/
│   ├── sec_financials.csv     P&L lines from XBRL, one accession number per value
│   ├── operating_metrics.csv  subscribers, ARPU, bookings, revenue by category, from each MD&A
│   └── SOURCES.md             where every file comes from and how it is checked
├── src/
│   ├── config.py              every assumption in one place
│   ├── analysis.py            transcription checks, P&L, volume and price bridge, trends
│   ├── business_case.py       three-year case, break-even uplift, sensitivity
│   ├── experiment.py          sample sizes, simulated test, decision rule and its error rates
│   ├── build_workbook.py      the Excel model and its reconciliation sheet
│   ├── build_memo.py          the memo and its figures
│   ├── build_web.py           inputs and JavaScript test vectors for the interactive model
│   └── run_all.py             the whole case
├── deliverables/              the workbook
├── report/                    the memo, its HTML page and figures
├── web/                       the interactive model: one page, model.js, inputs.json
├── docs/assumptions.md
└── tests/
```

## Limits

- **Outside in.** No access to Vimeo's data: the organic upgrade rate, the signals that predict an upgrade and
  sales capacity are assumptions, and the memo lists them as the first things to measure.
- **ARPU is rounded** to the dollar and Enterprise subscribers to the hundred in the filings; the bridge shows
  the residual this leaves.
- **Correlation, not cause**, for advertising and Self-Serve subscribers: three yearly points.

## About

Built by **Domenico Perroni** — HR advisory, people analytics and media education, based in Kraków.
I build with an AI coding assistant; the question, the method and the checks are mine.
[GitHub profile](https://github.com/D0M3N1C0X) · [LinkedIn](https://www.linkedin.com/in/domenico-perroni)

**More from the same portfolio**

- [workforce-cost-model](https://github.com/D0M3N1C0X/workforce-cost-model) — a driver-based people-cost model with budget variance and scenarios, Excel reconciled with pandas
- [where-pay-transparency-bites](https://github.com/D0M3N1C0X/where-pay-transparency-bites) — Eurostat data for 27 countries in R: a published statistic that understates what it measures
- [controlli-cedolini](https://github.com/D0M3N1C0X/controlli-cedolini) — nine pre-release checks on Italian payslips, measured on injected errors and random perturbations
- [pay-transparency-readiness-kit](https://github.com/D0M3N1C0X/pay-transparency-readiness-kit) — the EU Pay Transparency Directive run end to end for a four-country employer

MIT licensed.
