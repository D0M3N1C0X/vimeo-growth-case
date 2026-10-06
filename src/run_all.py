"""
The whole case in one command:

    python src/run_all.py

filings -> analysis -> business case -> test design and simulated readout -> workbook -> memo.
Deterministic: the same data and seeds give the same outputs.
"""
import time

import analysis
import build_memo
import build_workbook
import business_case
import experiment
import report_html


def main() -> None:
    start = time.perf_counter()
    a, bc, ex = analysis.run(), business_case.run(), experiment.run()
    w = build_workbook.build(a, bc, ex)
    print(f"workbook -> deliverables/vimeo_upgrade_case.xlsx ({len(w.checks)} reconciliation checks)")
    build_memo.write(a, bc, ex, experiment.operating_characteristics())
    report_html.build()
    print("memo -> report/memo.md, report/index.html, report/figures/")
    print(f"done in {time.perf_counter() - start:.1f}s")


if __name__ == "__main__":
    main()
