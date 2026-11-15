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
    for t in ["swap_events", "stations", "riders", "batteries", "station_hourly_status", "fleet_partners"]:
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

def test_backtest(con):
    rows = con.execute("""select station_id,
        1-avg((event_type='swap_completed')::int) filter (where year(t)=2024 and month(t) in (4,5,6)) a,
        1-avg((event_type='swap_completed')::int) filter (where year(t)=2025 and month(t) in (4,5,6)) b,
        sum((event_type<>'swap_completed')::int) filter (where year(t)=2025 and month(t) in (4,5,6)) f,
        count(*) filter (where year(t)=2025 and month(t) in (4,5,6)) n
        from e group by 1""").fetchall()
    both = [r for r in rows if r[1] is not None and r[2] is not None]
    rho = stats.spearmanr([r[1] for r in both], [r[2] for r in both]).correlation
    assert len(both) == F["backtest_stations"] and abs(rho - F["backtest_spearman"]) < 1e-6
    top = sorted(both, key=lambda r: -r[1])[:20]
    tf = sum(r[3] or 0 for r in rows); tn = sum(r[4] or 0 for r in rows)
    assert abs(100*sum(r[3] for r in top)/tf - F["top20_fail_share_2025_pct"]) < 1e-6
    assert abs(100*sum(r[4] for r in top)/tn - F["top20_attempt_share_2025_pct"]) < 1e-6

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
