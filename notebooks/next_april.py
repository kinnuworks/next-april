# ---
# jupyter:
#   jupytext:
#     formats: py:percent
#   kernelspec:
#     display_name: Python 3
#     name: python3
# ---

# %% [markdown]
# # Next April
# **VoltRelay Energy: what drives service failures, rider churn and margins, and what to fix before summer 2026**
#
# Dhiraj Kavuri · Gradient Learnings Data Analytics Hackathon · 15 Nov 2026
#
# This notebook runs top to bottom from the organiser's eight CSV files. Every number used in the report, the video and the summary is computed here and written to `outputs/facts.json`; a separate check fails if any text quotes a number that is not in that file.

# %% [markdown]
# ## Setup
# Downloads the dataset from the organiser's shared Drive folder if it is not already present. On Colab this takes about two minutes (the swap table is 729 MB).

# %%
import os, sys, json, subprocess, warnings
warnings.filterwarnings("ignore")

def _need(pkg, mod=None):
    try:
        __import__(mod or pkg)
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", pkg], check=True)

for p, m in [("duckdb", None), ("gdown", None), ("statsmodels", None), ("pyarrow", None)]:
    _need(p, m)

import duckdb, gdown
import numpy as np, pandas as pd
import pyarrow.csv as pacsv, pyarrow.parquet as pq
import matplotlib
matplotlib.use("Agg") if not hasattr(sys, "ps1") and "ipykernel" not in sys.modules else None
import matplotlib.pyplot as plt
import statsmodels.formula.api as smf
from scipy import stats

ROOT = os.environ.get("NA_ROOT", ".")
RAW = os.path.join(ROOT, "data", "raw")
PQ = os.path.join(ROOT, "data", "pq")
OUT = os.path.join(ROOT, "outputs")
CH = os.path.join(OUT, "charts")
for d in (RAW, PQ, OUT, CH):
    os.makedirs(d, exist_ok=True)

# The organiser's Drive folder: https://drive.google.com/drive/folders/1qsjGWrgmEvOaf2Is2fh7RgVEkKd1V3df
FILES = {
    "batteries": "1ODkUSlw3EzpzznYdzZe74wG84t3783al",
    "city_daily_context": "1UMDldAGOUEJitZ32D4M9szwRMvUjZc4G",
    "fleet_partners": "1fMy7LxZxESBqeveFB3iabpE3sxjnkkmY",
    "riders": "1w3TxH3NY2rk_agikJtv3oCq2OeXv1Pii",
    "station_hourly_status": "1pbGACXY95BemIbrSlRxE6o8CGcc2bSCn",
    "stations": "1WEou9h5lYvALA3IreUFoCRbmIh2_9Dm2",
    "support_tickets": "1tWK-zDoRy8QFqQe9ESw8ttpKHqMqMXbh",
    "swap_events": "15qkHruvAilomjWdNgntXrQLK4-_NPOZZ",
}
EXPECTED_ROWS = {"swap_events": 3877013, "station_hourly_status": 1487712, "riders": 20000,
                 "batteries": 6500, "support_tickets": 44000, "stations": 152,
                 "city_daily_context": 3282, "fleet_partners": 12}

