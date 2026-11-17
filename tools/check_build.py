"""Checker for app/build_nicolas.py

Run from the repo folder:
    python tools/check_build.py          status of all tasks + first hint for the first open task
    python tools/check_build.py hint     the same, plus a bigger hint (code skeleton)

It runs your app without a browser (Streamlit's test tool), clicks through the pages
and checks what appears. It never changes your file.
"""
import os
import sys
import warnings
import logging

warnings.filterwarnings("ignore")
logging.disable(logging.WARNING)

import io
import re
import contextlib
import pandas as pd
from streamlit.testing.v1 import AppTest

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
APP = os.path.join(ROOT, "app", "build_nicolas.py")
CLEAN = os.path.join(ROOT, "data", "clean")
BIG_HINT = "hint" in sys.argv[1:]
for arg in sys.argv[1:]:
    if arg.endswith(".py"):
        APP = os.path.abspath(arg)

panel = pd.read_csv(os.path.join(CLEAN, "panel.csv"))
sipri_suppliers = pd.read_csv(os.path.join(CLEAN, "sipri_suppliers.csv"))
SOURCE = open(APP, encoding="utf-8").read()
CODE = "\n".join(line for line in SOURCE.split("\n") if not line.strip().startswith("#"))

PAGES = ["Overview", "Country timeline", "Data and method"]

