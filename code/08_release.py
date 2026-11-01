"""Step 8. Blog post and meta (release/blog), Zenodo files and metadata (release/zenodo), Reddit post (reddit/post.md).
Numbers in the blog's alt text and in the post are checked against results.json here.
Run: python3 code/08_release.py
"""
import os, re, sys, zipfile, json as _json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

R = jload(f"{DATA}/results.json"); Z = R["zone"]; H = R["hyper"]
REL = os.path.join(ROOT, "release"); NAME = "Hotham_The_Internets_Seabed"
by = {t["year"]: t for t in R["timeline"]}

# ---------- facts written as words or numbers in alt text and captions ----------
assert [round(b["share_km"] * 100) for b in R["hyper_bins"]] == [0, 9, 24, 50, 55]
assert (H["Google"]["n"], H["Meta"]["n"], H["Microsoft"]["n"], H["Amazon"]["n"]) == (37, 21, 8, 6)
assert [(Z[k]["n_active"], Z[k]["n_planned"]) for k in ("sicily", "redsea", "bab")] == [(18, 5), (13, 4), (12, 4)]
assert (Z["luzon"]["n_active"], Z["malacca"]["n_active"], Z["egypt"]["n_active"], Z["hormuz"]["n_active"]) == (10, 10, 9, 5)
assert (Z["singapore"]["n_active"], Z["singapore"]["n_planned"], Z["boso"]["n_active"], Z["fujairah"]["n_active"], Z["guam"]["n_active"], Z["hongkong"]["n_active"], Z["cornwall"]["n_active"]) == (38, 14, 20, 15, 15, 14, 14)
assert by[1999]["n_active"] == 30 and max(by[y]["n_active"] for y in by if y < 2002) == 30 and by[2023]["n_active"] == 32 and by[2027]["n_planned"] == 49
assert [c["n"] for c in R["top_countries"][:3]] == [59, 51, 34]
assert [t["near"].split(",")[0] for t in R["top_cells"][:6]] == ["Sakra Island", "Chikura", "Fujairah", "Djibouti City", "Jeddah", "Chai Wan"] or \
       {t["near"].split(",")[0] for t in R["top_cells"][:6]} == {"Sakra Island", "Chikura", "Fujairah", "Djibouti City", "Jeddah", "Chai Wan"}
isl = [s["country"] for s in R["single"] if s["island"]]
assert len(isl) == 17 and isl[0] == "Anguilla" and isl[-1] == "Wallis and Futuna" and {"Christmas Island", "Vanuatu", "Greenland", "Nauru", "Niue", "Solomon Islands", "Saint Helena, Ascension and Tristan da Cunha"} <= set(isl)

# ---------- blog ----------
post = fill(open(os.path.join(ROOT, "code", "blog_template.html"), encoding="utf-8").read(), R)
used = re.findall(r"\{\{IMG\|([^|]+)\|", post)
assert 5 <= len(used) <= 8, used
for img in used:
    assert os.path.exists(f"{REL}/blog/{img}"), img
for fn in os.listdir(f"{REL}/blog"):
    if fn.startswith("b_") and fn not in used:
        os.remove(f"{REL}/blog/{fn}")
for ln in post.splitlines():
    if "{{IMG|" in ln:
        assert ln.startswith("{{IMG|") and ln.endswith("}}"), ln
assert not re.search(r"\{\{(?!IMG\||DOI_URL\}\}|BLOG_URL\}\}|DOI\}\})", post)
vis = re.sub(r"<!--.*?-->", "", post, flags=re.S)
visible_text_ok(vis, "blog")
open(f"{REL}/blog/post.html", "w", encoding="utf-8").write(post)
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]*\}\}", " ", vis).split())
meta = {"title": "The internet's seabed: every submarine cable, when it was laid, and the choke points",
        "slug": "submarine-cables",
        "excerpt": f"{R['n_active']} cables on the sea floor carry the internet between continents. I mapped when each was laid, how Google, Meta, Amazon and Microsoft came to part-own {round(H['share_planned_km'] * 100)}% of the planned length, and the straits and beaches where dozens squeeze through together.",
        "seo_description": "A map of every submarine internet cable: when each was laid, who owns them, and the straits and hubs where they crowd together.",
        "tags": ["submarine cables", "internet", "infrastructure", "maps", "data visualisation", "Red Sea", "TeleGeography"],
        "header_alt": f"Title card reading 'The internet's seabed' beside a world map of every submarine cable coloured by the decade it was laid, indigo for the 1990s through blue, teal and amber to dashed coral for planned cables. Text: {R['n_active']} submarine cables in service, {R['km_active'] / 1e6:.1f} million km, and {R['n_planned']} planned."}
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
jsave(meta, f"{REL}/blog/meta.json", indent=2)

# ---------- Zenodo ----------
Zd = f"{REL}/zenodo"; os.makedirs(Zd, exist_ok=True)
for fn in os.listdir(Zd):
    os.remove(os.path.join(Zd, fn))
