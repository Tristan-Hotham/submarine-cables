"""Step 3. Every number quoted anywhere (page, paper, blog, collage, Reddit post) goes into data/results.json, plus the
page data (data/site.json: cable attributes for the map popups, the timeline and the ranking tables).
Also writes data/timeline.csv, data/hyperscalers.csv and data/coastal_without_cables.csv.
Run: python3 code/03_results.py
"""
import csv, collections, os, sys, statistics as st
import numpy as np
import shapely
from shapely.geometry import shape
from shapely.ops import unary_union
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

J = jload(f"{WORK}/cables.json")
K = jload(f"{WORK}/choke.json")
C, LPS, CO = J["cables"], J["landing_points"], J["countries"]
A = [c for c in C if not c["planned"]]
P = [c for c in C if c["planned"]]
km = lambda cs: sum(c["length_km"] for c in cs)
R = {}

# ---------- totals ----------
R["n"] = len(C); R["n_active"] = len(A); R["n_planned"] = len(P)
R["km_active"] = round(km(A)); R["km_planned"] = round(km(P)); R["km_all"] = round(km(C))
R["n_landing_points"] = len(LPS); R["n_countries"] = len(CO)
R["n_lp_active"] = sum(1 for p in LPS if p["n_active"] > 0)
R["n_no_length"] = sum(1 for c in C if c["length_source"] == "route")
R["km_route_share"] = round(sum(c["length_km"] for c in C if c["length_source"] == "route") / km(C), 4)
R["route_vs_stated_median"] = round(float(np.median([c["route_km"] / c["length_stated_km"] for c in C if c["length_stated_km"]])), 3)
R["earth_circ"] = 40075
R["times_round_earth"] = round(R["km_active"] / 40075, 1)
R["moon_km"] = 384400
R["moon_share"] = round(R["km_active"] / 384400, 2)
R["first_year"] = min(c["year"] for c in A)
R["oldest"] = [dict(name=c["name"], year=c["year"], countries=c["countries"]) for c in sorted(A, key=lambda c: (c["year"], c["name"]))[:6]]
R["n_1990s_active"] = sum(1 for c in A if c["era"] == "1990s")
lng = sorted(C, key=lambda c: -c["length_km"])
R["longest"] = [dict(name=c["name"], km=round(c["length_km"]), year=c["year"], planned=c["planned"], n_landings=c["n_landings"], n_countries=c["n_countries"]) for c in lng[:10]]
R["longest_active"] = [dict(name=c["name"], km=round(c["length_km"]), year=c["year"], n_landings=c["n_landings"], n_countries=c["n_countries"]) for c in sorted(A, key=lambda c: -c["length_km"])[:6]]
R["median_km_active"] = round(st.median([c["length_km"] for c in A]))
R["n_short_active"] = sum(1 for c in A if c["length_km"] < 500)
R["n_intl_active"] = sum(1 for c in A if c["international"])
R["n_dom_active"] = len(A) - R["n_intl_active"]
R["n_planned_noyear"] = sum(1 for c in P if c["year"] is None)
R["planned_noyear"] = [c["name"] for c in P if c["year"] is None]
R["n_planned_by_2027"] = sum(1 for c in P if c["year"] and c["year"] <= 2027)
R["n_2027"] = sum(1 for c in C if c["year"] == 2027)
R["n_2026_active"] = sum(1 for c in A if c["year"] == 2026)
R["n_2026_planned"] = sum(1 for c in P if c["year"] == 2026)
R["last_planned_year"] = max(c["year"] for c in P if c["year"])

# ---------- timeline ----------
years = list(range(R["first_year"], R["last_planned_year"] + 1))
tl = []
cum_n = cum_km = 0
for y in years:
    a = [c for c in A if c["year"] == y]; p = [c for c in P if c["year"] == y]
    cum_n += len(a); cum_km += km(a)
    h = [c for c in a + p if c["hyperscalers"]]
    tl.append(dict(year=y, n_active=len(a), km_active=round(km(a)), n_planned=len(p), km_planned=round(km(p)),
                   cum_n=cum_n, cum_km=round(cum_km), n_hyper=len(h), km_hyper=round(km(h))))
