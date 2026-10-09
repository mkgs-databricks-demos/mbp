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

Requirements:
    - Node.js + @mermaid-js/mermaid-cli (`npm install -g @mermaid-js/mermaid-cli`)
    OR
    - Playwright-based rendering (pip install playwright && playwright install chromium)

The script tries mmdc (Mermaid CLI) first, then falls back to a Playwright-based
renderer if mmdc is not available.
"""

import os
import sys
import subprocess
import json
from pathlib import Path

# Paths
SCRIPT_DIR = Path(__file__).parent
MERMAID_DIR = SCRIPT_DIR / "mermaid"
SVG_DIR = SCRIPT_DIR / "svg"
HTML_DIR = SCRIPT_DIR / "html"

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


def render_with_playwright(mermaid_file: Path, svg_file: Path):
    """Render using Playwright + Mermaid JS (fallback)."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("  ❌ Neither mmdc nor playwright available. Install one:")
        print("     npm install -g @mermaid-js/mermaid-cli")
        print("     OR: pip install playwright && playwright install chromium")
        return False

    mermaid_code = mermaid_file.read_text()

    html_content = f"""<!DOCTYPE html>
    <html><head>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    </head><body>
    <div class="mermaid">{mermaid_code}</div>
    <script>mermaid.initialize({{startOnLoad: true}});</script>
    </body></html>"""

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(html_content)
        page.wait_for_selector("svg", timeout=10000)
        svg = page.inner_html(".mermaid")
        browser.close()

    svg_file.write_text(svg)
    return True


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


def main():
    SVG_DIR.mkdir(parents=True, exist_ok=True)
    HTML_DIR.mkdir(parents=True, exist_ok=True)

    mermaid_files = sorted(MERMAID_DIR.glob("*.md"))
    if not mermaid_files:
        print("No .md files found in mermaid/ directory.")
        sys.exit(1)

    use_mmdc = find_mmdc()
    renderer = "mmdc" if use_mmdc else "playwright"
    print(f"Using renderer: {renderer}")
    print(f"Found {len(mermaid_files)} diagram(s) to render.\n")

    for mf in mermaid_files:
        stem = mf.stem  # e.g., "01_workspace_topology"
        title = stem.split("_", 1)[1].replace("_", " ").title() if "_" in stem else stem
        svg_file = SVG_DIR / f"{stem}.svg"
        html_file = HTML_DIR / f"{stem}.html"

        print(f"Rendering {mf.name}...")

        if use_mmdc:
            success = render_with_mmdc(mf, svg_file)
        else:
            success = render_with_playwright(mf, svg_file)

        if success and svg_file.exists():
            svg_content = svg_file.read_text()
            html_content = wrap_html(title, svg_content)
            html_file.write_text(html_content)
            print(f"  ✅ SVG: {svg_file.name}")
            print(f"  ✅ HTML: {html_file.name}")
        else:
            print(f"  ⚠️  Skipped HTML (SVG render failed)")

    print(f"\nDone. Outputs in:\n  SVG:  {SVG_DIR}\n  HTML: {HTML_DIR}")


if __name__ == "__main__":
    main()
