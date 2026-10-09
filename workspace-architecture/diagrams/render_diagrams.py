#!/usr/bin/env python3
"""
render_diagrams.py — Batch render Mermaid diagrams to SVG and standalone HTML.

Databricks-branded theme is embedded in each .md source file.

Usage:
    python render_diagrams.py

Paths (all relative to this script's directory):
    ./mermaid/   Mermaid .md sources
    ./svg/       rendered SVG output
    ./html/      rendered standalone HTML output

Renderers, tried in this order:
    1. mmdc        Node.js + @mermaid-js/mermaid-cli (`npm install -g @mermaid-js/mermaid-cli`)
    2. playwright  local headless Chromium (pip install playwright && playwright install chromium)
    3. mermaid.ink remote HTTP rendering service -- OPT-IN ONLY, see below

Mermaid's layout engine only runs in a browser, so tiers 1 and 2 both need a local
Chromium. Where none is available (locked-down CI, Databricks serverless, any host
that cannot reach the browser CDN), tier 3 can render instead.

*** Tier 3 sends your diagram source over the network ***

mermaid.ink is a public third-party service. Using it uploads the full text of each
.md diagram source to an external host, so it is DISABLED by default and never
engages on its own. Enable it explicitly, per run:

    python render_diagrams.py --allow-remote
    ALLOW_REMOTE_RENDER=1 python render_diagrams.py

Point it at your own self-hosted instance (mermaid.ink or Kroki are both
self-hostable) to keep the diagram source inside your network:

    python render_diagrams.py --allow-remote --remote-url https://mermaid.internal.example.com
    MERMAID_INK_URL=https://mermaid.internal.example.com python render_diagrams.py --allow-remote
"""

import argparse
import base64
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
import zlib
from pathlib import Path

# Paths
SCRIPT_DIR = Path(__file__).parent
MERMAID_DIR = SCRIPT_DIR / "mermaid"
SVG_DIR = SCRIPT_DIR / "svg"
HTML_DIR = SCRIPT_DIR / "html"

# Remote rendering (tier 3) -- opt-in, see module docstring
MERMAID_INK_URL = os.environ.get("MERMAID_INK_URL", "https://mermaid.ink")
REMOTE_TIMEOUT_SECONDS = 30

# Databricks brand colors for HTML wrapper
DB_RED = "#FF3621"
DB_DARK = "#1B3139"
DB_WHITE = "#FFFFFF"
DB_GRAY = "#F2F2F2"

# HTML template for standalone diagram pages
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} — Databricks Architecture</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&display=swap');

        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            font-family: 'DM Sans', 'Inter', 'Segoe UI', sans-serif;
            background: {bg};
            color: {dark};
            display: flex;
            flex-direction: column;
            align-items: center;
            min-height: 100vh;
            padding: 2rem;
        }}

        header {{
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 2rem;
            padding-bottom: 1rem;
            border-bottom: 3px solid {red};
            width: 100%;
            max-width: 1200px;
        }}

        header .logo {{
            width: 40px;
            height: 40px;
            background: {red};
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
        }}

        header .logo svg {{
            width: 24px;
            height: 24px;
            fill: white;
        }}

        header h1 {{
            font-size: 1.5rem;
            font-weight: 700;
            color: {dark};
        }}

        header .subtitle {{
            font-size: 0.875rem;
            color: #6B7280;
            margin-left: auto;
        }}

        .diagram-container {{
            background: white;
            border-radius: 12px;
            padding: 2rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1), 0 1px 2px rgba(0,0,0,0.06);
            max-width: 1200px;
            width: 100%;
            overflow-x: auto;
        }}

        .diagram-container svg {{
            max-width: 100%;
            height: auto;
        }}

        footer {{
            margin-top: 2rem;
            font-size: 0.75rem;
            color: #6B7280;
        }}
    </style>
</head>
<body>
    <header>
        <div class="logo">
            <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
            </svg>
        </div>
        <h1>{title}</h1>
        <span class="subtitle">Enterprise Workspace Architecture Reference</span>
    </header>
    <div class="diagram-container">
        {svg_content}
    </div>
    <footer>
        Matthew Giglia | Field Engineering — Databricks
    </footer>