R["timeline"] = tl
byy = {t["year"]: t for t in tl}
R["peak_year"] = max((t for t in tl if t["year"] <= YEAR_NOW), key=lambda t: t["n_active"])["year"]
R["peak_n"] = byy[R["peak_year"]]["n_active"]
R["dotcom_n"] = sum(byy[y]["n_active"] for y in (1999, 2000, 2001))
R["dotcom_km"] = sum(byy[y]["km_active"] for y in (1999, 2000, 2001))
R["bust_n"] = sum(byy[y]["n_active"] for y in (2002, 2003, 2004))
R["n_by_year"] = {str(y): byy[y]["n_active"] + byy[y]["n_planned"] for y in years}
R["km_peak_year"] = max((t for t in tl if t["year"] <= YEAR_NOW), key=lambda t: t["km_active"])["year"]
R["km_peak"] = byy[R["km_peak_year"]]["km_active"]
R["km_2027_planned"] = byy[2027]["km_planned"]
R["n_2027_planned"] = byy[2027]["n_planned"]
R["km_since_2016"] = round(km([c for c in A if c["year"] >= 2016]))
R["km_since_2016_share"] = round(R["km_since_2016"] / R["km_active"], 3)
R["n_since_2016"] = sum(1 for c in A if c["year"] >= 2016)
R["km_before_2000_share"] = round(km([c for c in A if c["year"] < 2000]) / R["km_active"], 3)
R["km_dotcom_share"] = round(R["dotcom_km"] / R["km_active"], 3)
R["median_km_by_era"] = {e: round(st.median([c["length_km"] for c in C if c["era"] == e])) for e in ERA_COL}
R["eras"] = []
for k, lab, a, b, col in ERAS:
    cs = [c for c in C if c["era"] == k]
    R["eras"].append(dict(key=k, label=lab, colour=col, n=len(cs), km=round(km(cs)), share_n=round(len(cs) / len(C), 3),
                          median_owners=st.median([c["n_owners"] for c in cs]), single_owner=round(sum(c["n_owners"] == 1 for c in cs) / len(cs), 3),
                          consortium5=round(sum(c["n_owners"] >= 5 for c in cs) / len(cs), 3), hyper=sum(1 for c in cs if c["hyperscalers"]),
                          hyper_km=round(km([c for c in cs if c["hyperscalers"]])), hyper_share_n=round(sum(1 for c in cs if c["hyperscalers"]) / len(cs), 3),
                          hyper_share_km=round(km([c for c in cs if c["hyperscalers"]]) / km(cs), 3)))
ER = {e["key"]: e for e in R["eras"]}
R["era"] = ER

# ---------- hyperscalers ----------
H = [c for c in C if c["hyperscalers"]]
R["hyper"] = dict(n=len(H), n_active=sum(1 for c in H if not c["planned"]), n_planned=sum(1 for c in H if c["planned"]),
                  km=round(km(H)), km_active=round(km([c for c in H if not c["planned"]])), km_planned=round(km([c for c in H if c["planned"]])),
                  first=min((c for c in H), key=lambda c: c["year"] or 9999)["name"], first_year=min(c["year"] for c in H if c["year"]),
                  sole=sum(1 for c in H if c["n_owners"] == 1), sole_planned=sum(1 for c in H if c["n_owners"] == 1 and c["planned"]),
                  sole_active=sum(1 for c in H if c["n_owners"] == 1 and not c["planned"]))
R["hyper"]["share_planned_n"] = round(R["hyper"]["n_planned"] / len(P), 3)
R["hyper"]["share_planned_km"] = round(R["hyper"]["km_planned"] / km(P), 3)
R["hyper"]["share_active_km"] = round(R["hyper"]["km_active"] / km(A), 3)
R["hyper"]["share_active_n"] = round(R["hyper"]["n_active"] / len(A), 3)
for nm in HYPER:
    cs = [c for c in C if nm in c["hyperscalers"]]
    R["hyper"][nm] = dict(n=len(cs), n_active=sum(1 for c in cs if not c["planned"]), n_planned=sum(1 for c in cs if c["planned"]),
                          km=round(km(cs)), sole=sum(1 for c in cs if c["n_owners"] == 1))
