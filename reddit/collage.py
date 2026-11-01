"""Reddit collage (r/dataisbeautiful style): every submarine cable coloured by decade laid, the choke points numbered,
an inset of the crowded corridor from the Atlantic to the Gulf, a timeline panel, the cloud companies' share and a key.
Light background. Number labels are placed automatically: a label may sit only on open sea or on the paper round the
world map (never on land or a cable), may not touch another label or leader line, and its leader line may not cross
another label or leader line. Writes reddit/the_internets_seabed.png (3000 px wide).
Run: python3 reddit/collage.py
"""
import os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "code"))
from figlib import *
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, Rectangle, Polygon as MPoly
from shapely.geometry import shape as shp

J, K, R = load()
C = J["cables"]
Z = {z["key"]: z for z in K["zones"]}
SEG = {c["id"]: cable_segments(c["lines"]) for c in C}
DPI = 200
W_IN, H_IN = 15, 23.6
FIGW, FIGH = W_IN * DPI, H_IN * DPI
LAT_MIN, LAT_MAX = -57, 78
x0, _ = FWD.transform(LON0 - 179.999, 0); x1, _ = FWD.transform(LON0 + 179.999, 0)
_, y0 = FWD.transform(LON0, LAT_MIN); _, y1 = FWD.transform(LON0, LAT_MAX)
MAP_H = 0.97 * W_IN / H_IN * (y1 - y0) / (x1 - x0)
MAP_RECT = [0.015, 0.872 - MAP_H, 0.97, MAP_H]
# inset: Atlantic approaches to the Gulf, equirectangular with x scaled by cos(32°)
KX = np.cos(np.radians(32))
IN_LON, IN_LAT = (-9.0, 62.0), (9.5, 52.5)
IN_W = 0.50
IN_H = IN_W * W_IN / H_IN * (IN_LAT[1] - IN_LAT[0]) / ((IN_LON[1] - IN_LON[0]) * KX)
IN_TOP = MAP_RECT[1] - .085
IN_RECT = [0.948 - IN_W, IN_TOP - IN_H, IN_W, IN_H]

INSET = ["sicily", "redsea", "bab", "fujairah", "cornwall", "marseille", "egypt", "hormuz"]
WORLD = ["singapore", "boso", "guam", "hongkong", "newyork", "luzon", "malacca", "mumbai", "florida", "hawaii", "fortaleza"]
KEYS = sorted(INSET + WORLD, key=lambda k: (-Z[k]["n_active"], -Z[k]["km_active"]))
SHORT = {"boso": "Boso peninsula, Japan", "cornwall": "Cornwall", "fujairah": "Fujairah, UAE", "newyork": "New York and New Jersey",
         "egypt": "Egypt crossing (Suez)", "redsea": "Red Sea at 20° N", "florida": "South Florida"}


def world_axes(fig):
    ax = fig.add_axes(MAP_RECT); ax.set_facecolor(BG)
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect("equal"); ax.axis("off")
    return ax


def inset_axes(fig):
    ax = fig.add_axes(IN_RECT); ax.set_facecolor(SEA)
    ax.set_xlim(IN_LON[0] * KX, IN_LON[1] * KX); ax.set_ylim(*IN_LAT); ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values(): s.set_color(FG); s.set_linewidth(1.1)
    return ax


NEL = [shp(f["geometry"]) for f in jload(f"{GEO}/ne_50m_land.geojson")["features"]]


def inset_land(ax, fc, ec, lw):
    from shapely.geometry import box as sbox
    win = sbox(IN_LON[0] - 3, IN_LAT[0] - 3, IN_LON[1] + 3, IN_LAT[1] + 3)
    for g in NEL:
        g = g.buffer(0).intersection(win)         # clip first: Afro-Eurasia's outline wraps round the date line
        for p in getattr(g, "geoms", [g]):
            if p.is_empty or p.geom_type != "Polygon":
                continue
            from matplotlib.path import Path
            from matplotlib.patches import PathPatch
            rings = [np.array(p.exterior.coords)] + [np.array(r.coords) for r in p.interiors]
            verts = np.concatenate([np.column_stack([r[:, 0] * KX, r[:, 1]]) for r in rings]); codes = []
            for r in rings:
                codes += [Path.MOVETO] + [Path.LINETO] * (len(r) - 2) + [Path.CLOSEPOLY]
            ax.add_patch(PathPatch(Path(verts, codes), fc=fc, ec=ec, lw=lw, zorder=1))


