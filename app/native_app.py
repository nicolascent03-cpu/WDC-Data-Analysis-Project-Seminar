"""ADC: Arms, Democracy and Conflict, built with Streamlit.

Run from the repo root:  streamlit run app/native_app.py

Pages live in app/native_pages/. Data comes from data/clean/ through app/native_data.py and
app/native_results.py (regression results of notebook 08, or placeholders until they exist).
Two small custom components in app/native_components/ draw what Streamlit cannot: the chord ring with
its country card, and the regimes map with striped conflict countries.
The earlier HTML prototype still runs as app/adc_app.py.
"""

from pathlib import Path

import streamlit as st

import native_data as nd

ASSETS = Path(__file__).parent / "native_assets"
COMPARE = "native_pages/compare.py"

st.set_page_config(page_title="ADC: Arms, Democracy and Conflict", page_icon=":material/public:", layout="wide")
# the mark of the HTML top bar ("ADC" on the accent, then the name); the small one shows when the sidebar is closed
st.logo(str(ASSETS / "logo.svg"), size="large", icon_image=str(ASSETS / "logo_icon.svg"))


@st.cache_data
def country_names():
    p = nd.load_panel().drop_duplicates("iso3")
    return dict(sorted(zip(p["iso3"], p["country_name"]), key=lambda kv: kv[1]))


def country_searched():
    """The HTML top bar's "Search a country": open that country's timeline in Countries & compare."""
    iso = st.session_state.pop("g_search", None)
    if iso:
        st.session_state["cmp_countries"] = [iso]  # one-shot hand-over, read by the compare page
        st.session_state["playing"] = False
        st.session_state["_g_go"] = True


pages = st.navigation([
    st.Page("native_pages/start.py", title="Start", icon=":material/home:", default=True),
    st.Page("native_pages/world_map.py", title="World map", icon=":material/public:"),
    st.Page("native_pages/findings.py", title="Findings", icon=":material/insights:"),
    st.Page("native_pages/compare.py", title="Countries & compare", icon=":material/compare_arrows:"),
    st.Page("native_pages/about.py", title="About the data", icon=":material/info:"),
], position="sidebar", expanded=True)

if st.session_state.pop("_g_go", False):
    st.switch_page(COMPARE)
# the search box of the HTML top bar, under the page menu (Countries & compare has its own country picker)
if pages.url_path != "compare":
    names = country_names()
    with st.sidebar:
        st.selectbox("Search a country", list(names), format_func=names.get, index=None, key="g_search",
                     on_change=country_searched, placeholder="Search a country", label_visibility="collapsed",
                     help="Opens the country's timeline in Countries & compare")
pages.run()

# The data sources under every page's own sidebar controls (the page menu sits at the top of the sidebar).
with st.sidebar:
    st.divider()
    st.caption("**Data:** V-Dem v16 (regimes and democracy index), UCDP/PRIO 26.1 (armed conflict), "
               "SIPRI Arms Transfers (TIV), 1950–2025.")
