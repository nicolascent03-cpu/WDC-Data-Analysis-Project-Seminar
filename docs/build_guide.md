# Conflict, Democracy and Arms: Full Build Guide

Nicolas Centorame and Yair. As of 27 October 2026.

## Overview

You build one merged country-year dataset from three sources and show it in a three-page Streamlit app, finished and presented on Thu 12 Nov 2026. This guide walks through every step in order. You write the analysis code yourselves; the guide gives tasks, hints and checks.

**Research question:** What happens to democracy during and after armed conflict, and does it look different in countries that import many weapons?

| Dataset | File | What it gives you |
| --- | --- | --- |
| UCDP/PRIO Armed Conflict v26.1 | `UcdpPrioConflict_v26_1.xlsx` | Conflict years, intensity, location codes |
| V-Dem Country-Year Core v16 | `vdem/V-Dem-CY-Core-v16.csv` | Democracy index (`v2x_polyarchy`), regime type (`v2x_regime`) |
| SIPRI Arms Transfers, trade register 1950 to 2025 | `trade-register.csv` | Arms deliveries per recipient, supplier and year (TIV) |

**The finished app has three pages:**

1. **Overview:** world map and global trends, a year slider.
2. **Country page:** stacked timelines for one country: regime bands, conflict bars, democracy line, arms imports, top suppliers.
3. **Analysis page:** the main chart: average democracy in the years before, during and after a conflict starts, split into high and low arms importers.

**Deliverables:** GitHub repo with notebooks 00 to 07 and the app, `panel.csv`, a short report, slides and a 2-minute pitch plus demo.

## Ground rules

Nicolas owns conflict and regime data (14 sandbox tasks), Yair owns arms data plus the democracy line and the main result chart (15 sandbox tasks). The crosswalk, the merge, the event-window analysis and the app are done together.

| Part | Owner |
| --- | --- |
| 01 Crosswalk | Together (pair programming, Yair types) |
| 02 UCDP, 03 V-Dem, `app/panels_conflict.py` | Nicolas |
| 04 SIPRI, `app/panels_arms.py`, `app/panels_analysis.py` | Yair |
| 05 Merge, 06 Part B and C, `app/streamlit_app.py` | Together |
| 06 Part A, 07 charts | Each person for their own theme |
| Bonus feature | Together, split once you pick it |

**Sandbox, then main.** Each person experiments in their own sandbox notebook (`sandbox_nicolas.ipynb`, `sandbox_yair.ipynb`). Only code that works and that you understand moves into the numbered main notebook. Before moving it, check:

- [ ] It runs with Restart and Run All
- [ ] Names follow `CONVENTIONS.md`
- [ ] Every checkpoint cell passes
- [ ] You can explain each line to your partner

**Daily routine.** Pull before you start, commit small steps with clear messages, push when a step works, then tell your partner in one line ("Pushed 03, vdem.csv is ready"). Only one person edits `streamlit_app.py` at a time. Details in `docs/process_guide_daily_routine.pdf`.

**Two fixed sessions a week**, about 90 minutes each, for shared notebooks, code review (each explains their notebook) and planning.

**AI use.** Ask for hints and explanations. Do not ask for finished code. Paste your attempt and the error, ask "what is wrong, give a hint first". Log every use in `AI_LOG.md`.

**Code style.** We are learning, so we write simple code in small steps: one operation per line, loops and dictionaries where they make the logic clear, print the result after each step. More lines are fine.

## Step 0: Setup

Both laptops run the same environment and the same repo before any data work starts. Done when `00_setup_check.ipynb` passes on both machines.

