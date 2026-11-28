"""About the data, with the glossary and the FAQ: how the three sources are joined, what the main finding measures
and where to be careful; definitions of the regime types, conflict types, arms measures and methods used in the app;
and short answers to common questions. Three tabs on one page. Native Streamlit only."""

import altair as alt
import pandas as pd
import streamlit as st
from streamlit.errors import StreamlitAPIException

import native_data as nd
import native_results as nr

# term, category, short definition (1–2 sentences), source, more detail (optional, shown in an expander)
TERMS = [
    # ---------------------------------------------------------------- political regimes
    ("Regimes of the World", "Political regimes",
     "V-Dem's four regime types. Every country-year gets exactly one of them.",
     "V-Dem v16, variable v2x_regime", ""),
    ("Closed autocracy", "Political regimes",
     "No multiparty elections for the head of government or the legislature.",
     "V-Dem v16", "Examples: one-party states, absolute monarchies, military juntas."),
    ("Electoral autocracy", "Political regimes",
     "Multiparty elections take place, but they are not free and fair.",
     "V-Dem v16", "Or basic freedoms such as expression and association are not sufficiently guaranteed."),
    ("Electoral democracy", "Political regimes",
     "Free and fair multiparty elections with freedom of expression and association.",
     "V-Dem v16", "The liberal criteria (rule of law, limits on the executive) are not fully met."),
    ("Liberal democracy", "Political regimes",
     "An electoral democracy that also has the rule of law and real limits on the executive.",
     "V-Dem v16", "Equality before the law, independent courts and legislature, and protected individual liberties."),
    ("Democracy index", "Political regimes",
     "V-Dem's Electoral Democracy Index, from 0 (least) to 1 (most democratic).",
     "V-Dem v16, variable v2x_polyarchy",
     "It combines free and fair elections, freedom of expression and association, suffrage and elected officials. "
     "It rests on expert assessments, so small changes from one year to the next carry little meaning."),
    ("Autocratisation / democratisation", "Political regimes",
     "A move down / up in the democracy index or to a less / more democratic regime type.",
     "Project definition", "The app describes these moves; it does not explain them."),

    # ---------------------------------------------------------------- armed conflict
    ("Armed conflict", "Armed conflict",
     "Fighting over government or territory in which a state is one side and at least 25 people die in battle in a year.",
     "UCDP/PRIO Armed Conflict Dataset v26.1", ""),
    ("Minor conflict", "Armed conflict",
     "A conflict year with 25 to 999 battle-related deaths.", "UCDP intensity level 1", ""),
    ("War", "Armed conflict",
     "A conflict year with at least 1,000 battle-related deaths.", "UCDP intensity level 2",
     "On the World map, war countries have denser stripes."),
    ("Battle-related deaths", "Armed conflict",
     "Deaths directly caused by the fighting, civilians caught in it included.", "UCDP",
     "One-sided violence against civilians and conflicts between non-state groups are separate UCDP datasets and "
     "are not counted here."),
    ("Conflict onset", "Armed conflict",
     "A year with an active armed conflict in a country after two years without one.",
     "Project definition (notebook 06)", "The main finding (the regression of notebook 08) looks at democracy around these onsets."),
    ("Interstate conflict", "Armed conflict", "Armed conflict between two or more states.", "UCDP type 2", ""),
    ("Intrastate conflict", "Armed conflict",
     "A government against one or more armed groups inside the country, without foreign troops.", "UCDP type 3", ""),
    ("Internationalised intrastate conflict", "Armed conflict",
     "An intrastate conflict in which other states send troops to one or both sides.", "UCDP type 4", ""),
    ("Extrasystemic conflict", "Armed conflict",
     "A state fighting a non-state group outside its own territory, mostly colonial wars of the 1950s and 1960s.",
     "UCDP type 1", ""),
    ("Incompatibility", "Armed conflict",
     "What a conflict is about: control of the government, or a territory.", "UCDP",
     "Government: the type of political system or who governs. Territory: secession or autonomy of a region."),

    # ---------------------------------------------------------------- arms transfers
    ("Major conventional arms", "Arms transfers",
     "What SIPRI records: aircraft, armoured vehicles, artillery, air defence, missiles, ships and similar systems.",
     "SIPRI Arms Transfers Database", "Small arms, ammunition and most services are not included."),
    ("TIV (trend-indicator value)", "Arms transfers",
     "SIPRI's unit for the volume of arms transferred, in millions. It measures military capability, not money.",
     "SIPRI", "It is based on the known production cost of a core set of weapons. Use it to compare volumes and "
     "trends, not prices."),
    ("Arms imports", "Arms transfers",
     "The TIV a country received in a year. Years without a recorded delivery count as 0.", "SIPRI, our panel",
     "Deliveries are counted in the year they arrive."),
    ("Supplier / recipient", "Arms transfers",
     "The country that delivers / receives the weapons (rarely an organisation or armed group).", "SIPRI", ""),
    ("Arms build-up", "Arms transfers",
     "Major arms received over the previous 10 years (sum of TIV), so one big delivery does not dominate a year.",
     "Project definition (World map)", ""),
    ("Main supplier", "Arms transfers",
     "The supplier that delivered the most TIV to a country over the last 5 years.", "Project definition", ""),
    ("Arms before onset (arms_z)", "Arms transfers",
     "Mean arms imports in the 5 years before a conflict onset, standardised (mean 0, standard deviation 1).",
     "Project definition (notebook 08)",
     "It enters the main regression as one continuous number for every onset."),
    ("Supplier democracy", "Arms transfers",
     "How democratic a country's arms suppliers were in a year, weighted by TIV: 0 = autocracies, 1 = democracies.",
     "Project definition (notebook 08)",
     "Share from democracies = the share of TIV from suppliers that were electoral or liberal democracies."),

    # ---------------------------------------------------------------- methods
    ("Main finding regression (A1)", "Methods",
     "How the democracy index changes in the 10 years after a conflict onset, and how that change differs with "
     "the arms imported before.", "Notebook 08",
     "For k = 1 to 10: y_k = democracy(t+k) − democracy(t−1), regressed on onset, onset × arms_z and arms_z with "
     "country and year fixed effects; standard errors clustered by country. b1 (onset) = the change after an onset at "
     "average arms imports; b2 (onset:arms_z) = the difference per standard deviation more arms imports."),
    ("Event study", "Methods",
     "Follows each country from 10 years before to 10 years after a conflict onset, compared with itself.",
     "Notebook 08", "The years before should show no change if democracy was not already moving."),
    ("Fixed effects", "Methods",
     "Country fixed effects compare a country only with itself; year fixed effects remove what hit the whole world "
     "in the same year.", "Notebook 08", "For example the end of the Cold War."),
    ("95% confidence interval", "Methods",
     "The range of plausible values for a result. If it crosses zero, the data show no clear effect.", "Statistics", ""),
    ("Correlation vs causation", "Methods",
     "All results in this app are associations: they cannot show what causes what.", "Project caveat",
     "Democracy, conflict and arms imports influence each other."),
    ("Country-year panel", "Methods",
     "One row per country and year, 1950 to 2025, joining V-Dem, UCDP and SIPRI on one country code.",
     "Notebook 05", "V-Dem decides which country exists in which year."),
    ("Placeholder numbers", "Methods",
     "Preview numbers on the Findings page for the parts of notebook 08 that are not finished yet.", "Project",
     "A warning names those parts; the page switches to the real results automatically."),

    # ---------------------------------------------------------------- map and data
    ("Equal Earth projection", "Map and data",
     "The world map projection used here. It shows every country's area in true proportion.",
     "Šavrič, Patterson & Jenny (2018)", "Unlike the Mercator map, Africa and South America are not shrunk next to Europe."),
    ("Historical states", "Map and data",
     "States that no longer exist are drawn at today's borders, under a successor's code.", "V-Dem codes",
     "Soviet Union at Russia, Czechoslovakia at Czechia, Yugoslavia at Serbia, East Germany at Germany, South Yemen "
     "at Yemen, South Vietnam at Vietnam."),
    ("Cold War / since 1992", "Map and data",
     "The two periods offered in the app: 1950 to 1991 and 1992 to 2025.", "Project convention", ""),
]

