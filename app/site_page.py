"""Assemble the ADC website page: the HTML template plus its data, map, flows script and regression results.

Used by app/adc_app.py (Streamlit) and tools/check_adc_app.py (smoke test), so both build the same page.

Regression results come from notebook 08 (data/clean/reg_*.csv). Until a file exists there, the
placeholder version from data/demo/ (made by tools/make_demo_regressions.py) is used instead, and the
page marks those numbers as placeholders.
"""

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "app" / "site"
CLEAN = ROOT / "data" / "clean"
DEMO = ROOT / "data" / "demo"

SITE_FILES = ["adc.html", "data.json", "mapdata.json", "flows.js"]
REG_FILES = ["reg_eventstudy", "reg_results", "reg_suppliers"]


def reg_path(name):
    """The real file from notebook 08 if it exists, else the placeholder, else None."""
    for folder in (CLEAN, DEMO):
        path = folder / (name + ".csv")
        if path.exists():
            return path
    return None


def input_mtimes():
    """Modification times of every input: the Streamlit cache key."""
    paths = [SITE / name for name in SITE_FILES] + [reg_path(name) for name in REG_FILES]
    return tuple((str(p), p.stat().st_mtime) for p in paths if p is not None)


def reg_json():
    out = {"source": {}}
    for name in REG_FILES:
        path = reg_path(name)
        key = name.replace("reg_", "")
        out["source"][key] = "none" if path is None else ("real" if path.parent == CLEAN else "demo")
        if path is None:
            continue
        df = pd.read_csv(path)
        if key == "suppliers":
            sup = {}
            for iso, g in df.sort_values(["iso3", "year"]).groupby("iso3"):
                # NaN would make invalid JSON: write null instead
                sup[iso] = [[int(y), None if pd.isna(a) else float(a), None if pd.isna(b) else float(b)]
                            for y, a, b in g[["year", "sup_dem", "share_dem"]].itertuples(index=False)]
            out["suppliers"] = sup
        else:
            out[key] = json.loads(df.to_json(orient="records"))
    return json.dumps(out, separators=(",", ":"))


def assemble():
    page, data, mapdata, flows = [(SITE / name).read_text(encoding="utf8") for name in SITE_FILES]
    # flows.js and the results first; the big data files last so their text is never searched for placeholders
    page = page.replace("__ADC_FLOWS_JS__", flows).replace("__ADC_REG__", reg_json())
    return page.replace("__ADC_DATA__", data).replace("__ADC_MAPDATA__", mapdata)