HINTS = {
    1: ("st.columns([2, 3, 2], vertical_alignment=\"center\") gives three columns. Put each widget "
        "inside `with col_x:`. Both widgets need their key, and `page`/`country` must be what they return.",
        """col_title, col_nav, col_search = st.columns([2, 3, 2], vertical_alignment="center")
with col_title:
    st.markdown("#### ...")
with col_nav:
    page = st.segmented_control("Page", [...three pages...], label_visibility="collapsed", key="page_nav")
with col_search:
    country = st.selectbox("Search a country", names, label_visibility="collapsed", key="country_box")
if page is None:
    page = ...
(and delete the two PLACEHOLDER lines above)"""),
    2: ("Three Streamlit calls for the text: st.caption, st.header, st.write. The two columns: "
        "st.columns([3, 2]) returns two objects you name col_map, col_find.",
        """st.caption("RESEARCH QUESTION")
st.header("What happens to democracy during and after armed conflict?")
st.write("And does it look different ... 1950 to 2025.")
col_map, col_find = st.columns([3, 2])"""),
    3: ("Inside `with col_map:` and `with st.container(border=True):`. Slider first, then filter panel "
        "by that year, then px.choropleth on the filtered table.",
        """with col_map:
    with st.container(border=True):
        map_year = st.slider("Year", 1950, 2025, 2000, key="map_year")
        map_data = panel[panel["year"] == ...]
        fig = px.choropleth(map_data, locations="iso3", color="regime_label",
                            hover_name="country_name", color_discrete_map=regime_colours)
        style_map(fig)
        st.plotly_chart(fig, width="stretch", key="map")"""),
    4: ("Split map_data into two tables with conflict_active == 0 and == 1. Make one choropleth per table. "
        "fig.update_traces(...) changes all layers of a figure. Then copy the layers of the second figure "
        "onto the first: for trace in second_fig.data: fig.add_trace(trace).",
        """show_conflicts = st.toggle("Show active conflicts", value=True)
if show_conflicts:
    calm = map_data[map_data["conflict_active"] == 0]
    war = map_data[...]
    fig = px.choropleth(calm, ...same arguments...)
    fig.update_traces(marker_opacity=0.35)
    war_fig = px.choropleth(war, ...same arguments...)
    war_fig.update_traces(marker_line_color="#1c1a17", marker_line_width=1.2, showlegend=False)
    for trace in war_fig.data:
        fig.add_trace(trace)
else:
    fig = px.choropleth(map_data, ...)"""),
    5: ("st.plotly_chart returns an event when you pass on_select=\"rerun\". event.selection.points "
        "is a list. Only do something if it is not empty.",
        """event = st.plotly_chart(fig, width="stretch", on_select="rerun", selection_mode="points", key="map")
points = event.selection.points
if len(points) > 0:
    clicked = points[0]["location"]
    match = panel[panel["iso3"] == clicked]
    if len(match) > 0:
        st.session_state["goto"] = match["country_name"].iloc[0]
        st.rerun()"""),
    6: ("A second toggle. Use if / else around the map: if the toggle is on, the animated map, "
        "otherwise everything from tasks 3 to 5.",
        """animate = st.toggle("Play through the years", value=False)
if animate:
    fig = px.choropleth(panel.sort_values("year"), locations="iso3", color="regime_label",
                        hover_name="country_name", animation_frame="year",
                        color_discrete_map=regime_colours)
    style_map(fig)
    st.plotly_chart(fig, width="stretch")
else:
    ... your map from tasks 3 to 5, indented one level more ..."""),
    7: ("Filter event_time twice by importer_group, then two ax.plot calls on one ax. "
        "ax.axvline(0, linestyle=\"--\") is the dashed line.",
        """with col_find:
    with st.container(border=True):
        st.caption("MAIN FINDING")
        st.subheader("Democracy around the start of a conflict")
        fig2, ax = plt.subplots(figsize=(5, 3.5))
        high = event_time[event_time["importer_group"] == "high importer"]
        low = ...
        ax.plot(high["t"], high["dem_change"], label="High arms imports")
        ax.plot(...)
        ax.axvline(0, linestyle="--", color="grey")
        ax.set_xlabel(...); ax.set_ylabel(...); ax.legend()
        st.pyplot(fig2)
        plt.close(fig2)
        with st.expander("Show the numbers"):
            st.dataframe(event_time, hide_index=True)"""),
    8: ("st.columns(3) and in each `with st.container(border=True):` an st.markdown(\"**name**\") "
        "and an st.caption. This is not inside col_map or col_find, so less indented.",
        """s1, s2, s3 = st.columns(3)
with s1:
    with st.container(border=True):
        st.markdown("**UCDP/PRIO Armed Conflict v26.1**")
        st.caption("Conflicts with at least 25 battle deaths in a year.")
(same for s2 with V-Dem and s3 with SIPRI)"""),
    9: ("Filter panel with two conditions: (panel[\"iso3\"] == iso3) & (panel[\"year\"] == year). "
        "Check len(rows) == 0 before you use rows.iloc[0]. For the supplier: filter sipri_suppliers the "
        "same way, drop \"Other\", sort by tiv from high to low, take the first row.",
        """rows = panel[(panel["iso3"] == iso3) & (panel["year"] == year)]
c1, c2, c3, c4 = st.columns(4)
if len(rows) == 0:
    c1.metric("Regime in " + str(year), "No data")
    c2.metric("Democracy index", "n/a")
    c3.metric("Armed conflicts", "n/a")
else:
    row = rows.iloc[0]
    c1.metric("Regime in " + str(year), row["regime_label"])
    c2.metric("Democracy index", round(row["democracy_index"], 2))
    if row["n_conflicts"] == 0:
        c3.metric("Armed conflicts", "None")
    elif row["max_intensity"] == 2:
        c3.metric("Armed conflicts", str(row["n_conflicts"]) + " · war")
    else:
        ...
sup = sipri_suppliers[(...) & (...)]
sup = sup[sup["supplier"] != "Other"]
if len(sup) == 0:
    c4.metric("Main arms supplier", "None")
else:
    top = sup.sort_values("tiv", ascending=False).iloc[0]
    c4.metric("Main arms supplier", top["supplier"])"""),
    10: ("First the code: panel[panel[\"country_name\"] == name][\"iso3\"].iloc[0]. Then everything inside "
         "`with st.container(border=True):`. plt.subplots(4, 1, sharex=True) gives four rows in `axes`.",
         """iso3 = panel[panel["country_name"] == name]["iso3"].iloc[0]
rows = panel[panel["iso3"] == iso3]
with st.container(border=True):
    st.subheader(name)
    st.caption("ISO3 " + iso3)
    year_card(iso3, year)
    fig, axes = plt.subplots(4, 1, sharex=True, figsize=(10, 6.5),
                             gridspec_kw={"height_ratios": [1, 2, 1, 2]})
    regime_bands(axes[0], vdem_regime_spans, iso3, year)
    axes[1].plot(rows["year"], rows["democracy_index"])
    conflict_bars(axes[2], ucdp_spans, iso3, year)
    axes[3].bar(rows["year"], rows["arms_imports_tiv"])
    axes[0].set_xlim(p0, p1)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)
    with st.expander("Year-by-year table for " + name):
        table = rows[(rows["year"] >= p0) & (rows["year"] <= p1)]
        st.dataframe(table, hide_index=True)"""),
    11: ("The dictionary maps the button text to (start, end). p0, p1 = periods[period] unpacks it. "
         "The slider's min and max are p0 and p1. The start value must lie inside: min(max(2000, p0), p1).",
         """periods = {"1950–2025": (1950, 2025), "Cold War": (1950, 1991), "Since 1992": (1992, 2025)}
c1, c2, c3 = st.columns([2, 3, 2], vertical_alignment="bottom")
with c1:
    period = st.segmented_control("Period", list(periods.keys()), default="1950–2025")
    if period is None:
        period = "1950–2025"
    p0, p1 = periods[period]
with c2:
    year = st.slider("Year", p0, p1, min(max(2000, p0), p1))
with c3:
    other = st.selectbox("Compare with", ["(none)"] + names)
if other == "(none)":
    show_country(country, year, p0, p1)
else:
    left, right = st.columns(2)
    with left:
        ...
    with right:
        ..."""),
    12: ("Like the source cards, but one container under the other. st.markdown with triple quotes "
         "lets you write several lines; lines starting with \"- \" become bullets.",
         """st.caption("DATA AND METHOD")
st.header("How the numbers are built")
with st.container(border=True):
    st.subheader("Pipeline")
    st.markdown(\"\"\"
- ...
- ...
\"\"\")
(same for "Main finding" and "Caveats")"""),
}

