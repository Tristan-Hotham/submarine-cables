"""Step 7. README.md and LICENSE, numbers from data/results.json.
Run: python3 code/07_readme.py
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

R = jload(f"{DATA}/results.json"); Z = R["zone"]; H = R["hyper"]
kb = lambda f: f"{os.path.getsize(os.path.join(DATA, f)) // 1024:,} KB"
isl = ", ".join(s["country"] for s in R["single"] if s["island"])
readme = f"""# The internet's seabed

Every submarine cable in TeleGeography's open Submarine Cable Map (2026): when each was laid, who owns it, and the straits and landing hubs where cables crowd together. {R['n_active']} cables in service ({R['km_active']:,} km) and {R['n_planned']} planned ({R['km_planned']:,} km), landing at {R['n_landing_points']:,} points in {R['n_countries']} countries and territories.

Interactive page: https://maps.tristanhotham.com/submarine-cables/
Paper: {{https://doi.org/10.5281/zenodo.23856607}}
Blog post: {{https://blog.tristanhotham.com/2026/10/31/submarine-cables/}}

## Headline results

- When they were laid: the oldest cables still in service date from {R['first_year']}. {R['dotcom_n']} of today's cables came into service in the dot-com boom of 1999 to 2001, and {R['km_peak_year']} is still the year with the most kilometres ({R['km_peak']:,} km). Only {R['bust_n']} followed in 2002 to 2004. The busiest year for new cables was {R['peak_year']} ({R['peak_n']}), and {R['n_2027']} are planned for 2027.
- Who owns them: Google, Meta, Amazon (Amazon Web Services) and Microsoft part-own none of the cable length ready before 2010, {round(H['share_km_1015'] * 100)}% of the length ready in 2010 to 2014, {round(H['share_km_1519'] * 100)}% in 2015 to 2019, {round(H['share_km_2020s'] * 100)}% in 2020 to 2026 and {round(H['share_planned_km'] * 100)}% of the planned length. {H['sole']} of their {H['n']} cables have no other owner.
- Choke points: {Z['sicily']['n_active']} cables in service cross the Strait of Sicily, {Z['redsea']['n_active']} the Red Sea at 20° N and {Z['bab']['n_active']} the Bab el-Mandeb (combined length {Z['bab']['km_active']:,} km, {round(R['bab_share_km'] * 100)}% of all cable length in service); {Z['egypt']['n_active']} cross Egypt overland. {Z['singapore']['n_active']} cables reach the sea within 35 km of Singapore ({Z['singapore']['n_planned']} more planned); the busiest half-degree cell, off Singapore, is crossed by {R['grid_max']}.
- Most and least connected: the United States has {R['top_countries'][0]['n']} international cables, the United Kingdom {R['top_countries'][1]['n']} and Singapore {R['top_countries'][2]['n']}. {R['n_single']} countries and territories have one; {R['n_single_island']} of these are islands with no land border: {isl}. Tuvalu appears only on a planned cable. {R['n_lp_single']:,} of {R['n_lp_active']:,} landing points in service ({round(R['lp_single_share'] * 100)}%) serve one cable.

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/04_build_site.py`); loads `data/site.json`, `data/cables.geojson`, `data/chokepoints.geojson` and, on demand, `data/grid_density.png`. |
| `header.png` | Social card, 1200 x 630. |
| `data/cables.csv` | {R['n']} cables: ready-for-service date and year, status, era, length (stated or measured), landing and country counts, countries, owners, cloud-company owners, suppliers ({kb('cables.csv')}). |
| `data/cables.geojson` | Cable routes, lightly simplified, keyed by cable id ({kb('cables.geojson')}). |
| `data/landing_points.csv`, `.geojson` | {R['n_landing_points']:,} landing points with cables in service and planned. |
| `data/countries.csv` | Countries and territories: international and domestic cables in service, planned cables, landing points, land border. |
| `data/chokepoints.csv`, `.geojson` | {R['n_straits']} straits and corridors and {R['n_hubs']} hubs: definition, cables in service and planned, combined length, cable ids; the bands and areas used. |
| `data/grid_cells.csv`, `data/grid.json`, `data/grid_density.png` | Distinct cables crossing each half-degree cell. |
| `data/timeline.csv` | Cables and kilometres per ready-for-service year, cumulative, and part-owned by the four cloud companies. |
| `data/hyperscalers.csv` | The {H['n']} cables with Google, Meta, Amazon Web Services or Microsoft among their owners. |
| `data/results.json` | Every number used in the page, paper, blog and collage. |
| `data/site.json` | Page data. |
| `code/` | Scripts, run in order (below), and the page, paper and blog templates. |
| `release/` | Paper PDF and LaTeX source, blog figures and post, Zenodo files. |
| `reddit/` | Collage (`collage.py`, PNG) and post text. |

## Method in brief

- Status and year: in service unless TeleGeography marks a cable as planned; year is the ready-for-service year (expected year for planned cables; {R['n_planned_noyear']} planned cables have none). Eras by decade, planned cables separate.
- Length: TeleGeography's stated length; for the {R['n_no_length']} cables without one, the drawn route measured on the WGS84 ellipsoid.
- Owners: Google, Meta, Amazon Web Services and Microsoft matched as whole names in the comma-separated owners list (no other spellings occur; Metacore Subcom is a different company). Shares are of kilometres ready in each period.
- Choke points: bands drawn across straits from shore to shore and areas round hubs (definitions in `code/02_chokepoints.py` and `data/chokepoints.geojson`); a cable counts if its drawn route intersects the band or area. Egypt: routes over Egyptian land or landings on both coasts. Grid: distinct cables crossing each half-degree cell.
- Countries: a cable is international if it lands in more than one of TeleGeography's countries and territories. Islands: Natural Earth outline touches no other country (some territories set by hand).
- Caveats: retired cables are not in the data, so early years count survivors; routes are schematic; no capacities; owners as listed (capacity purchases not visible).

## How to rerun

Needs Python 3 with numpy, shapely, pyproj, matplotlib, fontTools and Pillow; xelatex and pdfinfo; Playwright with Chromium for the QA step. Raw inputs are read in place (paths in `code/common.py`): the TeleGeography API v3 files `cable-geo.json`, `landing-point-geo.json` and `cable_details.json` (fetched 2026 from https://www.submarinecablemap.com/api/v3/), and Natural Earth countries and land. Intermediate files go to `/home/claude/work/submarine-cables` (set `CABLES_WORK` to change).

```
python3 code/01_clean.py        # cables, landing points, countries
python3 code/02_chokepoints.py  # straits, hubs, grid
python3 code/03_results.py      # results.json and page data
python3 code/04_build_site.py   # index.html (and checks on every number stated in words)
python3 code/05_figures.py      # header, blog and paper figures
python3 code/06_paper.py        # paper PDF
python3 code/07_readme.py       # README and LICENSE
python3 code/08_release.py      # blog post, Zenodo files
python3 reddit/collage.py       # collage
python3 code/09_qa.py           # screenshots and text checks
```

## Sources and licences

Licence of this study's outputs: data, figures and text CC BY-NC-SA 4.0; code MIT. Source data: TeleGeography, CC BY-NC-SA 3.0.


- TeleGeography, Submarine Cable Map (https://www.submarinecablemap.com/), API version 3, 2026. CC BY-NC-SA 3.0. All derived data in `data/`, the figures, the collage and the page text are shared under CC BY-NC-SA 4.0, with credit to TeleGeography. CC BY-NC-SA 3.0 allows adaptations to be licensed under a later version of the same licence.
- Natural Earth countries and land (public domain).
- Base map tiles on the page: © Esri.
- Code: MIT (see `LICENSE`).

## Citation

Hotham, T. (2026) The internet's seabed: submarine cables, when they were laid, who owns them and where they crowd together. Zenodo. {{https://doi.org/10.5281/zenodo.23856607}}

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

{AI}
"""
visible_text_ok(re.sub(r"(?m)^\|[-| ]+\|$", "", readme), "README")
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(readme)
LIC = """MIT License

Copyright (c) 2026 Tristan Hotham

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.


This MIT licence covers the code in code/ and reddit/collage.py and the page
scripts only.

The data in data/, the figures (header.png, release/blog/, release/paper/,
reddit/), the collage and the text of the page, paper and blog post are derived
from the TeleGeography Submarine Cable Map (www.submarinecablemap.com), which is
licensed under Creative Commons Attribution-NonCommercial-ShareAlike 3.0
(https://creativecommons.org/licenses/by-nc-sa/3.0/). They are shared under
Creative Commons Attribution-NonCommercial-ShareAlike 4.0 (CC BY-NC-SA 4.0,
https://creativecommons.org/licenses/by-nc-sa/4.0/), a later version of the
same licence, as the 3.0 licence permits for adaptations: you may share and
adapt them for non-commercial purposes, with credit to TeleGeography and to
Tristan Hotham, under the same licence. Country outlines and land are from Natural
Earth (public domain).
"""
open(os.path.join(ROOT, "LICENSE"), "w", encoding="utf-8").write(LIC)
print("README and LICENSE written")
