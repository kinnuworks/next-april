# LinkedIn drafts (you post these; tag Gradient Learnings)

Timing: post 1 now, post 2 mid-afternoon, post 3 after you submit (it gives away the station list and the back-test, so other teams can't use it today). Each one ends with a question, as the template asks. Attach the image named under each post.

## Post 1 (now): the problem

Day 1 of the Data Analytics Hackathon by Gradient Learnings.

The dataset is 3,877,013 battery-swap attempts from an electric two- and three-wheeler swap network in six Indian cities. Delivery and bike-taxi riders pull up, drop a flat battery, take a charged one, and leave in about two minutes. When there's no charged pack, they lose time and money.

Completed swaps grew 2.93 times in 18 months, but failed attempts grew 5.98 times. Leadership has four ideas for the next budget: more stations, more batteries, peak pricing everywhere, or an exclusive deal with the biggest fleet partner. My job is to work out which of those the data supports.

First step was checking the data before trusting it. I found six problems the documentation doesn't mention, including two "test" stations that billed ₹39.3 lakh and a field that holds the same value on every row.

What's the most surprising data quality issue you've found in a real dataset?

Image: outputs/charts/q1_trends.png

#DataAnalytics #DataAnalyticsHackathon #DataScience #Analytics #BuildWithData #ProductSpace

## Post 2 (afternoon): the mechanism

Hackathon update (Data Analytics Hackathon, Gradient Learnings).

Why do battery-swap stations fail? I linked hourly cabinet telemetry to every swap attempt in the same station-hour.

At a cabinet temperature of 45°C or more, the oldest cabinets take 156 minutes to charge a pack instead of 88, and they have no charged pack in 37.3% of those hours. The newest cabinets get just as hot and still charge in 43 minutes. When a station has no charged pack, 11.6% of attempts fail, against 5.9% when packs are in stock.

So summer failures aren't really about too few stations. They come from one generation of hardware in the hottest cities.

Has heat ever broken something you thought was a capacity problem?

Image: outputs/charts/q3_mechanism.png

#DataAnalytics #DataAnalyticsHackathon #DataScience #Analytics #BuildWithData #ProductSpace

## Post 3 (after submitting): the answer

Submitted my entry for the Data Analytics Hackathon by Gradient Learnings. It's called Next April.

The question was where a battery-swap network should spend its next budget. The answer: the same 20 stations fail every summer, and they can be named in advance.

I ranked stations using only summer 2024 data, froze the list, and checked it against summer 2025. The ranking held (rank correlation 0.948 across 90 stations). The 20 worst stations of 2024 produced 30.6% of summer 2025's failed attempts while handling 15.0% of attempts. The 60 new stations opened in between didn't change that: those 20 failed at 17.3% of attempts in 2024 and 17.0% in 2025.

New riders who hit failed swaps in their first two weeks left at 33.2%, against 13.3% for riders with none. Separately, a new battery supplier's packs wore out more than three times as fast and cost ₹4.35 crore in extra wear.

My recommendation: replace the old cabinets on the list before April, swap out the weak batteries, and skip the "more stations" plan.

If you had to defend a budget with one chart, which kind would you pick?

Image: outputs/charts/backtest.png

#DataAnalytics #DataAnalyticsHackathon #DataScience #Analytics #BuildWithData #ProductSpace
