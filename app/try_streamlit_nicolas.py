"""Streamlit practice. Each of you works only in your own copy (try_streamlit_nicolas.py or
try_streamlit_yair.py), so you never get merge conflicts.

Run from the repo root:  streamlit run app/try_streamlit_<your name>.py
Leave it running. After every save, click "Rerun" (or "Always rerun") in the browser.
This file is only for learning. Nothing here goes into the final app unchanged.
Docs: https://docs.streamlit.io (search for the function names below).

Part 1 teaches the basics. Part 2 builds a small version of our real app step by step,
so you know how it should look and feel before you write streamlit_app.py.
Exercises 1 to 4 need no data: do them now (week 1). You need data/clean/panel.csv for
exercise 5 onwards (from notebook 05).

Charts: we use matplotlib, as in the week 5 data viz lecture. Make the chart with
fig, ax = plt.subplots(), draw on ax, then show it in the app with st.pyplot(fig).

One warning: if two identical widgets (for example two dropdowns with the same label) are on
one page, Streamlit stops with a "duplicate element" error. Give each its own key, for example
st.selectbox("Country", names, key="country_left").

------------------------------------------------------------------------------------
HOW THE FINISHED APP SHOULD LOOK AND FEEL
------------------------------------------------------------------------------------
- Calm and readable: white background, one main colour, lots of space, few words.
- Left sidebar: page choice (Overview, Country, Analysis) and the country search.
- Country page from top to bottom:
    country name as title, one sentence of context
    one year slider
    three numbers in a row (democracy index, conflict years, total arms imports)
    five thin timelines stacked like one picture: regime bands, conflict bars,
    democracy line, arms imports, suppliers. Same x-axis 1950 to 2025, same width,
    small gaps, a dashed line at the chosen year in every chart.
- Same colour for the same thing everywhere (for example liberal democracy is always
  the same blue, a war is always the same dark red).
- Never an error on screen: a country without data shows a short grey message.
- The user should understand a country's story in 10 seconds without reading code.
"""

# ==================================================================================
# PART 1: BASICS
# ==================================================================================

# Exercise 1: import streamlit as st and show a title with st.title("...").
# Save and look at the browser.


# Exercise 2: show a sentence with st.write("..."). Then show a number, for example st.write(3 + 4).


# Exercise 3: a slider. year = st.slider("Year", 1950, 2025, 2000)
# Then st.write(year). Move the slider. What happens to the whole script each time you move it?


# Exercise 4: a dropdown. Make a list of three country names and use st.selectbox.
# Show the chosen name with st.write.


# Exercise 5: load data/clean/panel.csv with pandas and show the first 20 rows with st.dataframe.
# Put @st.cache_data on a small load function. Add print("loading") inside it and watch the
# terminal: how often does it print when you move the slider, with and without the decorator?


# Exercise 6: filter panel to one country (for example "UKR") and draw democracy_index over time:
#   import matplotlib.pyplot as plt
#   fig, ax = plt.subplots(figsize=(8, 2))
#   ax.plot(rows["year"], rows["democracy_index"])
#   st.pyplot(fig)
# (the same as in the notebooks, only plt.show() becomes st.pyplot(fig))


# Exercise 7: write in a comment, in your own words: why does Streamlit run the whole file again
# every time you move a slider, and what does @st.cache_data change about that?


# ==================================================================================
# PART 2: A SMALL VERSION OF OUR APP
# ==================================================================================

# Exercise 8: SEARCH BAR, the simple way.
# 1. In the sidebar, a text field: search = st.sidebar.text_input("Search a country")
# 2. Make a sorted list of all country names from panel.
# 3. Loop over the names. If the search text, in lower case, is part of the name in lower case,
#    add the name to a list called matches.   (Hint: "ukr" in "Ukraine".lower())
# 4. If the search field is empty, matches should be all names.
# 5. Show the matches in a st.sidebar.selectbox. Type "kor" and check that both Koreas appear.
# 6. If there are no matches, show st.sidebar.info("No country found") and skip the dropdown,
#    and stop the page with st.stop().
# 7. Question: in step 4 you may not need extra code at all. Why does an empty search text match
#    every name? (Hint: is "" in "Ukraine"?)
# 8. Now try a plain st.sidebar.selectbox with all names and type "kor" into it. Current Streamlit
#    already filters while you type. For the real app, choose the simpler version that does the
#    job, and write in a comment why.


