"""Glossary and FAQ: definitions of the regime types, conflict types, arms measures and methods used on
the site, and answers to common questions. Native Streamlit only."""

import plotly.graph_objects as go
import streamlit as st
from streamlit.errors import StreamlitAPIException

import native_data as nd

# term, category, definition, source
TERMS = [
    # ---------------------------------------------------------------- political regimes
    ("Regimes of the World", "Political regimes",
     "V-Dem's four-category classification of political regimes (variable v2x_regime). Every country-year is "
     "assigned exactly one of the four types below, based on V-Dem's expert-coded indicators.", "V-Dem v16"),
    ("Closed autocracy", "Political regimes",
     "No multiparty elections for the chief executive or the legislature. Examples: one-party states, "
     "absolute monarchies, military juntas.", "V-Dem v16 (Regimes of the World)"),
    ("Electoral autocracy", "Political regimes",
     "Multiparty elections for the chief executive and the legislature take place, but they are not free and "
     "fair, or basic freedoms such as expression and association are not sufficiently guaranteed.",
     "V-Dem v16 (Regimes of the World)"),
    ("Electoral democracy", "Political regimes",
     "Free and fair multiparty elections, with sufficient freedom of expression and association, but the "
     "liberal criteria (rule of law, constraints on the executive) are not fully met.",
     "V-Dem v16 (Regimes of the World)"),
    ("Liberal democracy", "Political regimes",
     "An electoral democracy that also meets the liberal criteria: equality before the law, independent "
     "courts and legislature that constrain the executive, and protection of individual liberties.",
     "V-Dem v16 (Regimes of the World)"),
    ("Democracy index", "Political regimes",
     "V-Dem's Electoral Democracy Index (v2x_polyarchy), from 0 (least) to 1 (most democratic). It combines "
     "free and fair elections, freedom of expression, freedom of association, suffrage and elected officials. "
     "Small year-to-year changes carry little meaning; it is based on expert assessments.", "V-Dem v16"),
    ("Autocratisation / democratisation", "Political regimes",
     "A move down / up in the democracy index or to a less / more democratic regime type. On this site it is "
     "only described, not explained.", "Project definition"),

    # ---------------------------------------------------------------- armed conflict
    ("Armed conflict", "Armed conflict",
     "A contested incompatibility over government and/or territory, where the use of armed force between two "
     "parties, at least one of which is the government of a state, results in at least 25 battle-related "
     "deaths in a calendar year.", "UCDP/PRIO Armed Conflict Dataset v26.1"),
    ("Battle-related deaths", "Armed conflict",
     "Deaths caused by the warring parties that can be directly related to combat, including civilians killed "
     "in the fighting. One-sided violence against civilians and non-state conflicts are separate UCDP datasets "
     "and not included here.", "UCDP"),
    ("Minor conflict", "Armed conflict",
     "An armed conflict with 25 to 999 battle-related deaths in a given year (UCDP intensity level 1).", "UCDP/PRIO"),
    ("War", "Armed conflict",
     "An armed conflict with at least 1,000 battle-related deaths in a given year (UCDP intensity level 2). "
     "On the World map, war countries have denser stripes.", "UCDP/PRIO"),
    ("Interstate conflict", "Armed conflict",
     "Armed conflict between two or more states.", "UCDP/PRIO (type 2)"),
    ("Intrastate conflict", "Armed conflict",
     "Armed conflict between a government and one or more internal opposition groups, without intervention "
     "from other states.", "UCDP/PRIO (type 3)"),
    ("Internationalised intrastate conflict", "Armed conflict",
     "An intrastate conflict in which other states send troops to support one or both sides.", "UCDP/PRIO (type 4)"),
    ("Extrasystemic conflict", "Armed conflict",
     "Armed conflict between a state and a non-state group outside the state's own territory, mostly colonial "
     "wars of the 1950s and 1960s.", "UCDP/PRIO (type 1)"),
    ("Incompatibility", "Armed conflict",
     "What the conflict is about: control of the government (type of political system, replacement of the "
     "government) or territory (secession or autonomy of a region).", "UCDP"),
    ("Conflict onset", "Armed conflict",
     "Our definition: a year with an active armed conflict in a country after two years without one. The "
     "main finding and the regressions look at democracy around these onsets.", "Project definition (notebook 06)"),

    # ---------------------------------------------------------------- arms transfers
    ("Major conventional arms", "Arms transfers",
     "What SIPRI records: aircraft, armoured vehicles, artillery, sensors, air defence, missiles, ships, "
     "engines and some other systems. Small arms, ammunition and most services are not included.",
     "SIPRI Arms Transfers Database"),
    ("TIV (trend-indicator value)", "Arms transfers",
     "SIPRI's unit for the volume of arms transfers, in millions. It is based on the known production cost of "
     "a core set of weapons and measures the military capability transferred, not the price paid. Use it to "
     "compare volumes and trends, not as money.", "SIPRI"),
    ("Supplier / recipient", "Arms transfers",
     "The country (or, rarely, an organisation or armed group) that delivers / receives the weapons. Deliveries "
     "are counted in the year they arrive.", "SIPRI"),
    ("Arms imports", "Arms transfers",
     "Sum of TIV a country received in a year. Years without any recorded delivery count as 0.", "SIPRI, our panel"),
    ("Arms build-up", "Arms transfers",
     "Our measure on the World map: major arms received over the previous 10 years (sum of TIV), so that one "
     "big delivery does not dominate a single year.", "Project definition"),
    ("Main supplier", "Arms transfers",
     "The supplier that delivered the most TIV to a country over the last 5 years.", "Project definition"),
    ("High / low arms importers", "Arms transfers",
     "For each conflict onset: the average arms imports in the 5 years before onset, split at the median of all "
     "onsets. Above the median = high importer.", "Project definition (notebook 06)"),
    ("Supplier democracy", "Arms transfers",
     "The TIV-weighted average democracy index of the countries that supplied a country's arms in a year "
     "(0 = arms from autocracies, 1 = from democracies). Share from democracies = share of TIV from suppliers "
     "that were electoral or liberal democracies.", "Project definition (notebook 08)"),

    # ---------------------------------------------------------------- methods
    ("Country-year panel", "Methods",
     "One row per country and year, 1950 to 2025, joining V-Dem, UCDP and SIPRI on one country code. V-Dem "
     "decides which country exists in which year.", "Notebook 05"),
    ("Event study", "Methods",
     "Compares each country with itself in the years before and after a conflict onset (from 10 years before "
     "to 10 after). The years before should show no change if democracy was not already moving.",
     "Notebook 08"),
    ("Fixed effects", "Methods",
     "Country fixed effects compare a country only with itself; year fixed effects remove changes that hit the "
     "whole world in the same year (for example the end of the Cold War).", "Notebook 08"),
    ("95% confidence interval", "Methods",
     "The range that would contain the true value in 95 of 100 repeated samples. If it crosses zero, the data "
     "do not show a clear effect.", "Statistics"),
    ("Correlation vs causation", "Methods",
     "All results on this site are associations. Democracy, conflict and arms imports influence each other, so "
     "the charts cannot show what causes what.", "Project caveat"),
    ("Placeholder numbers", "Methods",
     "Until the regressions of notebook 08 are finished, the Findings page shows random preview numbers so the "
     "layout can be checked. A warning marks them; the page switches to the real results automatically.",
     "Project"),

    # ---------------------------------------------------------------- map and data
    ("Equal Earth projection", "Map and data",
     "The world map projection used on this site. It keeps every country's area in its true proportion, so "
     "Africa and South America are not shrunk next to Europe as in the Mercator projection.", "Šavrič, Patterson & Jenny (2018)"),
    ("Historical states", "Map and data",
     "States that no longer exist are drawn at today's borders: the Soviet Union at Russia, Czechoslovakia at "
     "Czechia, Yugoslavia at Serbia, East Germany at Germany, South Yemen at Yemen, South Vietnam at Vietnam.",
     "Project convention (V-Dem codes)"),
    ("Cold War / since 1992", "Map and data",
     "The two periods offered on the site: 1950 to 1991 (until the end of the Soviet Union) and 1992 to 2025.",
     "Project convention"),
]

