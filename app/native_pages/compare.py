"""Countries & compare, built only with Streamlit (no custom HTML).

One country or a group side by side: a snapshot of the chosen year, democracy vs. arms imports as a
scatter with 10-year trails, democracy, conflict and arms on one shared year axis, regime periods,
the democracy index, armed conflicts by name, imports by supplier (every supplier SIPRI names), how
democratic the suppliers were, the arms flows to and from these countries and the year-by-year
numbers. The countries are chosen in the sidebar; the year bar (Play, speed, year, period) sits at the top of the page,
inside the page fragment, so Play and the slider only rerun the page body.

Every chart that shows the year is an Altair (Vega-Lite) chart with the year as its own rule layer: when the year
changes, Vega redraws the marks in place instead of Streamlit mounting a new chart (Plotly charts blank for a moment,
which flickered on every Play step).
"""

import json

import altair as alt
import numpy as np
import pandas as pd
import pydeck as pdk
import streamlit as st

import native_data as nd

Y0, Y1 = 1950, 2025
INK, INK2, MUTED, LINE = "#f0efec", "#c3c2b7", "#959086", "#2c2c2a"
FONT = "IBM Plex Sans"
SPEEDS = {"0.5×": 2.4, "1×": 1.2, "2×": 0.6}  # seconds per year
PERIODS = {"1950–2025": (1950, 2025), "Cold War": (1950, 1991), "Since 1992": (1992, 2025)}
CONFLICT = {2: "War", 1: "Minor conflict", 0: "No armed conflict"}
CONFLICT_COLOURS = {"War": "#ece8e0", "Minor conflict": "#6a655d"}  # as in the HTML version (dark theme)
UCDP_TYPE = {1: "Extrasystemic", 2: "Interstate", 3: "Intrastate", 4: "Internationalised intrastate"}
EXTRA_SUP = ["#2bb5c0", "#a3b54a", "#e07ab0", "#b98a68", "#a39d92", "#6f6a62"]  # suppliers without a fixed colour
UNKNOWN = "unknown supplier(s)"
ARMS = "#e48461"  # arms-import bars in the one-axis chart
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
ss.setdefault("cc_period", "1950–2025")
ss.setdefault("cc_speed", "1×")
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
    ss["cc_full_rerun"] = True  # the Play timer of the page fragment is set on a full run


def full_rerun():
    """The speed sets the Play timer of the page fragment, which only a full run changes."""
    ss["cc_full_rerun"] = True


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
        pts = ss["cc_scatter"]["selection"]["pick"]
    except (KeyError, TypeError):
        return
    if not pts or "year" not in pts[0]:
        return
    year, iso = pts[0]["year"], pts[0].get("iso3")
    p0, p1 = period_bounds()
    ss["year"] = min(max(int(year), p0), p1)
    ss["cc_year_slider"] = ss["year"]
    if ss["playing"]:
        ss["playing"] = False
        ss["cc_full_rerun"] = True  # stops the Play timer, which only a full run changes
    if iso in NAMES and len(ss.get("countries") or []) > 1 and iso not in (ss.get("cc_follow") or []):
        ss["cc_follow"] = list(ss.get("cc_follow") or []) + [iso]


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
    st.caption("SIPRI trend-indicator values (TIV, millions) measure military capability transferred, not money. "
               "Some states appear under a successor's code, as in V-Dem (Russia for the Soviet Union before 1991).")

speed = ss["cc_speed"] if ss.get("cc_speed") in SPEEDS else "1×"

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
def vl_finish(chart):
    """Look of every Altair chart on this page (as the scatter): transparent, IBM Plex, muted axes and legends."""
    chart = chart.properties(padding={"left": 8, "right": 4, "top": 4, "bottom": 4})  # room for the left axis labels
    return (chart.configure_view(stroke=None).configure(background="transparent", font=FONT + ", sans-serif")
            .configure_axis(gridColor=LINE, domainColor=LINE, tickColor=LINE, labelColor=MUTED, titleColor=MUTED,
                            titleFontWeight="normal", labelFontSize=11, titleFontSize=12)
            .configure_legend(labelColor=INK2, titleColor=MUTED, labelFontSize=11, labelLimit=170)
            .configure_title(color=INK, fontSize=12, fontWeight="normal", anchor="start", offset=4))


def year_ticks(a, b, step=None):
    step = step or (10 if b - a > 20 else 5)
    return [v for v in range(a - a % step + (step if a % step else 0), b + 1, step)]


def yr_x(field, a, b, axis=True, top=False, step=None, pad=.5):
    """The year axis (quantitative, so a rule at a year lands in the middle of that year's bar)."""
    ax = (alt.Axis(format="d", title=None, values=year_ticks(a, b, step), orient="top" if top else "bottom", labelFlush=False)
          if axis else alt.Axis(format="d", title=None, values=year_ticks(a, b, step), labels=False, ticks=False, domain=False))
    return alt.X(f"{field}:Q", scale=alt.Scale(domain=[a - pad, b + pad], nice=False, zero=False), axis=ax)


YR = "yr"  # Vega parameter holding the year


def year_rule(width=1.5):
    """The year as its own layer, at the parameter "yr": a chart is built once, and a new year only changes that
    parameter (`at_year`), so Vega redraws the marks in place and the chart does not flicker."""
    return alt.Chart().mark_rule(color=INK, strokeWidth=width).encode(x=alt.datum(alt.expr(YR), type="quantitative"))


def at_year(chart, y):
    """A copy of a (cached) chart with the year parameter set; the cached chart itself is not changed."""
    c = chart.copy(deep=False)
    c.params = ([] if c.params is alt.Undefined else list(c.params)) + [alt.VariableParameter(name=YR, value=int(y))]
    return c


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


# The scatter is an Altair (Vega-Lite) chart, not Plotly: when the year changes, Streamlit swaps Vega's drawing in
# one step, while a Plotly chart is rebuilt from scratch (it blanks for a moment, which flickers while playing).
SC_H = 440
SIZE = {2: 120, 1: 60, 0: 26}  # dot area (px²) per conflict intensity: war, minor, none
RING = {2: 2.4, 1: 1.2, 0: 0.0}  # outline width per conflict intensity
WRAP = {"war": ("rgba(236,232,224,0.2)", 8, [1, 0]), "minor": ("rgba(236,232,224,0.16)", 6, [2, 4])}


def sc_prep(d, ax):
    """Plot columns: x (arms on the log axis, 'none' strip for zero), and readable tooltip fields."""
    d = d.copy()
    d["x"] = np.where(d["arms_10"] > 0, d["arms_10"], ax["none_x"])
    d["Country"] = d["country_name"]
    d["Regime"] = d["regime_label"].str.capitalize()
    d["Conflict"] = d["max_intensity"].map(CONFLICT)
    d["from"] = (d["year"] - 9).clip(lower=Y0)
    d["intensity"] = d["max_intensity"].fillna(0).astype(int)
    return d


