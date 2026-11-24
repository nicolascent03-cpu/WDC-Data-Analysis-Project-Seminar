"""Findings: the regression results of notebook 08, or placeholder numbers (data/demo/) until they exist."""

import re

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import native_results as nr

CHART_CFG = {"displayModeBar": False}

es, es_src = nr.load("reg_eventstudy")
res, res_src = nr.load("reg_results")
sup, sup_src = nr.load("reg_suppliers")


def heading(text, source):
    """Card heading, with a badge when the numbers are placeholders."""
    with st.container(horizontal=True, vertical_alignment="center"):
        st.subheader(text, anchor=False, width="content")
        if source == "demo":
            st.badge("Placeholder", icon=":material/science:", color="orange")


# ------------------------------------------------------------------ header
st.markdown(":primary[**Findings**]")
st.title("What the regressions show", anchor=False)
st.markdown("Does democracy change after an armed conflict starts, and is the change different for countries that import "
            "many weapons, or that buy them from democracies?")
st.caption("The models show associations, not causes: conflict, arms imports and regime change all influence each other.")
if nr.any_placeholder():
    st.warning(nr.PLACEHOLDER_TEXT, title="Preview with placeholder numbers", icon=":material/science:")


# ------------------------------------------------------------------ (a) event study
def es_chart(groups):
    fig = go.Figure()
    lo, hi = 0.0, 0.0
    for grp in groups:
        r = nr.event_rows(es, grp)
        if r.empty:
            continue
        lo, hi = min(lo, r["ci_low"].min()), max(hi, r["ci_high"].max())
        hover = [f"<b>t = {nr.sgn(t, 0)}</b><br>{nr.ES_NAME[grp]}: " + ("0 (reference year)" if ref else
                 f"{nr.sgn(c)}<br>95% CI {nr.sgn(a)} to {nr.sgn(b)}" + ("" if pd.isna(n) else f"<br>n = {int(n):,}"))
                 for t, c, a, b, n, ref in r[["t", "coef", "ci_low", "ci_high", "n", "ref"]].itertuples(index=False)]
        band, line = nr.band_traces(r["t"], r["ci_low"], r["ci_high"], r["coef"], nr.ES_COL[grp], nr.ES_NAME[grp], hover,
                                    opacity=.16 if len(groups) == 1 else .12)
        line.marker.symbol = ["circle-open" if ref else "circle" for ref in r["ref"]]
        line.showlegend = True
        fig.add_traces([band, line])
    if not fig.data:
        return None
    pad = (hi - lo) * .12
    fig.add_vrect(x0=-10.5, x1=0, fillcolor="rgba(240,239,236,0.04)", line_width=0, layer="below")
    fig.add_vline(x=0, line=dict(color=nr.INK2, dash="dash", width=1.2))
    fig.add_annotation(x=0, y=hi + pad, text="<b>Conflict starts</b>", showarrow=False, xanchor="left", xshift=6,
                       font=dict(color=nr.INK, size=12))
    fig.add_annotation(x=-10.4, y=hi + pad, text="Before: should be near zero", showarrow=False, xanchor="left",
                       font=dict(color=nr.MUTED, size=12))
    nr.layout(fig, 380, hovermode="x unified", showlegend=len(groups) > 1,
              legend=dict(orientation="h", x=1, xanchor="right", y=1.12, font=dict(color=nr.INK2)))
    fig.update_xaxes(range=[-10.6, 10.6], dtick=1, tickformat="+d", showgrid=False,
                     title="Years relative to conflict onset (t = −1, the year before, is the reference: 0 by definition)")
    fig.update_yaxes(title="Change in democracy index", tickformat="+.2f", range=[lo - pad, hi + pad * 2.2])
    return fig


