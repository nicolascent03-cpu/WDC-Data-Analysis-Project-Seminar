"""Countries & compare, built only with Streamlit (no custom HTML).

One country or a group side by side: a snapshot of the chosen year, democracy vs. arms imports as a
scatter with 10-year trails, democracy, conflict and arms on one shared year axis, regime periods,
the democracy index, armed conflicts by name, imports by supplier (every supplier SIPRI names), how
democratic the suppliers were, the arms flows to and from these countries and the year-by-year
numbers. Controls live in the sidebar; Play advances the year for the whole page.
"""

import json
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
CONFLICT_COLOURS = {"War": "#ece8e0", "Minor conflict": "#6a655d"}  # as in the HTML version (dark theme)
UCDP_TYPE = {1: "Extrasystemic", 2: "Interstate", 3: "Intrastate", 4: "Internationalised intrastate"}
EXTRA_SUP = ["#2bb5c0", "#a3b54a", "#e07ab0", "#b98a68", "#a39d92", "#6f6a62"]  # suppliers without a fixed colour
UNKNOWN = "unknown supplier(s)"
NO_BAR = {"displayModeBar": False}
SC_GUIDE = ("Up = more democratic, right = more arms received (10-year total, log scale). "
            "Moving together is not proof that one drives the other.")
ROWS_MAX = 24  # more countries than this: the per-country row charts show only the followed countries
LEGEND_MAX = 10  # more countries than this: no legend, the followed countries stand out instead

panel = nd.load_panel()
flows = nd.load_flows()
points = nd.country_points()
NAMES = panel.drop_duplicates("iso3").set_index("iso3")["country_name"].to_dict()
ALL_ISO = sorted(NAMES, key=NAMES.get)
GROUPS = {"All countries": ALL_ISO, **nd.country_groups()}

# ------------------------------------------------------------------ state
ss = st.session_state
ss.setdefault("year", 2000)
ss.setdefault("playing", False)
# The country list is bound to the URL, which holds the country names (?countries=Ethiopia&countries=Eritrea).
# The URL wins when it names countries.
if "countries" not in st.query_params:
    ss.setdefault("countries", ["ETH"])
# one-shot hand-overs from other pages: a group picked on Start, or countries chosen on the World map
_group = ss.pop("cmp_group", None)
if _group in GROUPS:
    ss["countries"] = list(GROUPS[_group])
    ss["cc_group_name"] = _group
    ss.pop("cc_follow", None)
_picked = [i for i in (ss.pop("cmp_countries", None) or []) if i in NAMES]
if _picked:
    ss["countries"] = _picked
    ss.pop("cc_group_name", None)
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


def countries_changed():
    ss.pop("cc_group_name", None)


def group_chosen():
    name = ss.get("cc_group")
    if name:
        ss["countries"] = list(GROUPS[name])
        ss["cc_group_name"] = name
        ss.pop("cc_follow", None)
    ss["cc_group"] = None


def clear_comparison():
    keep = ss.get("countries") or ["ETH"]
    ss["countries"] = keep[:1]
    ss.pop("cc_group_name", None)
    ss.pop("cc_follow", None)


def scatter_clicked():
    """A click on a dot of the scatter: jump to that year; in a comparison, also follow that country."""
    try:
        pts = ss["cc_scatter"]["selection"]["points"]
    except (KeyError, TypeError):
        return
    if not pts or "customdata" not in pts[0]:
        return
    year, iso = pts[0]["customdata"][:2]
    p0, p1 = period_bounds()
    ss["year"] = min(max(int(year), p0), p1)
    ss["cc_year_slider"] = ss["year"]
    ss["playing"] = False
    if iso in NAMES and len(ss.get("countries") or []) > 1 and iso not in (ss.get("cc_follow") or []):
        ss["cc_follow"] = list(ss.get("cc_follow") or []) + [iso]
    ss["cc_full_rerun"] = True  # the sidebar slider sits outside the page fragment


# keep the slider on the page-wide year (it may have moved on another page) and inside the period
clamp_year()

# ------------------------------------------------------------------ sidebar
with st.sidebar:
    st.multiselect("Countries", ALL_ISO, format_func=NAMES.get, key="countries", bind="query-params",
                   placeholder="Add a country…", on_change=countries_changed)
    st.selectbox("Preset groups", list(GROUPS), index=None, key="cc_group", on_change=group_chosen,
                 placeholder="Choose a group…", format_func=lambda g: f"{g} ({len(GROUPS[g])})",
                 help="Replaces the list above with the members of the group.")
    st.button("Clear comparison", icon=":material/close:", on_click=clear_comparison, width="stretch",
              disabled=len(ss.get("countries") or []) < 2, help="Keep only the first country.")
    st.divider()
    st.segmented_control("Period", list(PERIODS), default="1950–2025", key="cc_period", on_change=clamp_year,
                         width="stretch", required=True)
    p0, p1 = period_bounds()
    st.slider("Year", p0, p1, key="cc_year_slider", on_change=slider_moved, disabled=ss["playing"])
    st.button("Pause" if ss["playing"] else "Play through the years", icon=":material/pause:" if ss["playing"] else ":material/play_arrow:",
              type="primary", on_click=toggle_play, width="stretch")
    speed = st.segmented_control("Speed", list(SPEEDS), default="1×", key="cc_speed", width="stretch", required=True) or "1×"
    st.caption("SIPRI trend-indicator values (TIV, millions) measure military capability transferred, not money. "
               "Some states appear under a successor's code, as in V-Dem (Russia for the Soviet Union before 1991).")

sel = [i for i in (ss.get("countries") or []) if i in NAMES]
if not sel:
    st.title("Countries & compare")
    st.info("Choose at least one country in the sidebar, or pick a preset group.", icon=":material/arrow_back:")
    st.stop()
single = len(sel) == 1
COL = {iso: nd.COMPARE_COLOURS[k % len(nd.COMPARE_COLOURS)] for k, iso in enumerate(sel)}
DASH = {iso: "solid" if k < len(nd.COMPARE_COLOURS) else "dot" for k, iso in enumerate(sel)}