# Exercise 9: NAME TO CODE.
# The user picks a name, but our charts need iso3. Filter panel to the chosen name and take the
# first iso3 value. Show it small with st.caption(iso3) to check it is right.


# Exercise 10: HEADER WITH NUMBERS.
# 1. st.title with the country name.
# 2. A year slider.
# 3. Three columns with st.columns(3). In each, one st.metric:
#    democracy index in the chosen year, number of years with conflict, total arms imports.
#    Compute each number in its own lines above (filter, then sum or take the value).
# 4. Optional: in the democracy metric, show the change since the year before with delta=...
# 5. Ukraine has no rows for the years before its independence. If the filtered table for the chosen year is empty, show
#    st.metric("Democracy index", "n/a"), so the app does not crash. Round numbers with round(x, 2)
#    before you pass them, also the delta.


# Exercise 11: STACKED TIMELINES THAT LOOK LIKE ONE PICTURE.
# 1. One figure with three drawing areas under each other that share the year axis:
#      fig, axes = plt.subplots(3, 1, sharex=True, figsize=(10, 5))
# 2. Draw democracy_index on axes[0] (ax.plot), arms_imports_tiv on axes[1] (ax.bar) and
#    conflict_active on axes[2] (ax.bar) for the chosen country.
# 3. On each ax: a short title (ax.set_title) and a y-label with the unit. Set the year range once:
#    axes[0].set_xlim(1950, 2025). Because of sharex=True, all three follow.
# 4. A dashed line at the slider year on every ax: ax.axvline(year, linestyle="--", color="grey").
#    A loop does it in two lines: for ax in axes: ax.axvline(...)
# 5. plt.tight_layout(), then st.pyplot(fig).
# Move the slider and watch the line move in all three.
# Later in the app, the same five charts come from your functions in the panels files.


# Exercise 12: ONE COLOUR SYSTEM.
# 1. Write a dictionary regime_colours with one colour (hex code, for example "#1D4E89") for each
#    of the four regime labels.
# 2. Count how many years the country spent in each regime type (value_counts) and draw a bar
#    chart: ax.bar(labels, counts, color=[regime_colours[l] for l in labels]).
# 3. Agree with Yair on the final colours and write them into 07_charts.ipynb.


# Exercise 13: NO ERRORS ON SCREEN.
# Pick a country with no arms imports or no conflict. Before drawing a chart, check if the filtered
# table is empty or all zeros. If so, show st.caption("No arms imports recorded") and skip the chart.


# Exercise 14: PAGES AND REMEMBERING THE COUNTRY.
# 1. A sidebar radio with "Overview" and "Country". Show different content with if / else.
# 2. Put the country dropdown inside the "Country" part, choose a country, switch to Overview
#    and back. The choice is forgotten, because the dropdown was not drawn on the other page.
# 3. Fix 1 (use this in the app): move the country dropdown ABOVE the if / else, so it is drawn on
#    every page. Then it remembers the choice by itself.
# 4. Fix 2 (only to learn session_state): save the chosen name in st.session_state["country"].
#    Next time, if the saved name is in your list, pass index=names.index(saved_name) to the
#    selectbox, otherwise index=0. (Docs: search "session state")


# Exercise 15: THEME.
# Create the folder .streamlit in the repo root and inside it a file config.toml with:
#   [theme]
#   base = "light"
#   primaryColor = "#1D4E89"
#   backgroundColor = "#FFFFFF"
#   textColor = "#333333"
#   font = "sans-serif"
# (base = "light" keeps the white look on laptops in dark mode. Choose your own primaryColor.)
# Restart streamlit. Which elements changed colour?


# Exercise 16: COMPARE YOURSELF WITH THE GOAL.
# Look at the description at the top of this file and at your page. Write three things in a comment
# that are still different, and how you would fix them in the real app.
