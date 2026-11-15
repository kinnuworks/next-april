#!/usr/bin/env python3
"""report/report.md -> report/report.html -> report/Next_April_report.pdf (headless Chrome)."""
import os, subprocess, sys, markdown
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
md = open(os.path.join(ROOT, "report", "report.md"), encoding="utf-8").read()
body = markdown.markdown(md, extensions=["tables"])
# Same type and colours as the briefing page (Brainfish's measured system): Fraunces headings, Geist text, black ink, hairlines.
css = """@font-face{font-family:Fraunces;src:url(../assets/fonts/Fraunces-420.ttf)}
@font-face{font-family:Geist;src:url(../assets/fonts/Geist-400.ttf);font-weight:400}
@font-face{font-family:Geist;src:url(../assets/fonts/Geist-600.ttf);font-weight:600}
body{font-family:Geist,-apple-system,Helvetica,Arial,sans-serif;max-width:820px;margin:28px auto;color:#262626;line-height:1.5;font-size:10.5pt}
.brand{display:flex;align-items:center;gap:8px;font-weight:600;font-size:15pt;letter-spacing:-.02em;color:#000;padding-bottom:12px;border-bottom:1px solid #e5e5e5;margin-bottom:22px}.brand svg{width:26px;height:26px}
h1{font-family:Fraunces,Georgia,serif;font-weight:420;font-size:34pt;line-height:1.02;letter-spacing:-.03em;color:#000;margin:6px 0 10px}
h2{font-family:Fraunces,Georgia,serif;font-weight:420;font-size:20pt;letter-spacing:-.02em;color:#000;margin-top:30px;padding-bottom:6px;border-bottom:1px solid #e5e5e5}
h3{font-size:11.5pt;font-weight:600;color:#000;margin:20px 0 4px}
strong{color:#000;font-weight:600}
table{border-collapse:collapse;font-size:9pt;margin:12px 0;width:100%;border:1px solid #262626;box-shadow:3px 3px 0 0 #262626}
th,td{border-bottom:1px solid #e5e5e5;padding:6px 8px;vertical-align:top;text-align:left}th{background:#f4f5f0;color:#000;font-weight:600;border-bottom:1px solid #262626}
img{max-width:100%;margin:8px 0 12px}code{font-size:9pt;background:#f4f5f0;padding:0 3px;border-radius:3px}
@page{margin:14mm}h2,h3{page-break-after:avoid}img,tr{page-break-inside:avoid}"""
MARK = open(os.path.join(ROOT, "assets", "brand", "mark.svg")).read().strip()
body = f'<div class="brand">{MARK}<span>Gradient Learnings Data Analytics Hackathon</span></div>' + body
html = f"<!doctype html><html><head><meta charset='utf-8'><title>Next April</title><style>{css}</style></head><body>{body}</body></html>"
out_html = os.path.join(ROOT, "report", "report.html")
open(out_html, "w", encoding="utf-8").write(html)
chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
pdf = os.path.join(ROOT, "report", "Next_April_report.pdf")
subprocess.run([chrome, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={pdf}", f"file://{out_html}"],
               check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("built", pdf)
