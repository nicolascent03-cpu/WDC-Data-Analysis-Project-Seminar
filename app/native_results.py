"""Data and chart helpers for the native Start, Findings and About pages.

Regression results come from notebook 08 (data/clean/reg_*.csv). Until a file exists there, the placeholder
version from data/demo/ is used, exactly as in app/site_page.py (whose reg_path() this module reuses).
"""

import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import site_page

ROOT = Path(__file__).resolve().parent.parent
CLEAN = ROOT / "data" / "clean"
SITE_DATA = ROOT / "app" / "site" / "data.json"

# Colours, as on the World map page
BG = "rgba(0,0,0,0)"
INK, INK2, MUTED, LINE = "#f0efec", "#c3c2b7", "#959086", "#2c2c2a"
ACCENT, HI, LO = "#e48461", "#d95926", "#3987e5"
REGIMES = ["Closed autocracy", "Electoral autocracy", "Electoral democracy", "Liberal democracy"]
REG_COLS = ["#e66767", "#874239", "#2f5784", "#6da7ec"]

PLACEHOLDER_TEXT = ("These are not real results. They show how the regression results of notebook 08 will appear; "
                    "the page switches to the real numbers as soon as they exist.")

# Plain-English names of the model terms (TERM_LAB in app/site/adc.html)
TERM_LAB = {
    "onset:war_onset": "War instead of minor conflict", "onset:intrastate": "Conflict inside one country",
    "onset:post1991": "After the Cold War", "onset:democracy_t1": "Democracy just before the conflict",
    "onset:sup_dem_pre5": "Arms from democratic suppliers", "dem_lag1": "Democracy last year",
    "dem_lag1_sq": "Democracy squared (unstable middle)", "log_arms_lag1": "Arms imports last year (log)",
    "onset": "Conflict onset", "onset:arms_z": "Onset × arms imports (per sd)",
}

# Forest-plot groups (FOREST in app/site/adc.html): model-name prefix regex, title, description
FOREST = [
    (r"^B_", "Kind of conflict (B)",
     "Extra change in the democracy index 5 years after onset for these cases, compared with the others."),
    (r"^C\d*_", "Who supplied the arms (C)",
     "Extra change in the democracy index after onset when the arms of the 5 years before came from more "
     "democratic suppliers (0 to 1)."),
    (r"^D\d*_", "What predicts a conflict (D)",
     "Change in the probability that a conflict starts next year (linear probability model)."),
]

ES_NAME = {"all": "All onsets", "high importer": "High arms importers", "low importer": "Low arms importers"}
ES_COL = {"all": ACCENT, "high importer": HI, "low importer": LO}


def _mtime(name):
    path = site_page.reg_path(name)
    return None if path is None else (str(path), path.stat().st_mtime)


@st.cache_data(max_entries=8)
def _read(name, key):
    path = site_page.reg_path(name)
    if path is None:
        return None, "none"
    return pd.read_csv(path), ("real" if path.parent == site_page.CLEAN else "demo")


def load(name):
    """(DataFrame or None, source) for reg_eventstudy / reg_results / reg_suppliers; source is real, demo or none."""
    return _read(name, _mtime(name))


def any_placeholder():
    return any(load(n)[1] == "demo" for n in site_page.REG_FILES)


@st.cache_data
def load_panel():
    return pd.read_csv(CLEAN / "panel.csv", usecols=["country_name", "iso3", "year", "regime_type", "regime_label",
                                                     "democracy_index", "conflict_active", "arms_imports_tiv"])


@st.cache_data
def load_finding():
    """The simple high vs low importer comparison of the original prototype (D.finding in data.json)."""
    with open(SITE_DATA, encoding="utf8") as f:
        return json.load(f)["finding"]


def event_rows(es, group):
    """Rows of one event-study group sorted by t, with the reference year t = -1 added as a 0 point."""
    g = es[(es["group"] == group) & es["coef"].notna()].copy()
    if g.empty:
        return g
    g["ref"] = False
    if not (g["t"] == -1).any():
        g = pd.concat([g, pd.DataFrame([{"t": -1, "group": group, "coef": 0.0, "ci_low": 0.0, "ci_high": 0.0,
                                         "n": None, "ref": True}])], ignore_index=True)
    return g.sort_values("t").reset_index(drop=True)


def a1_points(res, term):
    m = res["model"].str.extract(r"^A1_k(\d+)$")[0]
    out = res[m.notna() & (res["term"] == term) & res["coef"].notna()].copy()
    out["k"] = m[out.index].astype(int)
    return out.sort_values("k")


@st.cache_data
def supplier_series(key):
    """Mean supplier democracy per year: all recipients, democratic (regime 2-3) and autocratic (0-1) recipients."""
    sup, _ = load("reg_suppliers")
    reg = load_panel()[["iso3", "year", "regime_type"]]
    d = sup.dropna(subset=["sup_dem"]).merge(reg, on=["iso3", "year"], how="left")
    d["side"] = pd.cut(d["regime_type"], [-1, 1.5, 4], labels=["aut", "dem"])
    out = d.groupby("year")["sup_dem"].agg(all="mean", n="count")
    by = d.groupby(["year", "side"], observed=False)["sup_dem"].agg(["mean", "count"]).unstack("side")
    out["dem"], out["aut"] = by[("mean", "dem")], by[("mean", "aut")]
    out["nd"], out["na"] = by[("count", "dem")], by[("count", "aut")]
    return out.reindex(range(1950, 2026)).reset_index()


def sgn(v, d=3):
    if v is None or pd.isna(v):
        return "–"
    return ("+" if v > 0 else "−" if v < 0 else "") + f"{abs(v):.{d}f}"


def layout(fig, height, **kw):
    """Transparent dark layout in IBM Plex, matching the World map page."""
    base = dict(height=height, paper_bgcolor=BG, plot_bgcolor=BG, font=dict(family="IBM Plex Sans", color=INK2, size=12),
                margin=dict(l=8, r=8, t=28, b=8), showlegend=False,
                hoverlabel=dict(bgcolor=INK, font_color="#111110", font_family="IBM Plex Sans"))
    fig.update_layout(**(base | kw))
    fig.update_xaxes(automargin=True, gridcolor=LINE, zeroline=False, linecolor=LINE, tickfont=dict(color=MUTED), title_font=dict(color=MUTED))
    fig.update_yaxes(automargin=True, gridcolor=LINE, zerolinecolor=MUTED, zerolinewidth=1, linecolor=LINE, tickfont=dict(color=MUTED),
                     title_font=dict(color=MUTED))
    return fig


def rgba(h, a):
    h = h.lstrip("#")
    return "rgba(%d,%d,%d,%s)" % (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def band_traces(x, lo, hi, mid, colour, name, hover, opacity=.16):
    """A shaded 95% band plus the coefficient line with markers."""
    x = list(x)
    return [
        go.Scatter(x=x + x[::-1], y=list(hi) + list(lo)[::-1], fill="toself", fillcolor=rgba(colour, opacity),
                   line=dict(width=0), hoverinfo="skip", showlegend=False),
        go.Scatter(x=x, y=list(mid), mode="lines+markers", name=name, line=dict(color=colour, width=2.2),
                   marker=dict(size=7, color=colour, line=dict(width=1, color="#1a1a19")), text=hover, hoverinfo="text"),
    ]
