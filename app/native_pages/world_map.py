"""World map, built only with Streamlit (no custom HTML).

Charts: Plotly maps in the Equal Earth projection (regimes, arms build-up), pydeck arcs for arms flows,
ECharts for the chord graph, the bar panel and the rivers of time. Controls live in the sidebar; Play
advances the year for the whole page (map, side panel, river and numbers together).
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pydeck as pdk
import streamlit as st

import native_data as nd
from native_components.chord import chord_ring
from native_components.regime_map import regime_map as regime_svg_map

Y0, Y1 = 1950, 2025
BG = "rgba(0,0,0,0)"
INK, INK2, MUTED, LINE = "#f0efec", "#c3c2b7", "#959086", "#2c2c2a"
SPEEDS = {"0.5×": 2.4, "1×": 1.2, "2×": 0.6}  # seconds per year
MODES = ["Regimes", "Arms flows", "Arms build-up"]

panel = nd.load_panel()
points = nd.country_points()
flows = nd.load_flows()
NAMES = panel.drop_duplicates("iso3").set_index("iso3")["country_name"].to_dict()
REG_LABELS = [r.capitalize() for r in nd.REGIMES]
REG_COLS = [nd.REGIME_COLOURS[r] for r in nd.REGIMES]

# ------------------------------------------------------------------ state
ss = st.session_state
ss.setdefault("year", 2000)
ss.setdefault("playing", False)
ss.setdefault("wm_year_slider", ss["year"])


def slider_moved():
    ss["year"] = ss["wm_year_slider"]


def toggle_play():
    ss["playing"] = not ss["playing"]
    if ss["playing"] and ss["year"] >= Y1:
        ss["year"] = Y0
    ss["wm_year_slider"] = ss["year"]


# ------------------------------------------------------------------ sidebar
with st.sidebar:
    mode = st.segmented_control("Map shows", MODES, default="Regimes", key="wm_mode") or "Regimes"
    st.slider("Year", Y0, Y1, key="wm_year_slider", on_change=slider_moved, disabled=ss["playing"])
    st.button("Pause" if ss["playing"] else "Play through the years", icon=":material/pause:" if ss["playing"] else ":material/play_arrow:",
              type="primary", on_click=toggle_play, width="stretch")
    speed = st.segmented_control("Speed", list(SPEEDS), default="1×", key="wm_speed", width="stretch") or "1×"
    st.divider()
    if mode == "Regimes":
        show_conflict = st.toggle("Mark armed conflicts", value=True)
    elif mode == "Arms flows":
        top_n = st.segmented_control("Deliveries drawn", [25, 60], default=25, format_func=lambda n: f"Top {n}") or 25
    card_iso = st.selectbox("Country details", [None] + sorted(NAMES, key=NAMES.get), key="wm_card_iso",
                            format_func=lambda i: "Choose a country…" if i is None else NAMES[i])
    st.caption("SIPRI trend-indicator values (TIV) measure military capability transferred, not money. "
               "Historical states are drawn at today's borders.")


# ------------------------------------------------------------------ chart helpers
def echarts_stack(series, colours, year, unit, height=230, mark1991=True):
    """Stacked area river over 1950–2025 with the year marked."""
    years = list(range(Y0, Y1 + 1))
    lines = [{"xAxis": str(year), "lineStyle": {"color": INK, "width": 2, "type": "solid"}, "label": {"formatter": str(year), "color": INK}}]
    if mark1991:
        lines.append({"xAxis": "1991", "lineStyle": {"color": MUTED, "type": "dashed"}, "label": {"formatter": "1991", "color": MUTED}})
    out = []
    for i, (name, vals) in enumerate(series.items()):
        s = {"name": name, "type": "line", "stack": "all", "smooth": 0.3, "symbol": "none", "lineStyle": {"width": 0},
             "areaStyle": {"opacity": 0.9, "color": colours[i]}, "itemStyle": {"color": colours[i]}, "emphasis": {"focus": "series"},
             "data": [round(float(v), 1) for v in vals]}
        if i == 0:
            s["markLine"] = {"symbol": "none", "silent": True, "data": lines}
        out.append(s)
    return {"backgroundColor": "transparent", "animationDurationUpdate": 400,
            "tooltip": {"trigger": "axis", "valueFormatter": None},
            "legend": {"bottom": 0, "textStyle": {"color": INK2}, "icon": "roundRect", "itemWidth": 10, "itemHeight": 10},
            "grid": {"left": 56, "right": 16, "top": 24, "bottom": 46},
            "xAxis": {"type": "category", "data": [str(y) for y in years], "boundaryGap": False,
                      "axisLabel": {"color": MUTED, "interval": 9}, "axisLine": {"lineStyle": {"color": LINE}}},
            "yAxis": {"type": "value", "name": unit, "nameTextStyle": {"color": MUTED}, "axisLabel": {"color": MUTED},
                      "splitLine": {"lineStyle": {"color": LINE}}},
            "series": out}


def plotly_geo_layout(fig, height=470):
    fig.update_geos(projection_type="equal earth", showframe=False, showcoastlines=False, showcountries=True, countrycolor="#151514",
                    showland=True, landcolor="#2a2a28", showocean=False, bgcolor=BG, lataxis_range=[-58, 85])
    fig.update_layout(height=height, margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor=BG, showlegend=False,
                      hoverlabel=dict(bgcolor=INK, font_color="#111110", font_family="IBM Plex Sans"))
    return fig


@st.cache_data
def regime_map(y, show_conflict):
    g = panel[panel["year"] == y]
    scale = []
    for i, c in enumerate(REG_COLS):
        scale += [[i / 4, c], [(i + 1) / 4, c]]
    conflict = np.where(g["max_intensity"] == 2, "War (1000+ deaths)", np.where(g["max_intensity"] == 1, "Minor conflict", "No armed conflict"))
    text = (g["country_name"] + " · " + str(y) + "<br>" + g["regime_label"].str.capitalize() + ", democracy index "
            + g["democracy_index"].round(2).astype(str) + "<br>" + conflict + "<br>Arms imports: " + g["arms_imports_tiv"].round(0).astype(int).astype(str) + " TIV")
    fig = go.Figure(go.Choropleth(locations=g["iso3"], z=g["regime_type"], zmin=-0.5, zmax=3.5, colorscale=scale, showscale=False,
                                  marker_line_color="#151514", marker_line_width=0.4, text=text, hoverinfo="text"))
    if show_conflict:
        c = g[g["conflict_active"] == 1].join(points, on="iso3", how="inner")
        fig.add_trace(go.Scattergeo(lon=c["lon"], lat=c["lat"], mode="markers", hoverinfo="skip",
                                    marker=dict(symbol="x-thin", size=np.where(c["max_intensity"] == 2, 12, 7), line=dict(width=2.2, color=INK))))
    return plotly_geo_layout(fig)


@st.cache_data
def buildup_map(y):
    p = panel[(panel["year"] == y) & (panel["arms_10"] > 0)].copy()
    p["iso_pt"] = p["iso3"].replace(nd.HISTORICAL)
    p = p.join(points, on="iso_pt", how="inner")
    vmax = panel["arms_10"].max()
    text = (p["country_name"] + " · 10 years to " + str(y) + "<br>" + p["arms_10"].round(0).astype(int).map("{:,}".format)
            + " TIV of major arms received<br>" + p["regime_label"].str.capitalize())
    fig = go.Figure(go.Scattergeo(lon=p["lon"], lat=p["lat"], mode="markers", text=text, hoverinfo="text",
                                  marker=dict(size=3 + 64 * np.sqrt(p["arms_10"] / vmax), color=p["regime_label"].map(nd.REGIME_COLOURS),
                                              opacity=.9, line=dict(width=0.8, color="#151514"))))
    return plotly_geo_layout(fig)


def hex_rgb(h, a=200):
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)] + [a]


@st.cache_data
def year_flows(y):
    f = flows[(flows["year"] == y) & (flows["supplier"] != "Other")].dropna(subset=["supplier_iso3"])
    f = f.join(points.rename(columns={"lon": "s_lon", "lat": "s_lat"}), on="supplier_iso3", how="inner")
    f = f.join(points.rename(columns={"lon": "r_lon", "lat": "r_lat"}), on="recipient_iso3", how="inner")
    f["recipient"] = f["recipient_iso3"].map(NAMES).fillna(f["recipient_iso3"])
    return f.sort_values("tiv", ascending=False)


def flows_deck(y, n):
    f = year_flows(y).head(n).copy()
    vmax = flows["tiv"].max()
    f["width"] = 1 + 7 * np.sqrt(f["tiv"] / vmax)
    f["src"] = f.apply(lambda r: hex_rgb(nd.supplier_colour(r["supplier"]), 230), axis=1)
    f["tgt"] = f.apply(lambda r: hex_rgb(nd.supplier_colour(r["supplier"]), 120), axis=1)
    f["label"] = f["supplier"] + " → " + f["recipient"] + ": " + f["tiv"].round(0).astype(int).map("{:,}".format) + " TIV"
    arcs = pdk.Layer("ArcLayer", id="arcs", data=f, get_source_position=["s_lon", "s_lat"], get_target_position=["r_lon", "r_lat"],
                     get_source_color="src", get_target_color="tgt", get_width="width", get_height=0.35, great_circle=False,
                     pickable=True, auto_highlight=True)
    dots = pdk.Layer("ScatterplotLayer", id="dots", data=f, get_position=["r_lon", "r_lat"], get_fill_color=[240, 239, 236, 200],
                     get_radius=60000, radius_min_pixels=2, radius_max_pixels=6)
    land = pdk.Layer("GeoJsonLayer", id="land", data=nd.country_geojson(), filled=True, stroked=True, get_fill_color=[42, 42, 40, 255],
                     get_line_color=[21, 21, 20, 255], line_width_min_pixels=0.5)
    view = pdk.ViewState(latitude=22, longitude=20, zoom=0.55, pitch=30, bearing=0, min_zoom=0.3)
    return pdk.Deck(layers=[land, arcs, dots], initial_view_state=view, map_provider=None, map_style=None,
                    tooltip={"text": "{label}"}, parameters={"clearColor": [0.07, 0.07, 0.06, 1]})


def sankey(y):
    g = flows[(flows["year"] == y) & (flows["supplier"] != "unknown supplier(s)")].copy()
    if g.empty:
        return None
    top_s = list(g[g["supplier"] != "Other"].groupby("supplier")["tiv"].sum().nlargest(6).index)
    top_r = list(g.groupby("recipient_iso3")["tiv"].sum().nlargest(8).index)
    g["s"] = np.where(g["supplier"].isin(top_s), g["supplier"], "Other suppliers")  # includes SIPRI's "Other"
    g["r"] = np.where(g["recipient_iso3"].isin(top_r), g["recipient_iso3"].map(NAMES), "Other recipients")
    links = g.groupby(["s", "r"], as_index=False)["tiv"].sum()
    total = links["tiv"].sum()
    left = list(links.groupby("s")["tiv"].sum().sort_values(ascending=False).index)
    right = list(links.groupby("r")["tiv"].sum().sort_values(ascending=False).index)
    idx = {n: i for i, n in enumerate(left)} | {n: len(left) + i for i, n in enumerate(right)}
    s_tot = links.groupby("s")["tiv"].sum()
    labels = [f"{n} {s_tot[n] / total:.0%}" for n in left] + right

    def rgba(h, a):
        h = h.lstrip("#")
        return "rgba(%d,%d,%d,%s)" % (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)

    fig = go.Figure(go.Sankey(
        arrangement="snap",
        node=dict(label=labels, pad=8, thickness=10, line=dict(width=0),
                  color=[nd.supplier_colour(n) for n in left] + [INK2] * len(right),
                  hovertemplate="%{label}: %{value:,.0f} TIV<extra></extra>"),
        link=dict(source=links["s"].map(idx), target=links["r"].map(idx), value=links["tiv"],
                  color=[rgba(nd.supplier_colour(x), .35) for x in links["s"]],
                  hovertemplate="%{source.label} → %{target.label}: %{value:,.0f} TIV<extra></extra>")))
    fig.update_layout(height=440, margin=dict(l=0, r=0, t=4, b=4), paper_bgcolor=BG,
                      font=dict(color=INK, size=11, family="IBM Plex Sans"))
    return fig


def regime_bars(y):
    g = panel[panel["year"] == y]
    counts = [int((g["regime_type"] == i).sum()) for i in range(4)]
    fig = go.Figure(go.Bar(x=counts, y=REG_LABELS, orientation="h", marker=dict(color=REG_COLS, cornerradius=4),
                           text=counts, textposition="outside", textfont=dict(color=INK), cliponaxis=False,
                           hovertemplate="%{y}: %{x} countries<extra></extra>"))
    fig.update_layout(height=190, margin=dict(l=0, r=30, t=0, b=0), paper_bgcolor=BG, plot_bgcolor=BG, bargap=0.35,
                      xaxis=dict(visible=False, range=[0, max(counts) * 1.15]),
                      yaxis=dict(autorange="reversed", tickfont=dict(color=INK2), showgrid=False, automargin=True, ticksuffix="  "),
                      font=dict(family="IBM Plex Sans"))
    return fig


@st.cache_data
def river_data():
    reg = panel.pivot_table(index="year", columns="regime_type", values="iso3", aggfunc="count").reindex(range(Y0, Y1 + 1)).fillna(0)
    t = flows.copy()
    t["group"] = np.where(t["supplier"].isin(list(nd.SUPPLIER_COLOURS)), t["supplier"], "Other")
    sup = t.pivot_table(index="year", columns="group", values="tiv", aggfunc="sum").reindex(range(Y0, Y1 + 1)).fillna(0)
    b = panel.pivot_table(index="year", columns="regime_type", values="arms_10", aggfunc="sum").reindex(range(Y0, Y1 + 1)).fillna(0)
    return reg, sup, b


def country_card(iso, y):
    g = panel[(panel["iso3"] == iso) & (panel["year"] == y)]
    with st.container(border=True):
        st.markdown(f"**{NAMES[iso]}** · {y}")
        if st.button("Open in Countries & compare", icon=":material/compare_arrows:", key="wm_open_cmp", type="tertiary"):
            open_in_compare(iso)
        if g.empty:
            st.caption("No V-Dem data for this year.")
            return
        r = g.iloc[0]
        regime = str(r["regime_label"]).capitalize() if pd.notna(r["regime_label"]) else "No regime data"
        index = f" · democracy index {r['democracy_index']:.2f}" if pd.notna(r["democracy_index"]) else ""
        st.caption(f"{regime}{index} · "
                   + ("war" if r["max_intensity"] == 2 else "minor conflict" if r["max_intensity"] == 1 else "no armed conflict"))
        imp = flows[(flows["recipient_iso3"] == iso) & (flows["year"] == y)].groupby("supplier")["tiv"].sum().sort_values(ascending=False)
        exp = flows[(flows["supplier_iso3"] == iso) & (flows["year"] == y)].groupby("recipient_iso3")["tiv"].sum().sort_values(ascending=False)
        # unit in the label, so the value never gets cut off in the narrow columns; 10,000 and up in compact form
        tiv = lambda v: f"{v / 1000:,.1f}k" if v >= 10_000 else f"{v:,.0f}"
        a, b = st.columns(2)
        a.metric("Imports (TIV)", tiv(r["arms_imports_tiv"] if pd.notna(r["arms_imports_tiv"]) else 0))
        if exp.sum() > 0:
            b.metric("Exports (TIV)", tiv(exp.sum()))
        else:  # plain text, so "none recorded" is not cut off at the metric's large size
            b.markdown("Exports (TIV)  \n:gray[none recorded]")
        if len(imp):
            st.dataframe(pd.DataFrame({"Supplier": imp.index, "TIV": imp.values}).head(5), hide_index=True,
                         column_config={"TIV": st.column_config.ProgressColumn("TIV", format="%.0f", min_value=0, max_value=float(imp.max()))})
        if len(exp):
            st.dataframe(pd.DataFrame({"Recipient": exp.index.map(lambda i: NAMES.get(i, i)), "TIV": exp.values}).head(5), hide_index=True,
                         column_config={"TIV": st.column_config.ProgressColumn("TIV", format="%.0f", min_value=0, max_value=float(exp.max()))})


# ------------------------------------------------------------------ pinned country card of the chord ring (Arms flows)
# ss["wm_pin"] is a card key ("r:ISO3" or "s:Supplier"). Set by the sidebar "Country details" (when it changes), by a
# click on an arc of the map (its recipient) or on a country node of the ring; cleared by the card's ×.
_UNSET = object()
if ss.get("_wm_card_prev", _UNSET) != card_iso:
    ss["_wm_card_prev"] = card_iso
    ss["wm_pin"] = f"r:{card_iso}" if card_iso else None


def chord_pin():
    ss["wm_pin"] = ss["wm_chord"].pin


def chord_close():
    ss["wm_pin"] = None


def regime_clicked():
    """A click on the regimes map shows that country in the sidebar "Country details"."""
    ss["wm_card_iso"] = ss["wm_regmap"].select


def open_in_compare(iso):
    ss["countries"] = [iso]
    st.switch_page("native_pages/compare.py")


def arc_selected():
    objs = (ss["flow_map"].get("selection") or {}).get("objects", {}).get("arcs", [])
    if objs:
        ss["wm_pin"] = "r:" + objs[0]["recipient_iso3"]


# ------------------------------------------------------------------ page body (re-run on its own while playing)
@st.fragment(run_every=SPEEDS[speed] if ss["playing"] else None)
def body():
    if ss["playing"]:
        if ss["year"] >= Y1:
            ss["playing"] = False
            ss["wm_year_slider"] = ss["year"]
            st.rerun()
        ss["year"] += 1
    y = ss["year"]
    reg, sup, bld = river_data()

    head_l, head_r = st.columns([3, 1], vertical_alignment="bottom")
    head_l.title("World map")
    head_l.caption({"Regimes": "Regime type of every country; stripes mark an armed conflict (denser = war). Click a country for its details.",
                    "Arms flows": "Who delivered major arms to whom. Arc width = TIV delivered, colour = supplier.",
                    "Arms build-up": "Bubble area = major arms received in the previous 10 years; colour = regime type."}[mode])
    head_r.markdown(f"## {y}")

    # Arms flows: a slightly wider side panel, so the chord ring and its labels fit at their real size
    left, right = st.columns([1.45, 1] if mode == "Arms flows" else [1.7, 1], gap="medium")
    with left:
        with st.container(border=True):
            if mode == "Regimes":
                # SVG map with striped conflicts (custom component); the Plotly regime_map() is kept but no longer drawn
                regime_svg_map(y, stripes=show_conflict, selected=card_iso, key="wm_regmap", on_select=regime_clicked)
                if ss.get("wm_card_iso") != card_iso:  # a click picked a country: redraw the sidebar too (outside this fragment)
                    st.rerun(scope="app")
            elif mode == "Arms flows":
                f = year_flows(y)
                share = f.head(top_n)["tiv"].sum() / max(1, flows.loc[flows["year"] == y, "tiv"].sum())
                st.pydeck_chart(flows_deck(y, top_n), height=470, key="flow_map", on_select=arc_selected, selection_mode="single-object")
                st.badge(f"Top {top_n} of {len(f)} named deliveries · {share:.0%} of this year's TIV", color="gray")
            else:
                st.plotly_chart(buildup_map(y), key="bld_map", config={"displayModeBar": False})
    with right:
        with st.container(border=True, height=520 if card_iso is None or mode == "Arms flows" else "content"):
            if card_iso is not None and mode != "Arms flows":  # in Arms flows the ring shows it as a pinned card
                country_card(card_iso, y)
            if mode == "Regimes":
                st.markdown(f"**Regimes in {y}**")
                st.plotly_chart(regime_bars(y), key="reg_bars", config={"displayModeBar": False})
                g = panel[panel["year"] == y]
                st.metric("Countries with armed conflict", int(g["conflict_active"].sum()), border=False)
                st.metric("of which at war", int((g["max_intensity"] == 2).sum()), border=False)
            elif mode == "Arms flows":
                st.markdown(f"**Who supplied whom in {y}**")
                # chord ring + country card (custom component); sankey(y) is kept but no longer drawn
                chord_ring(y, pinned=ss.get("wm_pin"), height=440, key="wm_chord",
                           tween_ms=int(min(800, 700 * SPEEDS[speed])), on_pin=chord_pin, on_close=chord_close)
            else:
                st.markdown(f"**Largest build-ups, 10 years to {y}**")
                t = panel[panel["year"] == y].nlargest(10, "arms_10")[["country_name", "regime_label", "arms_10"]]
                st.dataframe(t, hide_index=True, height=420, column_config={
                    "country_name": "Country", "regime_label": "Regime",
                    "arms_10": st.column_config.ProgressColumn("TIV, 10 years", format="%.0f", min_value=0, max_value=float(t["arms_10"].max() or 1))})

    with st.container(border=True):
        if mode == "Regimes":
            st.markdown("**Countries per regime type, 1950 to 2025**")
            st.echarts_chart(echarts_stack({REG_LABELS[i]: reg.get(i, pd.Series(0, index=reg.index)) for i in range(4)}, REG_COLS, y, "countries"), height=230, key="riv_reg")
        elif mode == "Arms flows":
            st.markdown("**Arms deliveries by supplier, 1950 to 2025**")
            order = list(nd.SUPPLIER_COLOURS) + ["Other"]
            st.echarts_chart(echarts_stack({k: sup.get(k, pd.Series(0, index=sup.index)) for k in order},
                                           [nd.supplier_colour(k) for k in order], y, "TIV"), height=230, key="riv_sup")
        else:
            st.markdown("**Arms received in the previous 10 years, by the recipient's regime type**")
            st.echarts_chart(echarts_stack({REG_LABELS[i]: bld.get(i, pd.Series(0, index=bld.index)) for i in range(4)}, REG_COLS, y, "TIV"), height=230, key="riv_bld")

    g = panel[panel["year"] == y]
    m = st.columns(4)
    if mode == "Arms flows":
        f = flows[flows["year"] == y]
        top_s = f[f["supplier"] != "Other"].groupby("supplier")["tiv"].sum()
        top_r = f.groupby("recipient_iso3")["tiv"].sum()
        m[0].metric("TIV delivered", f"{f['tiv'].sum():,.0f}", border=True)
        m[1].metric("Deliveries (supplier → recipient)", len(f), border=True)
        m[2].metric("Top supplier", top_s.idxmax() if len(top_s) else "–", border=True)
        m[3].metric("Top recipient", NAMES.get(top_r.idxmax(), "–") if len(top_r) else "–", border=True)
    elif mode == "Arms build-up":
        m[0].metric(f"TIV received {y - 9}–{y}", f"{g['arms_10'].sum():,.0f}", border=True)
        m[1].metric("Countries that received arms", int((g["arms_10"] > 0).sum()), border=True)
        dem = g.loc[g["regime_type"] >= 2, "arms_10"].sum() / max(1, g["arms_10"].sum())
        m[2].metric("Went to democracies", f"{dem:.0%}", border=True)
        m[3].metric("Went to autocracies", f"{1 - dem:.0%}", border=True)
    else:
        m[0].metric("Democracies", int((g["regime_type"] >= 2).sum()), border=True)
        m[1].metric("Autocracies", int((g["regime_type"] <= 1).sum()), border=True)
        m[2].metric("Major arms imported", f"{g['arms_imports_tiv'].sum():,.0f} TIV", border=True)
        top = g.nlargest(1, "arms_imports_tiv")
        m[3].metric("Largest importer", top["country_name"].iloc[0] if len(top) else "–", border=True)

    with st.expander("Show the numbers"):
        if mode == "Arms flows":
            st.dataframe(year_flows(y)[["supplier", "recipient", "tiv"]], hide_index=True,
                         column_config={"tiv": st.column_config.NumberColumn("TIV", format="%.0f")})
        else:
            st.dataframe(g[["country_name", "regime_label", "democracy_index", "max_intensity", "arms_imports_tiv", "arms_10"]], hide_index=True)


body()
