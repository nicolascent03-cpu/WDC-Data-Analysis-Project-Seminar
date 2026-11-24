"""Countries & compare, built only with Streamlit (no custom HTML).

One country or a group side by side: a snapshot of the chosen year, democracy vs. arms imports as a
scatter with 10-year trails, democracy, conflict and arms on one shared year axis, regime periods,
the democracy index, armed conflicts, imports by supplier, how democratic the suppliers were, and
the arms flows to and from these countries. Controls live in the sidebar; Play advances the year
for the whole page.
"""

from datetime import datetime

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pydeck as pdk
import streamlit as st
from plotly.subplots import make_subplots

import native_data as nd

Y0, Y1 = 1950, 2025
BG = "rgba(0,0,0,0)"
INK, INK2, MUTED, LINE = "#f0efec", "#c3c2b7", "#959086", "#2c2c2a"
FONT = "IBM Plex Sans"
SPEEDS = {"0.5×": 2.4, "1×": 1.2, "2×": 0.6}  # seconds per year
PERIODS = {"1950–2025": (1950, 2025), "Cold War": (1950, 1991), "Since 1992": (1992, 2025)}
CONFLICT = {2: "War", 1: "Minor conflict", 0: "No armed conflict"}
CONFLICT_COLOURS = {"War": INK2, "Minor conflict": "#5f5b55"}
NO_BAR = {"displayModeBar": False}
SC_GUIDE = ("Up = more democratic, right = more arms received (10-year total, log scale). "
            "Moving together is not proof that one drives the other.")

panel = nd.load_panel()
flows = nd.load_flows()
points = nd.country_points()
NAMES = panel.drop_duplicates("iso3").set_index("iso3")["country_name"].to_dict()
GROUPS = nd.country_groups()
ALL_ISO = sorted(NAMES, key=NAMES.get)

# ------------------------------------------------------------------ state
ss = st.session_state
ss.setdefault("year", 2000)
ss.setdefault("playing", False)
if "countries" not in st.query_params:  # the URL wins when it names countries (?countries=ETH&countries=ERI)
    ss.setdefault("countries", ["ETH"])
# one-shot hand-overs from other pages: a group picked on Start, or countries chosen on the World map
_group = ss.pop("cmp_group", None)
if _group in GROUPS:
    ss["countries"] = list(GROUPS[_group])
    ss.pop("cc_follow", None)
_picked = [i for i in (ss.pop("cmp_countries", None) or []) if i in NAMES]
if _picked:
    ss["countries"] = _picked
    ss.pop("cc_follow", None)


def period_bounds():
    return PERIODS.get(ss.get("cc_period") or "1950–2025", (Y0, Y1))


def clamp_year():
    p0, p1 = period_bounds()
    ss["year"] = min(max(ss["year"], p0), p1)
    ss["cc_year_slider"] = ss["year"]


def slider_moved():
    ss["year"] = ss["cc_year_slider"]


def toggle_play():
    p0, p1 = period_bounds()
    ss["playing"] = not ss["playing"]
    if ss["playing"] and ss["year"] >= p1:
        ss["year"] = p0
    ss["cc_year_slider"] = ss["year"]


def group_chosen():
    name = ss.get("cc_group")
    if name:
        ss["countries"] = list(GROUPS[name])
        ss.pop("cc_follow", None)
    ss["cc_group"] = None


def clear_comparison():
    keep = ss.get("countries") or ["ETH"]
    ss["countries"] = keep[:1]
    ss.pop("cc_follow", None)


# keep the slider on the page-wide year (it may have moved on another page) and inside the period
clamp_year()

# ------------------------------------------------------------------ sidebar
with st.sidebar:
    st.multiselect("Countries", ALL_ISO, format_func=NAMES.get, key="countries", bind="query-params",
                   placeholder="Add a country…")
    st.selectbox("Preset groups", list(GROUPS), index=None, key="cc_group", on_change=group_chosen,
                 placeholder="Choose a group…", format_func=lambda g: f"{g} ({len(GROUPS[g])})",
                 help="Replaces the list above with the members of the group.")
    st.button("Clear comparison", icon=":material/close:", on_click=clear_comparison, width="stretch",
              disabled=len(ss.get("countries") or []) < 2, help="Keep only the first country.")
    st.divider()
    st.segmented_control("Period", list(PERIODS), default="1950–2025", key="cc_period", on_change=clamp_year, width="stretch")
    p0, p1 = period_bounds()
    st.slider("Year", p0, p1, key="cc_year_slider", on_change=slider_moved, disabled=ss["playing"])
    st.button("Pause" if ss["playing"] else "Play through the years", icon=":material/pause:" if ss["playing"] else ":material/play_arrow:",
              type="primary", on_click=toggle_play, width="stretch")
    speed = st.segmented_control("Speed", list(SPEEDS), default="1×", key="cc_speed", width="stretch") or "1×"
    st.caption("SIPRI trend-indicator values (TIV) measure military capability transferred, not money. "
               "Some states appear under a successor's code, as in V-Dem (Russia for the Soviet Union before 1991).")

sel = [i for i in (ss.get("countries") or []) if i in NAMES]
if not sel:
    st.title("Countries & compare")
    st.info("Choose at least one country in the sidebar, or pick a preset group.", icon=":material/arrow_back:")
    st.stop()
single = len(sel) == 1
COL = {iso: nd.COMPARE_COLOURS[k % len(nd.COMPARE_COLOURS)] for k, iso in enumerate(sel)}
DASH = {iso: "solid" if k < len(nd.COMPARE_COLOURS) else "dot" for k, iso in enumerate(sel)}