TITLES = {
    1: "Top bar", 2: "Research question and layout", 3: "Simple world map", 4: "Conflict highlight",
    5: "Map click", 6: "Play through the years", 7: "Main finding chart", 8: "Source cards",
    9: "Year card", 10: "Country card with timelines", 11: "Period, year, compare", 12: "Data and method",
}


class Fail(Exception):
    pass


def need(condition, message):
    if not condition:
        raise Fail(message)


def texts(elements):
    return [str(e.value) for e in elements]


def run(at):
    with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
        at.run()
    if len(at.exception) > 0:
        raise Fail("Your app stops with an error:\n      " + at.exception[0].message.split("\n")[0] +
                   "\n      Start it in the browser to see the red box with the line number.")
    return at


def get_plotly_spec(at):
    import json
    charts = at.get("plotly_chart")
    need(len(charts) > 0, "No Plotly map on the Overview page.")
    return json.loads(charts[0].proto.spec)


def new_app():
    return AppTest.from_file(APP, default_timeout=180)


def overview():
    at = new_app()
    return run(at)


def country_page(name="Ukraine"):
    at = new_app()
    run(at)
    at.session_state["page_nav"] = "Country timeline"
    at.session_state["country_box"] = name
    return run(at)


def find(elements, label):
    for e in elements:
        if e.label == label:
            return e
    return None


# ------------------------------------------------------------------------------ the checks

def t1():
    need(not re.search(r"PLACEHOLDER task 1(?!\d)", SOURCE), "Delete the two PLACEHOLDER lines of task 1 (page = ..., country = ...).")
    at = overview()
    groups = [b for b in at.get("button_group") if b.key == "page_nav"]
    need(len(groups) == 1, "No st.segmented_control with key=\"page_nav\" found.")
    options = [o.content for o in groups[0].proto.options]
    need(options == PAGES, "The page buttons should be exactly " + str(PAGES) + ", you have " + str(options) + ".")
    boxes = [s for s in at.selectbox if s.key == "country_box"]
    need(len(boxes) == 1, "No st.selectbox with key=\"country_box\" found.")
    need(len(boxes[0].options) == len(panel["country_name"].unique()),
         "The search box should list all countries (the list `names`).")
    need(any("Weapons" in t and "Conflict" in t for t in texts(at.markdown)),
         "The app name \"Weapons · Democracy · Conflict\" is missing (st.markdown(\"#### ...\")).")


