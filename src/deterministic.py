"""
Office files are zip archives stamped with the time they were written, so the same workbook
built twice differs byte for byte. Rewriting every entry with a fixed timestamp, and pinning
the created/modified dates inside docProps/core.xml, makes the content reproducible.

Compressed bytes can still differ between zlib builds, so CI compares the decompressed
entries (``same_content``) rather than the files themselves.

    python src/deterministic.py --check deliverables/vimeo_upgrade_case.xlsx
"""
import re
import subprocess
import sys
import zipfile
from io import BytesIO
from pathlib import Path

FIXED = (2026, 1, 1, 0, 0, 0)
FIXED_ISO = b"2026-01-01T00:00:00Z"
_STAMP = re.compile(rb"(<dcterms:(?:created|modified)[^>]*>)[^<]*(</dcterms:(?:created|modified)>)")


OFFICE = (".xlsx", ".xlsm", ".docx", ".pptx")


def _normalised(blob: bytes) -> bytes:
    """The same archive with fixed timestamps - including the workbooks embedded in charts."""
    with zipfile.ZipFile(BytesIO(blob)) as src:
        entries = [(info.filename, src.read(info.filename)) for info in src.infolist()]
    out = BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as dst:
        for name, data in entries:
            if name == "docProps/core.xml":
                data = _STAMP.sub(rb"\g<1>" + FIXED_ISO + rb"\g<2>", data)
            elif name.endswith(OFFICE):
                data = _normalised(data)
            info = zipfile.ZipInfo(name, date_time=FIXED)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            dst.writestr(info, data)
    return out.getvalue()


def normalise(path: Path) -> None:
    path.write_bytes(_normalised(path.read_bytes()))


def _entries(blob: bytes) -> dict:
    with zipfile.ZipFile(BytesIO(blob)) as z:
        return {n: (_entries(z.read(n)) if n.endswith(OFFICE) else z.read(n)) for n in z.namelist()}


def same_content(a: bytes, b: bytes) -> bool:
    return _entries(a) == _entries(b)


def differences(a: bytes, b: bytes) -> list[str]:
    """Which entries differ, with a little context around the first change in each."""
    ea, eb = _entries(a), _entries(b)
    out = []
    for name in sorted(set(ea) | set(eb)):
        x, y = ea.get(name), eb.get(name)
        if x == y:
            continue
        if not isinstance(x, bytes) or not isinstance(y, bytes):
            out.append(f"{name}: added, removed or an embedded file changed")
            continue
        i = next((k for k in range(min(len(x), len(y))) if x[k] != y[k]), min(len(x), len(y)))
        out.append(f"{name}: {x[max(0, i - 60):i + 60]!r} -> {y[max(0, i - 60):i + 60]!r}")
    return out


def main(paths: list[str]) -> int:
    failed = 0
    for p in paths:
        committed = subprocess.run(["git", "show", f"HEAD:{p}"], capture_output=True, check=True).stdout
        if same_content(committed, Path(p).read_bytes()):
            print(f"same content: {p}")
        else:
            print(f"::error::{p} changed when rebuilt - the build is not deterministic")
            for line in differences(committed, Path(p).read_bytes())[:10]:
                print("  " + line)
            failed += 1
    return failed


if __name__ == "__main__":
    if sys.argv[1:2] != ["--check"] or len(sys.argv) < 3:
        raise SystemExit("usage: deterministic.py --check FILE [FILE ...]")
    raise SystemExit(main(sys.argv[2:]))