def inset_cables(ax, colour=None, lw=1.2, mask=False):
    for c in era_order(C):
        segs = [np.column_stack([np.array(l)[:, 0] * KX, np.array(l)[:, 1]]) for l in c["lines"]]
        segs = [s for s in segs if (s[:, 0].max() > IN_LON[0] * KX - 2) and (s[:, 0].min() < IN_LON[1] * KX + 2)]
        if not segs:
            continue
        ax.add_collection(LineCollection(segs, colors=colour or ERA_COL[c["era"]], linewidths=lw, alpha=1 if mask else .92,
                                         linestyles="solid" if (mask or not c["planned"]) else (0, (2.4, 1.6)), capstyle="round", zorder=3 + c["planned"]))


# ---------- occupancy mask at the final resolution ----------
mfig = plt.figure(figsize=(W_IN, H_IN), dpi=DPI, facecolor="black")
mw = world_axes(mfig)            # paper inside the map frame but outside the ellipse is allowed
mw.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc="black", ec="none", zorder=0))
outline(mw, fc="white", ec="white", lw=0, z=0.5)   # world labels: open sea only
draw_land(mw, fc="black", ec="black", lw=1.2, z=2)
for c in C:
    mw.add_collection(LineCollection(SEG[c["id"]], colors="black", linewidths=2.0, zorder=3))
# the paper just above, right of and below the inset is allowed for its labels
mfig.add_artist(Rectangle((IN_RECT[0], IN_RECT[1] - .02), IN_RECT[2] + .04, IN_RECT[3] + .036, transform=mfig.transFigure, fc="white", ec="none", zorder=0))
mi = inset_axes(mfig); mi.set_facecolor("white")
inset_land(mi, "black", "black", 1.0); inset_cables(mi, "black", 1.3, mask=True)
for s in mi.spines.values(): s.set_color("black"); s.set_linewidth(6)
# inset labels go on the paper outside the frame only (never on the inset's land or sea), like a callout list
mfig.add_artist(Rectangle((IN_RECT[0], IN_RECT[1]), IN_RECT[2], IN_RECT[3], transform=mfig.transFigure, fc="black", ec="black", zorder=50))
mfig.canvas.draw()
BUSY = np.asarray(mfig.canvas.buffer_rgba())[:, :, 0] < 128
plt.close(mfig)
HPX, WPX = BUSY.shape


def px(ax, x, y):
    X, Y = ax.transData.transform((x, y)); return X, HPX - Y


def unpx(ax, X, Y):
    return ax.transData.inverted().transform((X, HPX - Y))


def seg_hits_circle(p, q, c, r):
    p, q, c = map(np.array, (p, q, c)); d = q - p
    t = np.clip(np.dot(c - p, d) / max(np.dot(d, d), 1e-9), 0, 1)
    return np.hypot(*(p + t * d - c)) < r


def segs_cross(a, b, c, d):
    o = lambda p, q, r: np.sign((q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0]))
    return o(a, b, c) != o(a, b, d) and o(c, d, a) != o(c, d, b)


RAD = 19
M_ = 8
yy_, xx_ = np.mgrid[-RAD - M_:RAD + M_ + 1, -RAD - M_:RAD + M_ + 1]
DISK = (xx_ ** 2 + yy_ ** 2) <= (RAD + M_) ** 2
taken = BUSY.copy()
placed, leaders = [], []      # all labels and leaders, both maps


def free(X, Y):
    X, Y = int(round(X)), int(round(Y)); a, b = Y - RAD - M_, X - RAD - M_
    if a < 0 or b < 0 or a + DISK.shape[0] > HPX or b + DISK.shape[1] > WPX:
        return False
    return not (taken[a:a + DISK.shape[0], b:b + DISK.shape[1]] & DISK).any()