bins = [(1989, 2009, "1989 to 2009"), (2010, 2014, "2010 to 2014"), (2015, 2019, "2015 to 2019"), (2020, 2026, "2020 to 2026"), (None, None, "Planned")]
R["hyper_bins"] = []
for a, b, lab in bins:
    cs = P if a is None else [c for c in A if a <= c["year"] <= b]
    hs = [c for c in cs if c["hyperscalers"]]
    R["hyper_bins"].append(dict(label=lab, n=len(cs), km=round(km(cs)), n_hyper=len(hs), km_hyper=round(km(hs)),
                                share_n=round(len(hs) / len(cs), 3), share_km=round(km(hs) / km(cs), 3),
                                by={nm: round(km([c for c in hs if nm in c["hyperscalers"]])) for nm in HYPER}))
HB = {b["label"]: b for b in R["hyper_bins"]}
R["hyper"]["share_km_2020s"] = HB["2020 to 2026"]["share_km"]
R["hyper"]["share_km_1015"] = HB["2010 to 2014"]["share_km"]
R["hyper"]["share_km_1519"] = HB["2015 to 2019"]["share_km"]
R["hyper"]["share_km_pre2010"] = HB["1989 to 2009"]["share_km"]
R["hyper"]["n_2020s"] = HB["2020 to 2026"]["n_hyper"]
R["hyper"]["sole_list"] = [c["name"] for c in sorted(H, key=lambda c: (c["year"] or 9999, c["name"])) if c["n_owners"] == 1]

# ---------- owners and suppliers ----------
oc = collections.Counter(o for c in A for o in c["owners"])
R["top_owners"] = [dict(name=o, n=n) for o, n in oc.most_common(12)]
R["n_owners_distinct"] = len({o for c in C for o in c["owners"]})
sc = collections.Counter(s for c in A for s in c["suppliers"])
R["n_supplier_known"] = sum(1 for c in A if c["suppliers"])
R["top_suppliers"] = [dict(name=s, n=n, share=round(n / R["n_supplier_known"], 3)) for s, n in sc.most_common(5)]
R["big3_share"] = round(sum(1 for c in A if set(c["suppliers"]) & {"ASN", "SubCom", "NEC"}) / R["n_supplier_known"], 3)
R["consortia"] = dict(max_owners=max(c["n_owners"] for c in C), max_owner_cable=max(C, key=lambda c: c["n_owners"])["name"])

# ---------- countries ----------
COA = [c for c in CO if c["n_active"] > 0]
R["n_countries_active"] = len(COA)
R["top_countries"] = [dict(country=c["country"], n=c["n_international"], all=c["n_active"], lps=c["n_landing_points"], planned=c["n_international_planned"]) for c in CO[:15]]
single = [c for c in CO if c["n_international"] == 1]
zero = [c for c in CO if c["n_international"] == 0]
R["single"] = [dict(country=c["country"], island=not c["land_border"], cable=next(x["name"] for x in C if x["id"] == c["intl_cables"][0]),
                    planned=c["n_international_planned"], lon=c["lon"], lat=c["lat"]) for c in sorted(single, key=lambda c: c["country"])]
R["n_single"] = len(single)
R["n_single_island"] = sum(1 for c in single if not c["land_border"])
R["n_single_island_planned"] = sum(1 for c in single if not c["land_border"] and c["n_international_planned"] > 0)
R["n_single_land"] = R["n_single"] - R["n_single_island"]
R["zero"] = [dict(country=c["country"], island=not c["land_border"], domestic=c["n_domestic"], planned=c["n_international_planned"]) for c in zero]
R["n_two"] = sum(1 for c in CO if c["n_international"] == 2)
R["n_two_island"] = sum(1 for c in CO if c["n_international"] == 2 and not c["land_border"])
R["n_islands"] = sum(1 for c in CO if not c["land_border"])
R["n_islands_le2"] = sum(1 for c in CO if not c["land_border"] and c["n_international"] <= 2)
R["n_10plus"] = sum(1 for c in CO if c["n_international"] >= 10)
R["tonga"] = [dict(name=x["name"], year=x["year"]) for x in C if "Tonga" in x["countries"] and x["international"] and not x["planned"]]
R["tonga_cable_year"] = next(x["year"] for x in C if x["name"] == "Tonga Cable")
R["tonga_hawaiki_year"] = next(x["year"] for x in C if x["name"] == "Hawaiki")