</body>
</html>"""


def find_mmdc():
    """Check if mermaid-cli (mmdc) is available."""
    try:
        result = subprocess.run(["mmdc", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            return True
    except FileNotFoundError:
        pass
    return False


def render_with_mmdc(mermaid_file: Path, svg_file: Path):
    """Render using mermaid-cli."""
    cmd = [
        "mmdc",
        "-i", str(mermaid_file),
        "-o", str(svg_file),
        "-b", "transparent",
        "--width", "1200",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ❌ mmdc error: {result.stderr}")
        return False
    return True


def find_playwright():
    """Check if playwright AND a usable local Chromium are both present."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return False
    try:
        with sync_playwright() as p:
            executable = p.chromium.executable_path
    except Exception:
        return False
    return bool(executable) and Path(executable).exists()


def render_with_playwright(mermaid_file: Path, svg_file: Path):
    """Render using Playwright + Mermaid JS."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("  ❌ playwright is not installed.")
        return False

    mermaid_code = mermaid_file.read_text()

    html_content = f"""<!DOCTYPE html>
    <html><head>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    </head><body>
    <div class="mermaid">{mermaid_code}</div>
    <script>mermaid.initialize({{startOnLoad: true}});</script>
    </body></html>"""

    # Launch/render failures must not abort the whole batch -- report and let the
    # caller fall through to the next renderer.
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            try:
                page = browser.new_page()
                page.set_content(html_content)
                page.wait_for_selector("svg", timeout=10000)
                svg = page.inner_html(".mermaid")
            finally:
                browser.close()
    except Exception as exc:
        print(f"  ❌ playwright error: {type(exc).__name__}: {exc}")
        return False

    svg_file.write_text(svg)
    return True


def _encode_base64(mermaid_code: str) -> str:
    """Plain base64url of the diagram source (mermaid.ink legacy form)."""
    return base64.urlsafe_b64encode(
        mermaid_code.encode("utf-8")
    ).decode("ascii").rstrip("=")


def _encode_pako(mermaid_code: str) -> str:
    """Deflated editor-state form -- yields a much shorter URL for big diagrams."""
    state = json.dumps({"code": mermaid_code}, separators=(",", ":"))
    deflated = zlib.compress(state.encode("utf-8"), 9)
    return "pako:" + base64.urlsafe_b64encode(deflated).decode("ascii").rstrip("=")


def render_with_mermaid_ink(mermaid_file: Path, svg_file: Path):
    """Render via a remote mermaid.ink-compatible HTTP service.

    NOTE: this uploads the diagram source to MERMAID_INK_URL. Only reached when
    the caller has explicitly opted in.

    The Databricks theme travels inside each file's own `%%{init: ...}%%`
    directive, so no theme has to be passed over the wire.
    """
    mermaid_code = mermaid_file.read_text()
    base = MERMAID_INK_URL.rstrip("/")
    errors = []

    # Plain base64 first (most widely supported); pako handles over-long URLs.
    for label, encoder in (("base64", _encode_base64), ("pako", _encode_pako)):
        url = f"{base}/svg/{encoder(mermaid_code)}"
        try:
            request = urllib.request.Request(
                url, headers={"User-Agent": "render_diagrams.py"}
            )
            with urllib.request.urlopen(request, timeout=REMOTE_TIMEOUT_SECONDS) as response:
                if response.status != 200:
                    errors.append(f"{label}: HTTP {response.status}")
                    continue
                svg = response.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            errors.append(f"{label}: HTTP {exc.code}")
            continue
        except Exception as exc:
            errors.append(f"{label}: {type(exc).__name__}: {exc}")
            continue

        if "<svg" not in svg:
            errors.append(f"{label}: response was not SVG")
            continue

        svg_file.write_text(svg)
        return True

    print(f"  ❌ {base} failed ({'; '.join(errors)})")
    return False


def wrap_html(title: str, svg_content: str) -> str:
    """Wrap SVG in Databricks-branded HTML."""
    return HTML_TEMPLATE.format(
        title=title,
        svg_content=svg_content,
        bg=DB_GRAY,
        dark=DB_DARK,
        red=DB_RED,
        white=DB_WHITE,
    )


RENDERERS = {
    "mmdc": render_with_mmdc,
    "playwright": render_with_playwright,
    "mermaid.ink": render_with_mermaid_ink,
}


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Batch render Mermaid diagrams to SVG and standalone HTML."
    )
    parser.add_argument(
        "--allow-remote",
        action="store_true",
        default=os.environ.get("ALLOW_REMOTE_RENDER", "").lower()
        in ("1", "true", "yes"),
        help="Permit the remote mermaid.ink fallback. This UPLOADS each diagram's "
        "source to %s. Off by default." % MERMAID_INK_URL,
    )
    parser.add_argument(
        "--remote-url",
        default=None,
        help="Base URL of a mermaid.ink-compatible service (e.g. a self-hosted "
        "instance). Overrides the MERMAID_INK_URL env var.",
    )
    parser.add_argument(
        "--renderer",
        choices=sorted(RENDERERS),
        default=None,
        help="Force a specific renderer instead of auto-detecting.",
    )
    return parser.parse_args(argv)


def resolve_renderer(allow_remote: bool):
    """Pick the best available renderer, preferring local ones."""
    if find_mmdc():
        return "mmdc"
    if find_playwright():
        return "playwright"
    if allow_remote:
        return "mermaid.ink"
    return None


def explain_no_renderer():
    print("ERROR: no local Mermaid renderer available.")
    print("Mermaid needs a browser to compute diagram layout. Either:")
    print("  1. npm install -g @mermaid-js/mermaid-cli")
    print("  2. pip install playwright && playwright install chromium")
    print("  3. Re-run with --allow-remote to render via a remote service.")
    print(f"     This UPLOADS each diagram's source to {MERMAID_INK_URL}.")
    print("     Use --remote-url to point at a self-hosted instance instead.")


def main(argv=None):
    global MERMAID_INK_URL
    args = parse_args(argv)
    if args.remote_url:
        MERMAID_INK_URL = args.remote_url

    SVG_DIR.mkdir(parents=True, exist_ok=True)
    HTML_DIR.mkdir(parents=True, exist_ok=True)

    mermaid_files = sorted(MERMAID_DIR.glob("*.md"))
    if not mermaid_files:
        print("No .md files found in mermaid/ directory.")
        sys.exit(1)

    renderer = args.renderer or resolve_renderer(args.allow_remote)
    if renderer is None:
        explain_no_renderer()
        sys.exit(1)

    render = RENDERERS[renderer]
    print(f"Using renderer: {renderer}")
    if renderer == "mermaid.ink":
        print(f"  NOTE: uploading diagram source to {MERMAID_INK_URL}")
    print(f"Found {len(mermaid_files)} diagram(s) to render.\n")

    rendered = 0
    for mf in mermaid_files:
        stem = mf.stem  # e.g., "01_workspace_topology"
        title = stem.split("_", 1)[1].replace("_", " ").title() if "_" in stem else stem
        svg_file = SVG_DIR / f"{stem}.svg"
        html_file = HTML_DIR / f"{stem}.html"

        print(f"Rendering {mf.name}...")

        success = render(mf, svg_file)

        if success and svg_file.exists():
            svg_content = svg_file.read_text()
            html_content = wrap_html(title, svg_content)
            html_file.write_text(html_content)
            rendered += 1
            print(f"  ✅ SVG: {svg_file.name}")
            print(f"  ✅ HTML: {html_file.name}")
        else:
            print(f"  ⚠️  Skipped HTML (SVG render failed)")

    failed = len(mermaid_files) - rendered
    print(f"\nRendered {rendered}/{len(mermaid_files)} diagram(s). Outputs in:")
    print(f"  SVG:  {SVG_DIR}")
    print(f"  HTML: {HTML_DIR}")
    if failed:
        print(f"\n{failed} diagram(s) failed to render.")
        sys.exit(1)


if __name__ == "__main__":
    main()
