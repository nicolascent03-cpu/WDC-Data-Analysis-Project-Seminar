# Changelog: Nicolas

What I changed in the project, on which date, and why. Newest first.

Sources: the git history of `nicolascent03-cpu` and my requests in the chat with Claude (Claude Code) while building
the Streamlit app.

- **"Why" in quotation marks:** my request from the chat, word for word.
- **"Why" without quotation marks:** taken from the commit message and the files the commit changed.
- **Not included:** Yair's commits (YairK3), except where my work builds on them.

---

## 2026-11-28 · App on Yair's finished notebook 08, ready to deploy

**What changed:**
- **Pulled Yair's finished notebook 08** (Parts 0, A and C done), with the real result files: `reg_results.csv` (A1 and C3), `reg_suppliers.csv` and `sipri_flows.csv`. All results in the app are now real, and no placeholder warning shows.
- **Findings:**
  - shows the notebook's Part C interpretation under "Who supplied the arms (C)";
  - notes that Parts B and D (optional) were not done.
- **FAQ:** the question about placeholder numbers is now "Are the results on the Findings page final?".
- **Removed `tools/export_reg_a1.py`.** The notebook now writes `reg_results.csv` itself and says not to run the script any more. Running it would have overwritten the real file with A1 only.
- **`requirements.txt`:** `streamlit>=1.66` instead of `>=1.50`. The app uses features of recent Streamlit, such as the year bar pinned to the bottom, and Streamlit Cloud installs from this file.

