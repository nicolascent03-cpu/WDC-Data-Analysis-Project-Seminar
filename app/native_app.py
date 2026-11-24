"""ADC: Arms, Democracy and Conflict, built with Streamlit.

Run from the repo root:  streamlit run app/native_app.py

Pages live in app/native_pages/. Data comes from data/clean/ through app/native_data.py and
app/native_results.py (regression results of notebook 08, or placeholders until they exist).
Two small custom components in app/native_components/ draw what Streamlit cannot: the chord ring with
its country card, and the regimes map with striped conflict countries.
The earlier HTML prototype still runs as app/adc_app.py.
"""

import streamlit as st

st.set_page_config(page_title="ADC: Arms, Democracy and Conflict", page_icon=":material/public:", layout="wide")

pages = st.navigation([
    st.Page("native_pages/start.py", title="Start", icon=":material/home:", default=True),
    st.Page("native_pages/world_map.py", title="World map", icon=":material/public:"),
    st.Page("native_pages/findings.py", title="Findings", icon=":material/insights:"),
    st.Page("native_pages/compare.py", title="Countries & compare", icon=":material/compare_arrows:"),
    st.Page("native_pages/about.py", title="About the data", icon=":material/info:"),
], position="top")
pages.run()