def place(anchors, keys):
    out = []
    for k in keys:
        A = anchors[k]; best = None
        for r in range(36, 700, 5):
            for th in np.linspace(0, 2 * np.pi, max(24, int(r / 3)), endpoint=False):
                X, Y = A[0] + r * np.cos(th), A[1] + r * np.sin(th)
                if not free(X, Y):
                    continue
                s = (A[0] + 9 * np.cos(th), A[1] + 9 * np.sin(th)); e = (X - RAD * np.cos(th), Y - RAD * np.sin(th))
                if any(seg_hits_circle(s, e, (p[0], p[1]), RAD + 3) for p in placed):
                    continue
                if any(seg_hits_circle(s, e, anchors[kk], 10) for kk in anchors if kk != k):
                    continue
                if any(segs_cross(s, e, a, b) for a, b in leaders):
                    continue
                best = (X, Y, s, e); break
            if best:
                break
        assert best, k
        X, Y, s, e = best
        placed.append((X, Y, k)); leaders.append((s, e)); out.append((k, X, Y, s, e))
        xi, yi = int(round(X)), int(round(Y)); taken[yi - RAD - M_:yi + RAD + M_ + 1, xi - RAD - M_:xi + RAD + M_ + 1] |= DISK
        for t in np.linspace(0, 1, 80):
            a_, b_ = int(s[0] + (e[0] - s[0]) * t), int(s[1] + (e[1] - s[1]) * t)
            taken[max(0, b_ - 3):b_ + 4, max(0, a_ - 3):a_ + 4] = True
    return out


def draw_labels(ax, anchors, res):
    unit = ax.transData.inverted().transform((1, 0))[0] - ax.transData.inverted().transform((0, 0))[0]
    for k in anchors:
        ax.add_patch(Circle(unpx(ax, *anchors[k]), radius=8 * unit, fc="none", ec=HOT, lw=1.7, zorder=8, clip_on=False))
    for k, X, Y, s, e in res:
        ax.plot(*zip(unpx(ax, *s), unpx(ax, *e)), color=FG, lw=.85, zorder=8, solid_capstyle="round", clip_on=False)
        cx, cy = unpx(ax, X, Y)
        ax.add_patch(Circle((cx, cy), radius=RAD * unit, fc=PAPER, ec=FG, lw=1.1, zorder=9, clip_on=False))
        ax.text(cx, cy, str(KEYS.index(k) + 1), ha="center", va="center_baseline", fontsize=10, color=FG, fontweight="medium", zorder=10, clip_on=False)


# ---------- figure ----------
fig = plt.figure(figsize=(W_IN, H_IN), dpi=DPI, facecolor=BG)
ax = world_axes(fig)
outline(ax, fc=SEA, ec="#B9C6CA", lw=1)
draw_land(ax, fc=LANDC, ec=COAST, lw=.45)
for c in era_order(C):
    ax.add_collection(LineCollection(SEG[c["id"]], colors=ERA_COL[c["era"]], linewidths=1.0 if not c["planned"] else .9, alpha=.92,
                                     linestyles=(0, (2.4, 1.6)) if c["planned"] else "solid", capstyle="round", zorder=3 + c["planned"]))
# the inset's area on the world map
bx = np.array([[IN_LON[0], IN_LAT[0]], [IN_LON[1], IN_LAT[0]], [IN_LON[1], IN_LAT[1]], [IN_LON[0], IN_LAT[1]], [IN_LON[0], IN_LAT[0]]])
dense = np.concatenate([np.linspace(bx[i], bx[i + 1], 40) for i in range(4)])
ax.plot(*proj(dense[:, 0], dense[:, 1]), color=FG, lw=1.1, ls=(0, (4, 2.5)), zorder=7)
ia = inset_axes(fig)
inset_land(ia, LANDC, COAST, .5); inset_cables(ia, lw=1.15)
fig.canvas.draw()
wa = {k: px(ax, *proj(Z[k]["lon"], Z[k]["lat"])) for k in WORLD}
ina = {k: px(ia, Z[k]["lon"] * KX, Z[k]["lat"]) for k in INSET}
# reserve every anchor ring before placing, so no label covers another place's ring
for A in list(wa.values()) + list(ina.values()):
    xi, yi = int(A[0]), int(A[1]); taken[yi - 12:yi + 13, xi - 12:xi + 13] = True
