"""Findings: the regression results of notebook 08, or placeholder numbers (data/demo/) until they exist.

Same content as the Findings page of app/site/adc.html: (a) the event study, (b) the A1 models over k, (c) the forest
plots of the B, C and D models, (d) the democracy of the arms suppliers over time, and the limits. All charts are Altair
(Vega-Lite): hover a year, a horizon or a row for its numbers; every chart has Streamlit's full-screen button.
"""

import re

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

import native_results as nr

FONT, MONO = "IBM Plex Sans, sans-serif", "IBM Plex Mono, ui-monospace, monospace"
SURFACE = "#1a1a19"  # card background: the open reference point and the dot outlines

es, es_src = nr.load("reg_eventstudy")
res, res_src = nr.load("reg_results")
sup, sup_src = nr.load("reg_suppliers")


# ------------------------------------------------------------------ helpers
def heading(text, source):
    """Card heading, with a badge when the numbers are placeholders."""
    with st.container(horizontal=True, vertical_alignment="center"):
        st.subheader(text, anchor=False, width="content")
        if source == "demo":
            st.badge("Placeholder", icon=":material/science:", color="orange")


def legend_line(items):
    """A one-line colour legend in Markdown, as the legends of the HTML version: (name, colour, symbol) items."""
    return ":small[" + " ".join(f':color[{sym}]{{foreground="{c}"}} {n.replace(" ", chr(160))}'
                                     for n, c, sym in items) + "]"


def nice(lo, hi, n):
    """niceTicks of app/site/adc.html: a round step for [lo, hi] with about n intervals, 0 always among the ticks."""
    if not hi > lo:
        m = abs(lo) or .01
        lo, hi = lo - m, hi + m
    raw = (hi - lo) / n
    p = 10 ** np.floor(np.log10(raw))
    step = next((m * p for m in (1, 2, 2.5, 5) if m * p >= raw), 10 * p)
    a, b = np.floor(lo / step + 1e-9) * step, np.ceil(hi / step - 1e-9) * step
    ticks = [round(v, 10) for v in np.arange(a, b + step / 2, step)]
    d = max(0, int(-np.floor(np.log10(step) + 1e-9))) + (1 if round(step / p) == 2.5 else 0)
    return a, b, ticks, d


def signed(d):
    """Vega label expression: +0.02, 0.00, −0.02 (true minus sign), as sgn() of the HTML version."""
    return (f"datum.value > 1e-12 ? '+' + format(datum.value, '.{d}f') : datum.value < -1e-12 ? "
            f"'−' + format(-datum.value, '.{d}f') : format(0, '.{d}f')")


def finish(chart, height):
    """Transparent, IBM Plex, no frame: the look of the Altair charts of the other pages."""
    return (chart.properties(height=height).configure_view(stroke=None)
            .configure(background="transparent", font=FONT)
            .configure_axis(labelColor=nr.MUTED, titleColor=nr.MUTED, titleFontWeight="normal", labelFontSize=11,
                            titleFontSize=11, domain=False, ticks=False, gridColor=nr.LINE, labelFont=MONO))


def hover_columns(tips, x0, x1, tooltip, height_px=None):
    """Invisible columns (one per year / horizon / row) carrying the tooltip; the hovered one lights up softly."""
    hov = alt.selection_point(fields=[x0], on="pointerover", clear="pointerout", empty=False)
    enc = dict(x=f"{x0}:Q", x2=f"{x1}:Q", y=alt.value(0), y2=alt.value("height"),
               opacity=alt.condition(hov, alt.value(.06), alt.value(0.001)), tooltip=tooltip)
    return alt.Chart(tips).mark_rect(color=nr.INK, clip=True).encode(**enc).add_params(hov)


def t_label(t):
    """tLab of the HTML version."""
    if t == 0:
        return "Onset year (t = 0)"
    if t == -1:
        return "1 year before (t = −1, reference)"
    return (f"{t} year{'s' if t > 1 else ''} after" if t > 0 else f"{-t} years before") + f" (t = {nr.sgn(t, 0)})"