**Why:** "how to run it on streamlit cloud", "is the newest version the one in github?" and "Yes, do all three" (pull Yair's results, check the app with them, then push).

## 2026-11-25 · Real regression results, no more high vs low importers

**Commit `d7e07d6`:** Findings shows the real Part A results of notebook 08.

**What changed:**
- The main finding is regression A1:
  - It explains the change in the democracy index 1 to 10 years after a conflict onset by the onset and by onset × arms imports.
  - Arms imports are the mean of the 5 years before onset, standardised.
- `tools/export_reg_a1.py` (new) saves the A1 results as `data/clean/reg_results.csv`:
  - It runs the notebook's own code, cell for cell: cells 3 to 10, 15 and 17.
  - It also saves the 95% interval of b1 + b2, from the covariance.
  - The notebook itself only writes this file in Part G, which is not done yet.
- The event study is the stacked event study A3, from the notebook's own file `data/clean/reg_eventstudy.csv`, all onsets only.
- The notebook's written interpretations of A1 and A3 appear under each result as "What it means". The sentence comparing high and low importers is left out.
- The placeholder warning names only the parts that are still placeholders (who supplied the arms, Part C). About and the FAQ say the same.
- Every mention of a high vs low importer split is removed from the app, including the unused event-study groups and the old comparison loader.
- `linearmodels` is installed in the environment. It was already in `requirements.txt`.

**Why:** "new push, include all new findings points and tell me what you used. and as i said before no more high vs low importer". Before this, I had pulled Yair's commits that finish Part A of notebook 08: `f65883f`, `6045ec7` and `dd74af3`.

## 2026-11-25 · Arms flows map size, logo, menu, page switching

**Commit `cc8ee56`:**
- **Arms flows map:** now the same size as in the other two modes, with the 10 largest suppliers beside it and the chord ring in its own row below.
  - Why: "arms flow is smaller now"
- **Logo and menu:**
  - The logo is on two lines, so the name reads larger.
  - The base font is 16 px instead of 15, so the sidebar menu is larger.
  - Why: "the title and tabs can be more prominent"
- **Year bars:** both stay on one line (the slider shrinks instead).
- **World map legend:** a sans-serif fallback, because it showed in a serif font.
- **Compare scatter, followed countries:** the "Follow" list is kept when you switch pages. Streamlit deleted the widget's value on another page, so the scatter came back with no paths and no labels.
  - Why: "sometimes go back and forth in tabs and reload and a graphic doesnt load even after waiting"

## 2026-11-25 · World map like the HTML, but bigger

**Commit `8fd8b6f`:**
- **One map for all three modes:**
  - The same map, projection and size in Regimes, Arms flows and Arms build-up.
  - Its height follows its width, so it is larger than in the HTML version.
  - The side panel sits beside the map, and the river of time runs at full width below.
  - Why: "why cant in world map all maps of the three settings show the same kind of map and not like 3 different maps tht all look different and have different sizing etc???" and "why are our main maps so small? in the html they were so much bigger and prominent".
- **Main finding card:** now regression A1.
- **Hover:** cheaper. Only the hovered country's outline is redrawn, not the whole map.
  - Why: "when hovering over the maps the popup is still very laggy when you hover over a country and the data changes, fix that"
- **Year bar:** "Year", the large year number and "Period", as in the HTML.

## 2026-11-25 · Closer to the HTML version

**Commit `5fe1fe6`:**
- **Main finding:** regression A1 replaces the high vs low importer comparison (split at the median).
  - Why: "our low vs high importer seperation is still bs and depends on an arbitrary border weve set, replace that with the regression and our main finding will be the regression"
- **Menu:**
  - The page menu moved from the top bar into the sidebar.
  - The menu no longer jumps sideways between pages.
  - Glossary & FAQ is a tab inside About the data.
  - Why: "these move depending on which menu were in i dont liek that" and "put glossary faq into the about the data tab so the menu side left isnt redundant and is the primary one".
- **Logo and search:** the ADC logo of the HTML and a "Search a country" box in the sidebar.
- **Countries & compare:** rebuilt in the order and layout of the HTML version.
- **Glossary and FAQ:**
  - The glossary is one calm reading column.
  - The FAQ is themed cards with short answers.
  - Why: "the glossary is still super ugly and not readable well its all cluttered" and "the faq is so lame and unreadable wall of text its horrible".
- **Theme:** the heading sizes, number size, link colour and country colours of the HTML. Start and Findings no longer use Plotly.
- **Start page:** the preview map fills its card.
- **About:** the cards are in two columns as in the HTML. The onset definition is corrected to "after two years without conflict", as in notebooks 06 and 08.
- **Why for this whole round:** "the html is still miles better, fix everything possible in streamlit" and "compare everything against the html".
  - I also asked for two control agents that compare the Streamlit app against the HTML: "run 2 control agents: everything that was in the html with the whole look and feel should be tried and tested to be made in streamlit".

## 2026-11-25 · Compare page fixes, Play bar at the bottom

**Commit `3e15782`:**
- **Regime chart:** no longer empty for a single country. The legend had taken all of its height.
  - Why: "why is this empty??"
- **Compare scatter, whole path:** when paused, the scatter shows each followed country's whole path. Older years are fainter, and newer stretches are drawn on top so overlapping parts stay readable.
  - Why: "there should be the case that under like pause or another view it shows the whole snake and like fade from old to new so the older the less visible while still visible with layers being easily readable even when its like back and forth over each other"
- **Play bar:** Play, speed, year slider and period are pinned to the bottom of the screen with `st.bottom`.
  - Why: "no possibility to make the play button fixed at the bottom of the users screen?"
- **FAQ:** themed cards.

**Commit `5f4076f`:**
- **Compare scatter:** it was blank. Numbers in a format Vega could not read (`np.float64(...)`) had got into its axis labels.
  - Why: "push then check again" (the check found it)

## 2026-11-25 · Smooth Play without flicker

**Commit `ba1e8e9`:**
- **Charts:** all charts that change with the year on World map and Countries & compare are now Altair. Only the year moves, so Play no longer rebuilds them.
- **Year controls:** the compare page has its year controls in the page instead of the sidebar.
- **Why:** "anywhere else where we can increase fluidity with streamlit?" and "Yes, do 1–3".

**Commit `d986871`:**
- **Compare scatter:** "Democracy vs. arms imports" is now Altair, so it no longer flickers when the year changes.
- **Why:** "is there no ingenous solution to fix the democracy vs arms import graphic not flickering as much, so like something below loads once and assets load above it so it flickers less"

## 2026-11-25 · Glossary redesign, faster compare

**Commit `c1df0b2`:**
- **Glossary:** in tabs, with a regime scale and a conflict ladder.
  - Why: "fix the glossary and faq page its horrendous looking"
- **Big selections in compare:** much faster (from about 2 minutes to about 1.5 seconds for all countries), with a loading bar. New "All countries" preset.
  - Why: "for many countries add a bar load overlay like for all countries it loads forever and lags and bugs"
- **Polish:** small changes on Start and the World map.

## 2026-11-24 · Glossary & FAQ page, conflict counts

**Commit `465c8e9`:**
- **Glossary & FAQ page:** new. It defines political regimes, conflict types and arms terms, and has a FAQ.
  - Why: "glossary about definitions on political regimes, war types etc and faq"
- **River headline:** in Regimes mode it shows both counts: countries in armed conflict, and countries at war.
  - Why: "put of them in war over this or if we have more than one definiton both"
- **Compare and Findings:** made closer to the HTML version.
  - Why: "run two agents so we get clean ui and ux and maybe something is missing when it was translated to streamlit or not working fully and correct that, never add html we cant use more of it"

## 2026-11-24 · Native Streamlit version of the website

**Commit `070b8be`:**
- **The app:** a native Streamlit app (`app/native_app.py` with pages in `app/native_pages/`). It has the same pages as the HTML website: Start, World map, Findings, Countries & compare, About the data.
- **HTML:** none on the pages themselves.
  - Two small custom components draw what Streamlit cannot: the chord ring, and the regime map with striped conflict countries.
  - Rule from then on: "never add html we cant use more of it".
- **Why:** the HTML website inside Streamlit was not allowed ("they dont want us to use html").

**Commit `be09916`:** progress PDF and preview settings (local files).

## 2026-11-24 · HTML website and notebook 08

These commits come before the Streamlit rebuild. The reasons are taken from the commit messages.

- **`edd4172`, `bf0ca7b`:** the ADC website as one HTML page shown in Streamlit (`app/adc_app.py`, `app/site/`), with its data export and map reprojection tools. The regression guide for Yair was added too.
- **`eebc88e`:** the same year bar on World map and Countries & compare: Play, speed, slider, period.
- **`7ab64ca`:** World map selection tray, zoom (+, −, Fit, pinch) and pan.
- **`440d0db`:** the guided notebook `08_regressions.ipynb`, with tasks and checkpoints and empty code cells for Yair.
- **`ea55ab3`:** the Findings page and the supplier views, with placeholder results (`data/demo/`) until notebook 08 is done.
- **`6c2b67e`, `eb95dc9`, `33d82cc`:**
  - layout fixes for the conflict and supplier lists;
  - messages when there is no data;
  - ticking countries to follow them in the scatter;
  - a country card and a richer tooltip on Arms flows.
- **`5d41d6e`:** website data (`adc_data.json`) and preview settings.

## 2026-11-16 to 2026-11-18 · First app tries

- **`23d3a50` (2026-11-16):** test website (`app/try_streamlit_nicolas.py`).
- **`c95bf5b`, `9837e82` (2026-11-17):** removed a duplicate build file that had been saved with the command in its name.
- **`f50e9cf` (2026-11-17):** `requirements.txt` updated.
- **`f8257d5`, `cdf7111`, `86e29b6` (2026-11-17 and 18):** worked through the app guide notebook (`app_guide_nicolas.ipynb`, up to task 6) and copied the result into `app/build_nicolas.py`.
- **`56e4d58` (2026-11-17):** build checker (`tools/check_build.py`) to test the app build.
- **`ae93574` (2026-11-17):** AI log update.
- **`639a7d7` (2026-11-18):** sandbox test.

## 2026-11-12 to 2026-11-14 · Merge, analysis and a first Streamlit start

- **`54e992e` (2026-11-12):** sandbox check.
- **`1b21373`, `a5c80c8` (2026-11-13):** copied the code out of the sandboxes into the main notebooks (02 UCDP, 03 V-Dem, 07 charts) and into `app/panels_conflict.py`.
- **`d8a0005` (2026-11-13):** notebook 07 charts.
- **`9c0f46c` (2026-11-14):** a basic start in Streamlit (`app/streamlit_app.py`) and the Streamlit skill, plus the first `panel.csv`.
- **`a0accf7`, `7172632` (2026-11-14):** worked on the merge (05) and the analysis (06), including the event files `event.csv` and `event_time.csv`, plus CONVENTIONS and the AI log.
- **`4d0b958`, `b5b4a64` (2026-11-14):** checked an overlap in the merge, then used Yair's version of 05.
- **`409e0db`, `f34c50b` (2026-11-14):** Yair's sandbox and the 06 analysis notebook.

## 2026-11-02 to 2026-11-12 · Data cleaning

- **`1d9fe1a` (2026-11-02):** added the raw UCDP (v26.1) and SIPRI (trade register) files.
- **`c5338de`, `5d15413`, `746c4e7`, `342dfa1` (2026-11-02):** sandbox progress through parts A and B. This made the V-Dem tables `vdem.csv` and `vdem_regime_spans.csv`, with notes in the AI log.
- **`0526c47`, `d2bbb2b` (2026-11-04 and 05):** the crosswalk notebook (01), making `crosswalk_gw.csv` and `crosswalk_sipri.csv`, to join the three sources on one country code.
- **`7eca524`, `e4e9c7a` (2026-11-05):** UCDP country-years and spans (`ucdp_cy.csv`, `ucdp_spans.csv`), descriptives, up to D2 in the sandbox.
- **`f430b54` (2026-11-12):** finished my sandbox and the crosswalk notebook.

## 2026-10-27 to 2026-10-28 · Project setup

- **`77d800a` to `ef98da4` (2026-10-27):**
  - created the repository and its folder structure (`app/`, `data/raw/`, `data/clean/`, `docs/`, `notebooks/`);
  - uploaded README, CONVENTIONS, AI log, requirements, the build guide, the daily routine guide, the notebooks 00 to 07, the sandboxes and the first app files.
- **`dd613a1` (2026-10-28):** rewrote the code to fit our skills and what was covered in the lectures.
- **`49ef866`, `52c8522` (2026-10-28):** edited `.gitignore` (local V-Dem raw file, environment, secrets) and updated the AI log.
