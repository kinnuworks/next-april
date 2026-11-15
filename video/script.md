# Video script (3:00 max): time | on screen | words spoken | caption | proof | rubric item

Every number is from outputs/facts.json. Order follows the brief: problem, approach, insights, recommendations.

0:00-0:12 | back-test bubble chart | "Every summer, the same 36 swap cabinets fail. A rule from summer 2024 predicted summer 2025, station by station, with an out-of-sample R squared of 0.990." | Same 36 cabinets fail every summer | backtest.png | Insight & Evidence

0:12-0:28 | growth vs failures chart | "VoltRelay grew completed swaps 2.93 times in 18 months, but failed attempts grew 5.98 times. Leadership has four budget ideas: more stations, more batteries, peak pricing, or an exclusive with ZipDrop. Which does the data support?" | Swaps up 2.93x, failures up 5.98x | q1_trends.png | Problem understanding

0:28-0:50 | cleaning table | "First, which numbers to trust. We checked every documented data issue and found six more: test stations that billed 39.3 lakh rupees, 139,490 swaps logged five and a half hours early, and 9,484 battery complaints filed as 'other'." | Six data problems the docs miss | cleaning table | Data cleaning

0:50-1:20 | mechanism chart, then weather chart | "Why: at 45 degrees inside the cabinet, old Gen1 cabinets take 156 minutes to charge a pack instead of 88, and run empty in 37.3% of those hours. Newer cabinets don't slow down. Outside, once the day passes 36 degrees, Gen1 failures jump: Jaipur had 80 such days last summer." | Only Gen1 slows in the heat | q3_mechanism.png, q3_weather.png | Analytical, Evidence

1:20-1:42 | survival curve | "It costs riders. New riders who hit failed swaps early leave in their first month: 90 days in, 70.8% are still swapping against 80.7%." | Early failures drive riders away | q6_survival.png | Insight

1:42-2:02 | Kyron + ZipDrop | "Margins are a separate problem. Kyron batteries wore out 3.22 times faster, 4.35 crore rupees of extra wear. ZipDrop's discount went from 12 to 28 percent, 11.78 rupees less per swap than other partners." | Kyron and ZipDrop are the margin leaks | q4_kyron.png, q5_partners.png | Insight

2:02-2:45 | ranked actions table | "So: don't fund more stations; the 60 new ones went everywhere except where failures happen. Before April, put 427 charged packs at the 36 hot stations, moved from cool cities or taken from the Kyron replacement order. Replace Kyron packs. Protect new riders' first two weeks. Reopen ZipDrop. Pricing raises revenue, not reliability." | Six actions, six owners, each sized | budget verdicts | Recommendations & Viz

2:45-3:00 | one-page summary | "Every number here comes from a notebook that runs top to bottom, re-checked by independent tests. AI helped write the code; every output was checked." | Next April | site | Completeness

Thumbnail: the back-test bubble chart with "Same 36 cabinets fail every summer".
