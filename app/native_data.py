"""Data for the native Streamlit version of the ADC website (no custom HTML).

Everything is read from data/clean/ (our own pipeline) plus the Equal Earth country shapes in
app/site/mapdata.json, which only serve to give every country one point (longitude, latitude) for
drawing arms flows as lines.
"""

import hashlib
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
CLEAN = ROOT / "data" / "clean"
MAPDATA = ROOT / "app" / "site" / "mapdata.json"

REGIMES = ["closed autocracy", "electoral autocracy", "electoral democracy", "liberal democracy"]
REGIME_COLOURS = {"closed autocracy": "#e66767", "electoral autocracy": "#874239",
                  "electoral democracy": "#2f5784", "liberal democracy": "#6da7ec"}
SUPPLIER_COLOURS = {"United States": "#3987e5", "Soviet Union": "#e66767", "Russia": "#d55181", "United Kingdom": "#199e70",
                    "France": "#9085e9", "Germany": "#c98500", "China": "#d95926"}
OTHER_COLOUR = "#8a857c"

# SIPRI supplier names that are not in the crosswalk (or historical states), mapped to a country on today's map
SUPPLIER_ISO = {"United States": "USA", "Soviet Union": "RUS", "Russia": "RUS", "Czechoslovakia": "CZE",
                "East Germany (GDR)": "DEU", "Turkiye": "TUR", "United Kingdom": "GBR", "North Korea": "PRK",
                "South Korea": "KOR", "Taiwan": "TWN", "United Arab Emirates": "ARE", "Yugoslavia": "SRB",
                "Viet Nam": "VNM", "South Vietnam": "VNM", "Bosnia-Herzegovina": "BIH", "DR Congo": "COD",
                "North Yemen": "YEM", "South Yemen": "YEM", "Cote d'Ivoire": "CIV"}
HISTORICAL = {"DDR": "DEU", "VDR": "VNM", "YMD": "YEM"}  # drawn at today's country


@st.cache_data
def load_panel():
    panel = pd.read_csv(CLEAN / "panel.csv")
    panel = panel.sort_values(["iso3", "year"])
    panel["arms_10"] = panel.groupby("iso3")["arms_imports_tiv"].transform(lambda s: s.rolling(10, min_periods=1).sum())
    return panel


def _equal_earth_inverse(X, Y):
    """Projected Equal Earth coordinates (unit sphere) -> longitude, latitude in degrees."""
    a1, a2, a3, a4 = 1.340264, -0.081106, 0.000893, 0.003796
    th = np.array(Y, dtype=float)
    for _ in range(30):  # Newton's method on y(theta)
        t2 = th * th
        t6 = t2 ** 3
        f = th * (a1 + a2 * t2 + t6 * (a3 + a4 * t2)) - Y
        df = a1 + 3 * a2 * t2 + t6 * (7 * a3 + 9 * a4 * t2)
        th = th - f / df
    t2 = th * th
    t6 = t2 ** 3
    lat = np.arcsin(2 * np.sin(th) / np.sqrt(3))
    lon = X * 3 * (9 * a4 * t6 * t2 + 7 * a3 * t6 + 3 * a2 * t2 + a1) / (2 * np.sqrt(3) * np.cos(th))
    return np.degrees(lon), np.degrees(lat)


@st.cache_data
def country_points():
    """One point per country: centroid of its largest landmass on our Equal Earth map, as (lon, lat)."""
    m = json.loads(MAPDATA.read_text(encoding="utf8"))
    p = m["from_natural_earth"]
    xy = {}
    for iso, d in m["p"].items():
        best = None
        for sub in d.split("M")[1:]:
            pts = np.array([(float(a), float(b)) for a, b in re.findall(r"(-?[\d.]+),(-?[\d.]+)", sub)])
            if len(pts) < 3:
                continue
            x, y = pts[:, 0], pts[:, 1]
            x2, y2 = np.roll(x, -1), np.roll(y, -1)
            c = x * y2 - x2 * y
            area = c.sum() / 2
            if area and (best is None or abs(area) > abs(best[0])):
                best = (area, ((x + x2) * c).sum() / (6 * area), ((y + y2) * c).sum() / (6 * area))
        if best:
            xy[iso] = (best[1], best[2])
    for iso, pt in m.get("pts", {}).items():
        xy.setdefault(iso, tuple(pt))
    isos = list(xy)
    arr = np.array([xy[i] for i in isos])
    lon, lat = _equal_earth_inverse((arr[:, 0] - p["W"] / 2) / p["S"], (p["TY"] - arr[:, 1]) / p["S"])
    pts = pd.DataFrame({"iso3": isos, "lon": lon, "lat": lat})
    for old, new in HISTORICAL.items():
        if new in xy:
            pts.loc[len(pts)] = [old, *pts.loc[pts["iso3"] == new, ["lon", "lat"]].values[0]]
    return pts.set_index("iso3")