# FAQ themes: label, icon, one-line description
THEMES = {
    "data": ("About the data", ":material/database:", "Where the numbers come from and how they are counted."),
    "map": ("Reading the map", ":material/map:", "Colours, stripes, borders and the projection."),
    "use": ("Using the site", ":material/touch_app:", "Comparing countries and getting at the numbers."),
    "limits": ("What results mean", ":material/balance:", "The three answers, how to read them, and what they cannot tell."),
}

# Pages the FAQ can point to (paths as registered in native_app.py)
PAGES = {
    "world_map": ("native_pages/world_map.py", "World map", ":material/public:"),
    "findings": ("native_pages/findings.py", "Findings", ":material/insights:"),
    "compare": ("native_pages/compare.py", "Countries & compare", ":material/compare_arrows:"),
    "about": ("native_pages/about.py", "How the numbers are built", ":material/info:"),
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
    ("map", "Why is a country dark grey or a dot?",
     "Dark grey means V-Dem has no data for that country in that year.",
     ["For example, years before independence.",
      "Small states too small to see on the map are drawn as dots."],
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
     "Open Countries & compare and pick countries in its sidebar.",
     ["Or choose a group, such as the European Union or the G7, or use the search box on any page.",
      "Clicking a country on a map opens its card, with a button to compare it.",
      "The year slider and Play at the bottom move all charts together."],
     ["compare"], []),
    ("use", "Can I see the exact numbers?",
     "Yes: most charts have a 'Show the numbers' table.",
     ["Every table can be searched and downloaded from its toolbar."],
     ["findings", "compare"], []),

    # ---------------------------------------------------------------- what results mean
    ("limits", "What does the Findings page show?",
     "Three answers, from 281 conflict onsets in notebook 08.",
     ["**1.** Democracy falls slowly behind after a conflict starts: about −0.02 after 6 to 9 years (event study).",
      "**2.** Arms imports before the conflict make no clear difference (regression A1).",
      "**3.** Neither does whether the arms came from democracies or autocracies (regression C3)."],
     ["findings"], ["Event study", "Main finding regression (A1)", "Supplier democracy"]),
    ("limits", "What does 'not clearly different from zero' mean?",
     "The 95% interval includes zero, so the data cannot tell the effect apart from no effect.",
     ["The interval is the range of values that fit the data.",
      "A result is clear when the whole interval lies above or below zero, as in the event study 6 to 9 years after onset."],
     ["findings"], ["95% confidence interval"]),
    ("limits", "Why compare with countries without a conflict?",
     "Because democracy rose almost everywhere after 1950.",
     ["A simple before-and-after comparison mixes the conflict with that worldwide trend.",
      "Control countries and year fixed effects take the trend out.",
      "That is why democracy looks higher after an onset in the raw averages, but lower in the event study."],
     ["findings"], ["Fixed effects", "Event study"]),
    ("limits", "Why measure arms imports in standard deviations?",
     "So one number covers every country, without choosing a border between groups.",
     ["Imports are averaged over the 5 years before onset, on a log scale, then standardised.",
      "One standard deviation more is a country that imported clearly more than the average."],
     ["findings"], ["Arms before onset (arms_z)"]),
    ("limits", "How do I read the event-study chart?",
     "Each dot is how far democracy in onset countries is from the controls, that many years from the onset.",
     ["Left of 'Conflict starts' it should be near zero (no pre-trend), and it is.",
      "Right of it, the line drifts below zero; from year 6 the band no longer reaches zero."],
     ["findings"], ["Event study"]),
    ("limits", "Do arms imports cause democracy to decline?",
     "The site cannot tell: it shows what happened at the same time.",
     ["Democracy, armed conflict and arms imports influence each other.",
      "For example, a government at war buys weapons and also restricts freedoms.",
      "So any pattern is an association, not proof of a cause."],
     ["findings"], ["Correlation vs causation"]),
    ("limits", "Are the results on the Findings page final?",
     "Yes for the required parts of notebook 08: the main finding and event study (Part A) and who supplied the arms (Part C).",
     ["The optional splits by kind of conflict (Part B) and what predicts a conflict (Part D) were not done.",
      "If a result file is missing, the page shows placeholder numbers instead and marks them with a warning."],
     ["findings"], ["Placeholder numbers"]),
]

