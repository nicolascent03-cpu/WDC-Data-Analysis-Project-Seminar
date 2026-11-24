"""Reproject the site's world map (app/site/mapdata.json) from Natural Earth to Equal Earth.

Usage (from the repo root):
    python tools/reproject_map.py            # converts app/site/mapdata.json in place
    python tools/reproject_map.py --check    # only prints how well the Natural Earth fit matches

The exported map only has projected x/y coordinates. This script fits the Natural Earth
projection to known country positions, inverts it to longitude/latitude, and projects the
points again with Equal Earth (Savric, Patterson & Jenny 2018), an equal-area projection:
every country keeps its true relative size. The map is cropped to the land's latitude range plus a small margin.
The file gets "proj": "equal-earth", and the script refuses to convert it a second time.
"""

import json
import os
import re
import sys

import numpy as np

MAP = os.path.join(os.path.dirname(__file__), "..", "app", "site", "mapdata.json")

# Approximate centroids of each country's main landmass (lon, lat), used to fit the old projection.
CONTROL = {
    "USA": (-98.6, 39.8), "BRA": (-53, -10.8), "AUS": (134.5, -25.7), "RUS": (97, 62), "CHN": (103.8, 36.5),
    "IND": (79, 22.8), "ZAF": (25, -29), "ARG": (-65, -35.4), "CAN": (-101, 57), "EGY": (29.9, 26.5),
    "DEU": (10.4, 51.1), "KAZ": (67.3, 48.2), "NGA": (8.1, 9.6), "IDN": (113.9, -0.8), "MEX": (-102.5, 23.9),
    "NOR": (13, 64.5), "FIN": (26, 64.5), "CHL": (-71, -37), "NZL": (172.5, -41.5), "JPN": (138, 36.5),
    "MNG": (103, 46.8), "SAU": (44.5, 24), "PER": (-75, -9.2), "COD": (23.6, -2.9),
}
NUM = re.compile(r"(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)")


def ne_forward(lon, lat):
    p2 = lat * lat
    p4 = p2 * p2
    x = lon * (0.8707 - 0.131979 * p2 + p4 * (-0.013791 + p4 * (0.003971 * p2 - 0.001529 * p4)))
    y = lat * (1.007226 + p2 * (0.015085 + p4 * (-0.044475 + 0.028874 * p2 - 0.005916 * p4)))
    return x, y


def ne_inverse(x, y):
    lat = y.copy()
    for _ in range(25):  # Newton's method on the latitude polynomial
        p2 = lat * lat
        p4 = p2 * p2
        f = lat * (1.007226 + p2 * (0.015085 + p4 * (-0.044475 + 0.028874 * p2 - 0.005916 * p4))) - y
        df = 1.007226 + p2 * (3 * 0.015085 + p4 * (7 * -0.044475 + 9 * 0.028874 * p2 - 11 * 0.005916 * p4))
        lat = lat - f / df
    p2 = lat * lat
    p4 = p2 * p2
    lon = x / (0.8707 - 0.131979 * p2 + p4 * (-0.013791 + p4 * (0.003971 * p2 - 0.001529 * p4)))
    return lon, lat


def ee_forward(lon, lat):
    a1, a2, a3, a4 = 1.340264, -0.081106, 0.000893, 0.003796
    th = np.arcsin(np.sqrt(3) / 2 * np.sin(lat))
    t2 = th * th
    t6 = t2 ** 3
    x = 2 * np.sqrt(3) * lon * np.cos(th) / (3 * (9 * a4 * t6 * t2 + 7 * a3 * t6 + 3 * a2 * t2 + a1))
    y = th * (a1 + a2 * t2 + t6 * (a3 + a4 * t2))
    return x, y


def landmass_centroid(d):
    best = None
    for sub in d.split("M")[1:]:
        p = np.array([(float(a), float(b)) for a, b in NUM.findall(sub)])
        if len(p) < 3:
            continue
        x, y = p[:, 0], p[:, 1]
        x2, y2 = np.roll(x, -1), np.roll(y, -1)
        c = x * y2 - x2 * y
        area = c.sum() / 2
        if area and (best is None or abs(area) > abs(best[0])):
            best = (area, ((x + x2) * c).sum() / (6 * area), ((y + y2) * c).sum() / (6 * area))
    return best[1], best[2]