# FAQ themes: label, icon, one-line description
THEMES = {
    "data": ("About the data", ":material/database:", "Where the numbers come from and how they are counted."),
    "map": ("Reading the map", ":material/map:", "Colours, stripes, borders and the projection."),
    "use": ("Using the site", ":material/touch_app:", "Comparing countries and getting at the numbers."),
    "limits": ("What results mean", ":material/balance:", "What the site can and cannot tell you."),
}

# Pages the FAQ can point to (paths as registered in native_app.py)
PAGES = {
    "world_map": ("native_pages/world_map.py", "World map", ":material/public:"),
    "findings": ("native_pages/findings.py", "Findings", ":material/insights:"),
    "compare": ("native_pages/compare.py", "Countries & compare", ":material/compare_arrows:"),
    "about": ("native_pages/about.py", "About the data", ":material/info:"),
}

# theme, question, short answer, bullets, pages to see, glossary terms to see
FAQ = [
    # ---------------------------------------------------------------- about the data
    ("data", "Where does the data come from?",
     "Three public datasets, joined into one country-year table.",
     ["**Conflicts:** UCDP/PRIO Armed Conflict Dataset v26.1",
      "**Regimes and democracy index:** V-Dem v16 Core",
      "**Arms deliveries:** SIPRI Arms Transfers Database, 1950 to 2025"],
     ["about"], ["Country-year panel"]),
    ("data", "Why is TIV not in dollars?",
     "TIV measures military capability transferred, not the price paid.",
     ["It is based on production costs of comparable weapons.",
      "Prices of real deals vary a lot (discounts, aid, credit).",
      "So TIV is better for comparing volumes over time and between countries."],
     [], ["TIV (trend-indicator value)"]),
    ("data", "What counts as a war?",
     "A conflict year with at least 1,000 battle-related deaths.",
     ["**War:** 1,000+ deaths (UCDP intensity 2)",
      "**Minor conflict:** 25 to 999 deaths",
      "**Below 25 deaths:** UCDP records no armed conflict"],
     [], ["War", "Minor conflict"]),
    ("data", "When does a conflict 'start' on this site?",
     "In a year with an active conflict after two years without one.",
     ["We call this a conflict onset.",
      "It avoids counting the same long conflict many times."],
     ["findings"], ["Conflict onset"]),

    # ---------------------------------------------------------------- reading the map
    ("map", "Why is a country grey or missing?",
     "Grey means V-Dem has no data for that country in that year.",
     ["For example, years before independence.",
      "Very small states such as Monaco or Liechtenstein are not in V-Dem at all."],
     ["world_map"], []),
    ("map", "Why is the Soviet Union shown as Russia?",
     "The map uses today's borders and V-Dem's country codes.",
     ["In those codes, Russia continues the Soviet Union.",
      "The same goes for Czechoslovakia (Czechia), Yugoslavia (Serbia) and other historical states."],
     ["world_map"], ["Historical states"]),
    ("map", "What do the stripes on the World map mean?",
     "A striped country had an active armed conflict that year.",
     ["Denser stripes mean a war (1,000+ battle-related deaths)."],
     ["world_map"], ["Armed conflict"]),
    ("map", "Why does the arms-flows map show only some deliveries?",
     "To stay readable, it draws only the year's largest 25 (or 60) deliveries.",
     ["The badge shows how much of the year's TIV those cover.",
      "The chord ring, tables and totals use **all** deliveries."],
     ["world_map"], []),
    ("map", "Why the Equal Earth map and not the usual one?",
     "Equal Earth keeps every country's area in proportion.",
     ["The common Mercator map makes countries near the poles look much bigger than they are.",
      "True areas matter when countries are compared on the map."],
     ["world_map"], ["Equal Earth projection"]),

    # ---------------------------------------------------------------- using the site
    ("use", "How do I compare countries?",
     "Open Countries & compare and pick countries in the sidebar.",
     ["Or choose a group, such as the European Union or the G7.",
      "The year slider and Play move all charts together."],
     ["compare"], []),
    ("use", "Can I see the exact numbers?",
     "Yes: most charts have a 'Show the numbers' table.",
     ["Every table can be searched and downloaded from its toolbar."],
     ["findings", "compare"], []),

    # ---------------------------------------------------------------- what results mean
    ("limits", "Do arms imports cause democracy to decline?",
     "The site cannot tell: it shows what happened at the same time.",
     ["Democracy, armed conflict and arms imports influence each other.",
      "For example, a government at war buys weapons and also restricts freedoms.",
      "So any pattern is an association, not proof of a cause."],
     ["findings"], ["Correlation vs causation"]),
    ("limits", "Why do the Findings show placeholder numbers?",
     "The regressions in notebook 08 are not finished yet.",
     ["Until they are, random preview numbers show how the results will look.",
      "A warning at the top of the Findings page says so."],
     ["findings"], ["Placeholder numbers"]),
]

