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


# ------------------------------------------------------------------ the main finding: regression A1
# The main finding is the A1 regression of notebook 08, not a split of the countries into high and low importers:
#   y_k = democracy(t + k) - democracy(t - 1) ~ onset + onset:arms_z + arms_z + country and year fixed effects,
# for k = 1 ... 10. arms_z is the mean arms import of the 5 years before onset, standardised (mean 0, sd 1), so arms
# imports enter as a continuous number and no cut-off between "high" and "low" importers is needed.
#   b1 = onset:            the change after an onset for a country with average arms imports
#   b2 = onset:arms_z:     how much that change differs per standard deviation more arms imports
#   b1 + b2:               the change for a country importing one sd more arms than average
# The 95% band of b1 + b2 needs the covariance of b1 and b2; notebook 08 can provide it as the term
# "onset+onset:arms_z" (e.g. with a linear combination test). Without that term the line is drawn without a band.
A1_SUM = "onset+onset:arms_z"
A1_AVG, A1_MORE = "Average arms imports", "One sd more arms imports"


def a1_main(res):
    """One row per horizon k with b1, b2 and b1 + b2 (and their intervals where known); empty without results."""
    if res is None:
        return pd.DataFrame()
    b1, b2 = a1_points(res, "onset"), a1_points(res, "onset:arms_z")
    if b1.empty:
        return pd.DataFrame()
    d = b1[["k", "coef", "ci_low", "ci_high", "n_obs", "n_countries"]].rename(
        columns={"coef": "b1", "ci_low": "b1_lo", "ci_high": "b1_hi"})
    d = d.merge(b2[["k", "coef", "ci_low", "ci_high"]].rename(columns={"coef": "b2", "ci_low": "b2_lo", "ci_high": "b2_hi"}),
                on="k", how="left")
    s = a1_points(res, A1_SUM)
    if s.empty:
        d["sum"], d["sum_lo"], d["sum_hi"] = d["b1"] + d["b2"], float("nan"), float("nan")
    else:
        d = d.merge(s[["k", "coef", "ci_low", "ci_high"]].rename(columns={"coef": "sum", "ci_low": "sum_lo", "ci_high": "sum_hi"}),
                    on="k", how="left")
        d["sum"] = d["sum"].fillna(d["b1"] + d["b2"])
    return d.sort_values("k").reset_index(drop=True)


def _ci(lo, hi):
    return "–" if pd.isna(lo) or pd.isna(hi) else f"{sgn(lo)} to {sgn(hi)}"


def _clear(lo, hi):
    return not (pd.isna(lo) or pd.isna(hi)) and (lo > 0 or hi < 0)


def a1_sentence(d, k=5):
    """The main finding in words, at horizon k (or the nearest available)."""
    if d.empty:
        return None
    r = d.iloc[(d["k"] - k).abs().argmin()]
    k = int(r["k"])
    yrs = f"{k} year{'s' if k > 1 else ''}"
    s = (f"{yrs.capitalize()} after a conflict starts, the democracy index of a country with average arms imports has "
         f"changed by **{sgn(r['b1'])}** (95% CI {_ci(r['b1_lo'], r['b1_hi'])}"
         f"{'' if _clear(r['b1_lo'], r['b1_hi']) else ', not clearly different from zero'}).")
    if not pd.isna(r["b2"]):
        s += (f" Per standard deviation more arms imported in the 5 years before, the change is **{sgn(r['b2'])}** "
              f"different (95% CI {_ci(r['b2_lo'], r['b2_hi'])}"
              f"{': a clear difference' if _clear(r['b2_lo'], r['b2_hi']) else ', not clearly different from zero'}), "
              f"so **{sgn(r['sum'])}** in total for such a country.")
    return s