# ------------------------------------------------------------------ tabs and links between them
T_ABOUT = ":material/info: How the numbers are built"
T_GLOSS = ":material/menu_book: Glossary"
T_FAQ = ":material/help: FAQ"
TABS = [T_ABOUT, T_GLOSS, T_FAQ]
ss = st.session_state
if ss.get("about_tab") not in TABS:
    ss.pop("about_tab", None)
_go = ss.pop("about_go", None)  # one-shot hand-over from another page: open this tab
if _go in TABS:
    ss["about_tab"] = _go

BY_NAME = {t[0]: t for t in TERMS}
CATEGORIES = {"Political regimes": ":material/how_to_vote:", "Armed conflict": ":material/crisis_alert:",
              "Arms transfers": ":material/flight:", "Methods": ":material/functions:", "Map and data": ":material/map:"}


def look_up(term):
    """A term button in the FAQ: search the glossary for it and open the glossary tab."""
    ss["g_query"] = term
    ss["about_tab"] = T_GLOSS


def open_tab(tab):
    ss["about_tab"] = tab


def term_list(items, key):
    """Terms as a calm list in one reading column: the name in bold, a one- or two-sentence definition in normal
    text, the source as a caption, and longer explanations folded into "More detail"."""
    for k, (term, _, definition, source, more) in enumerate(items):
        if k:
            st.space("small")
        long_ = len(more) > 150  # a short extra sentence goes into the caption line; only long ones fold away
        st.markdown(f"**{term}**  \n{definition}")
        st.caption(" · ".join(x for x in (more if more and not long_ else "", source) if x))
        if long_:
            with st.expander("More detail", key=f"{key}_{k}", type="compact"):
                st.markdown(more)