def es_table():
    rows = {}
    for grp in nr.ES_NAME:
        for t, c, a, b, n, ref in nr.event_rows(es, grp)[["t", "coef", "ci_low", "ci_high", "n", "ref"]].itertuples(index=False):
            row = rows.setdefault(int(t), {"t": nr.sgn(t, 0)})
            row[nr.ES_NAME[grp]] = "0 (ref.)" if ref else nr.sgn(c)
            row[f"{nr.ES_NAME[grp]}: 95% CI"] = "–" if ref else f"{nr.sgn(a)} to {nr.sgn(b)}"
            row[f"{nr.ES_NAME[grp]}: n"] = "–" if pd.isna(n) else f"{int(n):,}"
    return pd.DataFrame([rows[t] for t in sorted(rows)])


with st.container(border=True):
    heading("Democracy before and after a conflict starts", es_src)
    st.caption("Event study: change in the democracy index (0 to 1) compared with the year before a conflict starts, with "
               "country and year fixed effects. Below the dashed line = less democratic than just before the conflict. "
               "High vs low importers: arms imports in the 5 years before onset, split at the median. "
               "Band: 95% confidence interval.")
    if es is None or es.empty:
        st.info("Not available yet: the event study of notebook 08 has not been run.", icon=":material/hourglass_empty:")
    else:
        mode = st.segmented_control("Event study shows", ["All onsets", "High vs low importers"], default="All onsets",
                                    key="fd_es_mode", label_visibility="collapsed") or "All onsets"
        groups = ["all"] if mode == "All onsets" else ["high importer", "low importer"]
        fig = es_chart(groups)
        if fig is None:
            st.info(f"No event-study results for {mode.lower()} yet.", icon=":material/hourglass_empty:")
        else:
            st.plotly_chart(fig, config=CHART_CFG, key="fd_es")
        with st.expander("Show the numbers"):
            st.dataframe(es_table(), hide_index=True)


# ------------------------------------------------------------------ (b) A1 models over k
def k_chart(pts, colour, what, yrange):
    hover = [f"<b>{k} year{'s' if k > 1 else ''} after onset</b> ({m})<br>{what}: {nr.sgn(c)}<br>95% CI {nr.sgn(a)} to "
             f"{nr.sgn(b)}<br>n = {n:,} country-years, {nc:,} countries"
             for k, m, c, a, b, n, nc in pts[["k", "model", "coef", "ci_low", "ci_high", "n_obs", "n_countries"]].itertuples(index=False)]
    fig = go.Figure(go.Scatter(
        x=pts["k"], y=pts["coef"], mode="lines+markers", line=dict(color=nr.rgba(colour, .45), width=1.2),
        marker=dict(size=9, color=colour, line=dict(width=1.5, color="#1a1a19")), text=hover, hoverinfo="text",
        error_y=dict(type="data", symmetric=False, array=pts["ci_high"] - pts["coef"], arrayminus=pts["coef"] - pts["ci_low"],
                     color=colour, thickness=2, width=6)))
    nr.layout(fig, 260, margin=dict(l=8, r=8, t=8, b=8))
    fig.update_xaxes(title="Years after onset (k)", dtick=1, range=[0.4, max(10, int(pts["k"].max())) + 0.6], showgrid=False)
    fig.update_yaxes(tickformat="+.2f", range=yrange, zeroline=True, zerolinecolor=nr.INK2, title="Change in democracy index")
    return fig


