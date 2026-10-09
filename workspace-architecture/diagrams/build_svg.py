#!/usr/bin/env python3
"""
build_svg.py -- Draw the architecture diagrams directly as Databricks-themed SVG.

Mermaid's layout engine only runs in a browser, so render_diagrams.py needs a local
Chromium (or the opt-in remote service). This script is the browser-free alternative:
it hand-lays out the same seven diagrams using the Databricks brand palette and an
inline icon set. Pure standard library -- no browser, no network, no npm.

Usage:
    python build_svg.py                 # write all seven SVGs to ./svg/
    python build_svg.py --out somedir   # write elsewhere
    python build_svg.py --list          # just list what would be written

Output filenames match the SVG_MAP in ../docs/render_document.py, so running this
and then render_document.py embeds the diagrams into the final HTML.

Palette is kept in sync with ../docs/databricks_theme.css.
"""

import argparse
from pathlib import Path
from xml.sax.saxutils import escape

SCRIPT_DIR = Path(__file__).parent
SVG_DIR = SCRIPT_DIR / "svg"

# ---------------------------------------------------------------- brand palette
RED = "#FF3621"
DARK = "#1B3139"
TEAL = "#077A9D"
GREEN = "#00A972"
AMBER = "#FFAB00"
WHITE = "#FFFFFF"
GRAY = "#F2F2F2"
BORDER = "#E8E8E8"
MUTED = "#6B7280"

FONT = "'DM Sans','Inter','Segoe UI',Helvetica,Arial,sans-serif"

# fill, stroke, title colour
KINDS = {
    "red":   (RED,   "#CC2B1A", WHITE),
    "teal":  (TEAL,  "#055F7A", WHITE),
    "green": (GREEN, "#007A52", WHITE),
    "amber": (AMBER, "#CC8800", DARK),
    "dark":  (DARK,  "#0F1D22", WHITE),
    "gray":  (GRAY,  BORDER,    DARK),
    "white": (WHITE, BORDER,    DARK),
}

# ------------------------------------------------------------------- icon paths
# All 24x24, stroke-only so they inherit the card's text colour.
ICONS = {
    "layers": "M12 2.5L2.5 7l9.5 4.5L21.5 7 12 2.5zM2.5 16.5l9.5 4.5 9.5-4.5M2.5 11.75l9.5 4.5 9.5-4.5",
    "catalog": "M4 6c0-1.7 3.6-3 8-3s8 1.3 8 3-3.6 3-8 3-8-1.3-8-3zM4 6v12c0 1.7 3.6 3 8 3s8-1.3 8-3V6",
    "workspace": "M3 5h18v14H3zM3 9.5h18",
    "shield": "M12 2.5l8 3v5.5c0 5-3.4 9.3-8 10.5-4.6-1.2-8-5.5-8-10.5V5.5z",
    "lock": "M6.5 10.5V8a5.5 5.5 0 0111 0v2.5M5 10.5h14v10H5z",
    "globe": "M12 2.5a9.5 9.5 0 100 19 9.5 9.5 0 000-19zM2.5 12h19M12 2.5c3 3 3 16 0 19M12 2.5c-3 3-3 16 0 19",
    "user": "M12 11.5a4 4 0 100-8 4 4 0 000 8zM4.5 21c0-4 3.4-6.5 7.5-6.5s7.5 2.5 7.5 6.5",
    "gate": "M4.5 4.5h15v15h-15zM9.5 4.5v15M14.5 4.5v15",
    "chart": "M4 20V11M10 20V4.5M16 20v-7M2.5 20h19",
    "bolt": "M13 2.5L4.5 14H10l-1 7.5L19.5 10H13z",
    "git": "M6.5 3.5v11a3 3 0 003 3h6M6.5 3.5a2 2 0 100 4 2 2 0 000-4zM18.5 15.5a2 2 0 100 4 2 2 0 000-4z",
    "sync": "M20.5 12a8.5 8.5 0 11-2.8-6.3M20.5 4v5h-5",
    "warehouse": "M4 9l8-4.5L20 9v11H4zM9.5 20v-6h5v6",
    "cloud": "M7.5 18.5a4.2 4.2 0 01-.2-8.4 5.6 5.6 0 0110.8-1.3 4.4 4.4 0 01-.6 9.7z",
    "api": "M12 8.5a3.5 3.5 0 100 7 3.5 3.5 0 000-7M3.5 12h5M15.5 12h5M12 3.5v5M12 15.5v5",
}