def faq_text(item):
    """Everything a FAQ entry says, lower-cased, for the search."""
    theme, question, short, bullets, _, terms = item
    return " ".join([THEMES[theme][0], question, short, *bullets, *terms]).lower()


def faq_item(item, key):
    """One question as an expander: the short answer first, then a few bullets and links to pages and terms."""
    theme, question, short, bullets, pages, terms = item
    with st.expander(question, key=f"{key}_x"):
        st.markdown(f"**{short}**")
        st.markdown("\n".join(f"- {b}" for b in bullets))
        if pages or terms:
            with st.container(horizontal=True, vertical_alignment="center", gap="small"):
                st.caption("See also", width="content")
                for p in pages:
                    path, label, icon = PAGES[p]
                    if p == "about":  # this page: open its first tab
                        st.button(label, icon=icon, type="tertiary", key=f"{key}_p{p}", on_click=open_tab, args=(T_ABOUT,))
                        continue
                    try:
                        st.page_link(path, label=label, icon=icon, width="content")
                    except StreamlitAPIException:  # page run on its own, outside native_app.py's navigation
                        st.caption(f"{icon} {label} page", width="content")
                for j, term in enumerate(terms):
                    st.button(term, icon=":material/menu_book:", type="tertiary", key=f"{key}_t{j}",
                              on_click=look_up, args=(term,), help="Look this term up in the glossary")


def faq_list(items, key):
    for k, item in enumerate(items):
        faq_item(item, f"{key}_{k}")


panel = nd.load_panel()
LAST = int(panel["year"].max())
now = panel[panel["year"] == LAST]


@st.cache_data
def regime_counts(last):
    rows = []
    for code, name in enumerate(nd.REGIMES):
        rows.append(dict(Regime=name.capitalize(), n=int((now["regime_type"] == code).sum()), k=code))
    return rows


