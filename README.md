# Next April

The same 36 old battery-swap cabinets will fail again next summer (April to June). This analysis shows which ones, why, and what VoltRelay should fund instead of more stations.

One rule from summer 2024 (each station gets the failure rate of its charger generation in its city) predicted every station's summer 2025 failure rate with R² 0.991. The 36 Gen1 stations, the oldest cabinet generation, in Jaipur, Delhi NCR and Hyderabad handled 27.4% of summer 2025 attempts and produced 51.2% of its failed attempts.

![Back-test: the summer 2024 rule against summer 2025](outputs/charts/backtest.png)

**Run it in about two minutes:** open `notebooks/next_april.ipynb` in Google Colab and choose Runtime → Run all. It downloads the organiser's eight CSV files itself and runs top to bottom.

**Read it in five:** [`report/Next_April_report.pdf`](report/Next_April_report.pdf).

## What it finds

1. Failures are a summer problem at old Gen1 cabinets in Jaipur, Delhi NCR and Hyderabad. In April to June, Gen1 fails on 12.9% of attempts against 5.1% for Gen3.
2. Cabinet telemetry shows why. At 45°C or more, a Gen1 cabinet takes 156 minutes to charge a pack instead of 88, and has none charged in 37.3% of those hours.
3. The same stations fail every summer. The 60 new stations from the expansion waves did not reach them: the 36 failed on 15.9% of summer attempts in 2024 and 15.6% in 2025.
4. New riders who hit failed swaps in their first 14 days left at 33.2%, against 13.3% for riders with none.
5. Kyron, the new battery supplier, is the margin problem: its 2W packs cost ₹4.35 crore in extra wear and were all written off on 15 June 2025.
6. ZipDrop, the largest fleet partner, is the least profitable per swap after its discount rose from 12% to 28%.

## What to fund

| Proposal | Verdict | Instead |
|---|---|---|
| More stations | Not as proposed | Swap those 36 Gen1 cabinets for Gen3 before 1 April 2026, Jaipur and Delhi NCR first |
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