def t2():
    need("PLACEHOLDER tasks 2 to 8" not in SOURCE, "Delete the PLACEHOLDER line under if page == \"Overview\": once you start task 2.")
    at = overview()
    need(any("RESEARCH QUESTION" in t for t in texts(at.caption)), "st.caption(\"RESEARCH QUESTION\") is missing.")
    need(any("democracy" in t.lower() for t in texts(at.header)),
         "st.header with the research question is missing.")
    need("col_map" in SOURCE and "col_find" in SOURCE, "Name the two columns col_map and col_find.")


def t3():
    at = overview()
    slider = [s for s in at.slider if s.key == "map_year"]
    need(len(slider) == 1, "No st.slider with key=\"map_year\" on the Overview.")
    need(slider[0].min == 1950 and slider[0].max == 2025 and slider[0].value == 2000,
         "The map slider should go from 1950 to 2025 and start at 2000.")
    spec = get_plotly_spec(at)
    traces = spec["data"]
    need(len(traces) > 0 and traces[0]["type"] == "choropleth", "The map should be a px.choropleth.")
    need(all(t.get("locations") is not None for t in traces), "Use locations=\"iso3\".")
    need(spec["layout"].get("geo", {}).get("projection", {}).get("type") == "natural earth",
         "Call style_map(fig) before st.plotly_chart.")
    slider[0].set_value(1960)
    run(at)
    spec60 = get_plotly_spec(at)
    n60 = sum(len(t.get("locations", [])) for t in spec60["data"])
    expected = len(panel[panel["year"] == 1960])
    need(n60 == expected, "In 1960 the map should show " + str(expected) + " countries, it shows " + str(n60) +
         ". Is map_data filtered by the slider year?")


def t4():
    at = overview()
    tog = find(at.toggle, "Show active conflicts")
    need(tog is not None, "No st.toggle(\"Show active conflicts\").")
    need(tog.value is True, "The conflict toggle should be on at the start (value=True).")
    traces = get_plotly_spec(at)["data"]
    faded = [t for t in traces if t.get("marker", {}).get("opacity") == 0.35]
    outlined = [t for t in traces if t.get("marker", {}).get("line", {}).get("width", 0) > 0]
    need(len(faded) > 0, "Countries without conflict should be faded: marker_opacity=0.35.")
    need(len(outlined) > 0, "Countries in conflict need an outline: marker_line_width=1.2.")
    need(all(t.get("showlegend") is False for t in outlined), "Hide the legend of the conflict layer: showlegend=False.")
    n_war = sum(len(t["locations"]) for t in outlined)
    expected = int(panel[(panel["year"] == 2000)]["conflict_active"].sum())
    need(n_war == expected, "In 2000 there should be " + str(expected) + " outlined countries, you have " + str(n_war) + ".")
    tog.set_value(False)
    run(at)
    traces = get_plotly_spec(at)["data"]
    need(all(t.get("marker", {}).get("opacity") != 0.35 for t in traces),
         "With the toggle off, all countries should look normal (no faded layer).")


def t5():
    need('on_select="rerun"' in CODE or "on_select='rerun'" in CODE, "st.plotly_chart needs on_select=\"rerun\".")
    need("selection.points" in CODE, "Read the clicked countries from event.selection.points.")
    need('st.session_state["goto"]' in CODE.split("if page == \"Overview\":")[-1],
         "On the Overview, store the clicked country name in st.session_state[\"goto\"].")
    need("st.rerun()" in CODE, "Call st.rerun() after storing goto.")
    at = overview()
    at.session_state["goto"] = "Colombia"
    run(at)
    need(at.session_state["page_nav"] == "Country timeline", "The GIVEN block should switch the page. Did you change it?")


def t6():
    at = overview()
    tog = find(at.toggle, "Play through the years")
    need(tog is not None, "No st.toggle(\"Play through the years\").")
    need(tog.value is False, "The play toggle should be off at the start.")
    tog.set_value(True)
    run(at)
    spec = get_plotly_spec(at)
    need(len(spec.get("frames", [])) >= 70, "With the toggle on, the map needs animation_frame=\"year\" (one frame per year).")


