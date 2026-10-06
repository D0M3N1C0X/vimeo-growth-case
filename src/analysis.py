"""
What Vimeo's filings say, in numbers: the P&L, each category's revenue split into a volume and a
price effect, and the starting point of the bet. Every function reads data/ and nothing else.

    transcription()  checks the hand-transcribed MD&A tables against the XBRL totals
    pnl()            revenue, margins and cost lines, annual 2021-2024 and Q1-Q3 2024/2025
    bridge()         revenue change by category = volume effect + price effect (+ rounding)
    trends()         year-on-year change in subscribers, ARPU and bookings, by category
    baseline()       the numbers the business case starts from (Q3 2025)
"""
import calendar
import functools

import pandas as pd

import config as C


def financials() -> pd.DataFrame:
    f = pd.read_csv(C.FINANCIALS)
    return f.pivot(index="frame", columns="tag", values="value_usd")


def metrics() -> pd.DataFrame:
    return pd.read_csv(C.METRICS, dtype={"period": str, "basis": str})


def get(m: pd.DataFrame, basis: str, period: str, segment: str, metric: str) -> float:
    r = m[(m["basis"] == basis) & (m["period"] == period) & (m["segment"] == segment) & (m["metric"] == metric)]
    if len(r) != 1:
        raise KeyError((basis, period, segment, metric))
    return float(r["value"].iloc[0])


def days(period: str) -> tuple[int, int]:
    """Days in the period and in its year, for annualised ARPU."""
    y = int(period[:4])
    year = 366 if calendar.isleap(y) else 365
    if len(period) == 4:
        return year, year
    q = int(period[-1])
    start_month = 3 * (q - 1) + 1
    d = sum(calendar.monthrange(y, mo)[1] for mo in range(start_month, start_month + 3))
    return d, year


def implied_revenue_k(arpu: float, avg_k: float, period: str) -> float:
    d, year = days(period)
    return arpu * avg_k * d / year


# ---- Checks on the transcription ---------------------------------------------------------------

def transcription() -> pd.DataFrame:
    m, f = metrics(), financials()
    rows = []
    for (basis, period), g in m[m["metric"] == "revenue_k"].groupby(["basis", "period"]):
        total = f.loc[f"CY{period}", C.REVENUE] / 1000
        rows.append({"check": "categories add up to total revenue", "basis": basis, "period": period,
                     "segment": "all", "reported": total, "computed": g["value"].sum()})
    for (basis, period, seg), g in m.groupby(["basis", "period", "segment"]):
        have = set(g["metric"])
        if {"arpu_usd", "avg_subscribers_k", "revenue_k"} <= have:
            rows.append({"check": "revenue = ARPU x average subscribers", "basis": basis, "period": period,
                         "segment": seg, "reported": get(m, basis, period, seg, "revenue_k"),
                         "computed": implied_revenue_k(get(m, basis, period, seg, "arpu_usd"),
                                                       get(m, basis, period, seg, "avg_subscribers_k"), period)})
    t = pd.DataFrame(rows)
    t["gap"] = t["computed"] / t["reported"] - 1
    return t


# ---- P&L -------------------------------------------------------------------------------------

def pnl() -> pd.DataFrame:
    f = financials()
    periods = [f"CY{y}" for y in C.YEARS] + [f"CY{y}{q}" for y in ("2024", "2025") for q in C.QUARTERS]
    p = pd.DataFrame(index=[x[2:] for x in periods])
    get_ = lambda tag: [f.loc[x, tag] / 1e6 if x in f.index and pd.notna(f.loc[x, tag]) else float("nan") for x in periods]
    p["revenue"] = get_(C.REVENUE)
    p["cost_of_revenue"] = get_("CostOfGoodsAndServicesSold")
    p["sales_marketing"] = get_("SellingAndMarketingExpense")
    p["research_development"] = get_("ResearchAndDevelopmentExpense")
    p["general_admin"] = get_("GeneralAndAdministrativeExpense")
    p["operating_income"] = get_("OperatingIncomeLoss")
    p["advertising"] = get_("AdvertisingExpense")
    p["gross_margin"] = 1 - p["cost_of_revenue"] / p["revenue"]
    for c in ("sales_marketing", "research_development", "general_admin", "operating_income", "advertising"):
        p[f"{c}_pct"] = p[c] / p["revenue"]
    return p


# ---- Revenue bridge: volume and price --------------------------------------------------------