# ------------------------------------------------------------------ data helpers
@st.cache_data
def load_conflicts():
    """Every UCDP conflict per country with its name and its periods (D.conflicts in app/site/data.json).
    Name as in the HTML version: interstate conflicts name the other side ("vs. Somalia"), others side B."""
    data = json.loads((nd.ROOT / "app" / "site" / "data.json").read_text(encoding="utf8"))["conflicts"]
    names = panel.drop_duplicates("iso3").set_index("iso3")["country_name"].to_dict()
    rows = []
    for iso, lst in data.items():
        for c in lst:
            sa, sb = c["a"].replace("Government of ", ""), c["b"].replace("Government of ", "")
            inter = any(p[3] == 2 for p in c["p"])
            is_b = sb.split(" (")[0] == names.get(iso)  # this country is side B (e.g. Russia vs. Ukraine on Ukraine's page)
            name = "vs. " + (sa if is_b else sb) if inter else sb
            for s, e, inten, typ in c["p"]:
                rows.append((iso, c["id"], name, f"{c['a']} vs. {c['b']}", c["t"], s, e, inten, UCDP_TYPE.get(typ, "")))
    return pd.DataFrame(rows, columns=["iso3", "id", "name", "sides", "territory", "start", "end", "intensity", "type"])


@st.cache_data
def active_conflicts(isos, y):
    c = load_conflicts()
    c = c[c["iso3"].isin(isos) & (c["start"] <= y) & (c["end"] >= y)]
    return c.groupby("iso3")["name"].agg(lambda s: list(dict.fromkeys(s))).to_dict()


@st.cache_data
def period_panel(isos, a, b):
    return panel[panel["iso3"].isin(isos) & panel["year"].between(a, b)]


@st.cache_data
def largest_importers(isos, a, b, n):
    tot = period_panel(isos, a, b).groupby("iso3")["arms_imports_tiv"].sum()
    return [i for i in isos if i in set(tot.nlargest(n).index)]


@st.cache_data
def supplier_data(isos, a, b):
    f = flows[flows["recipient_iso3"].isin(isos) & flows["year"].between(a, b)].copy()
    f["Country"] = f["recipient_iso3"].map(NAMES)
    return f


@st.cache_data
def supplier_colours(isos, a, b, n=7):
    """Colours for the largest suppliers of these countries in the period (fixed colours for the big
    exporters, others from a spare palette); everything else is drawn as "Other suppliers"."""
    tot = supplier_data(isos, a, b).groupby("supplier")["tiv"].sum().sort_values(ascending=False)
    spare = iter(EXTRA_SUP)
    out = {}
    for s in [s for s in tot.index if s != UNKNOWN][:n]:
        out[s] = nd.SUPPLIER_COLOURS.get(s) or next(spare, nd.OTHER_COLOUR)
    return out


def main_supplier(iso, y):
    f = flows[(flows["recipient_iso3"] == iso) & (flows["year"] == y) & (flows["supplier"] != UNKNOWN)]
    return f.sort_values("tiv", ascending=False)["supplier"].iloc[0] if len(f) else None


# ------------------------------------------------------------------ chart helpers
def base_layout(fig, height, **kw):
    fig.update_layout(height=height, paper_bgcolor=BG, plot_bgcolor=BG, font=dict(family=FONT, color=INK2, size=12),
                      margin=kw.pop("margin", dict(l=0, r=8, t=8, b=0)),
                      hoverlabel=dict(bgcolor=INK, font_color="#111110", font_family=FONT), **kw)
    fig.update_xaxes(gridcolor=LINE, zeroline=False, linecolor=LINE, tickfont=dict(color=MUTED), automargin=True)
    fig.update_yaxes(gridcolor=LINE, zeroline=False, linecolor=LINE, tickfont=dict(color=MUTED), automargin=True)
    return fig


def legend_top(fig, entrywidth=150):
    fig.update_layout(legend=dict(orientation="h", x=0, y=1.02, yanchor="bottom", font=dict(color=INK2, size=11), title_text="",
                                  entrywidth=entrywidth, entrywidthmode="pixels"))


def year_ts(y, end=False):
    return datetime(y + 1 if end else y, 1, 1)


def year_line(fig, y, dates=False, width=1.5):
    """A vertical line at the year over the whole figure: one shape, also on figures with many subplots."""
    x = datetime(y, 7, 1) if dates else y
    fig.add_shape(type="line", x0=x, x1=x, xref="x", yref="paper", y0=0, y1=1, line=dict(color=INK, width=width))


def scroll_box(height_px, limit):
    """A card body that scrolls when the chart is taller than `limit` pixels."""
    return st.container(height=limit) if height_px > limit else st.container()


def muted_list(label, isos):
    if isos:
        st.caption(f"{label} ({len(isos)}): " + ", ".join(NAMES[i] for i in isos) + ".")


def fmt_tiv(v):
    return "–" if pd.isna(v) else f"{v:,.0f} TIV" if v >= 10 or v == 0 else f"{v:,.1f} TIV"


SHORT = {"United States of America": "United States", "Democratic Republic of the Congo": "DR Congo",
         "Central African Republic": "Central African Rep.", "Bosnia and Herzegovina": "Bosnia", "United Arab Emirates": "UAE",
         "Republic of the Congo": "Congo", "Republic of Vietnam": "South Vietnam", "German Democratic Republic": "East Germany"}


def short_name(n, k=18):
    n = SHORT.get(n, n)
    return n if len(n) <= k else n[:k - 1] + "…"


def runs(years):
    """Consecutive runs in a sorted list of years, as (first, last) pairs."""
    out = []
    for yr in years:
        if out and yr == out[-1][1] + 1:
            out[-1][1] = yr
        else:
            out.append([yr, yr])
    return out


# ------------------------------------------------------------------ scatter
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


def conflict_wraps(fig, t):
    """Bands along a path wherever two consecutive years both had an armed conflict: a solid band when both
    years were war, a dashed one otherwise (as in the HTML version)."""
    t = t.sort_values("year")
    segs = {"war": ([], []), "minor": ([], [])}
    prev = None
    for x, yv, yr, c in t[["x", "democracy_index", "year", "max_intensity"]].itertuples(index=False):
        if prev is not None and prev[2] == yr - 1 and prev[3] and c:
            xs, ys = segs["war" if prev[3] == 2 and c == 2 else "minor"]
            xs += [prev[0], x, None]
            ys += [prev[1], yv, None]
        prev = (x, yv, yr, c)
    for kind, (xs, ys) in segs.items():
        if xs:
            fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", hoverinfo="skip", showlegend=False,
                                     line=dict(color="rgba(236,232,224,0.2)" if kind == "war" else "rgba(236,232,224,0.16)",
                                               width=8 if kind == "war" else 6, dash="solid" if kind == "war" else "dot")))


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