def t7():
    at = overview()
    need(any("MAIN FINDING" in t for t in texts(at.caption)), "st.caption(\"MAIN FINDING\") is missing.")
    need(any("conflict" in t.lower() for t in texts(at.subheader)), "The subheader of the finding is missing.")
    need(len(at.get("image")) >= 1, "No matplotlib chart (st.pyplot) on the Overview.")
    exp = find(at.expander, "Show the numbers")
    need(exp is not None, "No st.expander(\"Show the numbers\").")
    need(len(exp.get("dataframe")) == 1, "Put st.dataframe(event_time) inside the expander.")


def t8():
    at = overview()
    all_text = " ".join(texts(at.markdown))
    for word in ["UCDP", "V-Dem", "SIPRI"]:
        need(word in all_text, "Source card with \"" + word + "\" in bold (st.markdown) is missing.")
    need(len(at.caption) >= 5, "Each source card needs one sentence in st.caption.")


def t9():
    need(not re.search(r"PLACEHOLDER task 9(?!\d)", SOURCE), "Delete the PLACEHOLDER line in year_card.")
    at = country_page("Ukraine")
    labels = [m.label for m in at.metric]
    need(len(at.metric) >= 4, "year_card should show four st.metric boxes, there are " + str(len(at.metric)) + ".")
    year = 2000
    sliders = [s for s in at.slider if s.label == "Year"]
    if len(sliders) > 0:
        year = sliders[0].value
    row = panel[(panel["iso3"] == "UKR") & (panel["year"] == year)].iloc[0]
    values = {m.label: str(m.value) for m in at.metric}
    need("Regime in " + str(year) in values, "First label should be \"Regime in " + str(year) + "\". You have " + str(labels[:4]) + ".")
    need(values["Regime in " + str(year)] == row["regime_label"], "Regime value should be " + row["regime_label"] + ".")
    need(values.get("Democracy index") == str(round(row["democracy_index"], 2)),
         "Democracy index for Ukraine " + str(year) + " should be " + str(round(row["democracy_index"], 2)) + ".")
    need("Armed conflicts" in values, "Label \"Armed conflicts\" is missing.")
    need("Main arms supplier" in values, "Label \"Main arms supplier\" is missing.")
    sup = sipri_suppliers[(sipri_suppliers["iso3"] == "UKR") & (sipri_suppliers["year"] == year)]
    sup = sup[sup["supplier"] != "Other"]
    want = "None" if len(sup) == 0 else sup.sort_values("tiv", ascending=False).iloc[0]["supplier"]
    need(values["Main arms supplier"] == want, "Main supplier should be " + want + ", you show " + values["Main arms supplier"] + ".")
    if len(sliders) > 0:
        sliders[0].set_value(2014)
        run(at)
        values = {m.label: str(m.value) for m in at.metric}
        need(values.get("Armed conflicts", "").endswith("war"), "Ukraine 2014 should show a war (max_intensity 2).")
        sliders = [s for s in at.slider if s.label == "Year"]
        sliders[0].set_value(1980)
        run(at)
        values = {m.label: str(m.value) for m in at.metric}
        need(values.get("Regime in 1980") == "No data", "Ukraine 1980 has no V-Dem row: show \"No data\".")


def t10():
    need(not re.search(r"PLACEHOLDER task 10(?!\d)", SOURCE), "Delete the PLACEHOLDER line in show_country.")
    at = country_page("Colombia")
    need("Colombia" in texts(at.subheader), "st.subheader(name) is missing in show_country.")
    need(any(t == "ISO3 COL" for t in texts(at.caption)), "st.caption(\"ISO3 \" + iso3) is missing.")
    need(len(at.get("image")) >= 1, "No timeline figure (st.pyplot) in show_country.")
    exp = [e for e in at.expander if e.label.startswith("Year-by-year table")]
    need(len(exp) == 1, "st.expander(\"Year-by-year table for \" + name) is missing.")
    need(len(exp[0].get("dataframe")) == 1, "Put the table (st.dataframe) inside the expander.")