# coastal sovereign countries with no cable in the data (Natural Earth): a country is coastal if part of its outline is
# not shared with another country
NE = jload(f"{GEO}/ne_10m_admin_0_countries.geojson")["features"]
names_in = set()
import importlib.util
spec = importlib.util.spec_from_file_location("c1", os.path.join(ROOT, "code", "01_clean.py"))
ALIAS = {}
src = open(os.path.join(ROOT, "code", "01_clean.py"), encoding="utf-8").read()
exec(src[src.index("ALIAS = {"):src.index("# French overseas")])
for c in CO:
    names_in.add(ALIAS.get(c["country"], c["country"]))
geo = [(f["properties"], shape(f["geometry"]).buffer(0)) for f in NE]
tree = shapely.STRtree([g for _, g in geo])
coastal_none = []
for i, (p, g) in enumerate(geo):
    if p["TYPE"] not in ("Sovereign country", "Country") or p["ADMIN"] in names_in or p["NAME"] in names_in or p["NAME_LONG"] in names_in:
        continue
    # Hong Kong's landings are listed under China in the data; Northern Cyprus and Somaliland are not generally recognised
    if p["ADMIN"] in ("Antarctica", "Hong Kong S.A.R.", "Northern Cyprus", "Somaliland") or p["POP_EST"] < 1e5:
        continue
    ring = g.boundary
    others = unary_union([geo[j][1].buffer(0.02) for j in tree.query(g.buffer(0.05)) if j != i])
    coast = ring.difference(others) if not others.is_empty else ring
    if coast.length > 0.3:     # degrees of outline not shared with a neighbour
        coastal_none.append(dict(country=p["ADMIN"], coast_deg=round(coast.length, 1)))
R["coastal_none"] = sorted(coastal_none, key=lambda c: c["country"])
print("coastal, no cable:", [(c["country"], c["coast_deg"]) for c in R["coastal_none"]])

# ---------- landing points ----------
LA = [p for p in LPS if p["n_active"] > 0]
R["top_lps"] = [dict(name=p["name"], country=p["country"], n=p["n_active"], planned=p["n_planned"]) for p in LA[:15]]
R["n_lp_single"] = sum(1 for p in LA if p["n_active"] == 1)
R["lp_single_share"] = round(R["n_lp_single"] / len(LA), 3)
R["n_lp_5plus"] = sum(1 for p in LA if p["n_active"] >= 5)
R["n_lp_10plus"] = sum(1 for p in LA if p["n_active"] >= 10)
R["n_lp_planned_only"] = sum(1 for p in LPS if p["n_active"] == 0)
R["median_lp_per_cable"] = st.median([c["n_landings"] for c in A])
R["max_lp_cable"] = max(A, key=lambda c: c["n_landings"])["name"]
R["max_lp"] = max(c["n_landings"] for c in A)

# ---------- choke points ----------
Z = {z["key"]: z for z in K["zones"]}
R["zones"] = [{k: z[k] for k in ("key", "name", "kind", "region", "note", "n_active", "n_planned", "km_active", "km_planned", "n_landing", "n_since_2015", "first_year", "n_hyper", "lon", "lat")} for z in K["zones"]]
R["zone"] = {z["key"]: {k: z[k] for k in ("name", "n_active", "n_planned", "km_active", "km_planned", "n_since_2015", "n_hyper", "first_year")} for z in K["zones"]}
straits = sorted([z for z in K["zones"] if z["kind"] == "strait"], key=lambda z: (-z["n_active"], -z["km_active"]))
hubs = sorted([z for z in K["zones"] if z["kind"] == "hub"], key=lambda z: (-z["n_active"], -z["km_active"]))
R["straits_rank"] = [z["key"] for z in straits]
R["hubs_rank"] = [z["key"] for z in hubs]
R["red_sea_share_km"] = round(Z["redsea"]["km_active"] / R["km_active"], 3)
R["bab_share_km"] = round(Z["bab"]["km_active"] / R["km_active"], 3)
R["bab_planned_names"] = [next(c["name"] for c in C if c["id"] == i) for i in Z["bab"]["planned"]]
R["egypt_names"] = [next(c["name"] for c in C if c["id"] == i) for i in Z["egypt"]["cables"]]
R["bab_names"] = [next(c["name"] for c in C if c["id"] == i) for i in Z["bab"]["cables"]]
R["top_cells"] = [dict(n=t["n"], lon=t["lon"], lat=t["lat"], near=t["near"], near_km=t["near_km"]) for t in K["top_cells"][:20]]
R["grid_res"] = K["res"]
R["grid_max"] = K["top_cells"][0]["n"]
R["hubs50"] = [dict(name=h["name"], country=h["country"], n=h["n"], stations=len(h["stations"])) for h in K["hubs"][:15]]
R["n_straits"] = len(straits); R["n_hubs"] = len(hubs)
_cn = [c["country"] for c in R["coastal_none"]]
R["coastal_none_list"] = ", ".join(_cn[:-1]) + " and " + _cn[-1]
R["retrieved"] = "2026"
R["source"] = CREDIT

