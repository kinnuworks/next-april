# Next April

Twenty battery-swap stations will fail again next summer. This analysis names them, shows why they fail, and says what VoltRelay should fund instead of more stations.

A list built only from summer 2024 data predicted which stations failed in summer 2025 (rank correlation 0.948 across 90 stations). The 20 worst stations of 2024 produced 30.6% of summer 2025's failed attempts while handling 15.0% of attempts.

![Back-test: the 2024 list against summer 2025](outputs/charts/backtest.png)

**Run it in about two minutes:** open `notebooks/next_april.ipynb` in Google Colab and choose Runtime → Run all. It downloads the organiser's eight CSV files itself and runs top to bottom.

**Read it in five:** [`report/Next_April_report.pdf`](report/Next_April_report.pdf).

## What it finds

1. Failures are a summer problem at old Gen1 cabinets in Jaipur, Delhi NCR and Hyderabad. In April to June, Gen1 fails on 12.9% of attempts against 5.1% for Gen3.
2. Cabinet telemetry shows why. At 45°C or more, a Gen1 cabinet takes 156 minutes to charge a pack instead of 88, and has none charged in 37.3% of those hours.
3. The same 20 stations fail every summer. The 60 new stations from the expansion waves did not reach them: those 20 failed at 17.3% of attempts in 2024 and 17.0% in 2025.
4. New riders who hit failed swaps in their first 14 days left at 33.2%, against 13.3% for riders with none.
5. Kyron, the new battery supplier, is the margin problem: its 2W packs cost ₹4.35 crore in extra wear and were all written off on 15 June 2025.
6. ZipDrop, the largest fleet partner, is the least profitable per swap after its discount rose from 12% to 28%.

## What to fund

| Proposal | Verdict | Instead |
|---|---|---|
| More stations | Not as proposed | Swap the Gen1 cabinets on the April list for Gen3 before 1 April 2026 |
| More batteries | Yes, as replacement | Replace the Kyron 2W fleet; stop issuing "retired" Kyron packs |
| Network-wide pricing | Yes for revenue only | Pilot added ₹5.41 per swap but did not reduce failures |
| ZipDrop exclusive | No | Reopen the contract |

## Files

- `notebooks/next_april.ipynb`: the analysis, run top to bottom (source: `notebooks/next_april.py`).
- `report/Next_April_report.pdf`: the analysis report.
- `outputs/facts.json`: every number used in the report, written by the notebook.
- `outputs/april_2026_list.csv`, `outputs/cleaning_table.csv`, `outputs/budget_verdicts.csv`, `outputs/self_audit.csv`, `outputs/charts/`.
- `tests/`: independent re-derivations of the headline numbers. `./check.sh` runs the notebook, the tests, and a check that every number in the text is in `facts.json`.

## AI use

An AI coding assistant (Claude) helped write code and draft text. Every number is computed by the notebook and checked by independent tests and a number-tracing script; see the report's AI use section.

Data: the synthetic VoltRelay dataset provided by Gradient Learnings for this hackathon.
