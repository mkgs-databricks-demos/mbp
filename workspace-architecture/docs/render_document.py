#!/usr/bin/env python3
"""
render_document.py
Converts document.md to Databricks-branded HTML with embedded SVG diagrams.

Usage: python render_document.py
Prerequisites: pip install markdown; run ../diagrams/render_diagrams.py first for SVGs.

Inputs (all relative to this script's directory):
  - ./document.md                  (canvas markdown export)
  - ./databricks_theme.css         (Databricks brand styles)
  - ./document_template.html       (HTML shell with placeholders)
  - ../diagrams/svg/*.svg          (rendered diagrams)

Output:
  - ./enterprise_workspace_architecture.html
"""

import os
import re
import sys
import html as html_mod
from pathlib import Path

try:
    import markdown
    from markdown.extensions.toc import TocExtension
except ImportError:
    os.system("pip install markdown")
    import markdown
    from markdown.extensions.toc import TocExtension

SCRIPT_DIR = Path(__file__).parent
REPO_DIR = SCRIPT_DIR.parent
DOC_MD = SCRIPT_DIR / "document.md"
SVG_DIR = REPO_DIR / "diagrams" / "svg"
CSS_FILE = SCRIPT_DIR / "databricks_theme.css"
TEMPLATE_FILE = SCRIPT_DIR / "document_template.html"
OUTPUT = SCRIPT_DIR / "enterprise_workspace_architecture.html"

# Map: keywords found in ASCII code blocks -> SVG filename
SVG_MAP = [
    (["SANDBOX", "INTERACTIVE", "CONSUMER", "Unity Catalog Metastore"],
     "01_workspace_topology.svg"),
    (["US-East Region", "EU-West Region", "Metastore A"],
     "02_uc_metastore_by_region.svg"),
    (["WRITE ACCESS", "READ ACCESS", "func_dev catalog"],
     "03_read_up_write_local.svg"),
    (["func (PROD catalog)", "top of hierarchy", "source of truth"],
     "03_read_up_write_local.svg"),
    (["PRIMARY REGION", "SECONDARY REGION", "Stable DR Endpoint"],
     "04_dr_architecture.svg"),
    (["Global Databricks Account", "US-East", "APAC"],
     "05_global_operations.svg"),
    (["DATABRICKS ACCOUNT", "UNITY CATALOG METASTORE"],
     "06_complete_architecture.svg"),
    (["External Customer", "Hyperscaler API Gateway"],
     "07_external_customer_access.svg"),
]


def find_svg_for_block(code_text):
    """Match an ASCII code block to its SVG replacement."""
    for keywords, svg_file in SVG_MAP:
        matches = sum(1 for kw in keywords if kw in code_text)
        if matches >= 2:
            svg_path = SVG_DIR / svg_file
            if svg_path.exists():
                return svg_path.read_text()
    return None


def replace_ascii_with_svg(html_content):
    """Replace ASCII art code blocks with embedded SVG diagrams."""
    box_chars = [
        "\u250c", "\u2510", "\u2514", "\u2518", "\u2502", "\u2500",
        "\u251c", "\u2524", "\u252c", "\u2534", "\u253c",
        "\u25bc", "\u25b6", "\u25c4", "\u25ba"
    ]

    def replacer(match):
        raw = match.group(1)
        decoded = html_mod.unescape(raw)
        if any(c in decoded for c in box_chars):
            svg = find_svg_for_block(decoded)
            if svg:
                return '<div class="diagram-embed">' + svg + '</div>'
        return match.group(0)

    return re.sub(
        r'<pre><code>(.*?)</code></pre>',
        replacer,
        html_content,
        flags=re.DOTALL
    )


def main():
    # Validate inputs
    if not DOC_MD.exists():
        print(f"ERROR: {DOC_MD} not found.")
        print("Export the canvas markdown to document.md first.")
        sys.exit(1)

    if not CSS_FILE.exists():
        print(f"ERROR: {CSS_FILE} not found.")
        sys.exit(1)

    if not TEMPLATE_FILE.exists():
        print(f"ERROR: {TEMPLATE_FILE} not found.")
        sys.exit(1)

    svg_count = len(list(SVG_DIR.glob("*.svg"))) if SVG_DIR.exists() else 0
    if svg_count == 0:
        print("WARNING: No SVGs found in ../diagrams/svg/.")
        print("Run ../diagrams/render_diagrams.py first. Proceeding with ASCII art preserved.")

    # Read inputs
    md_text = DOC_MD.read_text()
    css_text = CSS_FILE.read_text()
    template_text = TEMPLATE_FILE.read_text()

    # Convert markdown to HTML
    md_obj = markdown.Markdown(extensions=[
        "tables",
        "fenced_code",
        TocExtension(permalink=False, toc_depth="3-4"),
    ])
    body_html = md_obj.convert(md_text)
    toc_html = md_obj.toc

    # Replace ASCII diagrams with SVGs
    if svg_count > 0:
        body_html = replace_ascii_with_svg(body_html)

    # Assemble final HTML
    final_html = template_text
    final_html = final_html.replace("{{CSS_CONTENT}}", css_text)
    final_html = final_html.replace("{{TOC_CONTENT}}", toc_html)
    final_html = final_html.replace("{{BODY_CONTENT}}", body_html)

    # Write output
    OUTPUT.write_text(final_html)
    print(f"Done: {OUTPUT}")
    print(f"  SVGs embedded: {svg_count}")
    print(f"  Size: {OUTPUT.stat().st_size:,} bytes")
    print("  Open in a browser to view.")


if __name__ == "__main__":
    main()
