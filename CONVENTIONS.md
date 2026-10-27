# Conventions

Every notebook and app file uses exactly these names for tables and files that are saved or shared between notebooks. Small helper variables inside one task (like `top3` or `totals`) do not need to be listed.

## Raw files (data/raw/)

| File | How to read |
| --- | --- |
| `UcdpPrioConflict_v26_1.xlsx` | `pd.read_excel(...)` |
| `trade-register.csv` | `pd.read_csv(..., skiprows=11, encoding="latin-1")` |
| `vdem/V-Dem-CY-Core-v16.csv` | `pd.read_csv(..., usecols=[...])`, local only (over 100 MB) |

## Clean files (data/clean/)

| File | Made by | Used by |
| --- | --- | --- |
| `crosswalk_gw.csv`, `crosswalk_sipri.csv` | 01 | 02, 04 |
| `ucdp_cy.csv` | 02 | 05 |
| `ucdp_spans.csv` | 02 | 07, app |
| `vdem.csv` | 03 | 05 |
| `vdem_regime_spans.csv` | 03 | 07, app |
| `sipri_cy.csv` | 04 | 05 |
| `sipri_suppliers.csv` | 04 | 07, app |
| `panel.csv` | 05 | 06, 07, app |
| `event.csv` | 06 | 06 Part C |
| `event_time.csv` | 06 | 07, app |

## Dataframes

| Name | Content |
| --- | --- |
| `crosswalk_gw`, `crosswalk_sipri` | UCDP code → iso3, SIPRI name → iso3 |
| `ucdp_raw`, `ucdp_long`, `ucdp_cy`, `ucdp_spans` | UCDP as loaded, one row per country per conflict-year, per country-year, conflict periods |
| `vdem_raw`, `vdem`, `vdem_regime_spans` | V-Dem as loaded, clean country-years, regime periods |
| `sipri_raw`, `sipri`, `sipri_cy`, `sipri_suppliers` | SIPRI as loaded, clean deliveries, per country-year, top 3 suppliers + Other |
| `panel` | final merged country-year table |
| `onsets`, `event`, `event_time` | analysis in 06 |

## Columns (always these names)

| Column | Meaning |
| --- | --- |
| `iso3` | 3-letter code from V-Dem `country_text_id`, merge key |
| `year` | integer |
| `country_name` | V-Dem name, for display |
| `gw_code`, `cow_code` | UCDP location code, V-Dem COW code |
| `conflict_active` | 0 or 1 |
| `n_conflicts` | number of conflicts in the country-year |
| `max_intensity` | 0 none, 1 = 25 to 999 deaths, 2 = 1000+ |
| `democracy_index` | V-Dem `v2x_polyarchy`, 0 to 1 |
| `regime_type`, `regime_label` | V-Dem `v2x_regime` 0 to 3 and its label |
| `arms_imports_tiv` | SIPRI TIV in millions, 0 if no deliveries |
| `supplier`, `tiv` | supplier name or "Other", TIV delivered |
| `start`, `end` | first and last year of a period |
| `recipient`, `category`, `status` | SIPRI recipient name, armament category, deal status |
| `conflict_id`, `intensity_level` | UCDP conflict id and intensity (1 or 2) |
| `onset_year` | year a conflict started (06) |
| `t` | years since conflict onset (0 = onset year) |
| `dem_change` | democracy index minus its value at t = -1 |
| `importer_group` | "high importer" or "low importer" |
| `n_countries` | number of onsets with a value at this `t` (06) |

## Shared chart settings

| Name | Content |
| --- | --- |
| `regime_colours` | one colour per regime label |
| `intensity_colours` | colours for "minor" and "war" |
| Timeline layout | x-axis 1950 to 2025, height 180, margins `dict(l=60, r=10, t=30, b=10)`, `fig.update_yaxes(automargin=False)`, legend above, short chart title, y-axis title with unit, no x-axis title |

## Decisions log

| Date | Notebook | Decision | Why |
| --- | --- | --- | --- |
|  | 05 | Missing SIPRI value = 0 | No delivery recorded means no imports |
|  | 05 | Missing UCDP value = 0 | No conflict recorded means no conflict |
|  |  |  |  |
