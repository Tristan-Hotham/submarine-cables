"""Step 1. Clean the TeleGeography files into one table of cables, one of landing points and one of countries.

Writes data/cables.csv, data/landing_points.csv, data/countries.csv, data/cables.geojson (routes for the page, lightly
simplified), data/landing_points.geojson, and WORK/cables.json (full precision routes and attributes for later steps).
Run: python3 code/01_clean.py
"""
import csv, collections, os, sys
import numpy as np
from pyproj import Geod
import shapely
from shapely.geometry import shape, MultiLineString, mapping, Point
from shapely.ops import unary_union
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

G = Geod(ellps="WGS84")
D = jload(f"{CABLES}/cable_details.json")
GEOJ = jload(f"{CABLES}/cable-geo.json")
LPJ = jload(f"{CABLES}/landing-point-geo.json")
assert len(D) == 713

# ---------- routes ----------
lines = collections.defaultdict(list)
for f in GEOJ["features"]:
    for ln in f["geometry"]["coordinates"]:
        if len(ln) >= 2:
            lines[f["properties"]["id"]].append([tuple(c[:2]) for c in ln])


def route_km(lns):
    return sum(G.line_length([c[0] for c in ln], [c[1] for c in ln]) for ln in lns) / 1000


def parse_len(s):
    if not s or not str(s).strip():
        return None
    m = re.match(r"^\s*([\d,\.]+)\s*km\s*$", str(s))
    assert m, s
    return float(m.group(1).replace(",", ""))


# ---------- countries: land borders from Natural Earth (to tell islands from places with a land route) ----------
NE = jload(f"{GEO}/ne_10m_admin_0_countries.geojson")["features"]
ALIAS = {"Congo, Dem. Rep.": "Democratic Republic of the Congo", "Congo, Rep.": "Republic of the Congo", "Côte d'Ivoire": "Ivory Coast",
         "United States": "United States of America", "Virgin Islands (U.K.)": "British Virgin Islands", "Virgin Islands (U.S.)": "United States Virgin Islands",
         "Micronesia": "Federated States of Micronesia", "Bahamas": "The Bahamas", "Cape Verde": "Cabo Verde", "Tanzania": "United Republic of Tanzania",
         "Sao Tome and Principe": "São Tomé and Principe", "Saint Helena, Ascension and Tristan da Cunha": "Saint Helena", "Curaçao": "Curaçao",
         "Saint Barthélemy": "Saint Barthelemy", "Saint Martin": "Saint Martin", "Bonaire, Sint Eustatius and Saba": "Netherlands",
         "Christmas Island": "Indian Ocean Territories", "Cocos (Keeling) Islands": "Indian Ocean Territories", "Gambia": "Gambia",
         "Guinea-Bissau": "Guinea-Bissau", "Timor-Leste": "East Timor", "Serbia": "Republic of Serbia", "Hong Kong": "Hong Kong S.A.R.",
         "Macau": "Macao S.A.R", "Eswatini": "eSwatini", "North Macedonia": "North Macedonia", "Tokelau": "New Zealand",
         "British Indian Ocean Territory": "British Indian Ocean Territory", "Falkland Islands": "Falkland Islands"}
# French overseas departments are part of 'France' in Natural Earth admin 0: set by hand.
MANUAL_ISLAND = {"Réunion": True, "Martinique": True, "Guadeloupe": True, "Mayotte": True, "French Guiana": False, "Tokelau": True,
                 "Bonaire, Sint Eustatius and Saba": True}
ne_by = {}
for f in NE:
    p = f["properties"]
    for k in ("ADMIN", "NAME", "NAME_LONG", "GEOUNIT", "SOVEREIGNT", "BRK_NAME", "NAME_EN"):
        if p.get(k) and p[k] not in ne_by:
            ne_by[p[k]] = f
geoms = [shape(f["geometry"]) for f in NE]
tree = shapely.STRtree(geoms)


