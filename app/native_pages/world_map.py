"""World map: regimes, arms flows and arms build-up from 1950 to 2025, with Play through the years.

Same content as the World map page of app/site/adc.html. The three modes draw one and the same keyed Altair map (our Equal
Earth shapes in the pixel space of app/site/mapdata.json, same size, colours and legend box); a mode only changes what
is drawn on it (striped conflicts, delivery lines, bubbles). The year changes only named datasets, so Vega redraws the
map in place and Play does not flicker. The chord ring of Arms flows is the custom component of
app/native_components/chord. Play advances the year for the whole map card (map, side panel, river and numbers
together) by re-running one fragment; its year bar (Play, speed, year slider, period) is pinned to the bottom of the
screen with st.bottom. The main finding and the data sources below are outside the fragment.
"""

import json
import re

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

import native_data as nd
import native_results as nr
from native_components.chord import chord_ring

Y0, Y1 = 1950, 2025
BG = "rgba(0,0,0,0)"
INK, INK2, MUTED, LINE, NODATA = "#f0efec", "#c3c2b7", "#959086", "#2c2c2a", "#2a2a28"
FONT = "IBM Plex Sans"
MODES = ["Regimes", "Arms flows", "Arms build-up"]
TITLES = {"Regimes": "Regimes and conflicts", "Arms flows": "Arms deliveries", "Arms build-up": "Arms build-up"}
PERIODS = {"1950–2025": (1950, 2025), "Cold War": (1950, 1991), "Since 1992": (1992, 2025)}
SPEEDS = {"0.5×": 0.5, "1×": 1.0, "2×": 2.0}
PACE = {"Regimes": 0.6, "Arms flows": 1.5, "Arms build-up": 1.0}  # seconds per year at 1×, calmer for the busier maps
MAP_H = 300           # nominal map height (bubble sizes, side panel); the drawn map follows its width (MAP_HEIGHT)
SIDE_H = MAP_H + 40   # side panel: as tall as the map plus its badge line
MAP_MAX_H = 560       # the map never gets taller than this on very wide screens
COMPARE = "native_pages/compare.py"
TIV_NOTE = ("SIPRI trend-indicator values (TIV) measure military capability transferred, not money. "
            "Historical states are drawn at today's borders (Soviet Union at Russia).")
NOTES = {
    "Regimes": "Grey: no V-Dem data for that year. Small states without a shape on the map are drawn as dots.",
    "Arms flows": "Line width = TIV delivered; country tint = main supplier over the last 5 years. " + TIV_NOTE,
    "Arms build-up": "Bubble area = major arms received in the previous 10 years (SIPRI TIV, same scale for all years); "
                     "colour = regime type. A thin line points home where a bubble had to move. Historical states count with "
                     "today's country (e.g. East Germany with Germany).",
}

panel = nd.load_panel()
flows = nd.load_flows()
NAMES = panel.drop_duplicates("iso3").set_index("iso3")["country_name"].to_dict()
REG_LABELS = [r.capitalize() for r in nd.REGIMES]
REG_COLS = [nd.REGIME_COLOURS[r] for r in nd.REGIMES]
SUP_ORDER = list(nd.SUPPLIER_COLOURS) + ["Other"]
fmt = "{:,.0f}".format


def pct(v, t):
    return f"{v / t:.0%}" if t else "0%"


# ------------------------------------------------------------------ state
ss = st.session_state
ss.setdefault("year", 2000)
ss.setdefault("playing", False)
ss.setdefault("wm_period", "1950–2025")


def period():
    return PERIODS.get(ss.get("wm_period") or "1950–2025", (Y0, Y1))


def clamp_year():
    p0, p1 = period()
    ss["year"] = min(max(ss["year"], p0), p1)
    ss["wm_year_slider"] = ss["year"]


def slider_moved():
    ss["year"] = ss["wm_year_slider"]


def toggle_play():
    p0, p1 = period()
    ss["playing"] = not ss["playing"]
    if ss["playing"] and not p0 <= ss["year"] < p1:
        ss["year"] = p0
    ss["_wm_full"] = True  # the fragment's timer is set on a full run


def full_rerun():
    """Mode and speed change the sidebar or the Play timer, which live outside the map-card fragment."""
    ss["_wm_full"] = True


def set_year(y):
    """A click on a river: jump to that year (and stop playing); the sidebar is redrawn by a full rerun."""
    p0, p1 = period()
    ss["year"] = min(max(int(y), p0), p1)
    ss["wm_year_slider"] = ss["year"]
    ss["playing"] = False
    ss["_wm_full"] = True


def pick_country(iso):
    """Show `iso` in the country card (the sidebar "Country details" box), from a click inside the map card."""
    if iso in NAMES:
        ss["wm_card_iso"] = iso
        ss["_wm_full"] = True


def close_card():
    ss["wm_card_iso"] = None
    ss["_wm_full"] = True


def open_in_compare(iso):
    ss["cmp_countries"] = [iso]  # one-shot hand-over, read by the compare page
    ss["playing"] = False
    ss["_wm_go"] = COMPARE


ss.setdefault("wm_mode", "Regimes")
ss.setdefault("wm_speed", "1×")
if not ss["playing"]:
    clamp_year()
mode = ss["wm_mode"] if ss.get("wm_mode") in MODES else "Regimes"
speed = ss["wm_speed"] if ss.get("wm_speed") in SPEEDS else "1×"

# ------------------------------------------------------------------ sidebar: options of the mode, then the country card
with st.sidebar:
    if mode != "Arms build-up":  # build-up has no options of its own
        st.markdown("**Map options**")
    show_conflict, top_n, share, tint, highlight = True, 25, False, True, None
    if mode == "Regimes":
        show_conflict = st.toggle("Stripe countries with armed conflict", value=True, key="wm_stripes")
    elif mode == "Arms flows":
        top_n = st.segmented_control("Deliveries drawn on the map", [25, 60], default=25, key="wm_topn", required=True,
                                     format_func=lambda n: f"Top {n}", width="stretch") or 25
        share = st.segmented_control("River shows", ["Amount", "Share of world total"], default="Amount", key="wm_share",
                                     required=True, width="stretch") == "Share of world total"
        highlight = st.selectbox("Highlight a supplier", SUP_ORDER[:-1], index=None, key="wm_highlight",
                                 placeholder="All suppliers")
        tint = st.toggle("Tint countries by main supplier (last 5 years)", value=True, key="wm_tint")
    if mode != "Arms build-up":
        st.divider()
    card_iso = st.selectbox("Country details", sorted(NAMES, key=NAMES.get), index=None, key="wm_card_iso",
                            format_func=NAMES.get, placeholder="Search a country")
    st.caption("Or click a country on the map.")
    st.caption(TIV_NOTE)


# ------------------------------------------------------------------ chart helpers
NO_REG = "#5b5850"
SURF = "#1a1a19"  # card surface: the borders between countries
BLD_DOMAIN = REG_LABELS + ["No regime data"]


def alt_finish(chart, height):
    """The look of the Altair charts of this page (as the scatter of Countries & compare): transparent, IBM Plex, no frame."""
    return (chart.properties(height=height).configure_view(stroke=None)
            .configure(background="transparent", font=FONT + ", sans-serif")
            .configure_axis(labelColor=MUTED, titleColor=MUTED, titleFontWeight="normal", labelFontSize=11, titleFontSize=11,
                            domainColor=LINE, tickColor=LINE, gridColor=LINE)
            .configure_legend(labelColor=INK2, labelFontSize=12, titleColor=MUTED))


# ------------------------------------------------------------------ the one world map of the three modes
# All three modes draw the same Altair map: our Equal Earth shapes of app/site/mapdata.json in their own pixel space
# (960 × 423, the map of the HTML version), an identity projection fitted to that frame, the same height, colours,
# borders, hover outline, small-state dots and legend box. A mode only changes what is drawn on top (stripes, arcs,
# bubbles). The geometry is fixed in the spec; everything that changes with the year is in named datasets, so Play
# swaps the data of the same Vega view and never redraws the chart.
def _hex(rgb):
    return "#" + "".join(f"{int(v):02x}" for v in rgb[:3])


def _rgb(h):
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)]


def mix(h, base=NODATA, k=.32):
    """`k` of colour h mixed into `base`, as color-mix() in the HTML version."""
    a, b = _rgb(h), _rgb(base)
    return _hex([round(a[i] * k + b[i] * (1 - k)) for i in range(3)])


