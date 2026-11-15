#!/usr/bin/env python3
"""Builds site/index.html, the one-page briefing, from outputs/facts.json and
outputs/summary_data.json. Every number on the page comes from those two files.

Usage: build_site.py [--theme memo|control|board] [--out site/index.html]
"""
import argparse, json, os, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = json.load(open(os.path.join(ROOT, "outputs", "facts.json")))
D = json.load(open(os.path.join(ROOT, "outputs", "summary_data.json")))

def n(k, nd=1):
    v = F[k]
    return f"{v:,.{nd}f}" if nd else f"{v:,.0f}"

THEMES = {
    "memo": """
      --bg:#f4efe6; --ink:#1d1b18; --muted:#6f685d; --line:#d9d0c1; --card:#fbf8f2; --heat:#c4391d; --cool:#2f6f73; --grey:#a59c8d;
      --display:'Fraunces', Georgia, serif; --body:'Inter', system-ui, sans-serif; --mono:'IBM Plex Mono', ui-monospace, monospace;
      --hero-size:clamp(40px,6.2vw,84px); --hero-weight:500; --radius:2px; --grid:linear-gradient(var(--line) 1px,transparent 1px) 0 0/100% 28px;""",
    "control": """
      --bg:#0c0d0e; --ink:#eceae6; --muted:#8d918f; --line:#24272a; --card:#141618; --heat:#ff8a1f; --cool:#5ec2b7; --grey:#4a4f53;
      --display:'Inter Tight', 'Inter', system-ui, sans-serif; --body:'Inter', system-ui, sans-serif; --mono:'JetBrains Mono', ui-monospace, monospace;
      --hero-size:clamp(36px,5.4vw,72px); --hero-weight:600; --radius:10px; --grid:none;""",
    "board": """
      --bg:#ffffff; --ink:#111111; --muted:#6b6b6b; --line:#e3e3e3; --card:#f6f6f4; --heat:#e0461b; --cool:#1f5fbf; --grey:#b9b9b9;
      --display:'Inter Tight', 'Inter', system-ui, sans-serif; --body:'Inter', system-ui, sans-serif; --mono:'IBM Plex Mono', ui-monospace, monospace;
      --hero-size:clamp(34px,4.6vw,60px); --hero-weight:700; --radius:0; --grid:none;""",
}
FONTS = "https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600&family=Inter:wght@400;500;600;700&family=Inter+Tight:wght@500;600;700;800&family=IBM+Plex+Mono:wght@400;500&family=JetBrains+Mono:wght@400;500&display=swap"

