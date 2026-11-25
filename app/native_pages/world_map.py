"""World map: regimes, arms flows and arms build-up from 1950 to 2025, with Play through the years.

Same content as the World map page of app/site/adc.html. Charts: the regimes map with striped conflicts and the chord
ring are the two custom components of app/native_components/; the arms-flows map is pydeck; the build-up map, the
side bars and the rivers of time are Plotly. Controls live in the sidebar; Play advances the year for the whole map
card (map, side panel, river and numbers together) by re-running one fragment.
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pydeck as pdk
import streamlit as st

import native_data as nd
import native_results as nr
from native_components.chord import chord_ring
from native_components.regime_map import regime_map as regime_svg_map

Y0, Y1 = 1950, 2025
BG = "rgba(0,0,0,0)"
INK, INK2, MUTED, LINE, NODATA = "#f0efec", "#c3c2b7", "#959086", "#2c2c2a", "#2a2a28"
FONT = "IBM Plex Sans"
MODES = ["Regimes", "Arms flows", "Arms build-up"]
TITLES = {"Regimes": "Regimes and conflicts", "Arms flows": "Arms deliveries", "Arms build-up": "Arms build-up"}
PERIODS = {"1950–2025": (1950, 2025), "Cold War": (1950, 1991), "Since 1992": (1992, 2025)}
SPEEDS = {"0.5×": 0.5, "1×": 1.0, "2×": 2.0}
PACE = {"Regimes": 0.6, "Arms flows": 1.5, "Arms build-up": 1.0}  # seconds per year at 1×, calmer for the busier maps
MAP_H = 330           # map height; the whole map card fits a 1440 × 900 screen
SIDE_H = MAP_H + 50   # side panel: as tall as the map plus its legend line
COMPARE = "native_pages/compare.py"
TIV_NOTE = ("SIPRI trend-indicator values (TIV) measure military capability transferred, not money. "
            "Historical states are drawn at today's borders (Soviet Union at Russia).")
NOTES = {
    "Regimes": "Grey: no V-Dem data for that year. Small states without a shape on the map are drawn as dots.",
    "Arms flows": "Line width = TIV delivered; country tint = main supplier over the last 5 years. " + TIV_NOTE,
    "Arms build-up": "Bubble area = major arms received in the previous 10 years (SIPRI TIV, same scale for all years); "
                     "colour = regime type. Historical states count with today's country (e.g. East Germany with Germany).",
}

panel = nd.load_panel()
points = nd.country_points()
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
def legend_strip(items, per_row=4):
    """A colour legend (name, colour) in rows of `per_row`, drawn with Plotly, for the pydeck map that has none."""
    rows = (len(items) + per_row - 1) // per_row
    xs = [(k % per_row) / per_row for k in range(len(items))]
    ys = [rows - 1 - k // per_row for k in range(len(items))]
    fig = go.Figure(go.Scatter(x=xs, y=ys, mode="markers+text", text=[n for n, _ in items], textposition="middle right",
                               textfont=dict(color=INK2, family=FONT, size=12), hoverinfo="skip", cliponaxis=False,
                               marker=dict(symbol="square", size=10, color=[c for _, c in items])))
    fig.update_layout(height=22 * rows, margin=dict(l=6, r=0, t=0, b=0), paper_bgcolor=BG, plot_bgcolor=BG, showlegend=False,
                      xaxis=dict(visible=False, range=[-0.01, 1], fixedrange=True),
                      yaxis=dict(visible=False, range=[-0.5, rows - 0.5], fixedrange=True))
    return fig


@st.cache_data
def buildup_map(y):
    roll = nd.arms_rolling_hosted()
    v = roll.loc[y]
    reg = nd.regime_grid().loc[y]
    imp = panel[panel["year"] == y].set_index("iso3")["arms_imports_tiv"]
    p = pd.DataFrame({"v": v[v > 0]}).join(points, how="inner")
    p["r"] = reg.reindex(p.index)
    vmax = float(roll.values.max())
    p["size"] = 3 + 62 * np.sqrt(p["v"] / vmax)
    p["name"] = [NAMES.get(i, i) for i in p.index]
    p["tip"] = [f"<b>{n} · 10 years to {y}</b><br>{fmt(val)} TIV of major arms received<br>Arms imports in {y}: "
                f"{fmt(imp.get(i, 0) or 0)} TIV<br>" + (REG_LABELS[int(r)] if pd.notna(r) else f"No V-Dem data for {y}")
                for i, n, val, r in zip(p.index, p["name"], p["v"], p["r"])]
    p = p.sort_values("v", ascending=False)
    labelled = set(p.index[(p["size"] > 26)][:14])
    fig = go.Figure()
    groups = [(REG_LABELS[k], REG_COLS[k], p["r"] == k) for k in range(4)] + [("No regime data", "#5b5850", p["r"].isna())]
    for name, col, m in groups:
        g = p[m]
        fig.add_trace(go.Scattergeo(
            lon=g["lon"], lat=g["lat"], mode="markers+text", name=name, customdata=g.index, text=[i if i in labelled else "" for i in g.index],
            textfont=dict(color="#111110", size=10, family=FONT), hovertext=g["tip"], hoverinfo="text",
            marker=dict(size=g["size"], color=col, opacity=.9, line=dict(width=0.8, color="#151514"))))
    fig.update_geos(projection_type="equal earth", showframe=False, showcoastlines=False, showcountries=True, countrycolor="#151514",
                    showland=True, landcolor=NODATA, showocean=False, bgcolor=BG, lataxis_range=[-58, 85])
    fig.update_layout(height=MAP_H + 20, margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor=BG, dragmode=False, clickmode="event",
                      hoverlabel=dict(bgcolor=INK, font_color="#111110", font_family=FONT),
                      legend=dict(orientation="h", x=0, y=-0.02, yanchor="top", itemclick=False, itemdoubleclick=False,
                                  font=dict(color=INK2, family=FONT, size=12), itemsizing="constant"))
    return fig


def hex_rgb(h, a=200):
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)] + [a]


def mix(h, base=NODATA, k=.32):
    """`k` of colour h mixed into `base`, as color-mix() in the HTML version."""
    a, b = hex_rgb(h, 255), hex_rgb(base, 255)
    return [round(a[i] * k + b[i] * (1 - k)) for i in range(3)] + [255]


@st.cache_data
def year_flows(y):
    """Every delivery of the year, largest first; `drawable` = supplier and recipient both have a point on the map."""
    f = flows[(flows["year"] == y) & (flows["tiv"] > 0)].copy()
    f = f.join(points.rename(columns={"lon": "s_lon", "lat": "s_lat"}), on="supplier_iso3")
    f = f.join(points.rename(columns={"lon": "r_lon", "lat": "r_lat"}), on="recipient_iso3")
    f["recipient"] = f["recipient_iso3"].map(NAMES).fillna(f["recipient_iso3"])
    f["drawable"] = f["s_lon"].notna() & f["r_lon"].notna() & (f["supplier_iso3"] != f["recipient_iso3"].replace(nd.HISTORICAL))
    return f.sort_values("tiv", ascending=False).reset_index(drop=True)


@st.cache_data
def flow_tips(y):
    """Tooltip of every map country in Arms flows: imports with the top 3 suppliers, exports with the top 3 recipients."""
    f = year_flows(y)
    f = f.assign(rec=f["recipient_iso3"].replace(nd.HISTORICAL))
    named = f[~f["supplier"].map(nd.is_non_state)]
    out = {}
    top3 = lambda s: ", ".join(f"{k} {fmt(v)}" for k, v in s.nlargest(3).items()) + (f", other {fmt(s.sum() - s.nlargest(3).sum())}" if len(s) > 3 else "")
    for iso in points.index:
        imp = f[f["rec"] == iso].groupby("supplier")["tiv"].sum()
        exp = named[named["supplier_iso3"] == iso].groupby("recipient")["tiv"].sum()
        name = NAMES.get(iso, iso)
        if not imp.sum() and not exp.sum():
            out[iso] = f"<b>{name} · {y}</b><br>No major arms deliveries in {y}"
        else:
            out[iso] = (f"<b>{name} · {y}</b><br>Imports: {fmt(imp.sum())} TIV" + (f" ({top3(imp)})" if imp.sum() else "")
                        + f"<br>Exports: {fmt(exp.sum())} TIV" + (f" ({top3(exp)})" if exp.sum() else ""))
        if iso in NAMES:
            out[iso] += "<br><i>Click for its card</i>"
    return out


@st.cache_data
def land_features(y, tint):
    """Country shapes with the fill of the year (main-supplier tint) and the tooltip text at the top level of each feature."""
    main = nd.main_suppliers(y) if tint else {}
    tips = flow_tips(y)
    feats = []
    for ft in nd.country_geojson()["features"]:
        iso = ft["properties"]["iso3"]
        feats.append({"type": "Feature", "geometry": ft["geometry"], "properties": {"iso3": iso},
                      "iso3": iso, "fill": mix(nd.supplier_colour(main[iso])) if iso in main else hex_rgb(NODATA, 255),
                      "label": tips.get(iso, NAMES.get(iso, iso))})
    return feats


@st.cache_data
def small_states():
    """Countries with no shape on our map (Bahrain, Malta, Singapore, ...): a dot at their point."""
    shapes = {ft["properties"]["iso3"] for ft in nd.country_geojson()["features"]}
    return [i for i in points.index if i not in shapes and i in NAMES]


def flows_deck(y, n, tint, highlight):
    f = year_flows(y)
    f = f[f["drawable"]].head(n).copy()
    vmax = flows["tiv"].max()
    f["width"] = 1 + 11 * np.minimum(1, f["tiv"] / vmax)
    lit = f["supplier"].eq(highlight) if highlight else pd.Series(True, index=f.index)
    f["src"] = [hex_rgb(nd.supplier_colour(s), 235 if on else 25) for s, on in zip(f["supplier"], lit)]
    f["tgt"] = [hex_rgb(nd.supplier_colour(s), 130 if on else 15) for s, on in zip(f["supplier"], lit)]
    f["label"] = ("<b>" + f["supplier"] + " → " + f["recipient"] + "</b><br>" + f["tiv"].round(0).astype(int).map("{:,}".format)
                  + " TIV in " + str(y) + "<br><i>Click for the recipient's card</i>")
    tips = flow_tips(y)
    dots = pd.DataFrame([{"iso3": i, "lon": points.loc[i, "lon"], "lat": points.loc[i, "lat"], "label": tips.get(i, NAMES[i])}
                         for i in small_states()])
    land = pdk.Layer("GeoJsonLayer", id="land", data=land_features(y, tint), filled=True, stroked=True, get_fill_color="fill",
                     get_line_color=[21, 21, 20, 255], line_width_min_pixels=0.5, pickable=True, auto_highlight=True,
                     highlight_color=[240, 239, 236, 50])
    small = pdk.Layer("ScatterplotLayer", id="small", data=dots, get_position=["lon", "lat"], get_fill_color=[120, 116, 108, 255],
                      get_radius=45000, radius_min_pixels=3, radius_max_pixels=5, pickable=True, auto_highlight=True)
    arcs = pdk.Layer("ArcLayer", id="arcs", data=f, get_source_position=["s_lon", "s_lat"], get_target_position=["r_lon", "r_lat"],
                     get_source_color="src", get_target_color="tgt", get_width="width", get_height=0.35, great_circle=False,
                     pickable=True, auto_highlight=True)
    ends = pdk.Layer("ScatterplotLayer", id="ends", data=f, get_position=["r_lon", "r_lat"], get_fill_color=[240, 239, 236, 200],
                     get_radius=60000, radius_min_pixels=2, radius_max_pixels=5)
    view = pdk.ViewState(latitude=22, longitude=12, zoom=0.12, pitch=0, bearing=0, min_zoom=0)
    return pdk.Deck(layers=[land, small, arcs, ends], initial_view_state=view, map_provider=None, map_style=None,
                    tooltip={"html": "{label}", "style": {"backgroundColor": INK, "color": "#111110", "fontFamily": FONT,
                                                         "fontSize": "12px", "borderRadius": "6px", "padding": "6px 8px",
                                                         "maxWidth": "280px"}},
                    parameters={"clearColor": [0.07, 0.07, 0.06, 1]})


@st.cache_data
def regime_counts():
    """Countries per regime type (columns 0-3) per year."""
    return panel.pivot_table(index="year", columns="regime_type", values="iso3", aggfunc="count").reindex(range(Y0, Y1 + 1)).fillna(0)


def regime_bars(y):
    """Side panel of Regimes: one bar per regime type (liberal democracy on top), on one scale for all years."""
    rc = regime_counts()
    row, vmax = rc.loc[y], float(rc.values.max())
    fig = go.Figure()
    order = [3, 2, 1, 0]
    ys = list(range(len(order)))
    fig.add_trace(go.Bar(x=[vmax] * 4, y=ys, orientation="h", marker=dict(color="rgba(44,44,42,.6)", cornerradius=3),
                         hoverinfo="skip", width=0.34))
    tot = row.sum()
    fig.add_trace(go.Bar(x=[row.get(r, 0) for r in order], y=ys, orientation="h", width=0.34,
                         marker=dict(color=[REG_COLS[r] for r in order], cornerradius=3),
                         customdata=[[REG_LABELS[r], pct(row.get(r, 0), tot)] for r in order],
                         hovertemplate="%{customdata[0]} · " + str(y) + "<br>%{x} of " + str(int(tot)) + " countries (%{customdata[1]})<extra></extra>"))
    for k, r in enumerate(order):
        fig.add_annotation(x=0, y=k, yshift=17, xshift=2, xanchor="left", text=REG_LABELS[r], showarrow=False, font=dict(color=INK2, size=12))
        fig.add_annotation(x=vmax, y=k, yshift=17, xanchor="right", text=f"<b>{int(row.get(r, 0))}</b>", showarrow=False,
                           font=dict(color=INK, size=13))
    fig.update_layout(height=210, margin=dict(l=2, r=2, t=12, b=0), paper_bgcolor=BG, plot_bgcolor=BG, barmode="overlay",
                      showlegend=False, font=dict(family=FONT), xaxis=dict(visible=False, range=[0, vmax], fixedrange=True),
                      yaxis=dict(visible=False, autorange="reversed", fixedrange=True),
                      hoverlabel=dict(bgcolor=INK, font_color="#111110", font_family=FONT))
    return fig


@st.cache_data
def supplier_river():
    t = flows.copy()
    t["group"] = np.where(t["supplier"].isin(list(nd.SUPPLIER_COLOURS)), t["supplier"], "Other")
    return t.pivot_table(index="year", columns="group", values="tiv", aggfunc="sum").reindex(range(Y0, Y1 + 1)).fillna(0)


def river(series, colours, y, unit, label, share=False, key=None, height=155):
    """Stacked river of time, 1950 to 2025, with the year marked. A click sets the year."""
    years = list(range(Y0, Y1 + 1))
    tot = sum(s.reindex(years).fillna(0) for s in series.values())
    fig = go.Figure()
    for (name, s), col in zip(series.items(), colours):
        v = s.reindex(years).fillna(0)
        sh = (v / tot.replace(0, np.nan) * 100).fillna(0)
        fig.add_trace(go.Scatter(
            x=years, y=sh if share else v, name=name, stackgroup="one", mode="lines+markers", line=dict(width=0.5, color=col),
            # invisible markers: only points with a marker can be selected, so a click picks the year
            marker=dict(size=6, opacity=0), selected=dict(marker=dict(opacity=0)), unselected=dict(marker=dict(opacity=0)),
            fillcolor=nr.rgba(col, .88), customdata=np.c_[v, sh],
            hovertemplate=f"{name}: %{{customdata[0]:,.0f}} {unit} (%{{customdata[1]:.0f}}%)<extra></extra>"))
    fig.add_vline(x=1991, line=dict(color=MUTED, dash="dot", width=1))
    if abs(y - 1991) > 16:  # the year label takes its place when they are close
        fig.add_annotation(x=1991, y=1, yref="paper", text="Soviet Union ends (1991)", showarrow=False, yanchor="bottom",
                           font=dict(color=MUTED, size=11))
    fig.add_vline(x=y, line=dict(color=INK, width=2))
    anchor = "left" if y < Y0 + 12 else "right" if y > Y1 - 12 else "center"
    fig.add_annotation(x=y, y=1, yref="paper", yanchor="bottom", xanchor=anchor, text=f"<b>{label}</b>", showarrow=False,
                       font=dict(color=INK, size=12, family="IBM Plex Mono"))
    fig.update_layout(height=height, margin=dict(l=4, r=8, t=22, b=4), paper_bgcolor=BG, plot_bgcolor=BG, showlegend=False,
                      hovermode="x unified", dragmode=False, clickmode="event+select", font=dict(family=FONT, color=MUTED, size=11),
                      hoverlabel=dict(bgcolor=INK, font_color="#111110", font_family=FONT))
    fig.update_xaxes(range=[Y0, Y1], dtick=10, showgrid=False, linecolor=LINE, tickfont=dict(color=MUTED), fixedrange=True,
                     hoverformat="d")
    fig.update_yaxes(title=dict(text="% of world" if share else unit, font=dict(color=MUTED, size=11)), gridcolor=LINE,
                     zeroline=False, tickfont=dict(color=MUTED), fixedrange=True, nticks=4, range=[0, 100] if share else None,
                     ticksuffix="%" if share else "", automargin=True)

    def clicked():
        pts = (ss[key].get("selection") or {}).get("points") or []
        if pts:
            set_year(round(pts[0]["x"]))

    st.plotly_chart(fig, key=key, on_select=clicked, selection_mode="points", config={"displayModeBar": False},
                    alt=f"River of time, 1950 to 2025. Click a year to show it.")


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
    ss["wm_pin"] = f"r:{card_iso}" if card_iso else None


def chord_pin():
    ss["wm_pin"] = ss["wm_chord"].pin


def chord_close():
    ss["wm_pin"] = None


def regime_clicked():
    pick_country(ss["wm_regmap"].select)


def flow_map_clicked():
    sel = (ss["flow_map"].get("selection") or {}).get("objects", {})
    for layer, field in (("arcs", "recipient_iso3"), ("small", "iso3"), ("land", "iso3")):
        objs = sel.get(layer) or []
        if objs:
            iso = nd.HISTORICAL.get(objs[0][field], objs[0][field]) if layer != "arcs" else objs[0][field]
            if iso in NAMES:
                ss["wm_pin"] = "r:" + iso
            return


def bubble_clicked():
    pts = (ss["bld_map"].get("selection") or {}).get("points") or []
    if pts and pts[0].get("customdata"):
        cd = pts[0]["customdata"]
        pick_country(cd[0] if isinstance(cd, list) else cd)


def buildup_row_clicked():
    rows = (ss["bld_top"].get("selection") or {}).get("rows") or []
    top = ss.get("_wm_bld_top") or []
    if rows and rows[0] < len(top):
        pick_country(top[rows[0]])


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
        # the year bar: Play, speed, year and period (the slider follows Play)
        with st.container(horizontal=True, vertical_alignment="center", gap="medium"):
            st.button("Pause" if ss["playing"] else "Play", icon=":material/pause:" if ss["playing"] else ":material/play_arrow:",
                      type="primary", on_click=toggle_play, key="wm_play")
            st.segmented_control("Speed", list(SPEEDS), key="wm_speed", required=True, on_change=full_rerun,
                                 label_visibility="collapsed", help="Play speed")
            ss["wm_year_slider"] = y
            st.slider("Year", p0, p1, key="wm_year_slider", on_change=slider_moved, label_visibility="collapsed", width="stretch")
            st.segmented_control("Period", list(PERIODS), key="wm_period", required=True, on_change=clamp_year,
                                 label_visibility="collapsed", help="Limits the year slider and Play to this period.")

        left, right = st.columns([1.42, 1] if mode == "Arms flows" else [2.1, 1], gap="medium")
        with left:
            if mode == "Regimes":
                regime_svg_map(y, stripes=show_conflict, selected=card_iso, key="wm_regmap", on_select=regime_clicked)
                if show_conflict:
                    st.badge(f"Striped: active armed conflict in {y}", color="gray")
            elif mode == "Arms flows":
                st.plotly_chart(legend_strip([(k, nd.supplier_colour(k)) for k in SUP_ORDER[:-1]] + [("Other suppliers", nd.OTHER_COLOUR)]),
                                config={"displayModeBar": False, "staticPlot": True}, key="flow_legend")
                f = year_flows(y)
                drawn = f[f["drawable"]].head(top_n)
                st.pydeck_chart(flows_deck(y, top_n, tint, highlight), height=MAP_H - 54, key="flow_map",
                                on_select=flow_map_clicked, selection_mode="single-object",
                                alt=f"Map of the {top_n} largest arms deliveries in {y}")
                st.badge("No deliveries in " + str(y) if f.empty else
                         f"Top {len(drawn)} of {len(f):,} deliveries shown ({pct(drawn['tiv'].sum(), f['tiv'].sum())} of this year's TIV)",
                         color="gray")
            else:
                st.plotly_chart(buildup_map(y), key="bld_map", on_select=bubble_clicked, selection_mode="points",
                                config={"displayModeBar": False, "scrollZoom": False},
                                alt=f"Bubble map of major arms received {y - 9} to {y}")
        with right:
            with st.container(height=SIDE_H, border=False):
                if mode == "Arms flows":
                    pin = ss.get("wm_pin") or ""
                    pin_iso = pin[2:] if pin.startswith("r:") else nd.SUPPLIER_ISO.get(pin[2:]) if pin.startswith("s:") else None
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
                    st.plotly_chart(regime_bars(y), key="reg_bars", config={"displayModeBar": False})
                    a, b = st.columns(2)
                    a.metric("With armed conflict", int(g["conflict_active"].sum()), help="Countries with an active armed conflict (25+ battle deaths)")
                    b.metric("Of them at war", int((g["max_intensity"] == 2).sum()), help="1,000+ battle deaths in the year")
                else:
                    side_header(f"Largest build-ups, {y - 9}–{y}", "TIV received in 10 years")
                    v = nd.arms_rolling_hosted().loc[y]
                    top = v[v > 0].nlargest(10)
                    ss["_wm_bld_top"] = list(top.index)
                    if top.empty:
                        st.info(f"No major arms received in {y - 9}–{y}.", icon=":material/info:")
                    else:
                        t = pd.DataFrame({"#": range(1, len(top) + 1), "Country": [NAMES.get(i, i) for i in top.index],
                                          "TIV": top.values})
                        st.dataframe(t, hide_index=True, height=28 * len(t) + 32, row_height=28, key="bld_top",
                                     on_select=buildup_row_clicked, selection_mode="single-row", column_config={
                                         "#": st.column_config.NumberColumn("#", width=28),
                                         "TIV": st.column_config.ProgressColumn("TIV", format="%,.0f", min_value=0, width="medium",
                                                                                max_value=float(top.max()))})

        # river of time: click a year to jump there
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
            m[0].metric("TIV delivered", fmt(f["tiv"].sum()))
            m[1].metric("Transfers (supplier → recipient)", fmt(len(f)))
            m[2].metric(f"Top supplier ({fmt(ts.max())} TIV)" if len(ts) else "Top supplier", ts.idxmax() if len(ts) else "–")
            m[3].metric(f"Top recipient ({fmt(tr.max())} TIV)" if len(tr) else "Top recipient",
                        NAMES.get(tr.idxmax(), tr.idxmax()) if len(tr) else "–")
        elif mode == "Arms build-up":
            row = nd.buildup_rows().loc[y]
            tot = row.sum()
            v = nd.arms_rolling_hosted().loc[y]
            m[0].metric(f"TIV received worldwide, {y - 9}–{y}", fmt(tot))
            m[1].metric("Countries that received major arms", int((v > 0).sum()))
            m[2].metric(f"Went to democracies (regime in {y})", pct(row[2] + row[3], tot))
            m[3].metric(f"Went to autocracies (regime in {y})", pct(row[0] + row[1], tot))
        else:
            rc = regime_counts().loc[y]
            top = g.nlargest(1, "arms_imports_tiv")
            m[0].metric("Democracies", int(rc.get(2, 0) + rc.get(3, 0)))
            m[1].metric("Autocracies", int(rc.get(0, 0) + rc.get(1, 0)))
            m[2].metric("TIV of major arms imported", fmt(g["arms_imports_tiv"].sum()))
            m[3].metric(f"Largest importer ({fmt(top['arms_imports_tiv'].iloc[0])} TIV)" if len(top) and top["arms_imports_tiv"].iloc[0] > 0
                        else "Largest importer", top["country_name"].iloc[0] if len(top) and top["arms_imports_tiv"].iloc[0] > 0 else "–")

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


map_card()


# ------------------------------------------------------------------ main finding (as on the HTML World map page)
@st.cache_data
def finding_chart():
    F = nr.load_finding()
    fig = go.Figure()
    for grp, name, colour in [("high", "High arms importers", nr.HI), ("low", "Low arms importers", nr.LO)]:
        d = F["groups"][grp]
        hover = [f"{name}: {nr.sgn(m)} (95% CI {nr.sgn(a)} to {nr.sgn(b)}, n = {c})"
                 for m, a, b, c in zip(d["m"], d["lo"], d["hi"], d["cnt"])]
        band, line = nr.band_traces(d["rel"], d["lo"], d["hi"], d["m"], colour, f"{name} ({d['n']} onsets)", hover, .13)
        line.mode, line.showlegend = "lines", True
        line.hovertemplate, line.hoverinfo = "%{text}<extra></extra>", None
        fig.add_traces([band, line])
    fig.add_vline(x=0, line=dict(color=INK2, dash="dash", width=1.2))
    fig.add_annotation(x=0, y=1, yref="paper", text="Conflict starts", showarrow=False, xanchor="left", xshift=6,
                       font=dict(color=INK2, size=12))
    nr.layout(fig, 330, hovermode="x unified", showlegend=True, margin=dict(l=8, r=8, t=36, b=8),
              legend=dict(orientation="h", x=0, y=1.02, yanchor="bottom", font=dict(color=INK2)))
    fig.update_xaxes(title="Years relative to conflict onset", tickvals=[-10, -5, 0, 5, 10],
                     ticktext=["−10", "−5", "0", "+5", "+10"], showgrid=False, range=[-10.5, 10.5])
    fig.update_yaxes(tickformat="+.2f", zeroline=True, zerolinecolor=INK2)
    return fig


F = nr.load_finding()
hi_g, lo_g = F["groups"]["high"], F["groups"]["low"]
k5h, k5l = hi_g["rel"].index(5), lo_g["rel"].index(5)
overlap = hi_g["lo"][k5h] <= lo_g["hi"][k5l] and lo_g["lo"][k5l] <= hi_g["hi"][k5h]
with st.container(border=True):
    txt, chart = st.columns([1, 1.5], gap="large")
    with txt:
        st.markdown(":primary[**Main finding**]")
        st.subheader("Democracy around the start of a conflict", anchor=False)
        st.caption("Change in the democracy index compared with the year before a conflict starts (onset = first conflict year "
                   "after a year of peace). High vs. low arms importers: average imports in the 5 years before onset, split at "
                   "the median. Shaded: 95% confidence band.")
        st.markdown(":material/arrow_downward: Below the zero line = less democratic than just before the conflict began.")
        st.markdown(f"Five years after onset the index changed by **{nr.sgn(hi_g['m'][k5h])}** for high importers and "
                    f"**{nr.sgn(lo_g['m'][k5l])}** for low importers. "
                    + ("The 95% bands overlap at +5 years, so this data shows no clear difference between the groups."
                       if overlap else "The 95% bands do not overlap at +5 years.")
                    + f" Median pre-onset imports: {F['median_pre']:.1f} TIV (millions) per year. Figures are preliminary "
                    "(see About the data).")
        if st.button("See the regression results", icon=":material/arrow_forward:", type="tertiary", key="wm_to_findings"):
            st.switch_page("native_pages/findings.py")
    chart.plotly_chart(finding_chart(), config={"displayModeBar": False}, key="wm_finding",
                       alt="Line chart of the change in democracy around conflict onset, high vs. low arms importers")
    with st.expander("Show the numbers"):
        st.dataframe(pd.DataFrame({
            "Year": [nr.sgn(r, 0) for r in hi_g["rel"]],
            "High": [nr.sgn(v) for v in hi_g["m"]],
            "High: 95% CI": [f"{nr.sgn(a)} to {nr.sgn(b)}" for a, b in zip(hi_g["lo"], hi_g["hi"])],
            "Low": [nr.sgn(lo_g["m"][lo_g["rel"].index(r)]) for r in hi_g["rel"]],
            "Low: 95% CI": [f"{nr.sgn(lo_g['lo'][lo_g['rel'].index(r)])} to {nr.sgn(lo_g['hi'][lo_g['rel'].index(r)])}"
                            for r in hi_g["rel"]],
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