@st.cache_data
def px_map():
    """(width, height, {iso3: [rings as (n, 2) arrays]}, {iso3: [x, y]} of the small states) in the map's pixel space."""
    m = json.loads(nd.MAPDATA.read_text(encoding="utf8"))
    rings = {}
    for iso, d in m["p"].items():
        rs = [np.array(re.findall(r"(-?[\d.]+),(-?[\d.]+)", sub), dtype=float) for sub in d.split("M")[1:]]
        rings[iso] = [r for r in rs if len(r) >= 3]
    return float(m["w"]), float(m["h"]), rings, m.get("pts", {})


W_PX, H_PX, RINGS, PTS = px_map()
FRAME = {"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {}, "geometry": {
    "type": "Polygon", "coordinates": [[[0, 0], [W_PX, 0], [W_PX, H_PX], [0, H_PX], [0, 0]]]}}]}


@st.cache_data
def px_points():
    """One map point per country (centroid of its largest ring, or its small-state dot) and the size of its shape."""
    rows = {}
    for iso, rs in RINGS.items():
        best, x0, y0, x1, y1 = None, np.inf, np.inf, -np.inf, -np.inf
        for r in rs:
            x, y = r[:, 0], r[:, 1]
            x2, y2 = np.roll(x, -1), np.roll(y, -1)
            c = x * y2 - x2 * y
            a = c.sum() / 2
            x0, y0, x1, y1 = min(x0, x.min()), min(y0, y.min()), max(x1, x.max()), max(y1, y.max())
            if a and (best is None or abs(a) > abs(best[0])):
                best = (a, ((x + x2) * c).sum() / (6 * a), ((y + y2) * c).sum() / (6 * a))
        if best:
            rows[iso] = (best[1], best[2], max(x1 - x0, y1 - y0))
    for iso, (x, y) in PTS.items():
        rows.setdefault(iso, (x, y, 0.0))
    for old, new in nd.HISTORICAL.items():
        if new in rows:
            rows[old] = rows[new]
    return pd.DataFrame.from_dict(rows, orient="index", columns=["x", "y", "size"])


PX = px_points()
SHAPED = [i for i in RINGS if RINGS[i]]
# dots: small states without a shape (drawn), and tiny shapes (an invisible, larger click target, as in the HTML map)
DOTS = [i for i in PTS if i not in RINGS] + [i for i in SHAPED if PX.loc[i, "size"] < 14]


@st.cache_data
def shape_features():
    return [{"type": "Feature", "iso3": iso, "properties": {},
             "geometry": {"type": "MultiPolygon", "coordinates": [[np.round(r, 1).tolist() + [np.round(r[0], 1).tolist()]]
                                                                  for r in RINGS[iso]]}} for iso in SHAPED]


def _hatch(rings, s):
    """Diagonal hatch segments (lines x + y = const, `s` px apart, as the rotated <pattern> of the HTML map) inside the
    rings (non-zero fill rule, as SVG)."""
    k = 1 / np.sqrt(2)
    edges = []
    for r in rings:
        u, v = (r[:, 0] + r[:, 1]) * k, (r[:, 0] - r[:, 1]) * k
        edges.append((u, v, np.roll(u, -1), np.roll(v, -1)))
    u_all = np.concatenate([e[0] for e in edges])
    segs = []
    for c in np.arange(np.ceil(u_all.min() / s) * s, u_all.max(), s):
        vs, ws = [], []
        for ua, va, ub, vb in edges:
            m = ((ua <= c) & (ub > c)) | ((ub <= c) & (ua > c))
            t = (c - ua[m]) / (ub[m] - ua[m])
            vs.append(va[m] + t * (vb[m] - va[m]))
            ws.append(np.where(ub[m] > ua[m], 1, -1))
        v, w = np.concatenate(vs), np.concatenate(ws)
        o = np.argsort(v)
        v, wind = v[o], np.cumsum(w[o])
        for j in range(len(v) - 1):
            if wind[j] != 0 and v[j + 1] - v[j] > .3:
                segs.append([[round((c + v[j]) * k, 1), round((c - v[j]) * k, 1)],
                             [round((c + v[j + 1]) * k, 1), round((c - v[j + 1]) * k, 1)]])
    return segs


@st.cache_data
def hatch_features():
    """Stripes of every country: "ISO3:minor" (6 px apart) and "ISO3:war" (3.4 px, denser), as in regime_map.js."""
    out = []
    for iso in SHAPED:
        for cls, s in (("minor", 6.0), ("war", 3.4)):
            segs = _hatch(RINGS[iso], s)
            if segs:
                out.append({"type": "Feature", "key": f"{iso}:{cls}", "properties": {},
                            "geometry": {"type": "MultiLineString", "coordinates": segs}})
    return out


# selections of the map: "n" changes with the country card or the pinned card, so a click on the same country after the
# card was closed is a new selection
COUNTRY = alt.selection_point(name="country", fields=["iso3", "n"], on="click", empty=False)
COUNTRY_DOT = alt.selection_point(name="country_dot", fields=["iso3", "n"], on="click", empty=False)
COUNTRY_HATCH = alt.selection_point(name="country_hatch", fields=["iso3", "n"], on="click", empty=False)
ARC = alt.selection_point(name="arc", fields=["iso3", "n"], on="click", empty=False)
BUBBLE = alt.selection_point(name="bubble", fields=["iso3", "n"], on="click", empty=False)
BUBBLE_LABEL = alt.selection_point(name="bubble_label", fields=["iso3", "n"], on="click", empty=False)
HOVER = alt.selection_point(name="hover", fields=["iso3"], on="pointerover", clear="pointerout", empty=False)
MAP_SELECTIONS = {"Regimes": ["country", "country_dot", "country_hatch"],
                  "Arms flows": ["arc", "country", "country_dot"],
                  "Arms build-up": ["bubble", "bubble_label", "country", "country_dot"]}


def map_legend(symbol):
    """The legend of every mode: a box in the bottom-left corner of the map (over the South Pacific)."""
    return alt.Legend(title=None, orient="bottom-left", direction="vertical", symbolType=symbol, symbolSize=100,
                      symbolStrokeWidth=3 if symbol == "stroke" else .8,
                      symbolStrokeColor=alt.Undefined if symbol == "stroke" else "#45443f",
                      symbolOpacity=.95, labelColor=INK2, labelFontSize=12,
                      labelFont=FONT, fillColor="rgba(26,26,25,.85)", strokeColor=LINE, padding=8, cornerRadius=6, offset=4,
                      rowPadding=2)


def map_rows(info, selected, n):
    """Per-year rows of the shapes and of the dots from `info` (index iso3; columns fill, legend, tooltip fields)."""
    info = info.assign(iso3=info.index, n=n, sc=SURF, sw=.5)
    if selected in info.index:
        info.loc[selected, ["sc", "sw"]] = [INK, 1.6]
    land = info.reindex(SHAPED).dropna(subset=["iso3"])
    dots = info.reindex(DOTS).dropna(subset=["iso3"])
    dots = dots.assign(x=PX.loc[dots.index, "x"].values, y=PX.loc[dots.index, "y"].values,
                       vis=[0.0 if i in RINGS else 1.0 for i in dots.index])
    return land.to_dict("records"), dots.to_dict("records")


