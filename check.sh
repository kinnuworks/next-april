#!/usr/bin/env bash
# Checks that prove the submission works. Run by the Stop hook.
# 1. The notebook runs top to bottom in a fresh kernel from the organiser's data and
#    rewrites outputs/facts.json (problem statement: "Should run top to bottom without errors").
# 2. Independent tests re-derive the headline numbers with their own queries.
# 3. Every number in the report, the notebook's prose, and any README / video script /
#    LinkedIn draft that exists traces to facts.json.
# 4. The report has the sections the problem statement asks for and an AI-use disclosure;
#    the video (once it exists) is at most 3:00.
set -euo pipefail
cd "$(dirname "$0")"
PY=.venv/bin/python

NA_ROOT=$PWD tools/run_notebook.sh notebooks/next_april.ipynb 1800
# run_notebook executes a copy; refresh the saved outputs only through the same path the judges use
NA_ROOT=$PWD .venv/bin/jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=1800 notebooks/next_april.ipynb >/dev/null 2>&1

$PY -m pytest -q tests

$PY -c "
import json,sys
nb=json.load(open('notebooks/next_april.ipynb'))
open('outputs/notebook_prose.md','w').write('\n'.join(''.join(c['source']) for c in nb['cells'] if c['cell_type']=='markdown'))
"
$PY -c "
import re
h=open('site/index.html',encoding='utf-8').read()
h=re.sub(r'<(script|style)[^>]*>.*?</\\1>','',h,flags=re.S); h=re.sub(r'<[^>]+>',' ',h); h=re.sub(r'STN-[A-Z]+-[0-9]+','STN',h)
open('outputs/site_text.md','w').write(h)
"
texts=(report/report.md outputs/notebook_prose.md outputs/site_text.md)
for f in README.md video/script.md video/captions.srt linkedin/posts.md submission/submission.md; do [ -f "$f" ] && texts+=("$f"); done
$PY tools/check_claims.py outputs/facts.json --allow report/allow.txt "${texts[@]}"

video_args=()
[ -f video/next_april.mp4 ] && video_args=(--video video/next_april.mp4)
$PY tools/check_deliverables.py report/report.md report/sections.txt "${video_args[@]+"${video_args[@]}"}"

$PY tools/build_report.py >/dev/null
echo "check.sh: all checks passed"
