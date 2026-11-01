"""Shared paths and helpers for the submarine-cables study ("The internet's seabed").

Raw inputs (read in place, never copied into the repo):
  CABLES   TeleGeography Submarine Cable Map, API v3 (https://www.submarinecablemap.com/api/v3/), fetched 2026:
             cable-geo.json          routes (GeoJSON MultiLineStrings, one or more features per cable)
             landing-point-geo.json  landing points (GeoJSON points)
             cable_details.json      713 cables: name, length, landing points (with country), owners, suppliers,
                                     rfs (ready for service), rfs_year, is_planned, url, notes
           TeleGeography data licence: CC BY-NC-SA 3.0. Everything derived from it here (data/, figures, text) is shared
           under CC BY-NC-SA 4.0, a later version of the same licence, as 3.0 permits.
  GEO      Natural Earth 10m and 50m countries and land, 10m populated places (public domain).
Intermediates are written to WORK (outside the repo by default)."""
import json, os, re, math

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CABLES = os.environ.get("CABLES_RAW", "/home/claude/newdata/raw6/cables")
GEO = os.environ.get("CABLES_GEO", "/home/claude/newdata/raw/geo")
FONTS = os.environ.get("FONT_DIR", "/home/claude/ref/fonts")
DATA = os.path.join(ROOT, "data")
WORK = os.environ.get("CABLES_WORK", "/home/claude/work/submarine-cables")
for d in (DATA, WORK):
    os.makedirs(d, exist_ok=True)

SLUG = "submarine-cables"
PAGE_URL = "https://maps.tristanhotham.com/submarine-cables/"
REPO = "https://github.com/Tristan-Hotham/submarine-cables"
SOURCE_URL = "https://www.submarinecablemap.com/"
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")
DATA_LICENCE = "CC BY-NC-SA 4.0"   # outputs; the source is CC BY-NC-SA 3.0
CREDIT = "TeleGeography, Submarine Cable Map (submarinecablemap.com), CC BY-NC-SA 3.0"
YEAR_NOW = 2026

# Eras: decade the cable was ready for service; planned cables are their own class whatever their target year.
ERAS = [("1990s", "1989 to 1999", 1980, 1999, "#3D3A8C"),
        ("2000s", "2000 to 2009", 2000, 2009, "#2F7FC1"),
        ("2010s", "2010 to 2019", 2010, 2019, "#139C8C"),
        ("2020s", "2020 to 2026", 2020, 2030, "#E39B12"),
        ("planned", "Planned", None, None, "#D9482B")]
ERA_COL = {k: c for k, _, _, _, c in ERAS}
ERA_LAB = {k: l for k, l, _, _, _ in ERAS}

# The four hyperscalers, matched as whole owner names in TeleGeography's comma-separated owners field.
# Exact names only: 'Metacore Subcom' is not Meta; no other spelling (Facebook, Alphabet, AWS, Amazon) occurs.
HYPER = {"Google": ["Google"], "Meta": ["Meta", "Facebook"], "Amazon": ["Amazon Web Services", "Amazon", "AWS"],
         "Microsoft": ["Microsoft"]}


def era_of(year, planned):
    if planned:
        return "planned"
    for k, _, a, b, _ in ERAS[:-1]:
        if year is not None and a <= year <= b:
            return k
    return None


def dash(v):
    """House style: no em or en dashes, no double hyphens, in anything written to data/."""
    if isinstance(v, str):
        v = re.sub(r"(\d)\s*[–—]\s*(\d)", r"\1 to \2", v)
        v = v.replace(" — ", ", ").replace("—", ", ").replace(" – ", ", ").replace("–", "-")
        while "--" in v:
            v = v.replace("--", "-")
        return v
    if isinstance(v, (list, tuple)):
        return [dash(x) for x in v]
    if isinstance(v, dict):
        return {k: dash(x) for k, x in v.items()}
    return v


def _np(o):
    import numpy as np
    if isinstance(o, np.integer): return int(o)
    if isinstance(o, np.floating): return float(o)
    if isinstance(o, np.bool_): return bool(o)
    if isinstance(o, np.ndarray): return o.tolist()
    raise TypeError(type(o))


def jsave(obj, path, indent=None):
    if os.path.abspath(path).startswith(DATA):
        obj = dash(obj)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent, separators=None if indent else (",", ":"), default=_np)


def jload(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def get(R, path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(v):,}"
    if f == "k": return f"{round(v / 1000):,}"         # km -> thousand km
    if f == "m1": return f"{v / 1e6:.1f}"              # km -> million km
    if f == "pct": return f"{round(v * 100)}%"
    if f == "pct1": return f"{v * 100:.1f}%"
    if f == "f1": return f"{v:.1f}"
    if f == "x1": return f"{v:.1f}"
    raise ValueError(f)


def fill(text, R, keep=("DOI", "DOI_URL", "BLOG_URL", "IMG")):
    """Replace {{path|fmt}} tokens from results.json, leaving the publisher's placeholders alone."""
    def rep(m):
        k = m.group(1)
        if k in keep or k.startswith("IMG"):
            return m.group(0)
        return fmt(get(R, k), m.group(3))
    return re.sub(r"\{\{([^}|]+)(\|(\w+))?\}\}", rep, text)


def visible_text_ok(s, where=""):
    for bad in ("—", "–", "--", "DSIT", "DCMS", "civil serv", "Civil Serv"):
        assert bad not in s, (where, bad)
