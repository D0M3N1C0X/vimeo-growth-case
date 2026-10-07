// Recomputes every Python vector with web/model.js. Exit code 1 on any difference.
import { readFileSync } from "node:fs";
import { model, breakeven, designs } from "../../web/model.js";

const { base, cases } = JSON.parse(readFileSync(new URL("../fixtures/js_vectors.json", import.meta.url)));
const close = (a, b, rel = 1e-9) => Math.abs(a - b) <= rel * Math.max(1, Math.abs(b));
let failures = 0, checks = 0;
const expect = (ok, what) => { checks++; if (!ok) { failures++; if (failures <= 20) console.error("mismatch:", what); } };

cases.forEach((c, i) => {
  const m = model(c.bet, base);
  expect(close(m.npv, c.npv), `case ${i} npv ${m.npv} vs ${c.npv}`);
  expect(m.payback_year === c.payback_year, `case ${i} payback ${m.payback_year} vs ${c.payback_year}`);
  expect(close(m.eligible, c.eligible) && close(m.acv, c.acv), `case ${i} eligible/acv`);
  c.years.forEach((y, t) => {
    for (const k of ["net_revenue", "gross_profit", "sales_cost", "outreach_cost", "contribution", "present_value"])
      expect(close(m.years[t][k], y[k]), `case ${i} year ${t + 1} ${k}`);
  });
  expect(close(breakeven(c.bet, base), c.breakeven, 1e-7), `case ${i} breakeven ${breakeven(c.bet, base)} vs ${c.breakeven}`);
  const d = designs(c.bet, base, c.test);
  c.designs.forEach((e, k) => {
    expect(d[k].per_arm === e.per_arm, `case ${i} ${e.design} per arm ${d[k].per_arm} vs ${e.per_arm}`);
    expect(d[k].feasible === e.feasible, `case ${i} ${e.design} feasible`);
  });
});
console.log(`${checks - failures} of ${checks} checks match across ${cases.length} cases`);
process.exit(failures ? 1 : 0);