os.link(f"{REL}/paper/{NAME}.pdf", f"{Zd}/{NAME}.pdf")
zp = f"{Zd}/submarine-cables_code_and_data.zip"
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for d in ("code", "data"):
        for fn in sorted(os.listdir(os.path.join(ROOT, d))):
            if fn.endswith(".pyc") or fn == "__pycache__":
                continue
            z.write(os.path.join(ROOT, d, fn), f"submarine-cables/{d}/{fn}")
    for fn in ("README.md", "LICENSE", "reddit/collage.py"):
        z.write(os.path.join(ROOT, fn), f"submarine-cables/{fn}")
tex = open(f"{REL}/paper/{NAME}.tex", encoding="utf-8").read()
ab = re.search(r"\\begin\{center\}\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\n\\textbf\{Keywords", tex, re.S).group(1)
ab = ab.replace("\\%", "%").replace("\\&", "&").replace("\\emph{", "").replace("}", "")
zmeta = {"title": "The Internet's Seabed: Submarine Cables, When They Were Laid, Who Owns Them and Where They Crowd Together",
         "upload_type": "publication", "publication_type": "workingpaper",
         "description": f"<p>{ab}</p><p>Interactive version: <a href=\"{PAGE_URL}\">{PAGE_URL}</a>. Data and code: <a href=\"{REPO}\">{REPO}</a>. Blog post: {{https://blog.tristanhotham.com/2026/10/31/submarine-cables/}}.</p>"
                        "<p>Data: TeleGeography Submarine Cable Map (submarinecablemap.com), licensed CC BY-NC-SA 3.0; the derived data, figures and text are shared under CC BY-NC-SA 4.0, a later version of the same licence, as 3.0 permits. Code: MIT. Land and borders: Natural Earth (public domain).</p>",
         "creators": [{"name": "Hotham, Tristan", "affiliation": "Independent researcher", "orcid": "0000-0003-4931-9349"}],
         "keywords": ["submarine cables", "internet infrastructure", "choke points", "resilience", "hyperscalers", "Red Sea", "TeleGeography", "data visualisation"],
         "license": "cc-by-nc-sa-4.0", "language": "eng",
         "related_identifiers": [{"identifier": REPO, "relation": "isSupplementedBy", "resource_type": "software"},
                                 {"identifier": PAGE_URL, "relation": "isSupplementedBy", "resource_type": "other"},
                                 {"identifier": "https://www.submarinecablemap.com/", "relation": "isDerivedFrom", "resource_type": "dataset"},
                                 {"identifier": "https://www.naturalearthdata.com/", "relation": "isDerivedFrom", "resource_type": "dataset"}],
         "notes": AI}
s = _json.dumps(zmeta, ensure_ascii=False) + _json.dumps(meta, ensure_ascii=False)
visible_text_ok(s, "meta")
jsave(zmeta, f"{Zd}/metadata.json", indent=2)

# ---------- Reddit post ----------
pm = f"""## Title

[OC] The internet's seabed: {R['n_active']} submarine cables coloured by the decade they were laid. {Z['bab']['n_active']} squeeze through the Bab el-Mandeb, {Z['singapore']['n_active']} come ashore around Singapore, and Google, Meta, Amazon and Microsoft part-own {round(H['share_planned_km'] * 100)}% of the planned length

## Body

I mapped every cable in TeleGeography's open Submarine Cable Map: {R['n_active']} in service ({R['km_active'] / 1e6:.1f} million km, {R['times_round_earth']:.0f} times round the Earth) and {R['n_planned']} planned. {R['dotcom_n']} of today's cables came into service in the dot-com boom of 1999 to 2001; {R['peak_year']} had the most new cables ({R['peak_n']}) and {R['n_2027']} are planned for 2027. The four big cloud companies part-own none of the length ready before 2010, {round(H['share_km_2020s'] * 100)}% of the length ready since 2020 and {round(H['share_planned_km'] * 100)}% of the planned length. Choke points: {Z['sicily']['n_active']} cables cross the Strait of Sicily, {Z['bab']['n_active']} the Bab el-Mandeb at the foot of the Red Sea, and {R['n_single_island']} islands (Greenland, Nauru, Niue, Vanuatu, St Helena and more) hang on a single international cable. Caveats: TeleGeography draws routes schematically, retired cables are not included (so the 1990s count survivors), and there are no capacities, so an old cable counts the same as a new one. Interactive map with a time slider: {PAGE_URL}

## Source comment

Source: TeleGeography Submarine Cable Map (submarinecablemap.com), API v3, 2026, CC BY-NC-SA 3.0 (routes, landing points, ready-for-service years, lengths, owners). Land and borders: Natural Earth (public domain). Choke points: cables whose drawn routes cross a band drawn across each strait, or enter an area round each hub; owners matched by exact name (Amazon as Amazon Web Services).

Tools: Python (shapely, pyproj, matplotlib); Leaflet for the interactive map. Derived data and figures: CC BY-NC-SA 4.0.

Interactive version: {PAGE_URL}
Paper: {{https://doi.org/10.5281/zenodo.23856607}}
Blog post: {{https://blog.tristanhotham.com/2026/10/31/submarine-cables/}}
"""
visible_text_ok(pm, "post")
open(os.path.join(ROOT, "reddit", "post.md"), "w", encoding="utf-8").write(pm)
print("blog words", words, "; figures", len(used), "; zenodo", sorted(os.listdir(Zd)), os.path.getsize(zp) // 1024, "KB zip")
