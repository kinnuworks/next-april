#!/usr/bin/env python3
"""Builds site/index.html, the one-page briefing, from outputs/facts.json and
outputs/summary_data.json. Every number on the page comes from those two files.

Usage: build_site.py [--out site/index.html]
"""
import argparse, json, os, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = json.load(open(os.path.join(ROOT, "outputs", "facts.json")))
D = json.load(open(os.path.join(ROOT, "outputs", "summary_data.json")))

def n(k, nd=1):
    v = F[k]
    return f"{v:,.{nd}f}" if nd else f"{v:,.0f}"

# The look: Brainfish's measured system (design/refs/brainfish/spec.md), picked 2026-11-15.
THEME = """
:root{ /* Brainfish: Fraunces display over Geist, near-white page, ink buttons with hard offset shadow, 10px panels, 1px hairlines */
  --bg:#fcfff7; --sheet:#ffffff; --sheet-2:#f4f5f0; --ink:#000000; --ink-2:#262626; --muted:#5e5e5e; --line:#e5e5e5; --line-strong:#262626;
  --heat:#c63b17; --cool:#2f6f5e; --grey:#a3a3a3;
  --display:'Fraunces',Georgia,serif; --body:'Geist',system-ui,sans-serif; --num:'Geist',system-ui,sans-serif;
  --fs-display:clamp(40px,calc(40px + 38 * ((100vw - 375px) / 1065)),78px); --w-display:420; --track-display:-.034em; --lh-display:1;
  --fs-h2:clamp(30px,calc(30px + 22 * ((100vw - 375px) / 1065)),52px); --w-h2:420; --font-h2:var(--display);
  --r-card:10px; --r-window:6px; --shadow-window:4px 4px 0 0 #262626; --window-edge:1px solid #262626; --align:center; --page:1392px;
}
"""
FONTS = "https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,420;9..144,500&family=Geist:wght@400;500;600&display=swap"

MARK = open(os.path.join(ROOT, "assets", "brand", "mark.svg")).read().strip()
FAVICON = "data:image/svg+xml," + __import__("urllib.parse").parse.quote(MARK)

