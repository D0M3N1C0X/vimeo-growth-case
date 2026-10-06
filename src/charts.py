"""
Four SVG charts for the memo, hand-written like the ones in pay-transparency-readiness-kit:
validated reference palette, light and dark steps inside each file, a <title> on every mark.
"""
from html import escape

STYLE = """<style>
  svg { --surface:#fcfcfb; --ink:#0b0b0b; --ink2:#52514e; --muted:#898781; --grid:#e1e0d9; --axis:#c3c2b7;
        --s1:#2a78d6; --s2:#eb6834; --s3:#1baf7a; --base:#0b0b0b; --up:#e34948; --down:#2a78d6; }
  @media (prefers-color-scheme: dark) {
    svg { --surface:#1a1a19; --ink:#ffffff; --ink2:#c3c2b7; --muted:#898781; --grid:#2c2c2a; --axis:#383835;
          --s1:#3987e5; --s2:#d95926; --s3:#199e70; --base:#ffffff; --up:#e66767; --down:#3987e5; }
  }
  text { font-family: system-ui, -apple-system, "Segoe UI", sans-serif; fill: var(--ink2); font-size: 12px; }
  .title { fill: var(--ink); font-size: 15px; font-weight: 600; }
  .muted { fill: var(--muted); font-size: 11px; }
  .val { fill: var(--ink); font-variant-numeric: tabular-nums; paint-order: stroke; stroke: var(--surface);
         stroke-width: 4px; stroke-linejoin: round; }
  .inbar { fill: #ffffff; font-weight: 600; font-variant-numeric: tabular-nums; }
</style>"""


def _svg(w, h, body, label):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" '
            f'aria-label="{escape(label)}">{STYLE}<rect width="{w}" height="{h}" rx="8" fill="var(--surface)"/>'
            f'{"".join(body)}</svg>\n')



def _scale(d0, d1, r0, r1):
    return lambda v: r0 + (v - d0) / (d1 - d0) * (r1 - r0)


def _path(points):
    return "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in points)


def pct(x, d=0, signed=False):
    sign = ("+" if x > 0 else "−" if x < 0 else "") if signed else ("−" if x < 0 else "")
    return f"{sign}{abs(x) * 100:.{d}f}%"


def usd_m(x, d=1, signed=False):
    sign = ("+" if x > 0 else "−" if x < 0 else "") if signed else ("−" if x < 0 else "")
    return f"{sign}${abs(x):,.{d}f}M"