def hover_text(d):
    return (d["country_name"] + " · " + d["year"].astype(str) + "<br>Democracy index " + d["democracy_index"].round(2).astype(str)
            + " (" + d["regime_label"] + ")<br>Arms received " + (d["year"] - 9).clip(lower=Y0).astype(str) + "–" + d["year"].astype(str)
            + ": " + d["arms_10"].round(0).astype(int).map("{:,}".format) + " TIV<br>In " + d["year"].astype(str) + " alone: "
            + d["arms_imports_tiv"].round(0).astype(int).map("{:,}".format) + " TIV<br>" + d["max_intensity"].map(CONFLICT)
            + "<br><i>Click to jump to " + d["year"].astype(str) + "</i>")


@st.cache_data
def scatter_single(iso, a, b, y, full):
    d = period_panel((iso,), a, b).dropna(subset=["democracy_index"]).copy()
    if d.empty:
        return None
    ax = scatter_axis(d, d, full)
    fig = go.Figure()
    d["x"] = np.where(d["arms_10"] > 0, d["arms_10"], ax["none_x"])
    d["hover"] = hover_text(d)
    c = COL[iso]
    conflict_wraps(fig, d)
    fig.add_trace(go.Scatter(x=d["x"], y=d["democracy_index"], mode="lines", line=dict(color=c, width=1.2), opacity=.45, hoverinfo="skip"))
    last = d[d["year"].between(y - 10, y)]
    fig.add_trace(go.Scatter(x=last["x"], y=last["democracy_index"], mode="lines", line=dict(color=c, width=2.8), hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=d["x"], y=d["democracy_index"], mode="markers", text=d["hover"], hoverinfo="text",
                             customdata=np.column_stack([d["year"], d["iso3"]]), marker=trail_marker(d, c), opacity=.9))
    dec = d[(d["year"] % 10 == 0) & (d["year"] != y)]  # decade labels, as in the HTML version
    fig.add_trace(go.Scatter(x=dec["x"], y=dec["democracy_index"], mode="text", text=dec["year"].astype(str), textposition="top right",
                             textfont=dict(color=MUTED, size=11), hoverinfo="skip"))
    now = d[d["year"] == y]
    if len(now):
        fig.add_trace(go.Scatter(x=now["x"], y=now["democracy_index"], mode="markers+text", text=[str(y)], textposition="top center",
                                 textfont=dict(color=INK, size=13), hoverinfo="skip",
                                 marker=dict(color=c, size=18, line=dict(color=INK, width=max(1.5, float(ring(now["max_intensity"])[0]))))))
    scatter_frame(fig, ax, 440)
    return fig


@st.cache_data
def scatter_compare(isos, a, b, y, follow, full):
    d = period_panel(isos, max(Y0, y - 10), y).dropna(subset=["democracy_index"]).copy()
    if d.empty or not (d["year"] == y).any():
        return None
    focus = set(follow)
    visible = d[d["iso3"].isin(focus) | (d["year"] == y)]
    ax = scatter_axis(visible, period_panel(isos, a, b).dropna(subset=["democracy_index"]), full)
    d["x"] = np.where(d["arms_10"] > 0, d["arms_10"], ax["none_x"])
    d["hover"] = hover_text(d)
    fig = go.Figure()
    for iso in isos:
        if iso in focus:
            conflict_wraps(fig, d[d["iso3"] == iso])
    for iso in isos:
        if iso not in focus:
            continue
        t = d[d["iso3"] == iso].sort_values("year")  # the line runs into the bubble
        fig.add_trace(go.Scatter(x=t["x"], y=t["democracy_index"], mode="lines+markers", opacity=.8, text=t["hover"], hoverinfo="text",
                                 customdata=np.column_stack([t["year"], t["iso3"]]),
                                 line=dict(color=COL[iso], width=2, dash=DASH[iso]), marker=trail_marker(t, COL[iso])))
    now = d[d["year"] == y].copy()
    now["op"] = np.where(now["iso3"].isin(focus), 1.0, .2)
    now = now.sort_values("op")
    fig.add_trace(go.Scatter(x=now["x"], y=now["democracy_index"], mode="markers", hovertext=now["hover"], hoverinfo="text",
                             customdata=np.column_stack([now["year"], now["iso3"]]),
                             marker=dict(size=16, color=now["iso3"].map(COL), opacity=now["op"],
                                         line=dict(color="#111110", width=ring(now["max_intensity"], 0) * 1.3))))
    scatter_frame(fig, ax, 440)
    lab = now[now["iso3"].isin(focus)].assign(label=lambda f: f["country_name"].map(short_name))
    place_labels(fig, lab, now[now["iso3"].isin(focus)], ax)  # faint bubbles may sit under a label
    return fig