@st.cache_data
def country_geojson():
    """Our country shapes as GeoJSON in longitude/latitude (Equal Earth inverted), for pydeck maps
    without any external map service."""
    m = json.loads(MAPDATA.read_text(encoding="utf8"))
    p = m["from_natural_earth"]
    feats = []
    for iso, d in m["p"].items():
        polys = []
        for sub in d.split("M")[1:]:
            pts = np.array([(float(a), float(b)) for a, b in re.findall(r"(-?[\d.]+),(-?[\d.]+)", sub)])
            if len(pts) < 3:
                continue
            lon, lat = _equal_earth_inverse((pts[:, 0] - p["W"] / 2) / p["S"], (p["TY"] - pts[:, 1]) / p["S"])
            if lon.max() - lon.min() > 300:  # a ring split at the date line: skip the sliver
                continue
            ring = np.column_stack([lon, lat]).round(3).tolist()
            polys.append([ring + [ring[0]]])
        if polys:
            feats.append({"type": "Feature", "properties": {"iso3": iso}, "geometry": {"type": "MultiPolygon", "coordinates": polys}})
    return {"type": "FeatureCollection", "features": feats}


@st.cache_data
def load_flows():
    """Deliveries per year with EVERY supplier: supplier (SIPRI name and iso3), recipient iso3, TIV.

    The clean sipri_suppliers.csv from notebook 04 keeps only each recipient's top 3 suppliers plus "Other".
    The full lists per recipient and year are in app/site/data.json (the same data the HTML version shows),
    so the website uses those. Once notebook 08 writes a full supplier table to data/clean/, switch to it."""
    data = json.loads((ROOT / "app" / "site" / "data.json").read_text(encoding="utf8"))
    rows = [(iso, s["s"], int(y), float(v)) for iso, sups in data["suppliers"].items() for s in sups for y, v in s["y"]]
    sup = pd.DataFrame(rows, columns=["recipient_iso3", "supplier", "year", "tiv"])
    cw = pd.read_csv(CLEAN / "crosswalk_sipri.csv")
    name_iso = dict(zip(cw["recipient"], cw["iso3"]))
    name_iso.update(SUPPLIER_ISO)
    sup["supplier_iso3"] = sup["supplier"].map(name_iso)
    return sup


def supplier_colour(name):
    return SUPPLIER_COLOURS.get(name, OTHER_COLOUR)


def is_non_state(name):
    """SIPRI suppliers that are not a state: "Other", "unknown supplier(s)", rebel groups (*) and organisations (**)."""
    return name == "Other" or str(name).endswith("*") or str(name).lower().startswith("unknown")


# ------------------------------------------------------------------ World map: arms build-up and country tint
@st.cache_data
def arms_rolling(window=10):
    """Arms imports received in the `window` years up to each year, as a year x iso3 table on the full 1950-2025 grid
    (years without a delivery count as 0), like BUB.roll in app/site/adc.html."""
    p = load_panel()
    a = p.pivot_table(index="year", columns="iso3", values="arms_imports_tiv", aggfunc="sum")
    return a.reindex(range(1950, 2026)).fillna(0).rolling(window, min_periods=1).sum()


@st.cache_data
def arms_rolling_hosted(window=10):
    """arms_rolling() with historical states added to today's country (East Germany to Germany), as drawn on the map."""
    a = arms_rolling(window)
    return a.T.groupby(lambda iso: HISTORICAL.get(iso, iso)).sum().T


@st.cache_data
def regime_grid():
    """Regime type (0-3) per year x iso3; NaN where V-Dem has no data."""
    return load_panel().pivot_table(index="year", columns="iso3", values="regime_type", aggfunc="first").reindex(range(1950, 2026))


