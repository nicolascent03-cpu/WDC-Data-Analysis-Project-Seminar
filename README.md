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

## The app

The final website is a native Streamlit app: `app/native_app.py`, with its pages in `app/native_pages/` (Start, World map, Findings, Countries & compare, About the data with glossary and FAQ). It reads the tables in `data/clean/`, including the regression results that notebook 08 writes there.

Live version: *add the Streamlit Cloud link after deploying (branch `main`, main file `app/native_app.py`).*

Earlier versions, kept for reference and not part of the final app: the HTML website (`app/adc_app.py`, `app/site/`) and the first Streamlit app (`app/streamlit_app.py` with `app/panels_*.py`).

## Who did what

| Part | Owner |
| --- | --- |
| 01 Crosswalk, 05 Merge, 06 Part B and C | Together |
| 02 UCDP, 03 V-Dem, conflict-by-regime descriptives, `app/panels_conflict.py` (regime bands, conflict bars, first app) | Nicolas |
| 04 SIPRI, 07 Charts, 08 Regressions, arms and war/peace descriptives, `app/panels_arms.py` (arms imports, suppliers, global trends), `app/panels_analysis.py` (democracy line, main chart), both in the first app | Yair |
| Final app (`app/native_app.py`, `app/native_pages/`) | Nicolas, see AI use |


## Findings

1. **Democracy declines slowly after a conflict starts.** In a stacked event study (notebook 08, A3), each of the 281 conflict onsets is compared with countries that had no conflict in the same 21 years. Before the onset, democracy in onset countries moves in parallel with these controls (all leads between −0.006 and +0.004, intervals including zero). After the onset it falls behind: by about 0.013 after 4 to 5 years and 0.018 to 0.025 after 6 to 9 years, where the 95% intervals no longer include zero. This is the one clear result, and it is small on a 0 to 1 index.
2. **Arms imports before the onset make no clear difference.** With country and year fixed effects (notebook 08, A1), the change five years after onset is −0.006 (95% CI −0.021 to 0.010) for a country with average arms imports, and one standard deviation more arms imports before the onset goes with +0.011 (95% CI −0.003 to 0.025). All intervals include zero at every horizon from 1 to 10 years. Arms imports enter the model as one continuous, standardised number, so no cut-off between groups of countries is needed.
3. **Who supplied the arms makes no clear difference either.** Arms from democratic rather than autocratic suppliers in the five years before onset go with −0.005 after five years (95% CI −0.063 to 0.053) and −0.037 after ten years (95% CI −0.118 to 0.044), in the 243 onsets of countries that imported arms before.

The raw averages of notebook 06 show democracy slightly higher five years after an onset than in the year before, but it was already rising by about as much in the five years before: that is the worldwide trend towards democracy, which the fixed effects and the control countries of notebook 08 take out.

These results show patterns, not causes: arms imports and suppliers are not assigned at random, the confidence intervals are wide, historical states are mapped onto today's countries, and TIV measures military capability.

## Bonus feature

**Regression analysis (notebook 08).** We estimate how the democracy index changes 1 to 10 years after a conflict onset compared with countries without an onset, using panel regressions with country and year fixed effects and standard errors clustered by country. The models include an interaction with pre-onset arms imports, a stacked event study that checks the years before onset, and a model with the democracy of the arms suppliers. This goes beyond the raw averages of notebook 06: it separates the conflict from the worldwide trend towards democracy.

## AI use

We used AI as a tutor for planning, the notebook structure and hints. All analysis and app code is ours. AI prepared the setup, data-loading and checkpoint cells and the whole `00_setup_check` notebook. Details, with dates, are in `AI_LOG.md`.