# ------------------------------------------------------------------ timelines
@st.cache_data
def one_axis(isos, a, b, same_scale):
    """Per country: democracy index line, conflict years shaded (war darker), arms imports as bars on a second axis."""
    n = len(isos)
    row_h = 150 if n == 1 else 112 if n <= 6 else 84
    fig = make_subplots(rows=n, cols=1, shared_xaxes=True, vertical_spacing=min(.06, 26 / (row_h * n)),
                        specs=[[{"secondary_y": True}]] * n, subplot_titles=[NAMES[i] for i in isos] if n > 1 else None)
    d = period_panel(isos, a, b)
    cruns = nd.conflict_runs()
    conf = load_conflicts()
    vmax = max(1.0, d["arms_imports_tiv"].max() if len(d) else 1.0)
    shapes = []
    for r, iso in enumerate(isos, start=1):
        t = d[d["iso3"] == iso]
        c = conf[conf["iso3"] == iso]
        names = [", ".join(dict.fromkeys(c.loc[(c["start"] <= yr) & (c["end"] >= yr), "name"])) for yr in t["year"]]
        hover = [f"{v:.2f} ({reg})" if pd.notna(v) else "no data" for v, reg in zip(t["democracy_index"], t["regime_label"])]
        conf_txt = [CONFLICT[int(m)] + (f" ({nm[:60]})" if nm else "") for m, nm in zip(t["max_intensity"], names)]
        fig.add_trace(go.Bar(x=t["year"], y=t["arms_imports_tiv"], marker=dict(color="#e48461", opacity=.55), name="Arms imports",
                             hovertemplate="%{y:,.0f} TIV<extra>Arms imports</extra>", showlegend=False),
                      row=r, col=1, secondary_y=True)
        fig.add_trace(go.Scatter(x=t["year"], y=t["democracy_index"], mode="lines", line=dict(color=COL[iso], width=2.2), name="Democracy index",
                                 customdata=np.column_stack([hover, conf_txt]),
                                 hovertemplate="%{customdata[0]}<extra>Democracy index</extra>", showlegend=False),
                      row=r, col=1, secondary_y=False)
        fig.add_trace(go.Scatter(x=t["year"], y=[0] * len(t), mode="markers", marker=dict(opacity=0), customdata=conf_txt,
                                 hovertemplate="%{customdata}<extra>Conflict</extra>", showlegend=False),
                      row=r, col=1, secondary_y=False)
        y_dom = fig.get_subplot(r, 1).yaxis.domain  # shading as plain shapes, set once below (add_vrect is slow with many rows)
        for cr in cruns[(cruns["iso3"] == iso) & (cruns["end"] >= a) & (cruns["start"] <= b)].itertuples():
            shapes.append(dict(type="rect", xref="x", yref="paper", x0=max(cr.start, a) - .5, x1=min(cr.end, b) + .5,
                               y0=y_dom[0], y1=y_dom[1], line_width=0, layer="below", fillcolor=INK,
                               opacity=.2 if cr.intensity == 2 else .07))
        top = vmax if same_scale else max(1.0, t["arms_imports_tiv"].max() if len(t) else 1.0)
        fig.update_yaxes(range=[0, 1], tickvals=[0, .5, 1], row=r, col=1, secondary_y=False)
        fig.update_yaxes(range=[0, top * 1.08], showgrid=False, nticks=3, row=r, col=1, secondary_y=True)
    fig.update_layout(shapes=shapes)
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
    base_layout(fig, 90 + 26 * len(isos), bargap=.25, margin=dict(l=12, r=8, t=8, b=28))
    legend_top(fig, 150)
    fig.update_xaxes(range=[year_ts(a), year_ts(b, end=True)], tickformat="%Y", title=None)
    fig.update_yaxes(title=None, showgrid=False, tickfont=dict(color=INK2))
    return fig


def row_bars(fig, rows, label_y, colour, name, hover, legend=True):
    """Horizontal bars from `start` to `end` (years, inclusive) on the rows `label_y`."""
    fig.add_trace(go.Bar(orientation="h", y=label_y, x=rows["end"] - rows["start"] + 1, base=rows["start"] - .5,
                         marker=dict(color=colour, line_width=0), name=name, showlegend=legend, hovertext=hover,
                         hoverinfo="text", width=.62))


@st.cache_data
def conflict_chart(isos, a, b):
    """One row per conflict (named as in the HTML version), bars for its war and minor years in the period."""
    c = load_conflicts()
    c = c[c["iso3"].isin(isos) & (c["end"] >= a) & (c["start"] <= b)].copy()
    if c.empty:
        return None, list(isos), 0, 0
    c["s"], c["e"] = c["start"].clip(lower=a), c["end"].clip(upper=b)
    c["years"] = c["e"] - c["s"] + 1
    order = {iso: k for k, iso in enumerate(isos)}
    first = c.groupby(["iso3", "name"])["s"].transform("min")
    c = c.assign(k=c["iso3"].map(order), first=first).sort_values(["k", "first", "name", "s"])
    tot = c.groupby(["iso3", "name"])["years"].sum()
    c["label"] = [f"{short_name(nm, 24)} · {tot[(iso, nm)]} yr" for iso, nm in zip(c["iso3"], c["name"])]
    keys = list(dict.fromkeys(zip(c["iso3"], c["label"])))
    ylab = (lambda f: [f["label"].tolist()]) if single else (lambda f: [f["iso3"].map(NAMES).map(short_name).tolist(), f["label"].tolist()])
    fig = go.Figure()
    allrows = pd.DataFrame({"iso3": [k[0] for k in keys], "label": [k[1] for k in keys]})
    fig.add_trace(go.Bar(orientation="h", y=ylab(allrows)[0] if single else ylab(allrows), x=[0] * len(allrows), base=[a] * len(allrows),
                         showlegend=False, hoverinfo="skip", marker_color=BG))  # fixes the row order
    for inten, name in [(2, "War"), (1, "Minor conflict")]:
        r = c[c["intensity"] == inten]
        if r.empty:
            continue
        hover = (r["sides"] + "<br>" + r["type"] + np.where(r["territory"] != "", " · territory: " + r["territory"], " · over government")
                 + "<br>" + r["start"].astype(str) + np.where(r["end"] > r["start"], "–" + r["end"].astype(str), "")
                 + ("<br>War, 1000+ battle deaths a year" if inten == 2 else "<br>Minor, 25–999 battle deaths a year"))
        y = ylab(r)
        row_bars(fig, r, y[0] if single else y, CONFLICT_COLOURS[name], name, hover)
    n = len(keys)
    height = 40 + 25 * n
    base_layout(fig, height, barmode="overlay", margin=dict(l=0, r=8, t=28, b=4), showlegend=False)
    fig.update_xaxes(range=[a - .5, b + .5], title=None, dtick=20 if b - a > 50 else 10, tickangle=0, side="top")
    fig.update_yaxes(autorange="reversed", showgrid=False, tickfont=dict(color=INK2, size=11), title=None)
    return fig, [i for i in isos if i not in set(c["iso3"])], height, c["iso3"].nunique()


@st.cache_data
def democracy_lines(isos, a, b, follow):
    d = period_panel(isos, a, b)
    focus = set(follow) or set(isos)
    legend = len(isos) <= LEGEND_MAX
    fig = go.Figure()
    for iso in sorted(isos, key=lambda i: i in focus):  # followed lines on top
        t = d[d["iso3"] == iso]
        on = iso in focus
        fig.add_trace(go.Scatter(x=t["year"], y=t["democracy_index"], mode="lines", name=short_name(NAMES[iso]),
                                 line=dict(color=COL[iso], width=2 if on else 1, dash=DASH[iso]), opacity=1 if on else .22,
                                 hovertemplate="%{y:.2f}<extra>" + NAMES[iso] + "</extra>", legendrank=list(isos).index(iso)))
    base_layout(fig, 440, margin=dict(l=0, r=8, t=8, b=0), hovermode="x unified" if len(isos) <= 12 else "closest", showlegend=legend,
                legend=dict(font=dict(color=INK2, size=11), itemclick="toggle", itemdoubleclick="toggleothers"))
    fig.update_xaxes(range=[a, b])
    fig.update_yaxes(range=[0, 1], title=dict(text="Democracy index", font=dict(color=MUTED, size=12)))
    return fig


