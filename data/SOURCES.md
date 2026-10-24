# Data sources log

One row per downloaded public file. Fill in when you download, not later. Do not commit large copies of public lists; commit this log and keep the files local or in `data/registries/` only if the site's terms allow it.

| File | Source page (URL) | Downloaded (date, IST) | By | SHA-256 | Notes |
|---|---|---|---|---|---|
| sebi_brokers.csv | sebi.gov.in intermediaries list | 23 Oct 2026 | lead | dfa85ada37a7b0d57ee4ccb188ed8db20d45c42ecf5b0a67e5caf9da9c053091 | 5002 Registered Stock Brokers in equity segment (intmId=30); scripts/fetch_sebi.py; fetched with --ip because local DNS could not resolve sebi.gov.in |
| sebi_investment_advisers.csv | sebi.gov.in intermediaries list | 23 Oct 2026 | lead | d1c8e060fc5daaf7031a1a9fb4c8683e5744d0610d4e8b0adfd9b4aba2fac0d3 | 1062 Investment Advisers (intmId=13); scripts/fetch_sebi.py |
| sebi_research_analysts.csv | sebi.gov.in intermediaries list | 23 Oct 2026 | lead | e1c7e3cf79aab1e7fb4f5977a8fdfcc02031a33672e928cb97b93a893ca9ea85 | 2324 Research Analysts (intmId=14); scripts/fetch_sebi.py |
| rbi_alert_list.csv | rbi.org.in Alert List (converted from PDF) | 23 Oct 2026 | lead | 0c5cf65e022b75e8125d05a517b00d2666d2697642aeeec28949949a912346e8 | Typed from PDF 'Alert List (Updated as on November 19, 2025)', 95 entries, rbidocs.rbi.org.in/rdocs/Content/PDFs/ALERTLIST10022023CC5FC4ACD619431497A56B6894188478.PDF (PDF SHA-256 4b60d555d6296ac688d98df3b36f34bb60840ce5b0d276f048d16a9faa705d7c) |
| nse_equity.csv | nseindia.com list of securities | 23 Oct 2026 | lead | 6d8b5e219f2877136346831610975a1286f6aac3591d7566d78a22556adbab6a | from nsearchives.nseindia.com/content/equities/EQUITY_L.csv |
| bse_equity.csv | bseindia.com list of scrips | 23 Oct 2026 | lead | 9409a1479a9a45b51b5a42737ee1135dc5161aa0e542705c347cc3b5764faadf | 5120 Active Equity scrips from api.bseindia.com ListofScripData, fetched in a browser and saved as CSV |
| rebit_equities_schema | specifications.rebit.org.in .../documentation/equities.html | 23 Oct 2026 | lead | 0d953e9477edf37d582b17709c04295148e084f88845f591147160da6829086a | saved as data/schemas/rebit_equities.html; real URL specifications.rebit.org.in/api_schema/account_aggregator/documentation/equities.html (XSD docs) |
| rebit_mutual_funds_schema | specifications.rebit.org.in .../documentation/mutual_funds.html | 23 Oct 2026 | lead | 0b63b63cd82b09f088613de9a6fc5c54a5caf0e98c4f4ae43dff06eeee7d54e6 | saved as data/schemas/rebit_mutual_funds.html; .../account_aggregator/documentation/mutual_funds.html |
| sahamati_fi_types_screenshot.png | sahamati.org.in/fi-types-activated-by-non-banking-fips-on-aa/ |  |  |  | manual download needed: page screenshot, take it in a browser. page said "Last Updated 29 May 2026" on 23 Oct 2026 |
| evidence/sahamati_org_in_depositories-as-fip-on-account-aggregator_.png | sahamati.org.in/depositories-as-fip-on-account-aggregator/ | 25 Oct 2026 | lead | 273550e784a36838bb52108ef12fb0a60c63dff1b6aa5f21b91dc044a7d89c30 | Full-page screenshot (headless Chrome). Post dated 8 May 2023: "In April 2023, Central Depository went live as an FIP"; names CDSL and NSDL as the two depositories that can act as FIPs. Evidence for deck [7]. |
| evidence/nsdl_com_financial-information-provider.png | nsdl.com/financial-information-provider | 25 Oct 2026 | lead | 92c32388744153d3a4a081d168c9fd3bb6cf0542ed67a6a3e59ced3c63fdea1c | Full-page screenshot (headless Chrome), page footer "Last Updated: 25 October 2026". NSDL's own page: "NSDL has integrated with the Account Aggregator Ecosystem and is operational (LIVE) as FIP", 14 AA partners listed. Evidence that NSDL is live; Sahamati's live FIP-AA table loads by script and did not render in the screenshot. |

## Mocked (not downloadable)

| Item | Why mocked |
|---|---|
| Account Aggregator holdings | Only a regulated Financial Information User can fetch real data |
| I4C Suspect Registry | Shared with banks, not public |
| SEBI @valid handle list | SEBI Check is a lookup tool, not a dataset |
| Bank payment records | Private; synthetic ledger used |
| Official footage | Teammates' consented videos only; no real public figure |