def regime_scale():
    """One stacked bar (Altair): countries per regime type in the latest year, in the map colours."""
    d = pd.DataFrame(regime_counts(LAST))
    d["x1"] = d["n"].cumsum()
    d["x0"] = d["x1"] - d["n"]
    d["mid"] = (d["x0"] + d["x1"]) / 2
    d["label"] = d["Regime"] + " · " + d["n"].astype(str)
    total = int(d["n"].sum())
    x = alt.X("x0:Q", scale=alt.Scale(domain=[0, total], nice=False), axis=None)
    colour = alt.Color("Regime:N", scale=alt.Scale(domain=[r.capitalize() for r in nd.REGIMES],
                                                   range=[nd.REGIME_COLOURS[r] for r in nd.REGIMES]), legend=None)
    bars = alt.Chart(d).mark_bar(height=28, cornerRadius=3, stroke="#111110", strokeWidth=2).encode(
        x, x2="x1:Q", color=colour,
        tooltip=[alt.Tooltip("Regime:N"), alt.Tooltip("n:Q", title=f"Countries in {LAST}")])
    text = alt.Chart(d).mark_text(color="#f0efec", fontSize=7.7, fontWeight=500).encode(
        alt.X("mid:Q", scale=alt.Scale(domain=[0, total], nice=False), axis=None), text="label:N")
    return (alt.layer(bars, text).properties(height=30)
            .configure_view(stroke=None).configure(background="transparent", font="IBM Plex Sans, sans-serif"))


# ------------------------------------------------------------------ page
st.markdown(":primary[:small[**ABOUT THE DATA**]]")
st.title("About the data", anchor=False)
st.markdown("Three public datasets, joined into one table of country-years from 1950 to 2025: how they are combined, "
            "what the words used in the app mean, and answers to common questions.")
t_about, t_gloss, t_faq = st.tabs(TABS, key="about_tab", on_change="rerun")

# ---------------------------------------------------------------- how the numbers are built (as on the HTML page)
with t_about:
    # two columns of cards as the HTML page (.notes grid): status and main finding left, pipeline right
    c_left, c_right = st.columns(2, gap="medium")
    with c_left:
        with st.container(border=True):
            st.subheader("Where the numbers come from", anchor=False)
            st.markdown("Every figure comes from our notebooks 01 to 08, run on the original V-Dem, UCDP/PRIO and SIPRI "
                        "downloads. The tables are in `data/clean/`.")
            if nr.any_placeholder():
                st.caption(":material/science: A regression result file is missing, so the Findings page shows placeholder "
                           "numbers for it and says so.")
        with st.container(border=True):
            st.subheader("Main finding", anchor=False)
            st.markdown(
                "- A regression on all 281 conflict onsets (notebook 08, model A1), 1 to 10 years after each onset.\n"
                "- Onset: a conflict year after two years without conflict.\n"
                "- Arms imports of the 5 years before enter as one standardised number.\n"
                "- Associations, not causes.")
            with st.expander("Model details", icon=":material/functions:"):
                st.markdown(
                    "- Change: **y_k** = democracy(t+k) − democracy(t−1), k = 1 to 10.\n"
                    "- **arms_z**: mean arms imports (log TIV) in the 5 years before onset, standardised (mean 0, sd 1).\n"
                    "- Model: `y_k ~ onset + onset:arms_z + arms_z`, country and year fixed effects, standard errors "
                    "clustered by country.\n"
                    "- **b1** (onset): change at average arms imports. **b2** (onset:arms_z): difference per sd more arms.\n"
                    "- The Findings page also shows a stacked event study, 10 years before to 10 years after onset.")
            try:
                st.page_link("native_pages/findings.py", label="See the regression results", icon=":material/arrow_forward:")
            except StreamlitAPIException:  # page run on its own, outside native_app.py's navigation
                pass
    with c_right:
        with st.container(border=True):
            st.subheader("Pipeline", anchor=False)
            st.markdown(
                "- One country key (V-Dem code) for all three sources; 31 SIPRI names matched by hand.\n"
                "- UCDP conflicts with several locations: one row per country.\n"
                "- SIPRI deliveries summed per country and year; non-state recipients removed.\n"
                "- Years without a delivery count as 0, years without a UCDP conflict as no conflict.\n"
                "- Arms flows on the World map: only the largest deliveries of each year are drawn.")
    with st.container(border=True):
        st.subheader("Caveats", anchor=False)
        st.markdown(
            "- TIV measures military capability transferred, not price.\n"
            "- UCDP counts a conflict from 25 battle deaths a year.\n"
            "- V-Dem scores are expert ratings: small yearly changes mean little.\n"
            "- The map uses today's borders; some states appear under a successor's code, as in V-Dem (Russia for the "
            "Soviet Union before 1991, Serbia for Yugoslavia, Germany for West Germany before 1990).")
    st.subheader("Data sources", anchor=False)
    for col, (name, text, link) in zip(st.columns(3, border=True, gap="medium"), [
        ("UCDP/PRIO Armed Conflict v26.1", "Conflicts with at least 25 battle deaths in a year. Type and intensity per "
         "conflict-year.", "[ucdp.uu.se](https://ucdp.uu.se)"),
        ("V-Dem v16 (Core)", "Electoral democracy index from 0 to 1 and the four-category Regimes of the World "
         "classification.", "[v-dem.net](https://www.v-dem.net)"),
        ("SIPRI Arms Transfers", "Deliveries of major conventional arms in trend-indicator values (TIV), 1950 to 2025. "
         "TIV measures military capability, not price.", "[sipri.org](https://www.sipri.org/databases/armstransfers)"),
    ]):
        with col:
            st.markdown(f"**{name}**")
            st.markdown(text)
            st.caption(link)
    with st.container(horizontal=True, gap="small"):
        st.button("Glossary", icon=":material/menu_book:", on_click=open_tab, args=(T_GLOSS,))
        st.button("FAQ", icon=":material/help:", on_click=open_tab, args=(T_FAQ,))

