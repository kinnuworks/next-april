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

The question was where a battery-swap network should spend its next budget. The answer: the same old cabinets fail every summer, and one simple rule names them in advance.

I took summer 2024 alone and gave each station the failure rate of its charger generation in its city. Checked against summer 2025, that rule predicted every station's rate with R² 0.991. The 36 oldest cabinets in Jaipur, Delhi NCR and Hyderabad handled 27.4% of summer attempts and produced 51.2% of the failures. The 60 new stations opened in between didn't change that: those 36 failed on 15.9% of summer attempts in 2024 and 15.6% in 2025.

The surprise was what didn't work. Ranking individual stations by their own history added nothing once you knew the group (rank correlation 0.13), so the fix is the whole group.

New riders who hit failed swaps in their first two weeks left at 33.2%, against 13.3% for riders with none. Separately, a new battery supplier's packs wore out more than three times as fast and cost ₹4.35 crore in extra wear.

My recommendation: replace those old cabinets before April, starting with Jaipur and Delhi NCR, swap out the weak batteries, and skip the "more stations" plan.

If you had to defend a budget with one chart, which kind would you pick?

Image: outputs/charts/backtest.png

#DataAnalytics #DataAnalyticsHackathon #DataScience #Analytics #BuildWithData #ProductSpace