@st.cache_data
def supplier_bars(isos, a, b):
    f = supplier_data(isos, a, b)
    has = [i for i in isos if f.loc[f["recipient_iso3"] == i, "tiv"].sum() > 0]
    if not has:
        return None, list(isos), 0
    cmap = supplier_colours(isos, a, b)
    f = f[f["recipient_iso3"].isin(has)].assign(Supplier=lambda x: x["supplier"].where(x["supplier"].isin(cmap.keys()), "Other suppliers"))
    g = f.groupby(["Country", "year", "Supplier"], as_index=False)["tiv"].sum()
    wrap = 1 if len(has) == 1 else 2
    rows = -(-len(has) // wrap)
    fig = px.bar(g, x="year", y="tiv", color="Supplier", facet_col="Country" if len(has) > 1 else None, facet_col_wrap=wrap if len(has) > 1 else 0,
                 color_discrete_map={**cmap, "Other suppliers": nd.OTHER_COLOUR},
                 category_orders={"Supplier": list(cmap) + ["Other suppliers"], "Country": [NAMES[i] for i in has]},
                 facet_row_spacing=min(.08, 40 / (150 * rows)), facet_col_spacing=.06,
                 labels={"tiv": "TIV", "year": ""})
    fig.update_traces(hovertemplate="%{x}: %{y:,.1f} TIV<extra>%{fullData.name}</extra>")
    top = 40 + 18 * -(-(len(cmap) + 1) // 2)  # room for the legend (two entries a line in this card)
    height = (260 if len(has) == 1 else 150 * rows) + top + 20
    base_layout(fig, height, bargap=.1, margin=dict(l=0, r=8, t=top, b=0))
    legend_top(fig, 125)
    fig.update_layout(legend=dict(y=.995, yanchor="top", yref="container"))
    fig.update_yaxes(matches=None, showticklabels=True, nticks=3, title=None, tickfont=dict(size=10))
    fig.update_xaxes(range=[a - .5, b + .5], title=None)
    fig.for_each_annotation(lambda an: an.update(text=an.text.split("=")[-1], font=dict(color=INK, size=12)))
    return fig, [i for i in isos if i not in has], height


@st.cache_data
def supplier_rows(iso, a, b):
    """Every supplier of one country in the period: a bar for each run of years with deliveries, total on the label."""
    f = supplier_data((iso,), a, b)
    if f.empty:
        return None, None
    cmap = supplier_colours((iso,), a, b, n=4)
    tot = f.groupby("supplier")["tiv"].sum().sort_values(ascending=False)
    lab = {s: f"{short_name(s, 22)} · {v:,.0f}" for s, v in tot.items()}
    fig = go.Figure()
    fig.add_trace(go.Bar(orientation="h", y=[lab[s] for s in tot.index], x=[0] * len(tot), base=[a] * len(tot),
                         showlegend=False, hoverinfo="skip", marker_color=BG))
    for s in tot.index:
        t = f[f["supplier"] == s].sort_values("year")
        rr = pd.DataFrame(runs(t["year"].tolist()), columns=["start", "end"])
        sums = [t.loc[t["year"].between(p, q), "tiv"].sum() for p, q in rr.itertuples(index=False)]
        hover = [f"{s}<br>{p}" + (f"–{q}" if q > p else "") + f"<br>{v:,.1f} TIV delivered" for (p, q), v in zip(rr.itertuples(index=False), sums)]
        row_bars(fig, rr, [lab[s]] * len(rr), cmap.get(s, nd.OTHER_COLOUR), s, hover, legend=False)
    height = 40 + 24 * len(tot)
    base_layout(fig, height, barmode="overlay", margin=dict(l=0, r=8, t=28, b=4), showlegend=False)
    fig.update_xaxes(range=[a - .5, b + .5], title=None, side="top")
    fig.update_yaxes(autorange="reversed", showgrid=False, tickfont=dict(color=INK2, size=11), title=None)
    table = tot.rename("TIV").reset_index().rename(columns={"supplier": "Supplier"})
    yrs = f.groupby("supplier")["year"].agg(["min", "max", "nunique"])
    table["Years"] = table["Supplier"].map(lambda s: f"{yrs.loc[s, 'min']}–{yrs.loc[s, 'max']}" if yrs.loc[s, "max"] > yrs.loc[s, "min"] else str(yrs.loc[s, "min"]))
    table["Years with deliveries"] = table["Supplier"].map(yrs["nunique"])
    table["Share"] = 100 * table["TIV"] / table["TIV"].sum()
    return fig, table


@st.cache_data
def sup_dem_chart(isos, a, b, follow):
    s, demo = nd.load_sup_dem()
    s = s[s["iso3"].isin(isos) & s["year"].between(a, b)]
    if s.empty:
        return None, list(isos), demo
    focus = set(follow) or set(isos)
    fig = go.Figure()
    for iso in sorted(isos, key=lambda i: i in focus):
        t = s[s["iso3"] == iso].sort_values("year").set_index("year").reindex(range(a, b + 1))  # gaps = years without imports
        if t["sup_dem"].notna().sum() == 0:
            continue
        on = iso in focus
        fig.add_trace(go.Scatter(x=t.index, y=t["sup_dem"], mode="lines+markers", name=short_name(NAMES[iso]) if not single else "Supplier democracy (0–1)",
                                 line=dict(color=COL[iso], width=2 if on else 1, dash=DASH[iso]), connectgaps=False, opacity=1 if on else .22,
                                 marker=dict(size=np.where(t["sup_dem"].notna() & t["sup_dem"].shift(1).isna() & t["sup_dem"].shift(-1).isna(), 5, 0)),
                                 hovertemplate="%{y:.2f}<extra>" + NAMES[iso] + "</extra>", legendrank=list(isos).index(iso)))
        if single:
            fig.add_trace(go.Scatter(x=t.index, y=t["share_dem"], mode="lines", name="Share of TIV from democracies",
                                     line=dict(color=COL[iso], width=1.4, dash="dot"),
                                     hovertemplate="%{y:.0%}<extra>Share from democracies</extra>"))
    missing = [i for i in isos if i not in set(s["iso3"])]
    base_layout(fig, 360, margin=dict(l=0, r=8, t=8, b=0), legend=dict(font=dict(color=INK2, size=11)),
                hovermode="x unified" if len(isos) <= 12 else "closest", showlegend=len(isos) <= LEGEND_MAX)
    if single:
        legend_top(fig, 200)
    fig.update_xaxes(range=[a, b])
    fig.update_yaxes(range=[0, 1.02], tickvals=[0, .5, 1], title=dict(text="Supplier democracy (0–1)", font=dict(color=MUTED, size=12)))
    return fig, missing, demo


# ------------------------------------------------------------------ arms flows
def hex_rgb(h, a=200):
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)] + [a]