# ------------------------------------------------------------------ helpers
def base_layout(fig, height, **kw):
    fig.update_layout(height=height, paper_bgcolor=BG, plot_bgcolor=BG, font=dict(family=FONT, color=INK2, size=12),
                      margin=kw.pop("margin", dict(l=0, r=8, t=8, b=0)),
                      hoverlabel=dict(bgcolor=INK, font_color="#111110", font_family=FONT), **kw)
    fig.update_xaxes(gridcolor=LINE, zeroline=False, linecolor=LINE, tickfont=dict(color=MUTED))
    fig.update_yaxes(gridcolor=LINE, zeroline=False, linecolor=LINE, tickfont=dict(color=MUTED))
    return fig


def legend_top(fig):
    fig.update_layout(legend=dict(orientation="h", x=0, y=1.02, yanchor="bottom", font=dict(color=INK2, size=11), title_text="",
                                  entrywidth=150, entrywidthmode="pixels"))


def year_ts(y, end=False):
    return datetime(y + 1 if end else y, 1, 1)


def add_year_line_dates(fig, y):
    x = datetime(y, 7, 1)
    fig.add_shape(type="line", x0=x, x1=x, xref="x", yref="paper", y0=0, y1=1, line=dict(color=INK, width=1.5))


def scroll_box(height_px, limit):
    """A card body that scrolls when the chart is taller than `limit` pixels."""
    return st.container(height=limit) if height_px > limit else st.container()


def muted_list(label, isos):
    if isos:
        st.caption(f"{label}: " + ", ".join(NAMES[i] for i in isos) + ".")


def fmt_tiv(v):
    return "–" if pd.isna(v) else f"{v:,.0f} TIV"


@st.cache_data
def period_panel(isos, a, b):
    return panel[panel["iso3"].isin(isos) & panel["year"].between(a, b)]


@st.cache_data
def largest_importers(isos, a, b, n):
    tot = period_panel(isos, a, b).groupby("iso3")["arms_imports_tiv"].sum()
    return [i for i in isos if i in set(tot.nlargest(n).index)]


def main_supplier(iso, y):
    f = flows[(flows["recipient_iso3"] == iso) & (flows["year"] == y) & ~flows["supplier"].isin(["Other", "unknown supplier(s)"])]
    return f.sort_values("tiv", ascending=False)["supplier"].iloc[0] if len(f) else None


# ------------------------------------------------------------------ charts
SHORT = {"United States of America": "United States", "Democratic Republic of the Congo": "DR Congo",
         "Central African Republic": "Central African Rep.", "Bosnia and Herzegovina": "Bosnia", "United Arab Emirates": "UAE",
         "Republic of the Congo": "Congo", "Republic of Vietnam": "South Vietnam", "German Democratic Republic": "East Germany"}


def short_name(n):
    n = SHORT.get(n, n)
    return n if len(n) <= 18 else n[:17] + "…"


def scatter_axis(vis, period, full):
    """Axes fitted to the visible points `vis` with some padding; with `full`, the democracy index runs 0–1 and the
    arms axis covers the whole period (axes then stay put while playing). A "none" strip left of the log axis
    holds visible points without arms received; it is drawn only when there are any."""
    any_zero = bool((vis["arms_10"] <= 0).any())
    d = period if full else vis
    v = d.loc[d["arms_10"] > 0, "arms_10"]
    if len(v):
        ll, lh = np.log10(v.min()), np.log10(v.max())
        if lh - ll < .8:  # at least 0.8 decades wide
            mid = (ll + lh) / 2
            ll, lh = mid - .4, mid + .4
        pad = max(.12, (lh - ll) * .08)
        ll, lh = ll - pad, lh + pad
    else:
        ll, lh = 0, 3
    none_x = 10 ** (ll - .35)
    ticks = [10 ** e for e in range(int(np.ceil(ll)), int(np.floor(lh)) + 1)]
    if len(ticks) < 3:  # a narrow range: add 2 and 5 between the decades
        ticks = sorted(t * m for t in [10 ** e for e in range(int(np.floor(ll)), int(np.ceil(lh)) + 1)] for m in (1, 2, 5)
                       if ll <= np.log10(t * m) <= lh)
    lab = lambda t: f"{t / 1e6:g}M" if t >= 1e6 else f"{t / 1e3:g}k" if t >= 1e3 else f"{t:g}"
    ax = dict(none_x=none_x, any_zero=any_zero, tickvals=ticks, ticktext=[lab(t) for t in ticks], log=(ll, lh))
    if any_zero:
        ax.update(range=[ll - .6, lh], tickvals=[none_x] + ticks, ticktext=["none"] + ax["ticktext"], strip=(10 ** (ll - .6), 10 ** (ll - .12)))
    else:
        ax["range"] = [ll, lh]
    if full or d.empty:
        ax["y"] = [-.03, 1.03]
    else:
        lo, hi = d["democracy_index"].min(), d["democracy_index"].max()
        if hi - lo < .15:
            mid = (lo + hi) / 2
            lo, hi = mid - .075, mid + .075
        pad = max(.03, (hi - lo) * .1)
        ax["y"] = [max(-.03, lo - pad), min(1.03, hi + pad)]
    return ax


