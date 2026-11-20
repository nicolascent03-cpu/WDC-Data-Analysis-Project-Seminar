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
# 3. Agree with Nicolas on the final colours and write them into 07_charts.ipynb.


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
"""Conflict, Democracy and Arms: the full app, built in Yair's practice file.

Run from the repo root:  streamlit run app/try_streamlit_yair.py
Rule: the app only reads files from data/clean/. It never cleans data.
"""

# ---------------------------------------------------------------- imports
import os
import time
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

# ---------------------------------------------------------------- page settings
st.set_page_config(page_title="Conflict, Democracy and Arms", page_icon="🌍", layout="wide")

BRAND = "#A33A1E"

regime_colours = {
    "closed autocracy": "#B8312F",
    "electoral autocracy": "#F2A68F",
    "electoral democracy": "#A9C8F2",
    "liberal democracy": "#1F5BA8",
}
intensity_names = {0: "none", 1: "minor", 2: "war"}
intensity_colours = {"war": "#222222", "minor": "#BDBDBD"}

supplier_colours = {
    "United States": "#2E6FDB",
    "Soviet Union": "#D7263D",
    "Russia": "#E7739A",
    "United Kingdom": "#1BA672",
    "France": "#6C4CE0",
    "China": "#F26B38",
    "Germany": "#F2B134",
    "Italy": "#00A6A6",
    "Israel": "#8C6D46",
    "Other": "#CFCFCF",
}
spare_colours = ["#7A9E3E", "#B565A7", "#5B8DB8", "#D98E04", "#8E8E8E"]

PERIODS = {"1950–2025": (1950, 2025), "Cold War": (1950, 1991), "Since 1992": (1992, 2025)}