def sc_axes(ax):
    lo, hi = ax["range"]
    label = " : ".join(f"abs(datum.value - {float(v)!r}) < {float(v) * 1e-6!r} ? '{t}'" for v, t in zip(ax["tickvals"], ax["ticktext"])) + " : ''"
    x = alt.X("x:Q", scale=alt.Scale(type="log", domain=[10 ** lo, 10 ** hi], clamp=True, nice=False),
              axis=alt.Axis(values=list(ax["tickvals"]), labelExpr=label, title="Arms received in the previous 10 years (TIV, log scale)",
                            titleColor=MUTED, titleFontWeight="normal", grid=True, gridColor=LINE, labelColor=INK2))
    y = alt.Y("democracy_index:Q", scale=alt.Scale(domain=list(ax["y"]), clamp=True, nice=False, zero=False),
              axis=alt.Axis(title="Democracy index", titleColor=MUTED, titleFontWeight="normal", gridColor=LINE, labelColor=INK2,
                            tickCount=6))
    return x, y


TT = [alt.Tooltip("Country:N"), alt.Tooltip("year:O", title="Year"), alt.Tooltip("democracy_index:Q", title="Democracy index", format=".2f"),
      alt.Tooltip("Regime:N"), alt.Tooltip("arms_10:Q", title="Arms received in 10 years (TIV)", format=",.0f"),
      alt.Tooltip("arms_imports_tiv:Q", title="In that year alone (TIV)", format=",.0f"), alt.Tooltip("Conflict:N", title="Armed conflict")]
PICK = alt.selection_point(name="pick", fields=["year", "iso3"], on="click", empty=False)


def sc_strip(ax):
    """Grey strip left of the log axis for points without arms received."""
    if not ax["any_zero"]:
        return []
    s = pd.DataFrame({"x": [ax["strip"][0]], "x2": [ax["strip"][1]]})
    return [alt.Chart(s).mark_rect(color=LINE, opacity=.6).encode(x=alt.X("x:Q", scale=alt.Scale(type="log")), x2="x2:Q")]


def sc_wraps(d, x, y):
    """Bands along a path wherever two consecutive years both had an armed conflict: solid when both were war,
    dotted otherwise (as in the HTML version)."""
    rows = []
    for iso, t in d.sort_values("year").groupby("iso3"):
        prev = None
        for xv, yv, yr, c in t[["x", "democracy_index", "year", "intensity"]].itertuples(index=False):
            if prev is not None and prev[2] == yr - 1 and prev[3] and c:
                kind = "war" if prev[3] == 2 and c == 2 else "minor"
                seg = f"{iso}{yr}"
                rows += [dict(x=prev[0], democracy_index=prev[1], seg=seg, kind=kind, k=0), dict(x=xv, democracy_index=yv, seg=seg, kind=kind, k=1)]
            prev = (xv, yv, yr, c)
    w = pd.DataFrame(rows, columns=["x", "democracy_index", "seg", "kind", "k"])
    out = []
    for kind, (colour, width, dash) in WRAP.items():
        out.append(alt.Chart(w[w["kind"] == kind]).mark_line(color=colour, strokeWidth=width, strokeDash=dash, strokeCap="round")
                   .encode(x, y, detail="seg:N", order="k:Q"))
    return out


def sc_finish(layers):
    return (alt.layer(*layers).properties(height=SC_H)
            .configure_view(stroke=None).configure(background="transparent", font=FONT + ", sans-serif"))


def label_sides(pts, ax, width_px=480, height_px=370):
    """Greedy labels: biggest importers first, right of the bubble (or left), skipped when they would overlap another
    label or bubble. Returns {iso: 'right' | 'left'}; positions are estimated in pixels of the plot area."""
    x0, x1 = ax["range"]
    y0, y1 = ax["y"]
    to_px = lambda x, yv: ((np.log10(x) - x0) / (x1 - x0) * width_px, (yv - y0) / (y1 - y0) * height_px)
    placed = [(bx - 8, by - 8, bx + 8, by + 8) for bx, by in (to_px(r.x, r.democracy_index) for r in pts.itertuples())]
    sides = {}
    for p in pts.sort_values("arms_10", ascending=False).itertuples():
        px_, py_ = to_px(p.x, p.democracy_index)
        w, h = 7.6 * len(p.label) + 8, 18
        for side in ([1, -1] if px_ < width_px - w - 14 else [-1, 1]):
            box = (px_ + 12, py_ - h / 2, px_ + 12 + w, py_ + h / 2) if side == 1 else (px_ - 12 - w, py_ - h / 2, px_ - 12, py_ + h / 2)
            if box[0] < 0 or box[2] > width_px:
                continue
            if not any(box[0] < q[2] and box[2] > q[0] and box[1] < q[3] and box[3] > q[1] for q in placed):
                placed.append(box)
                sides[p.iso3] = "right" if side == 1 else "left"
                break
    return sides


@st.cache_data
def scatter_single(iso, a, b, y, full):
    d = period_panel((iso,), a, b).dropna(subset=["democracy_index"])
    if d.empty:
        return None
    ax = scatter_axis(d, d, full)
    d = sc_prep(d, ax).sort_values("year")
    x, yy = sc_axes(ax)
    c = COL[iso]
    d["size"], d["ring"] = d["intensity"].map(SIZE), d["intensity"].map(RING)
    last = d[d["year"].between(y - 10, y)]
    dec = d[(d["year"] % 10 == 0) & (d["year"] != y)]
    now = d[d["year"] == y]
    layers = sc_strip(ax) + sc_wraps(d, x, yy) + [
        alt.Chart(d).mark_line(color=c, strokeWidth=1.2, opacity=.45).encode(x, yy, order="year:Q"),
        alt.Chart(last).mark_line(color=c, strokeWidth=2.8).encode(x, yy, order="year:Q"),
        alt.Chart(d).mark_point(filled=True, color=c, opacity=.9, stroke="#111110", cursor="pointer")
        .encode(x, yy, size=alt.Size("size:Q", scale=None), strokeWidth=alt.StrokeWidth("ring:Q", scale=None), tooltip=TT)
        .add_params(PICK),
        alt.Chart(dec).mark_text(align="left", dx=6, dy=-8, color=MUTED, fontSize=11).encode(x, yy, text="year:N"),
        alt.Chart(now).mark_point(filled=True, color=c, size=330, stroke=INK,
                                  strokeWidth=max(1.5, RING[int(now["intensity"].iloc[0])]) if len(now) else 1.5).encode(x, yy),
        alt.Chart(now).mark_text(dy=-18, color=INK, fontSize=13, fontWeight=600).encode(x, yy, text="year:N"),
    ]
    return sc_finish(layers), ax["any_zero"]


