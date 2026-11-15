# Next April: submission text

Next April shows VoltRelay which 36 swap cabinets will fail again next summer, why they fail, and what to fund instead of more stations, with every number computed and re-checked from the organiser's data.

**Problem.** Completed swaps grew 2.93 times in 18 months, but failed attempts grew 5.98 times, and leadership has four budget proposals on the table: more stations, more batteries, network-wide peak pricing, and an exclusive with ZipDrop, its largest fleet partner.

**Data cleaning.** We checked every documented issue and found six the documentation misses, each with a row count and its effect on a result: test stations that billed ₹39.3 lakh, 139,490 swaps logged five and a half hours early by one firmware version, 9,484 battery complaints filed as "other", a payment field that never changes, packs issued before their commission date, and Kyron packs still issued 36,277 times after their recorded retirement.

**Key insights.** The 36 Gen1 cabinets in Jaipur, Delhi NCR and Hyderabad handled 27.4% of summer 2025 attempts and produced 51.2% of the failures. Cabinet telemetry shows why: at 45°C or more inside the cabinet, a Gen1 cabinet takes 156 minutes to charge a pack instead of 88 and runs out of charged packs in 37.3% of those hours, while Gen3 cabinets still charge in 43 minutes. A rule built from summer 2024 alone predicted summer 2025 for the 90 stations open both summers with an out-of-sample R² of 0.990, and the 60 new stations opened in between did not change it. New riders who hit more than 20% failed swaps in their first two weeks left at 33.2%, against 13.3%. Margins are a separate problem: Kyron packs wore out 3.22 times as fast as other suppliers' packs, costing ₹4.35 crore in extra wear.

**Recommendations.** Before April, put 427 charged packs at the 36 hot stations, sized from each station's busiest summer hour and its measured charge times, and moved from cool-city stations or taken from the Kyron replacement order. Replace the Kyron fleet, protect new riders' first two weeks, reopen the ZipDrop contract (₹11.78 less per swap than other partners after its discount went from 12% to 28%), and roll out peak pricing for revenue only: the pilot added ₹5.41 per swap but did not reduce failures. Each action has an owner, a sized effect and a confidence level.

**How we checked it.** The Colab notebook downloads the organiser's files and runs top to bottom. Independent tests re-derive the headline numbers, a script fails if any text quotes a number the notebook did not compute, and a self-audit recomputes the headlines under other reasonable choices.

**AI use.** An AI coding assistant (Claude) helped write code and draft text. Every output was checked against the data by the notebook, the tests and the number-tracing script.
