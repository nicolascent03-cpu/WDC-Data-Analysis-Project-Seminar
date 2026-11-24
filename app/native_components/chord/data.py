"""Numbers for the chord ring and the country cards, as plain JSON (lists and dicts of str/float).

Source: native_data.load_flows() (every SIPRI supplier per recipient-year) and
native_data.load_panel() (regime label and total imports, which equal the sum of the flows per recipient-year).
"""

import pandas as pd
import streamlit as st

import native_data as nd

NS, NR = 6, 8                              # named supplier slots, named recipient slots
NON_STATE = {"Other", "unknown supplier(s)"}  # not a country: never a named slot, never a "main supplier"
SHORT = {"United States": "USA", "Soviet Union": "Soviet U.", "United Kingdom": "UK"}
MUTED, OTHER_REC = "#959086", "#45423d"


@st.cache_data
def _base():
    f = nd.load_flows()
    p = nd.load_panel()
    names = p.drop_duplicates("iso3").set_index("iso3")["country_name"].to_dict()
    named = f[~f["supplier"].isin(NON_STATE)]
    top_sup = list(named.groupby("supplier")["tiv"].sum().nlargest(NS).index)
    return f, p, names, top_sup


def _chord(f, top_sup, y):
    """Chord of one year from ALL deliveries of that year (SIPRI's "Other" counts as "Other suppliers")."""
    g = f[f["year"] == y]
    tot = float(g["tiv"].sum())
    rt = g.groupby("recipient_iso3")["tiv"].sum()
    recs = sorted(rt.index, key=lambda r: (-rt[r], r))[:NR]
    si = {n: i for i, n in enumerate(top_sup)}
    ri = {r: i for i, r in enumerate(recs)}
    s_idx = g["supplier"].map(si).fillna(len(top_sup)).astype(int)
    r_idx = g["recipient_iso3"].map(ri).fillna(len(recs)).astype(int)
    links = g.assign(si=s_idx, ri=r_idx).groupby(["si", "ri"])["tiv"].sum()
    return g, tot, recs, s_idx, r_idx, links


@st.cache_data
def slot_max():
    """Largest share each slot reaches over all years, so every slot keeps one fixed place on the ring."""
    f, _, _, top_sup = _base()
    s, r = [0.0] * (NS + 1), [0.0] * (NR + 1)
    for y in sorted(f["year"].unique()):
        g, tot, recs, s_idx, r_idx, _ = _chord(f, top_sup, y)
        if not tot:
            continue
        for i, v in g.groupby(s_idx)["tiv"].sum().items():
            s[i] = max(s[i], v / tot)
        # the "Other recipients" node always sits in the last slot, whatever the number of named recipients
        for i, v in g.groupby(r_idx)["tiv"].sum().items():
            k = NR if i >= len(recs) else i
            r[k] = max(r[k], v / tot)
    return {"s": s, "r": r}


@st.cache_data
def ring(y):
    f, _, names, top_sup = _base()
    g, tot, recs, s_idx, r_idx, links = _chord(f, top_sup, y)
    sv = g.groupby(s_idx)["tiv"].sum()
    rv = g.groupby(r_idx)["tiv"].sum()
    share = lambda v: float(v) / tot if tot else 0.0
    S = [{"id": "s:" + n, "name": n, "label": SHORT.get(n, n), "color": nd.supplier_colour(n), "slot": i,
          "v": float(sv.get(i, 0)), "share": share(sv.get(i, 0)), "card": "s:" + n} for i, n in enumerate(top_sup)]
    n_other_s = int(g.loc[s_idx == len(top_sup), "supplier"].nunique())
    S.append({"id": "s:~", "name": "Other suppliers", "label": "Other", "color": nd.OTHER_COLOUR, "slot": NS, "other": True,
              "v": float(sv.get(len(top_sup), 0)), "share": share(sv.get(len(top_sup), 0)), "card": None,
              "note": ""})
    R = [{"id": "r:" + r, "name": names.get(r, r), "slot": i, "color": MUTED,
          "v": float(rv.get(i, 0)), "share": share(rv.get(i, 0)), "card": "r:" + r} for i, r in enumerate(recs)]
    n_other_r = int(g.loc[r_idx == len(recs), "recipient_iso3"].nunique())
    R.append({"id": "r:~", "name": "Other recipients", "slot": NR, "color": OTHER_REC, "other": True,
              "v": float(rv.get(len(recs), 0)), "share": share(rv.get(len(recs), 0)), "card": None,
              "note": f"{n_other_r} countries" if n_other_r else ""})
    # the "Other recipients" link index is len(recs); map it to the R list position
    L = []
    for (i, j), v in links.items():
        if v > 0:
            L.append({"si": int(i), "ri": int(j) if j < len(recs) else len(R) - 1, "v": float(v), "share": share(v)})
    for x in S + R:
        x["v"], x["share"] = round(x["v"], 2), round(x["share"], 6)
    return {"year": int(y), "tot": round(tot, 2), "S": S, "R": R, "links": L, "max": slot_max()}