@st.cache_data
def buildup_rows(window=10):
    """World arms received in the `window` years to each year, split by the recipient's regime type in that year
    (columns 0-3, and 4 = no regime data). A historical state that no longer exists takes the regime of today's
    country, as buildRows() in app/site/adc.html."""
    a, reg = arms_rolling(window), regime_grid()
    out = pd.DataFrame(0.0, index=a.index, columns=range(5))
    for iso in a.columns:
        r = reg[iso] if iso in reg else pd.Series(np.nan, index=a.index)
        host = HISTORICAL.get(iso)
        if host and host in reg:
            r = r.fillna(reg[host])
        band = r.fillna(4).astype(int)
        for k in range(5):
            out[k] += a[iso].where(band == k, 0)
    return out


@st.cache_data
def main_suppliers(y, years=5):
    """{recipient iso3 (map country): main state supplier over the `years` years up to y}, the country tint of the
    Arms flows map (FL.tints in app/site/flows.js)."""
    f = load_flows()
    w = f[(f["year"] > y - years) & (f["year"] <= y) & ~f["supplier"].map(is_non_state)].copy()
    w["iso"] = w["recipient_iso3"].replace(HISTORICAL)
    s = w.groupby(["iso", "supplier"])["tiv"].sum()
    if s.empty:
        return {}
    return s.groupby(level=0).idxmax().map(lambda t: t[1]).to_dict()


# ------------------------------------------------------------------ Countries & compare page
DEMO = ROOT / "data" / "demo"
COMPARE_COLOURS = ["#3987e5", "#e66767", "#199e70", "#c98500", "#9085e9", "#d95926", "#2bb5c0", "#e07ab0", "#a3b54a", "#b98a68"]

# Preset country groups, same names and members as GROUPS in app/site/adc.html (category, name, members)
GROUPS = [
    ("Blocs and alliances", "Former Soviet Union", "RUS UKR BLR MDA EST LVA LTU GEO ARM AZE KAZ KGZ TJK TKM UZB"),
    ("Blocs and alliances", "Warsaw Pact (1955 members)", "RUS POL DDR CZE HUN ROU BGR ALB"),
    ("Blocs and alliances", "European Union (27)", "AUT BEL BGR HRV CYP CZE DNK EST FIN FRA DEU GRC HUN IRL ITA LVA LTU LUX MLT NLD POL PRT ROU SVK SVN ESP SWE"),
    ("Blocs and alliances", "NATO founders (1949)", "USA CAN GBR FRA BEL NLD LUX ITA PRT DNK NOR ISL"),
    ("Blocs and alliances", "G7", "USA CAN GBR FRA DEU ITA JPN"),
    ("Blocs and alliances", "BRICS (members from 2010)", "BRA RUS IND CHN ZAF"),
    ("Blocs and alliances", "UN Security Council (current P5)", "USA RUS CHN GBR FRA"),
    ("Blocs and alliances", "Gulf states", "SAU KWT BHR QAT ARE OMN"),
    ("Blocs and alliances", "Arab Spring countries", "TUN EGY LBY YEM SYR BHR"),
    ("Regions", "North America", "USA CAN MEX"),
    ("Regions", "Latin America", "MEX GTM HND SLV NIC CRI PAN CUB DOM HTI ARG BOL BRA CHL COL ECU PRY PER URY VEN"),
    ("Regions", "Central America and Caribbean", "GTM HND SLV NIC CRI PAN CUB DOM HTI JAM TTO BRB"),
    ("Regions", "South America", "ARG BOL BRA CHL COL ECU GUY PRY PER SUR URY VEN"),
    ("Regions", "Western Europe", "GBR IRL FRA BEL NLD LUX DEU AUT CHE ITA ESP PRT DNK NOR SWE FIN ISL GRC"),
    ("Regions", "Eastern Europe", "POL DDR CZE SVK HUN ROU BGR ALB EST LVA LTU UKR BLR MDA"),
    ("Regions", "Former Yugoslavia", "SRB HRV SVN BIH MNE MKD XKX"),
    ("Regions", "Middle East and North Africa", "MAR DZA TUN LBY EGY ISR PSE PSG JOR LBN SYR IRQ IRN SAU YEM YMD KWT BHR QAT ARE OMN TUR"),
    ("Regions", "West Africa", "NGA GHA CIV SEN MLI BFA NER GIN SLE LBR TGO BEN GMB GNB MRT CPV"),
    ("Regions", "East Africa and Horn", "ETH ERI SOM DJI KEN UGA TZA RWA BDI SDN SSD"),
    ("Regions", "Southern Africa", "ZAF NAM BWA ZWE ZMB MOZ MWI AGO LSO SWZ MDG MUS COM SYC"),
    ("Regions", "Central Africa", "CAF CMR COD COG GAB GNQ TCD STP"),
    ("Regions", "Central Asia", "KAZ KGZ TJK TKM UZB"),
    ("Regions", "South Asia", "IND PAK BGD LKA NPL BTN AFG MDV"),
    ("Regions", "East Asia", "CHN JPN KOR PRK TWN MNG"),
    ("Regions", "Southeast Asia", "IDN MYS PHL THA VNM VDR KHM LAO MMR SGP TLS"),
    ("Regions", "Oceania", "AUS NZL PNG FJI SLB VUT"),
]


