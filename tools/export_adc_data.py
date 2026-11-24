"""Rebuild the website data (same structure as app/site/data.json) from the team's own clean files.

Usage (from the repo root):
    python tools/export_adc_data.py [output.json]      # default: data/clean/adc_data.json

Inputs (made by the notebooks):
    data/clean/panel.csv            05_merge     -> countries (d, r, c, a)
    data/clean/sipri_suppliers.csv  04_sipri     -> suppliers
    data/clean/event.csv            06_analysis  -> finding
    data/clean/crosswalk_gw.csv     01_crosswalk -> conflicts (gw code -> iso3)
    data/raw/UcdpPrioConflict_v26_1.xlsx (raw, read the same way 02_ucdp reads it) -> conflicts
The script never writes into app/; copying the result there is a manual step.
"""

import json
import os
import sys

import pandas as pd

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
CLEAN = os.path.join(ROOT, "data", "clean")
RAW = os.path.join(ROOT, "data", "raw")

INPUTS = {
    os.path.join(CLEAN, "panel.csv"): "notebooks/05_merge.ipynb",
    os.path.join(CLEAN, "sipri_suppliers.csv"): "notebooks/04_sipri.ipynb",
    os.path.join(CLEAN, "event.csv"): "notebooks/06_analysis.ipynb",
    os.path.join(CLEAN, "crosswalk_gw.csv"): "notebooks/01_crosswalk.ipynb",
    os.path.join(RAW, "UcdpPrioConflict_v26_1.xlsx"): "the raw UCDP download (see docs/build_guide.md)",
}


def check_inputs():
    missing = [(p, nb) for p, nb in INPUTS.items() if not os.path.exists(p)]
    if missing:
        lines = ["Missing input files:"]
        for p, nb in missing:
            lines.append("  %s  (created by %s)" % (os.path.relpath(p, ROOT), nb))
        sys.exit("\n".join(lines))


def num(v, nd=None):
    if pd.isna(v):
        return None
    v = float(v)
    if nd is None:
        return int(v)
    return round(v, nd)


def build_countries(panel, y0, y1):
    years = list(range(y0, y1 + 1))
    out = {}
    for iso, rows in panel.groupby("iso3"):
        rows = rows.set_index("year").reindex(years)
        out[iso] = {
            "n": panel.loc[panel["iso3"] == iso, "country_name"].iloc[-1],
            "d": [num(v, 3) for v in rows["democracy_index"]],
            "r": [num(v) for v in rows["regime_type"]],
            "c": [num(v) for v in rows["max_intensity"]],
            "a": [num(v, 1) for v in rows["arms_imports_tiv"]],
        }
    return out


def build_conflicts(isos):
    # Same reading and gwno_loc split as notebook 02_ucdp.
    raw = pd.read_excel(os.path.join(RAW, "UcdpPrioConflict_v26_1.xlsx"))
    raw = raw[raw["year"] >= 1950]
    gw = pd.read_csv(os.path.join(CLEAN, "crosswalk_gw.csv"))
    gw_to_iso = dict(zip(gw["gw_code"], gw["iso3"]))
    rows = []
    for r in raw.itertuples(index=False):
        for code in str(r.gwno_loc).split(","):
            iso = gw_to_iso.get(int(code.strip()))
            if iso is not None:
                rows.append((iso, r.conflict_id, r.year, r.side_a, r.side_b,
                             "" if pd.isna(r.territory_name) else r.territory_name,
                             int(r.intensity_level), int(r.type_of_conflict)))
    long = pd.DataFrame(rows, columns=["iso3", "id", "year", "a", "b", "t", "int", "type"])
    long = long.drop_duplicates(["iso3", "id", "year"]).sort_values(["iso3", "id", "year"])
    out = {}
    for (iso, cid), g in long.groupby(["iso3", "id"], sort=False):
        if iso not in isos:
            continue
        periods = []
        for y, inten, typ in zip(g["year"], g["int"], g["type"]):
            last = periods[-1] if periods else None
            if last and last[1] == y - 1 and last[2] == inten and last[3] == typ:
                last[1] = int(y)
            else:
                periods.append([int(y), int(y), inten, typ])
        last_row = g.iloc[-1]
        out.setdefault(iso, []).append({"id": int(cid), "a": last_row["a"], "b": last_row["b"],
                                        "t": last_row["t"], "p": periods})
    for iso in out:
        out[iso].sort(key=lambda c: (c["p"][0][0], c["id"]))
    return out


def build_suppliers(sup, isos):
    out = {}
    for iso, rows in sup.groupby("iso3"):
        if iso not in isos:
            continue
        lst = []
        for s, g in rows.groupby("supplier"):
            g = g.groupby("year", as_index=False)["tiv"].sum().sort_values("year")
            g = g[g["tiv"] > 0]
            if len(g) == 0:
                continue
            lst.append({"s": s, "tot": round(float(g["tiv"].sum()), 1),
                        "y": [[int(y), round(float(v), 1)] for y, v in zip(g["year"], g["tiv"])]})
        lst.sort(key=lambda x: -x["tot"])
        out[iso] = lst
    return out


def build_finding(event):
    # Pre-onset average imports per onset (t < 0), median split, as in 06_analysis.
    pre = event[event["t"] < 0].groupby(["iso3", "onset_year"])["arms_imports_tiv"].mean()
    groups = {}
    for key, label in [("high", "high importer"), ("low", "low importer")]:
        g = event[event["importer_group"] == label].dropna(subset=["dem_change"])
        stats = g.groupby("t")["dem_change"].agg(["mean", "std", "count"]).sort_index()
        se = (stats["std"] / stats["count"] ** 0.5).fillna(0)
        groups[key] = {
            "n": int(g[["iso3", "onset_year"]].drop_duplicates().shape[0]),
            "rel": [int(t) for t in stats.index],
            "m": [round(float(v), 4) for v in stats["mean"]],
            "lo": [round(float(v), 4) for v in stats["mean"] - 1.96 * se],
            "hi": [round(float(v), 4) for v in stats["mean"] + 1.96 * se],
            "cnt": [int(v) for v in stats["count"]],
        }
    return {"median_pre": round(float(pre.median()), 1), "groups": groups}


def main(out_path):
    if os.path.normpath(os.path.abspath(out_path)).startswith(os.path.join(ROOT, "app")):
        sys.exit("Refusing to write into app/. Copy the file there by hand once it is checked.")
    check_inputs()
    panel = pd.read_csv(os.path.join(CLEAN, "panel.csv"))
    y0, y1 = int(panel["year"].min()), int(panel["year"].max())
    countries = build_countries(panel, y0, y1)
    isos = set(countries)
    data = {
        "y0": y0,
        "y1": y1,
        "countries": countries,
        "conflicts": build_conflicts(isos),
        "suppliers": build_suppliers(pd.read_csv(os.path.join(CLEAN, "sipri_suppliers.csv")), isos),
        "finding": build_finding(pd.read_csv(os.path.join(CLEAN, "event.csv"))),
    }
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w", encoding="utf8") as f:
        json.dump(data, f, separators=(",", ":"), ensure_ascii=False)
    print("Wrote", out_path, "-", len(countries), "countries,", y0, "-", y1)


if __name__ == "__main__":
    if len(sys.argv) > 2:
        sys.exit(__doc__)
    main(sys.argv[1] if len(sys.argv) == 2 else os.path.join(CLEAN, "adc_data.json"))