def world_map(info, selected, n, colour, tooltip, legend_symbol="square", over=(), datasets=None):
    """Vega-Lite spec of the map of every mode: land filled by `colour` (on field `fill` or a legend field of `info`), dots of the small states,
    then the layers of the mode in `over` (named datasets in `datasets`)."""
    land_rows, dot_rows = map_rows(info, selected, n)
    paint = {"fill" if isinstance(colour, alt.Fill) else "color": colour}
    shapes = alt.LookupData(alt.NamedData("wm_shapes"), key="iso3")
    # no hover condition on the ~180 shapes (it re-encoded all of them on every move): the hovered country's outline is
    # a separate one-shape layer on top, filtered by the hover selection; it is stroke only, so it hardly catches the
    # pointer, and when it does it carries the same country, so the selection stays the same
    land = (alt.Chart(alt.NamedData("wm_land")).transform_lookup(lookup="iso3", from_=shapes, as_="geo")
            .mark_geoshape(cursor="pointer").encode(shape="geo:G", **paint, stroke=alt.Stroke("sc:N", scale=None),
                                                    strokeWidth=alt.StrokeWidth("sw:Q", scale=None), tooltip=tooltip)
            .add_params(COUNTRY, HOVER))
    outline = (alt.Chart(alt.NamedData("wm_land")).transform_filter(HOVER)
               .transform_lookup(lookup="iso3", from_=shapes, as_="geo")
               .mark_geoshape(filled=False, stroke=INK, strokeWidth=1.2).encode(shape="geo:G"))
    dots = (alt.Chart(alt.NamedData("wm_dots")).mark_circle(cursor="pointer", stroke=SURF, strokeWidth=.6)
            .encode(longitude="x:Q", latitude="y:Q", **paint,
                    opacity=alt.Opacity("vis:Q", scale=None),
                    size=alt.condition("datum.vis > 0", alt.value(34), alt.value(190)), tooltip=tooltip)
            .add_params(COUNTRY_DOT))
    chart = alt.layer(land, dots, *over, outline).properties(datasets={"wm_land": land_rows, "wm_dots": dot_rows, **(datasets or {})})
    chart = chart.project(type="identity", fit=FRAME).resolve_scale(color="shared")
    spec = (chart.properties(height=MAP_H).configure_view(stroke=None)
            .configure(background="transparent", font=FONT + ", sans-serif")
            .configure_legend(labelColor=INK2, labelFontSize=12, symbolType=legend_symbol)).to_dict()
    # the fixed geometry joins the spec only now: inside Altair objects it would be deep-copied on every Play step
    spec["datasets"]["wm_shapes"] = shape_features()
    # the map's height follows its width (Equal Earth frame 960 × 423, as `height: auto` of the HTML map), capped
    spec.pop("height", None)
    spec.setdefault("params", []).append({"name": "height", "update": f"min(width * {H_PX / W_PX:.4f}, {MAP_MAX_H})"})
    if "wm_hatch" in spec["datasets"]:
        spec["datasets"]["wm_stripes"] = hatch_features()
    return spec


# ---- Regimes: fill by regime type, stripes for armed conflict
CONFLICT = ["No armed conflict", "Minor armed conflict (25–999 deaths)", "War (1,000+ deaths)"]
REG_TIP = [alt.Tooltip("Country:N"), alt.Tooltip("Regime:N"), alt.Tooltip("Democracy index:N"),
           alt.Tooltip("Armed conflict:N"), alt.Tooltip("Arms imports:N")]


@st.cache_data
def regime_info(y):
    g = panel[panel["year"] == y].set_index("iso3")
    rows = {}
    for iso in dict.fromkeys(SHAPED + DOTS):
        name = NAMES.get(iso, iso)
        r = g.loc[iso] if iso in g.index else None
        if r is None or pd.isna(r["regime_type"]):
            rows[iso] = [f"{name} · {y}", "No regime data", f"No V-Dem data for {y}", "", "", 0]
            continue
        c = 0 if pd.isna(r["max_intensity"]) else int(r["max_intensity"])
        idx = "" if pd.isna(r["democracy_index"]) else f"{round(float(r['democracy_index']) + 1e-9, 2):.2f}"
        arms = 0 if pd.isna(r["arms_imports_tiv"]) else float(r["arms_imports_tiv"])
        rows[iso] = [f"{name} · {y}", REG_LABELS[int(r["regime_type"])], idx, CONFLICT[c], f"{fmt(arms)} TIV", c]
    return pd.DataFrame.from_dict(rows, orient="index",
                                  columns=["Country", "Regime", "Democracy index", "Armed conflict", "Arms imports", "c"])


def regimes_map(y, stripes, selected, n):
    info = regime_info(y)
    colour = alt.Color("Regime:N", scale=alt.Scale(domain=BLD_DOMAIN, range=REG_COLS + [NODATA]), legend=map_legend("square"))
    hatch = info[(info["c"] > 0) & (info["Regime"] != "No regime data")] if stripes else info.iloc[:0]
    hatch = hatch.assign(iso3=hatch.index, n=n, key=[f"{i}:{'war' if c == 2 else 'minor'}" for i, c in zip(hatch.index, hatch["c"])],
                         op=np.where(hatch["c"] == 2, .95, .6), sw=np.where(hatch["c"] == 2, 1.1, .8))
    rows = hatch.to_dict("records") or [{"iso3": "", "key": "", "n": n, "op": 0.0, "sw": 0.0}]  # never an empty dataset
    stripes_layer = (alt.Chart(alt.NamedData("wm_hatch"))
                     .transform_lookup(lookup="key", from_=alt.LookupData(alt.NamedData("wm_stripes"), key="key"), as_="geo")
                     .transform_filter("isValid(datum.geo)")
                     .mark_geoshape(filled=False, stroke=INK, cursor="pointer")
                     .encode(shape="geo:G", opacity=alt.Opacity("op:Q", scale=None), strokeWidth=alt.StrokeWidth("sw:Q", scale=None),
                             tooltip=REG_TIP)
                     .add_params(COUNTRY_HATCH))
    return world_map(info, selected, n, colour, REG_TIP, over=[stripes_layer], datasets={"wm_hatch": rows})


# ---- Arms flows: land tinted by main supplier, curved lines for the largest deliveries
FLOW_TIP = [alt.Tooltip("Country:N"), alt.Tooltip("Imports:N"), alt.Tooltip("Exports:N")]
ARC_TIP = [alt.Tooltip("Delivery:N"), alt.Tooltip("TIV:N")]
SUP_LABELS = SUP_ORDER[:-1] + ["Other suppliers"]


@st.cache_data
def year_flows(y):
    """Every delivery of the year, largest first; `drawable` = supplier and recipient both have a point on the map."""
    f = flows[(flows["year"] == y) & (flows["tiv"] > 0)].copy()
    f["recipient"] = f["recipient_iso3"].map(NAMES).fillna(f["recipient_iso3"])
    f["drawable"] = (f["supplier_iso3"].isin(PX.index) & f["recipient_iso3"].isin(PX.index)
                     & (f["supplier_iso3"] != f["recipient_iso3"].replace(nd.HISTORICAL)))
    return f.sort_values("tiv", ascending=False).reset_index(drop=True)


@st.cache_data
def flow_info(y, tint):
    """Per country of the map: fill (main supplier of the last 5 years) and imports/exports with the top 3 partners."""
    f = year_flows(y)
    f = f.assign(rec=f["recipient_iso3"].replace(nd.HISTORICAL))
    named = f[~f["supplier"].map(nd.is_non_state)]
    main = nd.main_suppliers(y) if tint else {}

    def top3(s):
        t = s.nlargest(3)
        return ", ".join(f"{k} {fmt(v)}" for k, v in t.items()) + (f", other {fmt(s.sum() - t.sum())}" if len(s) > 3 else "")

    rows = {}
    for iso in dict.fromkeys(SHAPED + DOTS):
        imp = f[f["rec"] == iso].groupby("supplier")["tiv"].sum()
        exp = named[named["supplier_iso3"] == iso].groupby("recipient")["tiv"].sum()
        fill = mix(nd.supplier_colour(main[iso])) if iso in main else (NODATA if iso in RINGS else "#78746c")
        rows[iso] = [f"{NAMES.get(iso, iso)} · {y}", fill,
                     f"{fmt(imp.sum())} TIV" + (f" ({top3(imp)})" if imp.sum() else ""),
                     f"{fmt(exp.sum())} TIV" + (f" ({top3(exp)})" if exp.sum() else "")]
    return pd.DataFrame.from_dict(rows, orient="index", columns=["Country", "fill", "Imports", "Exports"])


def arc_rows(y, top_n, highlight, n):
    """The `top_n` largest deliveries as curved lines (21 points each, bending north), one row per point."""
    f = year_flows(y)
    f = f[f["drawable"]].head(top_n)
    vmax = flows["tiv"].max()
    t = np.linspace(0, 1, 21)[:, None]
    rows = []
    for k, r in enumerate(f.itertuples()):
        a = PX.loc[r.supplier_iso3, ["x", "y"]].values.astype(float)
        b = PX.loc[r.recipient_iso3, ["x", "y"]].values.astype(float)
        d = b - a
        nrm = np.array([-d[1], d[0]]) * .16
        ctl = (a + b) / 2 + (nrm if nrm[1] < 0 else -nrm)
        pts = (1 - t) ** 2 * a + 2 * (1 - t) * t * ctl + t ** 2 * b
        lit = not highlight or r.supplier == highlight
        common = {"arc": k, "Supplier": r.supplier if r.supplier in nd.SUPPLIER_COLOURS else "Other suppliers",
                  "iso3": nd.HISTORICAL.get(r.recipient_iso3, r.recipient_iso3), "n": n,
                  "width": round(.8 + 6 * min(1.0, r.tiv / vmax), 2), "op": .85 if lit else .07,
                  "Delivery": f"{r.supplier} → {r.recipient}", "TIV": f"{fmt(r.tiv)} TIV in {y}"}
        rows += [{**common, "t": j, "x": round(float(p[0]), 1), "y": round(float(p[1]), 1)} for j, p in enumerate(pts)]
    return rows or [{"arc": -1, "Supplier": "Other suppliers", "iso3": "", "n": n, "width": 0.0, "op": 0.0, "Delivery": "",
                     "TIV": "", "t": 0, "x": 0.0, "y": 0.0}]


