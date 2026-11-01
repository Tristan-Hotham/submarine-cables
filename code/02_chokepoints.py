"""Step 2. Choke points: where many cables squeeze through a narrow passage or meet at one landing hub.

Three measures, all on the TeleGeography routes (which are drawn schematically, so treat positions as approximate):
  1. Gates: a line drawn from shore to shore across a strait or sea (both ends checked to lie on Natural Earth land).
     A cable passes the gate if its route crosses the line. The Egypt crossing is a special case: a cable crosses
     Egypt if its route runs over Egyptian land (more than 10 km inside the coast) or it lands on both the
     Mediterranean and the Red Sea or Gulf of Suez coasts.
  2. Hub areas: a named island group, coast or circle around a city; a cable counts if its route enters the area.
  3. A grid of half-degree cells: the number of distinct cables in service whose routes cross each cell. The busiest
     cells, at least 3 degrees apart, are the data's own list of crowded places; each is named after the nearest
     landing point.
Writes data/chokepoints.csv, data/chokepoints.geojson, data/grid_cells.csv, data/grid.json (page), WORK/choke.json.
Run: python3 code/02_chokepoints.py
"""
import csv, collections, os, sys
import numpy as np
from pyproj import Geod
import shapely
from shapely.geometry import shape, LineString, MultiLineString, Point, box, mapping
from shapely.ops import unary_union
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

J = jload(f"{WORK}/cables.json")
C, LPS = J["cables"], J["landing_points"]
LP = {p["id"]: p for p in LPS}
G = Geod(ellps="WGS84")
NE = jload(f"{GEO}/ne_10m_admin_0_countries.geojson")["features"]
LAND = unary_union([shape(f["geometry"]).buffer(0) for f in NE])
EGYPT = [shape(f["geometry"]) for f in NE if f["properties"]["ADMIN"] == "Egypt"][0]
for c in C:
    c["geom"] = MultiLineString(c["lines"])


def circle(lon, lat, km, n=72):
    az = np.linspace(0, 360, n, endpoint=False)
    lo, la, _ = G.fwd(np.full(n, lon), np.full(n, lat), az, np.full(n, km * 1000))
    return shapely.Polygon(list(zip(lo, la)))


# key, name, kind, geometry, region, short note (what the gate or area is)
Q = lambda *pts: shapely.Polygon(pts)
GATES = [
    ("bab", "Bab el-Mandeb", "gate", box(43.0, 12.3, 43.7, 13.0), "Red Sea",
     "the strait between Yemen and Djibouti and Eritrea, the southern door of the Red Sea"),
    ("redsea", "Red Sea (at 20° N)", "gate", box(37.0, 19.8, 40.6, 20.2), "Red Sea",
     "a band across the Red Sea from Sudan to Saudi Arabia, south of Jeddah"),
    ("egypt", "Egypt crossing (Suez)", "egypt", None, "Red Sea",
     "cables that cross Egypt overland between the Mediterranean and the Red Sea"),
    ("hormuz", "Strait of Hormuz", "gate", box(55.9, 25.85, 56.9, 26.9), "Gulf",
     "between Oman's Musandam peninsula and Iran, the door to the Gulf"),
    ("malacca", "Strait of Malacca", "gate", Q((100.6, 1.95), (101.0, 1.6), (102.0, 2.5), (101.6, 2.85)), "Southeast Asia",
     "a band across the strait from Sumatra to Malaysia near Port Dickson"),
    ("luzon", "Luzon Strait", "gate", box(120.0, 19.3, 122.2, 21.7), "East Asia",
     "between Taiwan and Luzon, through the Batanes and Babuyan islands"),
    ("sicily", "Strait of Sicily", "gate", Q((12.3, 37.9), (12.75, 37.55), (11.3, 36.65), (10.85, 37.0)), "Mediterranean",
     "a band from western Sicily to Cap Bon in Tunisia, the waist of the Mediterranean"),
    ("gibraltar", "Strait of Gibraltar", "gate", box(-5.9, 35.78, -5.3, 36.12), "Mediterranean",
     "between Tarifa in Spain and Morocco"),
    ("channel", "Western English Channel", "gate", box(-4.3, 48.75, -3.9, 50.3), "Europe",
     "a band from Plymouth to Brittany, past which cables to the Channel and the North Sea run"),
]
HUBS = [
    ("singapore", "Singapore", "area", circle(103.82, 1.33, 35), "Southeast Asia", "within 35 km of Singapore"),
    ("hongkong", "Hong Kong", "area", circle(114.17, 22.3, 35), "East Asia", "within 35 km of Hong Kong"),
    ("boso", "Chikura and the Boso peninsula, Japan", "area", circle(140.0, 35.0, 50), "East Asia", "within 50 km of Chikura and Maruyama, south of Tokyo"),
    ("marseille", "Marseille", "area", circle(5.37, 43.3, 35), "Mediterranean", "within 35 km of Marseille"),
    ("cornwall", "Cornwall (Bude and Porthcurno)", "area", box(-5.85, 49.9, -4.35, 50.95), "Europe", "Cornwall and its coasts, from Porthcurno to Bude"),
    ("hawaii", "Hawaii", "area", box(-160.6, 18.6, -154.6, 22.6), "Pacific", "the Hawaiian Islands and their waters"),
    ("guam", "Guam", "area", box(144.45, 13.15, 145.1, 13.75), "Pacific", "Guam and its waters"),
    ("fujairah", "Fujairah and the Gulf of Oman", "area", circle(56.33, 25.15, 40), "Gulf", "within 40 km of Fujairah, UAE"),
    ("mumbai", "Mumbai", "area", circle(72.85, 19.05, 35), "South Asia", "within 35 km of Mumbai"),
    ("fortaleza", "Fortaleza", "area", circle(-38.5, -3.75, 35), "Atlantic", "within 35 km of Fortaleza, Brazil"),
    ("florida", "South Florida", "area", box(-80.6, 25.4, -79.7, 26.9), "Atlantic", "the coast from Miami to Boca Raton and its waters"),
    ("newyork", "New York and New Jersey", "area", box(-74.4, 39.4, -71.7, 41.1), "Atlantic", "Long Island and the New Jersey shore"),
]
for k, nm, kind, g, reg, note in GATES:     # every band must reach land on both sides (it spans the whole passage)
    if g is not None:
        parts = g.intersection(LAND)
        parts = list(getattr(parts, "geoms", [parts]))
        assert len(parts) >= 2 or k in ("hormuz", "luzon"), (k, len(parts))