# ---------------------------------------------------------------- glossary: one reading column, one category control
with t_gloss:
    text_col, _ = st.columns([3, 1])  # a comfortable line length, whitespace on the right
    with text_col:
        query = st.text_input("Search", placeholder="Search terms and questions, e.g. war, TIV, autocracy",
                              icon=":material/search:", label_visibility="collapsed", key="g_query", width=420)
        q = query.strip().lower()
        if q:
            hits = [t for t in TERMS if q in " ".join(t[0:1] + t[2:]).lower()]
            faq_hits = [f for f in FAQ if q in faq_text(f)]
            with st.container(horizontal=True, vertical_alignment="center"):
                st.caption(f"{len(hits)} terms and {len(faq_hits)} questions match “{query}”.", width="content")
                st.button("Clear search", icon=":material/close:", type="tertiary", on_click=look_up, args=("",))
            if not hits and not faq_hits:
                st.info("Nothing matches. Try a shorter word.", icon=":material/search_off:")
            if hits:
                st.space("small")
                term_list(hits, "gs")
            if faq_hits:
                st.space("medium")
                st.markdown("**Questions**")
                faq_list(faq_hits, "s")
        else:
            cat = st.pills("Category", list(CATEGORIES), default="Political regimes", required=True,
                                       key="g_cat", label_visibility="collapsed",
                                       format_func=lambda c: f"{CATEGORIES[c]} {c}")
            st.space("small")
            if cat == "Political regimes":  # the one picture: the four types in the map colours, with their counts
                st.altair_chart(regime_scale(), key="g_scale", width="stretch", alt=f"Countries per regime type in {LAST}")
                st.caption(f"Countries per regime type in {LAST}, from least to most democratic, in the colours of the World map.")
                st.space("small")
            term_list([t for t in TERMS if t[1] == cat], f"g_{cat}")

# ---------------------------------------------------------------- FAQ: one column of questions per theme
with t_faq:
    text_col, _ = st.columns([3, 1])
    with text_col:
        theme = st.pills(
            "Theme", ["all", *THEMES], default="all", required=True, key="g_faq_theme", label_visibility="collapsed",
            format_func=lambda k: "All" if k == "all" else f"{THEMES[k][1]} {THEMES[k][0]}")
        for k, (label, icon, blurb) in THEMES.items():
            if theme not in ("all", k):
                continue
            st.space("small")
            st.markdown(f"**{label}**  \n{blurb}")
            faq_list([f for f in FAQ if f[0] == k], f"f_{k}")
