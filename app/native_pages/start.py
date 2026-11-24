"""Start page: the hero with its three entry points, a preview map of the latest year and the three ways to explore."""

import plotly.graph_objects as go
import streamlit as st

import native_results as nr

WORLD_MAP, COMPARE, FINDINGS = "native_pages/world_map.py", "native_pages/compare.py", "native_pages/findings.py"
# Shortcut groups, as START_GROUPS in app/site/adc.html
START_GROUPS = ["Former Soviet Union", "European Union (27)", "Latin America", "North America",
                "Middle East and North Africa", "G7"]

ss = st.session_state


def group_chosen():
    """Remember the group for the compare page, then leave from the script body (switch_page is not allowed here)."""
    name = ss.get("start_group")
    if name:
        ss["cmp_group"] = name
        ss["start_go"] = COMPARE
    ss["start_group"] = None


if ss.pop("start_go", None):
    st.switch_page(COMPARE)


@st.cache_data
def latest_year():
    panel = nr.load_panel()
    y = int(panel["year"].max())
    return y, panel[panel["year"] == y]


@st.cache_data
def preview_map(y):
    g = latest_year()[1]
    fig = go.Figure()
    for k, (name, col) in enumerate(zip(nr.REGIMES, nr.REG_COLS)):
        p = g[g["regime_type"] == k]
        fig.add_trace(go.Choropleth(
            locations=p["iso3"], z=[k] * len(p), zmin=0, zmax=3, colorscale=[[0, col], [1, col]], showscale=False,
            name=name, showlegend=True, marker_line_color="#151514", marker_line_width=0.4,
            text=p["country_name"] + "<br>" + name + ", democracy index " + p["democracy_index"].round(2).astype(str),
            hoverinfo="text"))
    fig.update_geos(projection_type="equal earth", showframe=False, showcoastlines=False, showcountries=True,
                    countrycolor="#151514", showland=True, landcolor="#2a2a28", showocean=False, bgcolor=nr.BG,
                    lataxis_range=[-58, 85])
    fig.update_layout(height=330, margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor=nr.BG, dragmode=False,
                      legend=dict(orientation="h", x=0.01, xanchor="left", y=-0.02, yanchor="top", entrywidth=0.245, entrywidthmode="fraction",
                                  font=dict(color=nr.INK2, family="IBM Plex Sans", size=11)),
                      hoverlabel=dict(bgcolor=nr.INK, font_color="#111110", font_family="IBM Plex Sans"))
    return fig


# ------------------------------------------------------------------ hero
left, right = st.columns([1.05, 1], gap="large", vertical_alignment="center")
with left:
    st.markdown(":primary[**Seminar project · 1950 to 2025**]")
    st.title("Arms, Democracy and Conflict", anchor=False)
    st.markdown("What happens to democracy during and after armed conflict, and does it look different in countries "
                "that import many weapons? Explore regimes, wars and arms deliveries from 1950 to 2025.")
    with st.container(horizontal=True):
        if st.button("Explore the world map", type="primary", icon=":material/public:"):
            st.switch_page(WORLD_MAP)
        if st.button("Open a country timeline", icon=":material/timeline:"):
            st.switch_page(COMPARE)
        if st.button("See the main finding", icon=":material/insights:"):
            st.switch_page(FINDINGS)
    st.space("small")
    st.pills("Or jump straight to a group of countries:", START_GROUPS, key="start_group", on_change=group_chosen,
             wrap=True)

with right:
    y, g = latest_year()
    with st.container(border=True):
        head_l, head_r = st.columns([3, 1.3], vertical_alignment="bottom")
        head_l.markdown(f"**Regimes of the world in {y}**")
        head_r.caption("Preview · latest year")
        st.plotly_chart(preview_map(y), config={"displayModeBar": False, "scrollZoom": False}, key="start_map")
        m = st.columns(4)
        m[0].metric("Countries with data", int(g["regime_type"].notna().sum()))
        m[1].metric("Democracies", int((g["regime_type"] >= 2).sum()))
        m[2].metric("Autocracies", int((g["regime_type"] <= 1).sum()))
        m[3].metric("With armed conflict", int(g["conflict_active"].sum()))

# ------------------------------------------------------------------ three ways to explore
st.space("medium")
st.subheader("Three ways to explore", anchor=False)
STEPS = [
    ("1", "World map", "Pick any year from 1950 to 2025 and see which countries were democracies, autocracies or at war. "
     "Press play to watch the years go by.", "Open the map", ":material/public:", WORLD_MAP),
    ("2", "One country over time", "Follow one country: regime, democracy index, armed conflicts and arms imports on one "
     "shared year axis.", "Open a timeline", ":material/timeline:", COMPARE),
    ("3", "Compare countries", "Put several countries, or a whole group like the EU or Latin America, side by side.",
     "Start comparing", ":material/compare_arrows:", COMPARE),
]
for col, (num, title, text, go_label, icon, page) in zip(st.columns(3), STEPS):
    with col.container(border=True, height="stretch"):
        st.markdown(f":primary[{icon} **{num}**]")
        st.markdown(f"#### {title}")
        st.markdown(text)
        if st.button(go_label, icon=":material/arrow_forward:", key=f"step_{num}", type="tertiary"):
            st.switch_page(page)