def n(value, places=1):
    """Compact number formatting -- keeps the SVG free of trailing '.0' noise."""
    text = f"{float(value):.{places}f}".rstrip("0").rstrip(".")
    return text if text not in ("", "-") else "0"


class Canvas:
    """Minimal SVG builder: cards, dashed group frames, polyline arrows, chips."""

    def __init__(self, uid, width, height, aria=""):
        self.uid = uid
        self.w = width
        self.h = height
        self.aria = aria
        self.body = []
        self._markers = set()

    # -- primitives ----------------------------------------------------------
    def _marker(self, color):
        self._markers.add(color)
        return f"{self.uid}-ah-{color.lstrip('#')}"

    def text(self, x, y, s, size=11, fill=DARK, weight=400, anchor="middle",
             spacing=None, opacity=None):
        extra = ""
        if spacing is not None:
            extra += f' letter-spacing="{spacing}"'
        if opacity is not None:
            extra += f' opacity="{opacity}"'
        self.body.append(
            f'<text x="{n(x)}" y="{n(y)}" font-size="{n(size,2)}" font-weight="{weight}"'
            f' fill="{fill}" text-anchor="{anchor}"{extra}>{escape(str(s))}</text>'
        )

    def rect(self, x, y, w, h, fill="none", stroke=BORDER, sw=1.5, rx=10,
             dash=None, opacity=None):
        extra = ""
        if dash:
            extra += f' stroke-dasharray="{dash}"'
        if opacity is not None:
            extra += f' opacity="{opacity}"'
        self.body.append(
            f'<rect x="{n(x)}" y="{n(y)}" width="{n(w)}" height="{n(h)}" rx="{n(rx)}"'
            f' fill="{fill}" stroke="{stroke}" stroke-width="{n(sw,2)}"{extra}/>'
        )

    def icon(self, name, cx, cy, size=17, color=DARK, sw=1.7):
        d = ICONS.get(name)
        if not d:
            return
        scale = size / 24.0
        self.body.append(
            f'<g transform="translate({n(cx - size / 2)},{n(cy - size / 2)}) '
            f'scale({n(scale, 4)})" fill="none" stroke="{color}" '
            f'stroke-width="{n(sw / scale, 2)}" stroke-linecap="round" '
            f'stroke-linejoin="round"><path d="{d}"/></g>'
        )

    # -- composites ----------------------------------------------------------
    def card(self, x, y, w, h, title=None, lines=(), kind="white", icon=None,
             stroke=None, sw=1.6, rx=10, title_size=13, line_size=10.5, dash=None):
        fill, edge, tc = KINDS[kind]
        sub = MUTED if kind in ("white", "gray") else tc
        sub_opacity = None if kind in ("white", "gray") else 0.88
        self.rect(x, y, w, h, fill=fill, stroke=stroke or edge, sw=sw, rx=rx, dash=dash)

        cx = x + w / 2.0
        block = (23 if icon else 0) + ((title_size + 6) if title else 0) + 13.5 * len(lines)
        cur = y + (h - block) / 2.0
        if icon:
            self.icon(icon, cx, cur + 9, size=17, color=tc)
            cur += 23
        if title:
            self.text(cx, cur + title_size - 1, title, size=title_size, weight=700, fill=tc)
            cur += title_size + 6
        for line in lines:
            self.text(cx, cur + line_size - 1, line, size=line_size, fill=sub,
                      opacity=sub_opacity)
            cur += 13.5

    def frame(self, x, y, w, h, label=None, stroke=DARK, dash="7 5", align="start",
              sw=1.5, rx=14, fill="none"):
        self.rect(x, y, w, h, fill=fill, stroke=stroke, sw=sw, rx=rx, dash=dash)
        if label:
            lx = x + 18 if align == "start" else x + w - 18
            self.text(lx, y + 20, str(label).upper(), size=10.5, weight=700,
                      fill=stroke, anchor=align, spacing="1.3")

    def chip(self, x, y, lines, size=9.5, fill=MUTED, bg=WHITE):
        if isinstance(lines, str):
            lines = [lines]
        pad = 5
        w = max(len(s) for s in lines) * size * 0.57 + pad * 2
        h = len(lines) * (size + 3.5) + pad * 2 - 3.5
        self.rect(x - w / 2, y - h / 2, w, h, fill=bg, stroke="none", sw=0, rx=5,
                  opacity=0.93)
        cur = y - h / 2 + pad + size - 1.5
        for s in lines:
            self.text(x, cur, s, size=size, fill=fill, weight=500)
            cur += size + 3.5

    def link(self, pts, color=MUTED, sw=1.7, dash=None, end=True, start=False,
             label=None, label_at=None):
        d = "M" + " L".join(f"{n(px)},{n(py)}" for px, py in pts)
        attrs = (f' stroke="{color}" stroke-width="{n(sw,2)}" fill="none"'
                 f' stroke-linecap="round" stroke-linejoin="round"')
        if dash:
            attrs += f' stroke-dasharray="{dash}"'
        if end:
            attrs += f' marker-end="url(#{self._marker(color)})"'
        if start:
            attrs += f' marker-start="url(#{self._marker(color)})"'
        self.body.append(f'<path d="{d}"{attrs}/>')
        if label:
            lx, ly = label_at if label_at else _midpoint(pts)
            self.chip(lx, ly, label, fill=color)

    # -- output --------------------------------------------------------------
    def render(self):
        defs = []
        for color in sorted(self._markers):
            defs.append(
                f'<marker id="{self.uid}-ah-{color.lstrip("#")}" viewBox="0 0 10 10"'
                f' refX="9" refY="5" markerWidth="7" markerHeight="7"'
                f' orient="auto-start-reverse">'
                f'<path d="M0,1 L9,5 L0,9 z" fill="{color}"/></marker>'
            )
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}"'
            f' width="100%" role="img" aria-label="{escape(self.aria)}"'
            f' font-family="{FONT}">'
            f'<defs>{"".join(defs)}</defs>{"".join(self.body)}</svg>\n'
        )


