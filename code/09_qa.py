"""Step 9. QA: open index.html in Chromium (Playwright) at 1280 px and 390 px, record console errors and save screenshots
to qa/. The container cannot reach the Leaflet CDN, Esri tiles or web fonts: Leaflet is served from a local copy
(LEAFLET_DIST) and the rest is left blank. Also checks the built text files for dashes and banned words.
Run: python3 code/09_qa.py
"""
import os, re, sys, threading, http.server, functools, glob
from playwright.sync_api import sync_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

LEAF = os.environ.get("LEAFLET_DIST", "/tmp/claude-0/-home-claude/9791f396-0812-550b-8fd1-2ad33918f115/scratchpad/node_modules/leaflet/dist")
QA = os.path.join(ROOT, "qa"); os.makedirs(QA, exist_ok=True)


def serve():
    class Q(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    h = functools.partial(Q, directory=ROOT)
    s = http.server.ThreadingHTTPServer(("127.0.0.1", 8853), h); threading.Thread(target=s.serve_forever, daemon=True).start(); return s


def route(r):
    u = r.request.url
    if "cdnjs.cloudflare.com" in u and "leaflet" in u:
        f = "leaflet.css" if u.endswith(".css") else "leaflet.js"
        return r.fulfill(status=200, body=open(os.path.join(LEAF, f), "rb").read(), headers={"Content-Type": "text/css" if f.endswith("css") else "application/javascript"})
    if u.startswith("http://127.0.0.1"):
        return r.continue_()
    return r.abort()


if __name__ == "__main__":
    srv = serve(); errs = []
    with sync_playwright() as p:
        br = p.chromium.launch()
        for name, vw, vh in (("desktop", 1280, 900), ("phone", 390, 844)):
            pg = br.new_page(viewport={"width": vw, "height": vh}, device_scale_factor=1 if vw > 500 else 2)
            pg.on("console", lambda m, n=name: errs.append((n, m.type, m.text)) if m.type == "error" and "ERR_FAILED" not in m.text and "Failed to load resource" not in m.text else None)
            pg.on("pageerror", lambda e, n=name: errs.append((n, "pageerror", str(e))))
            pg.route("**/*", route)
            pg.goto("http://127.0.0.1:8853/index.html", wait_until="load"); pg.wait_for_timeout(3000)
            pg.screenshot(path=f"{QA}/{name}_top.png")
            pg.locator("#atlas").scroll_into_view_if_needed(); pg.wait_for_timeout(1500)
            pg.screenshot(path=f"{QA}/{name}_map.png")
            pg.evaluate("pick('cable', '2africa', true); 0"); pg.wait_for_timeout(1500)
            pg.screenshot(path=f"{QA}/{name}_cable.png")
            pg.evaluate("intro(); slider.value = 2001; S.year = 2001; restyle(); map.setView([30, 0], 2); 0"); pg.wait_for_timeout(1200)
            pg.locator("#map").screenshot(path=f"{QA}/{name}_2001.png")
            pg.evaluate("slider.value = 2031; S.year = 2031; LY.grid = true; applyLayers(); map.setView([15, 60], 3); 0"); pg.wait_for_timeout(2000)
            pg.locator("#map").screenshot(path=f"{QA}/{name}_grid.png")
            pg.evaluate("LY.grid = false; applyLayers(); pick('zone', 'bab', true); 0"); pg.wait_for_timeout(1800)
            pg.screenshot(path=f"{QA}/{name}_zone.png")
            pg.evaluate("pick('country', 'Niue', true); 0"); pg.wait_for_timeout(1800)
            pg.screenshot(path=f"{QA}/{name}_niue.png")
            pg.locator(".lyrBtn").click(); pg.wait_for_timeout(400)
            pg.locator("#map").screenshot(path=f"{QA}/{name}_layers.png")
            pg.locator(".lyrBtn").click()
            pg.locator("#q").fill("Marseille"); pg.wait_for_timeout(500)
            pg.screenshot(path=f"{QA}/{name}_search.png")
            pg.locator("#q").fill("")
            for sel in ("#tlChart", "#hyChart", "#straitTable", "#ctyTable", "#singleCards"):
                pg.locator(sel).scroll_into_view_if_needed(); pg.wait_for_timeout(300)
                pg.locator(sel).screenshot(path=f"{QA}/{name}_{sel[1:]}.png")
            # full screen button exists on the map
            assert pg.locator("#map .mfs-btn").count() == 1, "no full-screen button"
            pg.locator("#map .mfs-btn").click(); pg.wait_for_timeout(800)
            pg.screenshot(path=f"{QA}/{name}_fullscreen.png")
            sw = pg.evaluate("document.documentElement.scrollWidth"); assert sw <= vw + 1, (name, "horizontal scroll", sw)
            pg.close()
        # dark mode
        pg = br.new_page(viewport={"width": 1280, "height": 900}, color_scheme="dark"); pg.route("**/*", route)
        pg.on("pageerror", lambda e: errs.append(("dark", "pageerror", str(e))))
        pg.goto("http://127.0.0.1:8853/index.html", wait_until="load"); pg.wait_for_timeout(2500)
        pg.screenshot(path=f"{QA}/dark_top.png"); pg.locator("#atlas").scroll_into_view_if_needed(); pg.wait_for_timeout(1000); pg.screenshot(path=f"{QA}/dark_map.png")
        br.close()
    srv.shutdown()
    print("console errors:", errs if errs else "none")
    # text checks on everything visible that we built
    for f in [os.path.join(ROOT, "index.html"), os.path.join(ROOT, "README.md"), *glob.glob(os.path.join(ROOT, "release", "blog", "*.html")),
              *glob.glob(os.path.join(ROOT, "release", "blog", "*.json")), *glob.glob(os.path.join(ROOT, "release", "zenodo", "*.json")),
              *glob.glob(os.path.join(ROOT, "reddit", "*.md")), *glob.glob(os.path.join(ROOT, "release", "paper", "*.tex"))]:
        if not os.path.exists(f):
            continue
        s = open(f, encoding="utf-8").read()
        s = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", s, flags=re.S) if f.endswith(".html") else s
        if f.endswith(".md"):
            s = re.sub(r"(?m)^\|[-| ]+\|$", "", s)
        if f.endswith(".tex"):
            s = re.sub(r"(?m)^%.*$", "", s).replace("\\-\\-", "")
        for bad in ("—", "–", "DSIT", "DCMS", "civil serv", "Civil Serv"):
            assert bad not in s, (f, bad)
        if not f.endswith(".tex"):
            assert "--" not in s, (f, "--")
    print("text checks passed")
    assert not errs
