"""World map of regime types with striped armed conflicts (custom component, st.components.v2).

Same map as buildMap()/updateReg() in app/site/adc.html: our Equal Earth country shapes (app/site/mapdata.json),
filled by regime type for the year; countries with an active armed conflict get diagonal stripes (denser and
brighter for war). Small states get a larger invisible hover circle. A click sends the country back to Python.

    res = regime_map(year, stripes=True, key="wm_regmap", on_select=...)   # res.select -> iso3 of a clicked country
"""

import json
from pathlib import Path

import pandas as pd
import streamlit as st

import native_data as nd

_HERE = Path(__file__).resolve().parent
_COMPONENT = st.components.v2.component(
    "adc_regime_map",
    html='<div class="rm-root"></div>',
    css=(_HERE / "regime_map.css").read_text(encoding="utf8"),
    js=(_HERE / "regime_map.js").read_text(encoding="utf8"),
)


@st.cache_data
def geometry():
    """Map shapes once: {w, h, p: {iso3: path}, pts: {iso3: [x, y]}} in the map's own pixel coordinates."""
    m = json.loads(nd.MAPDATA.read_text(encoding="utf8"))
    return {"w": m["w"], "h": m["h"], "p": m["p"], "pts": m.get("pts", {})}


@st.cache_data
def year_values(y):
    """{iso3: [regime_type, democracy_index, max_intensity, arms_tiv, name]} for one year (V-Dem panel)."""
    g = nd.load_panel()
    g = g[g["year"] == y]
    num = lambda v, d=None: None if pd.isna(v) else round(float(v), d) if d else float(v)
    return {r.iso3: [None if pd.isna(r.regime_type) else int(r.regime_type), num(r.democracy_index, 3),
                     0 if pd.isna(r.max_intensity) else int(r.max_intensity), num(r.arms_imports_tiv, 1), r.country_name]
            for r in g.itertuples()}


def regime_map(year, *, stripes=True, selected=None, key=None, on_select=None):
    """Draw the map for `year`. `selected` (iso3) is outlined. Returns the component result (.select = iso3 clicked)."""
    payload = {
        "year": int(year),
        "values": year_values(int(year)),
        "geo": geometry(),
        "stripes": bool(stripes),
        "selected": selected,
        "regimes": [r.capitalize() for r in nd.REGIMES],
        "colours": [nd.REGIME_COLOURS[r] for r in nd.REGIMES],
    }
    return _COMPONENT(data=payload, key=key, height="content", on_select_change=on_select or (lambda: None))