@st.cache_data
def scatter_compare(isos, a, b, y, follow, full):
    d = period_panel(isos, max(Y0, y - 10), y).dropna(subset=["democracy_index"])
    if d.empty or not (d["year"] == y).any():
        return None
    focus = set(follow)
    visible = d[d["iso3"].isin(focus) | (d["year"] == y)]
    ax = scatter_axis(visible, period_panel(isos, a, b).dropna(subset=["democracy_index"]), full)
    d = sc_prep(d, ax)
    x, yy = sc_axes(ax)
    colour = alt.Color("iso3:N", scale=alt.Scale(domain=list(isos), range=[COL[i] for i in isos]), legend=None)
    dash = alt.StrokeDash("dash:N", scale=alt.Scale(domain=["solid", "dot"], range=[[1, 0], [2, 3]]), legend=None)
    d["dash"] = d["iso3"].map(DASH)
    trail = d[d["iso3"].isin(focus)].sort_values(["iso3", "year"])
    now = d[d["year"] == y]
    # one layer for every clickable point (trail dots, then faint bubbles, then followed bubbles on top), so the
    # click selection lives on a single layer
    pts = pd.concat([
        trail[trail["year"] < y].assign(size=lambda f: f["intensity"].map(SIZE), ring=lambda f: f["intensity"].map(RING), op=.8, z=0),
        now.assign(size=250, ring=lambda f: f["intensity"].map(RING) * 1.3, op=np.where(now["iso3"].isin(focus), 1.0, .2),
                   z=np.where(now["iso3"].isin(focus), 2, 1)),
    ]).sort_values(["z", "iso3", "year"])
    lab = now[now["iso3"].isin(focus)].assign(label=lambda f: f["country_name"].map(short_name))
    sides = label_sides(lab, ax)
    lab = lab.assign(side=lab["iso3"].map(sides)).dropna(subset=["side"])
    layers = sc_strip(ax) + sc_wraps(trail, x, yy) + [
        alt.Chart(trail).mark_line(strokeWidth=2, opacity=.8).encode(x, yy, colour, dash, detail="iso3:N", order="year:Q"),
        alt.Chart(pts).mark_point(filled=True, stroke="#111110", cursor="pointer")
        .encode(x, yy, colour, size=alt.Size("size:Q", scale=None), strokeWidth=alt.StrokeWidth("ring:Q", scale=None),
                opacity=alt.Opacity("op:Q", scale=None), order="z:Q", tooltip=TT)
        .add_params(PICK),
        alt.Chart(lab[lab["side"] == "right"]).mark_text(align="left", dx=12, color=INK, fontSize=12).encode(x, yy, text="label:N"),
        alt.Chart(lab[lab["side"] == "left"]).mark_text(align="right", dx=-12, color=INK, fontSize=12).encode(x, yy, text="label:N"),
    ]
    return sc_finish(layers), ax["any_zero"]


# ------------------------------------------------------------------ timelines
# Data is cached per selection and period (st.cache_data). The finished charts are cached too (st.cache_resource, so
# they are not copied on every run) without the year: the year rule reads the parameter "yr", which `at_year` adds on
# every run. Building and configuring Altair charts is the slow part, so Play only pays for the year.
CHARTS = dict(max_entries=96)
NOT_IN_LEGEND = .06  # opacity of a line whose name is not picked in a legend


def style(isos):
    """Colours and dashes of these countries in the current selection (part of the chart cache keys)."""
    return tuple((COL[i], DASH[i]) for i in isos)


@st.cache_data
def one_axis_data(isos, a, b):
    """Per country and year: democracy index, arms imports and hover texts; conflict runs as shading spans."""
    d = period_panel(isos, a, b)
    conf = load_conflicts()
    parts = []
    for iso in isos:
        t = d[d["iso3"] == iso][["iso3", "year", "democracy_index", "arms_imports_tiv", "regime_label", "max_intensity"]].copy()
        c = conf[conf["iso3"] == iso]
        names = [", ".join(dict.fromkeys(c.loc[(c["start"] <= yr) & (c["end"] >= yr), "name"])) for yr in t["year"]]
        t["Democracy index"] = [f"{v:.2f} ({reg})" if pd.notna(v) else "no data" for v, reg in zip(t["democracy_index"], t["regime_label"])]
        t["Conflict"] = [(CONFLICT[int(m)] + (f" ({nm[:60]})" if nm else "")) if pd.notna(m) else "no data"
                         for m, nm in zip(t["max_intensity"], names)]
        t["Arms imports"] = t["arms_imports_tiv"].map(fmt_tiv)
        parts.append(t)
    t = pd.concat(parts)
    t = t.assign(h0=t["year"] - .5, h1=t["year"] + .5, b0=t["year"] - .425, b1=t["year"] + .425).drop(columns=["regime_label"])
    cr = nd.conflict_runs()
    cr = cr[cr["iso3"].isin(isos) & (cr["end"] >= a) & (cr["start"] <= b)]
    shade = pd.DataFrame({"iso3": cr["iso3"], "x0": cr["start"].clip(lower=a) - .5, "x1": cr["end"].clip(upper=b) + .5,
                          "op": np.where(cr["intensity"] == 2, .2, .07)})
    return t, shade


ONE_TT = [alt.Tooltip("year:Q", title="Year", format="d"), alt.Tooltip("Democracy index:N"), alt.Tooltip("Arms imports:N"),
          alt.Tooltip("Conflict:N")]


def one_axis_heights(n, single_h=None):
    """Chart height of a row (Streamlit fits the whole chart, title and axis included, into it; the last row is
    taller by the year labels) and the height of all rows together, in pixels."""
    h = single_h or (104 if n <= 6 else 78)
    return h, (h + 16) * n + 24


@st.cache_resource(**CHARTS)
def one_axis(isos, a, b, same_scale, single_h, style_):
    """Per country: democracy index line (0–1, left axis), conflict years shaded (war darker), arms imports as bars on
    a second axis (right). One chart per country (stacked rows; Vega-Lite's vconcat cannot stretch to the card width),
    year labels on the last row only. Returns [(iso, chart)]."""
    t, shade = one_axis_data(isos, a, b)
    n = len(isos)
    h, _ = one_axis_heights(n, single_h)
    vmax = max(1.0, t["arms_imports_tiv"].fillna(0).max())
    out = []
    for k, iso in enumerate(isos):
        last = k == n - 1
        tt, sh = t[t["iso3"] == iso], shade[shade["iso3"] == iso]
        top = vmax if same_scale else max(1.0, tt["arms_imports_tiv"].fillna(0).max() if len(tt) else 1.0)
        layers = [
            alt.Chart(sh).mark_rect(color=INK).encode(yr_x("x0", a, b, last), x2="x1:Q", opacity=alt.Opacity("op:Q", scale=None)),
            alt.Chart(tt).mark_rect(color=ARMS, opacity=.55).encode(
                yr_x("b0", a, b, last), x2="b1:Q", y2=alt.datum(0),
                y=alt.Y("arms_imports_tiv:Q", scale=alt.Scale(domain=[0, top * 1.08], nice=False),
                        axis=alt.Axis(orient="right", title=None, tickCount=3, grid=False, format=",.0f", minExtent=34))),
            alt.Chart(tt).mark_line(color=COL[iso], strokeWidth=2.2, invalid="break-paths-filter-domains").encode(
                yr_x("year", a, b, last),
                y=alt.Y("democracy_index:Q", scale=alt.Scale(domain=[0, 1], nice=False),
                        axis=alt.Axis(values=[0, .5, 1], title=None, minExtent=24))),
            alt.Chart(tt).mark_rect(opacity=0).encode(yr_x("h0", a, b, last), x2="h1:Q", tooltip=ONE_TT),  # hover: the whole year
            year_rule(),
        ]
        row = alt.layer(*layers).resolve_scale(y="independent").properties(height=h + (22 if last and n > 1 else 0))
        out.append((iso, vl_finish(row.properties(title=NAMES[iso]) if n > 1 else row)))
    return out


