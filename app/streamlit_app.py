"""Conflict, Democracy and Arms: the Streamlit app.

Written together, one person edits at a time. Do your try_streamlit_<name>.py exercises first.
Run from the repo root:  streamlit run app/streamlit_app.py
Rule: the app only reads files from data/clean/. It never cleans data.

Work through the steps below. Write your code under each step. Save the file,
look at the browser, then go to the next step. Commit after every step that works.
"""

# ---------------------------------------------------------------- Step 1: imports
# Import os, pandas (as pd), matplotlib.pyplot (as plt) and streamlit (as st).
# Import your chart functions from panels_conflict, panels_arms and panels_analysis.


# ---------------------------------------------------------------- Step 2: page settings
# Use st.set_page_config with a page title and layout="wide".


# ---------------------------------------------------------------- Step 3: load the data
# Write a function load(name) that reads data/clean/<name>.csv and returns the dataframe.
# Put @st.cache_data on the line above it, so Streamlit reads each file only once.
# Hint: the folder path, seen from this file, is os.path.join(os.path.dirname(__file__), "..", "data", "clean")
# Load panel, vdem_regime_spans, ucdp_spans, sipri_suppliers, event_time.
# Load only the files that already exist; add the others when their notebook is done
# (event_time.csv only exists after 06). Otherwise the app stops with an error.
# Test: st.write(panel.shape) should show the size of panel in the browser. Remove it afterwards.


# ---------------------------------------------------------------- Step 4: sidebar
# 1. A radio button in the sidebar with three pages: "Overview", "Country", "Analysis"
#    (st.sidebar.radio(label, list_of_options) returns the chosen option).
# 2. Below it, the country choice: a plain st.sidebar.selectbox with the sorted country names
#    (try_streamlit exercise 8, part 8). Because it is drawn before the pages, it remembers the choice on every page
#    (exercise 14).
# 3. Then an if / elif / else block, one part per page. Start with st.title("...") in each part.


# ---------------------------------------------------------------- Step 5: Overview page
# 1. A sentence with the research question (st.write).
# 2. A year slider from 1950 to 2025 (st.slider).
# 3. fig, ax = plt.subplots(figsize=(10, 2.5)), then global_trends(ax, panel, year), then st.pyplot(fig).
# 4. The top 10 importers in the chosen year as a small table (filter, sort, head, st.dataframe).


# ---------------------------------------------------------------- Step 6: Country page
# 1. Find the iso3 code that belongs to the chosen name (filter panel, take the first value).
# 2. A year slider.
# 3. Three numbers next to each other: st.columns(3), then st.metric in each column
#    (democracy index in that year, number of conflict years, total arms imports).
#    If the country has no row for that year, show "n/a" (exercise 10).
# 4. The five timelines as one figure, exactly as in the "Final look check" of 07_charts:
#      fig, axes = plt.subplots(5, 1, sharex=True, figsize=(10, 8))
#      regime_bands(axes[0], ...), conflict_bars(axes[1], ...), democracy_line(axes[2], ...),
#      arms_line(axes[3], ...), supplier_bars(axes[4], ...)
#      plt.tight_layout()
#      st.pyplot(fig)
# 5. Test with a country without conflict (Switzerland) and one without imports.


# ---------------------------------------------------------------- Step 7: Analysis page
# 1. The main chart: fig, ax = plt.subplots(figsize=(8, 4)), main_chart(ax, event_time), st.pyplot(fig).
# 2. How many onsets are in each group (from event_time at t = 0).
# 3. Your three findings and the sentence on what the chart cannot show (st.markdown).


# ---------------------------------------------------------------- Step 8: bonus feature
# Add it only after steps 1 to 7 work. Build it in your try_streamlit file first.
# For the country comparison: st.columns(2), one stacked figure per column, and two country
# dropdowns with different keys (key="country_left", key="country_right"), and two year sliders with
# different keys (key="year_left", key="year_right"), otherwise Streamlit stops with a duplicate
# element error.
