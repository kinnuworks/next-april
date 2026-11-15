#!/usr/bin/env python3
"""Checks the submission pieces the rules ask for.

- the report has every required section heading (one per line in the sections file,
  copied from the problem statement's deliverables list);
- the report has an AI-use disclosure section (rule: "Participants must disclose the
  use of AI tools in their analysis or submission.");
- the video, if given, is no longer than the limit (rule: "a 3-minute video").

Usage: check_deliverables.py report.md sections.txt [--video file.mp4] [--max-seconds 180]
"""
import argparse, re, subprocess, sys

ap = argparse.ArgumentParser()
ap.add_argument("report"); ap.add_argument("sections")
ap.add_argument("--video"); ap.add_argument("--max-seconds", type=float, default=180)
a = ap.parse_args()

text = open(a.report, encoding="utf-8").read()
heads = [h.strip().lower() for h in re.findall(r"^#+\s*(.+)$", text, re.M)]
bad = []
for s in (l.strip() for l in open(a.sections) if l.strip() and not l.startswith("#")):
    if not any(s.lower() in h for h in heads):
        bad.append(f"report is missing a section heading containing '{s}'")
if not any("ai" in h.split() or "ai-use" in h or "ai use" in h for h in heads):
    bad.append("report has no AI-use disclosure heading")
if a.video:
    d = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                       "-of", "csv=p=0", a.video]).decode())
    if d > a.max_seconds:
        bad.append(f"video is {d:.1f}s, over {a.max_seconds:.0f}s")
    else:
        print(f"video length {d:.1f}s (limit {a.max_seconds:.0f}s)")
for b in bad:
    print("check_deliverables:", b)
if bad:
    sys.exit(1)
print("check_deliverables: report sections, AI disclosure" + (" and video length" if a.video else "") + " pass")
