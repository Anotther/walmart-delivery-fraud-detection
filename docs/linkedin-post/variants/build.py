"""
Derive 3 design variants from the base carousel and screenshot
representative slides (cover + KPIs) for side-by-side ranking.

Each variant = base HTML + an appended <style> override (CSS cascade
lets later rules win). All variants stay in light mode so the existing
inline styles render correctly; they differ in card treatment, depth,
texture, radius and numerals.
"""
import pathlib
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).parent
BASE = (HERE / ".." / "carousel.html").resolve()
SHOTS = HERE / "shots"
SHOTS.mkdir(exist_ok=True)

CHROME = "/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell"

base_html = BASE.read_text(encoding="utf-8")

# ── Variant override themes ────────────────────────────────────────────
V1 = """
/* V1 — Editorial Hairline · flat, borderless, airy, blue-led */
:root { --bg-page:#EDF0F5; --shadow:none; }
.slide { background:#F7F9FC; }
.slide::before { height:4px; background:var(--blue-dark); }
.s-label { letter-spacing:4px; }
.h1 { font-size:66px; letter-spacing:-0.04em; }
.card, .card-b { background:transparent; border:none; border-left:2px solid var(--border-md);
  border-radius:0; box-shadow:none; padding:4px 0 4px 24px; }
.card-y { background:transparent; border:none; border-left:3px solid var(--yellow);
  border-radius:0; box-shadow:none; padding:2px 0 2px 24px; }
.kpi { background:transparent; border:none; border-top:none; border-left:2px solid var(--blue-lt);
  border-radius:0; box-shadow:none; padding:2px 0 2px 22px; }
.badge { background:transparent; box-shadow:none; }
.badge.b { background:transparent; border-color:#BFD3EC; }
.step-num { box-shadow:0 0 0 5px #F7F9FC; }
"""

V2 = """
/* V2 — Soft Elevated · rounded white cards floating with depth, yellow-led */
:root {
  --bg-page:#D2DBE8;
  --shadow:0 2px 6px rgba(16,33,66,.06), 0 18px 40px rgba(16,33,66,.10);
  --shadow-lg:0 4px 10px rgba(16,33,66,.07), 0 28px 60px rgba(16,33,66,.13);
}
.slide { background:radial-gradient(130% 100% at 50% -10%, #FFFFFF 0%, #EEF2F8 50%, #E2E9F3 100%); }
.slide::before { height:6px; }
.card, .card-b { border-radius:18px; }
.card-y { border-radius:0 18px 18px 0; }
.kpi { border-radius:18px; border-top-width:5px; }
.badge { border-radius:9999px; }
.accent { height:5px; width:60px; }
"""

V3 = """
/* V3 — Analyst Grid · graph-paper texture, tabular numerals, sharp corners */
:root { --bg-page:#E6EBF2; }
.slide {
  background-color:#F5F8FC;
  background-image:
    repeating-linear-gradient(0deg,  rgba(0,76,145,.055) 0 1px, transparent 1px 44px),
    repeating-linear-gradient(90deg, rgba(0,76,145,.055) 0 1px, transparent 1px 44px);
}
.slide::before { height:5px; background:repeating-linear-gradient(90deg, var(--blue-dark) 0 18px, var(--blue-lt) 18px 36px); }
.kpi-val, .prog-pct, .h1, .h2 { font-feature-settings:"tnum" 1, "lnum" 1; }
.card, .card-b, .kpi, .badge { border-radius:6px; }
.card-y { border-radius:0 6px 6px 0; }
.kpi { border-top-color:var(--blue); }
"""

VARIANTS = {"v1": V1, "v2": V2, "v3": V3}

def make(name, override):
    html = base_html.replace("</head>", f"<style>{override}</style>\n</head>")
    out = HERE / f"carousel-{name}.html"
    out.write_text(html, encoding="utf-8")
    return out

files = {"base": BASE}
for name, css in VARIANTS.items():
    files[name] = make(name, css)
    print("wrote", files[name].name)

# ── Screenshots: cover (slide 1) + KPIs (slide 5) for each version ─────
SHOT_SLIDES = [1, 5]
with sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path=CHROME)
    page = browser.new_page(viewport={"width": 1080, "height": 1350}, device_scale_factor=1)
    for ver, f in files.items():
        page.goto(f"file://{f}", wait_until="networkidle")
        for s in SHOT_SLIDES:
            el = page.locator(f'.slide[data-slide="{s}"]')
            el.screenshot(path=str(SHOTS / f"{ver}-slide{s}.png"))
            print("shot", f"{ver}-slide{s}.png")
    browser.close()
print("done")
