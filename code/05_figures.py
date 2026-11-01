"""Step 5. Static figures: header.png (1200 x 630 social card), the blog figures (release/blog/b_*.png) and the paper
figures (release/paper/fig_*.png, the same images). All numbers come from data/results.json.
Run: python3 code/05_figures.py
"""
import os, sys, shutil
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from figlib import *
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle, Polygon as MPoly
import matplotlib.patheffects as pe

J, K, R = load()
C = J["cables"]
BLOG = os.path.join(ROOT, "release", "blog"); PAP = os.path.join(ROOT, "release", "paper")
os.makedirs(BLOG, exist_ok=True); os.makedirs(PAP, exist_ok=True)
SEG = {c["id"]: cable_segments(c["lines"]) for c in C}
halo = [pe.withStroke(linewidth=3.2, foreground=BG)]


def draw_cables(ax, lw=.9, alpha=.9, only=None, grey=None, z=3):
    for c in era_order(C):
        if only is not None and c["id"] not in only:
            continue
        col = ERA_COL[c["era"]]
        lc = LineCollection(SEG[c["id"]], colors=col, linewidths=lw, alpha=alpha, zorder=z + (1 if c["planned"] else 0),
                            linestyles=(0, (2.2, 1.6)) if c["planned"] else "solid", capstyle="round")
        ax.add_collection(lc)


def era_legend(ax, loc="lower left", fs=10, ncol=5, **kw):
    h = [Line2D([], [], color=ERA_COL[k], lw=3, ls=(0, (2, 1.4)) if k == "planned" else "-") for k, *_ in ERAS]
    l = [("Planned" if k == "planned" else "Ready " + lab) for k, lab, *_ in ERAS]
    return ax.legend(h, l, loc=loc, ncol=ncol, frameon=False, fontsize=fs, handlelength=2.2, **kw)


def world_ax(fig, rect, lat_min=-60, lat_max=82):
    ax = fig.add_axes(rect); ax.set_facecolor(BG)
    outline(ax, lat_min=-90, lat_max=90)
    draw_land(ax)
    x0, _ = FWD.transform(LON0 - 179.999, 0); x1, _ = FWD.transform(LON0 + 179.999, 0)
    _, y0 = FWD.transform(LON0, lat_min); _, y1 = FWD.transform(LON0, lat_max)
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect("equal"); ax.axis("off")
    return ax


# ---------- world map ----------
fig = plt.figure(figsize=(12, 6.6), facecolor=BG)
ax = world_ax(fig, [0.01, 0.09, 0.98, 0.83])
draw_cables(ax, lw=.75)
fig.text(.02, .955, "Every submarine cable in TeleGeography's map, by the year it was ready", fontproperties=DISPB, fontsize=17, color=FG)
fig.text(.02, .915, f"{R['n_active']:,} in service ({R['km_active']:,} km) and {R['n_planned']} planned (dashed). Equal Earth projection centred on 10° E.", fontsize=9.5, color=MUT)
lg = era_legend(fig.axes[0], loc="upper left", bbox_to_anchor=(0.0, -0.005), fs=9.5)
fig.text(.98, .02, "Data: TeleGeography Submarine Cable Map, CC BY-NC-SA 3.0 · maps.tristanhotham.com/submarine-cables", fontsize=7.5, color=MUT, ha="right")
save(fig, f"{BLOG}/b_world.png")

# ---------- timeline ----------
T = R["timeline"]
fig, axs = plt.subplots(2, 1, figsize=(12, 7.2), facecolor=BG, gridspec_kw=dict(height_ratios=[1.25, 1], hspace=.32))
for ax, key, ttl in ((axs[0], ("n_active", "n_planned"), "New cables per year"), (axs[1], ("km_active", "km_planned"), "Kilometres per year (thousand km)")):
    ax.set_facecolor(BG); style(ax)
    k = 1000 if "km" in key[0] else 1
    for t in T:
        y = t["year"]; e = era_of(y, False)
        ax.bar(y, t[key[0]] / k, color=ERA_COL[e] if e else "#999", width=.82, zorder=2)
        ax.bar(y, t[key[1]] / k, bottom=t[key[0]] / k, color=ERA_COL["planned"], width=.82, zorder=2)
    ax.set_xlim(1988.3, R["last_planned_year"] + .7)
    ax.set_title(ttl, loc="left", fontsize=11, color=FG, fontfamily=MONO, pad=4)
    for a, b in ((1998.55, 2001.45), (2015.55, 2026.45)):
        ax.axvspan(a, b, color="#E3E6E2", zorder=0, lw=0)