with st.container(border=True):
    heading("How the effect builds up", res_src)
    st.caption("One regression for each horizon k: the change in the democracy index from the year before onset to k years "
               "after it, with country and year fixed effects. Bars: 95% confidence intervals; an interval that crosses "
               "the zero line means no clear change.")
    p1 = nr.a1_points(res, "onset") if res is not None else pd.DataFrame()
    p2 = nr.a1_points(res, "onset:arms_z") if res is not None else pd.DataFrame()
    if p1.empty and p2.empty:
        st.info("Not available yet: the A1 models of notebook 08 have not been run.", icon=":material/hourglass_empty:")
    else:
        both = pd.concat([p1, p2])
        lo, hi = min(0, both["ci_low"].min()), max(0, both["ci_high"].max())
        pad = (hi - lo) * .08
        yrange = [lo - pad, hi + pad]  # one scale for both charts, so they can be compared
        c1, c2 = st.columns(2, gap="medium")
        for col, pts, colour, title, term, desc in [
            (c1, p1, nr.ACCENT, "Average change after an onset", "onset",
             "countries with a conflict onset compared with those without"),
            (c2, p2, nr.HI, "Extra change per standard deviation of arms imports", "onset:arms_z",
             "how much more (or less) for a country importing one sd more arms before the onset"),
        ]:
            with col:
                st.markdown(f"**{title}**")
                st.caption(f"Term `{term}`: {desc}")
                if pts.empty:
                    st.info("No results for this term yet.", icon=":material/hourglass_empty:")
                else:
                    st.plotly_chart(k_chart(pts, colour, title, yrange), config=CHART_CFG, key=f"fd_k_{term}")


# ------------------------------------------------------------------ (c) forest plot and (d) suppliers
def model_note(m):
    k = re.search(r"_k(\d+)$", m)
    return m + (f" · after {k.group(1)} years" if k else " · linear probability" if re.search("lpm", m, re.I) else "")


def forest(rows):
    rows = rows.iloc[::-1]  # first row on top
    sig = (rows["ci_low"] > 0) | (rows["ci_high"] < 0)
    cols = [nr.ACCENT if s else nr.INK2 for s in sig]
    labels = [f"<b>{nr.TERM_LAB.get(t, t)}</b><br><span style='color:{nr.MUTED}'>{model_note(m)}</span>"
              for t, m in zip(rows["term"], rows["model"])]
    hover = [f"<b>{nr.TERM_LAB.get(t, t)}</b><br>{m} · {t}<br>Coefficient {nr.sgn(c)}"
             + ("" if pd.isna(se) else f" (se {se:.3f})") + f"<br>95% CI {nr.sgn(a)} to {nr.sgn(b)}"
             + f"<br>n = {n:,} country-years, {nc:,} countries"
             for m, t, c, se, a, b, n, nc in rows[["model", "term", "coef", "se", "ci_low", "ci_high", "n_obs", "n_countries"]].itertuples(index=False)]
    fig = go.Figure(go.Scatter(
        x=rows["coef"], y=labels, mode="markers", marker=dict(size=10, color=cols, line=dict(width=1.5, color="#1a1a19")),
        error_x=dict(type="data", symmetric=False, array=rows["ci_high"] - rows["coef"],
                     arrayminus=rows["coef"] - rows["ci_low"], color=nr.INK2, thickness=2, width=0),
        text=hover, hoverinfo="text"))
    width = max(max(len(nr.TERM_LAB.get(t, t)) for t in rows["term"]), max(len(model_note(m)) for m in rows["model"]))
    nr.layout(fig, 40 + 46 * len(rows), margin=dict(l=int(7.4 * width) + 16, r=16, t=6, b=8))
    fig.update_xaxes(zeroline=True, zerolinecolor=nr.INK2, zerolinewidth=1.2, tickformat="+.2f")
    fig.update_yaxes(automargin=False, showgrid=False, tickfont=dict(color=nr.INK, size=12), ticklabelstandoff=10)
    return fig