@st.cache_data
def regime_data(isos, a, b):
    s = nd.regime_spans()
    s = s[s["iso3"].isin(isos) & (s["end"] >= a) & (s["start"] <= b)].copy()
    if s.empty:
        return None, []
    s["x0"] = s["start"].clip(lower=a) - .5
    s["x1"] = s["end"].clip(upper=b) + .5
    s["Country"] = s["iso3"].map(NAMES).map(short_name)
    s["Regime"] = s["regime_label"].str.capitalize()
    s["Years"] = s["start"].astype(str) + "–" + s["end"].astype(str)
    order = list(dict.fromkeys(short_name(NAMES[i]) for i in isos))
    return s[["Country", "Regime", "Years", "x0", "x1"]], order


@st.cache_resource(**CHARTS)
def regime_chart(isos, a, b):
    s, order = regime_data(isos, a, b)
    if s is None:
        return None, 0
    regs = [r.capitalize() for r in nd.REGIMES]
    bars = alt.Chart(s).mark_bar(height=alt.RelativeBandSize(.75)).encode(
        yr_x("x0", a, b), x2="x1:Q",
        y=alt.Y("Country:N", sort=order, scale=alt.Scale(domain=order),
                axis=alt.Axis(title=None, labelColor=INK2, labelLimit=160, ticks=False, domain=False, labelFontSize=12)),
        color=alt.Color("Regime:N", scale=alt.Scale(domain=regs, range=[nd.REGIME_COLOURS[r] for r in nd.REGIMES]),
                        legend=alt.Legend(orient="top", direction="horizontal", title=None, columns=4 if len(isos) > 1 else 2,
                                          symbolType="square")),
        tooltip=["Country:N", "Regime:N", "Years:N"])
    h = 26 * len(order) + 64  # the whole chart: rows, legend and year axis
    return vl_finish(alt.layer(bars, year_rule()).properties(height=h)), h + 10


@st.cache_data
def conflict_data(isos, a, b):
    """One row per conflict (named as in the HTML version), bars for its war and minor years in the period."""
    c = load_conflicts()
    c = c[c["iso3"].isin(isos) & (c["end"] >= a) & (c["start"] <= b)].copy()
    if c.empty:
        return None, [], list(isos), 0
    c["s"], c["e"] = c["start"].clip(lower=a), c["end"].clip(upper=b)
    c["years"] = c["e"] - c["s"] + 1
    order = {iso: k for k, iso in enumerate(isos)}
    first = c.groupby(["iso3", "name"])["s"].transform("min")
    c = c.assign(k=c["iso3"].map(order), first=first).sort_values(["k", "first", "name", "s"])
    tot = c.groupby(["iso3", "name"])["years"].sum()
    c["row"] = [(f"{short_name(NAMES[iso])} · " if len(isos) > 1 else "") + f"{short_name(nm, 24)} · {tot[(iso, nm)]} yr"
                for iso, nm in zip(c["iso3"], c["name"])]
    c["x0"], c["x1"] = c["s"] - .5, c["e"] + .5
    c["kind"] = c["intensity"].map({2: "War", 1: "Minor conflict"})
    c["Country"] = c["iso3"].map(NAMES)
    c["Type"] = c["type"] + np.where(c["territory"] != "", " · territory: " + c["territory"], " · over government")
    c["Years"] = c["start"].astype(str) + np.where(c["end"] > c["start"], "–" + c["end"].astype(str), "")
    c["Intensity"] = np.where(c["intensity"] == 2, "War, 1000+ battle deaths a year", "Minor, 25–999 battle deaths a year")
    rows = list(dict.fromkeys(c["row"]))
    out = c[["row", "x0", "x1", "kind", "name", "Country", "sides", "Type", "Years", "Intensity"]]
    have = set(c["iso3"].unique())
    return out, rows, [i for i in isos if i not in have], len(have)


def range_rows(df, rows, a, b, colour, tooltip):
    """Horizontal bars from x0 to x1 on the rows `rows` (in this order), year axis on top, and the year rule."""
    step = 20 if b - a > 50 else 10
    bars = alt.Chart(df).mark_bar(height=alt.RelativeBandSize(.62)).encode(
        yr_x("x0", a, b, top=True, step=step), x2="x1:Q",
        y=alt.Y("row:N", sort=rows, scale=alt.Scale(domain=rows),
                axis=alt.Axis(title=None, labelColor=INK2, labelLimit=330, ticks=False, domain=False)),
        color=colour, tooltip=tooltip)
    h = 25 * len(rows) + 30  # the whole chart: rows and year axis
    return vl_finish(alt.layer(bars, year_rule(1.2)).properties(height=h)), h + 10


@st.cache_resource(**CHARTS)
def conflict_chart(isos, a, b):
    c, rows, none, n_with = conflict_data(isos, a, b)
    if c is None:
        return None, none, 0, 0
    colour = alt.Color("kind:N", scale=alt.Scale(domain=list(CONFLICT_COLOURS), range=list(CONFLICT_COLOURS.values())), legend=None)
    tt = [alt.Tooltip("name:N", title="Conflict"), alt.Tooltip("Country:N"), alt.Tooltip("sides:N", title="Sides"),
          alt.Tooltip("Type:N"), alt.Tooltip("Years:N"), alt.Tooltip("Intensity:N")]
    chart, h = range_rows(c, rows, a, b, colour, tt)
    return chart, none, h, n_with


def value_frame(isos, a, b):
    """Supplier democracy per country and every year of the period (gaps = years without imports, NaN)."""
    s, _ = nd.load_sup_dem()
    s = s[s["iso3"].isin(isos) & s["year"].between(a, b)]
    parts = []
    for iso in isos:
        t = s[s["iso3"] == iso].sort_values("year").set_index("year").reindex(range(a, b + 1))
        if t["sup_dem"].notna().sum() == 0:
            continue
        t["iso3"] = iso
        t["alone"] = t["sup_dem"].notna() & t["sup_dem"].shift(1).isna() & t["sup_dem"].shift(-1).isna()
        parts.append(t.reset_index()[["iso3", "year", "sup_dem", "share_dem", "alone"]])
    return pd.concat(parts) if parts else pd.DataFrame(columns=["iso3", "year", "sup_dem", "share_dem", "alone"])