def in_egypt(c):
    inner = EGYPT.buffer(-0.1)
    eg = [LP[i] for i in c["landing_ids"] if LP[i]["country"] == "Egypt"]
    both = any(p["lat"] > 30.8 for p in eg) and any(p["lat"] < 30.3 for p in eg)
    return c["geom"].intersects(inner) or both


rows, feats = [], []
for k, nm, kind, g, reg, note in GATES + HUBS:
    hit = [c for c in C if (in_egypt(c) if kind == "egypt" else c["geom"].intersects(g))]
    act = [c for c in hit if not c["planned"]]
    pl = [c for c in hit if c["planned"]]
    lands = [c for c in act if kind == "area" and any(g.contains(Point(LP[i]["lon"], LP[i]["lat"])) for i in c["landing_ids"])]
    yrs = sorted(c["year"] for c in act)
    rows.append(dict(key=k, name=nm, kind="hub" if kind == "area" else "strait", region=reg, note=note,
                     n_active=len(act), n_planned=len(pl), km_active=round(sum(c["length_km"] for c in act)),
                     km_planned=round(sum(c["length_km"] for c in pl)), n_landing=len(lands),
                     n_since_2015=sum(1 for y in yrs if y >= 2015), first_year=yrs[0] if yrs else None,
                     n_hyper=sum(1 for c in act if c["hyperscalers"]),
                     by_era={e: sum(1 for c in act if c["era"] == e) for e in ERA_COL if e != "planned"},
                     cables=[c["id"] for c in sorted(act, key=lambda c: c["year"])], planned=[c["id"] for c in pl],
                     lon=None, lat=None))
    if kind == "egypt":
        gg = box(29.6, 29.6, 32.7, 31.3)      # drawn as the isthmus box on the page
    else:
        gg = g
    cen = gg.difference(LAND).representative_point() if kind != "egypt" else gg.centroid
    rows[-1]["lon"], rows[-1]["lat"] = round(cen.x, 3), round(cen.y, 3)
    feats.append({"type": "Feature", "properties": {"key": k, "name": nm, "kind": rows[-1]["kind"], "n": len(act), "np": len(pl)},
                  "geometry": mapping(gg)})

# ---------- half-degree grid ----------
RES = 0.5
cell_c = collections.defaultdict(set)
cell_p = collections.defaultdict(set)
for c in C:
    cells = set()
    for ln in c["lines"]:
        a = np.array(ln)
        for p, q in zip(a[:-1], a[1:]):
            n = max(2, int(np.ceil(np.hypot(*(q - p)) / 0.02)))
            pts = p + (q - p) * np.linspace(0, 1, n)[:, None]
            cells.update(zip(np.floor(pts[:, 0] / RES).astype(int).tolist(), np.floor(pts[:, 1] / RES).astype(int).tolist()))
    for k in cells:
        (cell_p if c["planned"] else cell_c)[k].add(c["id"])
lpa = np.array([[p["lon"], p["lat"]] for p in LPS])
cells = []
for k in set(cell_c) | set(cell_p):
    x, y = (k[0] + .5) * RES, (k[1] + .5) * RES
    d = np.hypot((lpa[:, 0] - x) * np.cos(np.radians(y)), lpa[:, 1] - y)
    j = int(d.argmin())
    cells.append(dict(i=k[0], j=k[1], lon=x, lat=y, n=len(cell_c[k]), np=len(cell_p[k]), near=LPS[j]["name"], near_km=round(float(d[j]) * 111.2)))