def land_border(cname):
    if cname in MANUAL_ISLAND:
        return not MANUAL_ISLAND[cname]
    f = ne_by.get(ALIAS.get(cname, cname))
    assert f is not None, cname
    g = shape(f["geometry"])
    # touching any other country (within about 1 km) counts as a land border
    gb = g.buffer(0.01)
    for i in tree.query(gb):
        if NE[i] is f:
            continue
        if NE[i]["properties"]["ADMIN"] == f["properties"]["ADMIN"]:
            continue
        if gb.intersects(geoms[i]):
            return True
    return False


# ---------- cables ----------
lp_xy = {f["properties"]["id"]: tuple(f["geometry"]["coordinates"]) for f in LPJ["features"]}
cables = []
for x in D:
    owners = [o.strip() for o in (x["owners"] or "").split(",") if o.strip()]
    hyp = sorted({h for h, names in HYPER.items() if any(o in names for o in owners)})
    lns = lines[x["id"]]
    assert lns, x["id"]
    rk = route_km(lns)
    sl = parse_len(x["length"])
    lps = x["landing_points"]
    ctry = sorted({p["country"] for p in lps})
    planned = bool(x["is_planned"])
    yr = x["rfs_year"]
    cables.append(dict(id=x["id"], name=x["name"].strip(), rfs=x["rfs"] or "", year=yr, planned=planned, era=era_of(yr, planned),
                       length_stated_km=sl, route_km=round(rk, 1), length_km=sl if sl else round(rk), length_source="TeleGeography" if sl else "route",
                       owners=owners, n_owners=len(owners), hyperscalers=hyp, suppliers=[s.strip() for s in (x["suppliers"] or "").split(",") if s.strip()],
                       landing_ids=[p["id"] for p in lps], countries=ctry, n_landings=len(lps), n_countries=len(ctry),
                       international=len(ctry) > 1, url=x["url"] or "", notes=x["notes"] or "", lines=lns))
by_id = {c["id"]: c for c in cables}
assert all(c["era"] for c in cables if not c["planned"]), [c["name"] for c in cables if not c["era"]]

# ---------- landing points ----------
lpinfo = {}
for x in D:
    for p in x["landing_points"]:
        lpinfo.setdefault(p["id"], dict(id=p["id"], name=p["name"].strip(), country=p["country"], tbd=bool(p["is_tbd"]), cables=[]))
        lpinfo[p["id"]]["cables"].append(x["id"])
lps = []
for k, v in lpinfo.items():
    lon, lat = lp_xy[k]
    cs = [by_id[c] for c in v["cables"]]
    act = [c for c in cs if not c["planned"]]
    lps.append(dict(id=k, name=v["name"], country=v["country"], lon=round(lon, 5), lat=round(lat, 5), tbd=v["tbd"],
                    n_active=len(act), n_planned=len(cs) - len(act), n_all=len(cs),
                    first_year=min([c["year"] for c in act if c["year"]], default=None),
                    cables=[c["id"] for c in sorted(cs, key=lambda c: (c["planned"], c["year"] or 9999))]))
lps.sort(key=lambda p: (-p["n_active"], -p["n_all"], p["name"]))

# ---------- countries ----------
cty = collections.defaultdict(lambda: dict(active=[], planned=[], intl=[], intl_planned=[], dom=[], lps=set()))
for c in cables:
    for k in c["countries"]:
        e = cty[k]
        (e["planned"] if c["planned"] else e["active"]).append(c["id"])
        if c["international"]:
            (e["intl_planned"] if c["planned"] else e["intl"]).append(c["id"])
        elif not c["planned"]:
            e["dom"].append(c["id"])
for p in lps:
    cty[p["country"]]["lps"].add(p["id"])