def _midpoint(pts):
    """Point halfway along a polyline, measured by arc length."""
    segs = []
    total = 0.0
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        length = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        segs.append((length, x1, y1, x2, y2))
        total += length
    target = total / 2.0
    for length, x1, y1, x2, y2 in segs:
        if target <= length or length == 0:
            t = 0 if length == 0 else target / length
            return x1 + (x2 - x1) * t, y1 + (y2 - y1) * t
        target -= length
    return pts[-1]


# ============================================================ the seven diagrams

def d01_workspace_topology():
    c = Canvas("d01", 1200, 700, "Enterprise workspace topology")
    c.frame(20, 10, 1160, 680, "Databricks Account", stroke=DARK, dash="8 6")
    c.frame(50, 55, 1100, 170, "SDLC Workspaces", stroke=TEAL, dash="6 5")

    tiers = [
        ("SANDBOX", ["Preview features", "Synthetic data only", "No CSP"], "amber", "shield"),
        ("DEV", ["Personal schemas", "DAB dev mode"], "teal", "workspace"),
        ("TST / UAT", ["Integration &", "business validation"], "teal", "workspace"),
        ("PRODUCTION", ["Certified pipelines", "Gold tables", "HIPAA / PCI-DSS"], "red", "lock"),
    ]
    xs = [70, 345, 620, 895]
    for (title, lines, kind, icon), x in zip(tiers, xs):
        c.card(x, 90, 235, 112, title, lines, kind=kind, icon=icon)
    for x in xs[:-1]:
        c.link([(x + 237, 146), (x + 273, 146)], color=MUTED)

    c.card(380, 300, 290, 125, "INTERACTIVE ANALYST",
           ["Ad-hoc SQL", "Authors assets", "No publishing to prod"],
           kind="green", icon="chart")
    c.card(730, 300, 290, 125, "CONSUMER",
           ["Genie Agents · Genie One", "Dashboards · Apps"],
           kind="dark", icon="user")
    c.link([(990, 202), (990, 252), (525, 252), (525, 300)], color=RED,
           label="read-only", label_at=(757, 252))
    c.link([(1040, 202), (1040, 274), (875, 274), (875, 300)], color=RED,
           label="read-only", label_at=(957, 274))

    c.frame(50, 470, 1100, 200, "Unity Catalog Metastore · Regional",
            stroke=MUTED, dash="6 5", align="end")
    cats = [
        ("sandbox_cat", ["bound: Sandbox"], None),
        ("func_dev", ["bound: Dev"], None),
        ("func_tst", ["bound: Tst / UAT"], None),
        ("func · prod", ["ISOLATED: Prod, Consumer,", "Analyst  (+read Dev, Tst)"], RED),
        ("analyst_cat", ["bound: Analyst"], None),
    ]
    for (title, lines, edge), x in zip(cats, [70, 288, 506, 724, 942]):
        c.card(x, 530, 195, 95, title, lines, kind="gray", icon="catalog",
               stroke=edge, sw=2.2 if edge else 1.6)
    c.text(600, 452, "Workspace–catalog binding is noted on each catalog",
           size=10, fill=MUTED, opacity=0.9)
    return c


