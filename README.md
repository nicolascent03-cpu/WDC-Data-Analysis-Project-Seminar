# Conflict, Democracy and Arms

Data Analysis with Python, University of Zurich, HS26. Nicolas Centorame and Yair Segal.

## Research question

What happens to democracy during and after armed conflict, and does it look different in countries that import many weapons?

## Data

| Dataset | Version | Source |
| --- | --- | --- |
| UCDP/PRIO Armed Conflict Dataset | 26.1 | ucdp.uu.se |
| V-Dem Country-Year Core | 16 | v-dem.net |
| SIPRI Arms Transfers Database, trade register | 1950 to 2025 | sipri.org |

The V-Dem file is too large for GitHub. Download it and put it in `data/raw/vdem/`.

## How to run

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

1. Run the notebooks in this order with Restart and Run All: 00, 03, 01, 02, 04, 05, 06, 07. Notebooks 01 to 06 write their results to `data/clean/`.
2. Start the app from the repo root: `streamlit run app/streamlit_app.py`
3. `app/try_streamlit_nicolas.py` and `app/try_streamlit_yair.py`: Streamlit practice files only.

## Who did what

| Part | Owner |
| --- | --- |
| 01 Crosswalk, 05 Merge, 06 Part B and C, app | Together |
| 02 UCDP, 03 V-Dem, conflict-by-regime descriptives, `app/panels_conflict.py` (regime bands, conflict bars) | Nicolas |
| 04 SIPRI, arms and war/peace descriptives, `app/panels_arms.py` (arms line, suppliers, world map), `app/panels_analysis.py` (democracy line, main chart) | Yair |

## Findings

TODO: the three findings from 06 Part C.

## Bonus feature

TODO: what it does and why it helps the question (two sentences).

## AI use

We used AI as a tutor for planning, the notebook structure and hints. All analysis and app code is ours. AI prepared the setup, data-loading and checkpoint cells and the whole `00_setup_check` notebook. Details, with dates, are in `AI_LOG.md`.