@st.cache_data
def lines_data(isos, a, b, follow, value):
    """Long table for a line per country (followed ones drawn on top and stronger) and a wide one for the hover
    (one column per country, c0, c1, …)."""
    d = period_panel(isos, a, b)[["iso3", "year", value]] if value == "democracy_index" else value_frame(isos, a, b)
    focus = set(follow) or set(isos)
    d = d.assign(Country=d["iso3"].map(NAMES).map(short_name), Name=d["iso3"].map(NAMES), dash=d["iso3"].map(DASH),
                 on=d["iso3"].isin(focus))
    d["sw"] = np.where(d["on"], 2.0, 1.0)
    d["op"] = np.where(d["on"], 1.0, .22)
    wide = d.pivot_table(index="year", columns="iso3", values=value, dropna=False).reindex(columns=list(isos))
    wide.columns = [f"c{k}" for k in range(len(isos))]
    wide = wide.reset_index()
    wide = wide.assign(h0=wide["year"] - .5, h1=wide["year"] + .5)
    return d, wide


@st.cache_resource(**CHARTS)
def lines_chart(isos, a, b, follow, value, y_title, height, y_dom, y_vals, style_):
    """A line per country; with up to LEGEND_MAX countries a legend (click a name to pick it, shift-click for more,
    double-click the chart to show all again); hover shows every country's value of that year up to 12 countries."""
    d, wide = lines_data(isos, a, b, follow, value)
    have = set(d["iso3"].unique())
    present = [i for i in isos if i in have]
    labels = [short_name(NAMES[i]) for i in present]
    legend = len(isos) <= LEGEND_MAX
    pick = alt.selection_point(name="pick_line", fields=["Country"], bind="legend")
    colour = alt.Color("Country:N", scale=alt.Scale(domain=labels, range=[COL[i] for i in present]),
                       legend=alt.Legend(title=None, symbolType="stroke", symbolStrokeWidth=2.5, symbolOpacity=1) if legend else None)
    dash = alt.StrokeDash("dash:N", scale=alt.Scale(domain=["solid", "dot"], range=[[1, 0], [2, 3]]), legend=None)
    op = alt.condition(pick, alt.Opacity("op:Q", scale=None), alt.value(NOT_IN_LEGEND)) if legend else alt.Opacity("op:Q", scale=None)
    x = yr_x("year", a, b, pad=0)
    yy = alt.Y(f"{value}:Q", scale=alt.Scale(domain=list(y_dom), nice=False),
               axis=alt.Axis(title=y_title, values=list(y_vals)) if y_vals else alt.Axis(title=y_title))
    enc = dict(x=x, y=yy, color=colour, strokeDash=dash, strokeWidth=alt.StrokeWidth("sw:Q", scale=None), opacity=op, detail="iso3:N")
    if len(isos) > 12:  # many countries: hover a line for its name (an extra layer of hover points would be slow)
        enc["tooltip"] = [alt.Tooltip("Name:N", title="Country")]
    layers = [alt.Chart(d[~d["on"]]).mark_line(invalid="break-paths-filter-domains").encode(**enc),
              alt.Chart(d[d["on"]]).mark_line(invalid="break-paths-filter-domains").encode(**enc)]
    if legend:
        layers[1] = layers[1].add_params(pick)
    if "alone" in d:  # single years between gaps: a dot, or they would not show
        layers.append(alt.Chart(d[d["alone"].astype(bool)]).mark_point(filled=True, size=22).encode(x=x, y=yy, color=colour, opacity=op))
    if len(isos) <= 12:  # hover a year: all countries' values
        tt = [alt.Tooltip("year:Q", title="Year", format="d")] + [
            alt.Tooltip(f"c{k}:Q", title=NAMES[iso], format=".2f") for k, iso in enumerate(isos) if iso in have]
        layers.append(alt.Chart(wide).mark_rect(opacity=0).encode(yr_x("h0", a, b, pad=0), x2="h1:Q", tooltip=tt))
    layers.append(year_rule())
    return vl_finish(alt.layer(*layers).properties(height=height))


def democracy_lines(isos, a, b, follow):
    return lines_chart(isos, a, b, follow, "democracy_index", "Democracy index", 440, (0, 1), None, style(isos))


@st.cache_data
def supplier_bars_data(isos, a, b):
    """Arms imports per country, year and supplier (largest suppliers by name, the rest as "Other suppliers"),
    stacked in pandas so each bar piece is a plain rectangle."""
    f = supplier_data(isos, a, b)
    tot = f.groupby("recipient_iso3")["tiv"].sum()
    has = [i for i in isos if tot.get(i, 0) > 0]
    if not has:
        return None, {}, has
    cmap = supplier_colours(isos, a, b)
    order = list(cmap) + ["Other suppliers"]
    f = f[f["recipient_iso3"].isin(has)].assign(Supplier=lambda x: x["supplier"].where(x["supplier"].isin(cmap.keys()), "Other suppliers"))
    g = f.groupby(["recipient_iso3", "year", "Supplier"], as_index=False)["tiv"].sum()
    g["k"] = g["Supplier"].map({s: k for k, s in enumerate(order)})
    g = g.sort_values(["recipient_iso3", "year", "k"])
    g["y1"] = g.groupby(["recipient_iso3", "year"])["tiv"].cumsum()
    g["y0"] = g["y1"] - g["tiv"]
    g["x0"], g["x1"] = g["year"] - .45, g["year"] + .45
    return g, cmap, has


def supplier_colour_scale(cmap):
    return alt.Scale(domain=list(cmap) + ["Other suppliers"], range=list(cmap.values()) + [nd.OTHER_COLOUR])