def d02_uc_metastore_by_region():
    c = Canvas("d02", 1200, 560, "One Unity Catalog metastore per region")

    def region(x, label, meta, cats, ws_lines):
        c.frame(x, 20, 490, 520, label, stroke=TEAL, dash="7 5")
        c.card(x + 60, 70, 370, 62, meta, kind="red", icon="catalog")
        spine = x + 75
        c.link([(x + 245, 132), (x + 245, 150), (spine, 150), (spine, 337)],
               color=MUTED, end=False)
        for name, y, edge in cats:
            c.card(x + 95, y, 300, 54, name, kind="teal", stroke=edge,
                   sw=2.2 if edge else 1.6)
            c.link([(spine, y + 27), (x + 95, y + 27)], color=MUTED)
        c.card(x + 40, 410, 410, 100, "Workspaces", ws_lines, kind="gray",
               icon="workspace")

    region(30, "US-East Region", "Metastore A",
           [("func_dev", 170, None), ("func_tst", 240, None), ("func · prod", 310, RED)],
           ["sandbox · dev · tst/uat", "prod · analyst · consumer"])
    region(680, "EU-West Region", "Metastore B",
           [("func_eu_dev", 170, None), ("func_eu_tst", 240, None),
            ("func_eu · prod", 310, RED)],
           ["eu-dev · eu-prod", "eu-consumer"])

    c.link([(520, 270), (680, 270)], color=DARK, start=True, sw=2,
           label=["D2D OpenSharing", "(cross-region)"])
    return c


def d03_read_up_write_local():
    c = Canvas("d03", 1200, 600, "Read up, write local access hierarchy")
    c.frame(30, 20, 1140, 560, "Read Up, Write Local — Access Hierarchy", stroke=DARK)

    c.card(90, 70, 380, 95, "func · PROD catalog", ["Source of truth"],
           kind="red", icon="lock")
    c.card(90, 230, 380, 85, "func_tst", ["TEST catalog"], kind="teal", icon="catalog")
    c.card(90, 390, 380, 85, "func_dev", ["DEV catalog"], kind="teal", icon="catalog")
    c.link([(280, 390), (280, 315)], color=TEAL, label="READ by Dev WS")
    c.link([(280, 230), (280, 165)], color=RED, label="READ by Dev WS, Tst WS")

    rows = [
        ("Prod WS", "WRITE: func · prod   ·   top of the hierarchy", "red"),
        ("Tst / UAT WS", "WRITE: func_tst   ·   READ: func", "teal"),
        ("Dev WS", "WRITE: func_dev   ·   READ: func_tst, func", "teal"),
        ("Analyst WS", "WRITE: analyst_cat   ·   READ: func", "green"),
        ("Consumer WS", "no write   ·   READ: func (certified gold)", "dark"),
    ]
    for (title, detail, kind), y in zip(rows, [60, 150, 240, 330, 420]):
        c.card(550, y, 580, 78, title, [detail], kind=kind, icon="workspace")
    c.text(840, 540, "Each workspace writes only to its own catalog and reads upward",
           size=10, fill=MUTED, opacity=0.9)
    return c