@st.cache_data
def country_flows(isos, y):
    f = flows[(flows["year"] == y) & (flows["recipient_iso3"].isin(isos) | flows["supplier_iso3"].isin(isos))]
    f = f[f["supplier"] != UNKNOWN].copy()
    f["recipient"] = f["recipient_iso3"].map(NAMES).fillna(f["recipient_iso3"])
    f["direction"] = np.where(f["recipient_iso3"].isin(isos), "Import", "Export")
    return f.sort_values("tiv", ascending=False)


def flow_colour(s, cmap):
    return cmap.get(s) or nd.supplier_colour(s)


def flows_deck(f, cmap):
    f = f.dropna(subset=["supplier_iso3"]).copy()
    f["s_iso"] = f["supplier_iso3"].replace(nd.HISTORICAL)
    f["r_iso"] = f["recipient_iso3"].replace(nd.HISTORICAL)
    f = f.join(points.rename(columns={"lon": "s_lon", "lat": "s_lat"}), on="s_iso", how="inner")
    f = f.join(points.rename(columns={"lon": "r_lon", "lat": "r_lat"}), on="r_iso", how="inner")
    vmax = flows["tiv"].max()
    f["width"] = 1 + 7 * np.sqrt(f["tiv"] / vmax)
    f["src"] = f["supplier"].map(lambda s: hex_rgb(flow_colour(s, cmap), 230))
    f["tgt"] = f["supplier"].map(lambda s: hex_rgb(flow_colour(s, cmap), 120))
    f["label"] = f["supplier"] + " → " + f["recipient"] + ": " + f["tiv"].map(lambda v: f"{v:,.1f}" if v < 10 else f"{v:,.0f}") + " TIV"
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


def flows_sankey(f, cmap):
    if f.empty:
        return None
    top_s = list(f.groupby("supplier")["tiv"].sum().nlargest(8).index)
    top_r = list(f.groupby("recipient")["tiv"].sum().nlargest(10).index)
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
                  color=[flow_colour(n, cmap) for n in left] + [INK2] * len(right),
                  hovertemplate="%{label}: %{value:,.0f} TIV<extra></extra>"),
        link=dict(source=links["s"].map(idx), target=links["r"].map(idx_r), value=links["tiv"],
                  color=[rgba(flow_colour(x, cmap), .35) for x in links["s"]],
                  hovertemplate="%{source.label} → %{target.label}: %{value:,.1f} TIV<extra></extra>")))
    fig.update_layout(height=420, margin=dict(l=0, r=0, t=4, b=4), paper_bgcolor=BG, font=dict(color=INK, size=11, family=FONT))
    return fig


# ------------------------------------------------------------------ year by year
@st.cache_data
def year_table(isos, a, b):
    d = period_panel(isos, a, b).dropna(subset=["democracy_index"]).copy()
    d["Country"] = d["iso3"].map(NAMES)
    d["Regime"] = d["regime_label"].str.capitalize()
    d["Conflict"] = d["max_intensity"].map({2: "War", 1: "Minor", 0: "–"})
    d["k"] = d["iso3"].map({iso: k for k, iso in enumerate(isos)})
    d = d.sort_values(["k", "year"], ascending=[True, False])
    cols = (["Country"] if len(isos) > 1 else []) + ["year", "Regime", "democracy_index", "Conflict", "arms_imports_tiv", "arms_10"]
    return d[cols]