top = axs[0].get_ylim()[1]
axs[0].text(2000, top * .97, "dot-com boom\n" + f"{R['dotcom_n']} cables, 1999 to 2001", ha="center", va="top", fontsize=9, color=FG)
axs[0].text(2021, top * .97, "the cloud companies arrive", ha="center", va="top", fontsize=9, color=FG)
axs[0].text(2003, max(R["timeline"][y - R["first_year"]]["n_active"] for y in (2002, 2003, 2004)) + 1.5, f"bust: {R['bust_n']}\nin 2002 to 2004", ha="center", va="bottom", fontsize=8.5, color=MUT)
axs[1].annotate(f"{R['km_peak_year']}: {R['km_peak']:,} km", xy=(R["km_peak_year"], R["km_peak"] / 1000), xytext=(1991, R["km_peak"] / 1000 * .92), fontsize=9, color=FG,
                arrowprops=dict(arrowstyle="-", color=MUT, lw=.8))
era_legend(axs[0], loc="upper left", fs=8.5, ncol=1, bbox_to_anchor=(0.0, 0.88))
fig.text(.01, .965, "When each cable was laid", fontproperties=DISPB, fontsize=17, color=FG)
fig.text(.01, .93, f"Ready-for-service year of the {R['n_active']} cables in service and expected year of {R['n_planned'] - R['n_planned_noyear']} planned ones (coral). Retired cables are not in the data.", fontsize=9.2, color=MUT)
fig.text(.99, .01, "Data: TeleGeography Submarine Cable Map, CC BY-NC-SA 3.0", fontsize=7.5, color=MUT, ha="right")
fig.subplots_adjust(left=.06, right=.985, top=.86, bottom=.06)
save(fig, f"{BLOG}/b_timeline.png")

# ---------- hyperscalers ----------
B = R["hyper_bins"]
fig = plt.figure(figsize=(12, 5.4), facecolor=BG)
ax = fig.add_axes([.17, .14, .45, .68]); ax.set_facecolor(BG)
for i, b in enumerate(B):
    y = len(B) - 1 - i
    ax.barh(y, 1, color="#E3E6E2", height=.62)
    ax.barh(y, b["share_km"], color=HOT if b["label"] == "Planned" else COOL, height=.62)
    ax.text(b["share_km"] + .015, y, f"{round(b['share_km'] * 100)}%", va="center", fontsize=11, color=FG, fontweight="medium")
    ax.text(-.02, y, b["label"], va="center", ha="right", fontsize=10.5, color=FG)
    ax.text(.985, y, f"{b['n_hyper']} of {b['n']} cables", va="center", ha="right", fontsize=8.5, color=MUT)
ax.set_xlim(0, 1); ax.set_ylim(-.6, len(B) - .4); ax.axis("off")
ax.set_title("Share of new cable length part-owned by\nGoogle, Meta, Amazon or Microsoft", loc="left", fontsize=10.5, color=FG, fontfamily=MONO)
ax2 = fig.add_axes([.7, .14, .28, .68]); ax2.set_facecolor(BG)
names = ["Google", "Meta", "Microsoft", "Amazon"]
H = R["hyper"]
for i, n in enumerate(names):
    y = len(names) - 1 - i
    ax2.barh(y, H[n]["n_active"], color=COOL, height=.6)
    ax2.barh(y, H[n]["n_planned"], left=H[n]["n_active"], color=HOT, height=.6)
    ax2.text(-.6, y, n, ha="right", va="center", fontsize=10.5, color=FG)
    ax2.text(H[n]["n"] + .6, y, f"{H[n]['n']}", va="center", fontsize=10.5, color=FG)
