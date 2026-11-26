# MKW Times

Personal Mario Kart World time-trial tracker: my times vs current WRs from mkwrs.com.

- `index.html`: the whole app (times saved in the phone's browser storage)
- `wrs.json`: current WRs, refreshed every 4 hours by `.github/workflows/update-wrs.yml`
- `scripts/scrape.py`: the scraper the workflow runs

Time entry: type digits only, e.g. `152430` = 1'52"430.