def flows_map(y, top_n, tint, highlight, selected, n):
    sup = alt.Color("Supplier:N", scale=alt.Scale(domain=SUP_LABELS, range=[nd.supplier_colour(k) for k in SUP_ORDER[:-1]]
                                                   + [nd.OTHER_COLOUR]), legend=map_legend("stroke"))
    arcs = (alt.Chart(alt.NamedData("wm_arcs")).mark_line(strokeCap="round", cursor="pointer", interpolate="linear")
            .encode(longitude="x:Q", latitude="y:Q", detail="arc:N", order="t:Q", color=sup,
                    strokeWidth=alt.StrokeWidth("width:Q", scale=None), opacity=alt.Opacity("op:Q", scale=None), tooltip=ARC_TIP)
            .add_params(ARC))
    ends = (alt.Chart(alt.NamedData("wm_arcs")).transform_filter("datum.t == 20 && datum.op > 0.5")
            .mark_circle(color=INK, opacity=.8, size=14).encode(longitude="x:Q", latitude="y:Q"))
    return world_map(flow_info(y, tint), selected, n, alt.Fill("fill:N", scale=None), FLOW_TIP, "stroke", over=[arcs, ends],
                     datasets={"wm_arcs": arc_rows(y, top_n, highlight, n)})


# ---- Arms build-up: bubbles of the arms received in 10 years, coloured by regime type
@st.cache_data
def buildup_points(y):
    roll = nd.arms_rolling_hosted()
    v = roll.loc[y]
    reg = nd.regime_grid().loc[y]
    imp = panel[panel["year"] == y].set_index("iso3")["arms_imports_tiv"]
    p = pd.DataFrame({"v": v[v > 0]}).join(PX[["x", "y"]], how="inner")
    r = reg.reindex(p.index)
    vmax = float(roll.values.max())
    r_map = 1.5 + W_PX / 24 * np.sqrt(p["v"] / vmax)  # radius in map pixels, as BUB.radius in app/site/adc.html
    d = 2 * r_map * MAP_H / H_PX                       # diameter on a map MAP_H px tall (for the labels below)
    p["r_map"] = r_map.round(2)                        # the drawn area follows the map's real size (see buildup_map)
    p["hx"], p["hy"] = p["x"], p["y"]                  # home: the country's point; x/y may drift to avoid overlaps
    p[["x", "y"]] = relax(p[["x", "y"]].to_numpy(float), r_map.to_numpy(float))
    p["moved"] = np.hypot(p["x"] - p["hx"], p["y"] - p["hy"]) > 1
    p["iso3"] = p.index
    p["Country"] = [f"{NAMES.get(i, i)} · 10 years to {y}" for i in p.index]
    p["Regime"] = [REG_LABELS[int(k)] if pd.notna(k) else "No regime data" for k in r]
    p["Regime in the year"] = [REG_LABELS[int(k)] if pd.notna(k) else f"No V-Dem data for {y}" for k in r]
    p["Received in 10 years"] = [f"{fmt(x)} TIV" for x in p["v"]]
    p["Imports in the year"] = [f"{fmt(float(imp.get(i, 0) or 0))} TIV in {y}" for i in p.index]
    p = p.sort_values("v", ascending=False).reset_index(drop=True)
    p["label"] = np.where((d.reindex(p["iso3"]).values > 26) & (np.arange(len(p)) < 14), p["iso3"], "")
    return p


def relax(xy, r, drift=16.0, rounds=60):
    """Push overlapping bubbles apart (bigger ones move less), at most `drift` map pixels from home, as BUB.relax of
    app/site/adc.html (which does it step by step during the animation; here it is done once per year)."""
    home, xy = xy.copy(), xy.copy()
    if len(xy) < 2:
        return xy
    a2 = r ** 2
    for _ in range(rounds):
        xy += (home - xy) * .25
        dx = xy[None, :, 0] - xy[:, None, 0]
        dy = xy[None, :, 1] - xy[:, None, 1]
        dist = np.hypot(dx, dy) + 1e-9
        over = np.triu((r[:, None] + r[None, :] + .5 - dist) * .6, 1)
        over[over < 0] = 0
        ux, uy = dx / dist * over, dy / dist * over
        wa = a2[None, :] / (a2[:, None] + a2[None, :])     # share of the push taken by bubble i (the smaller one moves more)
        xy[:, 0] -= (ux * wa).sum(1) - (ux * (1 - wa)).sum(0)
        xy[:, 1] -= (uy * wa).sum(1) - (uy * (1 - wa)).sum(0)
        off = xy - home
        far = np.hypot(off[:, 0], off[:, 1])
        k = np.where(far > drift, drift / np.maximum(far, 1e-9), 1)
        xy = home + off * k[:, None]
    return xy.round(1)


BLD_TIP = [alt.Tooltip("Country:N"), alt.Tooltip("Received in 10 years:N"), alt.Tooltip("Imports in the year:N"),
           alt.Tooltip("Regime in the year:N", title="Regime")]


@st.cache_data
def buildup_info(y):
    v = nd.arms_rolling_hosted().loc[y]
    isos = list(dict.fromkeys(SHAPED + DOTS))
    return pd.DataFrame({"Country": [f"{NAMES.get(i, i)} · 10 years to {y}" for i in isos],
                         "fill": [NODATA if i in RINGS else "#78746c" for i in isos],
                         "Received in 10 years": [f"{fmt(float(v.get(i, 0) or 0))} TIV" for i in isos],
                         "Imports in the year": "", "Regime in the year": ""}, index=isos)


def buildup_map(y, selected, n):
    """Bubble map of Arms build-up: area = major arms received in the 10 years to `y`, colour = regime type."""
    p = buildup_points(y).assign(n=n)
    colour = alt.Color("Regime:N", scale=alt.Scale(domain=BLD_DOMAIN, range=REG_COLS + [NO_REG]), legend=map_legend("circle"))
    # area in px²: the radius in map pixels times the scale of the drawn map (identity projection fitted to 960 × 423)
    bubbles = (alt.Chart(alt.NamedData("wm_bubbles"))
               .transform_calculate(area=f"PI * pow(datum.r_map * min(width / {W_PX}, height / {H_PX}), 2)")
               .mark_circle(opacity=.9, stroke="#151514", strokeWidth=0.8, cursor="pointer")
               .encode(longitude="x:Q", latitude="y:Q", size=alt.Size("area:Q", scale=None), color=colour,
                       order=alt.Order("v:Q", sort="descending"), tooltip=BLD_TIP)
               .add_params(BUBBLE))
    # a thin line points home where a bubble had to move (as in the HTML map)
    home = (alt.Chart(alt.NamedData("wm_bubbles")).transform_filter("datum.moved")
            .mark_rule(color=INK2, strokeWidth=.8, opacity=.7)
            .encode(longitude="hx:Q", latitude="hy:Q", longitude2="x:Q", latitude2="y:Q"))
    home_dot = (alt.Chart(alt.NamedData("wm_bubbles")).transform_filter("datum.moved")
                .mark_circle(color=INK2, size=8, opacity=.8).encode(longitude="hx:Q", latitude="hy:Q"))
    labels = (alt.Chart(alt.NamedData("wm_bubbles")).transform_filter("datum.label != ''")
              .mark_text(color="#111110", fontSize=10, fontWeight=500, cursor="pointer")
              .encode(longitude="x:Q", latitude="y:Q", text="label:N", tooltip=BLD_TIP)
              .add_params(BUBBLE_LABEL))
    rows = p.to_dict("records") or [{"iso3": "", "n": n, "x": 0.0, "y": 0.0, "hx": 0.0, "hy": 0.0, "moved": False, "v": 0.0,
                                     "r_map": 0.0, "Regime": "No regime data",
                                     "label": "", "Country": "", "Received in 10 years": "", "Imports in the year": "",
                                     "Regime in the year": ""}]
    return world_map(buildup_info(y), selected, n, alt.Fill("fill:N", scale=None), BLD_TIP, "circle",
                     over=[home, home_dot, bubbles, labels], datasets={"wm_bubbles": rows})