def fit_natural_earth(paths):
    """Find scale s and offsets tx, ty with x = tx + s*X, y = ty - s*Y (X, Y = Natural Earth)."""
    keys = [k for k in CONTROL if k in paths]
    xy = np.array([landmass_centroid(paths[k]) for k in keys])
    lonlat = np.radians(np.array([CONTROL[k] for k in keys]))
    X, Y = ne_forward(lonlat[:, 0], lonlat[:, 1])
    n = len(keys)
    A = np.zeros((2 * n, 3))
    A[:n, 0], A[:n, 1] = X, 1
    A[n:, 0], A[n:, 2] = -Y, 1
    target = np.concatenate([xy[:, 0], xy[:, 1]])
    (s, tx, ty), *_ = np.linalg.lstsq(A, target, rcond=None)
    err = np.sqrt(((A @ np.array([s, tx, ty]) - target) ** 2).reshape(2, -1).sum(0))
    return s, tx, ty, err.mean()


def main(check_only):
    with open(MAP, encoding="utf8") as f:
        m = json.load(f)
    if m.get("proj") == "equal-earth":
        sys.exit("mapdata.json is already in Equal Earth; nothing to do.")
    s, tx, ty, err = fit_natural_earth(m["p"])
    print("Natural Earth fit: scale %.2f, offset (%.1f, %.1f), mean error %.1f px" % (s, tx, ty, err))
    if check_only:
        return

    def to_lonlat(x, y):
        return ne_inverse((x - tx) / s, (ty - y) / s)

    # Crop: the latitude range of the land itself, plus the same empty band the old frame had.
    ys = np.array([float(b) for d in m["p"].values() for _, b in NUM.findall(d)])
    _, lats = to_lonlat(np.full(2, tx), np.array([ys.min(), ys.max()]))
    pad = np.radians(3.0)
    lat_top, lat_bot = np.minimum(lats[:1] + pad, np.pi / 2), np.maximum(lats[1:] - pad, -np.pi / 2)
    W = m["w"]
    margin = tx - s * ne_forward(np.array([np.pi]), np.array([0.0]))[0][0]  # keep the old side margin
    _, xmax = None, ee_forward(np.array([np.pi]), np.array([0.0]))[0][0]
    S = (W / 2 - margin) / xmax
    _, y_top = ee_forward(np.array([0.0]), lat_top)
    _, y_bot = ee_forward(np.array([0.0]), lat_bot)
    H = round(float(S * (y_top[0] - y_bot[0])), 1)
    TY = float(S * y_top[0])

    def convert(d):
        pts = NUM.findall(d)
        p = np.array([(float(a), float(b)) for a, b in pts])
        lon, lat = to_lonlat(p[:, 0], p[:, 1])
        lon = np.clip(lon, -np.pi, np.pi)
        lat = np.clip(lat, -np.pi / 2, np.pi / 2)
        X, Y = ee_forward(lon, lat)
        new = iter(zip(W / 2 + S * X, TY - S * Y))
        return NUM.sub(lambda _: "%s,%s" % tuple(("%.1f" % v).rstrip("0").rstrip(".") for v in next(new)), d)

    m["p"] = {iso: convert(d) for iso, d in m["p"].items()}
    m["h"] = H
    m["proj"] = "equal-earth"
    m["from_natural_earth"] = {"s": round(float(s), 4), "tx": round(float(tx), 3), "ty": round(float(ty), 3),
                               "S": round(float(S), 4), "TY": round(TY, 3), "W": W}
    with open(MAP, "w", encoding="utf8") as f:
        json.dump(m, f, separators=(",", ":"))
    print("Wrote %s: Equal Earth, %d x %s" % (os.path.normpath(MAP), W, H))


def convert_point(x, y, params):
    """Convert one old Natural Earth map point with the stored parameters (for hand-placed points)."""
    lon, lat = ne_inverse(np.array([(x - params["tx"]) / params["s"]]), np.array([(params["ty"] - y) / params["s"]]))
    X, Y = ee_forward(lon, lat)
    return round(float(params["W"] / 2 + params["S"] * X[0]), 1), round(float(params["TY"] - params["S"] * Y[0]), 1)


if __name__ == "__main__":
    main("--check" in sys.argv)