def scatter_frame(fig, ax, height):
    if ax["any_zero"]:
        fig.add_vrect(x0=ax["strip"][0], x1=ax["strip"][1], fillcolor=LINE, opacity=.6, line_width=0, layer="below")
    base_layout(fig, height, showlegend=False, margin=dict(l=0, r=12, t=10, b=0))
    fig.update_xaxes(type="log", range=ax["range"], tickvals=ax["tickvals"], ticktext=ax["ticktext"],
                     title=dict(text="Arms received in the previous 10 years (TIV, log scale)", font=dict(color=MUTED, size=12)))
    fig.update_yaxes(range=ax["y"], title=dict(text="Democracy index", font=dict(color=MUTED, size=12)))


def ring(intensity, base=0.0):
    """Outline width per conflict intensity: war = strong ring, minor = thin ring, none = base."""
    return np.select([intensity == 2, intensity == 1], [2.4, 1.2], base)


def trail_marker(t, colour):
    """A dot per year: war years bigger with a dark outline, minor conflicts smaller with a thin one."""
    return dict(color=colour, size=np.select([t["max_intensity"] == 2, t["max_intensity"] == 1], [10, 7], 5),
                line=dict(color="#111110", width=ring(t["max_intensity"])))


def place_labels(fig, pts, bubbles, ax, width_px=480, height_px=370):
    """Greedy labels: biggest importers first, to the right of the bubble (or the left), skipped when they would
    overlap another label or bubble. Positions are estimated in pixels of the plot area."""
    x0, x1 = ax["range"]
    y0, y1 = ax["y"]
    to_px = lambda x, yv: ((np.log10(x) - x0) / (x1 - x0) * width_px, (yv - y0) / (y1 - y0) * height_px)
    placed = [(bx - 8, by - 8, bx + 8, by + 8) for bx, by in (to_px(r["x"], r["democracy_index"]) for _, r in bubbles.iterrows())]
    for _, p in pts.sort_values("arms_10", ascending=False).iterrows():
        px_, py_ = to_px(p["x"], p["democracy_index"])
        w, h = 7.6 * len(p["label"]) + 8, 18
        for side in ([1, -1] if px_ < width_px - w - 14 else [-1, 1]):
            bx = (px_ + 12, px_ + 12 + w) if side == 1 else (px_ - 12 - w, px_ - 12)
            box = (bx[0], py_ - h / 2, bx[1], py_ + h / 2)
            if box[0] < 0 or box[2] > width_px:
                continue
            if not any(box[0] < q[2] and box[2] > q[0] and box[1] < q[3] and box[3] > q[1] for q in placed):
                placed.append(box)
                fig.add_annotation(x=np.log10(p["x"]), y=p["democracy_index"], text=p["label"], showarrow=False,
                                   xanchor="left" if side == 1 else "right", xshift=10 * side, font=dict(color=INK, size=12))
                break


@st.cache_data
def scatter_single(iso, a, b, y, full):
    d = period_panel((iso,), a, b).copy()
    if d.empty:
        return None
    ax = scatter_axis(d, d, full)
    fig = go.Figure()
    d["x"] = np.where(d["arms_10"] > 0, d["arms_10"], ax["none_x"])
    hover = (NAMES[iso] + " · " + d["year"].astype(str) + "<br>Democracy index " + d["democracy_index"].round(2).astype(str)
             + "<br>Arms received, 10 years: " + d["arms_10"].round(0).astype(int).map("{:,}".format) + " TIV<br>"
             + d["max_intensity"].map(CONFLICT))
    c = COL[iso]
    fig.add_trace(go.Scatter(x=d["x"], y=d["democracy_index"], mode="lines", line=dict(color=c, width=1.2), opacity=.45, hoverinfo="skip"))
    last = d[d["year"].between(y - 10, y)]
    fig.add_trace(go.Scatter(x=last["x"], y=last["democracy_index"], mode="lines", line=dict(color=c, width=2.8), hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=d["x"], y=d["democracy_index"], mode="markers", text=hover, hoverinfo="text", marker=trail_marker(d, c), opacity=.9))
    now = d[d["year"] == y]
    if len(now):
        fig.add_trace(go.Scatter(x=now["x"], y=now["democracy_index"], mode="markers+text", text=[str(y)], textposition="top center",
                                 textfont=dict(color=INK, size=13), hoverinfo="skip",
                                 marker=dict(color=c, size=18, line=dict(color=INK, width=max(1.5, float(ring(now["max_intensity"])[0]))))))
    scatter_frame(fig, ax, 420)
    return fig


