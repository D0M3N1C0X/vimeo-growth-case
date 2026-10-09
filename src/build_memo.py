"""
Writes report/memo.md and its figures: a business analyst's memo on Vimeo, from the public filings
to a recommendation and the test that would decide it. Every figure comes from analysis.py,
business_case.py and experiment.py.
"""
import pandas as pd

import analysis
import business_case
import charts
import config as C
import experiment

FIG = C.REPORT / "figures"


def usd_m(x, d=1, signed=False) -> str:
    sign = ("+" if x > 0 else "−" if x < 0 else "") if signed else ("−" if x < 0 else "")
    return f"{sign}${abs(x):,.{d}f}M"


def usd(x) -> str:
    return f"{'−' if x < 0 else ''}${abs(x):,.0f}"


def pct(x, d=0, signed=False) -> str:
    sign = ("+" if x > 0 else "−" if x < 0 else "") if signed else ("−" if x < 0 else "")
    return f"{sign}{abs(x) * 100:.{d}f}%"


def table(head, rows, align) -> str:
    out = ["| " + " | ".join(head) + " |", "|" + "|".join("---:" if a == "r" else "---" for a in align) + "|"]
    return "\n".join(out + ["| " + " | ".join(str(c) for c in r) + " |" for r in rows])


def facts(a: dict, bc: dict, ex: dict, oc: pd.DataFrame) -> dict:
    m = analysis.metrics()
    g = lambda basis, per, seg, met: analysis.get(m, basis, per, seg, met)
    S, E = C.OLD["self"], C.OLD["ent"]
    t = a["trends"]
    q = t[t["basis"] == "2025"]
    ss_q = q[q["segment"] == C.NEW["self"]].set_index("period")
    en_q = q[q["segment"] == C.NEW["ent"]].set_index("period")
    b = a["bridge"]
    ssb = b[(b["segment"] == C.NEW["self"]) & (b["to"].str.len() > 4)].set_index("to")
    bt = a["bridge_total"]
    p = a["pnl"]
    adv = a["advertising"]
    base = a["baseline"]
    mod = bc["model"]
    d = ex["designs"].set_index("design")
    ch = experiment.chosen_design()
    addons = {per: g("2025", per, "Add-Ons", "revenue_k") for per in ("2024Q1", "2024Q2", "2024Q3", "2025Q1", "2025Q2", "2025Q3")}
    return {
        "ss_subs_21": g("2022", "2021", S, "subscribers_k"), "ss_subs_24": g("2022", "2024", S, "subscribers_k"),
        "ss_arpu_21": g("2022", "2021", S, "arpu_usd"), "ss_arpu_24": g("2022", "2024", S, "arpu_usd"),
        "ent_rev_21": g("2022", "2021", E, "revenue_k") / 1000, "ent_rev_24": g("2022", "2024", E, "revenue_k") / 1000,
        "rev_21": p.loc["2021", "revenue"], "rev_24": p.loc["2024", "revenue"],
        "bt": bt, "ss_q": ss_q, "en_q": en_q, "ssb": ssb,
        "adv_21": p.loc["2021", "advertising"], "adv_24": p.loc["2024", "advertising"], "adv": adv,
        "sm_21": p.loc["2021", "sales_marketing_pct"], "sm_24": p.loc["2024", "sales_marketing_pct"],
        "gm_24": p.loc["2024", "gross_margin"], "op_21": p.loc["2021", "operating_income_pct"], "op_24": p.loc["2024", "operating_income_pct"],
        "base": base, "multiple": base["enterprise_arpu"] / base["self_serve_arpu"],
        "ss_run_rate": g("2025", "2025Q3", C.NEW["self"], "revenue_k") * 4 / 1000,
        "addons_9m_24": sum(addons[k] for k in ("2024Q1", "2024Q2", "2024Q3")) / 1000,
        "addons_9m_25": sum(addons[k] for k in ("2025Q1", "2025Q2", "2025Q3")) / 1000,
        "mod": mod, "be": bc["breakeven_uplift"], "sens": bc["sensitivity"], "d": d, "ch": ch,
        "sim": ex["simulation"], "oc": oc, "voi": ex["voi"],
    }


