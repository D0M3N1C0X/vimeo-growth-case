"""The figures quoted in the README are the ones the pipeline produces."""
import build_memo as M
import build_workbook
import config as C
import experiment

README = (C.ROOT / "README.md").read_text(encoding="utf-8")


def test_readme_is_current(a, bc, ex, tmp_path):
    f = M.facts(a, bc, ex, experiment.operating_characteristics(runs=5))
    mod, ch = f["mod"], f["ch"]
    want = [
        f"Subscribers fell {M.pct(1 - f['ss_subs_24'] / f['ss_subs_21'])} from 2021 to 2024 while ARPU rose "
        f"{M.pct(f['ss_arpu_24'] / f['ss_arpu_21'] - 1)}",
        f"down {M.pct(-f['ss_q'].loc['2025Q3', 'subscribers_k'])} a year in every quarter",
        f"ARPU growth has reached {M.pct(f['ss_q'].loc['2025Q3', 'arpu_usd'], 0, True)}",
        f"Revenue went from {M.usd_m(f['ent_rev_21'])} to {M.usd_m(f['ent_rev_24'])}",
        f"bookings fell {M.pct(-f['en_q'].loc['2025Q3', 'bookings_k'])} in Q3 2025",
        f"about {f['multiple']:.0f} times",
        f"pays above {M.pct(f['be'], 2)} upgrades a year",
        f"{M.usd_m(mod['npv'] / 1e6)} net present value",
        f"{int(ch['window_days'])}-day one-sided test on {int(ch['needed']):,} of the {ch['available']:,.0f} eligible accounts",
        f"**{len(build_workbook.build(a, bc, ex, tmp_path / 'w.xlsx').checks)} values**",
    ]
    assert not [w for w in want if w not in README]