@st.cache_data
def scatter_compare(isos, a, b, y, follow, full):
    d = period_panel(isos, max(Y0, y - 10), y).copy()
    if d.empty:
        return None
    focus = set(follow)
    visible = d[d["iso3"].isin(focus) | (d["year"] == y)]
    ax = scatter_axis(visible, period_panel(isos, a, b), full)
    d["x"] = np.where(d["arms_10"] > 0, d["arms_10"], ax["none_x"])
    d["hover"] = (d["country_name"] + " · " + d["year"].astype(str) + "<br>Democracy index " + d["democracy_index"].round(2).astype(str)
                  + " (" + d["regime_label"] + ")<br>Arms received, 10 years to " + d["year"].astype(str) + ": "
                  + d["arms_10"].round(0).astype(int).map("{:,}".format) + " TIV<br>" + d["max_intensity"].map(CONFLICT))
    fig = go.Figure()
    for iso in isos:
        if iso not in focus:
            continue
        t = d[(d["iso3"] == iso) & (d["year"] < y)]
        t = pd.concat([t, d[(d["iso3"] == iso) & (d["year"] == y)]])  # the line runs into the bubble
        fig.add_trace(go.Scatter(x=t["x"], y=t["democracy_index"], mode="lines+markers", opacity=.8, text=t["hover"], hoverinfo="text",
                                 line=dict(color=COL[iso], width=2, dash=DASH[iso]), marker=trail_marker(t, COL[iso])))
    now = d[d["year"] == y].copy()
    now["op"] = np.where(now["iso3"].isin(focus), 1.0, .2)
    now = now.sort_values("op")
    fig.add_trace(go.Scatter(x=now["x"], y=now["democracy_index"], mode="markers", hovertext=now["hover"], hoverinfo="text",
                             marker=dict(size=16, color=now["iso3"].map(COL), opacity=now["op"],
                                         line=dict(color="#111110", width=ring(now["max_intensity"], 0) * 1.3))))
    scatter_frame(fig, ax, 440)
    lab = now[now["iso3"].isin(focus)].assign(label=lambda f: f["country_name"].map(short_name))
    place_labels(fig, lab, now[now["iso3"].isin(focus)], ax)  # faint bubbles may sit under a label
    return fig


@st.cache_data
def one_axis(isos, a, b, same_scale):
    """Per country: democracy index line, conflict years shaded (war darker), arms imports as bars on a second axis."""
    n = len(isos)
    row_h = 150 if n == 1 else 112 if n <= 6 else 84
    fig = make_subplots(rows=n, cols=1, shared_xaxes=True, vertical_spacing=min(.06, 26 / (row_h * n)),
                        specs=[[{"secondary_y": True}]] * n, subplot_titles=[NAMES[i] for i in isos] if n > 1 else None)
    d = period_panel(isos, a, b)
    runs = nd.conflict_runs()
    vmax = max(1.0, d["arms_imports_tiv"].max() if len(d) else 1.0)
    for r, iso in enumerate(isos, start=1):
        t = d[d["iso3"] == iso]
        fig.add_trace(go.Bar(x=t["year"], y=t["arms_imports_tiv"], marker=dict(color="#e48461", opacity=.55), name="Arms imports",
                             hovertemplate="%{x}: %{y:,.0f} TIV<extra>Arms imports</extra>", showlegend=False),
                      row=r, col=1, secondary_y=True)
        fig.add_trace(go.Scatter(x=t["year"], y=t["democracy_index"], mode="lines", line=dict(color=COL[iso], width=2.2), name="Democracy index",
                                 hovertemplate="%{x}: %{y:.2f}<extra>Democracy index</extra>", showlegend=False),
                      row=r, col=1, secondary_y=False)
        for _, c in runs[(runs["iso3"] == iso) & (runs["end"] >= a) & (runs["start"] <= b)].iterrows():  # after the traces: Plotly skips empty subplots
            fig.add_vrect(x0=max(c["start"], a) - .5, x1=min(c["end"], b) + .5, row=r, col=1, line_width=0, layer="below",
                          fillcolor=INK, opacity=.2 if c["intensity"] == 2 else .07, exclude_empty_subplots=False)
        top = vmax if same_scale else max(1.0, t["arms_imports_tiv"].max() if len(t) else 1.0)
        fig.update_yaxes(range=[0, 1], tickvals=[0, .5, 1], row=r, col=1, secondary_y=False)
        fig.update_yaxes(range=[0, top * 1.08], showgrid=False, nticks=3, row=r, col=1, secondary_y=True)
    base_layout(fig, row_h * n + 40, margin=dict(l=0, r=4, t=24 if n > 1 else 8, b=0), bargap=.15, hovermode="x unified")
    fig.update_xaxes(range=[a - .5, b + .5])
    fig.update_yaxes(tickfont=dict(color=MUTED, size=10))
    fig.update_annotations(font=dict(color=INK, size=12), x=0, xanchor="left")
    return fig


@st.cache_data
def regime_chart(isos, a, b):
    s = nd.regime_spans()
    s = s[s["iso3"].isin(isos) & (s["end"] >= a) & (s["start"] <= b)].copy()
    if s.empty:
        return None
    s["from"] = s["start"].clip(lower=a).map(year_ts)
    s["to"] = s["end"].clip(upper=b).map(lambda v: year_ts(v, end=True))
    s["Country"] = s["iso3"].map(NAMES).map(short_name)
    s["Regime"] = s["regime_label"].str.capitalize()
    s["Years"] = s["start"].astype(str) + "–" + s["end"].astype(str)
    fig = px.timeline(s, x_start="from", x_end="to", y="Country", color="Regime", hover_data={"Years": True, "from": False, "to": False, "Country": False},
                      color_discrete_map={r.capitalize(): c for r, c in nd.REGIME_COLOURS.items()},
                      category_orders={"Country": [short_name(NAMES[i]) for i in isos], "Regime": [r.capitalize() for r in nd.REGIMES]})
    fig.update_traces(marker_line_width=0)
    base_layout(fig, 70 + 28 * len(isos), bargap=.25, margin=dict(l=0, r=8, t=30, b=28))
    legend_top(fig)
    fig.update_xaxes(range=[year_ts(a), year_ts(b, end=True)], tickformat="%Y", title=None)
    fig.update_yaxes(title=None, showgrid=False, tickfont=dict(color=INK2))
    return fig


