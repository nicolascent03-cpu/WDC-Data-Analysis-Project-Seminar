"""Chart functions for arms imports. Owner: Yair.

At the top of this file, below this text, write:
    import pandas as pd
    import matplotlib.pyplot as plt
then paste the colour dictionaries from 07_charts.ipynb.


Then paste each function here unchanged from notebooks/07_charts.ipynb once it works there:
arms_line(ax, panel, iso3, year=None)
supplier_bars(ax, suppliers, iso3, year=None)
global_trends(ax, panel, year=None)

Each function draws on the ax it receives and returns nothing. Once a function is here, this file
is the only place where you change it.
Only import a function into streamlit_app.py once it exists here, otherwise you get an ImportError.
"""
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter


regime_colours = {
    "closed autocracy": "#4C78A8",
    "electoral autocracy": "#F58518",
    "electoral democracy": "#54A24B",
    "liberal democracy": "#E45756",
}
intensity_colours = {"minor": "#F2C14E", "war": "#D62728"}
#arms line
def arms_line(ax, panel, iso3, year=None): 
    rows = panel[panel["iso3"] == iso3]
    ax.bar(rows["year"], rows["arms_imports_tiv"])
    ax.set_xlim(1950, 2025)
    ax.set_title("Arms imports")
    ax.set_ylabel("TIV, millions")
    if year is not None:
        ax.axvline(year, linestyle="--", color="grey")

#supplier bars over time for a single country
def supplier_bars(ax, suppliers, iso3, year=None):
    country = suppliers[suppliers["iso3"] == iso3]
    wide = country.pivot(index="year", columns="supplier", values="tiv").fillna(0)
    if wide.empty:
        ax.set_title(f"Suppliers of: {iso3}")
        ax.text(0.5, 0.5, "No arms imports recorded", transform=ax.transAxes, ha="center")
        return
    else:
        bottom = [0] * len(wide)
        for product in wide.columns:
            ax.bar(wide.index, wide[product], bottom=bottom, label=product)
            bottom = [b + v for b, v in zip(bottom, wide[product])]

        ax.set_title(f"Top suppliers of {iso3}")
        ax.set_ylabel("TIV, millions")
        ax.set_xlim(1950, 2025)
        if year is not None:
                ax.axvline(year, linestyle="--", color="grey")
        ax.legend(fontsize=7, loc="upper left" )

#share of countries in active conflict over time
def global_trends(ax, panel, year=None):
    conflict_active = panel.groupby("year", as_index=True).agg(share=("conflict_active", "mean"))
    ax.plot(conflict_active)
    ax.yaxis.set_major_formatter(PercentFormatter(xmax=1))
    ax.set_xlim(1950, 2025)
    ax.set_title("Share of countries in conflict")
    ax.set_ylabel("share")
    ax.axvline(2000, linestyle="--", color="grey")