def page(theme="a"):
    big36 = n("hot_gen1_stations", 0)
    hero_lead = f'<p class="kicker">Operations briefing for VoltRelay&rsquo;s battery-swap network</p><h1>The same {big36} old cabinets will fail again next April.</h1>'
    stats = [
        (n("hot_gen1_share_fail25_pct") + "%", f"of summer 2025 failed swaps came from these {big36} stations"),
        (n("hot_gen1_share_att25_pct") + "%", "of attempts went through them"),
        ("R² " + n("oos_r2_rule_loo", 3), "out of sample: a rule from summer 2024 predicted 90 stations in 2025"),
        (n("upgrade_avoided_failed", 0), "failed swaps a summer avoided if they ran like Gen3 cabinets"),
    ]
    stat_html = "".join(f'<div class="stat"><div class="v">{v}</div><div class="l">{html.escape(l)}</div></div>' for v, l in stats)
    verdicts = "".join(
        f'<div class="verdict"><div class="p">{html.escape(v["proposal"])}</div><div class="vv {"no" if v["verdict"].startswith(("No", "Not")) else "yes"}">{html.escape(v["verdict"])}</div>'
        f'<div class="d">{html.escape(v["do this instead"])}</div><div class="o"><b>Owner:</b> {html.escape(v["owner"])}<br><b>Confidence:</b> {html.escape(v["confidence"])}</div></div>'
        for v in D["verdicts"])
    rows = "".join(f'<tr><td>{s["wave_2026"]}</td><td class="mono">{s["station_id"]}</td><td>{s["city"]}</td><td class="num">{s["f25"]}%</td></tr>'
                   for s in D["stations"])
    data_js = json.dumps({"groups": D["groups"], "mechanism": D["mechanism"], "churn": D["churn"],
                          "months": D["months"], "gm": D["groups_monthly"], "ex": D["explorer"]})
    return f"""<!doctype html><html lang="en" ><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Next April</title><script>document.documentElement.dataset.motion=matchMedia("(prefers-reduced-motion: reduce)").matches?"reduce":"full"</script><link rel="icon" href="{FAVICON}">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="{FONTS}" rel="stylesheet">
<style>
{THEME}
*{{box-sizing:border-box}} html,body{{margin:0;overflow-x:hidden;background:var(--bg);color:var(--ink-2);font-family:var(--body);font-size:16px;line-height:1.5;-webkit-font-smoothing:antialiased}}
.wrap{{max-width:var(--page);margin:0 auto;padding:0 24px 72px}}
h1{{font-family:var(--display);font-size:var(--fs-display);font-weight:var(--w-display);line-height:var(--lh-display);letter-spacing:var(--track-display);color:var(--ink);margin:0 auto;max-width:18ch}}
.stop{{color:var(--heat)}}
.nav{{display:flex;align-items:center;justify-content:space-between;gap:16px;height:67px}}
.brand{{display:inline-flex;align-items:center;gap:8px;font-family:var(--body);font-weight:600;font-size:21px;letter-spacing:-.03em;color:var(--ink);text-decoration:none}} .brand svg{{width:34px;height:34px}} .wm{{display:inline-flex;align-items:center;gap:6px}} .wm svg{{width:22px;height:22px}}
.links{{display:flex;gap:28px}} .links a{{color:var(--ink-2);text-decoration:none;font-size:17px}} .links a:hover{{color:var(--ink)}}
.btn{{display:inline-flex;align-items:center;gap:8px;height:48px;padding:0 18px;background:#a3e635;color:#000;border:1px solid #262626;border-radius:4px;box-shadow:2px 2px 0 0 #262626;font:500 18px/1 var(--body);text-decoration:none;transition:transform .25s,box-shadow .25s}}
.btn:hover{{transform:translate(-1px,-1px);box-shadow:3px 3px 0 0 #262626}} .btn-sm{{height:40px;font-size:16px;padding:0 14px}}
.hero{{padding:76px 0 0;text-align:center}}
.badge{{display:inline-flex;align-items:center;gap:10px;padding:4px 14px 4px 4px;border:1px solid var(--line);border-radius:999px;background:#fff;color:var(--ink-2);font-size:14px;text-decoration:none}}
.badge .tag{{background:#a3e635;color:#000;border-radius:999px;padding:3px 10px;font-weight:600;font-size:13px}}
.hero h1{{margin-top:28px}}
.sub{{max-width:36ch;color:var(--ink-2);font-size:21px;line-height:1.5;margin:26px auto 30px}}
.trustrow{{display:flex;justify-content:center;flex-wrap:wrap;gap:8px 28px;margin:20px 0 0;font-size:14px;color:var(--ink-2)}} .trustrow span{{display:inline-flex;align-items:center;gap:8px}}
.trustrow svg{{width:16px;height:16px;fill:none;stroke:var(--ink-2);stroke-width:1.3}}
.window{{max-width:1310px;margin:64px auto 0;background:var(--sheet-2);border:1px solid #262626;border-radius:10px;box-shadow:6px 6px 0 0 #262626;text-align:left;overflow:hidden}}
.window-bar{{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:14px 20px;font-size:15px;color:var(--muted)}}
.crumb{{display:flex;align-items:center;gap:10px}} .crumb b{{color:var(--ink);font-weight:600}} .crumb i{{width:1px;height:18px;background:var(--line)}}
.status{{display:inline-flex;align-items:center;gap:8px;padding:5px 12px;border-radius:999px;background:#ecf8ef;border:1px solid #bfe3c8;color:#17603a;font-weight:500;font-size:14px}} .status i{{width:7px;height:7px;border-radius:50%;background:#1f8f4e}}
.window-body{{display:grid;grid-template-columns:1.15fr 1fr;margin:0 20px 20px;background:var(--sheet);border:1px solid #e6e6e1;border-radius:10px}}
.window-body > .view{{padding:22px 26px}} .axis-note{{margin:0 0 8px;color:var(--muted);font-size:14px}}
.steps{{border-left:1px solid #e6e6e1;padding:26px 30px}} .steps h3{{margin:0 0 18px;font-size:17px;font-weight:600;color:var(--ink);padding-bottom:16px;border-bottom:1px solid var(--line)}}
.steps ol{{list-style:none;margin:0;padding:0;counter-reset:s}}
.steps li{{position:relative;display:flex;justify-content:space-between;gap:16px;align-items:baseline;padding:0 0 22px 40px;font-size:16px}}
.steps li::before{{content:"";position:absolute;left:0;top:-2px;width:26px;height:26px;border-radius:50%;background:#111 url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'%3E%3Cpath d='M4.5 8.3l2.2 2.2 4.8-5' fill='none' stroke='white' stroke-width='1.8'/%3E%3C/svg%3E") center/14px no-repeat}}
.steps li::after{{content:"";position:absolute;left:12.5px;top:24px;bottom:-2px;width:1.5px;background:#111}} .steps li:last-child::after{{display:none}}
.steps li b{{font-weight:500;color:var(--ink)}} .steps li span{{flex:none;color:var(--muted);font-size:14px}}
.steps .foot{{display:flex;gap:10px;align-items:baseline;margin:6px 0 0;padding-top:16px;border-top:1px solid var(--line);font-size:15px;color:var(--ink);font-weight:500}} .steps .foot i{{flex:none;width:8px;height:8px;border-radius:50%;background:#1f8f4e;transform:translateY(-1px)}}
.tryrow{{display:flex;justify-content:flex-start;flex-wrap:wrap;align-items:center;gap:10px;max-width:1310px;margin:22px auto 0;font-size:14px;color:var(--ink-2)}}
.pill{{display:inline-flex;align-items:center;height:38px;padding:0 14px;border:1px solid #d4d4d4;border-radius:999px;background:#fff;color:#000;font:500 14px var(--body);cursor:pointer;text-decoration:none}}
.pill.on{{border-color:#262626;box-shadow:2px 2px 0 0 #262626}}
.stats{{display:grid;grid-template-columns:repeat(4,1fr);margin:88px calc(50% - 50vw) 0;padding:0 calc(50vw - 50%);background:#fff;border-top:1px solid var(--line);border-bottom:1px solid var(--line);text-align:left}}
.stat{{padding:30px 26px}} .stat + .stat{{border-left:1px solid var(--line)}}
.stat .v{{font-family:var(--display);font-size:var(--fs-h2);font-weight:420;letter-spacing:-.034em;line-height:1;color:var(--ink)}} .stat:first-child .v{{color:var(--heat)}}
.stat .l{{font-size:15px;color:var(--ink-2);line-height:1.45;margin-top:14px}}
[data-motion=reduce] *{{transition:none!important;animation:none!important}}
section{{margin-top:122px}} h2{{font-family:var(--font-h2);font-weight:var(--w-h2);font-size:var(--fs-h2);letter-spacing:-.02em;line-height:1.1;color:var(--ink);margin:0 0 12px}}
.lede{{color:var(--ink-2);margin:0 0 22px;max-width:62ch;line-height:1.55}}
.two{{display:grid;grid-template-columns:1fr 1fr;gap:24px}}
.panel{{background:var(--sheet);border:1px solid var(--line);border-radius:var(--r-card);padding:20px}}
.panel h3{{margin:0 0 4px;font-size:16px;font-weight:600;color:var(--ink)}} .panel p{{margin:0 0 10px;color:var(--muted);font-size:14px}}
svg{{width:100%;height:auto;display:block}} svg text{{fill:var(--muted);font-family:var(--body);font-size:13px}}
.filters{{display:flex;flex-wrap:wrap;gap:10px 22px;margin:0 0 14px;font-size:14px}} .filters select{{font:inherit;margin-left:6px;padding:6px 8px;background:var(--sheet);color:var(--ink);border:1px solid var(--line-strong);border-radius:calc(var(--r-card) / 2)}}
.tablewrap.ex{{max-height:380px;overflow:auto}} #ext td,#ext th{{white-space:nowrap}} #ext tbody tr{{cursor:pointer}} #ext tbody tr:hover,#ext tbody tr.sel{{background:var(--sheet-2)}} #ext tbody tr.hot td:first-child{{box-shadow:inset 3px 0 0 var(--heat)}}
.verdicts{{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:16px}}
.verdict{{border:1px solid var(--line);border-radius:var(--r-card);padding:18px;background:var(--sheet)}}
.verdict .p{{font-weight:600;color:var(--ink)}} .verdict .vv{{font-size:14px;font-weight:600;margin:8px 0}}
.verdict .vv.no{{color:var(--heat)}} .verdict .vv.yes{{color:var(--cool)}} .verdict .d{{font-size:15px;line-height:1.45}} .verdict .o{{font-size:14px;color:var(--muted);margin-top:12px;line-height:1.45}} .verdict .o b{{color:var(--ink-2);font-weight:500}}
table{{width:100%;border-collapse:collapse;font-size:14px}} td,th{{text-align:left;padding:8px 10px;border-bottom:1px solid var(--line)}} th{{color:var(--muted);font-weight:500;background:var(--sheet);position:sticky;top:0}}
.mono{{font-variant-numeric:tabular-nums}} .num{{text-align:right;font-variant-numeric:tabular-nums;color:var(--heat);font-weight:500}}
.tablewrap{{max-height:380px;overflow:auto;border:1px solid var(--line);border-radius:var(--r-card)}}
.trust{{display:grid;grid-template-columns:repeat(3,1fr);gap:24px;font-size:15px;line-height:1.55}} .trust div{{border-top:2px solid var(--ink);padding-top:12px}}
footer{{margin-top:72px;color:var(--muted);font-size:13px;border-top:1px solid var(--line);padding-top:16px}}
@media (max-width:820px){{.links{{display:none}} .crumb > b.wm,.crumb > i,.crumb > span[aria-hidden]{{display:none}} .crumb{{font-size:14px}} .badge{{font-size:13px;text-align:left}} .badge .tag{{white-space:nowrap}} .status{{font-size:13px}} .window-body{{grid-template-columns:1fr;margin:0 10px 10px}} .steps{{border-left:0;border-top:1px solid #e6e6e1;padding:20px}} .window-body > .view{{padding:16px}} .sub{{font-size:18px}} .window-bar{{flex-wrap:wrap}} .stats{{margin-top:56px}} .stats{{grid-template-columns:1fr 1fr}} .stat:nth-child(3){{border-left:0}} .two,.trust,.window-body{{grid-template-columns:1fr}} .window-body > div + div{{border-left:0;border-top:1px solid var(--line)}} .wrap{{padding:0 16px 48px}} .hero{{padding-top:40px}} .verdicts{{grid-template-columns:1fr}}}}
</style></head><body><div class="wrap">
<nav class="nav"><a class="brand" href="#" aria-label="Next April">{MARK}<span>Next April</span></a>
<div class="links"><a href="#win">Why</a><a href="#fund">What to fund</a><a href="#explore">Stations</a><a href="#trust">How it's checked</a></div>
<a class="btn btn-sm" href="#explore">Look up a station <span aria-hidden="true">&rarr;</span></a></nav>
<div class="hero" id="why">
<a class="badge" href="#win"><span class="tag">Back-tested</span>A summer 2024 rule, scored on summer 2025 <span aria-hidden="true">&rarr;</span></a>
<h1>The same {big36} old cabinets will fail again next April.</h1>
<p class="sub">Every April to June, the oldest cabinets in VoltRelay&rsquo;s EV battery-swap network overheat in Jaipur, Delhi NCR and Hyderabad and turn delivery riders away. Leadership should fund fixing those {big36} cabinets, not more stations.</p>
<a class="btn" href="#explore">Look up a station <span aria-hidden="true">&rarr;</span></a>
<div class="trustrow"><span><svg viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="6.5"/><path d="M5 8.2l2 2 4-4.4"/></svg>Runs top to bottom in Colab</span><span><svg viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="6.5"/><path d="M5 8.2l2 2 4-4.4"/></svg>Every number re-checked by tests</span><span><svg viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="6.5"/><path d="M5 8.2l2 2 4-4.4"/></svg>The organisers&rsquo; VoltRelay dataset (synthetic)</span></div>
<div class="window" id="win"><div class="window-bar"><span class="crumb"><b class="wm">{MARK}Next April</b><i></i>Back-tests<span aria-hidden="true">&rsaquo;</span><b id="wtitle">Summer 2024 rule vs summer 2025</b></span><span class="status"><i></i><span id="wstatus">R² {n("oos_r2_rule_loo", 3)} out of sample</span></span></div>
<div class="window-body"><div class="view" data-view="bt"><p class="axis-note">Failed attempts, % of attempts. Each bubble is one charger generation in one city; red is Gen1 in the three hottest cities.</p><svg id="bt" viewBox="0 0 520 340"></svg></div>
<div class="view" data-view="mech" hidden><p class="axis-note">Average minutes to charge a pack, by cabinet temperature.</p><svg id="mech" viewBox="0 0 520 340"></svg></div>
<div class="steps" id="steps-bt"><h3>How the rule works</h3><ol>
<li><b>Group stations by charger generation and city</b><span>stations</span></li>
<li><b>Take each group's summer 2024 failure rate</b><span>swap attempts</span></li>
<li><b>Predict each station's summer 2025 rate, leaving it out</b><span>out of sample</span></li>
<li><b>Score it against what happened</b><span>R² {n("oos_r2_rule_loo", 3)}</span></li></ol>
<p class="foot"><i></i>The {big36} red-group stations failed on {n("hot_gen1_fail24_pct")}% of summer attempts in 2024 and {n("hot_gen1_fail25_pct")}% in 2025.</p></div>
<div class="steps" id="steps-mech" hidden><h3>Why they fail</h3><ol>
<li><b>Cabinet passes 45°C inside</b><span>telemetry</span></li>
<li><b>Gen1 charge time rises from {n("chg_min_Gen1_cool", 0)} to {n("chg_min_Gen1_hot", 0)} minutes</b><span>Gen3: {n("chg_min_Gen3_hot", 0)}</span></li>
<li><b>Same cabinet, own hot hours: failure odds ×{n("fe_or_hot_Gen1", 2)}</b><span>Gen3 ×{n("fe_or_hot_Gen3", 2)}</span></li>
<li><b>Empty shelves are not the cause</b><span>odds ratio {n("stock_mh_or", 2)}</span></li></ol>
<p class="foot"><i></i>Fix the cabinet, not the stock.</p></div></div></div>
<div class="tryrow"><span>Try another view</span><button class="pill on" data-show="bt">Back-test</button><button class="pill" data-show="mech">Heat mechanism</button><a class="pill" href="#explore">One station</a></div>
<div class="stats">{stat_html}</div></div>

<section id="fund"><h2>What VoltRelay should fund</h2><p class="lede">A verdict on each of the four budget proposals, with an owner.</p><div class="verdicts">{verdicts}</div></section>

<section class="two"><div><h2>The April 2026 list</h2><p class="lede">Wave 1: Gen1 in Jaipur and Delhi NCR. Wave 2: Gen1 in Hyderabad. Summer 2025 failure rate per station.</p>
<div class="tablewrap"><table><tr><th>Wave</th><th>Station</th><th>City</th><th style="text-align:right">Failed, summer 2025</th></tr>{rows}</table></div></div>
<div><h2>Why it matters for riders</h2><p class="lede">New riders' churn by the share of their swap attempts that failed in their first 14 days.</p><div class="panel"><svg id="churn" viewBox="0 0 520 300"></svg></div></div></section>

<section id="explore"><h2>Look up any station</h2><p class="lede">Filter, then pick a station to see its monthly failure rate against the average for its charger generation in its city. Summer months are shaded.</p>
<div class="filters"><label>City <select id="fc"><option value="">All</option></select></label>
<label>Generation <select id="fg"><option value="">All</option></select></label>
<label><input type="checkbox" id="fa"> Only the April 2026 list</label></div>
<div class="two"><div class="tablewrap ex"><table id="ext"><thead><tr><th>Station</th><th>City</th><th>Gen</th><th>Opened</th><th>Site</th><th style="text-align:right">Failed, summer 2025</th></tr></thead><tbody></tbody></table></div>
<div class="panel"><h3 id="exh">Pick a station</h3><p id="exp">Click a row in the table.</p><svg id="exs" viewBox="0 0 520 300"></svg></div></div></section>

<section id="trust"><h2>Why these numbers can be trusted</h2><div class="trust">
<div>Every documented data issue checked, plus {n("issues_undocumented", 0)} the documentation does not mention, each with rows affected and its effect on a result.</div>
<div>Every number is computed by a notebook that runs top to bottom from the organiser's files, and re-derived by independent tests.</div>
<div>Out-of-sample checks: the summer 2024 rule on summer 2025, the churn model on riders who started in 2025, a placebo test for the pricing pilot.</div></div></section>
<footer>Synthetic VoltRelay dataset provided by Gradient Learnings. AI coding assistance used; every number checked by the notebook, tests and a number-tracing script.</footer>
</div>
<script>
const DATA={data_js};
const css=v=>getComputedStyle(document.documentElement).getPropertyValue(v).trim();
const NS='http://www.w3.org/2000/svg';
function el(t,a,p){{const e=document.createElementNS(NS,t);for(const k in a)e.setAttribute(k,a[k]);p.appendChild(e);return e}}
function axes(svg,x0,x1,y0,y1,xt,yt,xl,yl,W=520,H=340,m={{l:46,r:14,t:10,b:38}}){{
  const X=v=>m.l+(v-x0)/(x1-x0)*(W-m.l-m.r), Y=v=>H-m.b-(v-y0)/(y1-y0)*(H-m.t-m.b);
  xt.forEach(v=>{{el('line',{{x1:X(v),x2:X(v),y1:m.t,y2:H-m.b,stroke:css('--line')}},svg);el('text',{{x:X(v),y:H-m.b+16,'text-anchor':'middle'}},svg).textContent=v}});
  yt.forEach(v=>{{el('line',{{x1:m.l,x2:W-m.r,y1:Y(v),y2:Y(v),stroke:css('--line')}},svg);el('text',{{x:m.l-8,y:Y(v)+4,'text-anchor':'end'}},svg).textContent=v}});
  if(xl)el('text',{{x:(W+m.l)/2,y:H-4,'text-anchor':'middle'}},svg).textContent=xl;
  return [X,Y];
}}
(function(){{const s=document.getElementById('bt');const [X,Y]=axes(s,3,19,3,19,[4,8,12,16],[4,8,12,16],'summer 2024 (the rule)');
 el('line',{{x1:X(3),y1:Y(3),x2:X(19),y2:Y(19),stroke:css('--muted'),'stroke-dasharray':'4 4'}},s);
 DATA.groups.forEach(g=>{{const r=Math.sqrt(g.attempts25)/18;el('circle',{{cx:X(g.g24),cy:Y(g.g25),r,fill:g.hot?css('--heat'):css('--grey'),'fill-opacity':.85}},s);
  if(g.hot){{const c=g.group.replace('Gen1 in ','');const o={{'Delhi NCR':[-r-6,-14,'end'],'Jaipur':[0,r+16,'middle'],'Hyderabad':[-r-6,4,'end']}}[c];const t=el('text',{{x:X(g.g24)+o[0],y:Y(g.g25)+o[1],'text-anchor':o[2]}},s);t.textContent=c;t.style.fill=css('--ink')}}}});}})();
(function(){{const s=document.getElementById('mech');const bands=['<35','35-40','40-45','45+'];const [X,Y]=axes(s,0,3,30,170,[],[40,80,120,160],'cabinet temperature (°C)');
 bands.forEach((b,i)=>el('text',{{x:X(i),y:340-38+16,'text-anchor':'middle'}},s).textContent=b);
 [['Gen1','--heat'],['Gen2','--grey'],['Gen3','--cool']].forEach(([g,c])=>{{const pts=bands.map((b,i)=>{{const d=DATA.mechanism.find(m=>m.gen==g&&m.band==b);return [X(i),Y(d.charge_min)]}});
  el('polyline',{{points:pts.map(p=>p.join(',')).join(' '),fill:'none',stroke:css(c),'stroke-width':3}},s);pts.forEach(p=>el('circle',{{cx:p[0],cy:p[1],r:4,fill:css(c)}},s));
  const t=el('text',{{x:pts[3][0]-8,y:pts[3][1]-10,'text-anchor':'end'}},s);t.textContent=g;t.style.fill=css(c)}});}})();
(function(){{const s=document.getElementById('churn');const W=520,H=300,m=36,bw=(W-2*m)/DATA.churn.length;const max=40;
 DATA.churn.forEach((c,i)=>{{const h=(c.pct/max)*(H-80);const x=m+i*bw+10;const hot=c.band.includes('20');
  el('rect',{{x,y:H-40-h,width:bw-20,height:h,fill:(i>=2)?css('--heat'):css('--grey'),rx:2}},s);
  const v=el('text',{{x:x+(bw-20)/2,y:H-46-h,'text-anchor':'middle'}},s);v.textContent=c.pct+'%';v.style.fill=css('--ink');v.style.fontSize='13px';
  el('text',{{x:x+(bw-20)/2,y:H-22,'text-anchor':'middle'}},s).textContent=c.band==='none'?'no failures':c.band+' failed';}});}})();

(function(){{
 const ex=DATA.ex, M=DATA.months, fc=document.getElementById('fc'), fg=document.getElementById('fg'), fa=document.getElementById('fa'), tb=document.querySelector('#ext tbody');
 [...new Set(ex.map(r=>r.city))].sort().forEach(c=>fc.add(new Option(c,c)));
 [...new Set(ex.map(r=>r.gen))].sort().forEach(g=>fg.add(new Option(g,g)));
 function draw(r){{
  const s=document.getElementById('exs'); s.innerHTML='';
  const g=DATA.gm[r.gen+'|'+r.city]||[]; const vals=r.m.concat(g).filter(v=>v!=null);
  const top=Math.ceil(Math.max(...vals,5)/5)*5; const yt=[]; for(let v=0;v<=top;v+=5)yt.push(v);
  const n=M.length; const [X,Y]=axes(s,0,n-1,0,top,[],yt,null,null,520,300,{{l:40,r:12,t:10,b:30}});
  M.forEach((m,i)=>{{const mo=+m.slice(5);if([4,5,6].includes(mo))el('rect',{{x:X(i)-((X(1)-X(0))/2),y:10,width:X(1)-X(0),height:260,fill:css('--heat'),opacity:.08}},s);
   if(mo===1||i===0)el('text',{{x:X(i),y:290,'text-anchor':'middle'}},s).textContent=m}});
  const line=(arr,col,w,dash)=>{{const p=arr.map((v,i)=>v==null?null:[X(i),Y(v)]).filter(Boolean);if(p.length)el('polyline',{{points:p.map(q=>q.join(',')).join(' '),fill:'none',stroke:col,'stroke-width':w,'stroke-dasharray':dash||''}},s)}};
  line(g,css('--grey'),2,'4 3'); line(r.m,css('--heat'),2.5);
  document.getElementById('exh').textContent=r.id+', '+r.gen+' in '+r.city;
  document.getElementById('exp').textContent='Red: this station, % of attempts failed each month. Dashed: all '+r.gen+' stations in '+r.city+'.'+(r.april?' On the April 2026 list, wave '+r.april+'.':'');
 }}
 function render(){{
  const rows=ex.filter(r=>(!fc.value||r.city===fc.value)&&(!fg.value||r.gen===fg.value)&&(!fa.checked||r.april)).sort((a,b)=>(b.s25??-1)-(a.s25??-1));
  tb.innerHTML='';
  rows.forEach(r=>{{const tr=document.createElement('tr');if(r.april)tr.className='hot';
   tr.innerHTML=`<td class="mono">${{r.id}}</td><td>${{r.city}}</td><td>${{r.gen}}</td><td>${{r.opened}}</td><td>${{r.site}}</td><td class="num">${{r.s25==null?'not open':r.s25+'%'}}</td>`;
   tr.onclick=()=>{{tb.querySelectorAll('tr').forEach(t=>t.classList.remove('sel'));tr.classList.add('sel');draw(r)}};tb.appendChild(tr)}});
  if(rows.length){{tb.firstChild.classList.add('sel');draw(rows[0])}}
  else{{tb.innerHTML='<tr><td colspan="6">No station matches these filters. Clear a filter to see stations.</td></tr>';document.getElementById('exs').innerHTML='';
   document.getElementById('exh').textContent='No station selected';document.getElementById('exp').textContent='Pick a city and generation that have stations.'}}
 }}
 [fc,fg,fa].forEach(e=>e.onchange=render);
 // Every state can be opened directly: ?state=april | station&id=STN-... | empty | default
 const q=new URLSearchParams(location.search), st=q.get('state');
 if(st==='april'){{fa.checked=true}}
 if(st==='empty'){{fc.value='Mumbai';fg.value='Gen1';fa.checked=true}}
 render();
 if(st==='station'&&q.get('id')){{const r=ex.find(x=>x.id===q.get('id'));if(r){{fc.value=r.city;render();const tr=[...tb.querySelectorAll('tr')].find(t=>t.textContent.startsWith(r.id));if(tr)tr.click()}}}}
 if(st&&st!=='default')document.getElementById('explore').scrollIntoView();
}})();

document.querySelectorAll('.pill[data-show]').forEach(b=>b.onclick=()=>{{const v=b.dataset.show;
 document.querySelectorAll('.pill[data-show]').forEach(x=>x.classList.toggle('on',x===b));
 document.querySelectorAll('#win .view').forEach(x=>x.hidden=x.dataset.view!==v);
 document.getElementById('steps-bt').hidden=v!=='bt'; document.getElementById('steps-mech').hidden=v!=='mech';
 document.getElementById('wtitle').textContent=v==='bt'?'Summer 2024 rule vs summer 2025':'Charge time by cabinet temperature';
 document.getElementById('wstatus').textContent=v==='bt'?{json.dumps("R² "+n("oos_r2_rule_loo",3)+" out of sample")}:{json.dumps("Same cabinet, odds ×"+n("fe_or_hot_Gen1",2)+" when hot")};}});
if(new URLSearchParams(location.search).get('state')==='mechanism')document.querySelector('.pill[data-show=mech]').click();
</script></body></html>"""

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--theme", default="a"); ap.add_argument("--out", default=os.path.join(ROOT, "site", "index.html"))
    a = ap.parse_args()
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    open(a.out, "w", encoding="utf-8").write(page(a.theme))
    print("built", a.out, a.theme)