@st.cache_data
def conflict_chart(isos, a, b):
    runs = nd.conflict_runs()
    r = runs[runs["iso3"].isin(isos) & (runs["end"] >= a) & (runs["start"] <= b)].copy()
    if r.empty:
        return None, list(isos)
    r["from"] = r["start"].clip(lower=a).map(year_ts)
    r["to"] = r["end"].clip(upper=b).map(lambda v: year_ts(v, end=True))
    r["Country"] = r["iso3"].map(NAMES).map(short_name)
    r["Conflict"] = r["intensity"].map(CONFLICT)
    r["Years"] = r["start"].astype(str) + "–" + r["end"].astype(str)
    with_c = [i for i in isos if i in set(r["iso3"])]
    fig = px.timeline(r, x_start="from", x_end="to", y="Country", color="Conflict", color_discrete_map=CONFLICT_COLOURS,
                      hover_data={"Years": True, "from": False, "to": False, "Country": False},
                      category_orders={"Country": [short_name(NAMES[i]) for i in with_c], "Conflict": ["War", "Minor conflict"]})
    fig.update_traces(marker_line_width=0)
    base_layout(fig, 70 + 28 * len(with_c), bargap=.25, margin=dict(l=0, r=8, t=30, b=28))
    legend_top(fig)
    fig.update_xaxes(range=[year_ts(a), year_ts(b, end=True)], tickformat="%Y", title=None)
    fig.update_yaxes(title=None, showgrid=False, tickfont=dict(color=INK2))
    return fig, [i for i in isos if i not in with_c]


@st.cache_data
def democracy_lines(isos, a, b):
    d = period_panel(isos, a, b)
    fig = go.Figure()
    for iso in isos:
        t = d[d["iso3"] == iso]
        fig.add_trace(go.Scatter(x=t["year"], y=t["democracy_index"], mode="lines", name=short_name(NAMES[iso]),
                                 line=dict(color=COL[iso], width=2, dash=DASH[iso]),
                                 hovertemplate="%{x}: %{y:.2f}<extra>" + NAMES[iso] + "</extra>"))
    base_layout(fig, 440, margin=dict(l=0, r=8, t=8, b=0), hovermode="closest",
                legend=dict(font=dict(color=INK2, size=11), itemclick="toggle", itemdoubleclick="toggleothers"))
    fig.update_xaxes(range=[a, b])
    fig.update_yaxes(range=[0, 1], title=dict(text="Democracy index", font=dict(color=MUTED, size=12)))
    return fig


def supplier_group(name):
    return name if name in nd.SUPPLIER_COLOURS else "Other suppliers"


@st.cache_data
def supplier_data(isos, a, b):
    f = flows[flows["recipient_iso3"].isin(isos) & flows["year"].between(a, b)].copy()
    f["Supplier"] = f["supplier"].map(supplier_group)
    f["Country"] = f["recipient_iso3"].map(NAMES)
    return f


@st.cache_data
def supplier_bars(isos, a, b):
    f = supplier_data(isos, a, b)
    has = [i for i in isos if f.loc[f["recipient_iso3"] == i, "tiv"].sum() > 0]
    if not has:
        return None, list(isos), 0
    g = f[f["recipient_iso3"].isin(has)].groupby(["Country", "year", "Supplier"], as_index=False)["tiv"].sum()
    order = list(nd.SUPPLIER_COLOURS) + ["Other suppliers"]
    wrap = 1 if len(has) == 1 else 2
    rows = -(-len(has) // wrap)
    fig = px.bar(g, x="year", y="tiv", color="Supplier", facet_col="Country" if len(has) > 1 else None, facet_col_wrap=wrap if len(has) > 1 else 0,
                 color_discrete_map={**nd.SUPPLIER_COLOURS, "Other suppliers": nd.OTHER_COLOUR},
                 category_orders={"Supplier": order, "Country": [NAMES[i] for i in has]},
                 facet_row_spacing=min(.08, 40 / (150 * rows)), facet_col_spacing=.06,
                 labels={"tiv": "TIV", "year": ""})
    fig.update_traces(hovertemplate="%{x}: %{y:,.0f} TIV")
    height = (260 if len(has) == 1 else 150 * rows) + 100
    base_layout(fig, height, bargap=.1, margin=dict(l=0, r=8, t=78, b=0))
    legend_top(fig)
    fig.update_layout(legend=dict(y=.995, yanchor="top", yref="container", entrywidth=120))
    fig.update_yaxes(matches=None, showticklabels=True, nticks=3, title=None, tickfont=dict(size=10))
    fig.update_xaxes(range=[a - .5, b + .5], title=None)
    fig.for_each_annotation(lambda an: an.update(text=an.text.split("=")[-1], font=dict(color=INK, size=12)))
    return fig, [i for i in isos if i not in has], height


@st.cache_data
def sup_dem_chart(isos, a, b):
    s, demo = nd.load_sup_dem()
    s = s[s["iso3"].isin(isos) & s["year"].between(a, b)]
    if s.empty:
        return None, list(isos), demo
    fig = go.Figure()
    for iso in isos:
        t = s[s["iso3"] == iso].sort_values("year").set_index("year").reindex(range(a, b + 1))  # gaps = years without imports
        if t["sup_dem"].notna().sum() == 0:
            continue
        fig.add_trace(go.Scatter(x=t.index, y=t["sup_dem"], mode="lines", name=short_name(NAMES[iso]) if not single else "Supplier democracy (0–1)",
                                 line=dict(color=COL[iso], width=2, dash=DASH[iso]), connectgaps=False,
                                 hovertemplate="%{x}: %{y:.2f}<extra>" + NAMES[iso] + "</extra>"))
        if single:
            fig.add_trace(go.Scatter(x=t.index, y=t["share_dem"], mode="lines", name="Share of TIV from democracies",
                                     line=dict(color=COL[iso], width=1.4, dash="dot"),
                                     hovertemplate="%{x}: %{y:.0%}<extra>Share from democracies</extra>"))
    missing = [i for i in isos if i not in set(s["iso3"])]
    base_layout(fig, 360, margin=dict(l=0, r=8, t=8, b=0), legend=dict(font=dict(color=INK2, size=11)))
    if single:
        legend_top(fig)
    fig.update_xaxes(range=[a, b])
    fig.update_yaxes(range=[0, 1.02], tickvals=[0, .5, 1], title=dict(text="Supplier democracy (0–1)", font=dict(color=MUTED, size=12)))
    return fig, missing, demo


def hex_rgb(h, a=200):
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)] + [a]


