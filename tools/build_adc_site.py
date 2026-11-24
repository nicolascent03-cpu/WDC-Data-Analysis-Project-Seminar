"""Refresh the website data from a new export of the prototype page.

Usage (from the repo root):
    python tools/build_adc_site.py "path/to/Conflict, Arms and Democracy.html"

The export carries its data in two <script type="application/json"> blocks ("data" and
"mapdata"). This script copies them to app/site/data.json and app/site/mapdata.json.
The page itself (app/site/adc.html) is edited by hand and is not touched.
"""

import os
import sys

SITE = os.path.join(os.path.dirname(__file__), "..", "app", "site")


def grab(html, block_id):
    start = html.find('<script type="application/json" id="%s">' % block_id)
    if start < 0:
        sys.exit("No %r block found in the export" % block_id)
    start = html.index(">", start) + 1
    return html[start:html.index("</script>", start)]


def main(src):
    with open(src, encoding="utf8") as f:
        html = f.read()
    for block_id, name in [("data", "data.json"), ("mapdata", "mapdata.json")]:
        out = os.path.normpath(os.path.join(SITE, name))
        with open(out, "w", encoding="utf8") as f:
            f.write(grab(html, block_id))
        print("Wrote", out)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