BLD_ROW = alt.selection_point(name="bld_row", fields=["iso3", "n"], on="click", empty=False)
BLD_ROW_HOVER = alt.selection_point(name="bld_row_hover", fields=["k"], on="pointerover", clear="pointerout", empty=False)


def buildup_top(y, n):
    """Side panel of Arms build-up: the 10 largest build-ups as rows (rank, name, bar coloured by regime, TIV), as the
    .sp-list of the HTML version. A click on a row opens the country card."""
    v = nd.arms_rolling_hosted().loc[y]
    top = v[v > 0].nlargest(10)
    reg = nd.regime_grid().loc[y]
    d = pd.DataFrame({"k": range(len(top)), "rank": [str(k + 1) for k in range(len(top))], "iso3": list(top.index),
                      "name": [NAMES.get(i, i) for i in top.index], "v": top.values,
                      "Regime": [REG_LABELS[int(reg[i])] if pd.notna(reg.get(i)) else "No regime data" for i in top.index],
                      "n": n})
    d["val"] = [fmt(x) for x in d["v"]]
    d["Country"] = [f"{nm} · {y - 9}–{y}" for nm in d["name"]]
    d["Received"] = [f"{fmt(x)} TIV of major arms" for x in d["v"]]
    d["Regime in the year"] = [f"{r} in {y}" if r != "No regime data" else f"No V-Dem data in {y}" for r in d["Regime"]]
    d["vmax"] = float(top.max())
    yk = alt.Y("k:O", axis=None, scale=alt.Scale(domain=list(range(10)), paddingInner=0, paddingOuter=0))
    xs = alt.Scale(domain=[0, float(top.max())], nice=False, zero=True,
                   range=[alt.ExprRef("width * 0.6"), alt.ExprRef("width - 64")])
    tip = [alt.Tooltip("Country:N"), alt.Tooltip("Received:N", title="Received"), alt.Tooltip("Regime in the year:N", title="Regime")]
    row = (alt.Chart(d).mark_rect(color=INK, cornerRadius=4, cursor="pointer")
           .encode(x=alt.value(0), x2=alt.value("width"), y=yk,
                   opacity=alt.condition(BLD_ROW_HOVER, alt.value(.06), alt.value(0.001)), tooltip=tip)
           .add_params(BLD_ROW, BLD_ROW_HOVER))
    track = alt.Chart(d).mark_bar(height=10, cornerRadius=3, color="#111110").encode(
        x=alt.X("vmax:Q", scale=xs, axis=None), x2=alt.value(alt.ExprRef("width * 0.6")), y=yk)
    bar = alt.Chart(d).mark_bar(height=10, cornerRadius=3).encode(
        x=alt.X("v:Q", scale=xs, axis=None), x2=alt.value(alt.ExprRef("width * 0.6")), y=yk,
        color=alt.Color("Regime:N", scale=alt.Scale(domain=BLD_DOMAIN, range=REG_COLS + [NO_REG]), legend=None))
    rank = alt.Chart(d).mark_text(align="left", color=MUTED, fontSize=12, font="IBM Plex Mono, ui-monospace, monospace").encode(
        x=alt.value(4), y=yk, text="rank:N")
    name = alt.Chart(d).mark_text(align="left", color=INK, fontSize=13, limit=alt.ExprRef("width * 0.6 - 36")).encode(
        x=alt.value(28), y=yk, text="name:N")
    val = alt.Chart(d).mark_text(align="right", color=INK, fontSize=12, fontWeight=500,
                                 font="IBM Plex Mono, ui-monospace, monospace").encode(x=alt.value("width"), y=yk, text="val:N")
    layers = alt.layer(row, track, bar, rank, name, val).properties(padding={"left": 0, "right": 4, "top": 0, "bottom": 0})
    return alt_finish(layers, SIDE_H - 64)


@st.cache_data
def regime_counts():
    """Countries per regime type (columns 0-3) per year."""
    return panel.pivot_table(index="year", columns="regime_type", values="iso3", aggfunc="count").reindex(range(Y0, Y1 + 1)).fillna(0)


def regime_bars(y):
    """Side panel of Regimes: one bar per regime type (liberal democracy on top), on one scale for all years."""
    rc = regime_counts()
    row, vmax = rc.loc[y], float(rc.values.max())
    tot = row.sum()
    d = pd.DataFrame({"k": range(4), "Regime": [REG_LABELS[r] for r in (3, 2, 1, 0)],
                      "n": [int(row.get(r, 0)) for r in (3, 2, 1, 0)], "vmax": vmax})
    d["tip"] = [f"{n} of {int(tot)} countries ({pct(n, tot)})" for n in d["n"]]
    yk = alt.Y("k:O", axis=None, scale=alt.Scale(paddingInner=0, paddingOuter=0))
    x = alt.X("n:Q", axis=None, scale=alt.Scale(domain=[0, vmax], nice=False, zero=True))
    track = alt.Chart(d).mark_bar(size=16, cornerRadius=3, color=LINE, opacity=.6).encode(x=alt.X("vmax:Q", axis=None,
                                                                                          scale=alt.Scale(domain=[0, vmax])), y=yk)
    bars = (alt.Chart(d).mark_bar(size=16, cornerRadius=3)
            .encode(x=x, y=yk, color=alt.Color("Regime:N", scale=alt.Scale(domain=[REG_LABELS[r] for r in (3, 2, 1, 0)],
                                                                          range=[REG_COLS[r] for r in (3, 2, 1, 0)]), legend=None),
                    tooltip=[alt.Tooltip("Regime:N"), alt.Tooltip("tip:N", title=f"Countries in {y}")]))
    names = alt.Chart(d).mark_text(align="left", baseline="bottom", dy=-11, dx=2, color=INK2, fontSize=12).encode(
        x=alt.value(0), y=yk, text="Regime:N")
    counts = alt.Chart(d).mark_text(align="right", baseline="bottom", dy=-11, color=INK, fontSize=13, fontWeight=600).encode(
        x=alt.value("width"), y=yk, text="n:Q")
    return alt_finish(alt.layer(track, bars, names, counts), 200)


@st.cache_data
def supplier_river():
    t = flows.copy()
    t["group"] = np.where(t["supplier"].isin(list(nd.SUPPLIER_COLOURS)), t["supplier"], "Other")
    return t.pivot_table(index="year", columns="group", values="tiv", aggfunc="sum").reindex(range(Y0, Y1 + 1)).fillna(0)


# "cur" is the year shown, so a click on the year picked before (and since left by Play) is a new selection
YEAR_PICK = alt.selection_point(name="year_pick", fields=["year", "cur"], on="click", empty=False, clear=False)
YEAR_HOVER = alt.selection_point(name="year_hover", fields=["year"], on="pointerover", clear="pointerout", empty=False)


@st.cache_data
def river_data(series, unit):
    """Long table of a river (one row per series and year, first series at the bottom) and the hover tooltip per year."""
    years = list(range(Y0, Y1 + 1))
    vals = pd.DataFrame({name: s.reindex(years).fillna(0) for name, s in series.items()}, index=years)
    tot = vals.sum(axis=1)
    shares = (vals.div(tot.replace(0, np.nan), axis=0) * 100).fillna(0)
    long = vals.stack().rename("value").reset_index()
    long.columns = ["year", "series", "value"]
    long["share"] = shares.stack().values
    long["k"] = long["series"].map({n: k for k, n in enumerate(series)})
    tips = pd.DataFrame({"year": years, "x0": [v - .5 for v in years], "x1": [v + .5 for v in years]})
    for k, name in enumerate(series):
        tips[f"s{k}"] = [f"{v:,.0f} {unit} ({sh:.0f}%)" for v, sh in zip(vals[name], shares[name])]
    return long, tips


