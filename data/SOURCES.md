# Sources

All figures come from Vimeo, Inc. filings with the US Securities and Exchange Commission (CIK 0001837686),
retrieved on 6 October 2026 through EDGAR in a browser. SEC servers refused scripted requests from the
network used, so the files here are transcriptions, checked by the tests (see below).

| File | What | Where it comes from |
|---|---|---|
| `sec_financials.csv` | Revenue, cost of revenue, operating expenses, operating and net income, advertising, deferred revenue | XBRL company facts, `https://data.sec.gov/api/xbrl/companyfacts/CIK0001837686.json`; one accession number per value |
| `operating_metrics.csv` | Subscribers, average subscribers, ARPU, bookings and revenue by category | Management's Discussion and Analysis of each filing: 10-K FY2022, FY2023, FY2024 and 10-Q Q1, Q2, Q3 2025 |

## Two bases that must not be joined

- **2022 basis** (10-K FY2022–FY2024): Self-Serve & Add-Ons, Vimeo Enterprise, Other.
- **2025 basis** (10-Q 2025, with restated 2024 quarters): Self-Serve, Vimeo Enterprise, OTT, plus Add-Ons and Other
  as revenue lines without subscriber metrics.

Vimeo changed the definitions in the first quarter of 2025. The analysis keeps the two series apart.

## How the transcription is checked

- Revenue by category adds up to total revenue in the XBRL facts, for every year and quarter.
- Revenue ≈ ARPU × average subscribers (annualised for quarters), within the rounding of ARPU to the dollar.

Filing index: `https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001837686&type=10-`
