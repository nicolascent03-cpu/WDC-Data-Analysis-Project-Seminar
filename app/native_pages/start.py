"""Start page: the hero with its three entry points, a preview map of the latest year and the three ways to explore.

Same content as the Start page of app/site/adc.html. The preview map is an Altair geoshape map (Equal Earth, as the
HTML version); a click on a country opens the World map at that year with the country's card.
"""

import altair as alt
import streamlit as st

import native_data as nd
import native_results as nr

WORLD_MAP, COMPARE, FINDINGS = "native_pages/world_map.py", "native_pages/compare.py", "native_pages/findings.py"
# Shortcut groups, as START_GROUPS in app/site/adc.html
START_GROUPS = ["Former Soviet Union", "European Union (27)", "Latin America", "North America",
                "Middle East and North Africa", "G7"]
NO_DATA, NODATA_COL = "No V-Dem data", "#2a2a28"

ss = st.session_state


def group_chosen():
    """Remember the group for the compare page, then leave from the script body (switch_page is not allowed here)."""
    name = ss.get("start_group")
    if name:
        ss["cmp_group"] = name
        ss["start_go"] = COMPARE
    ss["start_group"] = None


def open_map(y, iso=None):
    """Open the World map at year `y` (Regimes), with the card of `iso` if a country was clicked."""
    ss["year"] = y
    ss["playing"] = False
    ss["wm_period"] = "1950–2025"  # so the year is inside the map's period
    ss["wm_mode"] = "Regimes"
    if iso:
        ss["wm_card_iso"] = iso
    ss["start_go"] = WORLD_MAP


if go := ss.pop("start_go", None):
    st.switch_page(go)


@st.cache_data
def latest_year():
    panel = nr.load_panel()
    y = int(panel["year"].max())
    return y, panel[panel["year"] == y]


@st.cache_data
def preview_features(y):
    """Country shapes with the regime of year `y` and the tooltip fields at the top level of each feature."""
    g = latest_year()[1].set_index("iso3")
    names = nr.load_panel().drop_duplicates("iso3").set_index("iso3")["country_name"]
    feats = []
    for ft in nd.vega_land_shapes():
        iso = ft["iso3"]
        r = g["regime_type"].get(iso)
        has = r is not None and r == r
        row = g.loc[iso] if has else None
        feats.append({**ft, "Country": names.get(iso, iso),
                      "Regime": nr.REGIMES[int(r)] if has else NO_DATA,
                      "Index": f"{row['democracy_index']:.2f}" if has else "–",
                      "Conflict": ("Active armed conflict" if row["conflict_active"] else "No armed conflict") if has else "–"})
    return feats


def legend_line(names, colours):
    """A one-line colour legend in Markdown: a coloured square before each name."""
    return ":small[" + "\u2002 ".join(f':color[■]{{foreground="{c}"}}\u00a0{n.replace(" ", "\u00a0")}' for n, c in zip(names, colours)) + "]"


# The projection is fitted to this fixed frame (the land of the HTML map: 180°W to 180°E, 56°S to 84°N), not to the
# shapes: polygons crossing the date line (Fiji, Russia) widen the shapes' own bounds and the world came out small.
FRAME = {"type": "Feature", "properties": {}, "geometry": {"type": "MultiPoint", "coordinates":
         [[lon, lat] for lon in range(-180, 181, 5) for lat in (-56, 84)] + [[lon, lat] for lon in (-180, 180) for lat in range(-56, 85, 4)]}}


def preview_map(y):
    sel = alt.selection_point(name="country", fields=["iso3"], on="click", empty=False)
    colour = alt.Color("Regime:N", scale=alt.Scale(domain=nr.REGIMES + [NO_DATA], range=nr.REG_COLS + [NODATA_COL]),
                       legend=None)  # the legend is a Markdown line under the map, so it never gets cut off
    chart = (alt.Chart(alt.Data(values=preview_features(y)))
             .mark_geoshape(stroke="#1a1a19", strokeWidth=0.5, cursor="pointer")
             .encode(color=colour,
                     tooltip=[alt.Tooltip("Country:N", title=str(y)), alt.Tooltip("Regime:N"),
                              alt.Tooltip("Index:N", title="Democracy index"), alt.Tooltip("Conflict:N", title="Conflict")])
             .add_params(sel).project("equalEarth", fit=FRAME)
             .properties(height=250)
             .configure_view(stroke=None)
             .configure(background="transparent", font="IBM Plex Sans, sans-serif"))
    return chart