# ------------------------------------------------------------------ layout helpers
BY_NAME = {t[0]: t for t in TERMS}
REG_TERMS = ["Closed autocracy", "Electoral autocracy", "Electoral democracy", "Liberal democracy"]
TYPE_TERMS = ["Extrasystemic conflict", "Interstate conflict", "Intrastate conflict", "Internationalised intrastate conflict"]
LADDER = ["Minor conflict", "War"]
SPECIAL = set(REG_TERMS + TYPE_TERMS + LADDER)


def term_rows(items):
    """Terms two per row in bordered columns, so the boxes of one row have the same height."""
    for i in range(0, len(items), 2):
        pair = items[i:i + 2]
        boxes = st.columns(2, border=True, gap="medium") if len(pair) == 2 else [st.container(border=True)]
        for col, (term, _, definition, source) in zip(boxes, pair):
            with col:
                st.markdown(f"**{term}**")
                st.markdown(definition)
                st.caption(source)


def others(cat):
    return [t for t in TERMS if t[1] == cat and t[0] not in SPECIAL]


def faq_text(item):
    """Everything a FAQ entry says, lower-cased, for the search."""
    theme, question, short, bullets, _, terms = item
    return " ".join([THEMES[theme][0], question, short, *bullets, *terms]).lower()


def look_up(term):
    st.session_state["g_query"] = term


