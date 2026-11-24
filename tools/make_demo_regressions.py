"""Make PLACEHOLDER regression result files so the website's Findings views can be designed before
notebook 08 is done.

Usage (from the repo root):
    python tools/make_demo_regressions.py

Writes data/demo/reg_eventstudy.csv, reg_results.csv and reg_suppliers.csv in exactly the format the
checkpoints of notebooks/08_regressions.ipynb require. The numbers are RANDOM (seeded), not estimated
from our data, and the website shows a "placeholder numbers" banner whenever it uses them. As soon as
notebook 08 writes the real files to data/clean/, the website uses those instead.
"""

import os

import numpy as np
import pandas as pd

ROOT = os.path.join(os.path.dirname(__file__), "..")
OUT = os.path.join(ROOT, "data", "demo")
rng = np.random.default_rng(2026)


def eventstudy():
    rows = []
    for group, drift, n in [("all", -0.012, 281), ("high importer", -0.02, 140), ("low importer", -0.005, 141)]:
        for t in range(-10, 11):
            if t == -1:
                continue
            coef = (drift * min(t, 8) / 8 if t >= 0 else 0) + rng.normal(0, 0.004)
            half = 0.012 + 0.0015 * abs(t + 1) + (0.006 if group != "all" else 0)
            rows.append([t, group, round(coef, 4), round(coef - half, 4), round(coef + half, 4), int(n * (1 - abs(t) / 40))])
    return pd.DataFrame(rows, columns=["t", "group", "coef", "ci_low", "ci_high", "n"])


def results():
    rows = []

    def add(model, term, coef, se, n_obs, n_c):
        rows.append([model, term, round(coef, 4), round(se, 4), round(coef - 1.96 * se, 4), round(coef + 1.96 * se, 4), n_obs, n_c])

    for k in range(1, 11):
        add("A1_k%d" % k, "onset", -0.002 * k + rng.normal(0, 0.003), 0.006 + 0.0007 * k, 11800 - 150 * k, 176)
        add("A1_k%d" % k, "onset:arms_z", -0.0012 * k + rng.normal(0, 0.002), 0.005 + 0.0005 * k, 11800 - 150 * k, 176)
    for split, term in [("war", "onset:war_onset"), ("type", "onset:intrastate"), ("post1991", "onset:post1991"), ("regime", "onset:democracy_t1")]:
        add("B_%s_k5" % split, term, rng.normal(-0.01, 0.012), 0.011, 11000, 176)
    for k in (5, 10):
        add("C3_k%d" % k, "onset:sup_dem_pre5", rng.normal(0.015, 0.01) * (k / 5), 0.012, 7400, 150)
    add("D1_lpm", "dem_lag1", 0.09 + rng.normal(0, 0.01), 0.03, 9800, 176)
    add("D1_lpm", "dem_lag1_sq", -0.11 + rng.normal(0, 0.01), 0.035, 9800, 176)
    add("D1_lpm", "log_arms_lag1", 0.004 + rng.normal(0, 0.001), 0.002, 9800, 176)
    return pd.DataFrame(rows, columns=["model", "term", "coef", "se", "ci_low", "ci_high", "n_obs", "n_countries"])


def suppliers():
    panel = pd.read_csv(os.path.join(ROOT, "data", "clean", "panel.csv"))
    rows = []
    for iso, g in panel[panel["arms_imports_tiv"] > 0].groupby("iso3"):
        level = rng.uniform(0.2, 0.85)
        for year in sorted(g["year"]):
            level = float(np.clip(level + rng.normal(0, 0.03), 0.05, 0.95))
            rows.append([iso, int(year), round(level, 3), round(float(np.clip(level * 1.15 - 0.08, 0, 1)), 3)])
    return pd.DataFrame(rows, columns=["iso3", "year", "sup_dem", "share_dem"])


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for name, df in [("reg_eventstudy", eventstudy()), ("reg_results", results()), ("reg_suppliers", suppliers())]:
        df.to_csv(os.path.join(OUT, name + ".csv"), index=False)
        print("wrote", os.path.normpath(os.path.join(OUT, name + ".csv")), df.shape)