def d04_dr_architecture():
    c = Canvas("d04", 1200, 640, "Active-passive disaster recovery architecture")
    c.card(480, 20, 240, 66, "Users / BI / APIs", kind="dark", icon="user")
    c.link([(600, 86), (600, 118)], color=DARK)
    c.card(460, 120, 280, 66, "Stable DR Endpoint URL", kind="red", icon="globe")

    c.frame(60, 250, 480, 340, "Primary Region · Active", stroke=GREEN)
    c.frame(660, 250, 480, 340, "Secondary Region · Standby", stroke=MUTED)
    primary = ["Metastore A", "Prod workspace", "Consumer workspace",
               "Jobs running", "SQL active"]
    secondary = ["Metastore B", "DR workspace", "DR consumer workspace",
                 "Jobs paused", "SQL standby"]
    icons = ["catalog", "workspace", "user", "bolt", "warehouse"]
    for i, y in enumerate([290, 348, 406, 464, 522]):
        c.card(100, y, 400, 48, primary[i], kind="green", icon=icons[i], title_size=12)
        c.card(700, y, 400, 48, secondary[i], kind="gray", icon=icons[i], title_size=12)

    c.link([(460, 153), (300, 153), (300, 250)], color=GREEN)
    c.link([(740, 153), (900, 153), (900, 250)], color=MUTED, dash="6 4",
           label="failover", label_at=(900, 205))
    c.link([(540, 420), (660, 420)], color=DARK, sw=2,
           label=["Managed DR", "or DIY replication"])
    return c


def d05_global_operations():
    c = Canvas("d05", 1200, 700, "Global multi-region operations model")
    c.frame(30, 20, 1140, 480, "Global Databricks Account", stroke=DARK, dash="8 6")

    regions = [
        (60, "US-East", "Metastore A", ["Prod · Consumer · Analyst", "Dev · Tst · Sandbox"]),
        (440, "EU-West", "Metastore B", ["Prod · Consumer", "Analyst · Dev"]),
        (820, "APAC · Sydney", "Metastore C", ["Prod · Consumer"]),
    ]
    for x, label, meta, ws in regions:
        c.frame(x, 70, 320, 250, label, stroke=TEAL, dash="6 5")
        c.card(x + 25, 115, 270, 56, meta, kind="red", icon="catalog")
        c.card(x + 20, 195, 280, 95, "Workspaces", ws, kind="gray", icon="workspace")

    c.link([(380, 195), (440, 195)], color=DARK, start=True, sw=2)
    c.link([(760, 195), (820, 195)], color=DARK, start=True, sw=2)
    c.link([(220, 320), (220, 352), (980, 352), (980, 320)], color=DARK,
           start=True, sw=2)
    c.text(600, 378, "D2D OpenSharing — cross-region reference data and aggregates",
           size=10, fill=MUTED, opacity=0.95)
    c.card(70, 400, 1060, 62, None,
           ["Data sovereignty: EU data stays in the EU metastore",
            "GDPR enforced at the metastore + catalog-binding level"],
           kind="amber", icon="shield")

    c.card(120, 540, 300, 80, "US-West", ["DR secondary"], kind="gray", icon="sync")
    c.card(500, 540, 300, 80, "EU-North", ["DR secondary"], kind="gray", icon="sync")
    c.link([(270, 540), (270, 502)], color=MUTED, dash="6 4",
           label="Managed DR", label_at=(345, 521))
    c.link([(650, 540), (650, 502)], color=MUTED, dash="6 4",
           label="Managed DR", label_at=(725, 521))
    return c


