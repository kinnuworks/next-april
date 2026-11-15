#!/usr/bin/env python3
"""Every number written in a text file must come from facts.json.

The notebook writes facts.json: {"fact_name": number, ...}. This script pulls every
number out of the given text files (report, README, video script, captions) and fails
on any number that doesn't match a fact at the precision it is written with.

A written number matches a fact when rounding the fact to the written number's
decimal places gives the written number. Percentages also match a fact stored as a
share (0.123 -> 12.3%). Thousands separators, Indian grouping (12,34,567), ₹ and
suffixes K / M / L / lakh / Cr / crore are understood.

Numbers that aren't data (section numbers, years, "3-minute", question labels) go in
an allow file, one per line, as `<number>  # why`.

Usage: check_claims.py facts.json [--allow allow.txt] file [file ...]
"""
import argparse
import json
import re
import sys

SCALE = {"k": 1e3, "m": 1e6, "l": 1e5, "lakh": 1e5, "lakhs": 1e5, "cr": 1e7, "crore": 1e7, "crores": 1e7, "bn": 1e9}
NUM = re.compile(
    r"(?<![\w.])(?P<num>\d{1,3}(?:,\d{2,3})+(?:\.\d+)?|\d+(?:\.\d+)?)"
    r"(?P<pct>\s?%)?"
    r"(?:\s?(?P<suf>lakhs?|crores?|cr|bn|[kml])\b)?",
    re.IGNORECASE,
)


def decimals(s):
    return len(s.split(".")[1]) if "." in s else 0


def candidates(fact):
    """Values a fact may be written as. The sign is read separately (a minus before ₹
    is not part of the number the regex sees), so magnitudes are compared."""
    for v in (fact, fact * 100):  # share written as a percentage
        yield v
        yield abs(v)


def matches(written, places, fact):
    for v in candidates(fact):
        if round(v, places) == round(written, places):
            return True
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("facts")
    ap.add_argument("--allow")
    ap.add_argument("files", nargs="+")
    a = ap.parse_args()

    facts = json.load(open(a.facts))
    vals = [float(v) for v in facts.values() if isinstance(v, (int, float)) and not isinstance(v, bool)]
    # Facts already stored in a unit (key ends _lakh / _cr / _crore) match "₹x lakh" / "₹x crore" directly.
    unit_vals = {"l": [], "lakh": [], "lakhs": [], "cr": [], "crore": [], "crores": []}
    for k, v in facts.items():
        if not isinstance(v, (int, float)) or isinstance(v, bool):
            continue
        if k.endswith("_lakh"):
            for u in ("l", "lakh", "lakhs"): unit_vals[u].append(float(v))
        if k.endswith("_cr") or k.endswith("_crore"):
            for u in ("cr", "crore", "crores"): unit_vals[u].append(float(v))
    allow = set()
    if a.allow:
        for line in open(a.allow):
            line = line.split("#")[0].strip()
            if line:
                allow.add(line)

    bad = 0
    for path in a.files:
        for n, line in enumerate(open(path, encoding="utf-8"), 1):
            for m in NUM.finditer(line):
                raw = m.group("num")
                if raw in allow:
                    continue
                written = float(raw.replace(",", ""))
                places = decimals(raw)
                suf = (m.group("suf") or "").lower()
                if suf:
                    # "1.2M" is 1,200,000 written to 0.1M precision.
                    mult = SCALE[suf]
                    if any(round(abs(f) / mult, places) == round(written, places) for f in vals):
                        continue
                    if any(round(abs(f), places) == round(written, places) for f in unit_vals.get(suf, [])):
                        continue
                elif any(matches(written, places, f) for f in vals):
                    continue
                bad += 1
                print(f"{path}:{n}: '{m.group(0).strip()}' is not in facts.json -> {line.strip()[:120]}")
    if bad:
        print(f"check_claims: {bad} number(s) without a fact")
        sys.exit(1)
    print(f"check_claims: every number in {len(a.files)} file(s) traces to facts.json")


if __name__ == "__main__":
    main()