@st.cache_data
def river_labels(long, share, ph):
    """Where to write each band's name: its thickest year (kept clear of the ends), the middle of the band, only if the
    band is at least 12 px thick there and the label does not collide with one already placed (the labels of stackView in
    app/site/flows.js). About 8.5 px per year (the river is about 640 px wide beside the side panel)."""
    field = "share" if share else "value"
    wide = long.pivot(index="year", columns="series", values=field)
    order = long.drop_duplicates("series").sort_values("k")["series"].tolist()
    wide = wide[order]
    top = 100.0 if share else float(wide.sum(axis=1).max()) or 1.0
    base = wide.cumsum(axis=1) - wide
    ppy = 8.5
    note_hw = len("Soviet Union ends (1991)") * 2.9 / ppy  # the 1991 note at the top of the plot is kept clear too
    out, placed = [], [(1991.5 + note_hw, top * (1 - 9 / ph), note_hw)]
    for name in order:
        col = wide[name]
        yr = int(col.idxmax())
        if col.max() / top * ph < 12:
            continue
        hw = (len(name) * 3.2 + 4) / ppy  # half the label's width, in years
        x = min(max(yr, Y0 + hw), Y1 - hw)
        mid = float(base.loc[yr, name] + col.loc[yr] / 2)
        if any(abs(px - x) < phw + hw and abs(py - mid) / top * ph < 13 for px, py, phw in placed):
            continue
        placed.append((x, mid, hw))
        out.append({"year": x, "mid": mid, "series": name})
    return pd.DataFrame(out or [{"year": 0.0, "mid": 0.0, "series": ""}])


def river(series, colours, y, unit, label, share=False, key=None, height=155):
    """Stacked river of time, 1950 to 2025, with the year marked. A click sets the year."""
    long, tips = river_data(series, unit)
    tips = tips.assign(cur=y)
    names = list(series)
    ph = height - 26  # plot height; the padding above holds the headline
    x = alt.X("year:Q", scale=alt.Scale(domain=[Y0, Y1], nice=False, zero=False),
              axis=alt.Axis(values=list(range(1950, 2030, 10)), format="d", grid=False, title=None, labelColor=MUTED))
    field = "share" if share else "value"
    yax = alt.Axis(title="% of world" if share else unit, tickCount=4, grid=True, domain=False, ticks=False,
                   labelExpr="datum.value + '%'" if share else "format(datum.value, '~s')")
    yy = alt.Y(f"{field}:Q", stack="zero", axis=yax,
               scale=alt.Scale(domain=[0, 100], nice=False) if share else alt.Scale(nice=True))
    area = (alt.Chart(long).mark_area(opacity=.88, stroke=None, interpolate="linear")
            .encode(x=x, y=yy, order=alt.Order("k:Q"), color=alt.Color("series:N", legend=None,
                                                                         scale=alt.Scale(domain=names, range=list(colours)))))
    # one invisible column per year: hover shows every series of that year, a click picks the year
    cols = (alt.Chart(tips).mark_rect(color=INK, cursor="pointer", clip=True)
            .encode(x="x0:Q", x2="x1:Q", y=alt.value(0), y2=alt.value(ph),
                    opacity=alt.condition(YEAR_HOVER, alt.value(.07), alt.value(0.001)),
                    tooltip=[alt.Tooltip("year:Q", title="Year", format="d")]
                    + [alt.Tooltip(f"s{k}:N", title=n) for k, n in reversed(list(enumerate(names)))])
            .add_params(YEAR_PICK, YEAR_HOVER))
    marks = pd.DataFrame({"year": [1991, y], "kind": ["ussr", "now"]})
    ussr = alt.Chart(marks[marks["kind"] == "ussr"]).mark_rule(color=MUTED, strokeDash=[2, 3], strokeWidth=1).encode(x="year:Q")
    now = alt.Chart(marks[marks["kind"] == "now"]).mark_rule(color=INK, strokeWidth=2).encode(x="year:Q")
    # names written on the bands, at each band's thickest year, and the 1991 note inside the plot (as the HTML rivers)
    band_names = alt.Chart(river_labels(long, share, ph)).mark_text(color=INK, fontSize=11, fontWeight=500).encode(
        x="year:Q", y=alt.Y("mid:Q", axis=yax),
        text="series:N")
    ussr_note = alt.Chart(marks[marks["kind"] == "ussr"]).mark_text(text="Soviet Union ends (1991)", color=INK2, fontSize=11,
                                                                    align="left", baseline="top", dx=4, dy=2).encode(
        x="year:Q", y=alt.value(0))
    layers = [area, band_names, ussr, ussr_note, now, cols]
    align = "left" if y < Y0 + 12 else "right" if y > Y1 - 12 else "center"
    layers.append(alt.Chart(marks[marks["kind"] == "now"]).mark_text(text=label, color=INK, fontSize=12, font="IBM Plex Mono, ui-monospace, monospace",
                                                                      fontWeight="bold", baseline="bottom", dy=-4, align=align)
                  .encode(x="year:Q", y=alt.value(0)))
    chart = alt_finish(alt.layer(*layers).properties(padding={"left": 4, "right": 8, "top": 22, "bottom": 4}), ph)

    def clicked():
        pts = ((ss[key].get("selection") or {}).get("year_pick")) or []
        if pts and pts[0].get("year") is not None:
            set_year(round(pts[0]["year"]))

    st.altair_chart(chart, key=key, on_select=clicked, selection_mode="year_pick", width="stretch",
                    alt="River of time, 1950 to 2025. Click a year to show it.")


def stat(col, label, value, help=None):
    """A number with its label below, as the .stat blocks of the HTML version."""
    col.markdown(f"**{value}**  \n:small[:gray[{label}]]", help=help)


def side_header(title, note):
    st.markdown(f"**{title}**  \n:gray[{note}]")


def country_card(iso, y):
    """Card of one country in the year (Regimes and Arms build-up): regime, conflict, arms imports and exports."""
    g = panel[(panel["iso3"] == iso) & (panel["year"] == y)]
    with st.container(horizontal=True, vertical_alignment="center", gap="small"):
        st.markdown(f"**{NAMES[iso]}** · {y}", width="stretch")
        st.button("Compare", icon=":material/compare_arrows:", key="wm_open_cmp", type="tertiary", on_click=open_in_compare,
                  args=(iso,), help="Open this country in Countries & compare")
        st.button("", icon=":material/close:", key="wm_card_x", type="tertiary", on_click=close_card, help="Close the card")
    if g.empty:
        st.caption(f"No V-Dem data for {NAMES[iso]} in {y}.")
    else:
        r = g.iloc[0]
        conflict = ("war (1,000+ deaths)" if r["max_intensity"] == 2 else "minor armed conflict" if r["max_intensity"] == 1
                    else "no armed conflict")
        idx = round(float(r["democracy_index"]) + 1e-9, 2)  # rounded half up, as the map's tooltip
        st.caption(f"{str(r['regime_label']).capitalize()} · democracy index {idx:.2f} · {conflict}")
    f = flows[flows["year"] == y]
    imp = f[f["recipient_iso3"] == iso].groupby("supplier")["tiv"].sum().sort_values(ascending=False)
    imp_total = float(g["arms_imports_tiv"].iloc[0]) if len(g) and pd.notna(g["arms_imports_tiv"].iloc[0]) else imp.sum()
    exp = f[(f["supplier_iso3"] == iso)].groupby("recipient_iso3")["tiv"].sum().sort_values(ascending=False)
    a, b = st.columns(2)
    if mode == "Arms build-up":
        a.metric("Received in 10 years", fmt(nd.arms_rolling_hosted().loc[y].get(iso, 0)), help=f"TIV of major arms received {y - 9}–{y}")
        b.metric(f"Imports {y}", fmt(imp_total), help="TIV")
    else:
        a.metric(f"Imports {y}", fmt(imp_total), help="TIV of major arms received")
        b.metric(f"Exports {y}", fmt(exp.sum()), help="TIV of major arms delivered")

    if len(imp):
        t = pd.DataFrame({"Main suppliers": imp.index, "TIV": imp.values}).head(3)
        st.dataframe(t, hide_index=True, height=35 * len(t) + 38, column_config={
            "TIV": st.column_config.ProgressColumn("TIV", format="%.0f", min_value=0, max_value=float(imp.max()))})
    else:
        st.caption(f"No major arms imports in {y}.")
    if len(exp):
        st.caption("Main recipients: " + ", ".join(f"{NAMES.get(i, i)} {fmt(v)}" for i, v in exp.head(3).items())
                   + (f" and {len(exp) - 3} more" if len(exp) > 3 else ""))


# ------------------------------------------------------------------ pinned country card of the chord ring (Arms flows)
# ss["wm_pin"] is a card key ("r:ISO3" or "s:Supplier"). Set by the sidebar "Country details" (when it changes), by a
# click on the map (a country or an arc: its recipient) or on a country node of the ring; cleared by the card's ×.
_UNSET = object()
if ss.get("_wm_card_prev", _UNSET) != card_iso:
    ss["_wm_card_prev"] = card_iso
    ss["_wm_card_n"] = ss.get("_wm_card_n", 0) + 1
    ss["wm_pin"] = f"r:{card_iso}" if card_iso else None


