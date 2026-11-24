# ADC app: Arms, Democracy and Conflict

Short guide to the finished website inside Streamlit. For the team and the lecturer. As of 24 November 2026.

## How to run

From the repo root, with the project `.venv` active:

```
source .venv/bin/activate
streamlit run app/adc_app.py
```

The app opens in the browser. It needs no notebooks to run first: all data it shows is already in `app/site/`.

## How it is built

| File | What it holds |
| --- | --- |
| `app/adc_app.py` | The Streamlit script. Reads the four files below, puts them together and shows the result in an iframe. |
| `app/site/adc.html` | The page itself: CSS, HTML for all pages, and the JavaScript that draws the charts. |
| `app/site/data.json` | Country data: regimes, democracy index, conflicts, arms imports, suppliers, the main finding. |
| `app/site/mapdata.json` | The country shapes for the world map. |
| `app/site/flows.js` | The arms-flows layer of the map (supplier to recipient arcs per year). |

`adc.html` has three placeholders: `__ADC_DATA__`, `__ADC_MAPDATA__` and `__ADC_FLOWS_JS__`. `adc_app.py` replaces them with the file contents. The result is cached and rebuilt when any of the four files changes, so after an edit you only reload the page.

**Why one HTML template and not Streamlit widgets.** The site needs things Streamlit widgets do not do well: one shared year axis across stacked timelines, a clickable world map, tooltips, an animated year slider and switching pages without a rerun of the script. In plain HTML and JavaScript all of this runs in the browser and stays fast. Streamlit only serves the page.

**Where to edit what** (all in `app/site/adc.html`):

- **Look and layout:** the `<style>` block at the top. Colours and spacing are CSS variables (`--ink`, `--accent`, `--sp-3`, ...) at its start.
- **Text and page structure:** the HTML sections `<!-- START -->`, `<!-- OVERVIEW -->`, `<!-- COUNTRY -->` and `<!-- NOTES -->`. The data notes are plain text there.
- **Behaviour and charts:** the `<script>` block at the end, split into parts marked `// ---------- ...`.
- **Preset country groups:** the `GROUPS` list in the script. Each entry has a heading (`g`), a name (`n`) and space-separated country codes (`l`). Codes missing from the data are skipped.
- **Arms-flows layer:** `app/site/flows.js` (supplier name fixes, supplier colours, how many arcs are drawn).

## What a user can do

| Page | What you can do |
| --- | --- |
| **Start** | Read the research question, see a small regime map of one year with key numbers, jump to the world map or a country timeline, or open a preset group directly. |
| **World map**, Regimes mode | Pick a year from 1950 to 2025 with the slider, or press Play to run through the years. Countries are coloured by regime type; countries in active conflict are hatched (button to turn this off). Hover for details, click a country to open its timeline. Next to the map: the main finding (democracy change around conflict onset, high vs. low arms importers) with a "Show the numbers" table. |
| **World map**, Arms flows mode | Same year slider and Play button. The map draws arcs from supplier to recipient for the largest deliveries of that year, coloured by supplier (USA, Soviet Union, Russia, UK, France, Germany, China, other). Key numbers for the year: total TIV, number of transfers, top supplier and recipient (check). Hover a country for its imports and exports (check). |
| **Countries & compare** | One country on one shared year axis: regime bands, democracy index, armed conflicts, arms imports and top suppliers. Move the year marker with the slider or by clicking a chart; pick a period (all years, Cold War, since 1992). Search for any country in the top bar, including historical states like East Germany. |
| Comparing | Add countries with "Add a country to compare", or pick a preset group (EU, NATO founders, BRICS, Latin America, ...) from the drop-down. Each country gets its own colour; countries can be hidden in the democracy chart (check). "Clear comparison" goes back to one country. |
| Enlarging a chart | Each chart on the country page has an enlarge button that makes it about 2.4 times taller; press it again to shrink it. |
| **About the data** | Prototype status, how the pipeline joins the three sources, how the main finding is computed, and caveats. |

The address bar keeps the current page and countries (after `#`), so a view can be bookmarked or sent to someone (check).

## Updating the data

`tools/build_adc_site.py` refreshes `data.json` and `mapdata.json` from an HTML export of the prototype page:

```
python tools/build_adc_site.py "path/to/Conflict, Arms and Democracy.html"
```

It copies the two JSON blocks from the export and does not touch `adc.html`.

`tools/export_adc_data.py` is being written now. It will build `data.json` directly from our own results in `data/clean/` and may replace `build_adc_site.py`. Once it exists, use it after re-running the notebooks.

## Known limits

- **Prototype data.** The numbers come from a test run of the notebooks, not from our final results. Check every number against the notebooks before quoting it (this matters until `export_adc_data.py` is in use).
- **Today's borders.** The map uses current country shapes. Historical states (East Germany, South Yemen, Soviet Union as supplier, ...) are drawn at today's country or are only in the search. Very small states have no shape and appear grey.
- **Only the largest arms flows.** The flows mode draws the largest flows of each year (60 by default), not all transfers. Small transfers count in the totals but have no arc.
