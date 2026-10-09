# Data dictionary

Two files in `data/`, both transcribed from Vimeo's SEC filings (see [SOURCES.md](../data/SOURCES.md)).
`tests/test_docs.py` fails if a column, metric or tag appears in the data without an entry here.

## `data/sec_financials.csv`: the P&L and one balance, from XBRL

One row per figure, one figure per filing period.

| Column | Type | Meaning |
|---|---|---|
| `tag` | text | The US-GAAP XBRL element, exactly as filed (list below) |
| `frame` | text | The SEC period frame: `CY2024` a calendar year, `CY2024Q1` a quarter, `CY2024Q4I` an instant at the end of the period (balances) |
| `value_usd` | integer | The value in US dollars, as filed (not in thousands) |
| `accession` | text | Accession number of the filing the value comes from, to find it on EDGAR |

| Tag | What it is |
|---|---|
| `RevenueFromContractWithCustomerExcludingAssessedTax` | Revenue |
| `CostOfGoodsAndServicesSold` | Cost of revenue |
| `SellingAndMarketingExpense` | Sales and marketing |
| `ResearchAndDevelopmentExpense` | Research and development |
| `GeneralAndAdministrativeExpense` | General and administrative |
| `OperatingIncomeLoss` | Operating income (loss) |
| `NetIncomeLoss` | Net income (loss) |
| `AdvertisingExpense` | Advertising, part of sales and marketing, disclosed in the notes |
| `ContractWithCustomerLiabilityCurrent` | Deferred revenue, current: a balance, so its frames are instants |

## `data/operating_metrics.csv`: subscribers, ARPU, bookings and revenue by category

Transcribed from Management's Discussion and Analysis; one row per metric, category and period.

| Column | Type | Meaning |
|---|---|---|
| `basis` | text | `2022` for the categories used in the 10-K filings for 2022–2024, `2025` for those introduced in the first quarter of 2025. The two are never joined |
| `period` | text | `2024` a fiscal year, `2025Q1` a quarter |
| `period_type` | text | `FY` or `Q` |
| `segment` | text | The category as Vimeo names it (list below) |
| `metric` | text | What the value measures (list below) |
| `value` | number | The value, in the unit the metric name gives |
| `accession` | text | Accession number of the filing |
| `document` | text | The filing's primary document on EDGAR |

| Segment | Basis | What it is |
|---|---|---|
| `Self-Serve & Add-Ons` | 2022 | Plans bought online, with add-ons |
| `Vimeo Enterprise` | both | Contracts sold by the sales team |
| `Other` | 2022 | The third category in the 2022–2024 filings, as Vimeo labels it; the 2025 basis splits it differently |
| `Self-Serve` | 2025 | Plans bought online, without add-ons |
| `Add-Ons` | 2025 | Add-on revenue, reported without subscriber metrics |
| `OTT` | 2025 | Vimeo's streaming-channel product |

| Metric | Unit | Meaning |
|---|---|---|
| `subscribers_k` | thousands | Subscribers at the end of the period |
| `avg_subscribers_k` | thousands | Average subscribers over the period |
| `arpu_usd` | US dollars a year | Average revenue per user, annualised by Vimeo even for quarters |
| `bookings_k` | thousands of US dollars | Bookings in the period |
| `revenue_k` | thousands of US dollars | Revenue in the period |