def chord_pin():
    ss["wm_pin"] = ss["wm_chord"].pin


def chord_close():
    ss["wm_pin"] = None


MAP_KEY = {"Regimes": "wm_map_reg", "Arms flows": "wm_map_flow", "Arms build-up": "wm_map_bld"}


def map_clicked():
    """A click on the map: a country, a dot, a stripe, a bubble or (Arms flows) a delivery line, whose recipient is picked.
    Arms flows pins the card of the chord ring; the other modes open the country card."""
    sel = ss[MAP_KEY[mode]].get("selection") or {}
    for name in MAP_SELECTIONS[mode]:
        pts = sel.get(name) or []
        iso = pts[0].get("iso3") if pts else None
        if iso:
            iso = nd.HISTORICAL.get(iso, iso)
            if mode == "Arms flows":
                if iso in NAMES:
                    ss["wm_pin"] = "r:" + iso
            else:
                pick_country(iso)
            return


def buildup_row_clicked():
    pts = (ss["bld_top_chart"].get("selection") or {}).get("bld_row") or []
    if pts and pts[0].get("iso3"):
        pick_country(pts[0]["iso3"])


# ------------------------------------------------------------------ the map card (re-run on its own while playing)
@st.fragment(run_every=PACE[mode] / SPEEDS[speed] if ss["playing"] else None)
def map_card():
    if ss.pop("_wm_go", None):
        st.switch_page(COMPARE)
    if ss.pop("_wm_full", False):  # a click picked a year or a country: redraw the sidebar too (outside this fragment)
        st.rerun(scope="app")
    p0, p1 = period()
    if ss["playing"]:
        if ss["year"] >= p1:
            ss["playing"] = False
            ss["wm_year_slider"] = ss["year"]
            st.rerun(scope="app")
        ss["year"] += 1
    y = ss["year"]
    g = panel[panel["year"] == y]

    with st.container(border=True):
        title, modes = st.columns([1, 1], vertical_alignment="center")
        title.subheader(f"{TITLES[mode]} in {y}", anchor=False)
        with modes.container(horizontal=True, horizontal_alignment="right"):
            st.segmented_control("Map shows", MODES, key="wm_mode", required=True, on_change=full_rerun,
                                 label_visibility="collapsed")
        # the year bar, pinned to the bottom of the screen (st.bottom): Play, speed, year and period; the slider follows Play
        with year_bar:
            with st.container(horizontal=True, vertical_alignment="center", gap="medium"):
                st.button("Pause" if ss["playing"] else "Play", icon=":material/pause:" if ss["playing"] else ":material/play_arrow:",
                          type="primary", on_click=toggle_play, key="wm_play")
                st.segmented_control("Speed", list(SPEEDS), key="wm_speed", required=True, on_change=full_rerun,
                                     label_visibility="collapsed", help="Play speed")
                ss["wm_year_slider"] = y
                # as the HTML year bar: "Year", the slider, the year in large digits, then "Period" and its buttons
                st.caption("Year", width="content")
                st.slider("Year", p0, p1, key="wm_year_slider", on_change=slider_moved, label_visibility="collapsed",
                          width="stretch")
                st.markdown(f"### {y}", width="content")
                st.caption("Period", width="content")
                st.segmented_control("Period", list(PERIODS), key="wm_period", required=True, on_change=clamp_year,
                                     label_visibility="collapsed", help="Limits the year slider and Play to this period.")

        pin = ss.get("wm_pin") or ""
        pin_iso = pin[2:] if pin.startswith("r:") else nd.SUPPLIER_ISO.get(pin[2:]) if pin.startswith("s:") else None
        # one map for the three modes: same chart, size, projection and legend box; the badge below always takes one line
        n = f"{ss.get('_wm_card_n', 0)}|{pin}"
        # as the HTML: map | side panel (Arms flows: 62 | 38 with the chord ring; the others: regime bars or the top-10
        # list in a narrower column, so the map stays larger than in the HTML), then the river of time at full width.
        # The map's height follows its width, so it grows with the screen.
        if mode == "Arms flows":
            left, right = st.columns([62, 38], gap="medium")
        else:
            left, right = st.columns([3.2, 1], gap="medium", vertical_alignment="center")
        with left:
            if mode == "Regimes":
                chart = regimes_map(y, show_conflict, card_iso, n)
                badge = (f"Striped: active armed conflict in {y} (denser stripes: war)" if show_conflict
                         else f"Dark grey: no V-Dem data for {y}")
            elif mode == "Arms flows":
                chart = flows_map(y, top_n, tint, highlight, pin_iso, n)
                f = year_flows(y)
                drawn = f[f["drawable"]].head(top_n)
                badge = ("No deliveries in " + str(y) if f.empty else
                         f"Top {len(drawn)} of {len(f):,} deliveries shown ({pct(drawn['tiv'].sum(), f['tiv'].sum())} of this year's TIV)")
            else:
                chart = buildup_map(y, card_iso, n)
                badge = f"Bubble area: major arms received {y - 9}–{y} (same scale for all years)"
            st.vega_lite_chart(chart, key=MAP_KEY[mode], on_select=map_clicked, selection_mode=MAP_SELECTIONS[mode],
                            width="stretch", alt=f"World map: {TITLES[mode].lower()} in {y}. Click a country for its card.")
            st.badge(badge, color="gray")
        riv_col = st.container()
        with right:
            with st.container(height=SIDE_H if mode == "Arms flows" else "content", border=False):
                if mode == "Arms flows":
                    if pin_iso in NAMES:  # a pinned country: its card can open the compare page
                        st.markdown(f"**Who supplied whom in {y}**")
                        st.button(f"Open {NAMES[pin_iso]} in Countries & compare", icon=":material/compare_arrows:",
                                  type="tertiary", key="wm_pin_cmp", on_click=open_in_compare, args=(pin_iso,))
                    else:
                        side_header(f"Who supplied whom in {y}", "Hover a country, click to pin its card")
                    chord_ring(y, pinned=ss.get("wm_pin"), height=SIDE_H - 94, key="wm_chord",
                               tween_ms=int(min(800, 700 * PACE[mode] / SPEEDS[speed])), on_pin=chord_pin, on_close=chord_close)
                elif card_iso is not None:
                    country_card(card_iso, y)
                elif mode == "Regimes":
                    rc = regime_counts().loc[y]
                    side_header(f"Regimes in {y}", f"Number of countries ({int(rc.sum())} with data)")
                    st.altair_chart(regime_bars(y), key="reg_bars", width="stretch",
                                    alt="Bars of the number of countries per regime type in the year")
                    a, b = st.columns(2)
                    stat(a, "with armed conflict", int(g["conflict_active"].sum()))
                    stat(b, "of them at war", int((g["max_intensity"] == 2).sum()))
                else:
                    side_header(f"Largest build-ups, {y - 9}–{y}", "TIV received in 10 years")
                    v = nd.arms_rolling_hosted().loc[y]
                    top = v[v > 0].nlargest(10)
                    ss["_wm_bld_top"] = list(top.index)
                    if top.empty:
                        st.info(f"No major arms received in {y - 9}–{y}.", icon=":material/info:")
                    else:
                        st.altair_chart(buildup_top(y, n), key="bld_top_chart", on_select=buildup_row_clicked,
                                        selection_mode="bld_row", width="stretch",
                                        alt=f"The 10 countries that received the most major arms in {y - 9}–{y}")

        # river of time: click a year to jump there
        with riv_col:
            if mode == "Regimes":
                rc = regime_counts()
                row = rc.loc[y]
                river({REG_LABELS[i]: rc.get(i, pd.Series(0, index=rc.index)) for i in range(4)}, REG_COLS, y, "countries",
                      f"{y} · {int(row.get(2, 0) + row.get(3, 0))} of {int(row.sum())} democracies · "
                      f"{int(g['conflict_active'].sum())} in armed conflict, "
                      f"{int((g['max_intensity'] == 2).sum())} at war", key="riv_reg")
            elif mode == "Arms flows":
                sup = supplier_river()
                river({("Other suppliers" if k == "Other" else k): sup.get(k, pd.Series(0, index=sup.index)) for k in SUP_ORDER},
                      [nd.supplier_colour(k) for k in SUP_ORDER], y, "TIV", f"{y} · {fmt(sup.loc[y].sum())} TIV", share=share,
                      key="riv_sup")
            else:
                b = nd.buildup_rows()
                river({**{REG_LABELS[i]: b[i] for i in range(4)}, "No regime data": b[4]}, REG_COLS + ["#5b5850"], y, "TIV, 10 years",
                      f"{y} · {fmt(b.loc[y].sum())} TIV received {y - 9}–{y}", key="riv_bld")

        # numbers of the year
        m = st.columns(4)
        if mode == "Arms flows":
            f = flows[(flows["year"] == y) & (flows["tiv"] > 0)]
            ts = f[~f["supplier"].map(nd.is_non_state)].groupby("supplier")["tiv"].sum()
            tr = f.groupby("recipient_iso3")["tiv"].sum()
            stat(m[0], "TIV delivered", fmt(f["tiv"].sum()))
            stat(m[1], "transfers (supplier to recipient)", fmt(len(f)))
            stat(m[2], f"top supplier ({fmt(ts.max())} TIV)" if len(ts) else "top supplier", ts.idxmax() if len(ts) else "–")
            stat(m[3], f"top recipient ({fmt(tr.max())} TIV)" if len(tr) else "top recipient",
                 NAMES.get(tr.idxmax(), tr.idxmax()) if len(tr) else "–")
        elif mode == "Arms build-up":
            row = nd.buildup_rows().loc[y]
            tot = row.sum()
            v = nd.arms_rolling_hosted().loc[y]
            stat(m[0], f"TIV received worldwide, {y - 9}–{y}", fmt(tot))
            stat(m[1], "countries that received major arms", int((v > 0).sum()))
            stat(m[2], f"went to democracies (regime in {y})", pct(row[2] + row[3], tot))
            stat(m[3], f"went to autocracies (regime in {y})", pct(row[0] + row[1], tot))
        else:
            rc = regime_counts().loc[y]
            top = g.nlargest(1, "arms_imports_tiv")
            has_top = len(top) and top["arms_imports_tiv"].iloc[0] > 0
            stat(m[0], "democracies", int(rc.get(2, 0) + rc.get(3, 0)))
            stat(m[1], "autocracies", int(rc.get(0, 0) + rc.get(1, 0)))
            stat(m[2], "TIV of major arms imported", fmt(g["arms_imports_tiv"].sum()))
            stat(m[3], f"largest importer ({fmt(top['arms_imports_tiv'].iloc[0])} TIV)" if has_top else "largest importer",
                 top["country_name"].iloc[0] if has_top else "–")

        st.caption(NOTES[mode])
        num = st.expander("Show the numbers", on_change="rerun", key="wm_numbers")
        if num.open:  # the table is only built while the expander is open
            with num:
                numbers(y)