def ci_txt(a, b, d=3):
    return "–" if pd.isna(a) or pd.isna(b) else f"{nr.sgn(a, d)} to {nr.sgn(b, d)}"


# ------------------------------------------------------------------ header
if nr.any_placeholder():
    st.warning(nr.PLACEHOLDER_TEXT, title="Preview with placeholder numbers", icon=":material/science:")
st.markdown(":primary[:small[**FINDINGS**]]")
st.title("What the regressions show", anchor=False)
st.markdown("Does democracy change after an armed conflict starts, and is the change different for countries that import "
            "many weapons, or that buy them from democracies?")
st.caption(":material/info: The models show associations, not causes: conflict, arms imports and regime change all "
           "influence each other.")


# ------------------------------------------------------------------ main finding: the A1 regression
main = nr.a1_main(res)
with st.container(border=True):
    heading("Main finding: democracy after a conflict starts, by arms imports", res_src)
    st.caption("Regression A1 of notebook 08, one for each horizon k = 1 to 10 years: the change in the democracy index from "
               "the year before a conflict starts to k years after it, explained by the onset and by onset × arms imports. "
               "Arms imports are the average of the 5 years before onset, standardised (mean 0, sd 1), so they enter as a "
               "number: there is no cut-off between \"high\" and \"low\" importers. Country and year fixed effects, standard "
               "errors clustered by country.")
    if main.empty:
        st.info("Not available yet: the A1 models of notebook 08 have not been run.", icon=":material/hourglass_empty:")
    else:
        st.markdown(nr.a1_sentence(main, 5))
        st.markdown(legend_line([(f"{nr.A1_AVG} (b1)", nr.ACCENT, "━"), (f"{nr.A1_MORE} (b1 + b2)", nr.HI, "╍"),
                                 ("Band: 95% confidence interval", "#5a5955", "■")]))
        st.altair_chart(nr.a1_chart(main, 280), key="fd_main", width="stretch",
                        alt="Change in the democracy index 1 to 10 years after conflict onset, at average arms imports "
                            "and at one standard deviation more arms imports")
        st.caption("Solid: a country with average arms imports before the conflict (b1, with its 95% band). Dashed: a "
                   "country importing one standard deviation more (b1 + b2)"
                   + ("." if main["sum_lo"].notna().any() else "; its band needs the term onset+onset:arms_z from notebook 08.")
                   + " Hover a year for the numbers.")


