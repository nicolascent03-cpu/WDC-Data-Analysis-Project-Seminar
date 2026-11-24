"""About the data: how the three sources are joined, what the main finding measures, and where to be careful."""

import streamlit as st

import native_results as nr

st.markdown(":primary[**About the data**]")
st.title("How the numbers are built", anchor=False)
st.markdown("Three public datasets, joined into one table of country-years from 1950 to 2025. Here is how they are "
            "combined, what the main finding measures, and where to be careful.")

left, right = st.columns(2, gap="medium")

with left:
    with st.container(border=True):
        st.subheader("Prototype status", anchor=False)
        st.markdown("This page is a working prototype of the Streamlit app. The figures come from a test run of the project "
                    "notebooks on the real downloads. Before quoting any number, check it against your own notebook results.")
        if nr.any_placeholder():
            st.caption(":material/science: The Findings page currently shows placeholder regression numbers.")

    with st.container(border=True):
        st.subheader("Main finding", anchor=False)
        st.markdown(
            "- **Onset:** a year with an active conflict after a year without one.\n"
            "- **Arms group:** mean imports in the five years before onset, split at the median of all onsets.\n"
            "- **Change:** democracy index minus its value in the year before onset, averaged per group and year.\n"
            "- The chart shows patterns. Conflict, arms imports and regime change influence each other, so it shows no causes.")
        st.markdown("The **Findings** page adds the regression results of notebook 08: models with country and year fixed "
                    "effects, and an event study of the democracy index from 10 years before to 10 years after a conflict "
                    "starts. Until the notebook is done, that page shows placeholder numbers and says so.")
        if st.button("See the regression results", icon=":material/arrow_forward:", type="tertiary"):
            st.switch_page("native_pages/findings.py")

with right:
    with st.container(border=True):
        st.subheader("Pipeline", anchor=False)
        st.markdown(
            "- One country key (V-Dem country code) for all three sources; UCDP location codes match V-Dem COW codes, "
            "31 SIPRI names are matched by hand.\n"
            "- UCDP rows with several locations are split into one row per country; conflict-years are merged into "
            "periods for the bars.\n"
            "- SIPRI deliveries without a delivery year and non-state recipients are removed; imports are summed per "
            "country and year.\n"
            "- V-Dem defines which country exists in which year. Years without a SIPRI delivery count as 0, years without "
            "a UCDP conflict as no conflict.\n"
            "- The world map also has an **Arms flows** mode: SIPRI deliveries drawn from supplier to recipient for the "
            "chosen year. Only the largest flows of each year are drawn, so smaller deliveries are left out.")

    with st.container(border=True):
        st.subheader("Data sources", anchor=False)
        st.markdown(
            "- **UCDP/PRIO Armed Conflict Dataset**, version 26.1 (Uppsala Conflict Data Program): armed conflicts with "
            "at least 25 battle deaths per year. [ucdp.uu.se](https://ucdp.uu.se)\n"
            "- **V-Dem Country-Year Core**, version 16 (Varieties of Democracy): regime type and the electoral democracy "
            "index. [v-dem.net](https://www.v-dem.net)\n"
            "- **SIPRI Arms Transfers Database**, trade register 1950 to 2025: deliveries of major conventional arms in "
            "trend-indicator values (TIV). [sipri.org](https://www.sipri.org/databases/armstransfers)")

with st.container(border=True):
    st.subheader("Caveats", anchor=False)
    st.markdown(
        "- SIPRI TIV measures the military capability transferred. It is not a price.\n"
        "- UCDP counts a conflict only from 25 battle deaths per year.\n"
        "- V-Dem scores are expert assessments; small changes from one year to the next carry little meaning.\n"
        "- The map uses today's borders. Historical states such as East Germany or South Yemen are only in the search.\n"
        "- Some states appear under a successor's code, as in V-Dem: Russia stands for the Soviet Union before 1991, "
        "Czechia for Czechoslovakia, Serbia for Yugoslavia, Germany for West Germany before 1990, Yemen for North Yemen "
        "before 1990 and Vietnam for North Vietnam before 1976. Country groups such as the Warsaw Pact or the UN Security "
        "Council use these codes.")
