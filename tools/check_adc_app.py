"""Smoke test for app/adc_app.py (the ADC website inside Streamlit).

Run from the repo folder:
    .venv/bin/python tools/check_adc_app.py

It runs the app without a browser (Streamlit's test tool), then builds the page the same way
the app does and checks it: no placeholder left, data files valid, every element id the page's
JavaScript looks up exists, page under 16 MB. It never changes any file.
"""
import ast
import json
import logging
import os
import re
import sys
import warnings

warnings.filterwarnings("ignore")
logging.disable(logging.WARNING)

from streamlit.testing.v1 import AppTest

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
APP = os.path.join(ROOT, "app", "adc_app.py")
SITE = os.path.join(ROOT, "app", "site")

failures, warns = [], []


def check(ok, msg):
    print(("  ok    " if ok else "  FAIL  ") + msg)
    if not ok:
        failures.append(msg)


# 1. Run the app.
print("Running the app")
at = AppTest.from_file(APP, default_timeout=60).run()
check(not at.exception, "app runs without exception" + (f": {at.exception}" if at.exception else ""))
check(len(at.get("iframe")) == 1, f"exactly one iframe (found {len(at.get('iframe'))})")

# 2. Build the page exactly like the app does (app/site_page.py), and check every placeholder is filled.
print("Building the page")
sys.path.insert(0, os.path.dirname(APP))
import site_page  # noqa: E402

template = open(os.path.join(SITE, "adc.html"), encoding="utf8").read()
for ph in ["__ADC_FLOWS_JS__", "__ADC_REG__", "__ADC_DATA__", "__ADC_MAPDATA__"]:
    check(ph in template, f"template contains placeholder {ph}")
page = site_page.assemble()
texts = {name: open(os.path.join(SITE, name), encoding="utf8").read() for name in site_page.SITE_FILES}
check("__ADC_" not in page, "no __ADC_ placeholder left in the page")
reg = json.loads(site_page.reg_json())
check(all(v in ("real", "demo") for v in reg["source"].values()), "regression results found: " + ", ".join(f"{k} = {v}" for k, v in reg["source"].items()))

for name, keys in [("data.json", ["y0", "y1", "countries", "conflicts", "suppliers", "finding"]),
                   ("mapdata.json", ["w", "h", "p"])]:
    try:
        missing = [k for k in keys if k not in json.loads(texts[name])]
        check(not missing, f"{name} parses, top-level keys present" + (f" (missing {missing})" if missing else ""))
    except (KeyError, ValueError) as e:
        check(False, f"{name} parses as JSON ({e})")

# Literal ids (not ones built by string concatenation) looked up by the page's JavaScript must exist as id="..." in the HTML.
js = "\n".join(re.findall(r"<script[^>]*>(.*?)</script>", page, re.S))
used = set(re.findall(r"getElementById\(\s*[\"']([^\"']+)[\"']\s*\)", js))
used |= set(re.findall(r"\$\(\s*[\"']#([\w-]+)[\"']\s*\)", js))
html_ids = set(re.findall(r"\bid=[\"']([^\"']+)[\"']", page))
missing_ids = sorted(used - html_ids)
for i in missing_ids:
    warns.append(f"id #{i} used in JS but not found in HTML")
print(f"  {'ok  ' if not missing_ids else 'WARN'}  {len(used)} ids used in JS, {len(missing_ids)} missing in HTML")
for w in warns:
    print("        " + w)

size = len(page.encode("utf8"))
check(size < 16 * 1024 * 1024, f"page size {size / 1e6:.2f} MB (< 16 MB)")

print()
print(f"{'FAIL' if failures else 'PASS'}: {len(failures)} failure(s), {len(warns)} warning(s)")
sys.exit(1 if failures else 0)