@st.cache_data
def country_flows(isos, y):
    f = flows[(flows["year"] == y) & (flows["recipient_iso3"].isin(isos) | flows["supplier_iso3"].isin(isos))]
    f = f[~f["supplier"].isin(["Other", "unknown supplier(s)"])].dropna(subset=["supplier_iso3"]).copy()
    f["recipient"] = f["recipient_iso3"].map(NAMES).fillna(f["recipient_iso3"])
    f["direction"] = np.where(f["recipient_iso3"].isin(isos), "Import", "Export")
    return f.sort_values("tiv", ascending=False)


def flows_deck(f):
    f = f.copy()
    f["s_iso"] = f["supplier_iso3"].replace(nd.HISTORICAL)
    f["r_iso"] = f["recipient_iso3"].replace(nd.HISTORICAL)
    f = f.join(points.rename(columns={"lon": "s_lon", "lat": "s_lat"}), on="s_iso", how="inner")
    f = f.join(points.rename(columns={"lon": "r_lon", "lat": "r_lat"}), on="r_iso", how="inner")
    vmax = flows["tiv"].max()
    f["width"] = 1 + 7 * np.sqrt(f["tiv"] / vmax)
    f["src"] = f["supplier"].map(lambda s: hex_rgb(nd.supplier_colour(s), 230))
    f["tgt"] = f["supplier"].map(lambda s: hex_rgb(nd.supplier_colour(s), 120))
    f["label"] = f["supplier"] + " → " + f["recipient"] + ": " + f["tiv"].round(0).astype(int).map("{:,}".format) + " TIV"
    sel_pts = points.loc[[i for i in pd.Index(sel).map(lambda i: nd.HISTORICAL.get(i, i)) if i in points.index]].reset_index()
    arcs = pdk.Layer("ArcLayer", data=f, get_source_position=["s_lon", "s_lat"], get_target_position=["r_lon", "r_lat"],
                     get_source_color="src", get_target_color="tgt", get_width="width", get_height=0.35, great_circle=False,
                     pickable=True, auto_highlight=True)
    dots = pdk.Layer("ScatterplotLayer", data=sel_pts, get_position=["lon", "lat"], get_fill_color=[228, 132, 97, 230],
                     get_radius=70000, radius_min_pixels=3, radius_max_pixels=7)
    land = pdk.Layer("GeoJsonLayer", data=nd.country_geojson(), filled=True, stroked=True, get_fill_color=[42, 42, 40, 255],
                     get_line_color=[21, 21, 20, 255], line_width_min_pixels=0.5)
    view = pdk.ViewState(latitude=22, longitude=20, zoom=0.55, pitch=30, bearing=0, min_zoom=0.3)
    return pdk.Deck(layers=[land, arcs, dots], initial_view_state=view, map_provider=None, map_style=None,
                    tooltip={"text": "{label}"}, parameters={"clearColor": [0.07, 0.07, 0.06, 1]})


def flows_sankey(f):
    if f.empty:
        return None
    top_s = list(f.groupby("supplier")["tiv"].sum().nlargest(7).index)
    top_r = list(f.groupby("recipient")["tiv"].sum().nlargest(9).index)
    g = f.assign(s=np.where(f["supplier"].isin(top_s), f["supplier"], "Other suppliers"),
                 r=np.where(f["recipient"].isin(top_r), f["recipient"], "Other recipients"))
    links = g.groupby(["s", "r"], as_index=False)["tiv"].sum()
    left = list(links.groupby("s")["tiv"].sum().sort_values(ascending=False).index)
    right = list(links.groupby("r")["tiv"].sum().sort_values(ascending=False).index)
    idx = {n: i for i, n in enumerate(left)}
    idx_r = {n: len(left) + i for i, n in enumerate(right)}

    def rgba(h, a):
        h = h.lstrip("#")
        return "rgba(%d,%d,%d,%s)" % (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)

    fig = go.Figure(go.Sankey(
        arrangement="snap",
        node=dict(label=left + right, pad=8, thickness=10, line=dict(width=0),
                  color=[nd.supplier_colour(n) for n in left] + [INK2] * len(right),
                  hovertemplate="%{label}: %{value:,.0f} TIV<extra></extra>"),
        link=dict(source=links["s"].map(idx), target=links["r"].map(idx_r), value=links["tiv"],
                  color=[rgba(nd.supplier_colour(x), .35) for x in links["s"]],
                  hovertemplate="%{source.label} → %{target.label}: %{value:,.0f} TIV<extra></extra>")))
    fig.update_layout(height=420, margin=dict(l=0, r=0, t=4, b=4), paper_bgcolor=BG, font=dict(color=INK, size=11, family=FONT))
    return fig


