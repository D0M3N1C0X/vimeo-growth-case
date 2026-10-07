// The business case and the test design, in the browser. A line-for-line twin of
// src/business_case.py and src/experiment.py: tests/js/check_model.mjs runs this file against
// vectors computed in Python (tests/fixtures/js_vectors.json) and CI fails on any difference.

// Inverse of the standard normal CDF: Wichura's AS241, the algorithm Python's statistics uses.
export function normInv(p) {
  const q = p - 0.5;
  if (Math.abs(q) <= 0.425) {
    const r = 0.180625 - q * q;
    const num = (((((((2.5090809287301226727e+3 * r + 3.3430575583588128105e+4) * r +
      6.7265770927008700853e+4) * r + 4.5921953931549871457e+4) * r + 1.3731693765509461125e+4) * r +
      1.9715909503065514427e+3) * r + 1.3314166789178437745e+2) * r + 3.3871328727963666080e+0) * q;
    const den = (((((((5.2264952788528545610e+3 * r + 2.8729085735721942674e+4) * r +
      3.9307895800092710610e+4) * r + 2.1213794301586595867e+4) * r + 5.3941960214247511077e+3) * r +
      6.8718700749205790830e+2) * r + 4.2313330701600911252e+1) * r + 1.0);
    return num / den;
  }
  let r = q <= 0 ? p : 1 - p;
  r = Math.sqrt(-Math.log(r));
  let num, den;
  if (r <= 5.0) {
    r -= 1.6;
    num = (((((((7.74545014278341407640e-4 * r + 2.27238449892691845833e-2) * r +
      2.41780725177450611770e-1) * r + 1.27045825245236838258e+0) * r + 3.64784832476320460504e+0) * r +
      5.76949722146069140550e+0) * r + 4.63033784615654529590e+0) * r + 1.42343711074968357734e+0);
    den = (((((((1.05075007164441684324e-9 * r + 5.47593808499534494600e-4) * r +
      1.51986665636164571966e-2) * r + 1.48103976427480074590e-1) * r + 6.89767334985100004550e-1) * r +
      1.67638483018380384940e+0) * r + 2.05319162663775882187e+0) * r + 1.0);
  } else {
    r -= 5.0;
    num = (((((((2.01033439929228813265e-7 * r + 2.71155556874348757815e-5) * r +
      1.24266094738807843860e-3) * r + 2.65321895265761230930e-2) * r + 2.96560571828504891230e-1) * r +
      1.78482653991729133580e+0) * r + 5.46378491116411436990e+0) * r + 6.65790464350110377720e+0);
    den = (((((((2.04426310338993978564e-15 * r + 1.42151175831644588870e-7) * r +
      1.84631831751005468180e-5) * r + 7.86869131145613259100e-4) * r + 1.48753612908506148525e-2) * r +
      1.36929880922735805310e-1) * r + 5.99832206555887937690e-1) * r + 1.0);
  }
  const x = num / den;
  return q < 0 ? -x : x;
}

// Three years, a new cohort of upgrades each year, upgrades mid-year; the team is hired for the
// planned uplift, so its cost does not move with the real one.
export function model(bet, base) {
  const eligible = base.self_serve_subscribers * bet.eligible_share;
  const upgrades = eligible * bet.uplift;
  const acv = base.enterprise_arpu * bet.entry_acv_share;
  const lost = bet.cannibalised_self_serve ? base.self_serve_arpu : 0;
  const aes = Math.ceil(eligible * bet.planned_uplift / bet.upgrades_per_ae - 1e-9);
  const years = [];
  let cumulative = 0;
  let npv = 0;
  for (let t = 1; t <= bet.years; t++) {
    let weight = 0;
    let paying = 0;
    for (let c = 1; c <= t; c++) {
      weight += c === t ? 0.5 : bet.retention ** (t - c);
      paying += c === t ? 0.5 : 1.0;
    }
    const enterprise = upgrades * acv * weight;
    const cannibalised = upgrades * lost * paying;
    const net_revenue = enterprise - cannibalised;
    const gross_profit = net_revenue * bet.gross_margin;
    const sales_cost = aes * bet.ae_cost;
    const outreach_cost = eligible * bet.outreach_cost;
    const build_cost = t === 1 ? bet.build_cost : 0;
    const contribution = gross_profit - sales_cost - outreach_cost - build_cost;
    const discount = 1 / (1 + bet.discount_rate) ** t;
    cumulative += contribution;
    npv += contribution * discount;
    years.push({ year: t, weight, enterprise_revenue: enterprise, cannibalised, net_revenue, gross_profit,
      account_executives: aes, sales_cost, outreach_cost, build_cost, contribution, cumulative,
      present_value: contribution * discount });
  }
  const payback = years.find((y) => y.cumulative >= 0);
  return { eligible, upgrades, acv, account_executives: aes, years, npv,
    year3_net_revenue: years[years.length - 1].net_revenue, payback_year: payback ? payback.year : null };
}

// Value is linear in the uplift (fixed team), so break-even has a closed form.
export function breakeven(bet, base) {
  const at0 = model({ ...bet, uplift: 0 }, base).npv;
  const at1 = model({ ...bet, uplift: 1 }, base).npv;
  return -at0 / (at1 - at0);
}

export function sampleSize(p0, p1, alpha, power, oneSided) {
  const za = normInv(1 - alpha / (oneSided ? 1 : 2));
  const zb = normInv(power);
  return Math.ceil((za + zb) ** 2 * (p0 * (1 - p0) + p1 * (1 - p1)) / (p1 - p0) ** 2);
}

export const DESIGNS = [
  ["90 days, two-sided", 90, false, 1.0],
  ["90 days, one-sided", 90, true, 1.0],
  ["180 days, one-sided", 180, true, 1.0],
  ["90 days, one-sided, eligibility doubled", 90, true, 2.0],
];

export function designs(bet, base, test) {
  const available = model(bet, base).eligible;
  const be = breakeven(bet, base);
  return DESIGNS.map(([design, window, oneSided, mult]) => {
    const p0 = test.baseline_upgrade_rate * window / 90;
    const p1 = p0 + (be / mult) * window / 365;
    const perArm = be > 0 ? sampleSize(p0, p1, test.alpha, test.power, oneSided) : Infinity;
    return { design, window_days: window, one_sided: oneSided, control_rate: p0,
      treatment_rate_at_breakeven: p1, per_arm: perArm, needed: 2 * perArm,
      available: available * mult, feasible: 2 * perArm <= available * mult };
  });
}
