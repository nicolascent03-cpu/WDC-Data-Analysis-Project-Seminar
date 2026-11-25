"""Save the A1 results of notebook 08 (Part A, the main finding) for the app: data/clean/reg_results.csv.

Notebook 08 estimates A1 in Part A but only writes reg_results.csv in its last part (Part G, not done yet). Until then
this script runs the same code as the notebook, cell for cell, and saves the A1 rows:
  - panel preparation: cells 3, 6, 8, 10 (log arms, onsets after two years without conflict, arms_pre5, ...)
  - outcomes and arms_z: cell 15
  - A1 regressions for k = 1 ... 10: cell 17 (PanelOLS, country and year fixed effects, clustered by country),
    including the 95% interval of b1 + b2 from the covariance of b1 and b2
Rows: model A1_k1 ... A1_k10, terms "onset" (b1), "onset:arms_z" (b2) and "onset+onset:arms_z" (b1 + b2), in the
column format the app reads (model, term, coef, se, ci_low, ci_high, n_obs, n_countries). When Part G writes the full
reg_results.csv, that file replaces this one.

Run from the repo root:  .venv/bin/python tools/export_reg_a1.py
"""

from pathlib import Path

import numpy as np
import pandas as pd
from linearmodels.panel import PanelOLS

CLEAN = Path(__file__).resolve().parent.parent / "data" / "clean"

# cells 3 and 6
panel = pd.read_csv(CLEAN / "panel.csv")
panel = panel.sort_values(["iso3", "year"]).reset_index(drop=True)
panel["log_arms"] = np.log1p(panel["arms_imports_tiv"])

# cell 8: onset = conflict year after two years without conflict
panel = panel.sort_values(["iso3", "year"]).copy()
by_country = panel.groupby("iso3")["conflict_active"]
previous_year = by_country.shift(1)
two_years_before = by_country.shift(2)
panel["onset"] = (panel["conflict_active"].eq(1) & previous_year.eq(0) & two_years_before.eq(0)).astype(int)
panel["war_onset"] = (panel["onset"].eq(1) & panel["max_intensity"].eq(2)).astype(int)

# cell 10
g = panel.groupby("iso3", sort=False)
panel["arms_pre5"] = g["log_arms"].transform(lambda s: s.shift(1).rolling(5).mean())

# cell 15: y_k and arms_z
panel = panel.sort_values(["iso3", "year"]).copy()
democracy_by_country = panel.groupby("iso3", sort=False)["democracy_index"]
for k in range(1, 11):
    panel[f"y_{k}"] = democracy_by_country.transform(lambda s, k=k: s.shift(-k) - s.shift(1))
panel["arms_z"] = (panel["arms_pre5"] - panel["arms_pre5"].mean()) / panel["arms_pre5"].std()

# cell 17: A1 for every k
panel_idx = panel.set_index(["iso3", "year"])
rows = []
for k in range(1, 11):
    res = PanelOLS.from_formula(f"y_{k} ~ onset + onset:arms_z + arms_z + EntityEffects + TimeEffects",
                                data=panel_idx).fit(cov_type="clustered", cluster_entity=True)
    ci = res.conf_int()
    cov = res.cov.astype("float64")
    b_sum = res.params["onset"] + res.params["onset:arms_z"]
    se_sum = np.sqrt(float(cov.loc["onset", "onset"]) + float(cov.loc["onset:arms_z", "onset:arms_z"])
                     + 2.0 * float(cov.loc["onset", "onset:arms_z"]))
    critical = (ci.loc["onset", "upper"] - res.params["onset"]) / res.std_errors["onset"]  # as res.conf_int()
    n_obs, n_c = int(res.nobs), int(res.entity_info["total"])
    for term in ["onset", "onset:arms_z"]:
        rows.append({"model": f"A1_k{k}", "term": term, "coef": res.params[term], "se": res.std_errors[term],
                     "ci_low": ci.loc[term, "lower"], "ci_high": ci.loc[term, "upper"], "n_obs": n_obs, "n_countries": n_c})
    rows.append({"model": f"A1_k{k}", "term": "onset+onset:arms_z", "coef": b_sum, "se": se_sum,
                 "ci_low": b_sum - critical * se_sum, "ci_high": b_sum + critical * se_sum, "n_obs": n_obs, "n_countries": n_c})

out = pd.DataFrame(rows)
out.to_csv(CLEAN / "reg_results.csv", index=False)
print(f"onsets: {int(panel['onset'].sum())}")
print(out.round(4).to_string(index=False))