def faq_card(item, key):
    """One question: the question, a bold one-line answer, a few bullets, then links to pages and terms."""
    theme, question, short, bullets, pages, terms = item
    st.markdown(f"**{question}**")
    st.markdown(f":blue[{short}]")
    st.markdown("\n".join(f"- {b}" for b in bullets))
    if pages or terms:
        with st.container(horizontal=True, vertical_alignment="center", gap="small"):
            st.caption("See also", width="content")
            for p in pages:
                path, label, icon = PAGES[p]
                try:
                    st.page_link(path, label=label, icon=icon, width="content")
                except StreamlitAPIException:  # page run on its own, outside native_app.py's navigation
                    st.caption(f"{icon} {label} page", width="content")
            for j, term in enumerate(terms):
                st.button(term, icon=":material/menu_book:", type="tertiary", key=f"{key}_t{j}",
                          on_click=look_up, args=(term,), help="Look this term up in the glossary")


def faq_grid(items, key):
    """FAQ cards two per row in bordered columns, so the cards of one row have the same height."""
    for i in range(0, len(items), 2):
        pair = items[i:i + 2]
        # a lone last card keeps half the width, without an empty bordered box beside it
        boxes = (st.columns(2, border=True, gap="medium") if len(pair) == 2
                 else [st.columns(2, gap="medium")[0].container(border=True)])
        for j, (col, item) in enumerate(zip(boxes, pair)):
            with col:
                faq_card(item, f"{key}_{i + j}")


panel = nd.load_panel()
LAST = int(panel["year"].max())
now = panel[panel["year"] == LAST]


def regime_scale():
    """One stacked bar: countries per regime type in the latest year, in the map colours."""
    fig = go.Figure()
    for code, name in enumerate(nd.REGIMES):
        n = int((now["regime_type"] == code).sum())
        fig.add_bar(y=[""], x=[n], orientation="h", marker_color=nd.REGIME_COLOURS[name], name=name.capitalize(),
                    text=f"{name.capitalize()} · {n}", textposition="inside", insidetextanchor="middle",
                    hovertemplate=f"{name.capitalize()}: {n} countries in {LAST}<extra></extra>")
    fig.update_layout(barmode="stack", height=64, margin=dict(l=0, r=0, t=0, b=0), showlegend=False,
                      xaxis=dict(visible=False, range=[0, int(now["regime_type"].notna().sum())]), yaxis=dict(visible=False),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      uniformtext=dict(minsize=11, mode="hide"), font=dict(color="#f0efec"))
    return fig


