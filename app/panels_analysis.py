"""Chart functions for democracy and the main result. Owner: Yair.

At the top of this file, below this text, write:
    import pandas as pd
    import matplotlib.pyplot as plt
then paste the colour dictionaries from 07_charts.ipynb.

Then paste each function here unchanged from notebooks/07_charts.ipynb once it works there:
democracy_line(ax, panel, iso3, year=None)
main_chart(ax, event_time)

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

# democracy_line: plots the democracy index of a single country over the whole time period
def democracy_line(ax, panel, iso3, year=None):
    country = panel[panel["iso3"] == iso3]
    ax.plot(country["year"], country["democracy_index"])
    ax.set_ylim(0, 1)
    ax.set_xlim(1950, 2025)
    ax.set_title(f"Democracy index of: {iso3}")
    ax.set_ylabel("0 to 1")
    if year is not None:
        ax.axvline(year, linestyle="--", color="grey")

#main chart: created a function that maps change in democracy index 
#            in the years before and after conflict, 
#            comparing between high and low importers
def main_chart(ax, event_time):
    for group, times in event_time.groupby("importer_group"):
        ax.plot(times["t"], times["dem_change"], label=group)
    ax.axvline(0, color="grey")
    ax.axhline(0, color="grey", linewidth=0.8)
    ax.set_xlabel("Years since conflict onset")
    ax.set_ylabel("Change in democracy index")
    ax.legend()

