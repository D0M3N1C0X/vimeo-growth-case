"""
Proves the workbook's formulas reproduce the pandas pipeline.

openpyxl writes formulas without results, so a spreadsheet engine has to calculate them
first. Two engines are supported:

    # LibreOffice (what CI uses): recalculate a copy, then check the saved values
    python src/recalc_libreoffice.py deliverables/vimeo_upgrade_case.xlsx build/
    python src/check_workbook.py build/vimeo_upgrade_case.xlsx

    # the pure-Python `formulas` package, on a small sample (quick to run locally)
    python src/check_workbook.py --sample 2    # 2 employees per country, department and level

The check fails on any formula error anywhere in the workbook, and on any row of the
Reconciliation sheet that does not match.
"""

import argparse
import sys
from pathlib import Path

import excel_twin as et
from excel_twin import ERRORS, values_from_formulas, values_from_saved  # noqa: F401  (used by the tests)
from excel_twin.reconcile import Layout

LAYOUT = Layout()


def check(values: dict, sheet_names: list[str], n_checks: int) -> int:
    """The excel-twin check with this repository's layout; 0 when everything matches."""
    report = et.check(values, n_checks, LAYOUT)
    report.print()
    return 0 if report.ok else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("workbook", nargs="?", type=Path, help="a workbook already recalculated by LibreOffice or Excel")
    ap.add_argument("--sample", type=int, help="build the workbook and evaluate it with `formulas` (N is ignored)")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--formulas", action="store_true",
                    help="calculate the given workbook with `formulas` (slow at full size)")
    args = ap.parse_args()

    if args.sample:
        # the whole workbook is small: build it and calculate it in pure Python
        import build_workbook
        from config import ROOT
        path = ROOT / "build" / "workbook_formulas.xlsx"
        f = build_workbook.build(path=path)
        print(f"workbook: {len(f.checks)} checks")
        return check(values_from_formulas(path), f.wb.sheetnames, len(f.checks))

    if not args.workbook:
        ap.error("give a recalculated workbook, or --sample N")
    from openpyxl import load_workbook
    names = load_workbook(args.workbook, read_only=True).sheetnames
    values = values_from_formulas(args.workbook) if args.formulas else values_from_saved(args.workbook)
    # one row per check from row 7, each with an item in column B
    n = sum(1 for (s, r) in values if s.upper() == "RECONCILIATION" and r.startswith("B")
            and r[1:].isdigit() and int(r[1:]) >= 7)
    return check(values, names, n)


if __name__ == "__main__":
    sys.exit(main())