res_w = place(wa, [k for k in KEYS if k in WORLD])
res_i = place(ina, [k for k in KEYS if k in INSET])
draw_labels(ax, wa, res_w); draw_labels(ia, ina, res_i)
for k, X, Y, s_, e_ in res_w + res_i:
    xi, yi = int(round(X)), int(round(Y))
    d = (np.mgrid[-RAD:RAD + 1, -RAD:RAD + 1] ** 2).sum(0) <= RAD ** 2
    assert not (BUSY[yi - RAD:yi + RAD + 1, xi - RAD:xi + RAD + 1] & d).any(), ("label on land, cable or inset", k)
    for X2, Y2, k2 in placed:
        if k2 != k:
            assert not seg_hits_circle(s_, e_, (X2, Y2), RAD), ("leader crosses label", k, k2)
print("labels checked:", len(res_w), "on open sea,", len(res_i), "on paper outside the inset")
# label the box on the world map and title the inset
fig.text(IN_RECT[0], IN_RECT[1] + IN_RECT[3] + .022, "Inset: from the Atlantic approaches to the Gulf (dashed box on the map)", fontsize=10.5, color=FG, fontweight="medium")

# ---------- title ----------
fig.text(.03, .972, "The internet's seabed", fontproperties=DISP, fontsize=58, color=FG, va="top")
fig.text(.03, .926, f"Every submarine cable in TeleGeography's map, coloured by when it was ready for service: {R['n_active']} in service\n"
         f"({R['km_active'] / 1e6:.1f} million km, {R['times_round_earth']:.0f} times round the Earth) and {R['n_planned']} planned. Coral rings mark the choke points,\n"
         "where many cables squeeze through one strait or crowd onto one stretch of coast.", fontsize=12.6, fontfamily=SER, color=FG, va="top", linespacing=1.45)

# ---------- legend under the map ----------
ly = MAP_RECT[1] - .012
lx = .03
for k, lab, *_r in ERAS:
    fig.add_artist(Line2D([lx, lx + .03], [ly, ly], color=ERA_COL[k], lw=3.4, ls=(0, (2, 1.3)) if k == "planned" else "-", transform=fig.transFigure))
    t = "Planned" if k == "planned" else f"Ready {lab}"
    fig.text(lx + .036, ly, t, fontsize=10.5, va="center", color=FG)
    lx += .036 + len(t) * .0072 + .03
fig.add_artist(Circle((.038, ly - .02), .0042, transform=fig.transFigure, fc="none", ec=HOT, lw=1.7))
fig.text(.05, ly - .02, "Choke point (numbers in the key)", fontsize=10.5, va="center", color=FG)
fig.text(.97, ly - .02, "Equal Earth projection centred on 10° E. Routes are drawn schematically.", fontsize=9, va="center", ha="right", color=MUT)

# ---------- key (left of the inset) ----------
ky = IN_TOP + .022
fig.text(.03, ky, "Choke points: cables in service through each\nstrait or reaching each hub (+ planned)", fontsize=10.5, color=FG, fontweight="medium", va="bottom", linespacing=1.35)
per = int(np.ceil(len(KEYS) / 2)); step = .0172
for i, k in enumerate(KEYS):
    c, r = divmod(i, per)
    x = .03 + c * .205; y = ky - .016 - r * step
    fig.add_artist(Circle((x + .007, y), .0058, transform=fig.transFigure, fc=PAPER, ec=FG, lw=1))
    fig.text(x + .007, y, str(i + 1), fontsize=8.3, ha="center", va="center_baseline", color=FG)
    z = Z[k]
    fig.text(x + .018, y, SHORT.get(k, z["name"]), fontsize=9.6, va="center", color=FG)
    fig.text(x + .195, y, f"{z['n_active']}" + (f" +{z['n_planned']}" if z["n_planned"] else ""), fontsize=9.6, va="center", ha="right", color=FG, fontweight="medium")