# ---------- checks ----------
assert R["n"] == 713 and R["n_active"] + R["n_planned"] == R["n"]
assert sum(t["n_active"] for t in tl) == R["n_active"] and sum(t["n_planned"] for t in tl) + R["n_planned_noyear"] == R["n_planned"]
assert sum(e["n"] for e in R["eras"]) == R["n"]
assert R["hyper"]["n"] == sum(b["n_hyper"] for b in R["hyper_bins"])

# ---------- page data ----------
LPI = {p["id"]: i for i, p in enumerate(LPS)}
site = dict(
    eras=[[k, lab, col] for k, lab, a, b, col in ERAS],
    cables=[[c["id"], c["name"], c["year"], int(c["planned"]), c["era"], round(c["length_km"]), int(c["length_source"] == "route"), c["rfs"],
             "; ".join(c["owners"]), "".join(h[0] for h in c["hyperscalers"]), "; ".join(c["suppliers"]), [LPI[i] for i in c["landing_ids"]], c["url"]] for c in C],
    lps=[[p["name"], p["country"], p["lon"], p["lat"], p["n_active"], p["n_planned"]] for p in LPS],
    countries=[[c["country"], c["n_international"], c["n_active"], c["n_international_planned"], int(not c["land_border"]), c["lon"], c["lat"]] for c in CO],
    zones=[[z["key"], z["name"], z["kind"], z["n_active"], z["n_planned"], z["km_active"], z["note"], z["lon"], z["lat"], z["cables"], z["planned"]] for z in K["zones"]],
)
jsave(site, f"{DATA}/site.json")
jsave(R, f"{DATA}/results.json", indent=1)
with open(f"{DATA}/timeline.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["rfs_year", "cables_in_service", "km_in_service", "cables_planned", "km_planned", "cumulative_cables_in_service", "cumulative_km_in_service",
                "cables_part_owned_by_google_meta_amazon_microsoft", "km_part_owned_by_google_meta_amazon_microsoft"])
    for t in tl:
        w.writerow([t["year"], t["n_active"], t["km_active"], t["n_planned"], t["km_planned"], t["cum_n"], t["cum_km"], t["n_hyper"], t["km_hyper"]])
with open(f"{DATA}/hyperscalers.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["name", "rfs_year", "status", "length_km", "hyperscaler_owners", "n_owners", "all_owners"])
    for c in sorted(H, key=lambda c: (c["year"] or 9999, c["name"])):
        w.writerow([dash(c["name"]), c["year"] or "", "planned" if c["planned"] else "in service", round(c["length_km"]), "; ".join(c["hyperscalers"]), c["n_owners"], dash("; ".join(c["owners"]))])
print(f"{R['n_active']} in service ({R['km_active']:,} km), {R['n_planned']} planned ({R['km_planned']:,} km)")
print("peak", R["peak_year"], R["peak_n"], "dotcom", R["dotcom_n"], "bust", R["bust_n"], "km peak", R["km_peak_year"], R["km_peak"])
print("hyper", R["hyper"])
for b in R["hyper_bins"]:
    print(b)
print("single:", R["n_single"], "islands", R["n_single_island"], [s["country"] for s in R["single"] if s["island"]])
print("zero:", R["zero"])
print("top lps", R["top_lps"][:6], "single lp share", R["lp_single_share"])