def index_lines(periods, series, title, subtitle):
    """series: (label, [values], colour var). Indexed to the first period = 100."""
    W, H, x0, x1, y0, y1 = 720, 380, 70, 600, 310, 90
    idx = [(lab, [v / vals[0] * 100 for v in vals], c) for lab, vals, c in series]
    lo = min(min(v) for _, v, _ in idx) - 5
    hi = max(max(v) for _, v, _ in idx) + 5
    x = _scale(0, len(periods) - 1, x0, x1)
    y = _scale(lo, hi, y0, y1)
    body = [f'<text class="title" x="24" y="34">{escape(title)}</text>', f'<text x="24" y="56">{escape(subtitle)}</text>']
    for v in range(int(lo // 10 * 10 + 10), int(hi) + 1, 10):
        body.append(f'<line x1="{x0}" y1="{y(v):.1f}" x2="{x1}" y2="{y(v):.1f}" stroke="var(--grid)"/>')
        body.append(f'<text class="muted" x="{x0 - 8}" y="{y(v) + 4:.1f}" text-anchor="end">{v}</text>')
    body.append(f'<line x1="{x0}" y1="{y(100):.1f}" x2="{x1}" y2="{y(100):.1f}" stroke="var(--axis)" stroke-width="1.5"/>')
    for i, per in enumerate(periods):
        body.append(f'<text class="muted" x="{x(i):.1f}" y="{y0 + 22}" text-anchor="middle">{escape(per)}</text>')
    for lab, vals, c in idx:
        pts = [(x(i), y(v)) for i, v in enumerate(vals)]
        body.append(f'<path d="{_path(pts)}" fill="none" stroke="{c}" stroke-width="2.5"/>')
        for (px, py), v, per in zip(pts, vals, periods):
            body.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="4" fill="{c}"><title>{escape(lab)} {per}: {v:.0f}</title></circle>')
        body.append(f'<text class="val" x="{pts[-1][0] + 10:.1f}" y="{pts[-1][1] + 4:.1f}" style="fill:{c}">{escape(lab)} {vals[-1]:.0f}</text>')
    return _svg(W, H, body, title)


def volume_price(rows, title, subtitle):
    """rows: (segment, volume, price) in US$ millions. Two bars per segment from zero."""
    W, top, band = 720, 110, 74
    H = top + band * len(rows) + 30
    x0, x1 = 210, W - 70
    m = max(max(abs(v), abs(p)) for _, v, p in rows) * 1.15
    x = _scale(-m, m, x0 + 90, x1)   # room for labels left of negative bars
    body = [f'<text class="title" x="24" y="34">{escape(title)}</text>', f'<text x="24" y="56">{escape(subtitle)}</text>']
    for k, (name, colour) in enumerate((("Volume: subscribers", "var(--s1)"), ("Price: ARPU", "var(--s2)"))):
        lx = x0 + k * 200
        body.append(f'<rect x="{lx}" y="76" width="12" height="12" rx="2" fill="{colour}"/><text x="{lx + 18}" y="86">{name}</text>')
    body.append(f'<line x1="{x(0):.1f}" y1="{top - 8}" x2="{x(0):.1f}" y2="{H - 24}" stroke="var(--base)" stroke-width="1.5"/>')
    for i, (seg, vol, pri) in enumerate(rows):
        y = top + i * band
        body.append(f'<text x="{x0 - 14}" y="{y + 30}" text-anchor="end">{escape(seg)}</text>')
        for j, (v, colour, lab) in enumerate(((vol, "var(--s1)", "volume"), (pri, "var(--s2)", "price"))):
            yy = y + 6 + j * 28
            a, b = sorted((x(0), x(v)))
            body.append(f'<rect x="{a:.1f}" y="{yy}" width="{max(b - a, 1):.1f}" height="22" rx="3" fill="{colour}">'
                        f'<title>{escape(seg)} {lab}: {usd_m(v, 1, True)}</title></rect>')
            tx, anchor = (b + 8, "start") if v >= 0 else (a - 8, "end")
            body.append(f'<text class="val" x="{tx:.1f}" y="{yy + 16}" text-anchor="{anchor}">{usd_m(v, 1, True)}</text>')
    return _svg(W, H, body, title)


def grouped_growth(periods, series, title, subtitle):
    """series: (label, [yoy], colour). Vertical grouped bars around zero."""
    W, H, x0, x1, y0, y1 = 720, 380, 70, 690, 320, 100
    vals = [v for _, vs, _ in series for v in vs]
    lo, hi = min(0, min(vals)) - 0.05, max(vals) + 0.08
    y = _scale(lo, hi, y0, y1)
    group = (x1 - x0) / len(periods)
    bw = group * 0.7 / len(series)
    body = [f'<text class="title" x="24" y="34">{escape(title)}</text>', f'<text x="24" y="56">{escape(subtitle)}</text>']
    for k, (lab, _, c) in enumerate(series):
        lx = x0 + k * 190
        body.append(f'<rect x="{lx}" y="72" width="12" height="12" rx="2" fill="{c}"/><text x="{lx + 18}" y="82">{escape(lab)}</text>')
    t = round(lo, 1)
    while t <= hi:
        body.append(f'<line x1="{x0}" y1="{y(t):.1f}" x2="{x1}" y2="{y(t):.1f}" stroke="var(--grid)"/>')
        body.append(f'<text class="muted" x="{x0 - 8}" y="{y(t) + 4:.1f}" text-anchor="end">{pct(t, 0, True)}</text>')
        t = round(t + 0.1, 1)
    body.append(f'<line x1="{x0}" y1="{y(0):.1f}" x2="{x1}" y2="{y(0):.1f}" stroke="var(--base)" stroke-width="1.5"/>')
    for i, per in enumerate(periods):
        gx = x0 + i * group + group * 0.15
        body.append(f'<text class="muted" x="{x0 + i * group + group / 2:.1f}" y="{y0 + 24}" text-anchor="middle">{escape(per)}</text>')
        for k, (lab, vs, c) in enumerate(series):
            v = vs[i]
            bx = gx + k * bw
            a, b = sorted((y(0), y(v)))
            body.append(f'<rect x="{bx:.1f}" y="{a:.1f}" width="{bw - 4:.1f}" height="{max(b - a, 1):.1f}" rx="2" fill="{c}">'
                        f'<title>{escape(lab)} {per}: {pct(v, 0, True)}</title></rect>')
            ty = a - 6 if v >= 0 else b + 16
            body.append(f'<text class="val" x="{bx + (bw - 4) / 2:.1f}" y="{ty:.1f}" text-anchor="middle">{pct(v, 0, True)}</text>')
    return _svg(W, H, body, title)


def outcomes(rows, labels, title, subtitle):
    """rows: (true uplift label, {decision: share}). One stacked bar per true uplift."""
    colours = {"Scale": "var(--s3)", "Iterate": "var(--s1)", "Stop or redesign": "var(--muted)", "Do not scale": "var(--s2)"}
    W, top, band = 720, 120, 46
    H = top + band * len(rows) + 20
    x0, x1 = 200, W - 40
    x = _scale(0, 1, x0, x1)
    body = [f'<text class="title" x="24" y="34">{escape(title)}</text>', f'<text x="24" y="56">{escape(subtitle)}</text>']
    for k, lab in enumerate(labels):
        lx = 24 + k * 170
        body.append(f'<rect x="{lx}" y="78" width="12" height="12" rx="2" fill="{colours[lab]}"/><text x="{lx + 18}" y="88">{escape(lab)}</text>')
    for i, (name, shares) in enumerate(rows):
        yy = top + i * band
        body.append(f'<text x="{x0 - 12}" y="{yy + 19}" text-anchor="end">{escape(name)}</text>')
        start = 0.0
        for lab in labels:
            v = shares.get(lab, 0.0)
            if v <= 0:
                continue
            body.append(f'<rect x="{x(start):.1f}" y="{yy + 4}" width="{x(start + v) - x(start):.1f}" height="24" fill="{colours[lab]}">'
                        f'<title>{escape(name)}: {escape(lab)} {pct(v)}</title></rect>')
            if v >= 0.08:
                cls = "inbar"
                body.append(f'<text class="{cls}" x="{x(start + v / 2):.1f}" y="{yy + 21}" text-anchor="middle">{pct(v)}</text>')
            start += v
    return _svg(W, H, body, title)