# ------------------------------------------------------------------ country cards
def _part(series, k=5, label=None):
    """{total, top: [{name, v}], other, n} from a Series of TIV by name (largest first, top k listed)."""
    s = series[series > 0].sort_values(ascending=False)
    named = s[~s.index.isin(NON_STATE)]
    top = named.head(k)
    return {"total": round(float(s.sum()), 2),
            "top": [{"name": label(n) if label else n, "v": round(float(v), 2)} for n, v in top.items()],
            "other": round(float(s.sum() - top.sum()), 2), "n": int(len(named) - len(top)),
            "lumped": bool(s.index.isin(NON_STATE).any())}  # the rest includes SIPRI's unnamed "Other"


def _card(key, y):
    f, p, names, _ = _base()
    kind, ref = key.split(":", 1)
    if kind == "s":  # a supplier: exports by its SIPRI name, imports and regime at its map country
        isos = f.loc[f["supplier"] == ref, "supplier_iso3"].dropna()
        iso = nd.SUPPLIER_ISO.get(ref) or (isos.iloc[0] if len(isos) else None)
        name = ref
        exp_rows = f[(f["year"] == y) & (f["supplier"] == ref)]
    else:            # a country: exports by everything SIPRI names at this iso3 (Soviet Union + Russia at RUS)
        iso = ref
        name = names.get(ref, ref)
        exp_rows = f[(f["year"] == y) & (f["supplier_iso3"] == ref)]
    imp = f[(f["year"] == y) & (f["recipient_iso3"] == iso)].groupby("supplier")["tiv"].sum() if iso else pd.Series(dtype=float)
    exp = exp_rows.groupby("recipient_iso3")["tiv"].sum()
    im = _part(imp)
    for x in im["top"]:
        x["color"] = nd.supplier_colour(x["name"])
    ex = _part(exp, label=lambda r: names.get(r, r))
    exp_col = nd.supplier_colour(exp_rows.groupby("supplier")["tiv"].sum().idxmax()) if len(exp_rows) else nd.OTHER_COLOUR
    for x in ex["top"]:
        x["color"] = exp_col
    row = p[(p["iso3"] == iso) & (p["year"] == y)] if iso else p.iloc[0:0]
    regime = str(row["regime_label"].iloc[0]).capitalize() if len(row) and pd.notna(row["regime_label"].iloc[0]) else "No V-Dem regime data"
    if len(row) and pd.notna(row["arms_imports_tiv"].iloc[0]):
        im["total"] = round(float(row["arms_imports_tiv"].iloc[0]), 2)
        im["other"] = round(max(0.0, im["total"] - sum(x["v"] for x in im["top"])), 2)
    win = f[(f["year"] > y - 5) & (f["year"] <= y) & (f["recipient_iso3"] == iso) & ~f["supplier"].isin(NON_STATE)] if iso else f.iloc[0:0]
    main = win.groupby("supplier")["tiv"].sum().idxmax() if len(win) else None
    world = float(f.loc[f["year"] == y, "tiv"].sum())
    return {"key": key, "name": name, "year": int(y), "regime": regime, "imp": im, "exp": ex,
            "main": main, "mainColor": nd.supplier_colour(main) if main else None,
            "worldShare": im["total"] / world if world else 0.0}


@st.cache_data
def cards(y, pinned=None):
    """Cards of every named country in the year's ring, plus the pinned one, keyed by card key."""
    r = ring(y)
    keys = [x["card"] for x in r["S"] + r["R"] if x["card"]]
    if pinned and pinned not in keys:
        keys.append(pinned)
    return {k: _card(k, y) for k in keys}