# ---------- stats ----------
sy = IN_RECT[1] - .03
stats = [(f"{R['n_active']}", "cables in service,\nthe oldest from " + str(R["first_year"]), COOL),
         (f"{R['dotcom_n']}", "of them ready in the\ndot-com boom, 1999 to 2001", ERA_COL["2000s"]),
         (f"{round(R['hyper']['share_planned_km'] * 100)}%", "of planned length part-owned\nby Google, Meta, Amazon or Microsoft", HOT),
         (f"{R['n_single_island']}", "islands hanging on a single\ninternational cable", ERA_COL["2020s"])]
for i, (big, small, col) in enumerate(stats):
    x = .03 + i * .24
    fig.text(x, sy, big, fontproperties=DISP, fontsize=40, color=col, va="top")
    fig.text(x, sy - .037, small, fontsize=10.5, color=FG, va="top", linespacing=1.35)

# ---------- timeline panel ----------
ty = sy - .085
T = R["timeline"]
tax = fig.add_axes([.06, .075, .52, ty - .115]); tax.set_facecolor(BG); style(tax)
for t in T:
    e = era_of(t["year"], False)
    tax.bar(t["year"], t["n_active"], color=ERA_COL[e], width=.8, zorder=2)
    tax.bar(t["year"], t["n_planned"], bottom=t["n_active"], color=ERA_COL["planned"], width=.8, zorder=2)
for a, b in ((1998.5, 2001.5), (2015.5, 2026.5)):
    tax.axvspan(a, b, color="#E3E6E2", zorder=0, lw=0)
tax.set_xlim(1988.3, R["last_planned_year"] + .7); tax.set_ylim(0, 58)
tax.text(2000, 56, "dot-com\nboom", ha="center", va="top", fontsize=9.5, color=FG)
tax.text(2021, 56, "the cloud companies\narrive", ha="center", va="top", fontsize=9.5, color=FG)
tax.text(2028.1, 50, "planned", ha="left", va="bottom", fontsize=9.5, color=HOT)
tax.set_ylabel("new cables per year", fontsize=9.5, color=MUT)
fig.text(.03, ty, "When each cable was laid", fontsize=12.5, fontweight="medium", color=FG, va="top")
fig.text(.03, ty - .015, "By ready-for-service year. Only today's cables: retired ones are not in the data.", fontsize=9.3, color=MUT, va="top")

# ---------- hyperscaler panel ----------
hx = .64
fig.text(hx, ty, "Who lays them now", fontsize=12.5, fontweight="medium", color=FG, va="top")
fig.text(hx, ty - .015, "Share of new cable length part-owned by\nGoogle, Meta, Amazon or Microsoft", fontsize=9.3, color=MUT, va="top")
hax = fig.add_axes([hx + .1, .065, .95 - hx - .1, ty - .105]); hax.set_facecolor(BG)
B = R["hyper_bins"]
for i, b in enumerate(B):
    y = len(B) - 1 - i
    hax.barh(y, 1, color="#E3E6E2", height=.62); hax.barh(y, b["share_km"], color=HOT if b["label"] == "Planned" else COOL, height=.62)
    hax.text(b["share_km"] + .03, y, f"{round(b['share_km'] * 100)}%", va="center", fontsize=11, color=FG, fontweight="medium")
    hax.text(-.04, y, b["label"].replace("1989 to 2009", "before 2010"), va="center", ha="right", fontsize=10, color=FG)
hax.set_xlim(0, 1); hax.set_ylim(-.6, len(B) - .4); hax.axis("off")

# ---------- footer ----------
fig.text(.03, .018, "Source: TeleGeography Submarine Cable Map (submarinecablemap.com), API v3, 2026, CC BY-NC-SA 3.0; land: Natural Earth. Choke points: cables whose drawn routes\n"
         "cross a band across each strait or enter each hub area. Owners matched by exact name (Amazon as Amazon Web Services).\n"
         "Analysis and chart: Tristan Hotham, with Python and matplotlib · chart and derived data CC BY-NC-SA 4.0 · maps.tristanhotham.com/submarine-cables",
         fontsize=8.6, color=MUT, va="bottom", linespacing=1.5)
out = os.path.join(HERE, "the_internets_seabed.png")
fig.savefig(out, dpi=DPI, facecolor=BG)
plt.close(fig)
print(out, WPX, HPX)