def a1_chart(d, height=260):
    """b1 (average arms imports) with its 95% band and b1 + b2 (one sd more), for k = 1 ... 10; one hover per k."""
    import altair as alt  # local import: this module is also used by pages that draw no Altair chart

    k1 = max(10, int(d["k"].max()))
    long = pd.concat([
        d.assign(grp=A1_AVG, coef=d["b1"], lo=d["b1_lo"], hi=d["b1_hi"]),
        d.assign(grp=A1_MORE, coef=d["sum"], lo=d["sum_lo"], hi=d["sum_hi"]),
    ])[["k", "grp", "coef", "lo", "hi"]]
    vals = pd.concat([long["coef"], long["lo"], long["hi"]]).dropna()
    lo, hi = min(0.0, vals.min()), max(0.0, vals.max())
    pad = (hi - lo) * .08 or .01
    ys = alt.Scale(domain=[lo - pad, hi + pad], nice=True, zero=False)
    xs = alt.Scale(domain=[.5, k1 + .5], nice=False, zero=False)
    x = alt.X("k:Q", scale=xs, title="Years after the conflict starts",
              axis=alt.Axis(values=list(range(1, k1 + 1)), format="d", grid=False))
    y = alt.Y("coef:Q", scale=ys, title="Change in democracy index",
              axis=alt.Axis(format="+.2f", grid=True, tickCount=5))
    csc = alt.Scale(domain=[A1_AVG, A1_MORE], range=[ACCENT, HI])
    colour = alt.Color("grp:N", scale=csc, legend=None)  # the page draws the legend as a text line above the chart
    dash = alt.StrokeDash("grp:N", scale=alt.Scale(domain=[A1_AVG, A1_MORE], range=[[1, 0], [5, 3]]), legend=None)
    zero = alt.Chart(pd.DataFrame({"v": [0]})).mark_rule(color=INK2, strokeDash=[4, 4]).encode(y=alt.Y("v:Q", scale=ys))
    band = alt.Chart(long.dropna(subset=["lo", "hi"])).mark_area(opacity=.16).encode(
        x=x, y=alt.Y("lo:Q", scale=ys), y2="hi:Q", color=alt.Color("grp:N", scale=csc, legend=None))
    line = alt.Chart(long).mark_line(strokeWidth=2.2).encode(x=x, y=y, color=colour, strokeDash=dash)
    dots = alt.Chart(long).mark_circle(size=55, opacity=1, stroke="#1a1a19", strokeWidth=1).encode(
        x=x, y=y, color=alt.Color("grp:N", scale=csc, legend=None))
    tips = d.assign(x0=d["k"] - .5, x1=d["k"] + .5,
                    When=[f"{k} year{'s' if k > 1 else ''} after onset" for k in d["k"]],
                    Avg=[f"{sgn(b)} (95% CI {_ci(a, c)})" for b, a, c in zip(d["b1"], d["b1_lo"], d["b1_hi"])],
                    More=[f"{sgn(s)}" + ("" if pd.isna(a) else f" (95% CI {_ci(a, c)})")
                          for s, a, c in zip(d["sum"], d["sum_lo"], d["sum_hi"])],
                    Diff=[f"{sgn(b)} (95% CI {_ci(a, c)})" for b, a, c in zip(d["b2"], d["b2_lo"], d["b2_hi"])],
                    N=[f"{int(n):,} country-years, {int(c):,} countries" for n, c in zip(d["n_obs"], d["n_countries"])])
    hit = alt.Chart(tips).mark_rect(opacity=0).encode(
        x=alt.X("x0:Q", scale=xs), x2="x1:Q", y=alt.value(0), y2=alt.value("height"),
        tooltip=[alt.Tooltip("When:N", title="Horizon"), alt.Tooltip("Avg:N", title=A1_AVG),
                 alt.Tooltip("More:N", title=A1_MORE), alt.Tooltip("Diff:N", title="Difference per sd (b2)"),
                 alt.Tooltip("N:N", title="n")])
    return (alt.layer(zero, band, line, dots, hit).properties(height=height, padding={"left": 4, "right": 8, "top": 4, "bottom": 4})
            .configure_view(stroke=None).configure(background="transparent", font="IBM Plex Sans, sans-serif")
            .configure_axis(gridColor=LINE, domainColor=LINE, tickColor=LINE, labelColor=MUTED, titleColor=MUTED,
                            titleFontWeight="normal", labelFontSize=11, titleFontSize=12)
            .configure_legend(labelColor=INK2, labelFontSize=12))


ci_text = _ci  # public name, used by the World map's "Show the numbers" table


def a1_legend():
    """The legend of a1_chart as a one-line Markdown text (the chart itself draws none)."""
    items = [(f"{A1_AVG} (b1)", ACCENT, "━"), (f"{A1_MORE} (b1 + b2)", HI, "╍"), ("Band: 95% confidence interval", "#5a5955", "■")]
    return ":small[" + " ".join(f':color[{sym}]{{foreground="{c}"}} {n.replace(" ", chr(160))}' for n, c, sym in items) + "]"