def _bridge_rows(m, basis, p0, p1, segments):
    rows = []
    for seg in segments:
        a0, a1 = get(m, basis, p0, seg, "avg_subscribers_k"), get(m, basis, p1, seg, "avg_subscribers_k")
        u0, u1 = get(m, basis, p0, seg, "arpu_usd"), get(m, basis, p1, seg, "arpu_usd")
        r0, r1 = get(m, basis, p0, seg, "revenue_k"), get(m, basis, p1, seg, "revenue_k")
        # ARPU is annualised: bring each period's back to revenue per average subscriber in that period,
        # so a leap-year quarter's extra day lands in the price effect instead of the residual
        d0, y0 = days(p0)
        d1, y1 = days(p1)
        u0, u1 = u0 * d0 / y0, u1 * d1 / y1
        volume = (a1 - a0) * (u0 + u1) / 2          # midpoint split: volume + price = change in ARPU x avg
        price = (u1 - u0) * (a0 + a1) / 2
        rows.append({"from": p0, "to": p1, "segment": seg, "revenue_from": r0 / 1000, "revenue_to": r1 / 1000,
                     "volume": volume / 1000, "price": price / 1000,
                     "rounding": (r1 - r0 - volume - price) / 1000})
    return rows


def bridge() -> pd.DataFrame:
    m = metrics()
    rows = []
    for y0, y1 in zip(C.YEARS[:-1], C.YEARS[1:]):
        rows += _bridge_rows(m, "2022", y0, y1, list(C.OLD.values()))
    for q in C.QUARTERS:
        rows += _bridge_rows(m, "2025", f"2024{q}", f"2025{q}", list(C.NEW.values()))
    b = pd.DataFrame(rows)
    b["change"] = b["revenue_to"] - b["revenue_from"]
    return b


def bridge_total(b: pd.DataFrame, years=("2021", "2024")) -> pd.DataFrame:
    """2021 to 2024 on the 2022 basis, by category: the sum of the three annual bridges."""
    sel = b[b["from"].isin(C.YEARS) & (b["from"] >= years[0]) & (b["to"] <= years[1])]
    return sel.groupby("segment", sort=False)[["volume", "price", "rounding", "change"]].sum()


# ---- Trends ----------------------------------------------------------------------------------

def trends() -> pd.DataFrame:
    m = metrics()
    rows = []
    for basis, pairs, segs in (("2022", list(zip(C.YEARS[:-1], C.YEARS[1:])), C.OLD.values()),
                               ("2025", [(f"2024{q}", f"2025{q}") for q in C.QUARTERS], C.NEW.values())):
        for p0, p1 in pairs:
            for seg in segs:
                row = {"basis": basis, "period": p1, "segment": seg}
                for met in ("subscribers_k", "arpu_usd", "bookings_k", "revenue_k"):
                    row[met] = get(m, basis, p1, seg, met) / get(m, basis, p0, seg, met) - 1
                rows.append(row)
    return pd.DataFrame(rows)


def advertising_vs_subscribers() -> pd.DataFrame:
    """Advertising spend and Self-Serve average subscribers, year on year. Three points: an
    observation to test, not a causal estimate."""
    p, m = pnl(), metrics()
    rows = []
    for y0, y1 in zip(C.YEARS[:-1], C.YEARS[1:]):
        rows.append({"year": y1, "advertising": p.loc[y1, "advertising"],
                     "advertising_change": p.loc[y1, "advertising"] / p.loc[y0, "advertising"] - 1,
                     "self_serve_avg_change": get(m, "2022", y1, C.OLD["self"], "avg_subscribers_k")
                     / get(m, "2022", y0, C.OLD["self"], "avg_subscribers_k") - 1})
    return pd.DataFrame(rows)


# ---- Starting point of the bet -----------------------------------------------------------------

@functools.lru_cache(maxsize=None)
def _baseline() -> tuple:
    m = metrics()
    q = "2025Q3"
    return {
        "period": q,
        "self_serve_subscribers": get(m, "2025", q, C.NEW["self"], "subscribers_k") * 1000,
        "self_serve_arpu": get(m, "2025", q, C.NEW["self"], "arpu_usd"),
        "enterprise_subscribers": get(m, "2025", q, C.NEW["ent"], "subscribers_k") * 1000,
        "enterprise_arpu": get(m, "2025", q, C.NEW["ent"], "arpu_usd"),
        "enterprise_revenue_q": get(m, "2025", q, C.NEW["ent"], "revenue_k") * 1000,
    }.items()


def baseline() -> dict:
    return dict(_baseline())


def run() -> dict:
    b = bridge()
    return {"transcription": transcription(), "pnl": pnl(), "bridge": b, "bridge_total": bridge_total(b),
            "trends": trends(), "advertising": advertising_vs_subscribers(), "baseline": baseline()}


if __name__ == "__main__":
    pd.set_option("display.width", 200)
    o = run()
    print(o["pnl"].round(3).T)
    print(o["bridge"].round(2))
    print(o["bridge_total"].round(1))
    print(o["trends"].round(3))
    print(o["advertising"].round(3))
    print(o["baseline"])
    t = o["transcription"]
    print("max ARPU gap", t["gap"].abs().max().round(4))