cells.sort(key=lambda r: (-r["n"], -r["np"]))
top = []
for r in cells:
    if r["n"] < 3:
        break
    if any(abs(r["lon"] - t["lon"]) < 3 and abs(r["lat"] - t["lat"]) < 3 for t in top):
        continue
    top.append(r)
lon_c = collections.Counter();
for r in cells:
    pass
print("busiest half-degree cells (3° apart):")
for r in top[:25]:
    print(f"  {r['n']:3d}  {r['lon']:8.2f} {r['lat']:7.2f}  near {r['near']} ({r['near_km']} km)")

# ---------- landing hubs from the data: cables landing within 50 km of a point ----------
lpx = np.array([[p["lon"], p["lat"]] for p in LPS])
act_ids = {c["id"] for c in C if not c["planned"]}
used = np.zeros(len(LPS), bool)
cand = []
for i, p in enumerate(LPS):
    d = np.array(G.inv(np.full(len(LPS), p["lon"]), np.full(len(LPS), p["lat"]), lpx[:, 0], lpx[:, 1])[2]) / 1000
    near = np.where(d <= 50)[0]
    cs = set().union(*[set(c for c in LPS[k]["cables"] if c in act_ids) for k in near])
    cand.append((len(cs), i, near, cs))
cand.sort(key=lambda t: -t[0])
hubs = []
for n, i, near, cs in cand:
    if used[i]:
        continue
    used[near] = True
    p = LPS[i]
    hubs.append(dict(name=p["name"], country=p["country"], lon=p["lon"], lat=p["lat"], n=n, stations=[LPS[k]["name"] for k in near]))
    if len(hubs) >= 30:
        break
print("landing clusters (50 km):")
for h in hubs[:20]:
    print(f"  {h['n']:3d} {h['name']} ({len(h['stations'])} stations)")

# ---------- write ----------
for r in rows:
    print(f"{r['name']:40s} {r['n_active']:3d} in service, {r['n_planned']:2d} planned, {r['km_active']:,} km, landing {r['n_landing']}")
jsave(dict(zones=rows, top_cells=top[:30], hubs=hubs, res=RES), f"{WORK}/choke.json")
jsave({"type": "FeatureCollection", "features": feats}, f"{DATA}/chokepoints.geojson")
with open(f"{DATA}/chokepoints.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["key", "name", "kind", "region", "definition", "cables_in_service", "cables_planned", "km_in_service", "km_planned",
                "cables_landing_in_area", "in_service_since_2015", "first_rfs_year", "hyperscaler_part_owned", "cable_ids", "planned_cable_ids"])
    for r in rows:
        w.writerow([r["key"], r["name"], r["kind"], r["region"], r["note"], r["n_active"], r["n_planned"], r["km_active"], r["km_planned"],
                    r["n_landing"] if r["kind"] == "hub" else "", r["n_since_2015"], r["first_year"] or "", r["n_hyper"], "; ".join(r["cables"]), "; ".join(r["planned"])])
with open(f"{DATA}/grid_cells.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["lon_min", "lat_min", "lon_max", "lat_max", "cables_in_service", "cables_planned", "nearest_landing_point", "nearest_km"])
    for r in cells:
        w.writerow([r["i"] * RES, r["j"] * RES, (r["i"] + 1) * RES, (r["j"] + 1) * RES, r["n"], r["np"], dash(r["near"]), r["near_km"]])
# page grid: a Web Mercator PNG (2,880 px square, lat +-85.05) of cells with 3 or more cables in service, coloured as on the page
from PIL import Image
NPX = 2880
cnt = np.zeros((int(180 / RES), int(360 / RES)), int)
for r in cells:
    cnt[r["j"] + int(90 / RES), (r["i"] + int(180 / RES)) % int(360 / RES)] = r["n"]
yy = (np.arange(NPX) + .5) / NPX
lat = np.degrees(np.arctan(np.sinh(np.pi * (1 - 2 * yy))))
lon = -180 + (np.arange(NPX) + .5) / NPX * 360
ji = np.clip(np.floor((lat + 90) / RES).astype(int), 0, cnt.shape[0] - 1)
ii = np.clip(np.floor((lon + 180) / RES).astype(int), 0, cnt.shape[1] - 1)
N_ = cnt[ji][:, ii].astype(float)
mx = cnt.max()
t = np.clip(np.log(np.maximum(N_, 2) / 2) / np.log(mx / 2), 0, 1)
a, b = np.array([240, 170, 40]), np.array([130, 12, 40])
rgb = a + (b - a) * t[..., None]
alpha = np.where(N_ >= 3, 245, 0)
Image.fromarray(np.dstack([rgb, alpha]).astype(np.uint8), "RGBA").quantize(colors=64, method=Image.Quantize.FASTOCTREE).save(f"{DATA}/grid_density.png", optimize=True)
# in-service cells with 2 or more cables, [i, j, n]
jsave(dict(res=RES, cells=[[r["i"], r["j"], r["n"]] for r in cells if r["n"] >= 2]), f"{DATA}/grid.json")