# ------------------------------------------------------------------ (a) event study
def es_chart(groups):
    rows = [nr.event_rows(es, g).assign(grp=nr.ES_NAME[g]) for g in groups]
    rows = [r for r in rows if not r.empty]
    if not rows:
        return None
    d = pd.concat(rows, ignore_index=True)
    lo, hi, ticks, dec = nice(min(0, d["ci_low"].min()), max(0, d["ci_high"].max()), 5)
    t0, t1 = int(d["t"].min()), int(d["t"].max())
    names = [nr.ES_NAME[g] for g in groups]
    csc = alt.Scale(domain=names, range=[nr.ES_COL[g] for g in groups])
    colour = alt.Color("grp:N", legend=None, scale=csc)
    xsc = alt.Scale(domain=[t0 - .5, t1 + .5], nice=False, zero=False)
    x = alt.X("t:Q", scale=xsc,
              axis=alt.Axis(values=list(range(t0, t1 + 1)), labelExpr=signed(0), grid=False, labelFlush=False,
                            title="Years relative to conflict onset (t = −1, the year before, is the reference: 0 by definition)"))
    y_scale = alt.Scale(domain=[lo, hi], nice=False, zero=False)
    y_axis = alt.Axis(values=ticks, labelExpr=signed(dec), title="Change in democracy index", grid=True)
    pre = alt.Chart(pd.DataFrame({"a": [t0 - .5], "b": [0]})).mark_rect(color=nr.INK, opacity=.045).encode(
        x=alt.X("a:Q", scale=xsc), x2="b:Q", y=alt.value(0), y2=alt.value("height"))
    zero = alt.Chart(pd.DataFrame({"v": [0]})).mark_rule(color=nr.INK2, strokeDash=[4, 4], strokeWidth=1).encode(
        y=alt.Y("v:Q", scale=y_scale, axis=y_axis))
    start = alt.Chart(pd.DataFrame({"t": [0]})).mark_rule(color=nr.INK2, strokeWidth=1.2).encode(
        x=alt.X("t:Q", scale=xsc), y=alt.value(-6), y2=alt.value("height"))
    labels = alt.layer(*[alt.Chart(pd.DataFrame({"t": [tx]})).mark_text(
        text=txt, align="left", baseline="bottom", dx=6, dy=-9, fontSize=12, fontWeight=w, color=c).encode(
        x=alt.X("t:Q", scale=xsc), y=alt.value(0))
        for tx, txt, w, c in [(0, "Conflict starts", 600, nr.INK), (t0 - .5, "Before: should be near zero", 400, nr.INK2)]])
    band = alt.Chart(d).mark_area(opacity=.16 if len(groups) == 1 else .12).encode(
        x=x, y=alt.Y("ci_low:Q", scale=y_scale, axis=y_axis), y2="ci_high:Q", color=colour)
    line = alt.Chart(d).mark_line(strokeWidth=2, strokeJoin="round").encode(x=x, y=alt.Y("coef:Q", scale=y_scale, axis=y_axis), color=colour)
    dots = alt.Chart(d[~d["ref"]]).mark_circle(size=40, opacity=1, stroke=SURFACE, strokeWidth=1).encode(
        x=x, y=alt.Y("coef:Q", scale=y_scale, axis=y_axis), color=colour)
    ref = alt.Chart(d[d["ref"]]).mark_point(size=60, filled=True, fill=SURFACE, strokeWidth=2, opacity=1).encode(
        x=x, y=alt.Y("coef:Q", scale=y_scale, axis=y_axis), stroke=alt.Stroke("grp:N", legend=None, scale=csc))
    # one hover column per t with every group's estimate (the "hit" rects of the HTML version)
    tips = pd.DataFrame({"t": range(t0, t1 + 1)})
    tips["x0"], tips["x1"], tips["When"] = tips["t"] - .5, tips["t"] + .5, tips["t"].map(t_label)
    tip = [alt.Tooltip("When:N", title="t")]
    for k, g in enumerate(groups):
        r = nr.event_rows(es, g).set_index("t")
        txt = []
        for t in tips["t"]:
            if t not in r.index:
                txt.append("no estimate")
            elif r.at[t, "ref"]:
                txt.append("0 (reference)")
            else:
                n = r.at[t, "n"]
                txt.append(f"{nr.sgn(r.at[t, 'coef'])} (95% CI {ci_txt(r.at[t, 'ci_low'], r.at[t, 'ci_high'])})"
                           + ("" if pd.isna(n) else f", n = {int(n):,}"))
        tips[f"g{k}"] = txt
        tip.append(alt.Tooltip(f"g{k}:N", title=nr.ES_NAME[g]))
    hit = hover_columns(tips, "x0", "x1", tip)
    chart = alt.layer(pre, zero, band, line, dots, ref, start, labels, hit).properties(
        padding={"left": 4, "right": 8, "top": 24, "bottom": 4})
    return finish(chart, 340)


def es_table():
    rows = {}
    for grp in ["all"]:
        for t, c, a, b, n, ref in nr.event_rows(es, grp)[["t", "coef", "ci_low", "ci_high", "n", "ref"]].itertuples(index=False):
            row = rows.setdefault(int(t), {"t": nr.sgn(t, 0)})
            row[nr.ES_NAME[grp]] = "0 (ref.)" if ref else nr.sgn(c)
            row[f"{nr.ES_NAME[grp]}: 95% CI"] = "–" if ref else ci_txt(a, b)
            row[f"{nr.ES_NAME[grp]}: n"] = "–" if pd.isna(n) else f"{int(n):,}"
    return pd.DataFrame([rows[t] for t in sorted(rows)])