# ------------------------------------------------------------------ page body (re-run on its own while playing)
@st.fragment(run_every=SPEEDS[speed] if ss["playing"] else None)
def body():
    a, b = period_bounds()
    if ss["playing"]:
        if ss["year"] >= b:
            ss["playing"] = False
            ss["cc_year_slider"] = ss["year"]
            st.rerun()
        ss["year"] += 1
    y = ss["year"]
    isos = tuple(sel)
    names = [NAMES[i] for i in sel]
    d = period_panel(isos, a, b)

    head_l, head_r = st.columns([3, 1], vertical_alignment="bottom")
    head_l.title(names[0] if single else "Countries & compare")
    head_l.caption(f"Regime, democracy index, armed conflict and arms imports, {a}–{b}." if single
                   else f"{len(sel)} countries side by side, {a}–{b}: " + ", ".join(names[:8]) + ("…" if len(sel) > 8 else "."))
    head_r.markdown(f"## {y}")

    no_data = [i for i in sel if d[d["iso3"] == i].empty]
    if no_data:
        st.info(("No V-Dem data in this period for " + ", ".join(NAMES[i] for i in no_data) + ". ")
                + ("" if len(no_data) < len(sel) else "Try another period."), icon=":material/info:")

    # ---- snapshot of the year
    now = panel[panel["iso3"].isin(isos) & (panel["year"] == y)].set_index("iso3")
    if single:
        iso = sel[0]
        m = st.columns([1.7, 1, 1.1, 1.1, 1.1])
        if iso in now.index:
            r = now.loc[iso]
            m[0].metric("Regime", str(r["regime_label"]).capitalize(), border=True)
            m[1].metric("Democracy index", f"{r['democracy_index']:.2f}", border=True)
            m[2].metric("Armed conflict", CONFLICT[int(r["max_intensity"])], border=True)
            m[3].metric(f"Arms imports {y}", fmt_tiv(r["arms_imports_tiv"]), border=True)
            m[4].metric("Main supplier", main_supplier(iso, y) or "–", border=True)
        else:
            st.caption(f"No data for {NAMES[iso]} in {y}.")
    else:
        with st.container(border=True):
            st.markdown(f"**Snapshot of {y}**")
            snap = pd.DataFrame({"Country": names}, index=list(isos))
            snap["Regime"] = now["regime_label"].str.capitalize()
            snap["Democracy index"] = now["democracy_index"]
            snap["Armed conflict"] = now["max_intensity"].map(lambda v: CONFLICT[int(v)] if pd.notna(v) else None)
            snap["Arms imports"] = now["arms_imports_tiv"].round(0)
            snap["10 years"] = now["arms_10"].round(0)
            snap["Main supplier"] = [main_supplier(i, y) for i in isos]
            snap = snap.sort_values("Democracy index", ascending=False, na_position="last")
            st.dataframe(snap, hide_index=True, height=min(38 + 35 * len(snap), 400), alt=f"Snapshot of the selected countries in {y}",
                         column_config={
                             "Democracy index": st.column_config.ProgressColumn("Democracy index", format="%.2f", min_value=0, max_value=1),
                             "Arms imports": st.column_config.NumberColumn(f"Imports {y} (TIV)", format="localized"),
                             "10 years": st.column_config.NumberColumn("10-year total (TIV)", format="localized"),
                         })

    # ---- scatter + (compare) democracy index / (single) one axis
    left, right = st.columns([1.35, 1], gap="medium")
    with left, st.container(border=True, height="stretch"):
        h_l, h_r = st.columns([2, 1], vertical_alignment="center")
        h_l.markdown("**Democracy vs. arms imports**")
        full = h_r.toggle("Full 0–1 scale", key="cc_full_scale", help="Show the whole democracy index instead of fitting the axis to these countries.")
        if single:
            st.caption(f"The path of {names[0]} through time. Thin line: the whole period; strong part: the last 10 years.")
            fig = scatter_single(sel[0], a, b, y, full)
        else:
            if ss.get("cc_follow_for") != isos:  # a new list: follow everyone up to 8, else the 6 largest importers
                ss["cc_follow_for"] = isos
                ss["cc_follow"] = list(isos) if len(isos) <= 8 else largest_importers(isos, a, b, 6)
            ss["cc_follow"] = [i for i in ss.get("cc_follow", []) if i in isos]
            follow = st.multiselect("Follow in scatter", list(isos), format_func=NAMES.get, key="cc_follow",
                                    placeholder="Pick countries to show their 10-year trails and labels")
            fig = scatter_compare(isos, a, b, y, tuple(follow), full)
        if fig is None:
            st.info(f"No data in {y} for {'this country' if single else 'these countries'}.")
        else:
            st.plotly_chart(fig, key="cc_scatter", config=NO_BAR)
        st.caption(SC_GUIDE + ("" if single else " Trails: the previous 10 years of the followed countries; the others are faint.")
                   + " Bigger dot with a dark ring: war year; smaller ringed dot: minor conflict."
                   + (" Left strip: no arms received." if fig is not None and fig.layout.shapes else ""))
    with right, st.container(border=True, height="stretch"):
        if single:
            st.markdown("**Democracy, conflict and arms on one axis**")
            st.caption("Line: democracy index (0–1). Bars: arms imports (TIV, right axis). Shading: war (darker) or minor conflict.")
            fig = one_axis(isos, a, b, False)
            fig.add_vline(x=y, line=dict(color=INK, width=1.5))
            fig.update_layout(height=420)
            st.plotly_chart(fig, key="cc_axis1", config=NO_BAR)
        else:
            st.markdown("**Democracy index**")
            st.caption("Click a name in the legend to hide it; double-click to show only that country.")
            fig = democracy_lines(isos, a, b)
            fig.add_vline(x=y, line=dict(color=INK, width=1.5))
            st.plotly_chart(fig, key="cc_demo", config=NO_BAR)

    # ---- one axis per country (compare)
    if not single:
        with st.container(border=True):
            h_l, h_r = st.columns([3, 1], vertical_alignment="center")
            h_l.markdown("**Democracy, conflict and arms on one axis**")
            same = h_r.toggle("Same arms scale for all", key="cc_same_scale")
            st.caption("Line: democracy index (0–1, left axis). Bars: arms imports (TIV, right axis). Shading: war (darker) or minor conflict.")
            fig = one_axis(isos, a, b, same)
            fig.add_vline(x=y, line=dict(color=INK, width=1.5))
            with scroll_box(fig.layout.height, 760):
                st.plotly_chart(fig, key="cc_axis", config=NO_BAR)

    # ---- regime + conflicts
    left, right = st.columns(2, gap="medium")
    with left, st.container(border=True, height="stretch"):
        st.markdown("**Regime**")
        fig = regime_chart(isos, a, b)
        if fig is None:
            st.info("No regime data in this period.")
        else:
            add_year_line_dates(fig, y)
            st.plotly_chart(fig, key="cc_regime", config=NO_BAR)
    with right, st.container(border=True, height="stretch"):
        st.markdown("**Armed conflicts**")
        fig, none = conflict_chart(isos, a, b)
        if fig is None:
            st.caption(f"No armed conflict in {a}–{b} (UCDP, 25+ battle deaths a year).")
        else:
            add_year_line_dates(fig, y)
            st.plotly_chart(fig, key="cc_conflict", config=NO_BAR)
            muted_list(f"No armed conflict in {a}–{b}", none)

    # ---- suppliers
    left, right = st.columns([1.5, 1], gap="medium")
    with left, st.container(border=True, height="stretch"):
        st.markdown("**Arms imports by supplier**")
        fig, none, height = supplier_bars(isos, a, b)
        if fig is None:
            st.caption(f"No major arms imports recorded in {a}–{b}.")
        else:
            fig.add_vline(x=y, line=dict(color=INK, width=1.2))
            with scroll_box(height, 760):
                st.plotly_chart(fig, key="cc_sup", config=NO_BAR)
            muted_list(f"No imports in {a}–{b}", none)
            with st.expander("All suppliers"):
                f = supplier_data(isos, a, b)
                t = f.groupby(["Country", "supplier"], as_index=False)["tiv"].sum()
                t["share"] = t["tiv"] / t.groupby("Country")["tiv"].transform("sum")
                t["tiv"] = t["tiv"].round(0)
                t = t.sort_values(["Country", "tiv"], ascending=[True, False])
                st.dataframe(t, hide_index=True, height=min(38 + 35 * len(t), 420), alt="All arms suppliers per country in the period",
                             column_config={"supplier": "Supplier", "tiv": st.column_config.NumberColumn("TIV", format="localized"),
                                            "share": st.column_config.ProgressColumn("Share", format="percent", min_value=0, max_value=1)})
                st.caption("SIPRI names the three largest suppliers per country and year; the rest is grouped as \"Other\".")
    with right, st.container(border=True, height="stretch"):
        st.markdown("**Who supplied the arms**")
        fig, missing, demo = sup_dem_chart(isos, a, b)
        if demo:
            st.warning("Placeholder numbers until notebook 08 is done.", icon=":material/science:")
        st.caption("How democratic the suppliers were, weighted by TIV: 0 = only autocratic suppliers, 1 = only democratic ones.")
        if fig is None:
            st.info(f"No arms imports to weigh in {a}–{b}.")
        else:
            fig.add_vline(x=y, line=dict(color=INK, width=1.2))
            st.plotly_chart(fig, key="cc_supdem", config=NO_BAR)
            muted_list("No imports to weigh", missing)

    # ---- arms flows
    with st.container(border=True):
        st.markdown(f"**Arms flows {'of ' + names[0] if single else 'of these countries'} in {y}**")
        f = country_flows(isos, y)
        if f.empty:
            st.info(f"No named deliveries to or from {'this country' if single else 'these countries'} in {y}.")
        else:
            imp, exp = f.loc[f["direction"] == "Import", "tiv"].sum(), f.loc[f["direction"] == "Export", "tiv"].sum()
            st.caption(f"Deliveries to or from {'it' if single else 'the selected countries'}: {imp:,.0f} TIV received, {exp:,.0f} TIV delivered "
                       "(SIPRI's three largest suppliers per recipient). Arc width = TIV, colour = supplier.")
            map_col, sk_col = st.columns([1.5, 1], gap="medium")
            with map_col:
                n = 60
                st.pydeck_chart(flows_deck(f.head(n)), height=420, key="cc_flows")
                if len(f) > n:
                    st.badge(f"Largest {n} of {len(f)} deliveries drawn", color="gray")
            with sk_col:
                st.plotly_chart(flows_sankey(f), key="cc_sankey", config=NO_BAR)


body()