def numbers(y):
    """The table behind the map of the year, per mode (ovTable and the flows table in app/site/adc.html)."""
    if mode == "Arms flows":
        f = year_flows(y)
        if f.empty:
            st.info(f"No deliveries in {y}.", icon=":material/info:")
            return
        tot = f["tiv"].sum()
        st.dataframe(pd.DataFrame({"Supplier": f["supplier"], "Recipient": f["recipient"], "TIV": f["tiv"],
                                   f"Share of {y}": f["tiv"] / tot * 100}), hide_index=True, height=280, column_config={
            "TIV": st.column_config.NumberColumn(format="%,.1f"),
            f"Share of {y}": st.column_config.NumberColumn(format="%.1f%%")})
    elif mode == "Arms build-up":
        v = nd.arms_rolling_hosted().loc[y]
        top = v[v > 0].nlargest(40)
        if top.empty:
            st.info(f"No major arms received in {y - 9}–{y}.", icon=":material/info:")
            return
        reg = nd.regime_grid().loc[y]
        st.dataframe(pd.DataFrame({"#": range(1, len(top) + 1), "Country": [NAMES.get(i, i) for i in top.index],
                                   f"Regime in {y}": [REG_LABELS[int(reg[i])] if pd.notna(reg.get(i)) else "No data" for i in top.index],
                                   f"TIV {y - 9}–{y}": top.values}), hide_index=True, height=280,
                     column_config={f"TIV {y - 9}–{y}": st.column_config.NumberColumn(format="%,.0f")})
    else:
        rc = regime_counts().loc[y]
        tot = rc.sum()
        rows = [(REG_LABELS[r], int(rc.get(r, 0)), rc.get(r, 0) / tot * 100 if tot else 0) for r in (3, 2, 1, 0)]
        rows.append(("All countries with data", int(tot), 100.0))
        st.dataframe(pd.DataFrame(rows, columns=[f"Regime type, {y}", "Countries", "Share"]), hide_index=True,
                     column_config={"Share": st.column_config.NumberColumn(format="%.0f%%")})


st.header("What happens to democracy during and after armed conflict?", anchor=False)
st.caption("Regimes (V-Dem), armed conflicts (UCDP) and arms transfers (SIPRI), 1950 to 2025. Hover for details, click a "
           "country for its card.")
year_bar = st.bottom.container()  # filled by the map card, so Play and the year stay in view while scrolling
map_card()


# ------------------------------------------------------------------ main finding: the A1 regression of notebook 08
# (no split into high and low importers: arms imports before the onset enter the model as one standardised variable)
res, res_src = nr.load("reg_results")
a1 = nr.a1_main(res)
with st.container(border=True):
    txt, chart = st.columns([1, 1.5], gap="large")
    with txt:
        st.markdown(":primary[:small[**MAIN FINDING**]]")
        with st.container(horizontal=True, vertical_alignment="center"):
            st.subheader("Democracy after a conflict starts", anchor=False, width="content")
            if res_src == "demo":
                st.badge("Placeholder", icon=":material/science:", color="orange")
        st.caption("Regression (model A1 of notebook 08): change in the democracy index k years after a conflict starts, "
                   "compared with the year before. Arms imports of the 5 years before the onset enter as one continuous, "
                   "standardised variable (onset × arms imports), with country and year fixed effects, so there is no "
                   "cut-off between high and low importers. Shaded: 95% confidence band.")
        st.markdown(":material/arrow_downward: Below the zero line = less democratic than just before the conflict began.")
        sentence = nr.a1_sentence(a1, k=5)
        if sentence:
            st.markdown(sentence)
        if res_src == "demo":
            st.caption(":material/science: " + nr.PLACEHOLDER_TEXT)
        if st.button("See the regression results", icon=":material/arrow_forward:", type="tertiary", key="wm_to_findings"):
            st.switch_page("native_pages/findings.py")
    with chart:
        if a1.empty:
            st.info("Not available yet: the A1 models of notebook 08 have not been run.", icon=":material/hourglass_empty:")
        else:
            st.markdown(nr.a1_legend())
            st.altair_chart(nr.a1_chart(a1, height=320), key="wm_finding", width="stretch",
                            alt="Change in the democracy index 1 to 10 years after a conflict starts: average arms imports "
                                "and one standard deviation more")
    if not a1.empty:
        with st.expander("Show the numbers"):
            st.dataframe(pd.DataFrame({
                "Years after onset": a1["k"],
                "Average arms imports": [nr.sgn(v) for v in a1["b1"]],
                "95% CI": [nr.ci_text(a, b) for a, b in zip(a1["b1_lo"], a1["b1_hi"])],
                "Per sd more arms imports": [nr.sgn(v) for v in a1["b2"]],
                "95% CI ": [nr.ci_text(a, b) for a, b in zip(a1["b2_lo"], a1["b2_hi"])],
                "One sd more, in total": [nr.sgn(v) for v in a1["sum"]],
                "Country-years": a1["n_obs"], "Countries": a1["n_countries"],
            }), hide_index=True, height=250)

# ------------------------------------------------------------------ data sources
head, link = st.columns([3, 1], vertical_alignment="bottom")
head.markdown(":primary[**Data sources**]")
with link:
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("How the data is combined", icon=":material/arrow_forward:", type="tertiary", key="wm_to_about"):
            st.switch_page("native_pages/about.py")
for col, (title, text) in zip(st.columns(3, gap="large"), [
    ("UCDP/PRIO Armed Conflict v26.1", "Conflicts with at least 25 battle deaths in a year. Type and intensity per conflict-year."),
    ("V-Dem v16 (Core)", "Electoral democracy index from 0 to 1 and the four-category Regimes of the World classification."),
    ("SIPRI Arms Transfers", "Deliveries of major conventional arms in trend-indicator values (TIV). TIV measures military "
                             "capability, not price."),
]):
    col.markdown(f"**{title}**")
    col.caption(text)