# ---------------------------------------------------------------- CSS
st.markdown(
    f"""
    <style>
    .stApp {{background-color: #FBF8F5;}}
    .block-container {{padding-top: 1.2rem; max-width: 1300px;}}
    header[data-testid="stHeader"] {{background: transparent;}}
    div[data-testid="stVerticalBlockBorderWrapper"] {{background-color: white; border-radius: 12px;}}
    .brand {{
        display: inline-block; background: {BRAND}; color: white; font-weight: 700;
        padding: 6px 14px; border-radius: 4px; transform: rotate(-2deg); font-size: 1.05rem;
    }}
    .kicker {{color: {BRAND}; font-size: 0.78rem; font-weight: 700; letter-spacing: 0.08em; margin-bottom: 0;}}
    .sub {{color: #777; font-size: 0.85rem; margin-top: 0;}}
    .cname {{color: {BRAND}; font-size: 1.9rem; font-weight: 700; margin: 0; line-height: 1.3;}}
    .badge {{
        float: right; background: #F1EEEA; color: #555; border-radius: 10px;
        padding: 2px 10px; font-size: 0.75rem; margin-top: 10px;
    }}
    .tiles {{display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin: 8px 0 14px 0;}}
    .tile {{background: #F6F4F1; border-radius: 8px; padding: 10px 12px; min-height: 92px;}}
    .tile .lab {{color: #888; font-size: 0.72rem;}}
    .tile .val {{font-weight: 700; font-size: 1.0rem; font-family: ui-monospace, monospace; margin: 2px 0;}}
    .tile .note {{color: #888; font-size: 0.72rem;}}
    .sec {{font-weight: 700; font-size: 1.05rem; margin: 10px 0 0 0;}}
    .sec span {{font-weight: 400; color: #999; font-size: 0.8rem;}}
    .chip {{display: inline-block; margin-right: 12px; font-size: 0.8rem; color: #444;}}
    .chip i {{display: inline-block; width: 10px; height: 10px; border-radius: 2px; margin-right: 5px;}}
    .read {{color: #777; font-size: 0.8rem; border-left: 3px solid #E8E2DC; padding-left: 8px; margin: 4px 0 10px 0;}}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------- load the data
CLEAN = os.path.join(os.path.dirname(__file__), "..", "data", "clean")


@st.cache_data
def load(name):
    path = os.path.join(CLEAN, name + ".csv")
    return pd.read_csv(path)


panel = load("panel")
vdem_regime_spans = load("vdem_regime_spans")
ucdp_spans = load("ucdp_spans")
sipri_suppliers = load("sipri_suppliers")
event_time = load("event_time")

names = sorted(panel["country_name"].unique())


# ---------------------------------------------------------------- small helpers
def name_to_iso3(name):
    rows = panel[panel["country_name"] == name]
    return rows["iso3"].iloc[0]


def chips(colours):
    html = ""
    for label, colour in colours.items():
        html = html + f'<span class="chip"><i style="background:{colour}"></i>{label[0].upper() + label[1:]}</span>'
    return html


def section(title, note=""):
    st.markdown(f'<p class="sec">{title} <span>{note}</span></p>', unsafe_allow_html=True)


def how_to_read(text):
    st.markdown(f'<p class="read">{text}</p>', unsafe_allow_html=True)


def colour_for_supplier(name, position):
    if name in supplier_colours:
        return supplier_colours[name]
    return spare_colours[position % len(spare_colours)]


def style(fig, height, start, end, year):
    """Same look for every Plotly chart: white background, light grid, shared year axis, year marker."""
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=10, b=10),
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(size=11, color="#444"),
        showlegend=False,
        bargap=0.15,
        hoverlabel=dict(bgcolor="white"),
    )
    fig.update_xaxes(range=[start - 0.5, end + 0.5], showgrid=True, gridcolor="#EEEEEE", zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="#F2F2F2", zeroline=False)
    if year is not None:
        fig.add_vline(x=year, line_color=BRAND, line_width=2)
    return fig


def show(fig):
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


# ---------------------------------------------------------------- Country timeline helpers (ct_)
CT_A = BRAND        # colour of the main country in the compare view
CT_B = "#2F6690"    # colour of the comparison country
CT_UP = "#1B7F4C"   # democracy went up
CT_EXAMPLES = ["Ukraine", "Pakistan", "Chile", "Sri Lanka", "Hungary", "Switzerland"]

st.markdown(
    f"""
    <style>
    .ct-story {{
        background: #FBF3EF; border-left: 4px solid {BRAND}; border-radius: 6px;
        padding: 10px 14px; margin: 6px 0 4px 0; font-size: 0.86rem; color: #333;
    }}
    .ct-story .ct-title {{color: {BRAND}; font-size: 0.7rem; font-weight: 700; letter-spacing: 0.08em; margin-bottom: 4px;}}
    .ct-story ul {{margin: 0; padding-left: 18px;}}
    .ct-story li {{margin: 2px 0;}}
    .ct-story b {{font-weight: 700; color: #111;}}
    .ct-tiles2 {{grid-template-columns: repeat(2, 1fr) !important;}}
    .ct-delta {{font-size: 0.72rem; font-weight: 600;}}
    .ct-spark {{display: block; width: 100%; height: 26px; margin-top: 4px;}}
    .ct-try {{color: #888; font-size: 0.78rem; margin: 0;}}
    .st-key-ct_try div[data-testid='stMarkdownContainer'] p {{margin-bottom: 0;}}
    .st-key-ct_try {{gap: 6px !important;}}
    .st-key-ct_try button {{
        border-radius: 999px; min-height: 26px; padding: 0 12px; font-size: 0.8rem;
        background: white; border: 1px solid #E5DED8; color: #555;
    }}
    .st-key-ct_try button:hover {{border-color: {BRAND}; color: {BRAND};}}
    .st-key-ct_try p {{font-size: 0.8rem;}}
    .ct-vs {{width: 100%; border-collapse: collapse; font-size: 0.82rem; margin-top: 6px;}}
    .ct-vs th {{text-align: left; font-weight: 700; padding: 6px 8px; border-bottom: 2px solid #EEE;}}
    .ct-vs td {{padding: 5px 8px; border-bottom: 1px solid #F2EFEC;}}
    .ct-vs td.num {{font-family: ui-monospace, monospace;}}
    .ct-vs td.lab {{color: #777;}}
    .ct-dot {{display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 6px;}}
    </style>
    """,
    unsafe_allow_html=True,
)


def ct_rows(iso3, start, end):
    """Panel rows of one country inside the chosen period, sorted by year."""
    rows = panel[(panel["iso3"] == iso3) & panel["year"].between(start, end)]
    return rows.sort_values("year")


def ct_conflict_runs(iso3, start, end):
    """Group consecutive conflict years into runs: [{'start', 'end', 'level'}, ...]."""
    rows = ct_rows(iso3, start, end)
    rows = rows[rows["conflict_active"] == 1]
    runs = []
    for y, level in zip(rows["year"], rows["max_intensity"]):
        if len(runs) > 0 and y == runs[-1]["end"] + 1:
            runs[-1]["end"] = y
            runs[-1]["level"] = max(runs[-1]["level"], int(level))
        else:
            runs.append({"start": int(y), "end": int(y), "level": int(level)})
    return runs


def ct_value(iso3, column, year):
    """One value from the panel, or None if the country has no row that year."""
    row = panel[(panel["iso3"] == iso3) & (panel["year"] == year)]
    if len(row) == 0:
        return None
    return row[column].iloc[0]


def ct_delta(iso3, column, year, fmt, colour_up, colour_down):
    """Small arrow text: change compared with 5 years earlier."""
    now = ct_value(iso3, column, year)
    before = ct_value(iso3, column, year - 5)
    if now is None or before is None:
        return f'<span class="ct-delta" style="color:#AAA">no data for {year - 5}</span>'
    diff = now - before
    if diff > 0:
        arrow, colour = "▲", colour_up
    elif diff < 0:
        arrow, colour = "▼", colour_down
    else:
        arrow, colour = "▶", "#999"
    return f'<span class="ct-delta" style="color:{colour}">{arrow} {diff:{fmt}} vs {year - 5}</span>'


def ct_sparkline(iso3, start, end, year):
    """Tiny SVG of the democracy index in the period: grey = conflict years, red line = chosen year."""
    rows = ct_rows(iso3, start, end)
    if len(rows) < 2:
        return ""
    width = max(end - start, 1)
    shapes = ""
    for run in ct_conflict_runs(iso3, start, end):
        x0 = (run["start"] - 0.5 - start) / width * 100
        x1 = (run["end"] + 0.5 - start) / width * 100
        shapes = shapes + f'<rect x="{x0:.1f}" y="0" width="{x1 - x0:.1f}" height="24" fill="#E4DED8"/>'
    points = ""
    for y, v in zip(rows["year"], rows["democracy_index"]):
        points = points + f"{(y - start) / width * 100:.1f},{(1 - v) * 22 + 1:.1f} "
    x_year = (year - start) / width * 100
    return (
        f'<svg class="ct-spark" viewBox="0 0 100 24" preserveAspectRatio="none">{shapes}'
        f'<polyline points="{points}" fill="none" stroke="#222" stroke-width="1.3" vector-effect="non-scaling-stroke"/>'
        f'<line x1="{x_year:.1f}" x2="{x_year:.1f}" y1="0" y2="24" stroke="{BRAND}" stroke-width="1.5" '
        f'vector-effect="non-scaling-stroke"/></svg>'
    )


def ct_top_supplier(iso3, first, last):
    """Named supplier (not 'Other') with the most TIV between two years, or None."""
    rows = sipri_suppliers[(sipri_suppliers["iso3"] == iso3) & sipri_suppliers["year"].between(first, last)
                           & (sipri_suppliers["supplier"] != "Other")]
    if rows["tiv"].sum() == 0:
        return None
    return rows.groupby("supplier")["tiv"].sum().idxmax()


def ct_story(iso3, start, end):
    """A few sentences about the country, every number computed from the data."""
    rows = ct_rows(iso3, start, end)
    if len(rows) == 0:
        return ["No data for this country in this period."]
    sentences = []

    # 1. democracy at the start and the end of the period
    first, last = rows.iloc[0], rows.iloc[-1]
    diff = last["democracy_index"] - first["democracy_index"]
    if diff > 0.02:
        verb = "rose"
    elif diff < -0.02:
        verb = "fell"
    else:
        verb = "stayed about the same"
    sentences.append(
        f"Democracy index {verb}: <b>{first['democracy_index']:.2f}</b> in {int(first['year'])} → "
        f"<b>{last['democracy_index']:.2f}</b> in {int(last['year'])}."
    )

    # 2. sharpest fall over 5 years, and was there a conflict at that time?
    democracy = dict(zip(rows["year"], rows["democracy_index"]))
    worst = None
    for y in democracy:
        if y - 5 in democracy:
            change = democracy[y] - democracy[y - 5]
            if worst is None or change < worst[0]:
                worst = (change, y - 5, y)
    if worst is not None and worst[0] <= -0.05:
        window = rows[rows["year"].between(worst[1], worst[2])]
        n_war = int(window["conflict_active"].sum())
        text = f"Sharpest 5-year fall: <b>{worst[0]:+.2f}</b> from {worst[1]} to {worst[2]}"
        if n_war > 0:
            text = text + f", with armed conflict in {n_war} of those {len(window)} years."
        else:
            text = text + ", with no armed conflict in those years."
        sentences.append(text)
    elif worst is not None:
        sentences.append("No 5-year fall in democracy bigger than 0.05 in this period.")

    # 3. longest unbroken conflict and democracy at its start and end
    runs = ct_conflict_runs(iso3, start, end)
    if len(runs) == 0:
        sentences.append("No armed conflict on record in this period.")
    else:
        longest = max(runs, key=lambda run: run["end"] - run["start"])
        n_years = longest["end"] - longest["start"] + 1
        level = "reached war level" if longest["level"] == 2 else "minor level only"
        text = (f"Longest unbroken conflict: <b>{longest['start']}–{longest['end']}</b> "
                f"({n_years} year{'s' if n_years > 1 else ''}, {level}); democracy "
                f"<b>{democracy[longest['start']]:.2f}</b> at its start, <b>{democracy[longest['end']]:.2f}</b> at its end.")
        sentences.append(text)

    # 4. arms suppliers: did the main supplier change after the Cold War?
    total = sipri_suppliers[(sipri_suppliers["iso3"] == iso3)
                            & sipri_suppliers["year"].between(start, end)]["tiv"].sum()
    if total == 0:
        sentences.append("No arms imports recorded in this period.")
    else:
        cold = ct_top_supplier(iso3, start, 1991) if start <= 1991 else None
        after = ct_top_supplier(iso3, 1992, end) if end >= 1992 else None
        top = ct_top_supplier(iso3, start, end)
        if cold is not None and after is not None and cold != after:
            sentences.append(f"Main arms supplier shifted from <b>{cold}</b> (until 1991) to "
                             f"<b>{after}</b> (since 1992). Total imports: <b>{total:,.0f}</b> TIV.")
        elif top is not None:
            rows_top = sipri_suppliers[(sipri_suppliers["iso3"] == iso3) & (sipri_suppliers["supplier"] == top)
                                       & sipri_suppliers["year"].between(start, end)]
            share = rows_top["tiv"].sum() / total
            sentences.append(f"Main arms supplier: <b>{top}</b>, {share:.0%} of all imports "
                             f"(<b>{total:,.0f}</b> TIV in this period).")
        else:
            sentences.append(f"Arms imports of <b>{total:,.0f}</b> TIV, all from smaller suppliers.")
    return sentences


def ct_story_box(iso3, start, end):
    items = "".join(f"<li>{s}</li>" for s in ct_story(iso3, start, end))
    st.markdown(f'<div class="ct-story"><div class="ct-title">THE STORY IN NUMBERS · {start}–{end}</div>'
                f'<ul>{items}</ul></div>', unsafe_allow_html=True)


def ct_pick(name):
    """Quick-pick button: show this country (runs before the next redraw)."""
    st.session_state["country_box"] = name


def ct_swap():
    """Swap the main country and the comparison country."""
    main = st.session_state["country_box"]
    st.session_state["country_box"] = st.session_state["compare"]
    st.session_state["compare"] = main


def ct_compare_chart(name_a, name_b, start, end, year):
    """Both democracy lines on one chart; the line is drawn thick in years with armed conflict."""
    fig = go.Figure()
    for name, colour in [(name_a, CT_A), (name_b, CT_B)]:
        rows = ct_rows(name_to_iso3(name), start, end)
        fig.add_trace(go.Scatter(
            x=rows["year"], y=rows["democracy_index"], mode="lines", line=dict(color=colour, width=1.8),
            customdata=rows["regime_label"],
            hovertemplate=name + ", %{x}: %{y:.2f} (%{customdata})<extra></extra>",
        ))
        # same line again, but only in conflict years (other years = gap)
        in_conflict = rows["democracy_index"].where(rows["conflict_active"] == 1)
        fig.add_trace(go.Scatter(
            x=rows["year"], y=in_conflict, mode="lines", line=dict(color=colour, width=7),
            opacity=0.35, hoverinfo="skip", connectgaps=False,
        ))
    fig.update_yaxes(range=[0, 1], tickvals=[0, 0.5, 1], title_text="Democracy index", title_font_size=10)
    return style(fig, 230, start, end, year)


def ct_compare(name_a, name_b, year, start, end):
    """Head-to-head box above the two country cards."""
    iso_a, iso_b = name_to_iso3(name_a), name_to_iso3(name_b)
    with st.container(border=True):
        section("Head to head", f"democracy index {start}–{end} · thick line = years in armed conflict")
        chart_col, table_col = st.columns([3, 2], vertical_alignment="center")
        with chart_col:
            st.markdown(chips({name_a: CT_A, name_b: CT_B}), unsafe_allow_html=True)
            show(ct_compare_chart(name_a, name_b, start, end, year))

        # one column of numbers per country
        cells = {}
        for iso3 in [iso_a, iso_b]:
            rows = ct_rows(iso3, start, end)
            now = ct_value(iso3, "democracy_index", year)
            if len(rows) > 0:
                change = f"{rows['democracy_index'].iloc[-1] - rows['democracy_index'].iloc[0]:+.2f}"
                during = rows[rows["conflict_active"] == 1]["democracy_index"]
                calm = rows[rows["conflict_active"] == 0]["democracy_index"]
            else:
                change, during, calm = "n/a", [], []
            cells[iso3] = [
                "n/a" if now is None else f"{now:.2f}",
                change,
                f"{int(rows['conflict_active'].sum())} of {len(rows)}",
                f"{during.mean():.2f}" if len(during) > 0 else "n/a",
                f"{calm.mean():.2f}" if len(calm) > 0 else "n/a",
                f"{rows['arms_imports_tiv'].sum():,.0f}",
                ct_top_supplier(iso3, start, end) or "none",
            ]
        labels = [f"Democracy index in {year}", "Change over the period", "Years in armed conflict",
                  "Avg. democracy, conflict years", "Avg. democracy, peace years",
                  "Arms imports (TIV, total)", "Main supplier"]
        body = ""
        for i, label in enumerate(labels):
            body = body + (f'<tr><td class="lab">{label}</td><td class="num">{cells[iso_a][i]}</td>'
                           f'<td class="num">{cells[iso_b][i]}</td></tr>')
        table_col.markdown(
            f'<table class="ct-vs"><tr><th></th>'
            f'<th><span class="ct-dot" style="background:{CT_A}"></span>{name_a}</th>'
            f'<th><span class="ct-dot" style="background:{CT_B}"></span>{name_b}</th></tr>{body}</table>',
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------- chart functions (Plotly)
def regime_and_democracy(iso3, start, end, year):
    """Top: regime bands. Bottom: democracy index line, conflict years shaded behind it."""
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.22, 0.78], vertical_spacing=0.06)

    spans = vdem_regime_spans[vdem_regime_spans["iso3"] == iso3]
    for label, s, e in zip(spans["regime_label"], spans["start"], spans["end"]):
        fig.add_trace(go.Bar(
            x=[e - s + 1], y=["Regime type"], base=[s - 0.5], orientation="h",
            marker_color=regime_colours[label], hovertemplate=f"{label}<br>{s} to {e}<extra></extra>",
        ), row=1, col=1)

    rows = panel[panel["iso3"] == iso3].sort_values("year")
    status = rows["max_intensity"].map({0: "no conflict", 1: "minor conflict", 2: "war"})
    fig.add_trace(go.Scatter(
        x=rows["year"], y=rows["democracy_index"], mode="lines", line=dict(color="#222", width=1.8),
        customdata=list(zip(rows["regime_label"], status)),
        hovertemplate="<b>%{x}</b>: %{y:.2f}<br>%{customdata[0]} · %{customdata[1]}<extra></extra>",
    ), row=2, col=1)

    # shaded conflict periods (added after the line: plotly needs a trace in row 2 first): darker for runs that reached war level
    for run in ct_conflict_runs(iso3, 1950, 2025):
        fig.add_vrect(x0=run["start"] - 0.5, x1=run["end"] + 0.5, line_width=0, layer="below",
                      fillcolor="#8A8178", opacity=0.22 if run["level"] == 2 else 0.11, row=2, col=1)

    # dot on the line at the chosen year
    now = rows[rows["year"] == year]
    if len(now) > 0:
        fig.add_trace(go.Scatter(x=now["year"], y=now["democracy_index"], mode="markers",
                                 marker=dict(color=BRAND, size=8, line=dict(color="white", width=1.5)),
                                 hoverinfo="skip"), row=2, col=1)

    fig.update_yaxes(range=[0, 1], tickvals=[0, 0.5, 1], title_text="Democracy index", title_font_size=10, row=2, col=1)
    fig.update_yaxes(showgrid=False, row=1, col=1)
    fig.update_layout(barmode="overlay")
    return style(fig, 240, start, end, year)


def conflict_timeline(iso3, start, end, year):
    """One row per conflict period, black = war, grey = minor conflict."""
    rows = panel[(panel["iso3"] == iso3) & (panel["conflict_active"] == 1)]
    fig = go.Figure()
    for level in [1, 2]:
        part = rows[rows["max_intensity"] == level]
        label = intensity_names[level]
        fig.add_trace(go.Bar(
            x=[1] * len(part), y=["Armed conflict"] * len(part), base=part["year"] - 0.5, orientation="h",
            marker_color=intensity_colours[label], marker_line_width=0,
            customdata=part["n_conflicts"],
            hovertemplate="%{base:.0f}: " + label + ", %{customdata} conflict(s)<extra></extra>",
        ))
    if len(rows[rows["year"].between(start, end)]) == 0:
        fig.add_annotation(text="No armed conflict on record", x=(start + end) / 2, y=0, showarrow=False,
                           font=dict(color="#999"))
        fig.update_yaxes(visible=False)
    fig.update_layout(barmode="overlay")
    fig.update_yaxes(showgrid=False)
    return style(fig, 90, start, end, year)


def arms_by_supplier(iso3, start, end, year):
    """Stacked bars: arms imports per year, split into the top 3 suppliers and Other."""
    rows = sipri_suppliers[sipri_suppliers["iso3"] == iso3]
    fig = go.Figure()
    if len(rows) == 0 or rows["tiv"].sum() == 0:
        fig.add_annotation(text="No arms imports recorded", x=(start + end) / 2, y=0.5, showarrow=False,
                           font=dict(color="#999"))
        fig.update_yaxes(visible=False)
        return style(fig, 120, start, end, year), {}

    totals = rows.groupby("supplier")["tiv"].sum().sort_values(ascending=False)
    order = [s for s in totals.index if s != "Other"] + (["Other"] if "Other" in totals.index else [])
    used = {}
    for position, supplier in enumerate(order):
        part = rows[rows["supplier"] == supplier]
        colour = colour_for_supplier(supplier, position)
        used[supplier] = colour
        fig.add_trace(go.Bar(
            x=part["year"], y=part["tiv"], name=supplier, marker_color=colour,
            hovertemplate=supplier + ", %{x}: %{y:,.0f} TIV<extra></extra>",
        ))
    fig.update_layout(barmode="stack")
    fig.update_yaxes(title_text="TIV, millions", title_font_size=10)
    return style(fig, 220, start, end, year), used


def supplier_rows(iso3, start, end, year, used):
    """One row per supplier: in which years did it deliver anything?"""
    rows = sipri_suppliers[(sipri_suppliers["iso3"] == iso3) & (sipri_suppliers["tiv"] > 0)]
    fig = go.Figure()
    for supplier in reversed(list(used.keys())):
        part = rows[rows["supplier"] == supplier]
        fig.add_trace(go.Bar(
            x=[0.9] * len(part), y=[supplier] * len(part), base=part["year"] - 0.45, orientation="h",
            marker_color=used[supplier], marker_line_width=0,
            customdata=part["tiv"], hovertemplate=supplier + ", %{base:.0f}: %{customdata:,.0f} TIV<extra></extra>",
        ))
    fig.update_layout(barmode="overlay")
    fig.update_yaxes(showgrid=False)
    return style(fig, 40 + 28 * len(used), start, end, year)


# ---------------------------------------------------------------- one country card
def tiles(iso3, year, start, end, narrow=False):
    country_rows = panel[panel["iso3"] == iso3]
    row = country_rows[country_rows["year"] == year]

    if len(row) == 0:
        regime, democracy, conflict, arms = "n/a", "n/a", "n/a", "n/a"
        regime_note, conflict_note, dem_note, arms_delta = "no data this year", "no data this year", "", ""
    else:
        r = row.iloc[0]
        regime = r["regime_label"].capitalize()
        span = vdem_regime_spans[(vdem_regime_spans["iso3"] == iso3) & (vdem_regime_spans["start"] <= year)
                                 & (vdem_regime_spans["end"] >= year)]
        regime_note = f"since {int(span['start'].iloc[0])} · V-Dem" if len(span) > 0 else "V-Dem classification"
        democracy = f"{r['democracy_index']:.2f}"
        dem_note = ct_delta(iso3, "democracy_index", year, "+.2f", CT_UP, BRAND)
        runs = ct_conflict_runs(iso3, 1950, 2025)
        if r["conflict_active"] == 1:
            conflict = f"{int(r['n_conflicts'])} · {intensity_names[int(r['max_intensity'])]}"
            run = [x for x in runs if x["start"] <= year <= x["end"]][0]
            conflict_note = f"conflict running since {run['start']}"
        else:
            conflict = "None"
            earlier = [x for x in runs if x["end"] < year]
            if len(earlier) > 0:
                conflict_note = f"last conflict year: {earlier[-1]['end']}"
            else:
                conflict_note = "no conflict on record before this"
        arms = f"{r['arms_imports_tiv']:,.0f} TIV"
        arms_delta = ct_delta(iso3, "arms_imports_tiv", year, "+,.0f", "#777", "#777")

    year_suppliers = sipri_suppliers[(sipri_suppliers["iso3"] == iso3) & (sipri_suppliers["year"] == year)]
    named = year_suppliers[(year_suppliers["supplier"] != "Other") & (year_suppliers["tiv"] > 0)]
    if len(named) > 0:
        arms_note = "Mostly from " + named.sort_values("tiv", ascending=False)["supplier"].iloc[0]
    elif year_suppliers["tiv"].sum() > 0:
        arms_note = "From smaller suppliers"
    else:
        arms_note = "No deliveries this year"

    spark = ct_sparkline(iso3, start, end, year)
    extra = " ct-tiles2" if narrow else ""
    st.markdown(
        f"""
        <div class="tiles{extra}">
          <div class="tile"><div class="lab">Regime in {year}</div><div class="val">{regime}</div><div class="note">{regime_note}</div></div>
          <div class="tile"><div class="lab">Democracy index · 0 to 1</div><div class="val">{democracy}</div><div class="note">{dem_note}</div>{spark}</div>
          <div class="tile"><div class="lab">Armed conflicts</div><div class="val">{conflict}</div><div class="note">{conflict_note}</div></div>
          <div class="tile"><div class="lab">Arms imports</div><div class="val">{arms}</div><div class="note">{arms_note}</div><div class="note">{arms_delta}</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def country_card(name, year, start, end, narrow=False):
    iso3 = name_to_iso3(name)
    with st.container(border=True):
        st.markdown(f'<span class="badge">{iso3}</span><div class="cname">{name}</div>', unsafe_allow_html=True)
        ct_story_box(iso3, start, end)
        tiles(iso3, year, start, end, narrow)

        section("Regime and democracy", "V-Dem · shaded = years in armed conflict")
        st.markdown(chips(regime_colours) + chips({"War years": "#E2DFDC", "Minor conflict years": "#F1EFED"}),
                    unsafe_allow_html=True)
        show(regime_and_democracy(iso3, start, end, year))

        rows = panel[(panel["iso3"] == iso3) & panel["year"].between(start, end)]
        section("Armed conflicts", f"{int(rows['conflict_active'].sum())} conflict years in this period · UCDP/PRIO")
        st.markdown(chips({"War, 1,000+ deaths": "#222222", "Minor, 25 to 999 deaths": "#BDBDBD"}), unsafe_allow_html=True)
        show(conflict_timeline(iso3, start, end, year))

        arms_fig, used = arms_by_supplier(iso3, start, end, year)
        section("Arms imports", "SIPRI TIV per year")
        st.markdown(chips(used), unsafe_allow_html=True)
        show(arms_fig)

        if len(used) > 0:
            section("Suppliers", "top 3 over all years + all others")
            show(supplier_rows(iso3, start, end, year, used))

        with st.expander("Year-by-year table for " + name):
            table = rows[["year", "regime_label", "democracy_index", "n_conflicts", "max_intensity", "arms_imports_tiv"]].copy()
            table["max_intensity"] = table["max_intensity"].map(intensity_names)
            st.dataframe(table, hide_index=True, width="stretch", column_config={
                "year": st.column_config.NumberColumn("Year", format="%d"),
                "regime_label": "Regime",
                "democracy_index": st.column_config.NumberColumn("Democracy", format="%.2f"),
                "n_conflicts": "Conflicts",
                "max_intensity": "Intensity",
                "arms_imports_tiv": st.column_config.NumberColumn("Arms imports (TIV)", format="%.0f"),
            })


# ---------------------------------------------------------------- Overview page helpers (prefix ov_)
st.markdown(
    f"""
    <style>
    .ov-hero {{padding: 10px 8px 4px 8px;}}
    .ov-hero h1 {{font-size: 2.5rem; line-height: 1.12; margin: 6px 0 10px 0; color: #222; font-weight: 800;}}
    .ov-hero h1 em {{color: {BRAND}; font-style: normal;}}
    .ov-lead {{color: #555; font-size: 1.02rem; max-width: 820px; margin: 0 0 14px 0;}}
    .ov-stats {{display: flex; gap: 34px; margin: 4px 0 6px 0; flex-wrap: wrap;}}
    .ov-stats div {{font-size: 0.78rem; color: #888;}}
    .ov-stats b {{display: block; font-size: 1.6rem; color: #222; font-family: ui-monospace, monospace;}}
    .ov-facts {{display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 6px 0 16px 0;}}
    .ov-fact {{background: white; border: 1px solid #E8E2DC; border-radius: 12px; padding: 14px 16px;}}
    .ov-fact .big {{color: {BRAND}; font-size: 1.75rem; font-weight: 800; font-family: ui-monospace, monospace; line-height: 1.2;}}
    .ov-fact .txt {{color: #333; font-size: 0.86rem; margin-top: 4px;}}
    .ov-fact .src {{color: #999; font-size: 0.7rem; margin-top: 6px;}}
    .ov-step {{color: {BRAND}; font-weight: 800; font-size: 0.78rem; letter-spacing: 0.08em;}}
    .ov-cta h3 {{margin: 2px 0 4px 0; font-size: 1.15rem;}}
    .ov-cta p {{color: #666; font-size: 0.86rem; margin: 0 0 8px 0;}}
    </style>
    """,
    unsafe_allow_html=True,
)

# regime colours from red (closed autocracy) to blue (liberal democracy), used as a smooth scale for the map
OV_MAP_SCALE = [[0.0, "#B8312F"], [0.35, "#F2A68F"], [0.6, "#A9C8F2"], [1.0, "#1F5BA8"]]


def ov_go_to(page_name, country_name=None):
    """Button callback: switch page (and optionally the selected country)."""
    st.session_state["page_nav"] = page_name
    if country_name is not None:
        st.session_state["country_box"] = country_name


def ov_pick_war_country():
    """Callback of the 'at war' pills: open the clicked country on the Country timeline page."""
    picked = st.session_state["ov_war_pick"]
    if picked is not None:
        st.session_state["ov_war_pick"] = None
        ov_go_to("Country timeline", picked)


def ov_plain(fig, height):
    """Look for Overview charts that do not have a year axis (map, bar chart)."""
    fig.update_layout(
        height=height, margin=dict(l=10, r=10, t=10, b=10),
        plot_bgcolor="white", paper_bgcolor="white", font=dict(size=11, color="#444"),
        hoverlabel=dict(bgcolor="white"),
    )
    return fig


def ov_world_map(one_year):
    """Choropleth of the democracy index; circles on top mark countries with an active armed conflict."""
    fig = go.Figure(go.Choropleth(
        locations=one_year["iso3"], z=one_year["democracy_index"], zmin=0, zmax=1,
        colorscale=OV_MAP_SCALE, marker_line_color="white", marker_line_width=0.4,
        text=one_year["country_name"], customdata=one_year["regime_label"],
        hovertemplate="<b>%{text}</b><br>Democracy index: %{z:.2f}<br>%{customdata}<extra></extra>",
        colorbar=dict(title=dict(text="Democracy", side="top"), x=0.97, y=0.5, len=0.55, thickness=10,
                      tickvals=[0, 0.5, 1], ticktext=["0 autocratic", "0.5", "1 democratic"]),
    ))
    # one layer of circles per intensity: grey ring = minor conflict, black dot = war
    layers = {1: ("Minor conflict", "#777777", "circle-open", 9), 2: ("War", "#111111", "circle", 9)}
    for level, (label, colour, symbol, size) in layers.items():
        part = one_year[one_year["max_intensity"] == level]
        fig.add_trace(go.Scattergeo(
            locations=part["iso3"], mode="markers", name=label, text=part["country_name"],
            marker=dict(color=colour, symbol=symbol, size=size, line=dict(width=2, color=colour)),
            customdata=part["n_conflicts"],
            hovertemplate="<b>%{text}</b><br>" + label + ", %{customdata} conflict(s)<extra></extra>",
        ))
    fig.update_geos(projection_type="natural earth", showframe=False, showcoastlines=False,
                    showcountries=False, landcolor="#EFEBE7", showland=True, bgcolor="white",
                    lataxis_range=[-58, 85])
    fig = ov_plain(fig, 470)
    fig.update_layout(showlegend=True, legend=dict(orientation="h", x=0.01, y=0.02, bgcolor="rgba(255,255,255,0.8)"))
    return fig


def ov_fact(big, text, source):
    return f'<div class="ov-fact"><div class="big">{big}</div><div class="txt">{text}</div><div class="src">{source}</div></div>'


def ov_conflict_counts(year):
    """Stacked bars: number of countries with a war / a minor conflict, per year."""
    counts = panel[panel["conflict_active"] == 1].groupby(["year", "max_intensity"]).size().unstack(fill_value=0)
    fig = go.Figure()
    for level in [2, 1]:
        label = intensity_names[level]
        fig.add_trace(go.Bar(
            x=counts.index, y=counts[level], name=label, marker_color=intensity_colours[label], marker_line_width=0,
            hovertemplate="%{x}: %{y} countries, " + label + "<extra></extra>",
        ))
    fig.update_layout(barmode="stack")
    fig.update_yaxes(title_text="Countries", title_font_size=10)
    return style(fig, 240, 1950, 2025, year)


def ov_regime_mix(year):
    """100% stacked area: share of countries in each regime type, per year."""
    shares = pd.crosstab(panel["year"], panel["regime_label"], normalize="index")
    fig = go.Figure()
    for label, colour in regime_colours.items():
        fig.add_trace(go.Scatter(
            x=shares.index, y=shares[label], name=label, mode="lines", stackgroup="one",
            line=dict(width=0.5, color=colour), fillcolor=colour,
            hovertemplate="%{x}: %{y:.0%} " + label + "<extra></extra>",
        ))
    fig.update_yaxes(tickformat=".0%", range=[0, 1])
    return style(fig, 240, 1950, 2025, year)


def ov_democracy_gap(year):
    """Average democracy index per year, countries in conflict vs. countries at peace."""
    means = panel.groupby(["year", "conflict_active"])["democracy_index"].mean().unstack()
    fig = go.Figure()
    lines = {0: ("At peace", "#1F5BA8"), 1: ("In armed conflict", BRAND)}
    for value, (label, colour) in lines.items():
        fig.add_trace(go.Scatter(
            x=means.index, y=means[value], name=label, mode="lines", line=dict(color=colour, width=2.4),
            hovertemplate="%{x}: %{y:.2f} " + label.lower() + "<extra></extra>",
        ))
    fig.update_yaxes(range=[0, 0.8], tickvals=[0, 0.2, 0.4, 0.6, 0.8], title_text="Average democracy index",
                     title_font_size=10)
    fig = style(fig, 280, 1950, 2025, year)
    fig.update_layout(showlegend=True, legend=dict(orientation="h", x=0, y=1.12))
    return fig


def ov_top_importers(one_year):
    """Horizontal bars of the 10 largest arms importers in one year, coloured by regime type."""
    top10 = one_year[one_year["arms_imports_tiv"] > 0].sort_values("arms_imports_tiv", ascending=False).head(10)
    top10 = top10.iloc[::-1]  # largest bar at the top
    labels = []
    for name, level in zip(top10["country_name"], top10["max_intensity"]):
        if level == 2:
            labels.append(name + "  ⚔ war")
        elif level == 1:
            labels.append(name + "  ⚔ minor")
        else:
            labels.append(name)
    fig = go.Figure(go.Bar(
        x=top10["arms_imports_tiv"], y=labels, orientation="h",
        marker_color=[regime_colours[r] for r in top10["regime_label"]], marker_line_width=0,
        customdata=top10["regime_label"],
        hovertemplate="%{y}<br>%{x:,.0f} TIV<br>%{customdata}<extra></extra>",
    ))
    fig = ov_plain(fig, 280)
    fig.update_layout(showlegend=False, bargap=0.25)
    fig.update_xaxes(title_text="Arms imports, TIV millions", title_font_size=10, showgrid=True, gridcolor="#EEEEEE")
    fig.update_yaxes(showgrid=False)
    return fig, top10


# ---------------------------------------------------------------- Analysis page helpers
AN_GROUPS = {"high importer": BRAND, "low importer": "#1F5BA8"}
AN_FILL = {"high importer": "rgba(163,58,30,0.14)", "low importer": "rgba(31,91,168,0.14)"}

st.markdown(
    f"""
    <style>
    .an-hero {{background: white; border: 1px solid #E8E2DC; border-left: 6px solid {BRAND};
        border-radius: 12px; padding: 18px 22px; margin: 6px 0 12px 0;}}
    .an-hero .big {{font-size: 1.55rem; font-weight: 700; line-height: 1.35; color: #222;}}
    .an-hero .hi {{color: {BRAND};}}
    .an-hero .lo {{color: #1F5BA8;}}
    .an-hero .small {{color: #777; font-size: 0.85rem; margin-top: 6px;}}
    .an-steps {{display: grid; grid-template-columns: repeat(5, 1fr); gap: 8px; margin: 6px 0 4px 0;}}
    .an-step {{background: #F6F4F1; border-radius: 8px; padding: 10px 12px;}}
    .an-step .num {{display: inline-block; background: {BRAND}; color: white; font-weight: 700; font-size: 0.75rem;
        width: 20px; height: 20px; line-height: 20px; text-align: center; border-radius: 50%; margin-bottom: 4px;}}
    .an-step .ttl {{font-weight: 700; font-size: 0.85rem; color: #333;}}
    .an-step .txt {{color: #777; font-size: 0.75rem; margin-top: 2px;}}
    .an-list {{font-size: 0.82rem; color: #444; margin: 2px 0 0 0; padding-left: 18px;}}
    .an-list li {{margin-bottom: 2px;}}
    .an-list .v {{font-family: ui-monospace, monospace; font-weight: 700;}}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def an_onsets():
    """One row per conflict onset: country, group, imports before, democracy changes, war or not."""
    event = load("event")
    rows = []
    for (iso3, onset_year), one in event.groupby(["iso3", "onset_year"]):
        before = one[one["t"].between(-5, -1)]
        first_years = one[one["t"].between(0, 5)]
        at = one.set_index("t")
        rows.append({
            "iso3": iso3,
            "onset_year": onset_year,
            "importer_group": one["importer_group"].iloc[0],
            "imports_before": before["arms_imports_tiv"].mean(),
            "dem_before": at["democracy_index"].get(-1),
            "change_5": at["dem_change"].get(5),
            "change_10": at["dem_change"].get(10),
            "war": bool((first_years["max_intensity"] == 2).any()),
        })
    onsets = pd.DataFrame(rows)
    # add country names from the panel
    country_names = panel[["iso3", "country_name"]].drop_duplicates("iso3")
    return onsets.merge(country_names, on="iso3", how="left")


def an_summary(wars_only):
    """Average change in democracy per year t and importer group (same as event_time.csv for all onsets)."""
    event = load("event")
    if wars_only:
        wars = an_onsets()
        wars = wars[wars["war"]][["iso3", "onset_year"]]
        event = event.merge(wars, on=["iso3", "onset_year"])
    summary = event.groupby(["t", "importer_group"], as_index=False).agg(
        dem_change=("dem_change", "mean"), n_countries=("dem_change", "count"), sd=("dem_change", "std"))
    # 95% interval of the average: 1.96 standard errors
    summary["se"] = summary["sd"] / summary["n_countries"] ** 0.5
    summary["low"] = summary["dem_change"] - 1.96 * summary["se"]
    summary["high"] = summary["dem_change"] + 1.96 * summary["se"]
    return summary


def an_value(summary, group, t, column="dem_change"):
    row = summary[(summary["importer_group"] == group) & (summary["t"] == t)]
    return row[column].iloc[0]


def an_main_chart(summary, t_pick, show_band):
    fig = go.Figure()
    # light background for the years after the conflict started
    fig.add_vrect(x0=-0.5, x1=10.5, fillcolor="#F6F1EC", line_width=0, layer="below")

    if show_band:
        # 95% band around each line
        for group, colour in AN_GROUPS.items():
            rows = summary[summary["importer_group"] == group]
            fig.add_trace(go.Scatter(
                x=list(rows["t"]) + list(rows["t"])[::-1], y=list(rows["high"]) + list(rows["low"])[::-1],
                fill="toself", fillcolor=AN_FILL[group], line=dict(width=0), hoverinfo="skip", showlegend=False))
    else:
        # shade the gap between the two lines (low first, then high fills to it)
        low = summary[summary["importer_group"] == "low importer"]
        high = summary[summary["importer_group"] == "high importer"]
        fig.add_trace(go.Scatter(x=low["t"], y=low["dem_change"], mode="lines", line=dict(width=0),
                                 hoverinfo="skip", showlegend=False))
        fig.add_trace(go.Scatter(x=high["t"], y=high["dem_change"], mode="lines", line=dict(width=0),
                                 fill="tonexty", fillcolor="rgba(163,58,30,0.10)", hoverinfo="skip", showlegend=False))

    for group, colour in AN_GROUPS.items():
        rows = summary[summary["importer_group"] == group]
        fig.add_trace(go.Scatter(
            x=rows["t"], y=rows["dem_change"], mode="lines+markers", name=group[0].upper() + group[1:] + "s",
            legendrank=1 if group == "high importer" else 2,
            line=dict(color=colour, width=2.8), marker=dict(size=6),
            customdata=rows["n_countries"],
            hovertemplate=group + "<br>t = %{x}: %{y:+.3f}<br>%{customdata} onsets<extra></extra>",
        ))

    fig.add_hline(y=0, line_color="#999", line_width=1)
    fig.add_vline(x=-0.5, line_color="#999", line_dash="dot")
    fig.add_annotation(x=-0.5, y=1, yref="paper", text="conflict starts →", showarrow=False,
                       xanchor="left", yanchor="top", font=dict(size=11, color="#777"))
    fig.add_annotation(x=-1, y=0, text="baseline (t = -1)", showarrow=True, arrowhead=0, ax=0, ay=28,
                       font=dict(size=10, color="#777"))

    # marker for the chosen year with the gap written next to it
    high_v = an_value(summary, "high importer", t_pick)
    low_v = an_value(summary, "low importer", t_pick)
    fig.add_shape(type="line", x0=t_pick, x1=t_pick, y0=low_v, y1=high_v, line=dict(color="#222", width=2))
    fig.add_annotation(x=t_pick, y=max(high_v, low_v), text=f"gap {high_v - low_v:+.3f}", showarrow=True,
                       arrowhead=0, ax=0, ay=-26, font=dict(size=12, color="#222"),
                       bgcolor="white", bordercolor="#222", borderwidth=1, borderpad=3)

    fig = style(fig, 420, -5, 10, None)
    fig.update_layout(showlegend=True, legend=dict(orientation="h", y=1.1, x=0))
    fig.update_xaxes(title_text="Years since conflict onset (t)", dtick=1)
    fig.update_yaxes(title_text="Change in democracy index", tickformat="+.2f")
    return fig


def an_sample_chart(summary):
    fig = go.Figure()
    for group, colour in AN_GROUPS.items():
        rows = summary[summary["importer_group"] == group]
        fig.add_trace(go.Bar(x=rows["t"], y=rows["n_countries"], name=group, marker_color=colour,
                             hovertemplate=group + ", t = %{x}: %{y} onsets<extra></extra>"))
    fig.update_layout(barmode="group")
    fig.update_xaxes(dtick=1, title_text="t")
    fig.update_yaxes(title_text="Onsets with data")
    return style(fig, 240, -5, 10, None)


def an_list(rows, column):
    """Small HTML list: country, onset year and value."""
    html = '<ol class="an-list">'
    for _, r in rows.iterrows():
        html = html + f'<li>{r["country_name"]} ({r["onset_year"]}) <span class="v">{r[column]:+.2f}</span></li>'
    return html + "</ol>"


# ---------------------------------------------------------------- session state (remembered between clicks)
if "page_nav" not in st.session_state:
    st.session_state["page_nav"] = "Overview"
if "country_box" not in st.session_state:
    st.session_state["country_box"] = "India"
if "compare" not in st.session_state:
    st.session_state["compare"] = None
if "year" not in st.session_state:
    st.session_state["year"] = 1977
if "playing" not in st.session_state:
    st.session_state["playing"] = False
if "period" not in st.session_state:
    st.session_state["period"] = "1950–2025"


def toggle_play():
    start, end = PERIODS[st.session_state["period"] or "1950–2025"]
    if not st.session_state["playing"] and st.session_state["year"] >= end:
        st.session_state["year"] = start
    st.session_state["playing"] = not st.session_state["playing"]


def remove_comparison():
    st.session_state["compare"] = None


# ---------------------------------------------------------------- top bar
col_brand, col_nav, col_search = st.columns([2, 4, 2], vertical_alignment="center")
with col_brand:
    st.markdown('<span class="brand">Conflict · Arms · Democracy</span>', unsafe_allow_html=True)
with col_nav:
    page = st.segmented_control(
        "Page", ["Overview", "Country timeline", "Analysis", "Data and method"],
        label_visibility="collapsed", key="page_nav",
    )
with col_search:
    country = st.selectbox("Search a country", names, label_visibility="collapsed", key="country_box")

if page is None:
    page = "Overview"


# ---------------------------------------------------------------- page: Country timeline
if page == "Country timeline":
    head_left, head_mid, head_right = st.columns([4, 2, 1.3], vertical_alignment="bottom")
    with head_left:
        st.markdown('<p class="kicker">COUNTRY TIMELINE</p>', unsafe_allow_html=True)
        st.markdown('<p class="sub">Regime, conflicts and arms imports on one shared year axis. '
                    'Move the slider or press Play to move the red year marker.</p>', unsafe_allow_html=True)
    with head_mid:
        st.selectbox("Compare with", names, placeholder="⇆ Compare with...",
                     label_visibility="collapsed", key="compare")
    with head_right:
        st.button("Remove comparison", on_click=remove_comparison, disabled=st.session_state["compare"] is None)

    # quick-pick example countries (buttons change the search box through a callback)
    with st.container(horizontal=True, key="ct_try", vertical_alignment="center"):
        st.markdown('<p class="ct-try">Try an example:</p>', unsafe_allow_html=True)
        for example in CT_EXAMPLES:
            if example in names:
                st.button(example, key="ct_try_" + example, on_click=ct_pick, args=(example,))
        if st.session_state["compare"] is not None:
            st.button("⇄ Swap countries", key="ct_try_swap", on_click=ct_swap)

    # controls: Play, year slider, period
    period_name = st.session_state["period"] or "1950–2025"
    start, end = PERIODS[period_name]

    if st.session_state["playing"]:
        if st.session_state["year"] < end:
            st.session_state["year"] = st.session_state["year"] + 1
        else:
            st.session_state["playing"] = False
    # keep the year inside the chosen period
    st.session_state["year"] = min(max(st.session_state["year"], start), end)

    with st.container(border=True):
        c_play, c_slider, c_period = st.columns([1, 6, 3], vertical_alignment="center")
        with c_play:
            label = "⏸ Pause" if st.session_state["playing"] else "▶ Play"
            st.button(label, on_click=toggle_play, type="primary")
        with c_slider:
            year = st.slider("Year", start, end, key="year")
        with c_period:
            st.segmented_control("Period", list(PERIODS.keys()), label_visibility="collapsed", key="period")

    compare = st.session_state["compare"]
    if compare is None:
        country_card(country, year, start, end)
    else:
        ct_compare(country, compare, year, start, end)
        left, right = st.columns(2)
        with left:
            country_card(country, year, start, end, narrow=True)
        with right:
            country_card(compare, year, start, end, narrow=True)

    how_to_read(
        "All charts share the same years, so read them from top to bottom: did democracy (black line) fall "
        "while a conflict (shaded years, black or grey bars) was running, and did arms imports rise before or "
        "during it? The story box and the small arrows (change vs. 5 years earlier) are computed from the same data. "
        "TIV is SIPRI's trend-indicator value: it measures military capability delivered, not the price paid."
    )

    # Play: wait a moment, then draw the next year
    if st.session_state["playing"]:
        time.sleep(0.4)
        st.rerun()


# ---------------------------------------------------------------- page: Overview
elif page == "Overview":
    n_countries = panel["iso3"].nunique()
    first_year, last_year = int(panel["year"].min()), int(panel["year"].max())

    # --- hero
    with st.container(border=True):
        st.markdown(
            f"""
            <div class="ov-hero">
              <p class="kicker">CONFLICT · DEMOCRACY · ARMS</p>
              <h1>What happens to <em>democracy</em> during and after armed conflict?</h1>
              <p class="ov-lead">And does it look different in countries that import many weapons? We merged three
              datasets (UCDP/PRIO conflicts, V-Dem democracy scores and SIPRI arms transfers) into one table with one
              row per country and year.</p>
              <div class="ov-stats">
                <div><b>{n_countries}</b>countries</div>
                <div><b>{last_year - first_year + 1}</b>years, {first_year} to {last_year}</div>
                <div><b>{len(panel):,}</b>country-years</div>
                <div><b>3</b>datasets</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        b1, b2, _ = st.columns([1.4, 1.4, 4])
        with b1:
            st.button("See the main finding →", type="primary", on_click=ov_go_to, args=("Analysis",),
                      key="ov_cta_analysis_top", width="stretch")
        with b2:
            st.button("Explore a country →", on_click=ov_go_to, args=("Country timeline",),
                      key="ov_cta_country_top", width="stretch")

    # --- key facts over all years (all computed from the panel)
    by_year = panel.groupby("year").agg(
        n_conflict=("conflict_active", "sum"), democracy=("democracy_index", "mean"))
    peak_year = int(by_year["n_conflict"].idxmax())
    peak_n = int(by_year["n_conflict"].max())

    dem_peace = panel[panel["conflict_active"] == 0]["democracy_index"].mean()
    dem_conflict = panel[panel["conflict_active"] == 1]["democracy_index"].mean()

    is_democracy = panel["regime_label"].isin(["electoral democracy", "liberal democracy"])
    dem_share = is_democracy.groupby(panel["year"]).mean()

    arms_total = panel["arms_imports_tiv"].sum()
    arms_in_conflict = panel[panel["conflict_active"] == 1]["arms_imports_tiv"].sum() / arms_total
    country_years_in_conflict = panel["conflict_active"].mean()

    st.markdown(
        '<div class="ov-facts">'
        + ov_fact(f"{dem_conflict:.2f} vs {dem_peace:.2f}",
                  "Average democracy index of countries <b>in conflict</b> vs. <b>at peace</b>, all years together.",
                  "V-Dem + UCDP/PRIO, country-years")
        + ov_fact(f"{dem_share[first_year]:.0%} → {dem_share[last_year]:.0%}",
                  f"Share of countries that are democracies, {first_year} vs. {last_year} "
                  f"(peak: {dem_share.max():.0%} in {int(dem_share.idxmax())}).",
                  "V-Dem regime type")
        + ov_fact(f"{peak_n} in {peak_year}",
                  "The most countries with an active armed conflict in a single year.",
                  "UCDP/PRIO, 25+ battle deaths")
        + ov_fact(f"{arms_in_conflict:.0%}",
                  f"of all arms imports went to a country in conflict that year, although only "
                  f"{country_years_in_conflict:.0%} of country-years are conflict years.",
                  "SIPRI TIV + UCDP/PRIO")
        + "</div>",
        unsafe_allow_html=True,
    )

    # --- the world in one year: map + tiles
    st.markdown('<p class="ov-step">1 · THE WORLD IN ONE YEAR</p>', unsafe_allow_html=True)
    o_year = st.slider("Pick a year", first_year, last_year, 2025, key="overview_year")
    one_year = panel[panel["year"] == o_year]
    n_war = int((one_year["max_intensity"] == 2).sum())
    n_minor = int((one_year["max_intensity"] == 1).sum())
    share_dem_year = one_year["regime_label"].isin(["electoral democracy", "liberal democracy"]).mean()

    st.markdown(
        f"""
        <div class="tiles">
          <div class="tile"><div class="lab">Countries in {o_year}</div><div class="val">{len(one_year)}</div><div class="note">in the merged panel</div></div>
          <div class="tile"><div class="lab">In armed conflict</div><div class="val">{n_war + n_minor}</div><div class="note">{n_war} at war (1,000+ deaths), {n_minor} minor</div></div>
          <div class="tile"><div class="lab">Democracies</div><div class="val">{share_dem_year:.0%}</div><div class="note">electoral or liberal democracy</div></div>
          <div class="tile"><div class="lab">Arms delivered</div><div class="val">{one_year['arms_imports_tiv'].sum():,.0f}</div><div class="note">TIV, millions, all countries</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        section(f"Democracy and armed conflict in {o_year}", "V-Dem · UCDP/PRIO")
        show(ov_world_map(one_year))
        how_to_read(
            "Colour = electoral democracy index, from red (0, autocratic) to blue (1, democratic). "
            "A black dot marks a war (1,000+ battle deaths that year), a grey ring a minor conflict (25 to 999). "
            "Grey land = no data. Hover over a country for details."
        )
        at_war = sorted(one_year[one_year["max_intensity"] == 2]["country_name"])
        if len(at_war) > 0:
            st.pills(f"At war in {o_year}: click to open the country timeline", at_war,
                     key="ov_war_pick", on_change=ov_pick_war_country)
        else:
            st.caption(f"No country had a war (1,000+ battle deaths) in {o_year}.")

    # --- long-term trends
    st.markdown(f'<p class="ov-step">2 · {last_year - first_year + 1} YEARS AT A GLANCE</p>', unsafe_allow_html=True)
    first_n = int(by_year.loc[first_year, "n_conflict"])
    last_n = int(by_year.loc[last_year, "n_conflict"])
    left, right = st.columns(2)
    with left:
        with st.container(border=True):
            section("How many countries are fighting?", "UCDP/PRIO")
            st.markdown(chips({"War, 1,000+ deaths": "#222222", "Minor, 25 to 999 deaths": "#BDBDBD"}),
                        unsafe_allow_html=True)
            show(ov_conflict_counts(o_year))
            how_to_read(
                f"Each bar is one year: number of countries with an active conflict. {first_n} in {first_year}, "
                f"a peak of {peak_n} in {peak_year}, and {last_n} in {last_year}. The red line is the year you picked."
            )
    with right:
        with st.container(border=True):
            section("The world's regime mix", "V-Dem")
            st.markdown(chips(regime_colours), unsafe_allow_html=True)
            show(ov_regime_mix(o_year))
            how_to_read(
                f"Share of countries in each regime type. The two blue bands together are the democracies: "
                f"{dem_share[first_year]:.0%} in {first_year}, {dem_share[1990]:.0%} in 1990, "
                f"{dem_share.max():.0%} at the peak in {int(dem_share.idxmax())} and {dem_share[last_year]:.0%} in {last_year}."
            )

    # --- the link to our question
    st.markdown('<p class="ov-step">3 · CONFLICT, DEMOCRACY AND ARMS</p>', unsafe_allow_html=True)
    gap = panel.groupby(["year", "conflict_active"])["democracy_index"].mean().unstack()
    years_lower = int((gap[1] < gap[0]).sum())
    years_both = int(gap.dropna().shape[0])
    left, right = st.columns([1.15, 1])
    with left:
        with st.container(border=True):
            section("Are countries in conflict less democratic?", "average democracy index per year")
            show(ov_democracy_gap(o_year))
            how_to_read(
                f"In {years_lower} of {years_both} years the countries in conflict (red) were on average less democratic "
                "than the countries at peace (blue). This is a correlation only: it does not say whether conflict lowers "
                "democracy or the other way round. The Analysis page follows countries through time to get closer."
            )
    with right:
        with st.container(border=True):
            top_fig, top10 = ov_top_importers(one_year)
            section(f"Top 10 arms importers in {o_year}", "SIPRI")
            st.markdown(chips(regime_colours), unsafe_allow_html=True)
            if len(top10) > 0:
                show(top_fig)
                how_to_read("Bar colour = regime type, ⚔ = armed conflict in that year. "
                            "TIV measures military capability delivered, not the price paid.")
                biggest = top10["country_name"].iloc[-1]
                st.button(f"Open the timeline of {biggest} →", on_click=ov_go_to,
                          args=("Country timeline", biggest), key="ov_open_top_importer")
            else:
                st.caption(f"No arms deliveries recorded in {o_year}.")

    # --- calls to action
    st.markdown('<p class="ov-step">WHERE TO GO NEXT</p>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True):
            st.markdown('<div class="ov-cta"><h3>🔎 Country timeline</h3><p>Regime, conflicts and arms imports of one '
                        'country on one shared year axis. Press Play to watch the history unfold, or compare two '
                        'countries side by side.</p></div>', unsafe_allow_html=True)
            pick = st.selectbox("Country", names, index=names.index(st.session_state["country_box"]),
                                key="ov_country_pick", label_visibility="collapsed")
            st.button("Open country timeline →", type="primary", on_click=ov_go_to,
                      args=("Country timeline", pick), key="ov_cta_country")
    with c2:
        with st.container(border=True):
            st.markdown('<div class="ov-cta"><h3>📈 Main finding</h3><p>What happens to the democracy index in the '
                        '5 years before and 10 years after a conflict starts, for high and low arms importers.</p></div>',
                        unsafe_allow_html=True)
            onsets = event_time[event_time["t"] == 0]["n_countries"].sum()
            st.caption(f"Based on {int(onsets)} conflict onsets with data at the start year.")
            st.button("Go to the analysis →", type="primary", on_click=ov_go_to, args=("Analysis",),
                      key="ov_cta_analysis")


# ---------------------------------------------------------------- page: Analysis
elif page == "Analysis":
    st.markdown('<p class="kicker">MAIN FINDING</p>', unsafe_allow_html=True)
    st.title("Democracy around the start of a conflict")
    st.markdown('<p class="sub">Average change in the democracy index from 5 years before to 10 years after '
                'a conflict starts, compared with the year before the conflict. '
                'Countries are split by how many weapons they imported before the conflict.</p>',
                unsafe_allow_html=True)

    # controls: which onsets, and which year to compare
    with st.container(border=True):
        c_which, c_year, c_band = st.columns([3, 5, 2], vertical_alignment="center")
        with c_which:
            which = st.segmented_control("Onsets", ["All conflicts", "Wars only"], default="All conflicts",
                                         key="an_which")
        with c_year:
            t_pick = st.slider("Compare the groups after ... years", 0, 10, 5, key="an_t")
        with c_band:
            show_band = st.toggle("Show 95% band", key="an_band",
                                  help="Range in which the average would likely fall with another sample of onsets.")
    wars_only = which == "Wars only"
    summary = an_summary(wars_only)
    onsets = an_onsets()
    if wars_only:
        onsets = onsets[onsets["war"]]

    # headline with the key numbers (all computed from the data)
    high_v = an_value(summary, "high importer", t_pick)
    low_v = an_value(summary, "low importer", t_pick)
    n_high_t = int(an_value(summary, "high importer", t_pick, "n_countries"))
    n_low_t = int(an_value(summary, "low importer", t_pick, "n_countries"))
    years = "year" if t_pick == 1 else "years"
    scope = "wars (1,000+ battle deaths in the first 6 years)" if wars_only else "armed conflicts"
    st.markdown(
        f"""
        <div class="an-hero">
          <div class="big">{t_pick} {years} after a conflict starts, democracy has changed by
            <span class="hi">{high_v:+.3f}</span> in high-importer countries
            and by <span class="lo">{low_v:+.3f}</span> in low-importer countries.</div>
          <div class="small">Change since the year before the conflict, democracy index from 0 to 1 ·
            gap {high_v - low_v:+.3f} · {len(onsets)} onsets of {scope} · {n_high_t} high and {n_low_t} low
            importers still have data at t = {t_pick}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # main chart
    with st.container(border=True):
        section("Change in democracy, by years since conflict onset",
                "V-Dem electoral democracy index · " + ("wars only" if wars_only else "all conflicts"))
        show(an_main_chart(summary, t_pick, show_band))
        if show_band:
            band_text = ("The coloured bands show the 95% range of each average: where the bands overlap, "
                         "the two groups cannot be told apart with this many onsets.")
        else:
            band_text = ("The light red area is the gap between the two groups; the black marker shows it for the "
                         "year chosen with the slider.")
        how_to_read(
            "t = 0 is the first conflict year (shaded area = years of and after the onset). Both lines are exactly 0 "
            "at t = -1, the year before the conflict, because everything is measured as the change since then. "
            "Above 0 = more democratic than just before the conflict, below 0 = less democratic. " + band_text
        )

    # tiles: computed numbers for the chosen year
    n_high = int(an_value(summary, "high importer", 0, "n_countries"))
    n_low = int(an_value(summary, "low importer", 0, "n_countries"))
    high_10 = an_value(summary, "high importer", 10)
    low_10 = an_value(summary, "low importer", 10)
    st.markdown(
        f"""
        <div class="tiles">
          <div class="tile"><div class="lab">Onsets, high importers</div><div class="val">{n_high}</div><div class="note">with data at t = 0</div></div>
          <div class="tile"><div class="lab">Onsets, low importers</div><div class="val">{n_low}</div><div class="note">with data at t = 0</div></div>
          <div class="tile"><div class="lab">After {t_pick} {years}, high / low</div><div class="val">{high_v:+.3f} / {low_v:+.3f}</div><div class="note">{100 * high_v:+.1f} / {100 * low_v:+.1f} points on a 0 to 100 scale</div></div>
          <div class="tile"><div class="lab">After 10 years, high / low</div><div class="val">{high_10:+.3f} / {low_10:+.3f}</div><div class="note">end of the window</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # how the chart is built, as a strip of steps
    with st.container(border=True):
        section("How the chart is built", "notebook 06")
        st.markdown(
            """
            <div class="an-steps">
              <div class="an-step"><div class="num">1</div><div class="ttl">Find onsets</div>
                <div class="txt">A conflict year after two years without conflict.</div></div>
              <div class="an-step"><div class="num">2</div><div class="ttl">Cut a window</div>
                <div class="txt">5 years before to 10 years after the onset (t = -5 to 10).</div></div>
              <div class="an-step"><div class="num">3</div><div class="ttl">Set the baseline</div>
                <div class="txt">Democracy minus its value in the year before the conflict (t = -1).</div></div>
              <div class="an-step"><div class="num">4</div><div class="ttl">Split by arms</div>
                <div class="txt">Average imports over t = -5 to -1 above the median of all onsets = high importer.</div></div>
              <div class="an-step"><div class="num">5</div><div class="ttl">Average</div>
                <div class="txt">Mean change for every t and group. Wars only = 1,000+ deaths in t = 0 to 5.</div></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # sample size and example onsets
    left, right = st.columns([1, 1])
    with left:
        with st.container(border=True):
            section("How many onsets are behind each point", "onsets with data")
            show(an_sample_chart(summary))
            n_drop = n_high + n_low - int(an_value(summary, "high importer", 10, "n_countries")) \
                - int(an_value(summary, "low importer", 10, "n_countries"))
            last_year = int(panel["year"].max())
            n_recent = int((onsets["onset_year"] > last_year - 10).sum())
            how_to_read(f"Fewer onsets at the edges: {n_drop} of the {n_high + n_low} onsets have no data at t = 10. "
                        f"{n_recent} of them started after {last_year - 10}, so their 10-year window runs past the "
                        f"end of the data ({last_year}). Points with few onsets move more by chance.")
    with right:
        with st.container(border=True):
            section(f"Biggest changes after {t_pick} {years}", "single onsets, change in democracy index")
            col = "change_pick"
            event = load("event")
            at_t = event[event["t"] == t_pick][["iso3", "onset_year", "dem_change"]].rename(columns={"dem_change": col})
            picked = onsets.merge(at_t, on=["iso3", "onset_year"])
            c_up, c_down = st.columns(2)
            with c_up:
                st.markdown("**Largest rises**")
                st.markdown(an_list(picked.sort_values(col, ascending=False).head(6), col), unsafe_allow_html=True)
            with c_down:
                st.markdown("**Largest falls**")
                st.markdown(an_list(picked.sort_values(col).head(6), col), unsafe_allow_html=True)
            how_to_read("The averages hide big differences between countries. "
                        "Look one up in the table below or in the Country timeline page.")

    # table of all onsets
    with st.container(border=True):
        section("Explore the onsets", f"{len(onsets)} onsets · click a column to sort")
        group_pick = st.segmented_control("Group", ["Both groups", "High importers", "Low importers"],
                                          default="Both groups", key="an_group", label_visibility="collapsed")
        table = onsets.copy()
        if group_pick == "High importers":
            table = table[table["importer_group"] == "high importer"]
        elif group_pick == "Low importers":
            table = table[table["importer_group"] == "low importer"]
        table["war"] = table["war"].map({True: "war", False: "minor"})
        table = table[["country_name", "onset_year", "importer_group", "war", "imports_before",
                       "dem_before", "change_5", "change_10"]].sort_values(["country_name", "onset_year"])
        st.dataframe(table, hide_index=True, width="stretch", height=320, column_config={
            "country_name": "Country",
            "onset_year": st.column_config.NumberColumn("Onset year", format="%d"),
            "importer_group": "Group",
            "war": "Intensity (t = 0 to 5)",
            "imports_before": st.column_config.NumberColumn("Arms imports before (TIV / year)", format="%.0f"),
            "dem_before": st.column_config.NumberColumn("Democracy at t = -1", format="%.2f"),
            "change_5": st.column_config.NumberColumn("Change after 5 years", format="%+.3f"),
            "change_10": st.column_config.NumberColumn("Change after 10 years", format="%+.3f"),
        })

    with st.container(border=True):
        section("Findings")
        # TODO: replace with your three findings from 06 Part C (one sentence each, with a number)
        st.markdown("1. Finding one ...\n2. Finding two ...\n3. Finding three ...")

    st.warning(
        # TODO: replace with your own sentence
        "**What this chart cannot show:** it shows averages, not causes. High and low importers may differ in many "
        "other ways (wealth, region, type of conflict), and arms imports can also be a result of the conflict."
    )

    with st.expander("Show the numbers behind the chart"):
        st.dataframe(summary[["t", "importer_group", "dem_change", "n_countries", "low", "high"]],
                     hide_index=True, width="stretch", column_config={
                         "dem_change": st.column_config.NumberColumn("Average change", format="%+.4f"),
                         "n_countries": "Onsets",
                         "low": st.column_config.NumberColumn("95% band, low", format="%+.4f"),
                         "high": st.column_config.NumberColumn("95% band, high", format="%+.4f"),
                     })


# ---------------------------------------------------------------- page: Data and method
else:
    st.markdown('<p class="kicker">DATA AND METHOD</p>', unsafe_allow_html=True)
    st.title("Where the numbers come from")

    c1, c2, c3 = st.columns(3)
    with c1:
        with st.container(border=True):
            section("⚔️ UCDP/PRIO Armed Conflict", "v26.1")
            st.caption("Every armed conflict with at least 25 battle deaths in a year. Minor = 25 to 999 deaths, "
                       "war = 1,000 or more. We count a country as in conflict if a conflict was located there.")
    with c2:
        with st.container(border=True):
            section("🗳️ V-Dem Country-Year Core", "v16")
            st.caption("The electoral democracy index (v2x_polyarchy) from 0 to 1, and the regime type: closed autocracy, "
                       "electoral autocracy, electoral democracy, liberal democracy.")
    with c3:
        with st.container(border=True):
            section("🚀 SIPRI Arms Transfers", "1950 to 2025")
            st.caption("Every delivery of major weapons. Values are trend-indicator values (TIV), which measure military "
                       "capability, not money. Only states as recipients; deals not yet delivered are dropped.")

    with st.container(border=True):
        section("How the main chart is built")
        st.markdown(
            """
            1. **Merge** the three datasets into one table with one row per country and year (country codes matched with a crosswalk).
            2. **Find conflict onsets:** a year with an active conflict after at least two years without one.
               Conflicts already running in 1950 do not count.
            3. **Line them up:** for every onset, take the 5 years before and the 10 years after, and measure democracy as the
               change since the year before the conflict (t = -1).
            4. **Split by arms imports:** average imports over the 5 years before the onset; above the median of all onsets =
               high importer, otherwise low importer.
            5. **Average** the change in democracy for each year and group.
            """
        )

    st.caption("Data Analysis with Python, University of Zurich, HS26. Nicolas Centorame and Yair Segal.")