countries = []
for k, e in cty.items():
    pts = [p for p in lps if p["country"] == k]
    countries.append(dict(country=k, n_active=len(e["active"]), n_international=len(e["intl"]), n_domestic=len(e["dom"]), n_planned=len(e["planned"]),
                          n_international_planned=len(e["intl_planned"]), n_landing_points=len(e["lps"]), land_border=land_border(k),
                          lon=round(float(np.mean([p["lon"] for p in pts])), 3), lat=round(float(np.mean([p["lat"] for p in pts])), 3),
                          intl_cables=e["intl"], intl_planned_cables=e["intl_planned"], domestic_cables=e["dom"], planned_cables=e["planned"]))
countries.sort(key=lambda c: (-c["n_international"], -c["n_active"], c["country"]))

# ---------- write ----------
jsave(dict(cables=cables, landing_points=lps, countries=countries), f"{WORK}/cables.json")
with open(f"{DATA}/cables.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["id", "name", "rfs", "rfs_year", "status", "era", "length_km", "length_source", "length_stated_km", "route_km", "n_landings", "n_countries",
                "international", "countries", "owners", "n_owners", "hyperscaler_owners", "suppliers", "url"])
    for c in sorted(cables, key=lambda c: (c["year"] or 9999, c["name"])):
        w.writerow([c["id"], dash(c["name"]), dash(c["rfs"]), c["year"] or "", "planned" if c["planned"] else "in service", c["era"], c["length_km"], c["length_source"],
                    c["length_stated_km"] or "", c["route_km"], c["n_landings"], c["n_countries"], int(c["international"]), "; ".join(c["countries"]),
                    dash("; ".join(c["owners"])), c["n_owners"], "; ".join(c["hyperscalers"]), dash("; ".join(c["suppliers"])), c["url"]])
with open(f"{DATA}/landing_points.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["id", "name", "country", "lon", "lat", "cables_in_service", "cables_planned", "first_rfs_year", "cable_ids"])
    for p in lps:
        w.writerow([p["id"], dash(p["name"]), p["country"], p["lon"], p["lat"], p["n_active"], p["n_planned"], p["first_year"] or "", "; ".join(p["cables"])])
with open(f"{DATA}/countries.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["country", "international_cables_in_service", "domestic_cables_in_service", "all_cables_in_service", "planned_cables", "planned_international_cables",
                "landing_points", "has_land_border", "international_cable_ids"])
    for c in countries:
        w.writerow([c["country"], c["n_international"], c["n_domestic"], c["n_active"], c["n_planned"], c["n_international_planned"], c["n_landing_points"],
                    int(c["land_border"]), "; ".join(c["intl_cables"])])

# page routes: simplified (about 1 km) and rounded to 3 decimals
feats = []
for c in sorted(cables, key=lambda c: (c["planned"], c["year"] or 9999)):
    g = MultiLineString(c["lines"]).simplify(0.01, preserve_topology=False)
    gl = [g] if g.geom_type == "LineString" else list(g.geoms)
    co = [[[round(x, 3), round(y, 3)] for x, y in l.coords] for l in gl if len(l.coords) >= 2]
    feats.append({"type": "Feature", "properties": {"id": c["id"]}, "geometry": {"type": "MultiLineString", "coordinates": co}})
jsave({"type": "FeatureCollection", "features": feats}, f"{DATA}/cables.geojson")
jsave({"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {"id": p["id"], "name": p["name"], "country": p["country"], "n": p["n_active"], "np": p["n_planned"]},
                                                  "geometry": {"type": "Point", "coordinates": [p["lon"], p["lat"]]}} for p in lps]}, f"{DATA}/landing_points.geojson")
print(len(cables), "cables;", sum(c["planned"] for c in cables), "planned;", len(lps), "landing points;", len(countries), "countries")
print("stated length missing:", sum(1 for c in cables if not c["length_stated_km"]))
r = [(c["length_stated_km"], c["route_km"]) for c in cables if c["length_stated_km"]]
print("route/stated median", np.median([b / a for a, b in r]))
print("islands:", sorted(c["country"] for c in countries if not c["land_border"]))