def figures(f: dict) -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    m = analysis.metrics()
    g = lambda per, met: analysis.get(m, "2022", per, C.OLD["self"], met)
    (FIG / "01_self_serve.svg").write_text(charts.index_lines(
        C.YEARS, [("Subscribers", [g(y, "subscribers_k") for y in C.YEARS], "var(--s1)"),
                  ("ARPU", [g(y, "arpu_usd") for y in C.YEARS], "var(--s2)")],
        f"Self-Serve: {pct(f['ss_subs_24'] / f['ss_subs_21'] - 1, 0, True)} subscribers, "
        f"{pct(f['ss_arpu_24'] / f['ss_arpu_21'] - 1, 0, True)} ARPU since 2021",
        "Self-Serve & Add-Ons, year-end subscribers and ARPU, 2021 = 100 (10-K, 2022 basis)"))
    bt = f["bt"]
    (FIG / "02_bridge.svg").write_text(charts.volume_price(
        [(seg, bt.loc[seg, "volume"], bt.loc[seg, "price"]) for seg in bt.index],
        "2021 to 2024: Self-Serve lost on volume what it won on price",
        "Change in revenue by category, split into subscribers (volume) and ARPU (price), US$ millions"))
    per = [f"Q{i}" for i in (1, 2, 3)]
    (FIG / "03_enterprise.svg").write_text(charts.grouped_growth(
        [f"{p} 2025" for p in per],
        [("Enterprise revenue", [f["en_q"].loc[f"2025{p}", "revenue_k"] for p in per], "var(--s1)"),
         ("Enterprise bookings", [f["en_q"].loc[f"2025{p}", "bookings_k"] for p in per], "var(--s2)"),
         ("Self-Serve subscribers", [f["ss_q"].loc[f"2025{p}", "subscribers_k"] for p in per], "var(--muted)")],
        "Enterprise revenue still grows; its bookings " + (f"fell {pct(-f['en_q'].loc['2025Q3', 'bookings_k'])}"
        if f['en_q'].loc['2025Q3', 'bookings_k'] < 0 else f"grew {pct(f['en_q'].loc['2025Q3', 'bookings_k'])}") + " in Q3 2025",
        "Year-on-year change, 2025 quarters against 2024 (10-Q, 2025 basis)"))
    oc = f["oc"]
    labels = ["Scale", "Iterate", "Stop or redesign", "Do not scale"]
    names = {0: "No real uplift", 1: "At break-even", 2: "At plan (1% a year)", 3: "Strong (1.5% a year)"}
    (FIG / "04_decisions.svg").write_text(charts.outcomes(
        [(names[i], {k: r[k] for k in labels if k in r}) for i, r in oc.reset_index(drop=True).iterrows()], labels,
        "The decision rule almost never scales a bet that does not work",
        "Share of 200 simulated tests ending in each decision, by true uplift"))


