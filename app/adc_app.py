"""ADC: Arms, Democracy and Conflict, the finished website inside Streamlit.

Run from the repo root:  streamlit run app/adc_app.py

The website (start page, map, country timelines with comparison, findings, data notes) is one HTML
template in app/site/adc.html. app/site_page.py joins it with its data (data.json, mapdata.json),
the arms-flow script (flows.js) and the regression results of notebook 08 (data/clean/reg_*.csv, or
placeholders from data/demo/ until those exist). Refresh the data from a new export with
tools/build_adc_site.py.
"""

import streamlit as st

import site_page

st.set_page_config(page_title="ADC: Arms, Democracy and Conflict", layout="wide")


@st.cache_data(max_entries=2)
def build_page(mtimes):
    # mtimes is only the cache key: editing any input file rebuilds the page.
    return site_page.assemble()


st.iframe(build_page(site_page.input_mtimes()), height="content", alt="ADC: Arms, Democracy and Conflict website")
