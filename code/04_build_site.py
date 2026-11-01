"""Step 4. Build index.html from code/page_template.html and code/fullscreen_snippet.html. Every number in the text is a
{{path|format}} token filled from data/results.json; facts stated in words are checked by the asserts below (they
cover the page, paper, blog and collage). 10.5281/zenodo.23856607, https://doi.org/10.5281/zenodo.23856607 and https://blog.tristanhotham.com/2026/10/31/submarine-cables/ are left for the publisher.
Run: python3 code/04_build_site.py
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

R = jload(f"{DATA}/results.json")
J = jload(f"{WORK}/cables.json")
C = {c["name"]: c for c in J["cables"]}
Z = R["zone"]

# ---------- facts stated in words (page, paper, blog, collage, post) ----------
assert R["n_2027"] == R["n_2027_planned"]                                  # 2027 cables all still planned
assert R["peak_year"] == 2023 and R["km_peak_year"] == 2001
assert R["n_by_year"]["2027"] == max(R["n_by_year"].values())              # 2027 the biggest year in the record
assert R["era"]["1990s"]["median_owners"] >= 1 and R["longest"][0]["name"] == "Project Waterworth" and R["longest"][0]["planned"]
assert C["Project Waterworth"]["owners"] == ["Meta"]
assert R["hyper"]["share_km_pre2010"] == 0 and R["hyper"]["first_year"] == 2010
assert R["hyper_bins"][0]["n_hyper"] == 0
assert [c["country"] for c in R["top_countries"][:3]] == ["United States", "United Kingdom", "Singapore"]
assert any(s["country"] == "Niue" and s["island"] for s in R["single"])
assert all(any(s["country"] == k and s["island"] for s in R["single"]) for k in ("Greenland", "Nauru", "Vanuatu", "Solomon Islands", "Cook Islands"))
assert any(s["country"] == "Poland" and not s["island"] for s in R["single"]) and any(s["country"] == "Romania" and not s["island"] for s in R["single"])
assert [z["country"] for z in R["zero"]] == ["Timor-Leste", "Tuvalu"] or sorted(z["country"] for z in R["zero"]) == ["Timor-Leste", "Tuvalu"]
assert next(z for z in R["zero"] if z["country"] == "Tuvalu")["domestic"] == 0
assert "VAKA" in [c["name"] for c in J["cables"] if "Tuvalu" in c["countries"] and c["planned"]]
assert R["tonga_cable_year"] < 2022 and {t["name"] for t in R["tonga"]} == {"Tonga Cable", "Hawaiki"}
assert R["straits_rank"][0] == "sicily" and Z["redsea"]["n_active"] >= Z["bab"]["n_active"]
assert R["hubs_rank"][0] == "singapore"
assert R["top_cells"][0]["near"].endswith("Singapore")
assert R["top_lps"][0]["n"] == R["top_lps"][1]["n"] > R["top_lps"][2]["n"]
for k in ("cornwall", "marseille", "hawaii", "guam", "boso", "fujairah"):
    assert Z[k]["n_active"] >= 10, k
assert sorted(c["country"] for c in R["coastal_none"]) == ["El Salvador", "Eritrea", "Montenegro", "North Korea", "Turkmenistan"]
single_islands = sorted(s["country"] for s in R["single"] if s["island"])
assert "Greenland" in single_islands and all(s["planned"] >= 0 for s in R["single"])


def build():
    tpl = open(os.path.join(ROOT, "code", "page_template.html"), encoding="utf-8").read()
    html = fill(tpl, R)
    assert not re.search(r"\{\{(?!DOI\}\}|DOI_URL\}\}|BLOG_URL\}\})", html), re.findall(r"\{\{[^}]*\}\}", html)[:5]
    J_ = lambda o: json.dumps(o, ensure_ascii=False, separators=(",", ":"))
    html = html.replace("/*RESULTS*/", J_(R))
    html = html.replace("/*FULLSCREEN*/", open(os.path.join(ROOT, "code", "fullscreen_snippet.html"), encoding="utf-8").read())
    vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", html, flags=re.S)
    vis = re.sub(r"<[^>]+>", " ", vis)
    visible_text_ok(vis, "page")
    for scr in re.findall(r"<script>(.*?)</script>", html, flags=re.S):
        for bad in ("—", "–"):
            assert bad not in scr, bad
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(html)
    print("index.html", len(html.encode()) // 1024, "KB")


if __name__ == "__main__":
    build()