def write(a, bc, ex, oc) -> dict:
    f = facts(a, bc, ex, oc)
    figures(f)
    mod, d, ch, sim, s = f["mod"], f["d"], f["ch"], f["sim"], f["sens"]
    y = mod["years"]
    L = []
    add = L.append
    add("# Vimeo: where the next dollar comes from")
    add("")
    add("**For:** the business owner of Vimeo Self-Serve and Enterprise")
    add("**Sources:** Vimeo, Inc. annual reports (10-K, covering 2021–2024) and quarterly reports (10-Q, Q1–Q3 2025) "
        "filed with the SEC; every figure traced in "
        "[data/SOURCES.md](../data/SOURCES.md)")
    add("**Status:** an outside-in exercise on public data. Assumptions are mine and labelled; the test results are simulated.")
    add("**Context:** Bending Spoons agreed to buy Vimeo on 10 September 2025 for $7.85 a share, about $1.38 billion in "
        "cash, and completed the deal on 24 November 2025; Vimeo then left Nasdaq, so the Q3 2025 10-Q is its last "
        "quarterly report. This memo reads the business as it stood at the handover and uses nothing published after it.")
    add("")
    add("**Try it:** [the interactive model](https://d0m3n1c0x.github.io/vimeo-growth-case/model/) recomputes the case and the test as you move each assumption.")
    add("")
    add("> The question: Self-Serve has lost subscribers every quarter for three years while price held revenue up. "
        "Where does growth come from next, and how would we know before spending on it?")
    add("")

    add("## The answer")
    add("")
    add(f"- **Self-Serve is running on price.** Subscribers fell {pct(1 - f['ss_subs_24'] / f['ss_subs_21'])} "
        f"from 2021 to 2024 and ARPU rose {pct(f['ss_arpu_24'] / f['ss_arpu_21'] - 1)}. In 2025 subscribers are "
        f"down {pct(-f['ss_q'].loc['2025Q3', 'subscribers_k'])} a year in every quarter, and ARPU growth has accelerated to "
        f"{pct(f['ss_q'].loc['2025Q3', 'arpu_usd'], 0, True)}. Price cannot outrun an 11% annual loss for long.")
    add(f"- **Enterprise carried the growth, and it is slowing.** Enterprise revenue went from "
        f"{usd_m(f['ent_rev_21'])} to {usd_m(f['ent_rev_24'])} between 2021 and 2024, but in Q3 2025 its bookings "
        + (f"fell {pct(-f['en_q'].loc['2025Q3', 'bookings_k'])}" if f['en_q'].loc['2025Q3', 'bookings_k'] < 0
           else f"grew only {pct(f['en_q'].loc['2025Q3', 'bookings_k'])}") + " on the year before.")
    add(f"- **The biggest lever is between the two.** An Enterprise account pays about {f['multiple']:.0f} times a Self-Serve "
        f"one ({usd(f['base']['enterprise_arpu'])} against {usd(f['base']['self_serve_arpu'])} a year), and Vimeo's own "
        "filings say Enterprise is often an upgrade from Self-Serve.")
    add(f"- **The bet:** score the Self-Serve base for team-level signals and route the {pct(C.BET['eligible_share'])} "
        f"with the strongest ones ({mod['eligible']:,.0f} accounts) to sales. At 1 extra upgrade per 100 accounts a year "
        f"its three-year net present value is {usd_m(mod['npv'] / 1e6)}, with payback in year {mod['payback_year']}.")
    add(f"- **The test decides it, not the model.** The bet pays only above {pct(f['be'], 2)} upgrades per account a year. "
        f"A 90-day test cannot see that; a {int(ch['window_days'])}-day one-sided test on the eligible base can, with "
        f"{int(ch['needed']):,} of {ch['available']:,.0f} accounts.")
    add("")

    add("## 1. What the filings say")
    add("")
    add("![Self-Serve subscribers and ARPU](figures/01_self_serve.svg)")
    add("")
    bt = f["bt"]
    add(table(["2021 → 2024, US$ millions", "Volume (subscribers)", "Price (ARPU)", "Rounding", "Change"],
              [[seg, usd_m(r.volume, 1, True), usd_m(r.price, 1, True), usd_m(r.rounding, 1, True), usd_m(r.change, 1, True)]
               for seg, r in bt.iterrows()], "lrrrr"))
    add("")
    add("*Volume is the change in average subscribers at the mid ARPU; price is the change in ARPU at the mid subscriber count. "
        "Rounding is what the published ARPU, rounded to the dollar, leaves unexplained.*")
    add("")
    add("![Volume and price](figures/02_bridge.svg)")
    add("")
    add("In 2025 Vimeo regrouped its categories, so the quarterly series stands apart from the annual one. On the new basis, "
        "the price effect on Self-Serve is growing each quarter:")
    add("")
    ssb = f["ssb"]
    add(table(["Self-Serve, year on year", "Subscribers", "ARPU", "Bookings", "Volume effect", "Price effect"],
              [[f"Q{q[-1]} 2025", pct(f["ss_q"].loc[q, "subscribers_k"], 0, True), pct(f["ss_q"].loc[q, "arpu_usd"], 0, True),
                pct(f["ss_q"].loc[q, "bookings_k"], 0, True), usd_m(ssb.loc[q, "volume"], 1, True), usd_m(ssb.loc[q, "price"], 1, True)]
               for q in ("2025Q1", "2025Q2", "2025Q3")], "lrrrrr"))
    add("")
    add("![Enterprise momentum](figures/03_enterprise.svg)")
    add("")
    adv = f["adv"]
    add(f"**Two observations to test, not conclusions.** Advertising fell from {usd_m(f['adv_21'])} in 2021 to "
        f"{usd_m(f['adv_24'])} in 2024, and Self-Serve average subscribers moved from "
        f"{pct(adv['self_serve_avg_change'].iloc[0], 0, True)} to {pct(adv['self_serve_avg_change'].iloc[-1], 0, True)} a year "
        "over the same years: three data points, consistent with acquisition spend driving the base, not proof of it. "
        f"Meanwhile the company turned an operating margin of {pct(f['op_21'], 0, True)} into {pct(f['op_24'], 0, True)}, "
        f"with sales and marketing down from {pct(f['sm_21'])} to {pct(f['sm_24'])} of revenue.")
    add("")

    add("## 2. Three places to look, sized")
    add("")
    rows = [
        ["More price on Self-Serve", f"Each 1% of ARPU ≈ {usd_m(f['ss_run_rate'] / 100)} a year on a {usd_m(f['ss_run_rate'], 0)} run rate",
         "Already in motion; the open question is how much of the 11% loss price causes", "Second: a price holdout cohort"],
        ["Route Self-Serve teams to Enterprise", f"{usd_m(mod['year3_net_revenue'] / 1e6)} net new revenue in year 3 at plan",
         "Uses the existing base, no new acquisition spend; adds a pipeline as Enterprise bookings slow", "**First**"],
        ["Stop the Add-Ons decline", f"{usd_m(f['addons_9m_24'])} → {usd_m(f['addons_9m_25'])} in the first nine months, "
                                      f"{pct(f['addons_9m_25'] / f['addons_9m_24'] - 1, 0, True)}",
         "Vimeo attributes it to lower bandwidth demand; packaging bandwidth into plans may matter more than selling it", "Third"],
    ]
    add(table(["Bet", "Size", "Why now", "Order"], rows, "llll"))
    add("")

    add("## 3. The business case")
    add("")
    add(f"The model starts from Q3 2025: {f['base']['self_serve_subscribers']:,.0f} Self-Serve subscribers at "
        f"{usd(f['base']['self_serve_arpu'])} a year and Enterprise ARPU of {usd(f['base']['enterprise_arpu'])}. Upgrades start at "
        f"{pct(C.BET['entry_acv_share'])} of the Enterprise average ({usd(mod['acv'])}), keep {pct(C.BET['retention'])} of revenue "
        f"each year after the first, and stop paying their Self-Serve plan, counted as lost every year even for accounts that later leave Enterprise (the conservative choice). The sales team is hired for the plan before the real "
        "uplift is known, so its cost is fixed.")
    add("")
    add(table(["US$", "Year 1", "Year 2", "Year 3"],
              [[label, *[usd(v) for v in y[col]]] for label, col in (
                  ("Net new revenue", "net_revenue"), ("Gross profit", "gross_profit"), ("Account executives", "sales_cost"),
                  ("Outreach", "outreach_cost"), ("Build", "build_cost"), ("**Contribution**", "contribution"))],
              "lrrr"))
    add("")
    add(f"**Net present value {usd_m(mod['npv'] / 1e6)} at {pct(C.BET['discount_rate'])}, payback in year {mod['payback_year']}.** "
        f"Because the team is a fixed cost, value is linear in the uplift, and it is zero at **{pct(f['be'], 2)} upgrades per "
        "eligible account a year**: the bar the test must clear.")
    add("")
    add(table(["Driver", "Low", "High", "NPV at low", "NPV at high"],
              [[r.driver.replace("_", " "), r.low_value, r.high_value, usd_m(r.npv_low / 1e6, 1), usd_m(r.npv_high / 1e6, 1)]
               for r in s.itertuples(index=False)], "lrrrr"))
    add("")
    add("*Sorted by swing. The uplift dominates: it is the one number no filing can provide, which is why the next section exists.*")
    add("")

    add("## 4. How to test it before hiring for it")
    add("")
    add("Randomise eligible accounts 50/50: treatment gets outreach, control gets the product as today. Primary metric: upgrades "
        "to Enterprise in the window. Guardrail: Self-Serve cancellations must not rise by more than half a point per 90 days.")
    add("")
    add(table(["Design", "Needed", "Available", "Feasible"],
              [[name, f"{int(r.needed):,}", f"{r.available:,.0f}", "Yes" if r.feasible else "No"] for name, r in d.iterrows()],
              "lrrl"))
    add("")
    add(f"*Sample sizes to detect the break-even uplift at 80% power, α = 5%. Organic upgrades are assumed at "
        f"{pct(C.TEST['baseline_upgrade_rate'], 1)} in 90 days, a number to read from Vimeo's own data first.*")
    add("")
    add("**The decision rule, in order:** a broken 50/50 split invalidates the test; without a significant uplift there is "
        "nothing to protect; then the cancellations guardrail; then the business bar. Scale only if the uplift is significant "
        "and at least break-even.")
    add("")
    add("![Decision rule](figures/04_decisions.svg)")
    add("")
    oc = f["oc"].reset_index(drop=True)
    add(f"Run 200 times on simulated accounts, the rule scales a bet with no real effect in {pct(oc.loc[0].get('Scale', 0))} of "
        f"tests and a bet at plan in {pct(oc.loc[2].get('Scale', 0))}. The cost: the guardrail stops about "
        f"{pct(oc.loc[2].get('Do not scale', 0))} of good bets by chance, which a larger margin or a longer window would reduce.")
    add("")
    add(f"One simulated run, read with the [workbook's readout sheet](../deliverables/vimeo_upgrade_case.xlsx): control "
        f"{pct(sim['control']['rate'], 2)}, treatment {pct(sim['treatment']['rate'], 2)}, uplift {pct(sim['uplift_yearly_estimate'], 2)} "
        f"a year (one-sided p = {sim['p_one_sided']:.3f}). Decision: *{sim['decision']}*.")
    add("")

    add("## 5. Is the test worth running?")
    add("")
    add("A test costs money and half a year, so it is not free insurance. Put a belief on the real uplift, then compare "
        "three options: launch now, do nothing, or test first and follow the rule. Value is linear in the uplift, so each "
        "option's expected value is a weighted sum over the scenarios; the chance that the test says *Scale* at each uplift "
        f"comes from {C.VOI_RUNS} simulated tests.")
    add("")
    voi = f["voi"]
    t = voi["sceptical"]["table"]
    add(table(["True uplift a year", "Sceptical prior", "Optimistic prior", "NPV if launched now", "Test says Scale"],
              [[pct(r.uplift, 1), pct(C.PRIORS["sceptical"][r.uplift]), pct(C.PRIORS["optimistic"][r.uplift]),
                usd_m(r.npv_launch_now / 1e6, 2), pct(r.p_scale)] for r in t.itertuples(index=False)], "lrrrr"))
    add("")
    add(table(["Expected value", "Sceptical prior", "Optimistic prior"],
              [["Launch now", *[usd_m(voi[k]["launch_now"] / 1e6, 2) for k in ("sceptical", "optimistic")]],
               ["Do nothing", "$0.00M", "$0.00M"],
               ["Test first, then follow the rule", *[usd_m(voi[k]["test_first"] / 1e6, 2) for k in ("sceptical", "optimistic")]],
               ["**Value of running the test**", *[f"**{usd_m(voi[k]['value_of_test'] / 1e6, 2, True)}**" for k in ("sceptical", "optimistic")]],
               ["Best option", *[voi[k]["best"] for k in ("sceptical", "optimistic")]]], "lrr"))
    add("")
    sc, op = voi["sceptical"], voi["optimistic"]
    add(f"**The answer depends on the belief, and that is the point.** If the average expectation sits below break-even "
        f"(sceptical prior, mean {pct(sc['prior_mean'], 2)}), launching blind loses {usd_m(-sc['launch_now'] / 1e6, 2)} in "
        f"expectation and the test is worth {usd_m(sc['value_of_test'] / 1e6, 2)}. If it sits well above "
        f"(optimistic, mean {pct(op['prior_mean'], 2)}), the test costs more than it saves and launching is better by "
        f"{usd_m(-op['value_of_test'] / 1e6, 2)}. The test also has a price in errors: at "
        f"{pct(t.iloc[1].uplift, 1)} a year, below break-even, it still says *Scale* in {pct(t.iloc[1].p_scale)} of runs.")
    add("")
    add("## 6. What I would want to know first")
    add("")
    add("- **The organic upgrade rate** from Self-Serve to Enterprise, by plan and team size: it sets the sample size.")
    add("- **Which signals predict an upgrade** in past data (seats, sign-on attempts, bandwidth, company domains): they define "
        "who is eligible.")
    add("- **Why Self-Serve customers cancel**, by price change and by tenure: it decides whether more price is safe.")
    add("- **Sales capacity**: whether the Enterprise team can absorb about 225 more deals a year, or needs hiring.")
    add("")

    add("## Method and limits")
    add("")
    add("- **Two engines, one answer.** Every figure is computed in pandas and again by live formulas in "
        "[the workbook](../deliverables/vimeo_upgrade_case.xlsx); its Reconciliation sheet checks each pair, and CI recalculates "
        "it with LibreOffice.")
    add("- **Public data only.** Subscriber metrics are transcribed from the filings and checked: categories add up to the "
        "reported revenue, and ARPU × average subscribers reproduces each category's revenue within 2%.")
    add("- **Two bases.** Vimeo regrouped its categories in 2025; the annual and quarterly series are never joined.")
    add("- **Assumptions are mine.** Eligibility, uplift, contract size, retention and costs are judgements, shown in the "
        "sensitivity table; the test results are simulated. Not investment advice.")
    add("")
    C.REPORT.mkdir(exist_ok=True)
    (C.REPORT / "memo.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    return f


def main() -> None:
    import report_html
    write(analysis.run(), business_case.run(), experiment.run(), experiment.operating_characteristics())
    report_html.build()
    print("memo -> report/memo.md, report/index.html")


if __name__ == "__main__":
    main()
