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
N_ONSETS = nr.n_onsets() or "the"  # 281 conflict onsets in notebook 08


# ------------------------------------------------------------------ helpers
def heading(text, source, help=None):
    """Card heading, with the method in its tooltip (help) and a badge when the numbers are placeholders."""
    with st.container(horizontal=True, vertical_alignment="center"):
        st.subheader(text, anchor=False, width="content", help=help)
        if source == "demo":
            st.badge("Placeholder", icon=":material/science:", color="orange")


def takeaway(text):
    """The one line a card should leave the reader with, above its chart."""
    st.markdown(f"**{text}**")


def notebook_note(part, text):
    """The interpretation written in notebook 08, folded away under the chart."""
    with st.expander(f"What notebook 08 concludes (Part {part})", icon=":material/menu_book:"):
        st.markdown(text)


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
            .configure_axis(labelColor=nr.MUTED, titleColor=nr.MUTED, titleFontWeight="normal", labelFontSize=7.7,
                            titleFontSize=7.7, domain=False, ticks=False, gridColor=nr.LINE, labelFont=MONO))


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
# only the parts that still use the placeholder numbers of data/demo/ are named
_demo = [name for name, src in [("the main finding", res_src), ("the event study", es_src),
                                ("who supplied the arms", sup_src)] if src == "demo"]
if _demo:
    st.warning("Placeholder numbers in " + ", ".join(_demo) + ": notebook 08 has not produced these results yet. The page "
               "switches to the real numbers as soon as they exist.", title="Partly a preview", icon=":material/science:")