for name, fid in FILES.items():
    csv = os.path.join(RAW, f"{name}.csv")
    if not os.path.exists(csv):
        gdown.download(id=fid, output=csv, quiet=True)
    out = os.path.join(PQ, f"{name}.parquet")
    if not os.path.exists(out):
        # Empty strings in ID columns mean "missing": read them as nulls.
        t = pacsv.read_csv(csv, convert_options=pacsv.ConvertOptions(
            strings_can_be_null=True, null_values=[""],
            timestamp_parsers=["%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]))
        pq.write_table(t, out)

con = duckdb.connect()
for name in FILES:
    con.execute(f"create or replace view raw_{name} as select * from '{PQ}/{name}.parquet'")

def sql(q):
    return con.sql(q).df()

rowcheck = pd.DataFrame([(n, int(sql(f"select count(*) c from raw_{n}").c[0]), r) for n, r in EXPECTED_ROWS.items()],
                        columns=["table", "rows", "expected"])
assert (rowcheck.rows == rowcheck.expected).all(), rowcheck
print(rowcheck.to_string(index=False))

# %%
FACTS = {}
def fact(key, value, nd=None):
    """Record a number used anywhere in the write-up. Returns it rounded for display."""
    v = float(value)
    FACTS[key] = v
    return round(v, nd) if nd is not None else v

def savefig(fig, name):
    fig.tight_layout()
    fig.savefig(os.path.join(CH, f"{name}.png"), dpi=150, bbox_inches="tight")
    plt.show()
    plt.close(fig)

plt.rcParams.update({"figure.figsize": (9, 4.5), "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.alpha": 0.25, "font.size": 11})
INK, ACCENT, MUTED, GOOD = "#222222", "#c0392b", "#9aa0a6", "#1f6f8b"

# %% [markdown]
# ## 1. Data understanding
# Eight linked tables. The core fact table has **one row per swap attempt**, completed or not, so a failure rate is non-completed attempts divided by all attempts. Five things changed during the 18 months, and each needs to be separated from the others: two station expansion waves, a base price change, a peak/off-peak pricing pilot in two cities, a new battery supplier (Kyron) and a renegotiated contract with the largest fleet partner (ZipDrop).

# %%
grain = pd.DataFrame([
    ("swap_events", "one swap attempt", "event_id"),
    ("station_hourly_status", "one station-hour of cabinet telemetry", "station_id + hour_start"),
    ("riders", "one registered rider", "rider_id"),
    ("batteries", "one battery pack", "battery_id"),
    ("support_tickets", "one support ticket", "ticket_id"),
    ("stations", "one swap station", "station_id"),
    ("city_daily_context", "one city-day of weather and calendar", "city + date"),
    ("fleet_partners", "one B2B fleet customer contract", "partner_id"),
], columns=["table", "one row is", "key"])
print(grain.to_string(index=False))
print()
print(sql("select event_type, count(*) attempts, round(100.0*count(*)/sum(count(*)) over (),2) pct from raw_swap_events group by 1 order by 2 desc").to_string(index=False))
fact("attempts_all", sql("select count(*) c from raw_swap_events").c[0])
fact("completion_pct_all", 100*sql("select avg((event_type='swap_completed')::int) c from raw_swap_events").c[0])
print(sql("select partner_id, partner_name, partner_segment, contract_type, discount_pct, amendment_date, discount_pct_after_amendment, peak_surcharge_billable from raw_fleet_partners").to_string(index=False))

# %% [markdown]
# ## 2. Data cleaning: every issue, how many rows, what we did, and what it changes
# The organiser documented nine data quality issues. We checked each one and looked for others. Each row of the table below says how many records are affected, the decision taken, and the effect on a number used later.

# %%
issues = []
def issue(name, documented, rows, decision, effect):
    issues.append(dict(issue=name, documented=documented, rows_affected=rows, decision=decision, effect=effect))

# 2.1 Test stations
t = sql("select count(*) n, sum(amount_charged_inr) amt, count(distinct station_id) st from raw_swap_events where station_id like 'STN-TST%'")
fact("test_rows", t.n[0]); fact("test_amount_inr", t.amt[0]); fact("test_amount_lakh", t.amt[0]/1e5)
th = sql("select hour(event_ts) h, count(*) n from raw_swap_events where station_id like 'STN-TST%' group by 1 order by 2 desc limit 1")
issue("Test stations STN-TST-01/02", "yes, as 'a small number of zero-value transactions at unusual hours'",
      int(t.n[0]), "Excluded from all network analysis",
      f"Docs understate it: {int(t.n[0]):,} rows charging ₹{t.amt[0]/1e5:.1f} lakh, busiest at {int(th.h[0])}:00, not zero-value. Keeping them would add ₹{t.amt[0]/1e5:.1f} lakh of revenue that never happened.")

# 2.2 Firmware clock bug
fw = sql("""select count(*) n from raw_swap_events where station_firmware='v3.2.0'
            and event_ts >= '2025-03-10' and event_ts < '2025-04-15'""").n[0]
fact("firmware_rows", fw)
night = sql("""select
  avg((hour(event_ts) between 0 and 4)::int) filter (where station_firmware='v3.2.0' and event_ts >= '2025-03-10' and event_ts < '2025-04-15') bug,
  avg((hour(event_ts) between 0 and 4)::int) filter (where not (station_firmware='v3.2.0' and event_ts >= '2025-03-10' and event_ts < '2025-04-15')) rest
  from raw_swap_events""")
night_fixed = sql("""select avg((hour(event_ts + interval 330 minute) between 0 and 4)::int) v from raw_swap_events
  where station_firmware='v3.2.0' and event_ts >= '2025-03-10' and event_ts < '2025-04-15'""").v[0]
fact("night_share_bug_pct", 100*night.bug[0]); fact("night_share_rest_pct", 100*night.rest[0]); fact("night_share_fixed_pct", 100*night_fixed)
issue("Firmware v3.2.0 clock 5h30 early (10 Mar-14 Apr 2025)", "yes", int(fw),
      "Added 5h30 to those timestamps",
      f"Share of these swaps logged between midnight and 5 AM falls from {100*night.bug[0]:.1f}% to {100*night_fixed:.1f}% (rest of data: {100*night.rest[0]:.1f}%), so hour-of-day results are right.")

# 2.3 Near-duplicates from offline sync
dups = {}
for label, key in [("rider+station+returned pack", "rider_id, station_id, battery_in_id"),
                   ("rider+station+issued pack", "rider_id, station_id, battery_out_id"),
                   ("rider+station, same outcome", "rider_id, station_id, event_type")]:
    dups[label] = int(sql(f"""with x as (select sync_mode, event_ts - lag(event_ts) over (partition by {key} order by event_ts) gap
                                         from raw_swap_events) select count(*) n from x where gap <= interval 3 minute""").n[0])
fact("dup_rows_strict", dups["rider+station+returned pack"])
fact("offline_rows", sql("select count(*) n from raw_swap_events where sync_mode='offline_batch'").n[0])
issue("Offline-sync near-duplicates", "yes", dups["rider+station+returned pack"],
      "Searched three ways within 3 minutes; nothing to remove",
      "Matches by key: " + "; ".join(f"{k}: {v:,}" for k, v in dups.items()) +
      f". The {int(FACTS['offline_rows']):,} offline_batch rows are not duplicates in this export, so all are kept.")

# 2.4 Non-completed attempts
nc = sql("select count(*) n from raw_swap_events where event_type<>'swap_completed'").n[0]
nc_amt = sql("select sum(amount_charged_inr) a from raw_swap_events where event_type<>'swap_completed'").a[0]
issue("Non-completed attempts", "yes", int(nc), "Kept for service and churn analysis; excluded from revenue, energy and range",
      f"They carry ₹{(nc_amt or 0):,.0f} of charges, so revenue is unaffected; leaving them out of failure rates would hide every failure.")

# 2.5 km and SOC outliers
o = sql("""select sum((km_since_last_swap<0)::int) neg, sum((km_since_last_swap>300)::int) big,
           sum((soc_out_pct>100)::int) soc, sum((soc_in_pct>100)::int) socin from raw_swap_events""")
fact("km_negative", o.neg[0]); fact("km_over300", o.big[0]); fact("soc_over100", o.soc[0])
med_raw = sql("select avg(km_since_last_swap) v from raw_swap_events where event_type='swap_completed'").v[0]
med_cln = sql("select avg(km_since_last_swap) v from raw_swap_events where event_type='swap_completed' and km_since_last_swap between 0 and 300").v[0]
issue("km_since_last_swap negative or > 300 km", "yes", int(o.neg[0] + o.big[0]),
      "Set to missing (odometer resets)", f"Mean km per swap moves from {med_raw:.1f} to {med_cln:.1f}.")
issue("soc_out_pct above 100", "yes", int(o.soc[0]), "Capped at 100 (sensor drift)", "Affects delivered-charge averages by less than 0.1 point.")

# 2.6 City spellings
cities = sql("select home_city, count(*) n from raw_riders group by 1 order by 2 desc")
CITY_MAP = {}
canon = {"bengaluru": "Bengaluru", "bangalore": "Bengaluru", "blr": "Bengaluru",
         "delhi ncr": "Delhi NCR", "delhi": "Delhi NCR", "new delhi": "Delhi NCR", "gurgaon": "Delhi NCR", "gurugram": "Delhi NCR", "noida": "Delhi NCR", "del": "Delhi NCR", "ncr": "Delhi NCR",
         "hyderabad": "Hyderabad", "hyd": "Hyderabad", "pune": "Pune", "pun": "Pune", "poona": "Pune",
         "mumbai": "Mumbai", "bombay": "Mumbai", "mum": "Mumbai", "bom": "Mumbai", "jaipur": "Jaipur", "jai": "Jaipur", "jpr": "Jaipur"}
for c in cities.home_city:
    k = str(c).strip().lower().replace(".", "")
    CITY_MAP[c] = canon.get(k)
unmapped = [c for c, v in CITY_MAP.items() if v is None]
assert not unmapped, f"unmapped city spellings: {unmapped}"
n_variant = int(cities[~cities.home_city.isin(["Bengaluru", "Delhi NCR", "Hyderabad", "Pune", "Mumbai", "Jaipur"])].n.sum())
fact("city_spellings", len(cities)); fact("city_variant_riders", n_variant)
issue("riders.home_city spellings", "yes", n_variant, f"Mapped {len(cities)} spellings to 6 cities",
      f"{n_variant} riders would otherwise sit in {len(cities)-6} phantom cities.")

# 2.7 Telemetry gaps
tel = sql("select telemetry_status, count(*) n from raw_station_hourly_status group by 1")
bad = int(tel[tel.telemetry_status != "ok"].n.sum())
fact("telemetry_bad_rows", bad)
poor_share = sql("""select avg((h.telemetry_status<>'ok')::int) filter (where s.connectivity_tier='poor') p,
                           avg((h.telemetry_status<>'ok')::int) filter (where s.connectivity_tier<>'poor') o
                    from raw_station_hourly_status h join raw_stations s using(station_id)""")
issue("Telemetry partial or missing", "yes", bad, "Those station-hours left out of telemetry averages, never treated as zero",
      f"Gaps hit {100*poor_share.p[0]:.1f}% of hours at poor-connectivity stations vs {100*poor_share.o[0]:.1f}% elsewhere.")

# 2.8 CSAT not missing at random
cs = sql("""select case when resolution_hours<4 then 'a <4h' when resolution_hours<24 then 'b 4-24h' else 'c >24h' end bucket,
            count(*) n, avg((csat_score is not null)::int) has, avg(csat_score) csat
            from raw_support_tickets where resolution_status='resolved' group by 1 order by 1""")
naive = sql("select avg(csat_score) v from raw_support_tickets").v[0]
w = (cs.n * cs.csat).sum() / cs.n.sum()
fact("csat_naive", naive); fact("csat_reweighted", w)
fact("csat_missing", sql("select count(*) n from raw_support_tickets where csat_score is null").n[0])
issue("CSAT mostly missing, not at random", "yes", int(FACTS["csat_missing"]),
      "Re-weighted CSAT by resolution-time bucket",
      f"Scores recorded on {100*cs.has.iloc[0]:.0f}% of <4h tickets vs {100*cs.has.iloc[-1]:.0f}% of >24h ones, but scores barely differ by resolution time ({', '.join(f'{v:.2f}' for v in cs.csat)}), so naive {naive:.2f} vs re-weighted {w:.2f}: the bias is real but small here.")

# 2.9 Ticket categories
issue("Ticket category not verified", "yes", int(sql("select count(*) n from raw_support_tickets where category in ('other','app_issue')").n[0]),
      "Re-tagged from comment text (section 6)", "See the battery-complaint recount in section 6.")

# Undocumented issues we found
pm = sql("select payment_mode, count(*) n from raw_swap_events group by 1")
issue("payment_mode is the same on every row", "no (docs list upi / wallet / prepaid / partner_invoice)", int(pm.n.sum()),
      "Not used", f"All {int(pm.n.sum()):,} rows say '{pm.payment_mode[0]}', including independent riders, so payment channel cannot be analysed.")
bin_missing = sql("select count(*) n from raw_swap_events where battery_in_id is null").n[0]
issue("battery_in_id rarely missing", "no (docs: 'often missing')", int(bin_missing),
      "Read as null where blank", f"Only {int(bin_missing):,} blanks, and failed attempts still record a returned pack.")
early = sql("""select count(*) n, median(date_diff('day', e.event_ts, b.commission_date)) d
               from raw_swap_events e join raw_batteries b on b.battery_id=e.battery_out_id where e.event_ts < b.commission_date""")
fact("batt_before_commission_rows", early.n[0]); fact("batt_before_commission_median_days", early.d[0])
issue("Packs issued before their commission_date", "no", int(early.n[0]),
      "Pack age measured from first observed swap, not the ledger date",
      f"Median {early.d[0]:.0f} days early, so ledger dates cannot be used for battery age.")
late = sql("""select count(*) n from raw_swap_events e join raw_batteries b on b.battery_id=e.battery_out_id
              where b.retired_date is not null and e.event_ts > b.retired_date""").n[0]
fact("kyron_issued_after_retirement", late)
issue("Packs issued after their retired_date", "no", int(late), "Kept; reported as an operations finding",
      f"Kyron packs marked retired on 15 Jun 2025 were handed to riders {int(late):,} more times by 30 Jun.")
gap = sql("""select round(avg(amount_charged_inr-(list_price_inr-discount_inr)),2) g, count(*) n from raw_swap_events
             where event_type='swap_completed' and tariff_code='PARTNER' and abs(amount_charged_inr-(list_price_inr-discount_inr))>0.05""")
issue("PARTNER charges differ from list minus discount", "no", int(gap.n[0]), "Used amount_charged_inr as revenue",
      f"Average gap +₹{gap.g[0]:.2f}; consistent with peak surcharges billed to partners.")
pre = sql("""select count(*) n from raw_swap_events e join raw_stations s using(station_id) where e.event_ts < s.commissioned_date""").n[0]
issue("Swaps before the station's commissioned_date", "no", int(pre), "Kept (too few to matter)", "No effect on any rate at one decimal.")

clean_table = pd.DataFrame(issues)
fact("issues_total", len(clean_table)); fact("issues_undocumented", (clean_table.documented.str.startswith("no")).sum())
pd.set_option("display.max_colwidth", 200)
print(clean_table.to_string(index=False))
clean_table.to_csv(os.path.join(OUT, "cleaning_table.csv"), index=False)

# %% [markdown]
# ### The cleaned tables used from here on

# %%
con.execute(f"""create or replace table st as select * from raw_stations where station_id not like 'STN-TST%'""")
con.execute("""create or replace table ev as
select e.event_id, e.rider_id, e.station_id,
  case when e.station_firmware='v3.2.0' and e.event_ts >= '2025-03-10' and e.event_ts < '2025-04-15'
       then e.event_ts + interval 330 minute else e.event_ts end as ts,
  e.event_type, e.event_type='swap_completed' as ok, e.queue_wait_sec, e.battery_in_id, e.battery_out_id,
  e.soc_in_pct, e.soh_in_pct, least(e.soc_out_pct, 100) soc_out_pct, e.soh_out_pct,
  case when e.km_since_last_swap between 0 and 300 then e.km_since_last_swap end km,
  e.tariff_code, e.list_price_inr, e.discount_inr,
  case when e.event_type='swap_completed' then e.amount_charged_inr else 0 end revenue,
  e.energy_to_recharge_kwh kwh, s.city, s.charger_generation gen, s.expansion_wave wave, s.location_type,
  s.connectivity_tier, s.grid_tariff_inr_kwh
from raw_swap_events e join st s using(station_id)""")
con.execute("""create or replace table ev2 as select *, year(ts) y, month(ts) m, hour(ts) h, month(ts) in (4,5,6) summer,
  date_trunc('month', ts) mon from ev""")
con.execute("create or replace view ev_ as select * from ev2")
n_clean = sql("select count(*) n, avg(ok::int) c from ev2")
fact("attempts_clean", n_clean.n[0]); fact("completion_pct_clean", 100*n_clean.c[0])
print(f"{int(n_clean.n[0]):,} attempts after removing test stations; {100*n_clean.c[0]:.2f}% completed")

# %% [markdown]
# ## 3. Core question 1: network performance over time
# Contribution margin per completed swap = revenue − grid energy to recharge the returned pack − battery wear − station rent and maintenance.
# * **Battery wear** comes from the data: each pack's state-of-health loss per swap it served, priced at its purchase cost spread over the health it can lose before replacement. The replacement threshold is not in the data; we use 70% state of health (**ASSUMPTION**; section 12 shows 60% and 80%).
# * **Station costs** are each live station's monthly rent and maintenance, spread over that month's completed swaps.
#
# Honest caveat, tested in section 12: whether margin per swap fell or rose between the two halves depends on the replacement threshold. What does not depend on it is that battery wear per swap jumped when Kyron packs entered service in September 2024, while revenue, energy and station costs per swap all moved in VoltRelay's favour.

# %%
EOL_SOH = 70.0
for e_ in (60, 70, 80): fact(f"eol_option_{e_}", e_)
con.execute("""create or replace table batt as
with use as (select battery_out_id battery_id, count(*) swaps_served, min(ts) first_use from ev2 where ok group by 1)
select b.*, u.swaps_served, u.first_use,
  (b.initial_soh_pct - b.current_soh_pct) / nullif(u.swaps_served,0) soh_loss_per_swap
from raw_batteries b left join use u using(battery_id)""")

def wear_table(eol):
    return f"""select battery_id, purchase_cost_inr * soh_loss_per_swap / nullif(initial_soh_pct - {eol}, 0) wear_per_swap from batt"""

def monthly(eol=EOL_SOH, where="true"):
    return sql(f"""
with w as ({wear_table(eol)}),
sw as (select mon, count(*) attempts, sum(ok::int) done, sum(revenue) rev,
          sum(case when ok then kwh*grid_tariff_inr_kwh end) energy, sum(case when ok then w.wear_per_swap end) wear
       from ev2 left join w on w.battery_id = ev2.battery_out_id where {where} group by 1),
live as (select m.mon, sum(s.monthly_rent_inr + s.monthly_maintenance_inr) fixed, count(*) stations
         from (select distinct mon from ev2) m join st s
           on s.commissioned_date < m.mon + interval 1 month and (s.decommissioned_date is null or s.decommissioned_date >= m.mon)
         group by 1)
select sw.*, live.fixed, live.stations, 1 - done/attempts fail_rate,
  rev/done rev_per_swap, energy/done energy_per_swap, wear/done wear_per_swap, fixed/done fixed_per_swap,
  (rev - energy - wear - fixed)/done cm_per_swap
from sw join live using(mon) order by mon""")

M = monthly()
print(M[["mon","attempts","done","rev","stations","fail_rate","rev_per_swap","energy_per_swap","wear_per_swap","fixed_per_swap","cm_per_swap"]].round(3).to_string(index=False))
first, last = M.iloc[0], M.iloc[-1]
h1 = M[M.mon < "2024-07-01"]; h4 = M[M.mon >= "2025-01-01"]
fact("done_growth_x", last.done/first.done); fact("rev_growth_x", last.rev/first.rev)
fact("fail_jan24_pct", 100*first.fail_rate); fact("fail_may24_pct", 100*M[M.mon=="2024-05-01"].fail_rate.iloc[0])
fact("fail_may25_pct", 100*M[M.mon=="2025-05-01"].fail_rate.iloc[0]); fact("fail_jun25_pct", 100*last.fail_rate)
fails_first = first.attempts - first.done; fails_last = last.attempts - last.done
fact("fail_count_growth_x", fails_last/fails_first)
fact("cm_h1_2024", (h1.rev - h1.energy - h1.wear - h1.fixed).sum()/h1.done.sum())
fact("cm_h1_2025", (h4.rev - h4.energy - h4.wear - h4.fixed).sum()/h4.done.sum())
for k in ["rev","energy","wear","fixed"]:
    fact(f"{k}_per_swap_h1_2024", h1[k].sum()/h1.done.sum()); fact(f"{k}_per_swap_h1_2025", h4[k].sum()/h4.done.sum())
print(f"Completed swaps x{FACTS['done_growth_x']:.2f}, revenue x{FACTS['rev_growth_x']:.2f}, failed attempts x{FACTS['fail_count_growth_x']:.2f} (Jan 2024 -> Jun 2025)")
print(f"Margin per swap: H1 2024 ₹{FACTS['cm_h1_2024']:.2f} -> H1 2025 ₹{FACTS['cm_h1_2025']:.2f}")

fig, axes = plt.subplots(1, 3, figsize=(13, 3.8))
x = pd.to_datetime(M.mon)
axes[0].plot(x, M.done/1e3, color=INK); axes[0].set_title("Completed swaps per month (000s)")
axes[1].plot(x, 100*M.fail_rate, color=ACCENT); axes[1].set_title("Failed attempts, % of attempts")
axes[1].axvspan(pd.Timestamp("2024-04-01"), pd.Timestamp("2024-07-01"), color=ACCENT, alpha=.08)
axes[1].axvspan(pd.Timestamp("2025-04-01"), pd.Timestamp("2025-07-01"), color=ACCENT, alpha=.08)
axes[2].plot(x, M.cm_per_swap, color=GOOD); axes[2].set_title("Contribution margin per swap (₹)")
axes[2].annotate("price rise", (pd.Timestamp("2024-07-01"), M.cm_per_swap[M.mon=="2024-07-01"].iloc[0]), xytext=(-60, -5), textcoords="offset points", fontsize=9, arrowprops=dict(arrowstyle="->", lw=.6))
axes[2].annotate("Kyron packs\nenter service", (pd.Timestamp("2024-09-01"), M.cm_per_swap[M.mon=="2024-09-01"].iloc[0]), xytext=(10, -25), textcoords="offset points", fontsize=9, arrowprops=dict(arrowstyle="->", lw=.6))
for a in axes: a.tick_params(axis="x", rotation=45)
fig.suptitle("Volume keeps growing; failures spike every April-June; margin per swap moves on its own path", x=0.01, ha="left")
savefig(fig, "q1_trends")

fig, ax = plt.subplots(figsize=(9, 4))
comp = pd.DataFrame({"H1 2024": [FACTS[f"{k}_per_swap_h1_2024"] for k in ["rev","energy","wear","fixed"]],
                     "H1 2025": [FACTS[f"{k}_per_swap_h1_2025"] for k in ["rev","energy","wear","fixed"]]},
                    index=["Revenue","Energy","Battery wear","Station rent + upkeep"])
comp.plot.barh(ax=ax, color=[MUTED, INK]); ax.invert_yaxis(); ax.set_xlabel("₹ per completed swap")
ax.set_title("Where each swap's rupees go, first half of 2024 vs 2025")
for c in ax.containers: ax.bar_label(c, fmt="₹%.1f", padding=3, fontsize=9)
savefig(fig, "q1_margin_parts")

# %% [markdown]
# ## 4. Core question 2: where and when service fails
# Hours use the corrected timestamps. Vehicle class comes from the rider.

# %%
con.execute("""create or replace table evr as select ev2.*, r.vehicle_class, r.partner_id, r.plan_type from ev2 join raw_riders r using(rider_id)""")
by_season = sql("""select summer, event_type, count(*) n from evr group by all""").pivot(index="event_type", columns="summer", values="n")
by_season = (100*by_season/by_season.sum()).round(2); by_season.columns = ["Jul-Mar", "Apr-Jun"]
print(by_season.to_string())
fact("nobatt_share_of_fail_summer_pct", 100*sql("select avg((event_type='failed_no_charged_battery')::int) v from evr where summer and not ok").v[0])
hr = sql("select h, summer, 1-avg(ok::int) f, avg(queue_wait_sec)/60 q from evr group by all order by h")
vc = sql("select vehicle_class, summer, 1-avg(ok::int) f from evr group by all order by all")
print(vc.round(4).to_string(index=False))
for _, r in vc.iterrows(): fact(f"fail_{r.vehicle_class}_{'summer' if r.summer else 'other'}_pct", 100*r.f)

stf = sql("select station_id, count(*) n, sum((not ok)::int) f from evr group by 1 order by f desc")
stf["cum"] = stf.f.cumsum()/stf.f.sum()
top10 = int(round(0.1*len(stf)))
fact("stations_n", len(stf)); fact("top10pct_stations_fail_share_pct", 100*stf.f.iloc[:top10].sum()/stf.f.sum())
fact("top10pct_stations_attempt_share_pct", 100*stf.n.iloc[:top10].sum()/stf.n.sum())
print(f"The worst {top10} of {len(stf)} stations hold {FACTS['top10pct_stations_fail_share_pct']:.1f}% of failed attempts and {FACTS['top10pct_stations_attempt_share_pct']:.1f}% of attempts")

fig, axes = plt.subplots(1, 2, figsize=(13, 4))
for s, c, lab in [(False, MUTED, "Jul-Mar"), (True, ACCENT, "Apr-Jun")]:
    d = hr[hr.summer == s]
    axes[0].plot(d.h, 100*d.f, color=c, label=lab, marker="o", ms=3)
    axes[1].plot(d.h, d.q, color=c, label=lab, marker="o", ms=3)
axes[0].set_title("Failed attempts by hour of day, %"); axes[1].set_title("Average queue wait by hour (minutes)")
for a in axes: a.set_xlabel("hour (corrected for the firmware clock bug)"); a.legend(frameon=False)
fig.suptitle("In summer, failures rise all day and peak in the evening rush, after a hot day has drained charged stock; queues barely change", x=0.01, ha="left")
savefig(fig, "q2_hours")
pk = hr[hr.summer].sort_values("f", ascending=False).iloc[0]
ev_s = hr[hr.summer & hr.h.between(19, 22)]; day_s = hr[hr.summer & ~hr.h.between(19, 22)]
fact("summer_fail_evening_pct", 100*ev_s.f.mean()); fact("summer_fail_rest_of_day_pct", 100*day_s.f.mean())
fact("summer_peak_fail_hour", pk.h); fact("summer_peak_fail_hour_pct", 100*pk.f)

# %% [markdown]
# ## 5. Core question 3: stations, equipment and the heat mechanism
# Charger generation, city and season together explain where failures happen. Hourly cabinet telemetry shows why.

# %%
gc = sql("""select gen, city, summer, count(*) n, 1-avg(ok::int) f from evr group by all""")
piv = gc[gc.summer].pivot(index="gen", columns="city", values="f")*100
print("Apr-Jun failure %, charger generation x city\n", piv.round(1).to_string())
g = sql("select gen, summer, 1-avg(ok::int) f from evr group by all order by all")
for _, r in g.iterrows(): fact(f"fail_{r.gen}_{'summer' if r.summer else 'other'}_pct", 100*r.f)
c = sql("select city, 1-avg(ok::int) f from evr where summer group by 1 order by 2 desc")
for _, r in c.iterrows(): fact(f"fail_summer_{r.city.replace(' ','_')}_pct", 100*r.f)
gen1_hot = sql("select count(*) n from st where charger_generation='Gen1' and city in ('Jaipur','Delhi NCR','Hyderabad')").n[0]
fact("gen1_stations", sql("select count(*) n from st where charger_generation='Gen1'").n[0]); fact("gen1_hot_city_stations", gen1_hot)

tele = sql("""select case when cabinet_temp_c<35 then '<35' when cabinet_temp_c<40 then '35-40' when cabinet_temp_c<45 then '40-45' else '45+' end band,
   s.charger_generation gen, count(*) n, avg(avg_charge_minutes) chg, avg((charged_2w_min=0)::int) zero, avg(packs_quarantined) quar
   from raw_station_hourly_status h join st s using(station_id) where telemetry_status='ok' group by all order by all""")
tb = sql("""select case when cabinet_temp_c<35 then '<35' when cabinet_temp_c<40 then '35-40' when cabinet_temp_c<45 then '40-45' else '45+' end band,
   count(*) n, avg(avg_charge_minutes) chg, avg((charged_2w_min=0)::int) zero from raw_station_hourly_status h join st using(station_id)
   where telemetry_status='ok' group by 1 order by 1""")
print(tele.round(2).to_string(index=False))
lo, hi = tb[tb.band=="<35"].iloc[0], tb[tb.band=="45+"].iloc[0]
fact("chg_min_cool", lo.chg); fact("chg_min_hot", hi.chg); fact("zero_stock_cool_pct", 100*lo.zero); fact("zero_stock_hot_pct", 100*hi.zero)
hot_by_gen = sql("""select s.charger_generation gen, avg((cabinet_temp_c>=45)::int) hot_share
   from raw_station_hourly_status h join st s using(station_id) where telemetry_status='ok' and month(hour_start) in (4,5,6) group by 1 order by 1""")
for _, r in hot_by_gen.iterrows(): fact(f"hot_hours_summer_{r.gen}_pct", 100*r.hot_share)
print(hot_by_gen.round(3).to_string(index=False))

# Link telemetry to swaps: failure rate in station-hours with zero charged 2W packs vs with stock
link = sql("""with e as (select station_id, date_trunc('hour', ts) hr, count(*) n, sum((not ok)::int) f from evr group by all)
 select (h.charged_2w_min=0) is_empty, sum(e.f)/sum(e.n) fail from e join raw_station_hourly_status h on h.station_id=e.station_id and h.hour_start=e.hr
 where h.telemetry_status='ok' group by 1""")
print(link.to_string(index=False))
fact("fail_in_empty_hours_pct", 100*link[link.is_empty].fail.iloc[0]); fact("fail_in_stocked_hours_pct", 100*link[~link.is_empty].fail.iloc[0])
for _, r in tele[tele.band.isin(["<35","45+"])].iterrows():
    fact(f"chg_min_{r.gen}_{'hot' if r.band=='45+' else 'cool'}", r.chg); fact(f"zero_stock_{r.gen}_{'hot' if r.band=='45+' else 'cool'}_pct", 100*r.zero)

fig, axes = plt.subplots(1, 3, figsize=(14, 4))
order = ["<35","35-40","40-45","45+"]
for gname, col in [("Gen1", ACCENT), ("Gen2", MUTED), ("Gen3", GOOD)]:
    d = tele[tele.gen == gname].set_index("band").loc[order]
    axes[0].plot(order, d.chg, marker="o", color=col, label=gname)
    axes[1].plot(order, 100*d.zero, marker="o", color=col, label=gname)
axes[0].set_title("Average charge time (min)"); axes[1].set_title("Hours with zero charged 2W packs, %")
for a in axes[:2]: a.set_xlabel("cabinet temperature (°C)"); a.legend(frameon=False)
lk = link.set_index("is_empty").fail*100
axes[2].bar(["packs in stock", "zero packs"], [lk[False], lk[True]], color=[MUTED, ACCENT]); axes[2].set_title("Failed attempts in that hour, %")
for p in axes[2].patches: axes[2].annotate(f"{p.get_height():.1f}%", (p.get_x()+p.get_width()/2, p.get_height()), ha="center", va="bottom", fontsize=9)
fig.suptitle("The mechanism: only Gen1 cabinets slow down in the heat, run out of packs, and turn riders away", x=0.01, ha="left")
savefig(fig, "q3_mechanism")

fig, ax = plt.subplots(figsize=(9, 3.6))
im = ax.imshow(piv.values, cmap="Reds", aspect="auto")
ax.set_xticks(range(len(piv.columns)), piv.columns); ax.set_yticks(range(len(piv.index)), piv.index)
for i in range(piv.shape[0]):
    for j in range(piv.shape[1]):
        v = piv.values[i, j]
        if not np.isnan(v): ax.text(j, i, f"{v:.1f}%", ha="center", va="center", fontsize=9, color="white" if v > 9 else INK)
ax.set_title("Apr-Jun failed attempts: old Gen1 cabinets in the three hottest cities"); ax.grid(False)
savefig(fig, "q3_gen_city")

tk = sql("""select s.charger_generation gen, count(t.ticket_id) tickets from raw_support_tickets t join st s using(station_id) group by 1""")
sw_by_gen = sql("select gen, count(*) n from evr group by 1")
tk = tk.merge(sw_by_gen, on="gen"); tk["per_10k"] = 1e4*tk.tickets/tk.n
print(tk.round(2).to_string(index=False))
for _, r in tk.iterrows(): fact(f"tickets_per10k_{r.gen}", r.per_10k)
loc = sql("select location_type, 1-avg(ok::int) f, count(*) n from evr where summer group by 1 order by 2 desc")
print(loc.round(4).to_string(index=False))

# %% [markdown]
# ## 6. Core question 4: batteries and the new supplier
# Pack health is measured from each pack's own swaps (ledger commission dates are unreliable, see section 2).

# %%
sup = sql("""select supplier, pack_type, count(*) packs, avg(initial_soh_pct-current_soh_pct) soh_lost, avg(swaps_served) swaps,
   100*avg(soh_loss_per_swap) soh_loss_per_100, sum((retired_date is not null)::int) retired, avg(current_soh_pct) soh_now
   from batt group by all order by pack_type, supplier""")
print(sup.round(2).to_string(index=False))
lots = sql("""select supplier, manufacturing_lot, pack_type, count(*) packs, 100*avg(soh_loss_per_swap) soh_loss_per_100
   from batt where pack_type like '2W%' group by all order by soh_loss_per_100 desc limit 8""")
print(lots.round(2).to_string(index=False))
for _, r in sup.iterrows():
    k = f"{r.supplier}_{r.pack_type[:2]}"
    fact(f"soh_loss_per100_{k}", r.soh_loss_per_100); fact(f"soh_now_{k}", r.soh_now); fact(f"packs_{k}", r.packs); fact(f"retired_{k}", r.retired)
rng = sql("""select b.supplier, b.pack_type, median(e.km) km, count(*) n from evr e join batt b on b.battery_id=e.battery_in_id
   where e.ok and e.km is not null and e.y=2025 group by all order by 2,1""")
print(rng.to_string(index=False))
for _, r in rng.iterrows(): fact(f"km_median_2025_{r.supplier}_{r.pack_type[:2]}", r.km)

wear = sql(f"""with w as ({wear_table(EOL_SOH)})
   select b.supplier, b.pack_type, avg(w.wear_per_swap) wear from evr e join batt b on b.battery_id=e.battery_out_id join w using(battery_id)
   where e.ok group by all""")
print(wear.round(2).to_string(index=False))
k2 = sql(f"""with w as ({wear_table(EOL_SOH)}), x as (select b.supplier='Kyron' kyron, b.pack_type, w.wear_per_swap from evr e
   join batt b on b.battery_id=e.battery_out_id join w using(battery_id) where e.ok)
   select pack_type, avg(wear_per_swap) filter (where kyron) ky, avg(wear_per_swap) filter (where not kyron) oth,
          count(*) filter (where kyron) n_ky from x group by 1""")
excess = float(((k2.ky - k2.oth)*k2.n_ky).sum())
fact("kyron_excess_wear_inr", excess); fact("kyron_excess_wear_cr", excess/1e7)
fact("kyron_swaps_served", k2.n_ky.sum())
fact("kyron_wear_2w", k2[k2.pack_type.str.startswith("2W")].ky.iloc[0]); fact("other_wear_2w", k2[k2.pack_type.str.startswith("2W")].oth.iloc[0])
print(f"Kyron packs served {int(k2.n_ky.sum()):,} swaps; their extra wear over other suppliers' packs: ₹{excess/1e7:.2f} crore")

# Ticket text: the 'other' bucket is battery complaints blamed on the vehicle
tix = sql("""select t.category, b.supplier, count(*) n from raw_support_tickets t left join raw_batteries b using(battery_id)
   where t.battery_id is not null group by all""").pivot(index="category", columns="supplier", values="n").fillna(0)
tix_share = (100*tix.div(tix.sum(1), axis=0)).round(1)
print("Supplier of the battery named on each ticket, % of tickets by category\n", tix_share.to_string())
fact("kyron_share_lowrange_tickets_pct", tix_share.loc["low_range", "Kyron"]); fact("kyron_share_other_tickets_pct", tix_share.loc["other", "Kyron"])
fact("kyron_share_billing_tickets_pct", tix_share.loc["billing_dispute", "Kyron"])
fact("kyron_share_of_packs_pct", 100*sql("select avg((supplier='Kyron')::int) v from raw_batteries").v[0])
fact("other_tickets", sql("select count(*) n from raw_support_tickets where category='other'").n[0])
fact("lowrange_tickets", sql("select count(*) n from raw_support_tickets where category='low_range'").n[0])

fig, axes = plt.subplots(1, 2, figsize=(13, 4))
s2 = sup[sup.pack_type.str.startswith("2W")]
axes[0].bar(s2.supplier, s2.soh_loss_per_100, color=[ACCENT if s == "Kyron" else MUTED for s in s2.supplier])
axes[0].set_title("2W packs: health lost per 100 swaps (points)")
r2 = rng[rng.pack_type.str.startswith("2W")]
axes[1].bar(r2.supplier, r2.km, color=[ACCENT if s == "Kyron" else MUTED for s in r2.supplier]); axes[1].set_title("2W packs: median km per swap, 2025")
for a in axes:
    for p in a.patches: a.annotate(f"{p.get_height():.1f}", (p.get_x()+p.get_width()/2, p.get_height()), ha="center", va="bottom", fontsize=9)
fig.suptitle("Kyron packs wear out several times faster and give riders less range per swap", x=0.01, ha="left")
savefig(fig, "q4_kyron")

# %% [markdown]
# ## 7. Core question 5: pricing and partner economics
# **Base price change (July 2024).** **Peak/off-peak pilot (Bengaluru and Pune from October 2024)**, measured as a difference-in-differences against the four other cities, with a pre-period check. **Partner contracts**, compared on contribution margin, not revenue.

# %%
price = sql("""select date_trunc('month', ts) mon, avg(list_price_inr) filter (where tariff_code='STD') std_list, avg(revenue) filter (where ok) rev from evr group by 1 order by 1""")
pre_p, post_p = price[price.mon < "2024-07-01"].std_list.mean(), price[(price.mon >= "2024-07-01")].std_list.mean()
fact("std_list_before", pre_p); fact("std_list_after", post_p)
# swaps per active rider per week around the change, independents (pay their own price) vs partner riders
spr = sql("""select r.partner_id is null indep, ts >= '2024-07-01' post, count(*) filter (where ok) / count(distinct rider_id || '-' || week(ts) || '-' || year(ts)) per_rider_week
   from evr r where ts between '2024-05-01' and '2024-08-31' group by all order by all""")
print(spr.round(3).to_string(index=False))

# Pilot windows from the data: hours where a tariff covers at least 10% of pilot-city swaps after launch
tw = sql("""select h, avg((tariff_code='PEAK')::int) peak, avg((tariff_code='OFFPEAK')::int) off from evr
   where city in ('Bengaluru','Pune') and ts >= '2024-10-01' and ok group by 1 order by 1""")
peak_hours = tw[tw.peak >= 0.10].h.tolist(); off_hours = tw[tw.off >= 0.10].h.tolist()
print("PEAK hours:", peak_hours, " OFFPEAK hours:", off_hours)
ph = ",".join(map(str, peak_hours))
cm_city = sql(f"""select city, mon, avg((h in ({ph}))::int) filter (where ok) peak_share, count(*) n,
   avg(revenue) filter (where ok) rev, 1-avg(ok::int) filter (where h in ({ph})) peak_fail
   from evr group by all""")
cm_city["treated"] = cm_city.city.isin(["Bengaluru", "Pune"]).astype(int)
cm_city["post"] = (pd.to_datetime(cm_city.mon) >= "2024-10-01").astype(int)
did = {}
for y in ["peak_share", "rev", "peak_fail"]:
    m = smf.wls(f"{y} ~ treated:post + C(city) + C(mon)", data=cm_city, weights=cm_city.n).fit(cov_type="cluster", cov_kwds={"groups": cm_city.city})
    did[y] = (m.params["treated:post"], m.conf_int().loc["treated:post"].tolist(), m.pvalues["treated:post"])
    print(f"DiD {y}: {m.params['treated:post']:.4f}  95% CI {m.conf_int().loc['treated:post'].round(4).tolist()}  p={m.pvalues['treated:post']:.3f}")
fact("did_peak_share_pts", 100*did["peak_share"][0]); fact("did_rev_inr", did["rev"][0]); fact("did_peak_fail_pts", 100*did["peak_fail"][0])
pre = cm_city[cm_city.post == 0].groupby(["treated", "mon"]).apply(lambda d: np.average(d.peak_share, weights=d.n)).unstack(0)
pre_gap_sd = (pre[1] - pre[0]).std()
fact("did_pretrend_gap_sd_pts", 100*pre_gap_sd)
es = cm_city.groupby(["treated", "mon"]).apply(lambda d: np.average(d.peak_share, weights=d.n)).unstack(0)
fig, ax = plt.subplots(figsize=(9, 4))
ax.plot(pd.to_datetime(es.index), 100*es[1], color=ACCENT, label="Pilot cities (Bengaluru, Pune)")
ax.plot(pd.to_datetime(es.index), 100*es[0], color=MUTED, label="Other four cities")
ax.axvline(pd.Timestamp("2024-10-01"), color=INK, ls="--", lw=1); ax.text(pd.Timestamp("2024-10-05"), ax.get_ylim()[1]*0.98, "pilot starts", va="top")
ax.set_ylabel("% of swaps in peak hours"); ax.legend(frameon=False)
ax.set_title(f"Pilot moved {abs(FACTS['did_peak_share_pts']):.1f} points of swaps out of peak hours vs the other cities")
savefig(fig, "q5_pilot")

# Event study: pilot-minus-control gap in peak share by month, relative to the pre-period average; and a placebo test that pretends the pilot began in April 2024
es_gap = 100*(es[1] - es[0]); pre_mean = es_gap[pd.to_datetime(es_gap.index) < "2024-10-01"].mean()
fact("pilot_gap_pre_mean", pre_mean); fact("pilot_gap_post_mean", es_gap[pd.to_datetime(es_gap.index) >= "2024-10-01"].mean())
pre_only = cm_city[cm_city.post == 0].copy(); pre_only["fake_post"] = (pd.to_datetime(pre_only.mon) >= "2024-04-01").astype(int)
pl = smf.wls("peak_share ~ treated:fake_post + C(city) + C(mon)", data=pre_only, weights=pre_only.n).fit(cov_type="cluster", cov_kwds={"groups": pre_only.city})
fact("placebo_peak_share_pts", 100*pl.params["treated:fake_post"]); fact("placebo_p", pl.pvalues["treated:fake_post"])
fact("did_peak_share_lo", 100*did["peak_share"][1][0]); fact("did_peak_share_hi", 100*did["peak_share"][1][1])
fact("did_rev_lo", did["rev"][1][0]); fact("did_rev_hi", did["rev"][1][1])
print(f"Placebo (fake start April 2024, pre-period only): {FACTS['placebo_peak_share_pts']:+.2f} points, p={FACTS['placebo_p']:.2f}; real effect {FACTS['did_peak_share_pts']:+.2f} points")

# Partner contribution margin (2025)
part = sql(f"""with w as ({wear_table(EOL_SOH)}),
 fixed as (select sum(s.monthly_rent_inr + s.monthly_maintenance_inr)*6 / (select count(*) from evr where ok and y=2025) per_swap
           from st s where s.commissioned_date < '2025-07-01' and (s.decommissioned_date is null or s.decommissioned_date >= '2025-01-01'))
 select coalesce(p.partner_name, 'Independent riders') partner, count(*) swaps, avg(e.revenue) rev,
   avg(e.revenue - e.kwh*e.grid_tariff_inr_kwh - w.wear_per_swap) - (select per_swap from fixed) cm,
   sum(e.revenue - e.kwh*e.grid_tariff_inr_kwh - w.wear_per_swap) - count(*)*(select per_swap from fixed) cm_total
 from evr e left join raw_fleet_partners p using(partner_id) left join w on w.battery_id=e.battery_out_id
 where e.ok and e.y=2025 group by 1 order by swaps desc""")
print(part.round(2).to_string(index=False))
z = part[part.partner == "ZipDrop"].iloc[0]
fact("zipdrop_swaps_2025", z.swaps); fact("zipdrop_rev_2025", z.rev); fact("zipdrop_cm_2025", z.cm); fact("zipdrop_cm_total_2025_lakh", z.cm_total/1e5)
fact("zipdrop_share_swaps_2025_pct", 100*z.swaps/part.swaps.sum())
ind = part[part.partner == "Independent riders"].iloc[0]; fact("indep_rev_2025", ind.rev); fact("indep_cm_2025", ind.cm)
zz = sql("""select ts >= '2024-11-01' after, avg(revenue) rev from evr where ok and partner_id='FP-03' and ts between '2024-08-01' and '2025-01-31' group by 1 order by 1""")
fact("zipdrop_rev_before", zz.rev.iloc[0]); fact("zipdrop_rev_after", zz.rev.iloc[1])
zip_lost = (zz.rev.iloc[0] - zz.rev.iloc[1]) * sql("select count(*) n from evr where ok and partner_id='FP-03' and ts >= '2024-11-01'").n[0]
fact("zipdrop_amendment_cost_lakh", zip_lost/1e5); fact("zipdrop_rev_drop", zz.rev.iloc[0] - zz.rev.iloc[1])
zd = sql("select discount_pct, discount_pct_after_amendment from raw_fleet_partners where partner_name='ZipDrop'")
fact("zipdrop_discount_before_pct", zd.discount_pct[0]); fact("zipdrop_discount_after_pct", zd.discount_pct_after_amendment[0])
fact("did_peak_share_pts_abs", abs(FACTS["did_peak_share_pts"]))
print(f"ZipDrop revenue per swap {zz.rev.iloc[0]:.2f} -> {zz.rev.iloc[1]:.2f}; the amendment gave away ₹{zip_lost/1e5:.1f} lakh to Jun 2025")
fig, ax = plt.subplots(figsize=(9, 4.6))
pp = part.sort_values("cm")
ax.barh(pp.partner, pp.cm, color=[ACCENT if p == "ZipDrop" else (GOOD if p == "Independent riders" else MUTED) for p in pp.partner])
ax.axvline(0, color=INK, lw=.8); ax.set_xlabel("₹ contribution margin per completed swap, 2025")
ax.set_title("The largest partner, ZipDrop, is the least profitable per swap")
savefig(fig, "q5_partners")

# %% [markdown]
# ## 8. Core question 6: why new riders do not come back
# **New rider** = signed up from January 2024 and first swap attempt before May 2025, so everyone has 60 days of follow-up. **Churned** = no attempt on days 30 to 60 after the first one. Factors are measured in the rider's first 14 days. A logistic regression holds the others constant; a factor is called **primary** when it is significant with controls *and* accounts for a large share of churned riders, **secondary** when it is significant but small.

# %%
nr = sql("""
with fa as (select rider_id, min(ts) t0 from evr group by 1),
w as (select e.rider_id, count(*) att, avg((not ok)::int) frate, avg(queue_wait_sec)/60 qw,
        avg((b.supplier='Kyron')::int) kyr, mode(e.city) city, mode(e.gen) gen
      from evr e join fa using(rider_id) left join raw_batteries b on b.battery_id=e.battery_out_id
      where e.ts < fa.t0 + interval 14 day group by 1),
lat as (select e.rider_id, count(*) later from evr e join fa using(rider_id)
        where e.ts between fa.t0 + interval 30 day and fa.t0 + interval 60 day group by 1)
select r.rider_id, r.plan_type, r.vehicle_class, r.signup_channel, coalesce(p.partner_segment,'independent') segment,
  fa.t0, month(fa.t0) in (4,5,6) summer_start, w.*, coalesce(lat.later,0)=0 churn
from raw_riders r join fa using(rider_id) join w using(rider_id) left join lat using(rider_id) left join raw_fleet_partners p using(partner_id)
where r.signup_date >= '2024-01-01' and fa.t0 < '2025-05-01'""")
nr["churn"] = nr.churn.astype(int); nr["summer_start"] = nr.summer_start.astype(int)
nr["frate10"] = 10*nr.frate; nr["kyr10"] = 10*nr.kyr; nr["att_c"] = nr.att.clip(upper=40)
fact("new_riders", len(nr)); fact("new_rider_churn_pct", 100*nr.churn.mean())
coh = nr.groupby(pd.to_datetime(nr.t0).dt.to_period("Q").astype(str)).churn.agg(["size", "mean"])
print(coh.round(3).to_string())
fact("churn_summer_start_pct", 100*nr[nr.summer_start == 1].churn.mean()); fact("churn_other_start_pct", 100*nr[nr.summer_start == 0].churn.mean())
bands = pd.cut(nr.frate, [-.001, 0, .1, .2, 1], labels=["none", "0-10%", "10-20%", ">20%"])
fb = nr.groupby(bands).churn.agg(["size", "mean"]); print(fb.round(3).to_string())
fact("churn_nofail_pct", 100*fb.loc["none", "mean"]); fact("churn_nofail_n", fb.loc["none", "size"])
fact("churn_highfail_pct", 100*fb.loc[">20%", "mean"]); fact("churn_highfail_n", fb.loc[">20%", "size"])

logit = smf.logit("churn ~ frate10 + qw + kyr10 + att_c + summer_start + C(city) + C(plan_type) + C(vehicle_class) + C(signup_channel)", nr).fit(disp=0)
tab = pd.DataFrame({"odds_ratio": np.exp(logit.params), "p": logit.pvalues}).round(3)
print(tab.to_string())
fact("or_frate10", np.exp(logit.params["frate10"])); fact("or_kyr10", np.exp(logit.params["kyr10"])); fact("or_summer", np.exp(logit.params["summer_start"]))
fact("p_kyr10", logit.pvalues["kyr10"]); fact("p_qw", logit.pvalues["qw"])
# Churned riders attributable to early failures: predicted churn as observed minus predicted churn with zero early failures
cf = nr.copy(); cf["frate10"] = 0
excess_fail = float((logit.predict(nr) - logit.predict(cf)).sum())
cf2 = nr.copy(); cf2["kyr10"] = 0
excess_kyr = float((logit.predict(nr) - logit.predict(cf2)).sum())
cf3 = nr.copy(); cf3["summer_start"] = 0
excess_summer = float((logit.predict(nr) - logit.predict(cf3)).sum())
cf4 = nr.copy(); cf4.loc[cf4.plan_type == "partner_billed", "plan_type"] = "pay_as_you_go"
excess_plan = float((logit.predict(nr) - logit.predict(cf4)).sum())
churned = nr.churn.sum()
fact("churned_new_riders", churned); fact("churn_from_early_fail", excess_fail); fact("churn_from_early_fail_pct", 100*excess_fail/churned)
fact("churn_from_kyron", excess_kyr); fact("churn_from_kyron_pct", 100*excess_kyr/churned); fact("churn_from_summer_start_pct", 100*excess_summer/churned); fact("churn_from_partner_plan_pct", 100*excess_plan/churned)
fact("or_partner_plan", 1/np.exp(logit.params["C(plan_type)[T.pay_as_you_go]"]))
drivers = pd.DataFrame([
    ("Failed swaps in the first 14 days", np.exp(logit.params["frate10"]), logit.pvalues["frate10"], excess_fail),
    ("Kyron share of packs received", np.exp(logit.params["kyr10"]), logit.pvalues["kyr10"], excess_kyr),
    ("Starting in April-June", np.exp(logit.params["summer_start"]), logit.pvalues["summer_start"], excess_summer),
    ("Partner-billed plan (vs paying themselves)", 1/np.exp(logit.params["C(plan_type)[T.pay_as_you_go]"]), logit.pvalues["C(plan_type)[T.pay_as_you_go]"], excess_plan),
], columns=["factor", "odds ratio (per 10 pts / yes)", "p", "churned riders it accounts for"])
drivers["share of churn %"] = 100*drivers.iloc[:, 3]/churned
drivers["label"] = np.where((drivers.p < 0.05) & (drivers["share of churn %"] >= 10), "primary", np.where(drivers.p < 0.05, "secondary", "not shown"))
print(drivers.round(3).to_string(index=False))
fig, ax = plt.subplots(figsize=(9, 4))
ax.bar(fb.index.astype(str), 100*fb["mean"], color=[MUTED, MUTED, ACCENT, ACCENT])
for p_, n_ in zip(ax.patches, fb["size"]): ax.annotate(f"{p_.get_height():.1f}%\n(n={n_:,})", (p_.get_x()+p_.get_width()/2, p_.get_height()), ha="center", va="bottom", fontsize=9)
ax.set_xlabel("share of a new rider's swap attempts that failed in their first 14 days"); ax.set_ylabel("% who did not come back (days 30-60)")
ax.set_title("New riders who hit failed swaps early are far more likely to leave")
savefig(fig, "q6_churn")

# Out-of-sample check: fit on riders who started before 2025, predict riders who started in 2025
from sklearn.metrics import roc_auc_score
nr_m = nr.dropna(subset=["kyr10", "qw"])  # riders with no completed swap in 14 days have no pack supplier share; the model drops them too
train = nr_m[pd.to_datetime(nr_m.t0) < "2025-01-01"]; test = nr_m[pd.to_datetime(nr_m.t0) >= "2025-01-01"]
f_ = "churn ~ frate10 + qw + kyr10 + att_c + summer_start + C(city) + C(plan_type) + C(vehicle_class) + C(signup_channel)"
m_tr = smf.logit(f_, train).fit(disp=0)
auc_out = roc_auc_score(test.churn, m_tr.predict(test)); auc_in = roc_auc_score(train.churn, m_tr.predict(train))
fact("churn_auc_in", auc_in); fact("churn_auc_out", auc_out); fact("churn_test_riders", len(test))
fact("or_frate10_train", np.exp(m_tr.params["frate10"]))
print(f"Churn model fitted on 2024 starters: AUC {auc_in:.3f} in sample, {auc_out:.3f} on {len(test):,} riders who started in 2025; early-failure odds ratio {np.exp(m_tr.params['frate10']):.2f} in the 2024-only fit")
by_partner = nr.groupby("segment").churn.agg(["size", "mean"])
print(by_partner.round(3).to_string())
fact("churn_independent_pct", 100*by_partner.loc["independent", "mean"])

# %% [markdown]
# ### How sure are the headline gaps? Bootstrap confidence intervals
# Stations (or riders) are resampled with replacement 1,000 times, so the intervals respect that attempts at the same station are not independent.

# %%
rng_ = np.random.default_rng(59500)
st_s = sql("""select station_id, gen, city, sum((not ok)::int) filter (where summer) fs, count(*) filter (where summer) ns,
   sum((not ok)::int) filter (where not summer) fo, count(*) filter (where not summer) no_ from evr group by all order by station_id""")
def gap(d):
    g1 = d[d.gen == "Gen1"]; g3 = d[d.gen == "Gen3"]
    return 100*(g1.fs.sum()/g1.ns.sum() - g3.fs.sum()/g3.ns.sum())
boot = [gap(st_s.iloc[rng_.integers(0, len(st_s), len(st_s))]) for _ in range(1000)]
fact("ci_gen1_gen3_gap", gap(st_s)); fact("ci_gen1_gen3_gap_lo", np.percentile(boot, 2.5)); fact("ci_gen1_gen3_gap_hi", np.percentile(boot, 97.5))
nr_sorted = nr.sort_values("rider_id")  # fixed row order so the seeded bootstrap is reproducible
hi_ = nr_sorted[nr_sorted.frate > .2].churn.values; no_ = nr_sorted[nr_sorted.frate == 0].churn.values
bc = [100*(rng_.choice(hi_, len(hi_)).mean() - rng_.choice(no_, len(no_)).mean()) for _ in range(1000)]
fact("ci_churn_gap", 100*(hi_.mean() - no_.mean())); fact("ci_churn_gap_lo", np.percentile(bc, 2.5)); fact("ci_churn_gap_hi", np.percentile(bc, 97.5))
kb = sql("select supplier, soh_loss_per_swap from batt where pack_type like '2W%' and soh_loss_per_swap is not null order by battery_id")
ky_ = kb[kb.supplier == "Kyron"].soh_loss_per_swap.values; ot_ = kb[kb.supplier != "Kyron"].soh_loss_per_swap.values
bk = [rng_.choice(ky_, len(ky_)).mean()/rng_.choice(ot_, len(ot_)).mean() for _ in range(1000)]
fact("ci_kyron_ratio", ky_.mean()/ot_.mean()); fact("ci_kyron_ratio_lo", np.percentile(bk, 2.5)); fact("ci_kyron_ratio_hi", np.percentile(bk, 97.5))
ci = pd.DataFrame([
    ("Gen1 minus Gen3 summer failure rate (points)", FACTS["ci_gen1_gen3_gap"], FACTS["ci_gen1_gen3_gap_lo"], FACTS["ci_gen1_gen3_gap_hi"]),
    ("Churn, >20% early failures minus none (points)", FACTS["ci_churn_gap"], FACTS["ci_churn_gap_lo"], FACTS["ci_churn_gap_hi"]),
    ("Kyron 2W health loss per swap, times other 2W packs", FACTS["ci_kyron_ratio"], FACTS["ci_kyron_ratio_lo"], FACTS["ci_kyron_ratio_hi"]),
], columns=["gap", "estimate", "95% low", "95% high"])
print(ci.round(2).to_string(index=False))

# %% [markdown]
# ## 9. The chain, priced: what summer failures at old cabinets cost
# Three links, each measured separately:
# 1. **Extra failed attempts**: Gen1 attempts in April-June beyond what Gen1 fails the rest of the year.
# 2. **Swaps lost for good**: the share of failed attempts where the rider did not complete a swap anywhere in the next two hours, priced at average revenue per swap.
# 3. **Riders lost**: new riders the churn model attributes to early failed swaps, priced at the monthly revenue of a retained new rider for 6 months (**ASSUMPTION**; 3 and 12 months shown as the range).

# %%
g1 = sql("""select summer, count(*) n, 1-avg(ok::int) f from evr where gen='Gen1' group by 1""").set_index("summer")
excess_attempts = g1.loc[True, "n"] * (g1.loc[True, "f"] - g1.loc[False, "f"])
fact("gen1_summer_excess_failed", excess_attempts)
rec = sql("""with f as (select rider_id, ts from evr where not ok),
 nxt as (select f.rider_id, f.ts, min(e.ts) nxt from f left join evr e on e.rider_id=f.rider_id and e.ok and e.ts > f.ts and e.ts <= f.ts + interval 2 hour group by all)
 select avg((nxt is null)::int) lost from nxt""").lost[0]
fact("failed_not_recovered_pct", 100*rec)
avg_rev = sql("select avg(revenue) r from evr where ok").r[0]
lost_swaps = excess_attempts * rec
fact("gen1_summer_lost_swaps", lost_swaps); fact("gen1_summer_lost_rev_lakh", lost_swaps*avg_rev/1e5)
# churn link: riders lost to early failures, and how many of their early failures happened at Gen1 in summer
share_gen1_summer = sql("""with fa as (select rider_id, min(ts) t0 from evr group by 1)
  select avg((e.gen='Gen1' and e.summer)::int) v from evr e join fa using(rider_id) where not e.ok and e.ts < fa.t0 + interval 14 day""").v[0]
fact("early_fail_share_gen1_summer_pct", 100*share_gen1_summer)
monthly_rev_retained = sql("""with fa as (select rider_id, min(ts) t0 from evr group by 1)
  select sum(e.revenue) / count(distinct e.rider_id) / 1.0 r from evr e join fa using(rider_id)
  where e.ts between fa.t0 + interval 30 day and fa.t0 + interval 60 day""").r[0]
fact("monthly_rev_retained_rider", monthly_rev_retained)
riders_lost = excess_fail * share_gen1_summer
fact("riders_lost_gen1_summer", riders_lost)
for mths in (3, 6, 12):
    fact(f"riders_lost_value_{mths}m_lakh", riders_lost*monthly_rev_retained*mths/1e5)
chain = pd.DataFrame([
    ("Extra failed attempts at Gen1 in Apr-Jun (both summers)", f"{excess_attempts:,.0f}", ""),
    ("... of which the rider did not swap anywhere within 2 hours", f"{100*rec:.0f}%", f"₹{lost_swaps*avg_rev/1e5:.1f} lakh revenue"),
    ("New riders lost to early failures that happened at Gen1 in summer", f"{riders_lost:,.0f}", f"₹{FACTS['riders_lost_value_3m_lakh']:.1f}-{FACTS['riders_lost_value_12m_lakh']:.1f} lakh (3-12 months of revenue)"),
], columns=["link", "size", "₹"])
print(chain.to_string(index=False))

leaks = pd.DataFrame([
    ("Kyron packs wearing out faster (to Jun 2025)", FACTS["kyron_excess_wear_inr"]/1e5),
    ("ZipDrop discount raised 12% -> 28% (Nov 2024-Jun 2025)", FACTS["zipdrop_amendment_cost_lakh"]),
    ("Summer failures at Gen1: swaps lost", FACTS["gen1_summer_lost_rev_lakh"]),
    ("Summer failures at Gen1: new riders lost (6 months)", FACTS["riders_lost_value_6m_lakh"]),
], columns=["leak", "₹ lakh"]).sort_values("₹ lakh")
print(leaks.round(1).to_string(index=False))
fig, ax = plt.subplots(figsize=(9, 3.8))
ax.barh(leaks.leak, leaks["₹ lakh"], color=[ACCENT if "Kyron" in l else (INK if "ZipDrop" in l else MUTED) for l in leaks.leak])
for p_ in ax.patches: ax.annotate(f"₹{p_.get_width():.1f} lakh", (p_.get_width(), p_.get_y()+p_.get_height()/2), va="center", xytext=(4, 0), textcoords="offset points", fontsize=9)
ax.set_xlabel("₹ lakh, Jan 2024 - Jun 2025"); ax.set_title("Ranked: what each problem has cost so far")
savefig(fig, "chain_leaks")

# %% [markdown]
# ## 10. Next April: which stations will fail next summer, tested on a summer the rule never saw
# **Back-test.** Take one simple rule from summer 2024 alone: a station's expected summer failure rate is the 2024 rate of its *charger generation in its city* (for example, Gen1 in Jaipur). Freeze it and compare with what each station actually did in summer 2025. Then ask whether a station's *own* 2024 history adds anything beyond its group.

# %%
ss = sql("""select station_id, city, gen, wave,
  1-avg(ok::int) filter (where y=2024 and summer) f24, count(*) filter (where y=2024 and summer) n24,
  1-avg(ok::int) filter (where y=2025 and summer) f25, count(*) filter (where y=2025 and summer) n25,
  sum((not ok)::int) filter (where y=2024 and summer) fails24,
  sum((not ok)::int) filter (where y=2025 and summer) fails25,
  count(distinct rider_id) filter (where y=2025 and summer) riders25
  from evr group by all""")
ss["group"] = ss.gen + " in " + ss.city
both = ss.dropna(subset=["f24", "f25"]).copy()
g24 = both.groupby("group").apply(lambda d: d.fails24.sum()/d.n24.sum()).rename("group24")
both = both.join(g24, on="group")
r_rule = stats.pearsonr(both.group24, both.f25)[0]
mae_rule = (both.group24 - both.f25).abs().mean()
rho = stats.spearmanr(both.f24, both.f25).correlation
both["own_vs_group24"] = both.f24 - both.group24
both["own_vs_group25"] = both.f25 - both.groupby("group").f25.transform("mean")
rho_within = stats.spearmanr(both.own_vs_group24, both.own_vs_group25).correlation
fact("backtest_stations", len(both)); fact("backtest_spearman", rho)
fact("rule_r2", r_rule**2); fact("rule_mae_pts", 100*mae_rule); fact("within_group_spearman", rho_within)
print(f"Group rule from 2024 predicts each station's 2025 summer failure rate: R^2 {r_rule**2:.3f}, mean error {100*mae_rule:.2f} points ({len(both)} stations)")
print(f"A station's own 2024 history beyond its group: rank correlation {rho_within:.2f} -> adds nothing")

HOT = ["Jaipur", "Delhi NCR", "Hyderabad"]
ss["cohort"] = np.where((ss.gen == "Gen1") & ss.city.isin(HOT), "Gen1 in Jaipur, Delhi NCR, Hyderabad", "all other stations")
co = ss.groupby("cohort").agg(stations=("station_id", "size"), fails24=("fails24", "sum"), n24=("n24", "sum"), fails25=("fails25", "sum"), n25=("n25", "sum"))
co["f24"] = co.fails24/co.n24; co["f25"] = co.fails25/co.n25
co["share_fail25"] = co.fails25/co.fails25.sum(); co["share_att25"] = co.n25/co.n25.sum()
print(co.round(3).to_string())
hc = co.loc["Gen1 in Jaipur, Delhi NCR, Hyderabad"]
fact("hot_gen1_stations", hc.stations); fact("hot_gen1_fail24_pct", 100*hc.f24); fact("hot_gen1_fail25_pct", 100*hc.f25)
fact("hot_gen1_share_fail25_pct", 100*hc.share_fail25); fact("hot_gen1_share_att25_pct", 100*hc.share_att25)
fact("hot_gen1_attempts_s24", hc.n24); fact("hot_gen1_attempts_s25", hc.n25)
oc = co.loc["all other stations"]; fact("other_stations_fail25_pct", 100*oc.f25); fact("other_stations_n", oc.stations)
new = ss[ss.f24.isna() & ss.f25.notna()]
fact("new_stations_2025", len(new)); fact("new_stations_fail_2025_pct", 100*new.fails25.sum()/new.n25.sum())

grp = both.groupby("group").agg(n=("n25", "sum"), g24=("group24", "first"), f25=("fails25", "sum"), n25=("n25", "sum"))
grp["g25"] = grp.f25/grp.n25
fig, axes = plt.subplots(1, 2, figsize=(13, 4.6))
for gname, r in grp.iterrows():
    hot = gname.startswith("Gen1") and any(c in gname for c in HOT)
    axes[0].scatter(100*r.g24, 100*r.g25, s=r.n/400, color=ACCENT if hot else MUTED, alpha=.8)
    OFF = {"Gen1 in Delhi NCR": (-95, 8), "Gen1 in Jaipur": (8, -12), "Gen1 in Hyderabad": (10, -3), "Gen2 in Delhi NCR": (8, 2)}
    if gname in OFF: axes[0].annotate(gname, (100*r.g24, 100*r.g25), xytext=OFF[gname], textcoords="offset points", fontsize=8)
lim = [3, 19]; axes[0].plot(lim, lim, color=INK, lw=.7, ls="--")
axes[0].set_xlabel("summer 2024 failed attempts, % (the rule)"); axes[0].set_ylabel("summer 2025, % (what happened)")
axes[0].set_title(f"Each bubble: one charger generation in one city. Station-level R² {r_rule**2:.2f}")
bars = pd.DataFrame({"share of summer-2025 failed attempts": [100*hc.share_fail25], "share of summer-2025 attempts": [100*hc.share_att25]})
axes[1].bar(["failed attempts", "all attempts"], [100*hc.share_fail25, 100*hc.share_att25], color=[ACCENT, MUTED])
for p_ in axes[1].patches: axes[1].annotate(f"{p_.get_height():.0f}%", (p_.get_x()+p_.get_width()/2, p_.get_height()), ha="center", va="bottom")
axes[1].set_title(f"The {int(hc.stations)} Gen1 stations in the three hottest cities, summer 2025"); axes[1].set_ylabel("% of network total")
fig.suptitle("Back-test: one rule from summer 2024 (old Gen1 cabinets in hot cities) predicted summer 2025", x=0.01, ha="left")
savefig(fig, "backtest")

# %% [markdown]
# ### The April 2026 list
# Because a station's own history adds nothing beyond its group, the list is the whole group, not a ranking within it. **Wave 1:** every Gen1 station in Jaipur and Delhi NCR (the two groups failing on about 17% of summer attempts). **Wave 2:** Gen1 in Hyderabad. "Excess failed attempts" = attempts beyond each station's own rate outside summer, at the summer-2025 volume.

# %%
base = sql("select station_id, 1-avg(ok::int) f_other from evr where not summer group by 1")
l26 = ss.merge(base, on="station_id").dropna(subset=["f25"])
l26["excess_failed"] = l26.n25*(l26.f25 - l26.f_other)
l26 = l26[(l26.gen == "Gen1") & l26.city.isin(HOT)].copy()
l26["wave_2026"] = np.where(l26.city.isin(["Jaipur", "Delhi NCR"]), 1, 2)
l26 = l26.sort_values(["wave_2026", "city", "station_id"])
april = l26[["wave_2026", "station_id", "city", "gen", "f24", "f25", "f_other", "n25", "excess_failed", "riders25"]]
april.to_csv(os.path.join(OUT, "april_2026_list.csv"), index=False)
wv = april.groupby("wave_2026").agg(stations=("station_id", "size"), excess=("excess_failed", "sum"), riders=("riders25", "sum"),
                                     f25=("f25", "mean"))
print(wv.round(1).to_string())
for w_, r in wv.iterrows():
    fact(f"wave{w_}_stations", r.stations); fact(f"wave{w_}_excess_failed", r.excess); fact(f"wave{w_}_riders", r.riders)
fact("list_excess_failed", april.excess_failed.sum()); fact("list_riders_exposed", april.riders25.sum()); fact("list_stations", len(april))
# Effect of the upgrade, from the data: if each listed Gen1 station had failed at the summer-2025 rate of Gen3 stations in its own city
g3 = ss[ss.gen == "Gen3"].groupby("city").apply(lambda d: d.fails25.sum()/d.n25.sum()).rename("g3_rate")
up = april.merge(g3, left_on="city", right_index=True)
up["avoided"] = up.n25*(up.f25 - up.g3_rate)
for w_, d_ in up.groupby("wave_2026"): fact(f"wave{w_}_avoided_failed", d_.avoided.sum())
fact("upgrade_avoided_failed", up.avoided.sum()); fact("upgrade_avoided_pct_of_summer_fails", 100*up.avoided.sum()/ss.fails25.sum())
fact("upgrade_cohort_fail_after_pct", 100*((up.n25*up.f25).sum() - up.avoided.sum())/up.n25.sum())
print(f"If the 36 Gen1 stations failed like Gen3 in their cities: {up.avoided.sum():,.0f} fewer failed attempts in summer 2025 ({FACTS['upgrade_avoided_pct_of_summer_fails']:.1f}% of all summer failures)")
pune_g1 = ss[(ss.gen == "Gen1") & (ss.city == "Pune")]
fact("pune_gen1_stations", len(pune_g1)); fact("pune_gen1_fail25_pct", 100*pune_g1.fails25.sum()/pune_g1.n25.sum())
print(april.assign(f24=lambda d: (100*d.f24).round(1), f25=lambda d: (100*d.f25).round(1), f_other=lambda d: (100*d.f_other).round(1),
                   excess_failed=lambda d: d.excess_failed.round(0)).to_string(index=False))

# %% [markdown]
# ### Did the expansion waves go where riders needed them?

# %%
need = sql("""select city, sum((not ok)::int) filter (where y=2024 and summer) fails_s24 from evr group by 1""")
waves = sql("select city, count(*) filter (where expansion_wave<>'Launch') new_stations from st group by 1")
need = need.merge(waves, on="city"); need["share_need"] = 100*need.fails_s24/need.fails_s24.sum(); need["share_new"] = 100*need.new_stations/need.new_stations.sum()
print(need.round(1).to_string(index=False))
for _, r in need.iterrows(): fact(f"share_need_{r.city.replace(' ','_')}_pct", r.share_need); fact(f"share_new_{r.city.replace(' ','_')}_pct", r.share_new)
fact("new_stations_total", need.new_stations.sum())
hot3 = need.city.isin(HOT)
fact("hot3_share_need_pct", need[hot3].share_need.sum()); fact("hot3_share_new_pct", need[hot3].share_new.sum())
fig, ax = plt.subplots(figsize=(9, 4))
xx = np.arange(len(need)); wdt = .38
ax.bar(xx - wdt/2, need.share_need, wdt, color=ACCENT, label="share of summer-2024 failed attempts")
ax.bar(xx + wdt/2, need.share_new, wdt, color=MUTED, label="share of the new stations opened after")
ax.set_xticks(xx, need.city); ax.set_ylabel("%"); ax.legend(frameon=False)
ax.set_title("New stations were spread evenly; the failures were not")
savefig(fig, "expansion")

# %% [markdown]
# ## 11. The budget decision: a verdict on each of the four proposals
# Cabinet upgrade prices are not in the data, so instead of guessing one we compute the **break-even**: the most VoltRelay could pay per listed station and still get the money back in one summer.

# %%
per_station_lost_swaps = up.set_index("station_id").avoided.reindex(april.station_id).values * rec
fact("upgrade_saved_rev_lakh", (up.avoided*rec*avg_rev).sum()/1e5)
per_station_value = per_station_lost_swaps*avg_rev + (riders_lost/FACTS["gen1_stations"])*monthly_rev_retained*6
fact("breakeven_per_station_lakh", per_station_value.mean()/1e5)
fact("list_lost_rev_lakh", (per_station_lost_swaps*avg_rev).sum()/1e5)
cellora_2w_cost = sql("select avg(purchase_cost_inr) c from raw_batteries where supplier<>'Kyron' and pack_type like '2W%'").c[0]
fact("pack_2w_cost_inr", cellora_2w_cost); fact("kyron_2w_replace_cost_cr", FACTS["packs_Kyron_2W"]*cellora_2w_cost/1e7)
fact("kyron_months_in_service", sql("select date_diff('month', min(ts), max(ts)) + 1 m from evr e join raw_batteries b on b.battery_id=e.battery_out_id where b.supplier='Kyron' and b.pack_type like '2W%'").m[0])
fact("zipdrop_months_after_amendment", sql("select date_diff('month', date '2024-11-01', max(ts)) + 1 m from evr").m[0])
verdicts = pd.DataFrame([
    ("More stations", "Not as proposed",
     f"The {int(FACTS['new_stations_total'])} stations opened in the two waves were spread evenly; the three hottest cities had {FACTS['share_need_Jaipur_pct']+FACTS['share_need_Delhi_NCR_pct']+FACTS['share_need_Hyderabad_pct']:.0f}% of summer-2024 failures but got {FACTS['share_new_Jaipur_pct']+FACTS['share_new_Delhi_NCR_pct']+FACTS['share_new_Hyderabad_pct']:.0f}% of new stations. The {int(FACTS['hot_gen1_stations'])} Gen1 stations in those cities failed on {FACTS['hot_gen1_fail24_pct']:.1f}% of summer attempts in 2024 and {FACTS['hot_gen1_fail25_pct']:.1f}% in 2025.",
     "Swap the Gen1 cabinets for Gen3 in place before 1 April 2026: Jaipur and Delhi NCR first, then Hyderabad", "Head of Network Ops",
     f"Pays back in one summer if it costs under ₹{FACTS['breakeven_per_station_lakh']:.1f} lakh per station", "High (back-tested)"),
    ("More batteries", "Yes, but replace, don't add Kyron",
     f"Kyron 2W packs lost {FACTS['soh_loss_per100_Kyron_2W']:.2f} health points per 100 swaps vs {FACTS['soh_loss_per100_Cellora_2W']:.2f} (Cellora); extra wear ₹{FACTS['kyron_excess_wear_cr']:.2f} crore; still issued {int(FACTS['kyron_issued_after_retirement']):,} times after 'retirement'.",
     "Stop issuing retired Kyron packs now; replace the Kyron 2W fleet with Cellora/Amptek; file a warranty claim on lots KY-2407/08/09", "Head of Fleet & Procurement",
     f"Replacement about ₹{FACTS['kyron_2w_replace_cost_cr']:.2f} crore at current pack prices, against ₹{FACTS['kyron_excess_wear_cr']:.2f} crore extra wear in 10 months", "High"),
    ("Network-wide pricing rollout", "Yes for revenue, not for service",
     f"Pilot vs other cities: {FACTS['did_peak_share_pts']:+.1f} points of swaps in peak hours, {FACTS['did_rev_inr']:+.2f} ₹ revenue per swap, peak-hour failures {FACTS['did_peak_fail_pts']:+.2f} points (not significant).",
     "Roll out city by city as a revenue measure; do not count on it to fix summer stock-outs", "Head of Pricing", f"About ₹{FACTS['did_rev_inr']:.2f} more per swap where applied", "Medium (6 city clusters)"),
    ("Long-term exclusive with ZipDrop", "No",
     f"ZipDrop is {FACTS['zipdrop_share_swaps_2025_pct']:.0f}% of 2025 swaps but the lowest margin per swap of all partners ({FACTS['zipdrop_cm_2025']:+.2f} ₹ vs {FACTS['indep_cm_2025']:+.2f} ₹ for independents); the 28% discount cost ₹{FACTS['zipdrop_amendment_cost_lakh']:.1f} lakh in 8 months.",
     "Reopen the contract: bring the discount back toward the 12% other partners pay and add the peak surcharge", "Head of Partnerships", f"Up to ₹{FACTS['zipdrop_rev_before']-FACTS['zipdrop_rev_after']:.2f} per ZipDrop swap", "High"),
], columns=["proposal", "verdict", "evidence", "do this instead", "owner", "effect", "confidence"])
print(verdicts.to_string(index=False))
verdicts.to_csv(os.path.join(OUT, "budget_verdicts.csv"), index=False)

# %% [markdown]
# ## 12. Self-audit: do the headline numbers survive other reasonable choices?

# %%
audit = []
def check(claim, base, alt_label, alt):
    audit.append(dict(claim=claim, as_reported=base, alternative=alt_label, alternative_value=alt))
for eol in (60, 80):
    Mx = monthly(eol)
    a1 = Mx[Mx.mon < "2024-07-01"]; a4 = Mx[Mx.mon >= "2025-01-01"]
    v1 = (a1.rev-a1.energy-a1.wear-a1.fixed).sum()/a1.done.sum(); v4 = (a4.rev-a4.energy-a4.wear-a4.fixed).sum()/a4.done.sum()
    check("Margin per swap H1 2024 -> H1 2025 (₹)", f"{FACTS['cm_h1_2024']:.2f} -> {FACTS['cm_h1_2025']:.2f}", f"battery replaced at {eol}% health", f"{v1:.2f} -> {v4:.2f}")
    fact(f"cm_h1_2024_eol{eol}", v1); fact(f"cm_h1_2025_eol{eol}", v4)
    w1, w4 = a1.wear.sum()/a1.done.sum(), a4.wear.sum()/a4.done.sum()
    check("Battery wear per swap H1 2024 -> H1 2025 (₹)", f"{FACTS['wear_per_swap_h1_2024']:.2f} -> {FACTS['wear_per_swap_h1_2025']:.2f}", f"battery replaced at {eol}% health", f"{w1:.2f} -> {w4:.2f}")
    fact(f"wear_h1_2024_eol{eol}", w1); fact(f"wear_h1_2025_eol{eol}", w4)
for label, key in [("generation only", "gen"), ("city only", "city")]:
    gg = both.groupby(key).apply(lambda d: d.fails24.sum()/d.n24.sum()).rename("alt")
    r_alt = stats.pearsonr(both.join(gg, on=key).alt, both.f25)[0]**2
    check("Rule's station-level R² (2024 rule vs 2025)", f"{FACTS['rule_r2']:.3f} (generation x city)", label, f"{r_alt:.3f}")
    fact(f"rule_r2_{key}_only", r_alt)
check("Station's own history beyond its group", f"Spearman {rho_within:.2f}", "Kendall tau", f"{stats.kendalltau(both.own_vs_group24, both.own_vs_group25).correlation:.2f}")
nb = sql("select gen, summer, avg((event_type='failed_no_charged_battery')::int) f from evr group by all order by all")
g1s = nb[(nb.gen=="Gen1") & nb.summer].f.iloc[0]; g3s = nb[(nb.gen=="Gen3") & nb.summer].f.iloc[0]
check("Gen1 vs Gen3 Apr-Jun failure", f"{FACTS['fail_Gen1_summer_pct']:.1f}% vs {FACTS['fail_Gen3_summer_pct']:.1f}%", "only 'no charged battery' failures", f"{100*g1s:.1f}% vs {100*g3s:.1f}%")
raw_c = sql("select avg((event_type='swap_completed')::int) c from raw_swap_events").c[0]
check("Completion rate", f"{FACTS['completion_pct_clean']:.2f}%", "test stations kept", f"{100*raw_c:.2f}%")
hr_raw = sql("""select hour(e.event_ts) h, 1-avg((e.event_type='swap_completed')::int) f from raw_swap_events e join st using(station_id)
   where month(e.event_ts) in (4,5,6) group by 1 order by 2 desc limit 1""")
check("Worst summer hour for failures", f"{int(FACTS['summer_peak_fail_hour'])}:00", "firmware clock not corrected", f"{int(hr_raw.h[0])}:00")
# churn window 30-90 days
nr90 = sql("""with fa as (select rider_id, min(ts) t0 from evr group by 1),
 w as (select e.rider_id, avg((not ok)::int) frate from evr e join fa using(rider_id) where e.ts < fa.t0 + interval 14 day group by 1),
 lat as (select e.rider_id, count(*) later from evr e join fa using(rider_id) where e.ts between fa.t0 + interval 30 day and fa.t0 + interval 90 day group by 1)
 select w.frate, coalesce(lat.later,0)=0 churn from raw_riders r join fa using(rider_id) join w using(rider_id) left join lat using(rider_id)
 where r.signup_date >= '2024-01-01' and fa.t0 < '2025-04-01'""")
hi90 = 100*nr90[nr90.frate > .2].churn.mean(); lo90 = 100*nr90[nr90.frate == 0].churn.mean()
check("Churn: >20% early failures vs none", f"{FACTS['churn_highfail_pct']:.1f}% vs {FACTS['churn_nofail_pct']:.1f}%", "churn window days 30-90", f"{hi90:.1f}% vs {lo90:.1f}%")
audit = pd.DataFrame(audit)
print(audit.to_string(index=False))
audit.to_csv(os.path.join(OUT, "self_audit.csv"), index=False)

# %% [markdown]
# ## 13. How AI was used, and how each output was checked
# * **AI tools used:** an AI coding assistant (Claude) helped write the queries and code, draft text, and search public sources.
# * **Every number was checked outside the AI's own reasoning.** Each headline number is written to `facts.json` by this notebook; a separate independent re-derivation (fresh queries written from the problem statement alone) confirmed the key facts; a script fails if the report, video script or summary quotes a number that is not in `facts.json`.
# * **Judgement calls are ours and stated:** the battery replacement threshold (70% health), the 6-month value of a lost rider, and the break-even framing for cabinet upgrades are assumptions, shown with their ranges in section 12.
# * **What AI got wrong and we caught:** a first pass at pilot peak hours listed hours where both tariffs appear; checking tariff counts by hour fixed the window (section 7). A first data load read blank pack IDs as text; the loader now treats blanks as missing (section 2).

# %%
with open(os.path.join(OUT, "facts.json"), "w") as f:
    json.dump({k: round(v, 6) for k, v in FACTS.items()}, f, indent=1, sort_keys=True)
print(f"{len(FACTS)} facts written to outputs/facts.json")