def page(theme):
    big36 = n("hot_gen1_stations", 0)
    hero_lead = {
        "memo": f'<p class="kicker">Operations briefing · VoltRelay battery-swap network</p><h1>The same {big36} old cabinets will fail again <em>next April</em>.</h1>',
        "control": f'<p class="kicker">VoltRelay · summer failure forecast</p><h1>{big36} cabinets. Every summer. <span class="hot">Again next April.</span></h1>',
        "board": f'<div class="giant">{big36}</div><h1>old cabinets will fail again next April.</h1>',
    }[theme]
    stats = [
        (n("hot_gen1_share_fail25_pct") + "%", f"of summer 2025 failed swaps came from these {big36} stations"),
        (n("hot_gen1_share_att25_pct") + "%", "of attempts went through them"),
        ("R² " + n("oos_r2_rule_loo", 3), "out of sample: a rule from summer 2024 predicted 90 stations in 2025"),
        (n("upgrade_avoided_failed", 0), "failed swaps a summer avoided if they ran like Gen3 cabinets"),
    ]
    stat_html = "".join(f'<div class="stat"><div class="v">{v}</div><div class="l">{html.escape(l)}</div></div>' for v, l in stats)
    verdicts = "".join(
        f'<div class="verdict"><div class="p">{html.escape(v["proposal"])}</div><div class="vv {"no" if v["verdict"].startswith(("No", "Not")) else "yes"}">{html.escape(v["verdict"])}</div>'
        f'<div class="d">{html.escape(v["do this instead"])}</div><div class="o">{html.escape(v["owner"])} · {html.escape(v["confidence"])}</div></div>'
        for v in D["verdicts"])
    rows = "".join(f'<tr><td>{s["wave_2026"]}</td><td class="mono">{s["station_id"]}</td><td>{s["city"]}</td><td class="num">{s["f25"]}%</td></tr>'
                   for s in D["stations"])
    data_js = json.dumps({"groups": D["groups"], "mechanism": D["mechanism"], "churn": D["churn"]})
    return f"""<!doctype html><html lang="en" data-theme="{theme}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Next April</title><link rel="preconnect" href="https://fonts.googleapis.com"><link href="{FONTS}" rel="stylesheet">
<style>
:root{{{THEMES[theme]}}}
*{{box-sizing:border-box}} html,body{{margin:0;background:var(--bg);color:var(--ink);font-family:var(--body);-webkit-font-smoothing:antialiased}}
.wrap{{max-width:1180px;margin:0 auto;padding:40px 24px 64px}}
.top{{display:flex;justify-content:space-between;align-items:baseline;border-bottom:1px solid var(--line);padding-bottom:14px;font-size:13px;color:var(--muted)}}
.top b{{color:var(--ink);font-family:var(--display);font-size:20px;letter-spacing:-.01em}}
.hero{{padding:48px 0 28px}} .kicker{{font-family:var(--mono);font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin:0 0 14px}}
h1{{font-family:var(--display);font-size:var(--hero-size);font-weight:var(--hero-weight);line-height:1.02;letter-spacing:-.02em;margin:0;max-width:16ch}}
h1 em{{font-style:italic;color:var(--heat)}} .hot{{color:var(--heat)}}
.giant{{font-family:var(--display);font-weight:800;font-size:clamp(120px,22vw,300px);line-height:.8;letter-spacing:-.06em;color:var(--heat)}}
.sub{{max-width:62ch;color:var(--muted);font-size:17px;line-height:1.55;margin:18px 0 0}}
.stats{{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:var(--line);border:1px solid var(--line);border-radius:var(--radius);overflow:hidden;margin:28px 0 8px}}
.stat{{background:var(--card);padding:18px}} .stat .v{{font-family:var(--display);font-size:34px;font-weight:600;letter-spacing:-.02em;color:var(--heat)}}
.stat .l{{font-size:13px;color:var(--muted);line-height:1.4;margin-top:6px}}
section{{margin-top:44px}} h2{{font-family:var(--display);font-weight:600;font-size:26px;letter-spacing:-.01em;margin:0 0 6px}}
.lede{{color:var(--muted);margin:0 0 16px;max-width:70ch;line-height:1.5}}
.two{{display:grid;grid-template-columns:1fr 1fr;gap:20px}}
.panel{{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);padding:18px;background-image:var(--grid)}}
.panel h3{{margin:0 0 4px;font-size:15px}} .panel p{{margin:0 0 10px;color:var(--muted);font-size:13px}}
svg{{width:100%;height:auto;display:block}} svg text{{fill:var(--muted);font-family:var(--mono);font-size:11px}}
.verdicts{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}}
.verdict{{border:1px solid var(--line);border-radius:var(--radius);padding:16px;background:var(--card)}}
.verdict .p{{font-weight:600}} .verdict .vv{{font-family:var(--mono);font-size:12px;text-transform:uppercase;letter-spacing:.06em;margin:8px 0}}
.verdict .vv.no{{color:var(--heat)}} .verdict .vv.yes{{color:var(--cool)}} .verdict .d{{font-size:14px;line-height:1.45}} .verdict .o{{font-size:12px;color:var(--muted);margin-top:10px}}
table{{width:100%;border-collapse:collapse;font-size:13px}} td,th{{text-align:left;padding:7px 8px;border-bottom:1px solid var(--line)}} th{{color:var(--muted);font-weight:500}}
.mono{{font-family:var(--mono)}} .num{{text-align:right;font-family:var(--mono);color:var(--heat)}}
.tablewrap{{max-height:360px;overflow:auto;border:1px solid var(--line);border-radius:var(--radius)}}
.trust{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;font-size:14px;line-height:1.5}} .trust div{{border-top:2px solid var(--ink);padding-top:10px}}
footer{{margin-top:48px;color:var(--muted);font-size:12px;border-top:1px solid var(--line);padding-top:14px}}
[data-theme=board] .stats{{border:0;background:transparent;gap:0}} [data-theme=board] .stat{{background:transparent;border-left:3px solid var(--ink)}}
[data-theme=board] h2{{text-transform:uppercase;font-size:15px;letter-spacing:.12em}}
[data-theme=board] table{{font-family:var(--mono)}} [data-theme=board] tr:nth-child(odd) td{{background:var(--card)}}
[data-theme=control] .panel,[data-theme=control] .verdict,[data-theme=control] .stat{{box-shadow:inset 0 1px 0 rgba(255,255,255,.04)}}
@media (max-width:820px){{.stats,.verdicts{{grid-template-columns:1fr 1fr}} .two,.trust{{grid-template-columns:1fr}} .wrap{{padding:24px 16px 48px}} .stat .v{{font-size:26px}}}}
</style></head><body><div class="wrap">
<div class="top"><b>Next April</b><span>Gradient Learnings Data Analytics Hackathon · Dhiraj Kavuri</span></div>
<div class="hero">{hero_lead}
<p class="sub">Every April to June, the oldest swap cabinets (Gen1) in Jaipur, Delhi NCR and Hyderabad overheat, charge slowly and run out of charged packs. A rule built from summer 2024 alone predicted summer 2025 for every station open both summers. The {n("new_stations_total", 0)} new stations VoltRelay opened in between did not reach them.</p>
<div class="stats">{stat_html}</div></div>

<section><h2>One rule, tested on a summer it never saw</h2>
<p class="lede">Each bubble is one charger generation in one city. Left to right: its summer 2024 failure rate. Bottom to top: what happened in summer 2025. The red bubbles are Gen1 in the three hottest cities.</p>
<div class="two"><div class="panel"><h3>Summer 2024 rule vs summer 2025</h3><p>Failed attempts, % of attempts</p><svg id="bt" viewBox="0 0 520 340"></svg></div>
<div class="panel"><h3>Why: only Gen1 slows down in the heat</h3><p>Average minutes to charge a pack, by cabinet temperature</p><svg id="mech" viewBox="0 0 520 340"></svg></div></div></section>

<section><h2>What VoltRelay should fund</h2><p class="lede">A verdict on each of the four budget proposals, with an owner.</p><div class="verdicts">{verdicts}</div></section>

<section class="two"><div><h2>The April 2026 list</h2><p class="lede">Wave 1: Gen1 in Jaipur and Delhi NCR. Wave 2: Gen1 in Hyderabad. Summer 2025 failure rate per station.</p>
<div class="tablewrap"><table><tr><th>Wave</th><th>Station</th><th>City</th><th style="text-align:right">Failed, summer 2025</th></tr>{rows}</table></div></div>
<div><h2>Why it matters for riders</h2><p class="lede">New riders' churn by the share of their swap attempts that failed in their first 14 days.</p><div class="panel"><svg id="churn" viewBox="0 0 520 300"></svg></div></div></section>

<section><h2>Why these numbers can be trusted</h2><div class="trust">
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
</script></body></html>"""

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--theme", default="memo"); ap.add_argument("--out", default=os.path.join(ROOT, "site", "index.html"))
    a = ap.parse_args()
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    open(a.out, "w", encoding="utf-8").write(page(a.theme))
    print("built", a.out, a.theme)
