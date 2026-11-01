# The internet's seabed

Every submarine cable in TeleGeography's open Submarine Cable Map (2026): when each was laid, who owns it, and the straits and landing hubs where cables crowd together. 608 cables in service (1,592,824 km) and 105 planned (502,770 km), landing at 1,928 points in 186 countries and territories.

Interactive page: https://maps.tristanhotham.com/submarine-cables/
Paper: https://doi.org/10.5281/zenodo.23856607
Blog post: https://blog.tristanhotham.com/2026/10/31/submarine-cables/

## Headline results

- When they were laid: the oldest cables still in service date from 1989. 74 of today's cables came into service in the dot-com boom of 1999 to 2001, and 2001 is still the year with the most kilometres (121,657 km). Only 31 followed in 2002 to 2004. The busiest year for new cables was 2023 (32), and 49 are planned for 2027.
- Who owns them: Google, Meta, Amazon (Amazon Web Services) and Microsoft part-own none of the cable length ready before 2010, 9% of the length ready in 2010 to 2014, 24% in 2015 to 2019, 50% in 2020 to 2026 and 55% of the planned length. 31 of their 62 cables have no other owner.
- Choke points: 18 cables in service cross the Strait of Sicily, 13 the Red Sea at 20° N and 12 the Bab el-Mandeb (combined length 217,777 km, 14% of all cable length in service); 9 cross Egypt overland. 38 cables reach the sea within 35 km of Singapore (14 more planned); the busiest half-degree cell, off Singapore, is crossed by 38.
- Most and least connected: the United States has 59 international cables, the United Kingdom 51 and Singapore 34. 29 countries and territories have one; 17 of these are islands with no land border: Anguilla, British Indian Ocean Territory, Christmas Island, Cocos (Keeling) Islands, Cook Islands, Greenland, Marshall Islands, Montserrat, Nauru, Niue, Saint Helena, Ascension and Tristan da Cunha, Saint Pierre and Miquelon, Solomon Islands, Tokelau, Turks and Caicos Islands, Vanuatu, Wallis and Futuna. Tuvalu appears only on a planned cable. 1,312 of 1,792 landing points in service (73%) serve one cable.

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/04_build_site.py`); loads `data/site.json`, `data/cables.geojson`, `data/chokepoints.geojson` and, on demand, `data/grid_density.png`. |
| `header.png` | Social card, 1200 x 630. |
| `data/cables.csv` | 713 cables: ready-for-service date and year, status, era, length (stated or measured), landing and country counts, countries, owners, cloud-company owners, suppliers (129 KB). |
| `data/cables.geojson` | Cable routes, lightly simplified, keyed by cable id (292 KB). |
| `data/landing_points.csv`, `.geojson` | 1,928 landing points with cables in service and planned. |
| `data/countries.csv` | Countries and territories: international and domestic cables in service, planned cables, landing points, land border. |
| `data/chokepoints.csv`, `.geojson` | 9 straits and corridors and 12 hubs: definition, cables in service and planned, combined length, cable ids; the bands and areas used. |
| `data/grid_cells.csv`, `data/grid.json`, `data/grid_density.png` | Distinct cables crossing each half-degree cell. |
| `data/timeline.csv` | Cables and kilometres per ready-for-service year, cumulative, and part-owned by the four cloud companies. |
| `data/hyperscalers.csv` | The 62 cables with Google, Meta, Amazon Web Services or Microsoft among their owners. |
| `data/results.json` | Every number used in the page, paper, blog and collage. |
| `data/site.json` | Page data. |
| `code/` | Scripts, run in order (below), and the page, paper and blog templates. |
| `release/` | Paper PDF and LaTeX source, blog figures and post, Zenodo files. |
| `reddit/` | Collage (`collage.py`, PNG) and post text. |

## Method in brief

- Status and year: in service unless TeleGeography marks a cable as planned; year is the ready-for-service year (expected year for planned cables; 6 planned cables have none). Eras by decade, planned cables separate.
- Length: TeleGeography's stated length; for the 73 cables without one, the drawn route measured on the WGS84 ellipsoid.
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

Hotham, T. (2026) The internet's seabed: submarine cables, when they were laid, who owns them and where they crowd together. Zenodo. https://doi.org/10.5281/zenodo.23856607

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