def d06_complete_architecture():
    c = Canvas("d06", 1200, 1070, "Complete enterprise architecture")
    c.frame(20, 10, 1160, 1050, "Databricks Account", stroke=DARK, dash="8 6")

    c.frame(50, 55, 1100, 110, "Unity Catalog Metastore · Regional",
            stroke=MUTED, dash="6 5", align="end")
    c.card(70, 85, 1060, 62,
           "Catalogs:  sandbox  |  func_dev  |  func_tst  |  func (prod)  |  analyst",
           ["Read Up, Write Local   ·   separate storage location and credentials per environment"],
           kind="gray", title_size=12.5)

    c.frame(50, 195, 1100, 150, "Workspaces", stroke=TEAL, dash="6 5")
    tiers = [
        ("Sandbox", ["No CSP"], "amber", "shield"),
        ("Dev", ["CSP if reading prod"], "teal", "workspace"),
        ("Tst / UAT", ["CSP if regulated"], "teal", "workspace"),
        ("Prod", ["HIPAA · PCI-DSS"], "red", "lock"),
    ]
    xs = [70, 345, 620, 895]
    for (title, lines, kind, icon), x in zip(tiers, xs):
        c.card(x, 230, 235, 92, title, lines, kind=kind, icon=icon)
    for x in xs[:-1]:
        c.link([(x + 237, 276), (x + 273, 276)], color=MUTED)

    c.card(90, 420, 330, 110, "Interactive Analyst",
           ["Frictionless Deployments", "CSP matches prod"], kind="green", icon="chart")
    c.card(470, 420, 330, 110, "Consumer",
           ["Genie One · Genie Agents", "Dashboards · Apps"], kind="dark", icon="user")
    c.link([(990, 322), (990, 372), (255, 372), (255, 420)], color=RED,
           label="read-only", label_at=(622, 372))
    c.link([(1040, 322), (1040, 394), (635, 394), (635, 420)], color=RED,
           label="read-only", label_at=(837, 394))

    c.frame(50, 560, 1100, 200, "External Access Layer", stroke=RED, dash="6 5")
    c.card(80, 635, 200, 72, "External Customers", kind="dark", icon="user")
    c.card(320, 625, 230, 92, "API Gateway", ["APIM / AWS GW / Apigee"],
           kind="amber", icon="gate")
    c.link([(280, 671), (320, 671)], color=DARK)
    c.link([(550, 671), (590, 671)], color=DARK, end=False)
    targets = [
        (585, "Databricks App", ["OBO via Lakebase"], "green", "cloud"),
        (645, "Unity Gateway", ["MCP · Models · Skills"], "red", "api"),
        (705, "Model Serving Endpoints", ["Governed by UC ACLs"], "teal", "bolt"),
    ]
    for y, title, lines, kind, icon in targets:
        c.card(620, y, 250, 52, title, lines, kind=kind, icon=icon, title_size=11.5,
               line_size=9.5)
        c.link([(590, 671), (590, y + 26), (620, y + 26)], color=DARK)
    c.link([(635, 530), (635, 560)], color=MUTED, dash="5 4", end=False)

    c.frame(50, 790, 540, 250, "CI/CD", stroke=TEAL, dash="6 5")
    c.card(80, 828, 130, 50, "Git", kind="teal", icon="git", title_size=12)
    c.card(240, 828, 150, 50, "DAB Bundle 1", ["Infra"], kind="teal", title_size=11.5,
           line_size=9.5)
    c.card(420, 828, 150, 50, "DAB Bundle 2", ["App"], kind="teal", title_size=11.5,
           line_size=9.5)
    c.link([(212, 853), (238, 853)], color=MUTED)
    c.link([(392, 853), (418, 853)], color=MUTED)
    c.card(80, 900, 130, 50, "Terraform", kind="gray", title_size=12)
    c.card(240, 900, 150, 50, "Workspace", ["provisioning"], kind="gray",
           title_size=11.5, line_size=9.5)
    c.link([(212, 925), (238, 925)], color=MUTED)
    c.card(80, 972, 490, 50, "Workload Identity Federation", ["No long-lived secrets"],
           kind="gray", icon=None, title_size=12, line_size=9.5)

    c.frame(640, 790, 510, 250, "Disaster Recovery", stroke=GREEN, dash="6 5")
    c.card(680, 840, 170, 56, "Primary", kind="green", title_size=12)
    c.card(940, 840, 170, 56, "Secondary", kind="gray", title_size=12)
    c.link([(852, 868), (938, 868)], color=DARK, start=True, sw=2)
    c.chip(895, 848, "Managed DR", fill=DARK)
    c.card(680, 930, 430, 56, "Stable URL", ["Quarterly failover testing"],
           kind="white", icon="sync", title_size=12, line_size=9.5)
    return c