with st.container(border=True):
    ok = es is not None and not es.empty
    with st.container(horizontal=True, vertical_alignment="center"):
        st.subheader("Democracy before and after a conflict starts", anchor=False, width="content")
        if es_src == "demo":
            st.badge("Placeholder", icon=":material/science:", color="orange")
    st.caption("Event study: change in the democracy index (0 to 1) compared with the year before a conflict starts, with "
               "country and year fixed effects. Below the dashed line = less democratic than just before the conflict. "
               "How arms imports change this is in the main finding above (a regression, not a split into groups).")
    if not ok:
        st.info("Not available yet: the event study of notebook 08 has not been run.", icon=":material/hourglass_empty:")
    else:
        groups = ["all"]
        st.markdown(legend_line([(nr.ES_NAME[g], nr.ES_COL[g], "■") for g in groups]
                                + [("Band: 95% confidence interval", "#5a5955", "■")]))
        chart = es_chart(groups)
        if chart is None:
            st.info("No event-study results yet.", icon=":material/hourglass_empty:")
        else:
            st.altair_chart(chart, key="fd_es", width="stretch",
                            alt="Event study: change in the democracy index from 10 years before to 10 years after conflict onset")
        with st.expander("Show the numbers"):
            st.dataframe(es_table(), hide_index=True)


# ------------------------------------------------------------------ (b) A1 models over k
def k_chart(pts, colour, what, scale, k1):
    lo, hi, ticks, dec = scale
    pts = pts.assign(x0=pts["k"] - .5, x1=pts["k"] + .5,
                     When=[f"{k} year{'s' if k > 1 else ''} after onset ({m})" for k, m in zip(pts["k"], pts["model"])],
                     Est=[nr.sgn(c) for c in pts["coef"]], CI=[ci_txt(a, b) for a, b in zip(pts["ci_low"], pts["ci_high"])],
                     N=[f"{n:,} country-years, {c:,} countries" for n, c in zip(pts["n_obs"], pts["n_countries"])])
    x = alt.X("k:Q", scale=alt.Scale(domain=[.5, k1 + .5], nice=False, zero=False), title="Years after onset (k)",
              axis=alt.Axis(values=list(range(1, k1 + 1)), format="d", grid=False))
    ys = alt.Scale(domain=[lo, hi], nice=False, zero=False)
    ya = alt.Axis(values=ticks, labelExpr=signed(dec), title=None, grid=True)
    zero = alt.Chart(pd.DataFrame({"v": [0]})).mark_rule(color=nr.INK2, strokeDash=[4, 4]).encode(
        y=alt.Y("v:Q", scale=ys, axis=ya))
    line = alt.Chart(pts).mark_line(color=colour, strokeWidth=1.2, opacity=.45).encode(x=x, y=alt.Y("coef:Q", scale=ys, axis=ya))
    ci = alt.Chart(pts).mark_rule(color=colour, strokeWidth=2, strokeCap="round").encode(
        x=x, y=alt.Y("ci_low:Q", scale=ys, axis=ya), y2="ci_high:Q")
    caps = [alt.Chart(pts).mark_tick(color=colour, orient="horizontal", size=10, thickness=1.5).encode(
        x=x, y=alt.Y(f"{f}:Q", scale=ys, axis=ya)) for f in ("ci_low", "ci_high")]
    dots = alt.Chart(pts).mark_circle(color=colour, size=70, opacity=1, stroke=SURFACE, strokeWidth=1.5).encode(
        x=x, y=alt.Y("coef:Q", scale=ys, axis=ya))
    hit = hover_columns(pts, "x0", "x1", [alt.Tooltip("When:N", title="Horizon"), alt.Tooltip("Est:N", title=what),
                                          alt.Tooltip("CI:N", title="95% CI"), alt.Tooltip("N:N", title="n")])
    return finish(alt.layer(zero, line, ci, *caps, dots, hit).properties(padding={"left": 4, "right": 8, "top": 8, "bottom": 4}), 220)