# ------------------------------------------------------------------ hero
left, right = st.columns([1, 1.1], gap="large", vertical_alignment="center")
with left:
    st.markdown(":primary[:small[**SEMINAR PROJECT · 1950 TO 2025**]]")
    st.title("Arms, :primary[Democracy] and Conflict", anchor=False)
    st.markdown("What happens to democracy during and after armed conflict, and does it look different in countries "
                "that import many weapons? Explore regimes, wars and arms deliveries from 1950 to 2025.")
    with st.container(horizontal=True):
        if st.button("Explore the world map", type="primary", icon=":material/public:"):
            st.switch_page(WORLD_MAP)
        if st.button("See the main finding", icon=":material/insights:"):
            st.switch_page(FINDINGS)
        if st.button("Open a country timeline", icon=":material/timeline:"):
            st.switch_page(COMPARE)
    st.divider()
    st.pills(":gray[Or jump straight to a group of countries:]", START_GROUPS, key="start_group", on_change=group_chosen,
             wrap=True)

with right:
    y, g = latest_year()
    with st.container(border=True):
        with st.container(horizontal=True, vertical_alignment="center"):
            st.markdown(f"**Regimes of the world in {y}**", width="stretch")
            st.button("Open on the map", icon=":material/arrow_forward:", type="tertiary", key="start_open_map",
                      help=f"Open the World map at {y}", on_click=open_map, args=(y,))

        def map_clicked():
            pts = (ss["start_map"].get("selection") or {}).get("country") or []
            if pts and pts[0].get("iso3"):
                open_map(y, pts[0]["iso3"])

        st.altair_chart(preview_map(y), key="start_map", on_select=map_clicked, selection_mode="country", width="stretch",
                        alt=f"World map of regime types in {y}. Click a country to open it on the World map.")
        st.markdown(legend_line(nr.REGIMES, nr.REG_COLS))
        st.caption("Preview · latest year. Click a country to open it on the World map.")
        stats = [(int(g["regime_type"].notna().sum()), f"countries with data in {y}"),
                 (int((g["regime_type"] >= 2).sum()), f"democracies in {y}"),
                 (int((g["regime_type"] <= 1).sum()), f"autocracies in {y}"),
                 (int(g["conflict_active"].sum()), "with armed conflict")]
        for col, (n, label) in zip(st.columns(4), stats):
            col.metric(label, n, label_visibility="collapsed")  # number first, its label below (as in the HTML)
            col.caption(label)

# ------------------------------------------------------------------ three ways to explore
st.space("medium")
st.subheader("Three ways to explore", anchor=False)
STEPS = [
    ("1", "World map", "Pick any year from 1950 to 2025 and see which countries were democracies, autocracies or at war. "
     "Press play to watch the years go by.", "Open the map", WORLD_MAP),
    ("2", "One country over time", "Follow one country: regime, democracy index, armed conflicts and arms imports on one "
     "shared year axis.", "Open a timeline", COMPARE),
    ("3", "Compare countries", "Put several countries, or a whole group like the EU or Latin America, side by side.",
     "Start comparing", COMPARE),
]
for col, (num, title, text, go_label, page) in zip(st.columns(3), STEPS):
    with col.container(border=True, height="stretch"):
        st.markdown(f":primary-badge[{num}]")
        st.markdown(f"#### {title}")
        st.markdown(f":gray[{text}]")
        st.space("stretch")  # the links of the three cards line up at the bottom
        if st.button(go_label, icon=":material/arrow_forward:", key=f"step_{num}", type="tertiary"):
            st.switch_page(page)
