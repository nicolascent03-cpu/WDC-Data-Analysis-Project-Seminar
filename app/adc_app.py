"""ADC: Arms, Democracy and Conflict, the finished website inside Streamlit.

Run from the repo root:  streamlit run app/adc_app.py

The website (start page, map, country timelines with comparison, data notes) is one HTML
template in app/site/adc.html. Its data sits next to it in data.json and mapdata.json.
This script joins them and shows the page. Refresh the data from a new export with
tools/build_adc_site.py.
"""

from pathlib import Path

import streamlit as st

SITE = Path(__file__).parent / "site"

st.set_page_config(page_title="ADC: Arms, Democracy and Conflict", layout="wide")


FILES = ["adc.html", "data.json", "mapdata.json"]


@st.cache_data(max_entries=2)
def build_page(mtimes):
    # mtimes is only the cache key: editing any of the three files rebuilds the page.
    page, data, mapdata = [(SITE / name).read_text(encoding="utf8") for name in FILES]
    return page.replace("__ADC_DATA__", data).replace("__ADC_MAPDATA__", mapdata)


page = build_page(tuple((SITE / name).stat().st_mtime for name in FILES))
st.iframe(page, height="content", alt="ADC: Arms, Democracy and Conflict website")
