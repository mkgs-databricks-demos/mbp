#!/usr/bin/env python3
"""
render_uc_convention.py - Generate Databricks-branded interactive HTML
from the UC Naming Convention markdown source.

Run from the directory containing uc-naming-convention-reference.md:
    python render_uc_convention.py

Generates:
    uc-naming-convention-best-practices.html - Interactive branded document

Colors: Databricks palette
    #FF3621 (red), #1B3139 (dark), #00A972 (green), #FFAB00 (amber), #077A9D (teal)

Author: Matthew Giglia | Databricks Field Engineering | October 2026
"""
import pathlib, markdown

LOGO = "https://cdn.bfldr.com/9AYANS2F/at/9c6z3t9c35wp88vc2t796qq9/primary-lockup-full-color-rgb.svg?auto=webp"
FONT = "https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400&display=swap"

CSS = """
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'DM Sans',system-ui,sans-serif;background:#F5F7F8;color:#1B3139;line-height:1.7;font-size:16px}
header{background:#1B3139;padding:20px 32px;position:sticky;top:0;z-index:100;
  box-shadow:0 2px 12px rgba(0,0,0,.15);display:flex;align-items:center;justify-content:space-between}
header img{height:32px}
header span{color:#D0D7DB;font-size:13px;font-weight:500;letter-spacing:.5px;text-transform:uppercase}
main{max-width:900px;margin:0 auto;padding:48px 32px 80px}
h1{font-size:36px;font-weight:700;color:#1B3139;margin:0 0 8px;line-height:1.2}
h2{font-size:24px;font-weight:700;color:#1B3139;margin:48px 0 16px;padding-top:24px;border-top:2px solid #E8ECEE}
h3{font-size:18px;font-weight:600;color:#2D3B41;margin:28px 0 12px}
h4{font-size:15px;font-weight:600;color:#374850;margin:24px 0 8px}
p{margin-bottom:16px}
strong{font-weight:600}
table{width:100%;border-collapse:collapse;margin:16px 0 24px;font-size:14px}
thead th{background:#1B3139;color:#FFF;padding:12px 16px;text-align:left;font-weight:600;
  font-size:13px;text-transform:uppercase;letter-spacing:.3px}
thead th:first-child{border-radius:8px 0 0 0}
thead th:last-child{border-radius:0 8px 0 0}
tbody td{padding:12px 16px;border-bottom:1px solid #E8ECEE}
tbody tr:hover{background:#F5F7F8}
tbody tr:last-child td:first-child{border-radius:0 0 0 8px}
tbody tr:last-child td:last-child{border-radius:0 0 8px 0}
code{font-family:'JetBrains Mono',monospace;font-size:13px;background:#E8ECEE;
  padding:2px 6px;border-radius:4px;color:#FF3621}
pre{background:#1B3139;color:#E8ECEE;padding:20px 24px;border-radius:10px;
  overflow-x:auto;margin:16px 0 24px;line-height:1.7}
pre code{background:none;padding:0;color:inherit;font-size:13px}
blockquote{border-left:4px solid #FF3621;padding:16px 24px;margin:20px 0;
  background:rgba(255,54,33,.04);border-radius:0 10px 10px 0;font-size:15px}
blockquote strong{color:#FF3621}
ul,ol{padding-left:24px;margin-bottom:16px}
li{margin-bottom:6px}
hr{border:none;border-top:2px solid #E8ECEE;margin:32px 0}
footer{text-align:center;padding:40px 32px;color:#8A9BA3;font-size:13px;border-top:1px solid #E8ECEE}
@media(max-width:768px){main{padding:24px 16px}h1{font-size:28px}h2{font-size:20px}
  table{font-size:12px}thead th,tbody td{padding:8px 10px}}
"""

def render():
    src = pathlib.Path("uc-naming-convention-reference.md")
    if not src.exists():
        print(f"ERROR: {src} not found. Run from the directory containing the markdown file.")
        return

    md_text = src.read_text(encoding="utf-8")
    body = markdown.markdown(md_text, extensions=["tables", "fenced_code", "codehilite"])

    doc_parts = [
        "<!DOCTYPE html>",
        "<html lang='en'>",
        "<head>",
        "<meta charset='UTF-8'>",
        "<meta name='viewport' content='width=device-width,initial-scale=1.0'>",
        "<title>UC Naming Convention - Databricks Best Practices</title>",
        f"<link href='{FONT}' rel='stylesheet'>",
        f"<style>{CSS}</style>",
        "</head>",
        "<body>",
        "<header>",
        f"<img src='{LOGO}' alt='Databricks'/>",
        "<span>Best Practices Guide</span>",
        "</header>",
        "<main>",
        body,
        "</main>",
        "<footer>",
        "<p>Databricks, Inc. | Field Engineering Best Practices | Matthew Giglia | 2026</p>",
        "</footer>",
        "</body>",
        "</html>",
    ]

    out = pathlib.Path("uc-naming-convention-best-practices.html")
    out.write_text("\n".join(doc_parts), encoding="utf-8")
    print(f"Generated: {out} ({out.stat().st_size:,} bytes)")

if __name__ == "__main__":
    render()