def sup_chart():
    s = nr.supplier_series(nr._mtime("reg_suppliers"))
    fig = go.Figure()
    for key, n_key, name, colour, width, op, rank in [("dem", "nd", "Democratic recipients", nr.REG_COLS[3], 1.5, .75, 2),
                                                      ("aut", "na", "Autocratic recipients", nr.REG_COLS[0], 1.5, .75, 3),
                                                      ("all", "n", "All recipients", nr.INK, 2.6, 1, 1)]:
        hover = [f"{name}: {'–' if pd.isna(v) else f'{v:.2f}'} ({0 if pd.isna(n) else int(n)} countries)"
                 for v, n in zip(s[key], s[n_key])]
        fig.add_trace(go.Scatter(x=s["year"], y=s[key], name=name, mode="lines", opacity=op, text=hover,
                                 hovertemplate="%{text}<extra></extra>", line=dict(color=colour, width=width),
                                 legendrank=rank))
    fig.add_vline(x=1991, line=dict(color=nr.MUTED, dash="dash", width=1.2))
    fig.add_annotation(x=1991, y=1.0, text="1991: end of the Cold War", showarrow=False, xanchor="left", xshift=5,
                       yanchor="bottom", font=dict(color=nr.MUTED, size=12))
    nr.layout(fig, 520, hovermode="x unified", showlegend=True,
              legend=dict(orientation="h", x=0, y=-0.08, yanchor="top", font=dict(color=nr.INK2)),
              margin=dict(l=8, r=8, t=28, b=8))
    fig.update_xaxes(range=[1949.5, 2025.5], dtick=10, showgrid=False)
    fig.update_yaxes(range=[0, 1.06], tickvals=[0, .25, .5, .75, 1], title="Mean supplier democracy")
    return fig


left, right = st.columns(2, gap="medium")
with left.container(border=True, height="stretch"):
    heading("Checks and splits", res_src)
    st.caption("Dot: estimate; line: 95% confidence interval. Orange: the interval does not cross zero. "
               "Each group has its own scale.")
    allr = res[res["coef"].notna() & res["model"].notna()] if res is not None else pd.DataFrame()
    if allr.empty:
        st.info("Not available yet: the models of notebook 08 have not been run.", icon=":material/hourglass_empty:")
    else:
        shown = False
        for pattern, title, desc in nr.FOREST:
            rows = allr[allr["model"].str.contains(pattern)]
            if rows.empty:
                continue
            shown = True
            st.markdown(f"**{title}**")
            st.caption(desc)
            st.plotly_chart(forest(rows), config=CHART_CFG, key=f"fd_forest_{title}")
        if not shown:
            st.info("No results for the B, C or D models yet.", icon=":material/hourglass_empty:")
        known = allr["model"].str.match(r"^A1_k\d+$")
        for pattern, _, _ in nr.FOREST:
            known |= allr["model"].str.contains(pattern)
        other = allr[~known]
        if not other.empty:
            st.markdown("**Other models**")
            st.dataframe(other[["model", "term", "coef", "ci_low", "ci_high", "n_obs", "n_countries"]], hide_index=True,
                         column_config={"model": "Model", "term": "Term",
                                        "coef": st.column_config.NumberColumn("Coef.", format="%+.3f"),
                                        "ci_low": st.column_config.NumberColumn("95% CI low", format="%+.3f"),
                                        "ci_high": st.column_config.NumberColumn("95% CI high", format="%+.3f"),
                                        "n_obs": st.column_config.NumberColumn("n", format="%d"),
                                        "n_countries": st.column_config.NumberColumn("Countries", format="%d")})

with right.container(border=True, height="stretch"):
    heading("Who supplied the arms over time", sup_src)
    st.caption("Democracy of the suppliers (0 = all arms from autocracies, 1 = from full democracies), weighted by TIV, "
               "averaged over all countries that imported arms that year.")
    if sup is None or sup.empty:
        st.info("Not available yet: the supplier table of notebook 08 does not exist.", icon=":material/hourglass_empty:")
    else:
        st.plotly_chart(sup_chart(), config=CHART_CFG, key="fd_sup")