@st.cache_data
def country_groups():
    """GROUPS as {name: [iso3, ...]}, keeping only countries that are in the panel (as the HTML version does)."""
    known = set(load_panel()["iso3"])
    return {name: [i for i in members.split() if i in known] for _, name, members in GROUPS}


@st.cache_data
def regime_spans():
    return pd.read_csv(CLEAN / "vdem_regime_spans.csv")


@st.cache_data
def conflict_runs():
    """Runs of consecutive years with the same conflict intensity (1 = minor, 2 = war) per country, from the panel."""
    p = load_panel()
    p = p[p["max_intensity"] > 0][["iso3", "year", "max_intensity"]].sort_values(["iso3", "year"])
    new = (p["iso3"] != p["iso3"].shift()) | (p["year"] != p["year"].shift() + 1) | (p["max_intensity"] != p["max_intensity"].shift())
    p["run"] = new.cumsum()
    return p.groupby("run").agg(iso3=("iso3", "first"), start=("year", "min"), end=("year", "max"),
                                intensity=("max_intensity", "first")).reset_index(drop=True)


@st.cache_data
def load_sup_dem():
    """Democracy of a country's arms suppliers per year (regression output of notebook 08).
    Returns (frame, is_placeholder): the demo file stands in until data/clean/reg_suppliers.csv exists."""
    real = CLEAN / "reg_suppliers.csv"
    if real.exists():
        return pd.read_csv(real), False
    return pd.read_csv(DEMO / "reg_suppliers.csv"), True


@st.cache_data
def vega_land_shapes():
    """Country shapes for Vega/Altair geoshape maps: GeoJSON features (lon/lat, about 0.1° precision, rings wound
    clockwise as d3-geo expects) with the iso3 code at the top level and in properties."""
    feats = []
    for ft in country_geojson()["features"]:
        polys = []
        for poly in ft["geometry"]["coordinates"]:
            r = np.round(np.array(poly[0]), 1)
            r = r[np.r_[True, np.any(np.diff(r, axis=0) != 0, axis=1)]]
            if len(r) < 4:
                continue
            x, yy = r[:, 0], r[:, 1]
            if (x * np.roll(yy, -1) - np.roll(x, -1) * yy).sum() > 0:
                r = r[::-1]
            polys.append([r.tolist()])
        if polys:
            iso = ft["properties"]["iso3"]
            feats.append({"type": "Feature", "iso3": iso, "properties": {"iso3": iso},
                          "geometry": {"type": "MultiPolygon", "coordinates": polys}})
    return feats


# ------------------------------------------------------------------ static files for fixed chart data
# Fixed data (country outlines, conflict stripes) is served from app/static/ (server.enableStaticServing in
# .streamlit/config.toml): the browser loads each file once and caches it, and a chart only names the file. Inline, it
# went to the browser again on every Play step and every click (about 0.3 MB on the World map, 1.2 MB on the compare
# page's arms-flows map), which is slow on Streamlit Cloud. The content hash in the file name makes browsers load a
# new file when the data changes.
STATIC = ROOT / "app" / "static"


@st.cache_resource
def static_url(name, _build):
    """Write the JSON of `_build()` to app/static/<name>.<hash>.json once, return its URL (relative to the page)."""
    body = json.dumps(_build(), separators=(",", ":"))
    path = STATIC / f"{name}.{hashlib.sha1(body.encode()).hexdigest()[:10]}.json"
    if not path.exists():
        STATIC.mkdir(exist_ok=True)
        path.write_text(body, encoding="utf8")
    return f"app/static/{path.name}"
