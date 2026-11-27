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
nbstripout --install
```

1. Run the notebooks in this order with Restart and Run All: 00, 03, 01, 02, 04, 05, 06, 07, 08. Notebooks 01 to 06 and 08 write their results to `data/clean/`.
2. Start the app from the repo root: `streamlit run app/native_app.py`
3. `app/try_streamlit_nicolas.py` and `app/try_streamlit_yair.py`: Streamlit practice files only.

## Who did what

| Part | Owner |
| --- | --- |
| 01 Crosswalk, 05 Merge, 06 Part B and C, app | Together |
| 02 UCDP, 03 V-Dem, conflict-by-regime descriptives, `app/panels_conflict.py` (regime bands, conflict bars) | Nicolas |
| 04 SIPRI, 07 Charts, 08 Regressions, arms and war/peace descriptives, `app/panels_arms.py` (arms imports, suppliers, global trends), `app/panels_analysis.py` (democracy line, main chart) | Yair |


## Findings

1. **Democracy keeps its pre-conflict trend.** In the raw event window (notebook 06, 281 conflict onsets), the democracy index is slightly higher five years after a conflict starts than in the year before (+0.021 for high and +0.007 for low arms importers), but it had already been rising by about the same amount in the five years before onset.
2. **Compared with countries without a conflict onset, there is no clear change, and arms imports make no clear difference.** With country and year fixed effects (notebook 08), the change five years after onset is −0.006 (95% CI −0.021 to 0.010), and one standard deviation more arms imports before onset goes with +0.011 (95% CI −0.003 to 0.025). The gap between high and low importers in 06 reverses when we keep only wars or only first onsets.
3. **Who supplied the arms makes no clear difference either.** Arms from democratic rather than autocratic suppliers in the five years before onset go with −0.005 after five years (95% CI −0.063 to 0.053) and −0.037 after ten years (95% CI −0.118 to 0.044).

These results show patterns: arms imports and suppliers are not assigned at random, the confidence intervals are wide, historical states are mapped onto today's countries, and TIV measures military capability.

## Bonus feature

**Regression analysis (notebook 08).** We estimate how the democracy index changes 1 to 10 years after a conflict onset compared with countries without an onset, using panel regressions with country and year fixed effects and standard errors clustered by country. The models include an interaction with pre-onset arms imports, a stacked event study that checks the years before onset, and a model with the democracy of the arms suppliers. This goes beyond the raw averages of notebook 06: it separates the conflict from the worldwide trend towards democracy.

## AI use

We used AI as a tutor for planning, the notebook structure and hints. All analysis and app code is ours. AI prepared the setup, data-loading and checkpoint cells and the whole `00_setup_check` notebook. Details, with dates, are in `AI_LOG.md`.
