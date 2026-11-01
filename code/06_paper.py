"""Step 6. Paper PDF: fill code/paper_template.tex from data/results.json, write release/paper/Hotham_The_Internets_Seabed.tex
and compile it with xelatex (figures from step 5 in release/paper/). The DOI line keeps the publisher's 10.5281/zenodo.23856607 placeholder
unless CABLES_DOI is set.
Run: python3 code/06_paper.py
"""
import os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

R = jload(f"{DATA}/results.json")
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_The_Internets_Seabed"
DOI = os.environ.get("CABLES_DOI", "")
tex = lambda s: str(s).replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#")


def ffmt(v, f):
    if f in ("pct",): return f"{round(v * 100)}\\%"
    if f == "pct1": return f"{v * 100:.1f}\\%"
    if f in (None, "raw"): return tex(v)
    return fmt(v, f)


def sub(m):
    k = m.group(1)
    if k == "DOI":
        return DOI or "10.5281/zenodo.23856607"
    if k == "TABLE_CHOKE":
        return m.group(0)
    return ffmt(get(R, k), m.group(3))


rows = []
for kind, lab in (("strait", "Straits and corridors"), ("hub", "Hub areas")):
    rows.append(f"\\multicolumn{{4}}{{l}}{{\\textit{{{lab}}}}}\\\\")
    for z in sorted([z for z in R["zones"] if z["kind"] == kind], key=lambda z: (-z["n_active"], -z["km_active"])):
        rows.append(f"{tex(z['name'])} & {z['n_active']} & {z['n_planned']} & {z['km_active']:,}\\\\")
TABLE = ("\\begin{table}[tbp]\\centering\\small\\caption{Cables through each choke point: in service, planned, and the combined length of the cables in service that pass (km).}\\label{tab:choke}"
         "\\begin{tabular}{lrrr}\\toprule Choke point & In service & Planned & Combined km\\\\\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\\end{tabular}\\end{table}")
src = open(os.path.join(ROOT, "code", "paper_template.tex"), encoding="utf-8").read()
out = re.sub(r"\{\{([^{}|]+)(\|(\w+))?\}\}", sub, src).replace("{{TABLE_CHOKE}}", TABLE)
assert not re.search(r"\{\{(?!DOI\}\})", out.replace("{10.5281/zenodo.23856607}", "{DOI}"))
body = re.sub(r"(?m)^%.*$", "", out)
for bad in ("—", "–", "DSIT", "DCMS"):
    assert bad not in body, bad
assert "--" not in body.replace("\\-\\-", "")
os.makedirs(OUT, exist_ok=True)
open(f"{OUT}/{NAME}.tex", "w", encoding="utf-8").write(out)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", f"{NAME}.tex"], cwd=OUT, capture_output=True, text=True)
pdf = f"{OUT}/{NAME}.pdf"
assert os.path.exists(pdf), r.stdout[-3000:]
pages = subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout
n = int(re.search(r"Pages:\s+(\d+)", pages).group(1))
print(NAME, n, "pages")
assert 8 <= n <= 15, n
for ext in ("aux", "log", "out"):
    if os.path.exists(f"{OUT}/{NAME}.{ext}"):
        os.remove(f"{OUT}/{NAME}.{ext}")