# ------------------------------------------------------------------ page
st.title("Glossary and FAQ")
query = st.text_input("Search", placeholder="Search terms and questions, e.g. war, TIV, autocracy",
                      icon=":material/search:", label_visibility="collapsed", key="g_query")
q = query.strip().lower()

if q:
    hits = [t for t in TERMS if q in t[0].lower() or q in t[2].lower()]
    faq_hits = [f for f in FAQ if q in faq_text(f)]
    st.caption(f"{len(hits)} terms and {len(faq_hits)} questions match “{query}”.")
    if not hits and not faq_hits:
        st.info("Nothing matches. Try a shorter word.", icon=":material/search_off:")
    if hits:
        st.markdown("##### :material/menu_book: Terms")
        term_rows(hits)
    if faq_hits:
        st.markdown("##### :material/help: Questions")
        faq_grid(faq_hits, "s")
    st.stop()

t_reg, t_con, t_arms, t_meth, t_map, t_faq = st.tabs(
    [":material/how_to_vote: Political regimes", ":material/crisis_alert: Armed conflict",
     ":material/flight: Arms transfers", ":material/functions: Methods", ":material/map: Map and data",
     ":material/help: FAQ"])

with t_reg:
    st.caption(f"V-Dem sorts every country-year into one of four regime types, from least to most democratic. "
               f"The bar shows how many countries had each type in {LAST}; the colours are those of the World map.")
    st.plotly_chart(regime_scale(), config={"displayModeBar": False, "staticPlot": True}, key="g_scale")
    for col, name in zip(st.columns(4, border=True), REG_TERMS):
        with col:
            st.markdown(f"**{name}**")
            st.markdown(BY_NAME[name][2])
    term_rows(others("Political regimes"))

with t_con:
    st.caption("UCDP counts battle-related deaths per conflict and year. The number of deaths decides whether a "
               f"conflict is recorded at all and whether it is a war. Countries in {LAST}:")
    minor = int(((now["conflict_active"] == 1) & (now["max_intensity"] == 1)).sum())
    war = int((now["max_intensity"] == 2).sum())
    none_ = int(len(now) - minor - war)
    a, b, c = st.columns(3, border=True)
    a.metric("Below 25 deaths", f"{none_} countries", help="No armed conflict recorded by UCDP")
    a.caption("Not recorded as armed conflict")
    b.metric("Minor conflict · 25–999", f"{minor} countries")
    b.caption(BY_NAME["Minor conflict"][2])
    c.metric("War · 1,000+", f"{war} countries")
    c.caption(BY_NAME["War"][2])
    st.markdown("##### Types of conflict")
    for col, name in zip(st.columns(4, border=True), TYPE_TERMS):
        with col:
            st.markdown(f"**{name}**")
            st.markdown(BY_NAME[name][2])
            st.caption(BY_NAME[name][3])
    st.markdown("##### Other terms")
    term_rows(others("Armed conflict"))

with t_arms:
    term_rows(others("Arms transfers"))

with t_meth:
    term_rows(others("Methods"))

with t_map:
    term_rows(others("Map and data"))

with t_faq:
    st.caption(f"{len(FAQ)} short answers in {len(THEMES)} themes. Pick a theme, or use the search box above.")
    theme = st.segmented_control(
        "Theme", ["all", *THEMES], default="all", required=True, key="g_faq_theme", label_visibility="collapsed",
        format_func=lambda k: ":material/apps: All" if k == "all" else f"{THEMES[k][1]} {THEMES[k][0]}")
    for k, (label, icon, blurb) in THEMES.items():
        if theme not in ("all", k):
            continue
        items = [f for f in FAQ if f[0] == k]
        st.markdown(f"#### {icon} {label}")
        st.caption(f"{blurb} · {len(items)} questions")
        faq_grid(items, f"f_{k}")