ax2.set_xlim(0, max(H[n]["n"] for n in names) * 1.15); ax2.axis("off")
ax2.set_title("Cables each part-owns\n(blue in service, coral planned)", loc="left", fontsize=10.5, color=FG, fontfamily=MONO)
fig.text(.01, .93, "From telephone clubs to cloud companies", fontproperties=DISPB, fontsize=17, color=FG)
fig.text(.01, .03, "Owner names matched exactly in TeleGeography's owners field (Amazon as Amazon Web Services). Owners only: capacity bought on other cables is not counted.", fontsize=8, color=MUT)
save(fig, f"{BLOG}/b_hyperscalers.png")

# ---------- Red Sea regional map ----------
Z = {z["key"]: z for z in K["zones"]}
fig = plt.figure(figsize=(12, 8.2), facecolor=BG)
ax = fig.add_axes([.01, .05, .98, .83]); ax.set_facecolor(SEA)
from shapely.geometry import shape as shp
NEL = jload(f"{GEO}/ne_50m_land.geojson")["features"]
kx = np.cos(np.radians(22))
for f in NEL:
    g = shp(f["geometry"])
    for p in getattr(g, "geoms", [g]):
        a = np.array(p.exterior.coords); ax.add_patch(MPoly(np.column_stack([a[:, 0] * kx, a[:, 1]]), fc=LANDC, ec=COAST, lw=.5, zorder=1))
through = set(Z["bab"]["cables"]) | set(Z["bab"]["planned"]) | set(Z["egypt"]["cables"]) | set(Z["egypt"]["planned"])
for c in era_order(C):
    on = c["id"] in through
    for ln in c["lines"]:
        a = np.array(ln)
        ax.plot(a[:, 0] * kx, a[:, 1], color=ERA_COL[c["era"]] if on else "#B9C3C6", lw=1.5 if on else .6, alpha=.95 if on else .7,
                ls=(0, (2.4, 1.6)) if c["planned"] else "-", zorder=4 if on else 2, solid_capstyle="round")
FC = jload(f"{DATA}/chokepoints.geojson")["features"]
for f in FC:
    if f["properties"]["key"] in ("bab", "redsea", "egypt", "hormuz", "fujairah", "sicily"):
        g = shp(f["geometry"]); a = np.array(g.exterior.coords)
        ax.add_patch(MPoly(np.column_stack([a[:, 0] * kx, a[:, 1]]), fc="none", ec=HOT, lw=1.6, zorder=6))
lab = [("bab", 42.0, 10.6, "right"), ("redsea", 41.2, 19.0, "left"), ("egypt", 31.0, 26.0, "right"), ("hormuz", 57.6, 28.4, "left"), ("fujairah", 49.0, 21.0, "left"), ("sicily", 13.5, 29.5, "left")]
for k, x, y, ha in lab:
    z = Z[k]
    ax.text(x * kx, y, f"{z['name']}\n{z['n_active']} in service, {z['n_planned']} planned", fontsize=9.5, color=FG, ha=ha, va="center", zorder=8, path_effects=halo)
ax.set_xlim(10 * kx, 66 * kx); ax.set_ylim(8, 40); ax.set_aspect("equal"); ax.axis("off")
fig.text(.01, .955, "The Red Sea funnel", fontproperties=DISPB, fontsize=17, color=FG)
fig.text(.01, .93, f"Coloured: the {len(set(Z['bab']['cables']) | set(Z['egypt']['cables']))} cables in service and {len(set(Z['bab']['planned']) | set(Z['egypt']['planned']))} planned that pass the Bab el-Mandeb or cross Egypt, by decade.\nGrey: all other cables. Coral outlines: the bands and areas used for counting.", fontsize=9, color=MUT, va="top")
era_legend(ax, loc="upper right", fs=9, ncol=1, facecolor=LANDC)
fig.text(.99, .015, "Data: TeleGeography Submarine Cable Map, CC BY-NC-SA 3.0 (routes schematic); land: Natural Earth", fontsize=7.5, color=MUT, ha="right")
save(fig, f"{BLOG}/b_redsea.png")