with st.container(border=True):
    heading("The two terms of the main finding, one by one", res_src)
    st.caption("One regression for each horizon k: the change in the democracy index from the year before onset to k years "
               "after it, with country and year fixed effects. Bars: 95% confidence intervals; an interval that crosses "
               "the dashed zero line means no clear change.")
    p1 = nr.a1_points(res, "onset") if res is not None else pd.DataFrame()
    p2 = nr.a1_points(res, "onset:arms_z") if res is not None else pd.DataFrame()
    if p1.empty and p2.empty:
        st.info("Not available yet: the A1 models of notebook 08 have not been run.", icon=":material/hourglass_empty:")
    else:
        both = pd.concat([p1, p2])
        scale = nice(min(0, both["ci_low"].min()), max(0, both["ci_high"].max()), 4)  # one scale for both charts
        k1 = max(10, int(both["k"].max()))
        c1, c2 = st.columns(2, gap="medium")
        for col, pts, colour, title, term, desc, what in [
            (c1, p1, nr.ACCENT, "Average change after an onset", "onset",
             "countries with a conflict onset compared with those without", "Change after onset"),
            (c2, p2, nr.HI, "Extra change per standard deviation of arms imports", "onset:arms_z",
             "how much more (or less) for a country importing one sd more arms before the onset",
             "Extra change per sd of arms imports"),
        ]:
            with col:
                st.markdown(f"**{title}**")
                st.caption(f"Term **{term}**: {desc}")
                if pts.empty:
                    st.info("No results for this term yet.", icon=":material/hourglass_empty:")
                else:
                    st.altair_chart(k_chart(pts, colour, what, scale, k1), key=f"fd_k_{term}", width="stretch",
                                    alt=f"{what} for k = 1 to {k1} years after onset")


# ------------------------------------------------------------------ (c) forest plot and (d) suppliers
def model_note(m):
    k = re.search(r"_k(\d+)$", m)
    return m + (f" · after {k.group(1)} years" if k else " · linear probability" if re.search("lpm", m, re.I) else "")


def trunc(s, n):
    return s if len(s) <= n else s[:n - 1] + "…"


LW, RH = 210, 36  # label column width and row height (forestSvg of the HTML version: min(250, 44% of the width), 34)