st.markdown(":primary[:small[**FINDINGS**]]")
st.title("What the regressions show", anchor=False)
st.markdown("Does democracy change after a conflict starts, and does it depend on the weapons a country imported?")
st.caption(":material/info: Associations, not causes.")


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
        text=txt, align="left", baseline="bottom", dx=6, dy=-9, fontSize=8.4, fontWeight=w, color=c).encode(
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
    xa = alt.Axis(values=ticks, labelExpr=signed(dec), title=None, grid=False, labelFontSize=7)
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
    lab = alt.Chart(d).mark_text(align="left", baseline="middle", dy=-8, color=nr.INK, fontSize=8.4, fontWeight=500).encode(
        x=alt.value(6), y=alt.Y("i:O", axis=None, scale=ysc, bandPosition=.5), text="lab:N")
    note = alt.Chart(d).mark_text(align="left", baseline="middle", dy=9, color=nr.MUTED, fontSize=7.3, font=MONO).encode(
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
                                  color=nr.INK2, fontSize=8.4).encode(x=alt.X("x:Q", scale=xsc), y=alt.value(0))
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




# ------------------------------------------------------------------ the numbers of the three answers
# Taken from the result files, so they follow notebook 08 when it is run again.
def es_window(t0=6, t1=9):
    """Mean event-study estimate in years t0 to t1 after onset, and whether every interval there excludes zero."""
    if es is None or es.empty:
        return None, False
    r = es[(es["group"] == "all") & es["t"].between(t0, t1)]
    if r.empty:
        return None, False
    return float(r["coef"].mean()), bool(((r["ci_high"] < 0) | (r["ci_low"] > 0)).all())


def term(model, name):
    """One row of reg_results.csv (coef, ci_low, ci_high, n_obs, n_countries), or None."""
    if res is None:
        return None
    r = res[(res["model"] == model) & (res["term"] == name)]
    return None if r.empty else r.iloc[0]


def clear(r):
    return r is not None and (r["ci_low"] > 0 or r["ci_high"] < 0)


def answer_card(col, question, value, label, is_clear, ci=None):
    with col.container(border=True, height="stretch"):
        st.markdown(f":gray[{question}]")
        st.markdown(f"## {value}")
        st.caption(label + (f" · 95% CI {ci}" if ci else ""))
        if value != "–":
            st.badge("clear" if is_clear else "not clearly different from zero",
                     color="green" if is_clear else "gray", icon=":material/check:" if is_clear else ":material/remove:")


def summary():
    es_v, es_clear = es_window()
    b2, c3 = term("A1_k5", "onset:arms_z"), term("C3_k5", "onset:sup_dem_pre5")
    c1, c2, c3c = st.columns(3, gap="medium")
    answer_card(c1, "1 · Democracy after a conflict starts", "–" if es_v is None else nr.sgn(es_v),
                "democracy index 6 to 9 years after onset, against countries without conflict", es_clear)
    answer_card(c2, "2 · Effect of arms imports", "–" if b2 is None else nr.sgn(b2["coef"]),
                "per standard deviation more arms imports, 5 years after onset", clear(b2),
                None if b2 is None else ci_txt(b2["ci_low"], b2["ci_high"]))
    answer_card(c3c, "3 · Effect of who supplied them", "–" if c3 is None else nr.sgn(c3["coef"]),
                "arms from democracies instead of autocracies, 5 years after onset", clear(c3),
                None if c3 is None else ci_txt(c3["ci_low"], c3["ci_high"]))
    a1k1 = term("A1_k1", "onset")
    if a1k1 is not None:
        st.caption(f"{N_ONSETS} conflict onsets in {int(a1k1['n_countries'])} countries · {int(a1k1['n_obs']):,} "
                   f"country-years · 1950 to 2025. On the democracy index from 0 to 1.")


def estimate(latex, lines):
    """What a question's model estimates: the equation and what its parts mean, folded away."""
    with st.expander("What we estimate", icon=":material/functions:"):
        st.latex(latex)
        st.markdown(lines)


# ------------------------------------------------------------------ 1. what happens to democracy (event study, A3)
def q1_card():
    with st.container(border=True):
        ok = es is not None and not es.empty
        heading("1 · What happens to democracy after a conflict starts?", es_src,
                help="Below the dashed line = less democratic than the year before the onset, compared with countries "
                     "without conflict. Hover a year for the estimate and the number of onsets.")
        if not ok:
            st.info("Not available yet: the event study of notebook 08 has not been run.", icon=":material/hourglass_empty:")
            return
        v, is_clear = es_window()
        if es_src == "real" and v is not None:
            takeaway(f"No gap before the onset. Afterwards democracy slowly falls behind: {nr.sgn(v)} on average "
                     f"6 to 9 years later{' (clear)' if is_clear else ''}.")
        st.markdown(legend_line([(nr.ES_NAME["all"], nr.ES_COL["all"], "■"), ("Band: 95% confidence interval", "#5a5955", "■")]))
        chart = es_chart(["all"])
        if chart is None:
            st.info("No event-study results yet.", icon=":material/hourglass_empty:")
        else:
            st.altair_chart(chart, key="fd_es", width="stretch",
                            alt="Event study: democracy index from 10 years before to 10 years after conflict onset")
        estimate(r"\text{democracy}_{s,i,t} = \sum_{e=-10,\; e \neq -1}^{10} \beta_e \, D^{\,e}_{s,i,t}"
                 r" + \alpha_{s,i} + \lambda_{s,t} + \varepsilon_{s,i,t}",
                 "- One **stack** *s* per conflict onset: the onset country and the **clean controls**, countries with no "
                 "conflict in the same 21 years.\n"
                 "- $D^{\\,e}$ = 1 for the onset country *e* years from its onset; **β_e** is how far its democracy index "
                 "is from the controls, against the year before onset (e = −1).\n"
                 "- Stack-by-country (α) and stack-by-year (λ) fixed effects, standard errors clustered by country. "
                 "Notebook 08, A3.")
        with st.expander("Show the numbers"):
            st.dataframe(es_table(), hide_index=True)
        if es_src == "real":
            notebook_note("A", "Before the onset, the democracy index of onset countries moves in parallel with the clean "
                          "controls (all ten leads between −0.006 and +0.004, intervals including zero), so there is no sign "
                          "of a pre-trend. After the onset it falls behind the controls: by about 0.013 after 4 to 5 years "
                          "and about 0.018 to 0.025 after 6 to 9 years, where the 95% intervals no longer include zero. This "
                          "fits conflict onsets being followed by a small, slow decline in democracy, but other shocks around "
                          "the onset could explain part of it.")


# ------------------------------------------------------------------ 2. do arms imports change it (A1)
def terms_detail():
    """b1 and b2 of A1 as separate charts, one scale for both."""
    p1 = nr.a1_points(res, "onset") if res is not None else pd.DataFrame()
    p2 = nr.a1_points(res, "onset:arms_z") if res is not None else pd.DataFrame()
    if p1.empty and p2.empty:
        return
    with st.expander("Show each term separately", icon=":material/bar_chart:"):
        both = pd.concat([p1, p2])
        scale = nice(min(0, both["ci_low"].min()), max(0, both["ci_high"].max()), 4)
        k1 = max(10, int(both["k"].max()))
        c1, c2 = st.columns(2, gap="medium")
        for col, pts, colour, title, name, what in [
            (c1, p1, nr.ACCENT, "Change after an onset (b1)", "onset", "Change after onset"),
            (c2, p2, nr.HI, "Extra change per sd of arms imports (b2)", "onset:arms_z", "Extra change per sd of arms imports"),
        ]:
            with col:
                st.markdown(f"**{title}**")
                if not pts.empty:
                    st.altair_chart(k_chart(pts, colour, what, scale, k1), key=f"fd_k_{name}", width="stretch",
                                    alt=f"{what} for k = 1 to {k1} years after onset")


def q2_card():
    main = nr.a1_main(res)
    with st.container(border=True):
        heading("2 · Do arms imports change that?", res_src,
                help="Solid line: a country with average arms imports before the conflict (b1, with its 95% band). "
                     "Dashed: one standard deviation more (b1 + b2). Hover a year for the numbers.")
        if main.empty:
            st.info("Not available yet: the A1 models of notebook 08 have not been run.", icon=":material/hourglass_empty:")
            return
        b2 = term("A1_k5", "onset:arms_z")
        takeaway("No clear difference: countries that imported more arms before the conflict look about the same afterwards."
                 if b2 is not None and not clear(b2) else "Arms imports before the conflict go with a different change.")
        st.markdown(nr.a1_sentence(main, 5))
        st.markdown(nr.a1_legend())
        st.altair_chart(nr.a1_chart(main, 280), key="fd_main", width="stretch",
                        alt="Change in the democracy index 1 to 10 years after conflict onset, at average arms imports "
                            "and at one standard deviation more arms imports")
        estimate(r"y^{(k)}_{i,t} = \beta_1\,\text{onset}_{i,t} + \beta_2\,\text{onset}_{i,t}\times\text{arms}^{z}_{i,t}"
                 r" + \gamma\,\text{arms}^{z}_{i,t} + \alpha_i + \lambda_t + \varepsilon_{i,t}",
                 "- $y^{(k)}$ = democracy index *k* years after *t* minus the year before *t*, one regression for each "
                 "k = 1 to 10.\n"
                 "- **onset** = 1 in a conflict year after two years without conflict.\n"
                 "- **arms_z** = mean log arms imports of the 5 years before, standardised (mean 0, sd 1): one "
                 "continuous number, no cut-off between groups.\n"
                 "- **β₁**: change at average arms imports; **β₂**: difference per sd more arms. Country (α) and year (λ) "
                 "fixed effects, standard errors clustered by country. Notebook 08, A1.")
        terms_detail()
        if res_src == "real":
            notebook_note("A", "In the years after a conflict onset, the democracy index of a country with average arms "
                          "imports is slightly lower than in other countries in the same year, by about 0.005 to 0.011 points "
                          "on the 0 to 1 scale. For countries that imported one standard deviation more arms in the five "
                          "years before the onset, the estimate is slightly positive in the first five years (about +0.001 to "
                          "+0.011), but from about k = 7 the two lines are almost identical. All 95% confidence intervals "
                          f"include zero at every horizon: with {N_ONSETS} onsets and a democracy index that changes slowly, "
                          "the data are not precise enough to show a clear difference.")


# ------------------------------------------------------------------ 3. does it matter who supplied them (C3)
def q3_card():
    allr = res[res["coef"].notna() & res["model"].notna()] if res is not None else pd.DataFrame()
    with st.container(border=True):
        heading("3 · Does it matter who supplied the arms?", res_src,
                help="Left: the regression (dot: estimate; line: 95% interval). Right: how democratic the suppliers were "
                     "each year, weighted by TIV, for all importing countries.")
        rows = allr[allr["model"].str.contains(r"^C\d*_")] if not allr.empty else allr
        c3 = term("C3_k5", "onset:sup_dem_pre5")
        if c3 is not None:
            takeaway("No clear difference between arms from democracies and arms from autocracies."
                     if not clear(c3) else "Arms from democracies go with a different change.")
        left, right = st.columns(2, gap="large")
        with left:
            if rows.empty:
                st.info("Not available yet: the supplier regression of notebook 08 has not been run.",
                        icon=":material/hourglass_empty:")
            else:
                st.markdown("**The regression**", help=dict((t, d) for _, t, d in nr.FOREST).get("Who supplied the arms (C)"))
                st.altair_chart(forest(rows), key="fd_forest_C", width="stretch",
                                alt="Supplier democracy before onset and the change in democracy after it, with 95% intervals")
                estimate(r"y^{(k)}_{i,t} = \beta_1\,\text{onset} + \beta_2\,\text{onset}\times\text{arms}^{z} + "
                         r"\beta_3\,\text{onset}\times\text{supdem} + \gamma\,\text{arms}^{z} + \delta\,\text{supdem}"
                         r" + \alpha_i + \lambda_t + \varepsilon_{i,t}",
                         "- The model of question 2 plus **supdem**: how democratic the suppliers of the 5 years before "
                         "were (0 = all autocracies, 1 = all democracies), weighted by TIV.\n"
                         "- **β₃**: the difference between arms only from democracies and only from autocracies, for k = 5 "
                         "and 10.\n"
                         "- Only countries that imported arms in those 5 years. Notebook 08, C3.")
        with right:
            if sup is None or sup.empty:
                st.info("Not available yet: the supplier table of notebook 08 does not exist.", icon=":material/hourglass_empty:")
            else:
                st.markdown("**Who supplied the arms, 1950 to 2025**")
                st.markdown(legend_line([("All recipients", nr.INK, "━"), ("Democratic recipients", nr.REG_COLS[3], "━"),
                                         ("Autocratic recipients", nr.REG_COLS[0], "━")]))
                st.altair_chart(sup_chart(), key="fd_sup", width="stretch",
                                alt="Mean democracy of arms suppliers per year, 1950 to 2025")
        if res_src == "real" and c3 is not None:
            notebook_note("C", "Countries whose arms in the five years before a conflict came mostly from democratic "
                          "suppliers show about the same change in democracy after onset as countries supplied mostly by "
                          "autocracies: −0.005 after 5 years (95% CI −0.063 to +0.053) and −0.037 after 10 years (−0.118 to "
                          "+0.044), comparing countries with similar amounts of arms imports. Both intervals include zero and "
                          "are wide, so a modest difference in either direction cannot be ruled out. The sample is the 243 "
                          "onsets in countries that imported arms in the five years before, and supplier democracy may go "
                          "along with other things, such as Cold War alignment, that the model does not capture.")


def more_models():
    """Further models of notebook 08 (splits B, prediction D, others), only when the results file has them."""
    allr = res[res["coef"].notna() & res["model"].notna()] if res is not None else pd.DataFrame()
    if allr.empty:
        return
    extra = [(p, t, d) for p, t, d in nr.FOREST if not p.startswith(r"^C") and allr["model"].str.contains(p).any()]
    known = allr["model"].str.match(r"^A1_k\d+$")
    for p, _, _ in nr.FOREST:
        known |= allr["model"].str.contains(p)
    other = allr[~known]
    if not extra and other.empty:
        return
    with st.container(border=True):
        heading("Further models", res_src)
        for pattern, title, desc in extra:
            st.markdown(f"**{title}**", help=desc)
            st.altair_chart(forest(allr[allr["model"].str.contains(pattern)]), key=f"fd_forest_{title}", width="stretch")
        if not other.empty:
            st.dataframe(pd.DataFrame({"Model": other["model"], "Term": other["term"],
                                       "Coef.": [nr.sgn(c) for c in other["coef"]],
                                       "95% CI": [ci_txt(a, b) for a, b in zip(other["ci_low"], other["ci_high"])],
                                       "n": other["n_obs"], "Countries": other["n_countries"]}), hide_index=True)


def limits_card():
    with st.container(border=True):
        st.subheader("Limits", anchor=False)
        a, b = st.columns(2, gap="large")
        a.markdown(
            "- **Associations, not causes.** :gray[Conflict, arms and regimes influence each other.]\n"
            "- **TIV is not money.** :gray[It measures military capability.]")
        b.markdown(
            "- **Few onsets.** :gray[281 (243 with arms before them): too few to tell groups apart.]\n"
            "- **Historical states.** :gray[Counted under a successor's code, as in V-Dem.]")


# ------------------------------------------------------------------ the page, in the order of the research question
summary()
q1_card()
q2_card()
q3_card()
more_models()
limits_card()