# ------------------------------------------------------------------ simple comparison of the first prototype
def finding_chart(F):
    fig = go.Figure()
    for g, name, colour in [("low", "Low arms importers", nr.LO), ("high", "High arms importers", nr.HI)]:
        d = F["groups"][g]
        hover = [f"{name}: {nr.sgn(m)} (95% CI {nr.sgn(a)} to {nr.sgn(b)}, n = {c})"
                 for m, a, b, c in zip(d["m"], d["lo"], d["hi"], d["cnt"])]
        band, line = nr.band_traces(d["rel"], d["lo"], d["hi"], d["m"], colour, f"{name} ({d['n']} onsets)", hover, .13)
        line.mode, line.showlegend = "lines", True
        line.hovertemplate, line.hoverinfo = "%{text}<extra></extra>", None
        fig.add_traces([band, line])
    fig.add_vline(x=0, line=dict(color=nr.INK2, dash="dash", width=1.2))
    fig.add_annotation(x=0, y=1, yref="paper", text="Conflict starts", showarrow=False, xanchor="left", xshift=6,
                       font=dict(color=nr.INK2, size=12))
    nr.layout(fig, 360, hovermode="x unified", showlegend=True,
              legend=dict(orientation="h", x=0, y=-0.2, yanchor="top", font=dict(color=nr.INK2)))
    fig.update_xaxes(title="Years relative to conflict onset", dtick=5, tickformat="+d", showgrid=False, range=[-10.5, 10.5])
    fig.update_yaxes(tickformat="+.2f", zeroline=True, zerolinecolor=nr.INK2)
    return fig


with st.expander("Simple comparison: the main finding of the first prototype", icon=":material/show_chart:"):
    F = nr.load_finding()
    hi_g, lo_g = F["groups"]["high"], F["groups"]["low"]
    k5h, k5l = hi_g["rel"].index(5), lo_g["rel"].index(5)
    overlap = hi_g["lo"][k5h] <= lo_g["hi"][k5l] and lo_g["lo"][k5l] <= hi_g["hi"][k5h]
    txt, chart = st.columns([1, 1.6], gap="medium")
    with txt:
        st.markdown("**Democracy around the start of a conflict**")
        st.caption("Change in the democracy index compared with the year before a conflict starts (onset = first conflict "
                   "year after a year of peace). High vs. low arms importers: average imports in the 5 years before onset, "
                   "split at the median. Shaded: 95% confidence band. Below the zero line = less democratic than just "
                   "before the conflict began.")
        st.markdown(f"Five years after onset the index changed by **{nr.sgn(hi_g['m'][k5h])}** for high importers and "
                    f"**{nr.sgn(lo_g['m'][k5l])}** for low importers. "
                    + ("The 95% bands overlap at +5 years, so this data shows no clear difference between the groups."
                       if overlap else "The 95% bands do not overlap at +5 years.")
                    + f" Median pre-onset imports: {F['median_pre']:.1f} TIV (millions) per year. Figures are preliminary.")
    chart.plotly_chart(finding_chart(F), config=CHART_CFG, key="fd_simple")
    table = pd.DataFrame({
        "Year": [nr.sgn(r, 0) for r in hi_g["rel"]],
        "High": [nr.sgn(v) for v in hi_g["m"]],
        "High: 95% CI": [f"{nr.sgn(a)} to {nr.sgn(b)}" for a, b in zip(hi_g["lo"], hi_g["hi"])],
        "Low": [nr.sgn(lo_g["m"][lo_g["rel"].index(r)]) for r in hi_g["rel"]],
        "Low: 95% CI": [f"{nr.sgn(lo_g['lo'][lo_g['rel'].index(r)])} to {nr.sgn(lo_g['hi'][lo_g['rel'].index(r)])}"
                        for r in hi_g["rel"]],
    })
    st.dataframe(table, hide_index=True, height=250)


# ------------------------------------------------------------------ limits
with st.container(border=True):
    st.subheader("Limits", anchor=False)
    st.markdown(
        "- **Associations, not causes.** Conflict, arms imports and regime change influence each other, so no model here "
        "shows what caused what.\n"
        "- **TIV is not money.** SIPRI trend-indicator values measure military capability transferred, not the price paid.\n"
        "- **Small groups.** Some splits rest on few conflict onsets; wide intervals there mean the data cannot tell.\n"
        "- **Historical states.** The Soviet Union, Yugoslavia and others are counted under a successor's code, as in V-Dem.\n"
        "- **Preliminary.** The models of notebook 08 are still being checked; numbers can change.")