def forest(rows):
    rows = rows.reset_index(drop=True)
    lo, hi, ticks, dec = nice(min(0, rows["ci_low"].min()), max(0, rows["ci_high"].max()), 4)
    nc = int((LW - 8) / 6.4)
    d = rows.assign(
        i=range(len(rows)), lab=[trunc(nr.TERM_LAB.get(t, t), nc) for t in rows["term"]],
        note=[trunc(model_note(m), nc + 4) for m in rows["model"]],
        sig=[bool(a > 0 or b < 0) for a, b in zip(rows["ci_low"], rows["ci_high"])],
        Name=[nr.TERM_LAB.get(t, t) for t in rows["term"]], Model=rows["model"] + " · " + rows["term"],
        Coef=[nr.sgn(c) + ("" if pd.isna(se) else f" (se {se:.3f})") for c, se in zip(rows["coef"], rows["se"])],
        CI=[ci_txt(a, b) for a, b in zip(rows["ci_low"], rows["ci_high"])],
        N=[f"{n:,} country-years, {c:,} countries" for n, c in zip(rows["n_obs"], rows["n_countries"])])
    d["stripe"] = d["i"] % 2 == 0
    ysc = alt.Scale(paddingInner=0, paddingOuter=0)
    y = alt.Y("i:O", axis=None, scale=ysc)
    # the plot starts LW px from the left: the labels live in that first column, inside the chart
    xs = alt.Scale(domain=[lo, hi], nice=False, zero=False, range=[LW, alt.ExprRef("width")])
    xa = alt.Axis(values=ticks, labelExpr=signed(dec), title=None, grid=False, labelFontSize=10)
    colour = alt.Color("sig:N", legend=None, scale=alt.Scale(domain=[True, False], range=[nr.ACCENT, nr.INK2]))
    stripes = alt.Chart(d[d["stripe"]]).mark_rect(color=SURFACE).encode(
        x=alt.value(0), x2=alt.value("width"), y=y)
    grid = alt.Chart(pd.DataFrame({"v": ticks})).mark_rule(strokeWidth=1).encode(
        x=alt.X("v:Q", scale=xs, axis=xa),
        color=alt.condition("abs(datum.v) < 1e-12", alt.value(nr.INK2), alt.value(nr.LINE)),
        strokeDash=alt.condition("abs(datum.v) < 1e-12", alt.value([4, 4]), alt.value([1, 0])))
    ci = alt.Chart(d).mark_rule(strokeWidth=2, strokeCap="round").encode(
        x=alt.X("ci_low:Q", scale=xs, axis=xa), x2="ci_high:Q", y=alt.Y("i:O", axis=None, scale=ysc, bandPosition=.5),
        color=colour)
    dots = alt.Chart(d).mark_circle(size=90, opacity=1, stroke=SURFACE, strokeWidth=1.5).encode(
        x=alt.X("coef:Q", scale=xs, axis=xa), y=alt.Y("i:O", axis=None, scale=ysc, bandPosition=.5), color=colour)
    lab = alt.Chart(d).mark_text(align="left", baseline="middle", dy=-8, color=nr.INK, fontSize=12, fontWeight=500).encode(
        x=alt.value(6), y=alt.Y("i:O", axis=None, scale=ysc, bandPosition=.5), text="lab:N")
    note = alt.Chart(d).mark_text(align="left", baseline="middle", dy=9, color=nr.MUTED, fontSize=10.5, font=MONO).encode(
        x=alt.value(6), y=alt.Y("i:O", axis=None, scale=ysc, bandPosition=.5), text="note:N")
    hit = alt.Chart(d).mark_rect(color=nr.INK, opacity=0.001).encode(
        x=alt.value(0), x2=alt.value("width"), y=y,
        tooltip=[alt.Tooltip("Name:N", title="Term"), alt.Tooltip("Model:N"), alt.Tooltip("Coef:N", title="Coefficient"),
                 alt.Tooltip("CI:N", title="95% CI"), alt.Tooltip("N:N", title="n")])
    chart = alt.layer(stripes, grid, ci, dots, lab, note, hit).properties(
        padding={"left": 0, "right": 16, "top": 4, "bottom": 4})
    return finish(chart, RH * len(d) + 30)  # the height includes the axis and the padding