def d07_external_customer_access():
    c = Canvas("d07", 1200, 840, "External customer access via Unity Gateway")
    c.card(430, 20, 340, 76, "External Customer",
           ["Mobile app · Partner API · Web portal"], kind="dark", icon="user")
    c.link([(600, 96), (600, 148)], color=DARK,
           label="API key / OAuth / mTLS", label_at=(718, 122))

    c.frame(300, 150, 600, 220, "Hyperscaler API Gateway", stroke=AMBER)
    controls = [
        (320, 190, "External authentication"), (605, 190, "Rate limiting & throttling"),
        (320, 250, "IP allowlisting"), (605, 250, "Request validation"),
        (320, 310, "API versioning"), (605, 310, "Usage metering"),
    ]
    for x, y, label in controls:
        c.card(x, y, 265, 50, label, kind="amber", title_size=12)
    c.link([(600, 370), (600, 423)], color=DARK,
           label=["M2M OAuth", "Service Principal"], label_at=(730, 396))

    c.frame(80, 425, 1040, 235, "Databricks Consumer Workspace", stroke=TEAL)
    blocks = [
        (110, "Databricks App · AppKit", GREEN,
         [("REST API endpoints", "green", "api"), ("Lakebase auth + memory", "green", "cloud")]),
        (445, "Unity Gateway", RED,
         [("MCP Services", "red", "api"), ("Genie Agent queries", "red", "chart")]),
        (780, "Model Serving", DARK,
         [("Foundation Model APIs", "dark", "bolt"), ("Governed by UC ACLs", "dark", "lock")]),
    ]
    for x, label, color, cards in blocks:
        c.frame(x, 460, 320, 170, label, stroke=color, dash="5 4", sw=1.3)
        for (title, kind, icon), y in zip(cards, [500, 560]):
            c.card(x + 25, y, 270, 50, title, kind=kind, icon=icon, title_size=11.5)

    c.frame(80, 700, 1040, 120, "Three-SPN Architecture", stroke=MUTED, dash="6 5")
    spns = [
        (110, "App SPN", "App-scoped"),
        (445, "Gateway SPN", "AI-scoped"),
        (780, "Bootstrap SPN", "Minimal blast radius"),
    ]
    for x, title, detail in spns:
        c.card(x, 738, 320, 62, title, [detail], kind="gray", icon="lock")
    return c


DIAGRAMS = {
    "01_workspace_topology": d01_workspace_topology,
    "02_uc_metastore_by_region": d02_uc_metastore_by_region,
    "03_read_up_write_local": d03_read_up_write_local,
    "04_dr_architecture": d04_dr_architecture,
    "05_global_operations": d05_global_operations,
    "06_complete_architecture": d06_complete_architecture,
    "07_external_customer_access": d07_external_customer_access,
}


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Draw the architecture diagrams as Databricks-themed SVG."
    )
    parser.add_argument("--out", default=None, help="Output directory (default ./svg/).")
    parser.add_argument("--list", action="store_true",
                        help="List the diagrams without writing anything.")
    args = parser.parse_args(argv)

    if args.list:
        for stem in DIAGRAMS:
            print(f"{stem}.svg")
        return

    out_dir = Path(args.out) if args.out else SVG_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    total = 0
    for stem, build in DIAGRAMS.items():
        svg = build().render()
        path = out_dir / f"{stem}.svg"
        path.write_text(svg, encoding="utf-8")
        total += len(svg.encode("utf-8"))
        print(f"  wrote {path.name:34s} {len(svg.encode('utf-8')):>7,} bytes")

    print(f"\n{len(DIAGRAMS)} diagram(s), {total:,} bytes total -> {out_dir}")


if __name__ == "__main__":
    main()
