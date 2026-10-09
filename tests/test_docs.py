"""The data dictionary describes every column, tag, segment and metric that the data contains."""
import csv

import config as C

DICTIONARY = (C.ROOT / "docs" / "data-dictionary.md").read_text(encoding="utf-8")


def documented(name: str) -> bool:
    return f"| `{name}` |" in DICTIONARY


def test_every_column_is_documented() -> None:
    for path in (C.FINANCIALS, C.METRICS):
        with path.open(encoding="utf-8") as f:
            columns = next(csv.reader(f))
        assert [c for c in columns if not documented(c)] == [], path.name


def test_every_tag_segment_and_metric_is_documented() -> None:
    with C.FINANCIALS.open(encoding="utf-8") as f:
        tags = {r["tag"] for r in csv.DictReader(f)}
    with C.METRICS.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    names = tags | {r["segment"] for r in rows} | {r["metric"] for r in rows}
    assert sorted(n for n in names if not documented(n)) == []
