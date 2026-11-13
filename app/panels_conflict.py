"""Chart functions for regimes and conflicts. Owner: Nicolas.

At the top of this file, below this text, write:
    import pandas as pd
    import matplotlib.pyplot as plt
then paste the colour dictionaries from 07_charts.ipynb.

Then paste each function here unchanged from notebooks/07_charts.ipynb once it works there:
regime_bands(ax, spans, iso3, year=None)
conflict_bars(ax, spans, iso3, year=None)

Each function draws on the ax it receives and returns nothing. Once a function is here, this file
is the only place where you change it.
Only import a function into streamlit_app.py once it exists here, otherwise you get an ImportError.
"""



import pandas as pd
import matplotlib.pyplot as plt

regime_colours = {
    "closed autocracy": "#4C78A8",
    "electoral autocracy": "#F58518",
    "electoral democracy": "#54A24B",
    "liberal democracy": "#E45756",
}
intensity_colours = {"minor": "#F2C14E", "war": "#D62728"}


def regime_bands(ax, spans, iso3, year=None):
    rows = spans[spans["iso3"] == iso3].copy()
    for label, start, end in zip(rows["regime_label"], rows["start"], rows["end"]):
        ax.barh(0, end - start + 1, left=start, color=regime_colours[label])
    ax.set_xlim(1950, 2025)
    ax.set_yticks([])
    ax.set_title("Regime")
    if year is not None:
        ax.axvline(year, linestyle="--", color="grey")


def conflict_bars(ax, spans, iso3, year=None):
    intensity_names = {1: "minor", 2: "war"}
    rows = spans[spans["iso3"] == iso3].copy()
    if len(rows) == 0:
        ax.text(0.5, 0.5, "No conflict on record", transform=ax.transAxes, ha="center", va="center", color="grey")
    for intensity, start, end in zip(rows["max_intensity"], rows["start"], rows["end"]):
        label = intensity_names[intensity]
        ax.barh(0, end - start + 1, left=start, color=intensity_colours[label])
    ax.set_xlim(1950, 2025)
    ax.set_yticks([])
    ax.set_title("Conflict")
    if year is not None:
        ax.axvline(year, linestyle="--", color="grey")