@st.cache_resource(**CHARTS)
def supplier_charts(isos, a, b, height):
    """The supplier colours as a legend of its own, then one chart per country (stacked bars by supplier)."""
    g, cmap, has = supplier_bars_data(isos, a, b)
    if g is None:
        return None, []
    leg = pd.DataFrame({"Supplier": list(cmap) + ["Other suppliers"]})
    legend = vl_finish(alt.Chart(leg).mark_square(opacity=0).encode(
        color=alt.Color("Supplier:N", scale=supplier_colour_scale(cmap),
                        legend=alt.Legend(orient="top", direction="horizontal", columns=3, title=None, symbolType="square",
                                          symbolOpacity=1, labelLimit=150, columnPadding=14)))
                       .properties(height=22 * -(-(len(cmap) + 1) // 3) + 24))  # the legend's rows; the chart has no plot
    charts = []
    for iso in has:
        bars = alt.Chart(g[g["recipient_iso3"] == iso]).mark_rect().encode(
            yr_x("x0", a, b, step=20 if b - a > 50 else 10), x2="x1:Q",
            y=alt.Y("y0:Q", title=None, axis=alt.Axis(tickCount=3, format=",.0f", minExtent=30)), y2="y1:Q",
            color=alt.Color("Supplier:N", scale=supplier_colour_scale(cmap), legend=None),
            tooltip=[alt.Tooltip("Supplier:N"), alt.Tooltip("year:Q", title="Year", format="d"),
                     alt.Tooltip("tiv:Q", title="TIV", format=",.1f")])
        ch = alt.layer(bars, year_rule(1.2)).properties(height=height)
        charts.append((iso, vl_finish(ch.properties(title=NAMES[iso]) if len(has) > 1 else ch)))
    return legend, charts


@st.cache_data
def supplier_rows_data(iso, a, b):
    """Every supplier of one country in the period: a bar for each run of years with deliveries, total on the label."""
    f = supplier_data((iso,), a, b)
    if f.empty:
        return None, None, None
    cmap = supplier_colours((iso,), a, b, n=4)
    tot = f.groupby("supplier")["tiv"].sum().sort_values(ascending=False)
    lab = {s: f"{short_name(s, 22)} · {v:,.0f}" for s, v in tot.items()}
    parts = []
    for s in tot.index:
        t = f[f["supplier"] == s].sort_values("year")
        for p, q in runs(t["year"].tolist()):
            parts.append(dict(row=lab[s], x0=p - .5, x1=q + .5, Supplier=s, Years=f"{p}" + (f"–{q}" if q > p else ""),
                              TIV=t.loc[t["year"].between(p, q), "tiv"].sum(), col=cmap.get(s, nd.OTHER_COLOUR)))
    table = tot.rename("TIV").reset_index().rename(columns={"supplier": "Supplier"})
    yrs = f.groupby("supplier")["year"].agg(["min", "max", "nunique"])
    table["Years"] = table["Supplier"].map(lambda s: f"{yrs.loc[s, 'min']}–{yrs.loc[s, 'max']}" if yrs.loc[s, "max"] > yrs.loc[s, "min"] else str(yrs.loc[s, "min"]))
    table["Years with deliveries"] = table["Supplier"].map(yrs["nunique"])
    table["Share"] = 100 * table["TIV"] / table["TIV"].sum()
    return pd.DataFrame(parts), [lab[s] for s in tot.index], table


@st.cache_resource(**CHARTS)
def supplier_rows(iso, a, b):
    df, rows, table = supplier_rows_data(iso, a, b)
    if df is None:
        return None, 0, None
    tt = [alt.Tooltip("Supplier:N"), alt.Tooltip("Years:N"), alt.Tooltip("TIV:Q", title="TIV delivered", format=",.1f")]
    chart, h = range_rows(df, rows, a, b, alt.Color("col:N", scale=None), tt)
    return chart, h, table


@st.cache_resource(**CHARTS)
def sup_dem_chart(isos, a, b, follow, style_):
    s, demo = nd.load_sup_dem()
    s = s[s["iso3"].isin(isos) & s["year"].between(a, b)]
    if s.empty:
        return None, list(isos), demo
    have = set(s["iso3"].unique())
    missing = [i for i in isos if i not in have]
    if len(isos) > 1:
        return (lines_chart(isos, a, b, follow, "sup_dem", "Supplier democracy (0–1)", 360, (0, 1.02), (0, .5, 1), style_),
                missing, demo)
    # one country: supplier democracy and the share of TIV from democracies
    t = value_frame(isos, a, b)
    if t.empty:
        return None, list(isos), demo
    iso = isos[0]
    series = {"Supplier democracy (0–1)": "sup_dem", "Share of TIV from democracies": "share_dem"}
    long = pd.concat([t.assign(Series=k, v=t[c]) for k, c in series.items()])
    colour = alt.Color("Series:N", scale=alt.Scale(domain=list(series), range=[COL[iso], COL[iso]]),
                       legend=alt.Legend(orient="top", direction="horizontal", title=None, columns=1, symbolType="stroke", symbolStrokeWidth=2.5, symbolOpacity=1, labelLimit=260))
    dash = alt.StrokeDash("Series:N", scale=alt.Scale(domain=list(series), range=[[1, 0], [2, 3]]), legend=None)
    width = alt.StrokeWidth("Series:N", scale=alt.Scale(domain=list(series), range=[2, 1.4]), legend=None)
    x = yr_x("year", a, b, pad=0)
    yy = alt.Y("v:Q", scale=alt.Scale(domain=[0, 1.02], nice=False), axis=alt.Axis(title="Supplier democracy (0–1)", values=[0, .5, 1]))
    t = t.assign(h0=t["year"] - .5, h1=t["year"] + .5)
    layers = [
        alt.Chart(long).mark_line(invalid="break-paths-filter-domains").encode(x=x, y=yy, color=colour, strokeDash=dash, strokeWidth=width),
        alt.Chart(t[t["alone"].astype(bool)]).mark_point(filled=True, size=22, color=COL[iso]).encode(
            x=x, y=alt.Y("sup_dem:Q", scale=alt.Scale(domain=[0, 1.02], nice=False), axis=alt.Axis(title="Supplier democracy (0–1)", values=[0, .5, 1]))),
        alt.Chart(t).mark_rect(opacity=0).encode(
            yr_x("h0", a, b, pad=0), x2="h1:Q",
            tooltip=[alt.Tooltip("year:Q", title="Year", format="d"), alt.Tooltip("sup_dem:Q", title="Supplier democracy", format=".2f"),
                     alt.Tooltip("share_dem:Q", title="Share from democracies", format=".0%")]),
        year_rule(1.2),
    ]
    return vl_finish(alt.layer(*layers).properties(height=360)), missing, demo


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


SK_H, SK_PAD, SK_STEPS = 400, 8, 24  # Sankey: height (px), gap between nodes (px), points along each band


@st.cache_data
def sankey_data(isos, y):
    """Who delivered to whom in the year, drawn as a Sankey in Altair: the 8 largest suppliers left, the 10 largest
    recipients right (the rest grouped), node heights and band widths in pixels of the chart (y runs 0..SK_H)."""
    f = country_flows(isos, y)
    if f.empty:
        return None, None
    top_s = list(f.groupby("supplier")["tiv"].sum().nlargest(8).index)
    top_r = list(f.groupby("recipient")["tiv"].sum().nlargest(10).index)
    g = f.assign(s=np.where(f["supplier"].isin(top_s), f["supplier"], "Other suppliers"),
                 r=np.where(f["recipient"].isin(top_r), f["recipient"], "Other recipients"))
    links = g.groupby(["s", "r"], as_index=False)["tiv"].sum()
    left = list(links.groupby("s")["tiv"].sum().sort_values(ascending=False).index)
    right = list(links.groupby("r")["tiv"].sum().sort_values(ascending=False).index)
    total = links["tiv"].sum()
    k = min(SK_H - SK_PAD * (len(left) - 1), SK_H - SK_PAD * (len(right) - 1)) / total  # px per TIV
    nodes, top = [], {}
    for side, names_, col in (("s", left, "s"), ("r", right, "r")):
        size = links.groupby(col)["tiv"].sum()
        pos = (SK_H - (total * k + SK_PAD * (len(names_) - 1))) / 2  # centre each side
        for n in names_:
            h = size[n] * k
            nodes.append(dict(node=n, side=side, y0=pos, y1=pos + h, mid=pos + h / 2, tiv=size[n]))
            top[(side, n)] = pos
            pos += h + SK_PAD
    nodes = pd.DataFrame(nodes)
    # bands: on the left ordered by recipient, on the right by supplier (as Plotly does), so they cross little
    links["w"] = links["tiv"] * k
    links = links.assign(ri=links["r"].map({n: i for i, n in enumerate(right)}), si=links["s"].map({n: i for i, n in enumerate(left)}))
    links = links.sort_values(["si", "ri"])
    links["ys"] = links["s"].map(lambda n: top[("s", n)]) + links.groupby("s")["w"].cumsum() - links["w"] / 2
    links = links.sort_values(["ri", "si"])
    links["yt"] = links["r"].map(lambda n: top[("r", n)]) + links.groupby("r")["w"].cumsum() - links["w"] / 2
    t = np.linspace(0, 1, SK_STEPS)
    smooth = t * t * (3 - 2 * t)
    pts = []
    for lid, l in enumerate(links.itertuples()):
        mid = l.ys + (l.yt - l.ys) * smooth
        tip = f"{l.s} → {l.r}: {l.tiv:,.1f} TIV"
        pts.append(pd.DataFrame({"lid": lid, "x": t, "lo": mid - l.w / 2, "hi": mid + l.w / 2, "s": l.s, "tip": tip}))
    return nodes, pd.concat(pts)


@st.cache_resource(**CHARTS)
def sankey_chart(isos, y, a, b):
    cmap = supplier_colours(isos, a, b)
    nodes, bands = sankey_data(isos, y)
    if nodes is None:
        return None
    nodes = nodes.assign(col=[flow_colour(n, cmap) if s == "s" else INK2 for n, s in zip(nodes["node"], nodes["side"])],
                         x0=np.where(nodes["side"] == "s", -.035, 1.0), x1=np.where(nodes["side"] == "s", 0.0, 1.035),
                         tip=nodes["node"] + ": " + nodes["tiv"].map(lambda v: f"{v:,.0f}") + " TIV")
    bands = bands.assign(col=bands["s"].map(lambda s: flow_colour(s, cmap)))
    xs = alt.Scale(domain=[-.035, 1.035], nice=False, zero=False)
    ys = alt.Scale(domain=[0, SK_H], reverse=True, nice=False, zero=False)
    x, yy, ny = alt.X("x:Q", scale=xs, axis=None), alt.Y("lo:Q", scale=ys, axis=None), alt.Y("y0:Q", scale=ys, axis=None)
    tip = [alt.Tooltip("tip:N", title=" ")]
    layers = [
        alt.Chart(bands).mark_area(opacity=.35).encode(x, yy, y2="hi:Q", detail="lid:N", color=alt.Color("col:N", scale=None), tooltip=tip),
        alt.Chart(nodes).mark_rect().encode(alt.X("x0:Q", scale=xs, axis=None), x2="x1:Q", y=ny, y2="y1:Q",
                                            color=alt.Color("col:N", scale=None), tooltip=tip),
        alt.Chart(nodes[nodes["side"] == "s"]).mark_text(align="left", dx=4, color=INK, fontSize=11).encode(
            alt.X("x1:Q", scale=xs, axis=None), alt.Y("mid:Q", scale=ys, axis=None), text="node:N"),
        alt.Chart(nodes[nodes["side"] == "r"]).mark_text(align="right", dx=-4, color=INK, fontSize=11).encode(
            alt.X("x0:Q", scale=xs, axis=None), alt.Y("mid:Q", scale=ys, axis=None), text="node:N"),
    ]
    return vl_finish(alt.layer(*layers).properties(height=SK_H))


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
    if ss.pop("cc_full_rerun", False):  # Play, Pause or the speed changed: the fragment's timer is set on a full run
        st.rerun(scope="app")
    a, b = period_bounds()
    if ss["playing"]:
        if ss["year"] >= b:
            ss["playing"] = False
            ss["cc_year_slider"] = ss["year"]
            st.rerun(scope="app")
        ss["year"] += 1
    y = ss["year"]
    isos = tuple(sel)
    names = [NAMES[i] for i in sel]
    d = period_panel(isos, a, b)
    group = ss.get("cc_group_name")

    st.title(names[0] if single else group or f"Comparing {len(sel)} countries", anchor=False)
    st.caption(f"Regime, democracy index, armed conflict and arms imports, {a}–{b}. Move the year or press Play."
               if single else f"{len(sel)} countries side by side, {a}–{b}: " + ", ".join(names[:8]) + (f" and {len(sel) - 8} more." if len(sel) > 8 else "."))

    # the year bar: Play, speed, year and period (the slider follows Play)
    with st.container(horizontal=True, vertical_alignment="center", gap="medium"):
        st.button("Pause" if ss["playing"] else "Play", icon=":material/pause:" if ss["playing"] else ":material/play_arrow:",
                  type="primary", on_click=toggle_play, key="cc_play", help="Play through the years of the period.")
        st.segmented_control("Speed", list(SPEEDS), key="cc_speed", required=True, on_change=full_rerun,
                             label_visibility="collapsed", help="Play speed")
        ss["cc_year_slider"] = y
        st.slider("Year", a, b, key="cc_year_slider", on_change=slider_moved, label_visibility="collapsed", width="stretch")
        st.segmented_control("Period", list(PERIODS), key="cc_period", required=True, on_change=clamp_year,
                             label_visibility="collapsed", help="Limits the year slider and Play to this period.")

    # loading bar for big selections (not while playing, where it would flicker every year)
    # (always in its own st.empty slot: an element that comes and goes would shift every chart below it, and
    # Streamlit would mount those charts anew)
    bar_slot = st.empty()
    bar = bar_slot.progress(0, text=f"Loading {len(sel)} countries…") if len(sel) > 8 and not ss["playing"] else None

    def loaded(frac, text):
        if bar is not None:
            bar.progress(frac, text=f"Loading {len(sel)} countries: {text}…")

    no_data = [i for i in sel if d[d["iso3"] == i]["democracy_index"].notna().sum() == 0]
    if no_data:
        st.info(("No V-Dem data in this period for " + ", ".join(NAMES[i] for i in no_data) + ". ")
                + ("" if len(no_data) < len(sel) else "The state did not exist then. Try another period."
                   if single else "Try another period."), icon=":material/info:")
        if len(no_data) == len(sel):
            bar_slot.empty()
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
            sc = scatter_single(sel[0], a, b, y, full)
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
            sc = scatter_compare(isos, a, b, y, follow, full)
        if sc is None:
            st.info(f"No V-Dem data in {y} for {'this country' if single else 'these countries'}. Move the year or pick another period.",
                    icon=":material/info:")
        else:
            st.altair_chart(sc[0], key="cc_scatter", on_select=scatter_clicked, selection_mode="pick", width="stretch")
            if not single:
                have = set(now.index[now["democracy_index"].notna()])
                muted_list(f"Not in the scatter, no data for {y}", [i for i in isos if i not in have])
        st.caption(SC_GUIDE + ("" if single else " Trails: the previous 10 years of the followed countries; the others are faint.")
                   + " Big ringed dot: war year; small ringed dot: minor conflict; pale band: several conflict years in a row "
                   "(solid: war, dotted: minor). Click a dot to jump to its year."
                   + (" Left strip: no arms received." if sc is not None and sc[1] else ""))
    with right, st.container(border=True, height="stretch"):
        if single:
            st.markdown("**Democracy, conflict and arms on one axis**")
            st.caption("Line: democracy index (0–1). Bars: arms imports (TIV, right axis). Shading: war (darker) or minor conflict.")
            (_, chart), = one_axis(isos, a, b, False, 450, style(isos))
            st.altair_chart(at_year(chart, y), key="cc_axis1", width="stretch")
        else:
            st.markdown("**Democracy index**")
            st.caption("V-Dem, 0 to 1. " + ("Click a name in the legend to show only that country (shift-click for more, "
                                            "double-click the chart to show all again)."
                                            if len(isos) <= LEGEND_MAX else "Followed countries stand out; hover a line for its name."))
            st.altair_chart(at_year(democracy_lines(isos, a, b, follow), y), key="cc_demo", width="stretch")

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
            charts = one_axis(rows_isos, a, b, same, None, style(rows_isos))
            with scroll_box(one_axis_heights(len(rows_isos))[1], 760):
                for iso, chart in charts:  # one chart per country, stacked
                    st.altair_chart(at_year(chart, y), key=f"cc_axis_{iso}", width="stretch")

    loaded(.55, "regimes and conflicts")
    # ---- regime + conflicts (side by side for one country; stacked for a comparison, which has many more rows)
    if single:
        left, right = st.columns(2, gap="medium")
    else:
        left, right = st.container(), st.container()
    with left, st.container(border=True, height="stretch"):
        st.markdown("**Regime**")
        st.caption("V-Dem regime type per year.")
        chart, height = regime_chart(isos, a, b)
        if chart is None:
            st.info("No regime data in this period.", icon=":material/info:")
        else:
            with scroll_box(height, 640):
                st.altair_chart(at_year(chart, y), key="cc_regime", width="stretch")
    with right, st.container(border=True, height="stretch"):
        st.markdown("**Armed conflicts**")
        chart, none, height, n_with = conflict_chart(isos, a, b)
        if chart is None:
            st.caption("UCDP, 25+ battle deaths a year.")
            st.info(f"No armed conflict with 25 or more battle deaths in {a}–{b}"
                    + ("." if single else f" in any of the {len(isos)} countries."), icon=":material/info:")
        else:
            st.caption("UCDP. Light bars: war (1,000+ battle deaths a year); dark bars: minor conflict (25–999). One row per conflict, "
                       "named after the other side, with its conflict years in this period. Hover a bar for the sides and type.")
            with scroll_box(height, 640):
                st.altair_chart(at_year(chart, y), key="cc_conflict", width="stretch")
            if not single:
                muted_list(f"No armed conflict in {a}–{b}", none)

    loaded(.75, "suppliers")
    # ---- suppliers
    left, right = st.columns([1.5, 1], gap="medium")
    with left, st.container(border=True, height="stretch"):
        st.markdown("**Arms imports by supplier**")
        st.caption("SIPRI TIV per year, coloured by the largest suppliers of " + ("this country" if single else "these countries") + " in the period." + rows_note)
        n_has = len(supplier_bars_data(rows_isos, a, b)[2])
        row_h = 280 if n_has == 1 else 150
        legend, charts = supplier_charts(rows_isos, a, b, row_h)
        if legend is None:
            st.info(f"No major arms imports recorded in {a}–{b}.", icon=":material/info:")
        else:
            st.altair_chart(legend, key="cc_sup_legend", width="stretch")
            # one chart per country, two per row (Vega-Lite facets cannot stretch to the card width)
            with scroll_box((row_h + 16) * -(-len(charts) // 2), 760):
                for r0 in range(0, len(charts), 2):
                    cols = st.columns(2, gap="small") if len(charts) > 1 else [st.container()]
                    for col, (iso, chart) in zip(cols, charts[r0:r0 + 2]):
                        with col:
                            st.altair_chart(at_year(chart, y), key=f"cc_sup_{iso}", width="stretch")
            has = [iso for iso, _ in charts]
            none = [i for i in rows_isos if i not in has]
            muted_list(f"No major arms imports in {a}–{b}", none)
            with_imports = has
            with st.expander("Every supplier, year by year", icon=":material/list:"):
                who = with_imports[0] if len(with_imports) == 1 else st.selectbox(
                    "Country", with_imports, format_func=NAMES.get, key="cc_sup_country")
                rchart, rheight, table = supplier_rows(who, a, b)
                st.caption(f"{len(table)} suppliers of {NAMES[who]} in {a}–{b}. A bar for each run of years with deliveries; "
                           "the number after the name is the total TIV in the period.")
                with scroll_box(rheight, 420):
                    st.altair_chart(at_year(rchart, y), key="cc_sup_rows", width="stretch")
                st.dataframe(table, hide_index=True, height=min(38 + 35 * len(table), 320), alt=f"All arms suppliers of {NAMES[who]} in the period",
                             column_config={"TIV": st.column_config.NumberColumn("TIV", format="localized"),
                                            "Share": st.column_config.ProgressColumn("Share", format="%.1f%%", min_value=0, max_value=100)})
    with right, st.container(border=True, height="stretch"):
        st.markdown("**Who supplied the arms**")
        chart, missing, demo = sup_dem_chart(isos, a, b, follow, style(isos))
        if demo:
            st.warning("Placeholder numbers until notebook 08 is done.", icon=":material/science:")
        st.caption("How democratic the suppliers were, weighted by TIV: 0 = only autocratic suppliers, 1 = only democratic ones. "
                   "Gaps: years without imports.")
        if chart is None:
            st.info(f"No arms imports to weigh in {a}–{b}.", icon=":material/info:")
        else:
            st.altair_chart(at_year(chart, y), key="cc_supdem", width="stretch")
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
                st.altair_chart(sankey_chart(isos, y, a, b), key="cc_sankey", width="stretch")

    bar_slot.empty()
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