def t11():
    need(not re.search(r"PLACEHOLDER task 11(?!\d)", SOURCE), "Delete the three PLACEHOLDER lines of task 11.")
    at = country_page("Ukraine")
    groups = [b for b in at.get("button_group") if b.key != "page_nav"]
    need(len(groups) == 1, "No st.segmented_control(\"Period\", ...) on the Country page.")
    options = [o.content for o in groups[0].proto.options]
    need(options == ["1950–2025", "Cold War", "Since 1992"], "Period buttons should be 1950–2025, Cold War, Since 1992.")
    slider = [s for s in at.slider if s.label == "Year"]
    need(len(slider) == 1 and slider[0].value == 2000, "A \"Year\" slider starting at 2000 is missing.")
    groups[0].set_value("Cold War")
    run(at)
    slider = [s for s in at.slider if s.label == "Year"]
    need(slider[0].max == 1991 and slider[0].value == 1991, "With Cold War the slider should end at 1991 (and start there).")
    comp = find(at.selectbox, "Compare with")
    need(comp is not None and comp.options[0] == "(none)", "st.selectbox(\"Compare with\", [\"(none)\"] + names) is missing.")
    comp.set_value("Colombia")
    run(at)
    subs = texts(at.subheader)
    need("Ukraine" in subs and "Colombia" in subs, "With a comparison, both countries need their own card.")


def t12():
    need(not re.search(r"PLACEHOLDER task 12(?!\d)", SOURCE), "Delete the PLACEHOLDER line of task 12.")
    at = new_app()
    run(at)
    at.session_state["page_nav"] = "Data and method"
    run(at)
    need("How the numbers are built" in texts(at.header), "st.header(\"How the numbers are built\") is missing.")
    subs = texts(at.subheader)
    for s in ["Pipeline", "Main finding", "Caveats"]:
        need(s in subs, "Subheader \"" + s + "\" is missing.")
    need(len(at.markdown) >= 4, "Write the bullet points with st.markdown.")


CHECKS = [t1, t2, t3, t4, t5, t6, t7, t8, t9, t10, t11, t12]


def main():
    print("\nChecking " + os.path.relpath(APP, ROOT) + "\n")
    try:
        compile(SOURCE, APP, "exec")
    except SyntaxError as e:
        print("  Your file has a Python error before anything can run:")
        print("    line " + str(e.lineno) + ": " + str(e.msg))
        if e.text:
            print("    " + e.text.strip())
        print("\n  Typical causes: a missing colon after if/else/with/def, an opening bracket without")
        print("  its closing one, or wrong indentation (every block under if/with/def is indented")
        print("  4 spaces more). An if/elif/else block may not be empty: leave the PLACEHOLDER line")
        print("  in it until you write the first real line.\n")
        return
    blanks = []
    docstring_end = SOURCE.find('"""', 3) + 3
    first_code_line = SOURCE[:docstring_end].count("\n") + 1
    for number, line in enumerate(SOURCE.split("\n"), start=1):
        if number > first_code_line and "___" in line and not line.strip().startswith("#"):
            blanks.append(number)
    if len(blanks) > 0:
        print("  You uncommented lines but still have ___ blanks in them, on line(s): " +
              ", ".join(str(b) for b in blanks))
        print("  Replace every ___ with the right value before the app can run.\n")
    first_open = None
    first_message = ""
    for number, check in enumerate(CHECKS, start=1):
        try:
            check()
            print("  OK    Task " + str(number).rjust(2) + "  " + TITLES[number])
        except Fail as f:
            print("  open  Task " + str(number).rjust(2) + "  " + TITLES[number])
            if first_open is None:
                first_open = number
                first_message = str(f)
        except Exception as e:
            print("  open  Task " + str(number).rjust(2) + "  " + TITLES[number] + "  (check crashed: " + type(e).__name__ + ")")
            if first_open is None:
                first_open = number
                first_message = "Something unexpected: " + type(e).__name__ + ": " + str(e)[:200]
    print()
    if first_open is None:
        print("All 12 tasks pass. Commit, push, and ask Claude to review your code style.\n")
        return
    print("Next: Task " + str(first_open) + " (" + TITLES[first_open] + ")")
    print("  What is wrong: " + first_message)
    print("  Hint: " + HINTS[first_open][0])
    if BIG_HINT:
        print("\n  Bigger hint (fill in the ... yourself):\n")
        for line in HINTS[first_open][1].split("\n"):
            print("      " + line)
    else:
        print("\n  Still stuck? Run:  python tools/check_build.py hint")
    print()


main()