def sup_chart():
    s = nr.supplier_series(nr._mtime("reg_suppliers"))
    long = s.melt(id_vars="year", value_vars=["dem", "aut", "all"], var_name="key", value_name="v").dropna()
    names = {"all": "All recipients", "dem": "Democratic recipients", "aut": "Autocratic recipients"}
    long["Series"] = long["key"].map(names)
    xsc = alt.Scale(domain=[1949.5, 2025.5], nice=False, zero=False)
    x = alt.X("year:Q", scale=xsc, title=None,
              axis=alt.Axis(values=list(range(1950, 2030, 10)), format="d", grid=False))
    ys = alt.Scale(domain=[0, 1], nice=False)
    lines = alt.Chart(long).mark_line(strokeJoin="round").encode(
        x=x, y=alt.Y("v:Q", scale=ys, title=None, axis=alt.Axis(values=[0, .25, .5, .75, 1], grid=True, labelExpr="format(datum.value, '~g')")),
        color=alt.Color("Series:N", legend=None, scale=alt.Scale(domain=list(names.values()),
                                                                 range=[nr.INK, nr.REG_COLS[3], nr.REG_COLS[0]])),
        strokeWidth=alt.condition("datum.key == 'all'", alt.value(2.4), alt.value(1.5)),
        opacity=alt.condition("datum.key == 'all'", alt.value(1), alt.value(.6)),
        detail="key:N", order=alt.Order("key:N"))
    cw = pd.DataFrame({"x": [1991.5]})
    rule = alt.Chart(cw).mark_rule(color=nr.INK2, strokeDash=[4, 4]).encode(x=alt.X("x:Q", scale=xsc), y=alt.value(-8),
                                                                          y2=alt.value("height"))
    lab = alt.Chart(cw).mark_text(text="1991: end of the Cold War", align="left", baseline="bottom", dx=5, dy=-10,
                                  color=nr.INK2, fontSize=12).encode(x=alt.X("x:Q", scale=xsc), y=alt.value(0))
    f2 = lambda v: "–" if pd.isna(v) else f"{v:.2f}"
    n0 = lambda v: 0 if pd.isna(v) else int(v)
    tips = pd.DataFrame({"year": s["year"], "x0": s["year"] - .5, "x1": s["year"] + .5,
                         "a": [f"{f2(v)} ({n0(n)} countries)" for v, n in zip(s["all"], s["n"])],
                         "d": [f"{f2(v)} ({n0(n)})" for v, n in zip(s["dem"], s["nd"])],
                         "u": [f"{f2(v)} ({n0(n)})" for v, n in zip(s["aut"], s["na"])]})
    hit = hover_columns(tips, "x0", "x1", [alt.Tooltip("year:Q", title="Year", format="d"),
                                           alt.Tooltip("a:N", title="All recipients"),
                                           alt.Tooltip("d:N", title="Democratic recipients"),
                                           alt.Tooltip("u:N", title="Autocratic recipients")])
    return finish(alt.layer(lines, rule, lab, hit).properties(padding={"left": 4, "right": 8, "top": 24, "bottom": 4}), 480)


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
            st.altair_chart(forest(rows), key=f"fd_forest_{title}", width="stretch",
                            alt=f"Forest plot of {title}: coefficients with 95% confidence intervals")
        if not shown:
            st.info("No results for the B, C or D models yet.", icon=":material/hourglass_empty:")
        known = allr["model"].str.match(r"^A1_k\d+$")
        for pattern, _, _ in nr.FOREST:
            known |= allr["model"].str.contains(pattern)
        other = allr[~known]
        if not other.empty:
            st.markdown("**Other models**")
            st.dataframe(pd.DataFrame({"Model": other["model"], "Term": other["term"],
                                       "Coef.": [nr.sgn(c) for c in other["coef"]],
                                       "95% CI": [ci_txt(a, b) for a, b in zip(other["ci_low"], other["ci_high"])],
                                       "n": other["n_obs"], "Countries": other["n_countries"]}), hide_index=True,
                         column_config={"n": st.column_config.NumberColumn(format="%,d"),
                                        "Countries": st.column_config.NumberColumn(format="%,d")})

with right.container(border=True, height="stretch"):
    heading("Who supplied the arms over time", sup_src)
    st.caption("Democracy of the suppliers (0 = all arms from autocracies, 1 = from full democracies), weighted by TIV, "
               "averaged over all countries that imported arms that year.")
    if sup is None or sup.empty:
        st.info("Not available yet: the supplier table of notebook 08 does not exist.", icon=":material/hourglass_empty:")
    else:
        st.markdown(legend_line([("All recipients", nr.INK, "━"), ("Democratic recipients", nr.REG_COLS[3], "━"),
                                 ("Autocratic recipients", nr.REG_COLS[0], "━")]))
        st.altair_chart(sup_chart(), key="fd_sup", width="stretch",
                        alt="Mean democracy of arms suppliers per year, 1950 to 2025")


# ------------------------------------------------------------------ limits
with st.container(border=True):
    st.subheader("Limits", anchor=False)
    a, b = st.columns(2, gap="large")
    a.markdown(
        "- **Associations, not causes.** :gray[Conflict, arms imports and regime change influence each other, so no model "
        "here shows what caused what.]\n"
        "- **TIV is not money.** :gray[SIPRI trend-indicator values measure military capability transferred, not the price "
        "paid.]\n"
        "- **Small groups.** :gray[Some splits rest on few conflict onsets; wide intervals there mean the data cannot tell.]")
    b.markdown(
        "- **Historical states.** :gray[The Soviet Union, Yugoslavia and others are counted under a successor's code, as in "
        "V-Dem.]\n"
        "- **Preliminary.** :gray[The models of notebook 08 are still being checked; numbers can change.]")