1. **Install the tools on both laptops:** Python 3.11 or newer, VS Code with the Python and Jupyter extensions, Git, GitHub Desktop.
2. **Nicolas creates the repo** `conflict-arms-democracy` (private) and invites Yair and the tutors as collaborators.
3. **Nicolas clones it** to a simple path without spaces or cloud sync, for example `~/projects/conflict-arms-democracy`, copies the repo files from the zip into it, puts the UCDP and SIPRI raw files in `data/raw/`, then commits and pushes.
4. **Yair clones the repo** only after that push. He does not copy the zip a second time.
5. **Both:** create a virtual environment in the repo folder (`python3 -m venv .venv`), activate it (`source .venv/bin/activate`), then `pip install -r requirements.txt`.
6. **Both:** run `nbstripout --install` in the repo, so notebook outputs never get committed.
7. **Both:** download the V-Dem file (over GitHub's 100 MB limit, already in `.gitignore`) and put it in `data/raw/vdem/`.
8. **Both:** in VS Code, select the `.venv` kernel for every notebook.
9. **Both:** run `00_setup_check`.

## Steps 1 to 4: Clean each dataset

Each data notebook turns one raw file into a clean table in `data/clean/`. Order: 03 V-Dem first (01 uses `vdem.csv`), then 01 Crosswalk, then 02 and 04 (both use the crosswalks). Every notebook ends with a checkpoint cell and must pass Restart and Run All.

### 01 Crosswalk (together)

Goal: tables that translate UCDP codes and SIPRI names into `iso3`.

1. From V-Dem, build a list of `iso3`, `country_name`, `cow_code` (one row per country).
2. **`crosswalk_gw.csv`:** match UCDP Gleditsch-Ward codes to `iso3`. Most GW and COW codes are identical; list the ones that differ and fix them by hand in a small dictionary.
3. **`crosswalk_sipri.csv`:** match SIPRI recipient names to V-Dem names. About 31 SIPRI names need manual matching. Loop over the names, sort them into matched and unmatched, and write a dictionary for the unmatched ones.
4. Checkpoint: each code and name only once, every state-level SIPRI recipient has an `iso3`.

### 02 UCDP (Nicolas, sandbox Part B)

Goal: `ucdp_cy.csv` (one row per country-year) and `ucdp_spans.csv` (conflict periods for the timeline bars).

1. Load with `pd.read_excel`. Look at `conflict_id`, `year`, `gwno_loc`, `intensity_level`.
2. `gwno_loc` sometimes holds several codes ("500, 501"). Loop over the rows, split the text on the comma, and append one dictionary per code to a list; then build a dataframe from the list.
3. Add `iso3` from `crosswalk_gw` with a left merge. Check the row count before and after.
4. Two small groupbys by `iso3` and `year` (number of conflicts, highest intensity), merged together; `conflict_active` = 1.
5. Spans: a year-by-year loop; consecutive conflict years per country become one row with `start` and `end`.

### 03 V-Dem (Nicolas, sandbox Part A)

Goal: `vdem.csv` and `vdem_regime_spans.csv`.

1. Load only the six columns you need with `usecols`.
2. Keep years 1950 to 2025. Rename with a dictionary to the names in `CONVENTIONS.md`.
3. Add `regime_label` from `regime_type` with a dictionary and a loop.
4. A few units have no COW code (Palestine/West Bank, Palestine/Gaza, Somaliland, Hong Kong). Keep them; they just cannot be linked to UCDP.
5. Spans: a year-by-year loop; consecutive years with the same regime type become one row.

### 04 SIPRI (Yair, sandbox Part A)

Goal: `sipri_cy.csv` and `sipri_suppliers.csv`.

1. Load with `pd.read_csv(RAW + "trade-register.csv", skiprows=11, encoding="latin-1")`. Expect 62,009 rows and 17 columns.
2. Rename `Supplier`, `Recipient`, `Delivery year`, `TIV delivery values` to `supplier`, `recipient`, `year`, `tiv`.
3. Drop the 1,220 rows with no delivery year (ordered, never delivered). Then make `year` an integer.
4. Drop non-state recipients (names ending in `*`), organisations (`**`) and "unknown recipient(s)".
5. Add `iso3` from `crosswalk_sipri`. Sum `tiv` per `iso3` and `year` into `arms_imports_tiv`. Check India 2000 by hand.
6. Suppliers: a dictionary with each country's top 3 suppliers, then a loop that renames all others to "Other".

Zero is a real value here. A country with no deliveries in a year imported nothing, so it gets 0 in the merge, never a missing value.

## Step 5: Merge into panel.csv (together)

Do the merge practice in the sandboxes first.

1. Start from `vdem.csv`. It defines which country-years exist.
2. Left-merge `ucdp_cy` on `iso3` and `year`. Write down the row count before and after; it must stay the same.
3. Fill missing conflict values with 0: no row in UCDP means no conflict that year.
4. Left-merge `sipri_cy` on `iso3` and `year`. Fill missing `arms_imports_tiv` with 0.
5. Spot check Ukraine, Colombia and Switzerland by hand.
6. Save to `data/clean/panel.csv` and commit it.

Write each decision into the decisions log in `CONVENTIONS.md`.

## Step 6: Analysis (06_analysis)

Notebook 06 answers the research question with one main result: how average democracy moves from 5 years before to 10 years after a conflict starts, for high versus low arms importers. It saves `event_time.csv` for the app.

### Part A: Descriptives (each your own theme)

- **Nicolas:** share of country-years in conflict per regime type.
- **Yair:** top 15 importers by total TIV; arms imports over time by regime type; average democracy in conflict years versus peace years.

### Part B: Event window (together, the core of the grade)

1. **Find the onsets** with a loop: a year with `conflict_active == 1` after at least 2 years without conflict. Ask Justinas whether this definition is fine.
2. **Build the window:** for each onset, the same country from 5 years before to 10 years after, with `t` = years since onset.
3. **Measure the change:** `dem_change` = democracy index in year `t` minus the value at `t = -1`.
4. **Split by arms imports:** average TIV in the 5 years before onset; above the median = "high importer", otherwise "low importer".
5. **Average** `dem_change` per `t` and group, and count the countries per point.
6. Save as `data/clean/event_time.csv`.

### Part C: Checks and findings

- Does the result hold for wars only (`max_intensity == 2`)?
- How many onsets are in each group? Fewer than about 20 makes the lines unreliable; say so.
- Write 3 findings, one sentence each, with a number.
- Write one sentence on what the chart cannot show (it shows a pattern; it does not show a cause).

## Step 7: Chart functions (07_charts)

Every chart is a function that takes a dataframe (and a country code where needed) and returns a plotly figure. Build it in your sandbox, test it in 07, then copy it unchanged into the app.

| Function | Chart | Owner | Goes into |
| --- | --- | --- | --- |
| `regime_bands(spans, iso3, year=None)` | Coloured bands per regime period | Nicolas | `panels_conflict.py` |
| `conflict_bars(spans, iso3, year=None)` | Bars for each conflict period, colour by intensity | Nicolas | `panels_conflict.py` |
| `democracy_line(panel, iso3, year=None)` | Democracy index over time | Yair | `panels_analysis.py` |
| `main_chart(event_time)` | `dem_change` by `t`, one line per importer group | Yair | `panels_analysis.py` |
| `arms_line(panel, iso3, year=None)` | Arms imports (TIV) over time | Yair | `panels_arms.py` |
| `supplier_area(suppliers, iso3, year=None)` | Top 3 suppliers + Other, stacked by year | Yair | `panels_arms.py` |
| `world_map(panel, year, column)` | Choropleth for one year | Yair | `panels_arms.py` |

Rules: same x-axis 1950 to 2025 on all timelines, height 180, the same margins with `fig.update_yaxes(automargin=False)`, a short chart title, a y-axis title with unit and no x-axis title, a dashed line at the selected year, one shared colour system (see `CONVENTIONS.md`).

## Step 8: Streamlit app

You write all app code yourselves. Each of you does the 16 exercises in your own `app/try_streamlit_<name>.py` first (basics, then country search, metrics, stacked timelines, colours, remembering the choice, theme), then follow the numbered steps in `app/streamlit_app.py`. Run it from the repo root with `streamlit run app/streamlit_app.py`. The app only reads files from `data/clean/`; it never cleans data.

Checkpoint: all three pages load for any country without an error, including countries with no conflicts and no arms imports.

## Step 9: Bonus feature

Pick one and build it well. Confirm the choice with Justinas.

| Option | What it does | Effort |
| --- | --- | --- |
| Country comparison (recommended) | Two countries side by side on the same stacked timelines | Medium |
| Play button | The world map animates through the years | Low to medium |
| Map click to country | Clicking a country on the map opens its country page | Medium to high |

Build it in a try_streamlit file first, add it to the app only after both of you reviewed it, and describe it in the README in two sentences.

## Step 10: Finish and deliver

Feature freeze is Mon 9 Nov; after that you only fix bugs, write and rehearse.

**Clean-clone test.** Clone the repo into a new folder, create a fresh environment, put the V-Dem file in place, run notebooks 00, 03, 01, 02, 04, 05, 06, 07, then start the app.

**Presentation (2 minutes plus demo):** question (15 s), data and merge (20 s), live demo (60 s), main finding and caveat (15 s), bonus (10 s). Each of you presents your own theme. Rehearse twice with a timer.

**Report outline:** question; data and cleaning decisions; method; findings with the main chart; limitations; next steps.

## Timeline and cut list

| Week | Dates | Nicolas | Yair | Together |
| --- | --- | --- | --- | --- |
| 1 Data | Thu 22 to Wed 28 Oct | 03 V-Dem, 02 UCDP, try_streamlit Ex 1 to 4 | 04 SIPRI, try_streamlit Ex 1 to 4 | Setup, 01 Crosswalk, 05 Merge |
| 2 Analysis and app | Thu 29 Oct to Wed 4 Nov | 06 A, 07 regime and conflict charts, try_streamlit Ex 5 to 16 | 06 A, 07 arms charts, map, democracy line and main chart, try_streamlit Ex 5 to 16 | 06 B and C, app, bonus choice |
| 3 Polish and deliver | Thu 5 to Thu 12 Nov | Bonus half, slides, report | Bonus half, slides, report | Freeze Mon 9, rehearsals |

If you fall behind, cut in this order: deployment, suppliers timeline, world map, wars-only check. Never cut the checkpoints, the decisions log or the main chart.

## Troubleshooting

| Problem | Likely cause | Fix |
| --- | --- | --- |
| `UnicodeDecodeError` reading SIPRI | Wrong encoding | `encoding="latin-1"` |
| SIPRI columns named `Unnamed: 0` | Header not on the first line | `skiprows=11` |
| Row count grows after a merge | Duplicate keys on the right side | Check `duplicated(["iso3", "year"]).sum()` first |
| Many missing values after a merge | Key types differ (int vs float vs text) | Compare `dtypes`, convert both with `astype(int)` |
| `ModuleNotFoundError` in Jupyter | Notebook uses a different Python | Select the `.venv` kernel in VS Code |
| `FileNotFoundError` in the app | The CSV does not exist yet (its notebook has not run) | Run the notebook that writes it, or load only files that exist |
| GitHub refuses the push | A file over 100 MB | Remove it from the commit, add it to `.gitignore` |
| Merge conflict in a notebook | Outputs committed or both edited it | `nbstripout --install`; one owner per notebook |
