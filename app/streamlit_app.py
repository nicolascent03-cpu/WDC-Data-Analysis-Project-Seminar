"""Conflict, Democracy and Arms: the Streamlit app.

Written together, one person edits at a time. Do your try_streamlit_<name>.py exercises first.
Run from the repo root:  streamlit run app/streamlit_app.py
Rule: the app only reads files from data/clean/. It never cleans data.

Work through the steps below. Write your code under each step. Save the file,
look at the browser, then go to the next step. Commit after every step that works.
"""

# ---------------------------------------------------------------- Step 1: imports
# Import pandas, plotly.express (as px), streamlit (as st) and os.
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


# ---------------------------------------------------------------- Step 4: navigation
# A radio button in the sidebar with three pages: "Overview", "Country", "Analysis".
# Hint: st.sidebar.radio(label, list_of_options) returns the chosen option.
# Then an if / elif / else block, one part per page. Start with st.title("...") in each part.


# ---------------------------------------------------------------- Step 5: Overview page
# 1. A sentence with the research question (st.write).
# 2. A year slider from 1950 to 2025 (st.slider).
# 3. A choice between democracy_index and arms_imports_tiv (st.radio).
# 4. The world map for the chosen year and column (st.plotly_chart with your world_map function).
# 5. Two global trend lines: share of countries in conflict per year, total arms imports per year.
#    Compute them here with a small groupby on panel (one line each), then draw with px.line.


# ---------------------------------------------------------------- Step 6: Country page
# 1. The country choice in the sidebar (exercise 8). Draw the page radio from step 4 first, then the
#    country choice, both ABOVE the page if / elif / else, so it is drawn on every page and remembers
#    the choice (exercise 14, fix 1). If the search finds nothing, show st.sidebar.info and call
#    st.stop() only inside the Country part; otherwise the other pages go blank too.
# 2. Find the iso3 code that belongs to the chosen name (filter panel, take the first value).
# 3. A year slider.
# 4. Three numbers next to each other: st.columns(3), then st.metric in each column
#    (democracy index in that year, number of conflict years, total arms imports).
# 5. The five timelines under each other: regime_bands, conflict_bars, democracy_line,
#    arms_line, supplier_area. Pass the chosen year so the dashed line moves with the slider.
#    Give every st.plotly_chart its own key (key="regime", key="conflict", ...). Two identical
#    empty charts on one page otherwise stop the app with a duplicate element error.
# 6. Test with a country without conflict (Switzerland) and one without imports.


# ---------------------------------------------------------------- Step 7: Analysis page
# 1. The main chart (main_chart with event_time).
# 2. How many onsets are in each group (from event_time or a small table you saved in 06).
# 3. Your three findings and the sentence on what the chart cannot show (st.markdown).


# ---------------------------------------------------------------- Step 8: bonus feature
# Add it only after steps 1 to 7 work. Build it in your try_streamlit file first.
# For the country comparison, use st.columns(2) and different keys for left and right charts
# (key="conflict_left", key="conflict_right"). Also give the two country dropdowns different keys
# (key="country_left", key="country_right"), otherwise Streamlit stops with a duplicate element error.