# ---------- choke point bars ----------
fig, axs = plt.subplots(1, 2, figsize=(12, 6.4), facecolor=BG)
for ax, kind, ttl in ((axs[0], "strait", "Straits and corridors"), (axs[1], "hub", "Landing hubs")):
    zs = sorted([z for z in K["zones"] if z["kind"] == kind], key=lambda z: (z["n_active"], z["km_active"]))
    ax.set_facecolor(BG)
    for i, z in enumerate(zs):
        ax.barh(i, z["n_active"], color=COOL, height=.66); ax.barh(i, z["n_planned"], left=z["n_active"], color=HOT, height=.66)
        ax.text(z["n_active"] + z["n_planned"] + .5, i, f"{z['n_active']}" + (f" + {z['n_planned']}" if z["n_planned"] else ""), va="center", fontsize=9.5, color=FG)
    ax.set_yticks(range(len(zs))); ax.set_yticklabels([z["name"] for z in zs], fontsize=9.5)
    style(ax, axis="x"); ax.set_xlim(0, max(z["n_active"] + z["n_planned"] for z in K["zones"]) * 1.22)
    ax.set_title(ttl, loc="left", fontsize=11, color=FG, fontfamily=MONO)
fig.text(.01, .95, "Where the network squeezes through", fontproperties=DISPB, fontsize=17, color=FG)
fig.text(.01, .91, "Cables in service (blue) and planned (coral) whose drawn routes cross a band across each strait, or reach each hub area.", fontsize=9.2, color=MUT)
fig.text(.99, .01, "Data: TeleGeography Submarine Cable Map, CC BY-NC-SA 3.0", fontsize=7.5, color=MUT, ha="right")
fig.subplots_adjust(left=.2, right=.98, top=.84, bottom=.08, wspace=.75)
save(fig, f"{BLOG}/b_chokepoints.png")

# ---------- density grid ----------
fig = plt.figure(figsize=(12, 6.6), facecolor=BG)
ax = world_ax(fig, [0.01, 0.09, 0.98, 0.83])
for c in C:
    if not c["planned"]:
        ax.add_collection(LineCollection(SEG[c["id"]], colors="#A7B4B8", linewidths=.35, alpha=.8, zorder=2))
import csv as _csv
cells = list(_csv.DictReader(open(f"{DATA}/grid_cells.csv", encoding="utf-8")))
mx = R["grid_max"]
cm = matplotlib.colors.LinearSegmentedColormap.from_list("d", ["#F0AA28", "#D9482B", "#820C28"])
cells = sorted([r for r in cells if int(r["cables_in_service"]) >= 3], key=lambda r: int(r["cables_in_service"]))
for r in cells:
    lo0, la0 = float(r["lon_min"]), float(r["lat_min"]); n = int(r["cables_in_service"])
    cx, cy = proj(lo0 + .25, la0 + .25)
    s = 1.5 + 9 * (n / mx) ** .8
    ax.scatter([cx], [cy], s=s ** 2 / 2.2, color=cm(np.log(n / 2) / np.log(mx / 2)), zorder=4, lw=0)
for t in R["top_cells"][:6]:
    x, y = proj(t["lon"], t["lat"])
    nm = {"Sakra Island": "Singapore", "Chai Wan": "Hong Kong", "Djibouti City": "Bab el-Mandeb", "Oxford Falls": "Sydney", "Agat": "Guam"}.get(t["near"].split(",")[0], t["near"].split(",")[0])
    ax.annotate(f"{nm} {t['n']}", xy=(x, y), xytext=(6, 6), textcoords="offset points", fontsize=8.5, color=FG, path_effects=halo, zorder=6)
fig.text(.02, .955, "How crowded the sea floor is", fontproperties=DISPB, fontsize=17, color=FG)
fig.text(.02, .935, f"Distinct cables in service crossing each half-degree cell (about 55 km), cells with 3 or more;\nthe busiest has {mx}. Labels name the place nearest the busiest cells.", fontsize=9.5, color=MUT, va="top")
for i, n in enumerate([3, 5, 10, 20, mx]):
    s = 1.5 + 9 * (n / mx) ** .8
    fig.axes[0].scatter([], [], s=s ** 2 / 2.2, color=cm(np.log(n / 2) / np.log(mx / 2)), label=f"{n} cables")
fig.axes[0].legend(loc="upper left", bbox_to_anchor=(0, -0.005), ncol=5, frameon=False, fontsize=9)
fig.text(.98, .02, "Data: TeleGeography Submarine Cable Map, CC BY-NC-SA 3.0", fontsize=7.5, color=MUT, ha="right")
save(fig, f"{BLOG}/b_density.png")

