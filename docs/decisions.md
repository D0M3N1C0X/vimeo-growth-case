# Decision log

The choices that shape the numbers, with the alternative each one replaced. Assumption values are in
[assumptions.md](assumptions.md); this page is about method.

| # | Decision | Alternative not taken | Why |
|---|---|---|---|
| D1 | Keep the 2022 and 2025 category bases apart; never chain them | Map the old categories onto the new ones to get one long series | Vimeo redefined the categories in Q1 2025 and restated only the 2024 quarters. Any mapping would be my invention presented as Vimeo's data |
| D2 | Split each revenue change into volume and price at the midpoint (volume at mean ARPU, price at mean subscribers) | Volume first at the old price, then price (Laspeyres) | The midpoint split does not depend on the order; the two effects add up to the change with no interaction term |
| D3 | Bring the annualised ARPU back to the days in each period before the split | Use ARPU as published | ARPU is annualised even for quarters. Without the correction, the leap day in Q1 2024 lands in the residual instead of in the price effect |
| D4 | Hire the sales team for the planned uplift, before the real one is known: a fixed cost | Make sales cost scale with the upgrades actually won | That is how a team gets hired. It also makes value a straight line in the real uplift, so the break-even is a single number the test can aim at |
| D5 | Count the lost Self-Serve plan every year, even for accounts that later leave Enterprise | Stop counting it when the account churns | Conservative: it can only lower the value of the bet |
| D6 | Compute the break-even twice: by bisection in Python, in closed form in the workbook | One method only | Two methods that agree are a check on both; the workbook reconciliation compares them |
| D7 | Size the test on the break-even uplift, not on the planned one | Size it on the plan (1%) | A test that cannot see the break-even cannot decide whether to scale. Only the 180-day one-sided design can, with 20,982 of 22,558 accounts |
| D8 | Decide with a rule fixed before the data: stop if the one-sided lower bound is not above zero, scale if the estimate clears break-even, iterate otherwise; a sample-ratio check and a churn guardrail come first | Read the result and decide afterwards | A rule written in advance can have its error rates measured. They are reported, including its weak spot: at a true 0.4% uplift it still says *Scale* in 14% of runs |
| D9 | Value the test under two priors, sceptical and optimistic | One prior, or none | The answer flips between them, and showing that is the point: whether a test is worth running depends on the belief before it |
| D10 | Simulate the test on accounts drawn at known rates | Present invented results as if observed | No real test exists. Simulation shows the rule working on data whose truth is known, and is labelled as such everywhere |
| D11 | Stop at the Q3 2025 10-Q | Use news or estimates for later periods | Bending Spoons completed the acquisition on 24 November 2025 and Vimeo stopped filing; nothing later is comparable or verifiable |