# ------------------------------------------------------------------ page body (re-run on its own while playing)
@st.fragment(run_every=SPEEDS[speed] if ss["playing"] else None)
def body():
    if ss.pop("cc_full_rerun", False):  # a click in the scatter moved the year: update the sidebar slider too
        st.rerun(scope="app")
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
    group = ss.get("cc_group_name")

    st.title(names[0] if single else group or f"Comparing {len(sel)} countries", anchor=False)
    st.caption(f"Regime, democracy index, armed conflict and arms imports, {a}–{b}. Change the year in the sidebar or press Play."
               if single else f"{len(sel)} countries side by side, {a}–{b}: " + ", ".join(names[:8]) + (f" and {len(sel) - 8} more." if len(sel) > 8 else "."))

    # loading bar for big selections (not while playing, where it would flicker every year)
    bar = st.progress(0, text=f"Loading {len(sel)} countries…") if len(sel) > 8 and not ss["playing"] else None

    def loaded(frac, text):
        if bar is not None:
            bar.progress(frac, text=f"Loading {len(sel)} countries: {text}…")

    no_data = [i for i in sel if d[d["iso3"] == i]["democracy_index"].notna().sum() == 0]
    if no_data:
        st.info(("No V-Dem data in this period for " + ", ".join(NAMES[i] for i in no_data) + ". ")
                + ("" if len(no_data) < len(sel) else "The state did not exist then. Try another period."
                   if single else "Try another period."), icon=":material/info:")
        if len(no_data) == len(sel):
            if bar is not None:
                bar.empty()
            return

    # ---- snapshot of the year
    now = panel[panel["iso3"].isin(isos) & (panel["year"] == y)].set_index("iso3")
    act = active_conflicts(isos, y)
    with st.container(border=True):
        st.markdown(f"**Snapshot of {y}**")
        if single:
            iso = sel[0]
            if iso in now.index and pd.notna(now.loc[iso, "democracy_index"]):
                r = now.loc[iso]
                names_now = act.get(iso, [])
                top = main_supplier(iso, y)
                m = st.columns(4)
                quiet = dict(delta_color="off", delta_arrow="off", border=False)
                m[0].metric("Democracy index", f"{r['democracy_index']:.2f}", str(r["regime_label"]).capitalize(), **quiet,
                            help="V-Dem electoral democracy index, 0 to 1, and the regime type of that year.")
                m[1].metric("Armed conflict", CONFLICT[int(r["max_intensity"])].replace("No armed conflict", "None"),
                            (f"{len(names_now)} active: " + ", ".join(names_now[:2]) + (" …" if len(names_now) > 2 else "")) if names_now else "UCDP, 25+ battle deaths",
                            **quiet)
                m[2].metric(f"Arms imports {y}", fmt_tiv(r["arms_imports_tiv"]), f"Mostly from {top}" if top else "No deliveries", **quiet)
                m[3].metric(f"Arms received {max(Y0, y - 9)}–{y}", fmt_tiv(r["arms_10"]), "10-year total, as in the scatter", **quiet)
            else:
                st.caption(f"No V-Dem data for {NAMES[iso]} in {y}.")
        else:
            snap = pd.DataFrame({"Country": names}, index=list(isos))
            snap["Regime"] = now["regime_label"].str.capitalize()
            snap["Democracy index"] = now["democracy_index"]
            snap["Armed conflict"] = [
                (CONFLICT[int(now.loc[i, "max_intensity"])] + (": " + ", ".join(act[i][:3]) + (" …" if len(act[i]) > 3 else "") if act.get(i) else ""))
                if i in now.index and pd.notna(now.loc[i, "max_intensity"]) else None for i in isos]
            snap["Arms imports"] = now["arms_imports_tiv"].round(0)
            snap["10 years"] = now["arms_10"].round(0)
            snap["Main supplier"] = [main_supplier(i, y) for i in isos]
            snap = snap.sort_values("Democracy index", ascending=False, na_position="last")
            st.dataframe(snap, hide_index=True, height=min(38 + 35 * len(snap), 320), alt=f"Snapshot of the selected countries in {y}",
                         placeholder="–",
                         column_config={
                             "Country": st.column_config.TextColumn("Country", pinned=True, width="medium"),
                             "Democracy index": st.column_config.ProgressColumn("Democracy index", format="%.2f", min_value=0, max_value=1),
                             "Armed conflict": st.column_config.TextColumn("Armed conflict", width="medium"),
                             "Arms imports": st.column_config.NumberColumn(f"Imports {y} (TIV)", format="localized"),
                             "10 years": st.column_config.NumberColumn("10-year total (TIV)", format="localized"),
                         })
            st.caption("Sorted by democracy index. Click a column header to sort by it.")

    loaded(.15, "scatter")
    # ---- scatter + (compare) democracy index / (single) one axis
    left, right = st.columns([1.35, 1], gap="medium")
    with left, st.container(border=True, height="stretch"):
        h_l, h_r = st.columns([2, 1], vertical_alignment="center")
        h_l.markdown("**Democracy vs. arms imports**")
        full = h_r.toggle("Full 0–1 scale", key="cc_full_scale", help="Show the whole democracy index and the whole period's arms range "
                          "instead of fitting the axes to the points on screen. The axes then stay put while playing.")
        if single:
            st.caption(f"The path of {names[0]} through time. Thin line: the whole period; strong part: the last 10 years.")
            fig = scatter_single(sel[0], a, b, y, full)
            follow = ()
        else:
            if ss.get("cc_follow_for") != isos:  # a new list: follow everyone up to 8, else the 6 largest importers
                ss["cc_follow_for"] = isos
                ss["cc_follow"] = list(isos) if len(isos) <= 8 else largest_importers(isos, a, b, 6)
            ss["cc_follow"] = [i for i in ss.get("cc_follow", []) if i in isos]
            follow = tuple(st.multiselect("Follow", list(isos), format_func=NAMES.get, key="cc_follow",
                                          placeholder="Pick countries to show their trails and labels",
                                          help="Followed countries get a 10-year trail and a label here, and stand out in the "
                                               "democracy and supplier charts. Clicking a faint bubble follows it too."))
            fig = scatter_compare(isos, a, b, y, follow, full)
        if fig is None:
            st.info(f"No V-Dem data in {y} for {'this country' if single else 'these countries'}. Move the year or pick another period.",
                    icon=":material/info:")
        else:
            st.plotly_chart(fig, key="cc_scatter", config=NO_BAR, on_select=scatter_clicked, selection_mode="points")
            if not single:
                have = set(now.index[now["democracy_index"].notna()])
                muted_list(f"Not in the scatter, no data for {y}", [i for i in isos if i not in have])
        st.caption(SC_GUIDE + ("" if single else " Trails: the previous 10 years of the followed countries; the others are faint.")
                   + " Big ringed dot: war year; small ringed dot: minor conflict; pale band: several conflict years in a row "
                   "(solid: war, dotted: minor). Click a dot to jump to its year."
                   + (" Left strip: no arms received." if fig is not None and fig.layout.shapes else ""))
    with right, st.container(border=True, height="stretch"):
        if single:
            st.markdown("**Democracy, conflict and arms on one axis**")
            st.caption("Line: democracy index (0–1). Bars: arms imports (TIV, right axis). Shading: war (darker) or minor conflict.")
            fig = one_axis(isos, a, b, False)
            year_line(fig, y, width=1.5)
            fig.update_layout(height=470)
            st.plotly_chart(fig, key="cc_axis1", config=NO_BAR)
        else:
            st.markdown("**Democracy index**")
            st.caption("V-Dem, 0 to 1. " + ("Click a name in the legend to hide it; double-click to show only that country."
                                            if len(isos) <= LEGEND_MAX else "Followed countries stand out; hover a line for its name."))
            fig = democracy_lines(isos, a, b, follow)
            year_line(fig, y, width=1.5)
            st.plotly_chart(fig, key="cc_demo", config=NO_BAR)

    # big selections: the per-country rows show only the followed countries
    rows_isos = isos if len(isos) <= ROWS_MAX else (follow or tuple(largest_importers(isos, a, b, 6)))
    rows_note = ("" if rows_isos == isos else
                 f" Showing the {len(rows_isos)} followed countries of {len(isos)}; add more under Follow above.")
    loaded(.35, "democracy, conflict and arms per country")
    # ---- one axis per country (compare)
    if not single:
        with st.container(border=True):
            h_l, h_r = st.columns([3, 1], vertical_alignment="center")
            h_l.markdown("**Democracy, conflict and arms on one axis**")
            same = h_r.toggle("Same arms scale for all", key="cc_same_scale",
                              help="Arms bars on one scale for every country instead of one scale per row.")
            st.caption("Line: democracy index (0–1, left axis). Bars: arms imports (TIV, right axis). Shading: war (darker) or minor conflict. "
                       "Hover a year for the values and the conflicts." + rows_note)
            fig = one_axis(rows_isos, a, b, same)
            year_line(fig, y, width=1.5)
            with scroll_box(fig.layout.height, 760):
                st.plotly_chart(fig, key="cc_axis", config=NO_BAR)

    loaded(.55, "regimes and conflicts")
    # ---- regime + conflicts (side by side for one country; stacked for a comparison, which has many more rows)
    if single:
        left, right = st.columns(2, gap="medium")
    else:
        left, right = st.container(), st.container()
    with left, st.container(border=True, height="stretch"):
        st.markdown("**Regime**")
        st.caption("V-Dem regime type per year.")
        fig = regime_chart(isos, a, b)
        if fig is None:
            st.info("No regime data in this period.", icon=":material/info:")
        else:
            year_line(fig, y, dates=True)
            with scroll_box(fig.layout.height, 640):
                st.plotly_chart(fig, key="cc_regime", config=NO_BAR)
    with right, st.container(border=True, height="stretch"):
        st.markdown("**Armed conflicts**")
        fig, none, height, n_with = conflict_chart(isos, a, b)
        if fig is None:
            st.caption("UCDP, 25+ battle deaths a year.")
            st.info(f"No armed conflict with 25 or more battle deaths in {a}–{b}"
                    + ("." if single else f" in any of the {len(isos)} countries."), icon=":material/info:")
        else:
            st.caption("UCDP. Light bars: war (1,000+ battle deaths a year); dark bars: minor conflict (25–999). One row per conflict, "
                       "named after the other side, with its conflict years in this period. Hover a bar for the sides and type.")
            year_line(fig, y)
            with scroll_box(height, 640):
                st.plotly_chart(fig, key="cc_conflict", config=NO_BAR)
            if not single:
                muted_list(f"No armed conflict in {a}–{b}", none)

    loaded(.75, "suppliers")
    # ---- suppliers
    left, right = st.columns([1.5, 1], gap="medium")
    with left, st.container(border=True, height="stretch"):
        st.markdown("**Arms imports by supplier**")
        st.caption("SIPRI TIV per year, coloured by the largest suppliers of " + ("this country" if single else "these countries") + " in the period." + rows_note)
        fig, none, height = supplier_bars(rows_isos, a, b)
        if fig is None:
            st.info(f"No major arms imports recorded in {a}–{b}.", icon=":material/info:")
        else:
            year_line(fig, y, width=1.2)
            with scroll_box(height, 760):
                st.plotly_chart(fig, key="cc_sup", config=NO_BAR)
            muted_list(f"No major arms imports in {a}–{b}", none)
            with_imports = [i for i in rows_isos if i not in none]
            with st.expander("Every supplier, year by year", icon=":material/list:"):
                who = with_imports[0] if len(with_imports) == 1 else st.selectbox(
                    "Country", with_imports, format_func=NAMES.get, key="cc_sup_country")
                rfig, table = supplier_rows(who, a, b)
                st.caption(f"{len(table)} suppliers of {NAMES[who]} in {a}–{b}. A bar for each run of years with deliveries; "
                           "the number after the name is the total TIV in the period.")
                year_line(rfig, y)
                with scroll_box(rfig.layout.height, 420):
                    st.plotly_chart(rfig, key="cc_sup_rows", config=NO_BAR)
                st.dataframe(table, hide_index=True, height=min(38 + 35 * len(table), 320), alt=f"All arms suppliers of {NAMES[who]} in the period",
                             column_config={"TIV": st.column_config.NumberColumn("TIV", format="localized"),
                                            "Share": st.column_config.ProgressColumn("Share", format="%.1f%%", min_value=0, max_value=100)})
    with right, st.container(border=True, height="stretch"):
        st.markdown("**Who supplied the arms**")
        fig, missing, demo = sup_dem_chart(isos, a, b, follow)
        if demo:
            st.warning("Placeholder numbers until notebook 08 is done.", icon=":material/science:")
        st.caption("How democratic the suppliers were, weighted by TIV: 0 = only autocratic suppliers, 1 = only democratic ones. "
                   "Gaps: years without imports.")
        if fig is None:
            st.info(f"No arms imports to weigh in {a}–{b}.", icon=":material/info:")
        else:
            year_line(fig, y, width=1.2)
            st.plotly_chart(fig, key="cc_supdem", config=NO_BAR)
            muted_list("No imports to weigh", missing)

    loaded(.9, "arms flows")
    # ---- arms flows
    with st.container(border=True):
        st.markdown(f"**Arms flows {'of ' + names[0] if single else 'of these countries'} in {y}**")
        f = country_flows(isos, y)
        if f.empty:
            st.info(f"No deliveries to or from {'this country' if single else 'these countries'} in {y}. Move the year to see others.",
                    icon=":material/info:")
        else:
            imp, exp = f.loc[f["direction"] == "Import", "tiv"].sum(), f.loc[f["direction"] == "Export", "tiv"].sum()
            st.caption(f"Deliveries to or from {'it' if single else 'the selected countries'}: {imp:,.0f} TIV received, {exp:,.0f} TIV delivered. "
                       "Map: arc width = TIV, colour = supplier, orange dots = the selected countries. Right: who delivered to whom.")
            cmap = supplier_colours(isos, a, b)
            map_col, sk_col = st.columns([1.5, 1], gap="medium")
            with map_col:
                n = 80
                st.pydeck_chart(flows_deck(f.head(n), cmap), height=420, key="cc_flows")
                if len(f) > n:
                    st.badge(f"Largest {n} of {len(f)} deliveries drawn", color="gray")
            with sk_col:
                st.plotly_chart(flows_sankey(f, cmap), key="cc_sankey", config=NO_BAR)

    if bar is not None:
        bar.empty()
    # ---- year by year
    with st.expander("Year-by-year table" + ("" if single else "s"), icon=":material/table:"):
        t = year_table(isos, a, b)
        if t.empty:
            st.info("No data in this period.", icon=":material/info:")
        else:
            st.dataframe(t, hide_index=True, height=420, alt="Year-by-year numbers of the selected countries",
                         column_config={"year": st.column_config.NumberColumn("Year", format="%d"),
                                        "democracy_index": st.column_config.NumberColumn("Index", format="%.2f"),
                                        "arms_imports_tiv": st.column_config.NumberColumn("Imports (TIV)", format="%.1f"),
                                        "arms_10": st.column_config.NumberColumn("10-year total (TIV)", format="localized")})


body()