# ---------- most and least connected ----------
fig = plt.figure(figsize=(12, 7), facecolor=BG)
ax = fig.add_axes([.16, .1, .36, .74]); ax.set_facecolor(BG)
tc = R["top_countries"][::-1]
for i, c in enumerate(tc):
    ax.barh(i, c["n"], color=COOL, height=.66); ax.barh(i, c["planned"], left=c["n"], color=HOT, height=.66)
    ax.text(c["n"] + c["planned"] + .6, i, f"{c['n']}" + (f" + {c['planned']}" if c["planned"] else ""), va="center", fontsize=9.5)
ax.set_yticks(range(len(tc))); ax.set_yticklabels([c["country"] for c in tc], fontsize=9.5); style(ax, axis="x")
ax.set_title("Most international cables", loc="left", fontsize=11, color=FG, fontfamily=MONO)
ax2 = fig.add_axes([.58, .1, .41, .74]); ax2.axis("off")
ax2.set_title(f"Islands with one international cable ({R['n_single_island']})\nand that cable; coral: planned cables", loc="left", fontsize=11, color=FG, fontfamily=MONO)
isl = [s for s in R["single"] if s["island"]]
for i, s in enumerate(isl):
    yy = 1 - (i + .6) / (len(isl) + 1.5)
    ax2.text(0, yy, s["country"].replace("Saint Helena, Ascension and Tristan da Cunha", "St Helena, Ascension, Tristan").replace("British Indian Ocean Territory", "British Indian Ocean Terr."), fontsize=9.4, color=FG, transform=ax2.transAxes, fontweight="medium")
    if s["planned"]:
        ax2.text(1.0, yy, f"+{s['planned']}", fontsize=9, color=HOT, transform=ax2.transAxes, ha="right", fontweight="medium")
    ax2.text(.48, yy, s["cable"], fontsize=8, color=MUT, transform=ax2.transAxes)
ax2.text(0, 1 - (len(isl) + .9) / (len(isl) + 1.5), "Tuvalu has no cable in service, only a planned one.", fontsize=9, color=HOT, transform=ax2.transAxes)
fig.text(.01, .95, "Most and least connected", fontproperties=DISPB, fontsize=17, color=FG)
fig.text(.01, .91, "International cables in service (blue) and planned (coral) landing in each country or territory; islands are places with no land border.", fontsize=9.2, color=MUT)
fig.text(.99, .01, "Data: TeleGeography Submarine Cable Map, CC BY-NC-SA 3.0; islands from Natural Earth", fontsize=7.5, color=MUT, ha="right")
save(fig, f"{BLOG}/b_connected.png")

for f in ("world", "timeline", "hyperscalers", "redsea", "chokepoints", "density", "connected"):
    shutil.copy(f"{BLOG}/b_{f}.png", f"{PAP}/fig_{f}.png")

# ---------- header 1200 x 630 ----------
fig = plt.figure(figsize=(12, 6.3), facecolor=BG, dpi=100)
ax = world_ax(fig, [0.30, 0.02, 0.74, 0.86], lat_min=-58, lat_max=78)
draw_cables(ax, lw=.85)
fig.text(.035, .86, "The internet's\nseabed", fontproperties=DISP, fontsize=46, color=FG, va="top", linespacing=.92)
fig.text(.035, .53, f"{R['n_active']} submarine cables\nin service,\n{R['km_active'] / 1e6:.1f} million km,\nand {R['n_planned']} planned", fontsize=13, color=FG, va="top", linespacing=1.4)
fig.text(.035, .30, "Coloured by the decade\neach was laid", fontsize=11, color=MUT, va="top", linespacing=1.4)
for i, (k, lab, *_r) in enumerate(ERAS):
    y = .185 - i * .036
    fig.add_artist(Line2D([.035, .07], [y, y], color=ERA_COL[k], lw=3.2, ls=(0, (2, 1.3)) if k == "planned" else "-", transform=fig.transFigure))
    fig.text(.08, y, "planned" if k == "planned" else lab, fontsize=10, color=FG, va="center")
fig.text(.965, .035, "maps.tristanhotham.com/submarine-cables · data: TeleGeography", fontsize=9, color=MUT, ha="right")
fig.savefig(os.path.join(ROOT, "header.png"), dpi=100, facecolor=BG)
plt.close(fig)
print("figures written")
