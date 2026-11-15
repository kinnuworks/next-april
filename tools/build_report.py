#!/usr/bin/env python3
"""report/report.md -> report/report.html -> report/Next_April_report.pdf (headless Chrome)."""
import os, subprocess, sys, markdown
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
md = open(os.path.join(ROOT, "report", "report.md"), encoding="utf-8").read()
body = markdown.markdown(md, extensions=["tables"])
css = """body{font-family:-apple-system,Helvetica,Arial,sans-serif;max-width:820px;margin:28px auto;color:#222;line-height:1.45;font-size:11pt}
h1{font-size:24pt;margin-bottom:4px}h2{font-size:15pt;margin-top:26px;border-bottom:1px solid #ddd;padding-bottom:3px}h3{font-size:11.5pt;margin:18px 0 4px}
table{border-collapse:collapse;font-size:9pt;margin:10px 0;width:100%}th,td{border:1px solid #ddd;padding:4px 6px;vertical-align:top;text-align:left}th{background:#f4f4f4}
img{max-width:100%;margin:6px 0 10px}code{font-size:9pt}@page{margin:14mm}h2,h3{page-break-after:avoid}img,tr{page-break-inside:avoid}"""
html = f"<!doctype html><html><head><meta charset='utf-8'><title>Next April</title><style>{css}</style></head><body>{body}</body></html>"
out_html = os.path.join(ROOT, "report", "report.html")
open(out_html, "w", encoding="utf-8").write(html)
chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
pdf = os.path.join(ROOT, "report", "Next_April_report.pdf")
subprocess.run([chrome, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={pdf}", f"file://{out_html}"],
               check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("built", pdf)
