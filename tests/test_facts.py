"""Independent re-derivations of the headline numbers.

Each test queries the organiser's data directly (not the notebook's tables) and
compares with outputs/facts.json, which the notebook writes. If the notebook's
logic drifts, these fail.
"""
import json, os
import duckdb, pytest
from scipy import stats

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PQ = os.path.join(ROOT, "data", "pq")
F = json.load(open(os.path.join(ROOT, "outputs", "facts.json")))

@pytest.fixture(scope="module")
def con():
    c = duckdb.connect()
    for t in ["swap_events", "stations", "riders", "batteries", "station_hourly_status", "fleet_partners", "city_daily_context"]:
        c.execute(f"create view {t} as select * from '{PQ}/{t}.parquet'")
    # independent firmware fix + test-station exclusion
    c.execute("""create view e as select x.*, s.city, s.charger_generation gen,
      case when station_firmware='v3.2.0' and event_ts >= '2025-03-10' and event_ts < '2025-04-15' then event_ts + interval 330 minute else event_ts end t
      from swap_events x join stations s using(station_id) where station_id not like 'STN-TST%'""")
    return c

def q(c, s):
    return c.execute(s).fetchone()

def test_row_counts(con):
    assert q(con, "select count(*) from swap_events")[0] == 3877013 == F["attempts_all"]
    assert q(con, "select count(*) from e")[0] == F["attempts_clean"]

def test_test_station_rows_and_money(con):
    n, amt = q(con, "select count(*), sum(amount_charged_inr) from swap_events where station_id like 'STN-TST%'")
    assert n == F["test_rows"] and abs(amt - F["test_amount_inr"]) < 1

def test_firmware_rows(con):
    n = q(con, "select count(*) from swap_events where station_firmware='v3.2.0' and event_ts >= '2025-03-10' and event_ts < '2025-04-15'")[0]
    assert n == F["firmware_rows"]

def test_gen_summer_failure(con):
    for gen in ("Gen1", "Gen2", "Gen3"):
        v = q(con, f"select 100*(1-avg((event_type='swap_completed')::int)) from e where gen='{gen}' and month(t) in (4,5,6)")[0]
        assert abs(v - F[f"fail_{gen}_summer_pct"]) < 0.05

def test_backtest_group_rule(con):
    rows = con.execute("""select station_id, gen || ' ' || city g,
        sum((event_type<>'swap_completed')::int) filter (where year(t)=2024 and month(t) in (4,5,6)) f24,
        count(*) filter (where year(t)=2024 and month(t) in (4,5,6)) n24,
        1-avg((event_type='swap_completed')::int) filter (where year(t)=2025 and month(t) in (4,5,6)) r25
        from e group by all""").fetchall()
    both = [r for r in rows if r[3] and r[4] is not None]
    grp = {}
    for _, g, f, n, _r in both:
        a = grp.setdefault(g, [0, 0]); a[0] += f; a[1] += n
    pred = [grp[r[1]][0]/grp[r[1]][1] for r in both]
    r2 = stats.pearsonr(pred, [r[4] for r in both])[0]**2
    assert len(both) == F["backtest_stations"] and abs(r2 - F["rule_r2"]) < 1e-6

def test_hot_gen1_cohort(con):
    tot = q(con, "select sum((event_type<>'swap_completed')::int), count(*) from e where year(t)=2025 and month(t) in (4,5,6)")
    hot = q(con, """select sum((event_type<>'swap_completed')::int), count(*), count(distinct station_id) from e
                    where year(t)=2025 and month(t) in (4,5,6) and gen='Gen1' and city in ('Jaipur','Delhi NCR','Hyderabad')""")
    assert hot[2] == F["hot_gen1_stations"]
    assert abs(100*hot[0]/tot[0] - F["hot_gen1_share_fail25_pct"]) < 1e-6 and abs(100*hot[1]/tot[1] - F["hot_gen1_share_att25_pct"]) < 1e-6

def test_heat_mechanism(con):
    hot = q(con, """select avg(avg_charge_minutes), 100*avg((charged_2w_min=0)::int) from station_hourly_status h join stations s using(station_id)
                    where telemetry_status='ok' and s.charger_generation='Gen1' and cabinet_temp_c>=45 and station_id not like 'STN-TST%'""")
    assert abs(hot[0] - F["chg_min_Gen1_hot"]) < 0.01 and abs(hot[1] - F["zero_stock_Gen1_hot_pct"]) < 0.01

def test_kyron(con):
    n, ret, soh = q(con, "select count(*), count(retired_date), avg(current_soh_pct) from batteries where supplier='Kyron' and pack_type like '2W%'")
    assert n == ret == F["packs_Kyron_2W"] == F["retired_Kyron_2W"] and abs(soh - F["soh_now_Kyron_2W"]) < 0.01
    late = q(con, """select count(*) from swap_events x join batteries b on b.battery_id=x.battery_out_id
                     where b.retired_date is not null and x.event_ts > b.retired_date""")[0]
    assert late == F["kyron_issued_after_retirement"]

def test_zipdrop_amendment(con):
    d, a = q(con, "select discount_pct, discount_pct_after_amendment from fleet_partners where partner_name='ZipDrop'")
    assert (d, a) == (12, 28)
    before, after = con.execute("""select avg(amount_charged_inr) from e join riders r using(rider_id) where r.partner_id='FP-03' and event_type='swap_completed'
        and t between '2024-08-01' and '2025-01-31' group by t >= '2024-11-01' order by t >= '2024-11-01'""").fetchall()
    assert abs(before[0] - F["zipdrop_rev_before"]) < 0.01 and abs(after[0] - F["zipdrop_rev_after"]) < 0.01

def test_payment_mode_constant(con):
    assert q(con, "select count(distinct payment_mode) from swap_events")[0] == 1

def test_weather_threshold(con):
    v = q(con, """select 100*avg((x.event_type<>'swap_completed')::int) from e x join city_daily_context c on c.city=x.city and c.date=x.t::date
                  where x.gen='Gen1' and c.max_temp_c > 38""")[0]
    assert abs(v - F["wx_fail_Gen1_ge38_pct"]) < 1e-6
