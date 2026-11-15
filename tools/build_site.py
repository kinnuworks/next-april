#!/usr/bin/env python3
"""Builds the one-page briefing from outputs/facts.json and outputs/summary_data.json.
Every number on the page comes from those two files.

The look is Brainfish's measured system (design/refs/brainfish/spec.md and system.md), built slot for slot.

Usage: build_site.py
"""
import json, os, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = json.load(open(os.path.join(ROOT, "outputs", "facts.json")))
D = json.load(open(os.path.join(ROOT, "outputs", "summary_data.json")))
MARK_SRC = open(os.path.join(ROOT, "assets", "brand", "mark.svg")).read().strip()
MARK = MARK_SRC
def mark(fill, slot):
    return MARK_SRC.replace("#a3e635", fill).replace("#c63b17", slot)


def n(k, nd=1):
    v = F[k]
    return f"{v:,.{nd}f}" if nd else f"{v:,.0f}"


def fill(t, **kw):
    for k, v in kw.items():
        t = t.replace("{{" + k + "}}", str(v))
    return t


B36 = n("hot_gen1_stations", 0)
R2 = n("oos_r2_rule_loo", 3)
DATA_JS = json.dumps({"groups": D["groups"], "mechanism": D["mechanism"], "churn": D["churn"],
                      "months": D["months"], "gm": D["groups_monthly"], "ex": D["explorer"]})
STATS = [
    (n("hot_gen1_share_fail25_pct") + "%", f"of summer 2025 failed swaps came from these {B36} stations"),
    ("R² " + R2, "out of sample: a rule from summer 2024 predicted 90 stations in 2025"),
    (n("upgrade_avoided_failed", 0), "failed swaps a summer avoided if they ran like Gen3 cabinets"),
    (n("hot_gen1_share_att25_pct") + "%", "of attempts went through them"),
]
VERDICTS = D["verdicts"]
STATIONS_ROWS = "".join(
    f'<tr><td>{s["wave_2026"]}</td><td class="mono">{s["station_id"]}</td><td>{s["city"]}</td><td class="num">{s["f25"]}%</td></tr>'
    for s in D["stations"])
STEPS_BT = f"""<li><b>Group stations by charger generation and city</b><span>stations</span></li>
<li><b>Take each group's summer 2024 failure rate</b><span>swap attempts</span></li>
<li><b>Predict each station's summer 2025 rate, leaving it out</b><span>out of sample</span></li>
<li><b>Score it against what happened</b><span>R² {R2}</span></li>"""
STEPS_MECH = f"""<li><b>Cabinet passes 45°C inside</b><span>telemetry</span></li>
<li><b>Gen1 charge time rises from {n("chg_min_Gen1_cool", 0)} to {n("chg_min_Gen1_hot", 0)} minutes</b><span>Gen3: {n("chg_min_Gen3_hot", 0)}</span></li>
<li><b>Same cabinet, own hot hours: failure odds ×{n("fe_or_hot_Gen1", 2)}</b><span>Gen3 ×{n("fe_or_hot_Gen3", 2)}</span></li>
<li><b>Empty shelves are not the cause</b><span>odds ratio {n("stock_mh_or", 2)}</span></li>"""
TAKEAWAYS = [
    f"The {B36} Gen1 stations in Jaipur, Delhi NCR and Hyderabad handled {n('hot_gen1_share_att25_pct')}% of summer 2025 attempts and produced {n('hot_gen1_share_fail25_pct')}% of its failures.",
    f"At 45°C inside the cabinet, Gen1 takes {n('chg_min_Gen1_hot', 0)} minutes to charge a pack instead of {n('chg_min_Gen1_cool', 0)}; Gen3 takes {n('chg_min_Gen3_hot', 0)}.",
    f"Empty shelves are a symptom: at the same station and temperature, an empty cabinet fails riders no more often (odds ratio {n('stock_mh_or', 2)}).",
    f"New riders with more than 20% failed swaps in their first two weeks left at {n('churn_highfail_pct')}%, against {n('churn_nofail_pct')}%.",
]

EXPLORER = """<div class="filters"><label>City <select id="fc"><option value="">All</option></select></label>
<label>Generation <select id="fg"><option value="">All</option></select></label>
<label><input type="checkbox" id="fa"> Only the April 2026 list</label></div>
<div class="two"><div class="tablewrap ex"><table id="ext"><thead><tr><th>Station</th><th>City</th><th>Gen</th><th>Opened</th><th>Site</th><th style="text-align:right">Failed, summer 2025</th></tr></thead><tbody></tbody></table></div>
<div class="panel"><h3 id="exh">Pick a station</h3><p id="exp">Click a row in the table.</p><svg id="exs" viewBox="0 0 520 300"></svg></div></div>"""

TRUST = [
    f"Every documented data issue checked, plus {n('issues_undocumented', 0)} the documentation does not mention, each with rows affected and its effect on a result.",
    "Every number is computed by a notebook that runs top to bottom from the organiser's files, and re-derived by independent tests.",
    "Out-of-sample checks: the summer 2024 rule on summer 2025, the churn model on riders who started in 2025, a placebo test for the pricing pilot.",
]

# Shared base CSS: only layout plumbing. Every colour, font, size, radius and shadow is a token set per direction.
BASE_CSS = """
*{box-sizing:border-box} html,body{margin:0;overflow-x:hidden;background:var(--page);color:var(--ink-2);font-family:var(--body);font-size:16px;line-height:1.5;-webkit-font-smoothing:antialiased}
a{color:inherit} svg{width:100%;height:auto;display:block} svg text{fill:var(--muted);font-family:var(--body);font-size:13px}
.two{display:grid;grid-template-columns:1fr 1fr;gap:24px}
.panel{background:var(--sheet);border:1px solid var(--line);border-radius:var(--r-card);padding:20px}
.panel h3{margin:0 0 4px;font-size:16px;font-weight:600;color:var(--ink)} .panel p{margin:0 0 10px;color:var(--muted);font-size:14px}
.filters{display:flex;flex-wrap:wrap;gap:10px 22px;margin:0 0 14px;font-size:14px} .filters select{font:inherit;margin-left:6px;padding:6px 8px;background:var(--sheet);color:var(--ink);border:1px solid var(--line-strong);border-radius:var(--r-control)}
.tablewrap{max-height:380px;overflow:auto;border:1px solid var(--line);border-radius:var(--r-card);background:var(--sheet)}
#ext td,#ext th{white-space:nowrap} #ext tbody tr{cursor:pointer} #ext tbody tr:hover,#ext tbody tr.sel{background:var(--sheet-2)} #ext tbody tr.hot td:first-child{box-shadow:inset 3px 0 0 var(--hot)}
table{width:100%;border-collapse:collapse;font-size:14px} td,th{text-align:left;padding:8px 10px;border-bottom:1px solid var(--line)} th{color:var(--muted);font-weight:500;background:var(--sheet);position:sticky;top:0}
.mono{font-variant-numeric:tabular-nums} .num{text-align:right;font-variant-numeric:tabular-nums;color:var(--ink);font-weight:500}
[data-motion=reduce] *{transition:none!important;animation:none!important}
@media (max-width:820px){.two{grid-template-columns:1fr}}
"""

CHART_JS = r"""
const css=v=>getComputedStyle(document.documentElement).getPropertyValue(v).trim();
const NS='http://www.w3.org/2000/svg';
function el(t,a,p){const e=document.createElementNS(NS,t);for(const k in a)e.setAttribute(k,a[k]);p.appendChild(e);return e}
function axes(svg,x0,x1,y0,y1,xt,yt,xl,yl,W=520,H=340,m={l:46,r:14,t:10,b:38}){
  const X=v=>m.l+(v-x0)/(x1-x0)*(W-m.l-m.r), Y=v=>H-m.b-(v-y0)/(y1-y0)*(H-m.t-m.b);
  xt.forEach(v=>{el('line',{x1:X(v),x2:X(v),y1:m.t,y2:H-m.b,stroke:css('--line')},svg);el('text',{x:X(v),y:H-m.b+16,'text-anchor':'middle'},svg).textContent=v});
  yt.forEach(v=>{el('line',{x1:m.l,x2:W-m.r,y1:Y(v),y2:Y(v),stroke:css('--line')},svg);el('text',{x:m.l-8,y:Y(v)+4,'text-anchor':'end'},svg).textContent=v});
  if(xl)el('text',{x:(W+m.l)/2,y:H-4,'text-anchor':'middle'},svg).textContent=xl;
  return [X,Y];
}
function drawBT(){const s=document.getElementById('bt');if(!s)return;const [X,Y]=axes(s,3,19,3,19,[4,8,12,16],[4,8,12,16],'summer 2024 (the rule)');
 el('line',{x1:X(3),y1:Y(3),x2:X(19),y2:Y(19),stroke:css('--muted'),'stroke-dasharray':'4 4'},s);
 DATA.groups.forEach(g=>{const r=Math.sqrt(g.attempts25)/18;el('circle',{cx:X(g.g24),cy:Y(g.g25),r,fill:g.hot?css('--hot'):css('--other'),'fill-opacity':.9,stroke:css('--mark-edge'),'stroke-width':g.hot?1:0},s);
  if(g.hot){const c=g.group.replace('Gen1 in ','');const o={'Delhi NCR':[-r-6,-14,'end'],'Jaipur':[0,r+16,'middle'],'Hyderabad':[-r-6,4,'end']}[c];const t=el('text',{x:X(g.g24)+o[0],y:Y(g.g25)+o[1],'text-anchor':o[2]},s);t.textContent=c;t.style.fill=css('--ink')}});}
function drawMech(){const s=document.getElementById('mech');if(!s)return;const bands=['<35','35-40','40-45','45+'];const [X,Y]=axes(s,0,3,30,170,[],[40,80,120,160],'cabinet temperature (°C)');
 bands.forEach((b,i)=>el('text',{x:X(i),y:340-38+16,'text-anchor':'middle'},s).textContent=b);
 [['Gen1','--hot'],['Gen2','--other'],['Gen3','--cool']].forEach(([g,c])=>{const pts=bands.map((b,i)=>{const d=DATA.mechanism.find(m=>m.gen==g&&m.band==b);return [X(i),Y(d.charge_min)]});
  el('polyline',{points:pts.map(p=>p.join(',')).join(' '),fill:'none',stroke:css(c),'stroke-width':3},s);pts.forEach(p=>el('circle',{cx:p[0],cy:p[1],r:4,fill:css(c)},s));
  const t=el('text',{x:pts[3][0]-8,y:pts[3][1]-10,'text-anchor':'end'},s);t.textContent=g;t.style.fill=css('--ink')});}
function drawChurn(){const s=document.getElementById('churn');if(!s)return;const W=520,H=300,m=36,bw=(W-2*m)/DATA.churn.length;const max=40;
 DATA.churn.forEach((c,i)=>{const h=(c.pct/max)*(H-80);const x=m+i*bw+10;
  el('rect',{x,y:H-40-h,width:bw-20,height:h,fill:(i>=2)?css('--hot'):css('--other'),rx:2},s);
  const v=el('text',{x:x+(bw-20)/2,y:H-46-h,'text-anchor':'middle'},s);v.textContent=c.pct+'%';v.style.fill=css('--ink');
  el('text',{x:x+(bw-20)/2,y:H-22,'text-anchor':'middle'},s).textContent=c.band==='none'?'no failures':c.band+' failed';});}
function explorer(){
 const ex=DATA.ex, M=DATA.months, fc=document.getElementById('fc'), fg=document.getElementById('fg'), fa=document.getElementById('fa'), tb=document.querySelector('#ext tbody');
 if(!tb)return;
 [...new Set(ex.map(r=>r.city))].sort().forEach(c=>fc.add(new Option(c,c)));
 [...new Set(ex.map(r=>r.gen))].sort().forEach(g=>fg.add(new Option(g,g)));
 function draw(r){
  const s=document.getElementById('exs'); s.innerHTML='';
  const g=DATA.gm[r.gen+'|'+r.city]||[]; const vals=r.m.concat(g).filter(v=>v!=null);
  const top=Math.ceil(Math.max(...vals,5)/5)*5; const yt=[]; for(let v=0;v<=top;v+=5)yt.push(v);
  const n=M.length; const [X,Y]=axes(s,0,n-1,0,top,[],yt,null,null,520,300,{l:40,r:12,t:10,b:30});
  M.forEach((m,i)=>{const mo=+m.slice(5);if([4,5,6].includes(mo))el('rect',{x:X(i)-((X(1)-X(0))/2),y:10,width:X(1)-X(0),height:260,fill:css('--shade'),opacity:.35},s);
   if(mo===1||i===0)el('text',{x:X(i),y:290,'text-anchor':'middle'},s).textContent=m});
  const line=(arr,col,w,dash)=>{const p=arr.map((v,i)=>v==null?null:[X(i),Y(v)]).filter(Boolean);if(p.length)el('polyline',{points:p.map(q=>q.join(',')).join(' '),fill:'none',stroke:col,'stroke-width':w,'stroke-dasharray':dash||''},s)};
  line(g,css('--other'),2,'4 3'); line(r.m,css('--hot'),2.5);
  document.getElementById('exh').textContent=r.id+', '+r.gen+' in '+r.city;
  document.getElementById('exp').textContent='Solid line: this station, % of attempts failed each month. Dashed: all '+r.gen+' stations in '+r.city+'. Shaded: April to June.'+(r.april?' On the April 2026 list, wave '+r.april+'.':'');
 }
 function render(){
  const rows=ex.filter(r=>(!fc.value||r.city===fc.value)&&(!fg.value||r.gen===fg.value)&&(!fa.checked||r.april)).sort((a,b)=>(b.s25??-1)-(a.s25??-1));
  tb.innerHTML='';
  rows.forEach(r=>{const tr=document.createElement('tr');if(r.april)tr.className='hot';
   tr.innerHTML=`<td class="mono">${r.id}</td><td>${r.city}</td><td>${r.gen}</td><td>${r.opened}</td><td>${r.site}</td><td class="num">${r.s25==null?'not open':r.s25+'%'}</td>`;
   tr.onclick=()=>{tb.querySelectorAll('tr').forEach(t=>t.classList.remove('sel'));tr.classList.add('sel');draw(r)};tb.appendChild(tr)});
  if(rows.length){tb.firstChild.classList.add('sel');draw(rows[0])}
  else{tb.innerHTML='<tr><td colspan="6">No station matches these filters. Clear a filter to see stations.</td></tr>';document.getElementById('exs').innerHTML='';
   document.getElementById('exh').textContent='No station selected';document.getElementById('exp').textContent='Pick a city and generation that have stations.'}
 }
 [fc,fg,fa].forEach(e=>e.onchange=render);
 // Every state can be opened directly: ?state=april | station&id=STN-... | empty | mechanism | default
 const q=new URLSearchParams(location.search), st=q.get('state');
 if(st==='april'){fa.checked=true}
 if(st==='empty'){fc.value='Mumbai';fg.value='Gen1';fa.checked=true}
 render();
 if(st==='station'&&q.get('id')){const r=ex.find(x=>x.id===q.get('id'));if(r){fc.value=r.city;render();const tr=[...tb.querySelectorAll('tr')].find(t=>t.textContent.startsWith(r.id));if(tr)tr.click()}}
 if(st&&st!=='default'&&st!=='mechanism')document.getElementById('explore').scrollIntoView();
}
function views(titles){
 document.querySelectorAll('[data-show]').forEach(b=>b.onclick=(e)=>{if(e)e.preventDefault();const v=b.dataset.show;
  document.querySelectorAll('[data-show]').forEach(x=>x.classList.toggle('on',x.dataset.show===v));
  document.querySelectorAll('#win .view').forEach(x=>x.hidden=x.dataset.view!==v);
  document.querySelectorAll('#win .steps').forEach(x=>x.hidden=x.dataset.for!==v);
  const t=document.getElementById('wtitle');if(t)t.textContent=titles[v][0];const s=document.getElementById('wstatus');if(s)s.textContent=titles[v][1];});
 if(new URLSearchParams(location.search).get('state')==='mechanism'){const b=document.querySelector('[data-show=mech]');if(b)b.click()}
}
drawBT();drawMech();drawChurn();explorer();
"""

VIEW_TITLES = json.dumps({"bt": ["Summer 2024 rule vs summer 2025", f"R² {R2} out of sample"],
                          "mech": ["Charge time by cabinet temperature", f"Same cabinet, odds ×{n('fe_or_hot_Gen1', 2)} when hot"]})

CHECK_ICON = '<svg viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="6.5"/><path d="M5 8.2l2 2 4-4.4"/></svg>'


FAVS = {"a": "data:image/svg+xml," + __import__("urllib.parse").parse.quote(mark("#a3e635", "#6e5dc6"))}


def shell(direction, title, fonts, css, body):
    return f"""<!doctype html><html lang="en" data-direction="{direction}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title><script>document.documentElement.dataset.motion=matchMedia("(prefers-reduced-motion: reduce)").matches?"reduce":"full"</script>
<link rel="icon" href="{FAVS[direction]}"><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="{fonts}" rel="stylesheet">
<style>{BASE_CSS}{css}</style></head><body>{body}
<script>const DATA={DATA_JS};{CHART_JS}views({VIEW_TITLES});</script></body></html>"""


# ---------------------------------------------------------------- A: Brainfish
def page_a():
    MARK = mark("#a3e635", "#6e5dc6")
    fonts = "https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,420&family=Geist:wght@400;500;600&display=swap"
    css = """
:root{ /* Brainfish, measured: page #fcfff7, ink #000/#262626, muted #737373, hairline #e5e5e5, panels #f4f5f0, lime #a3e635, lavender #6e5dc6/#352c63, green #1b7f46/#bce3ca, dark band #0b0b10 */
 --page:#fcfff7; --sheet:#ffffff; --sheet-2:#f4f5f0; --ink:#000000; --ink-2:#262626; --muted:#737373; --line:#e5e5e5; --line-strong:#262626; --r-card:10px; --r-control:4px;
 --hot:#0b0b10; --other:#c9c9c4; --cool:#1b7f46; --shade:#a3e635; --mark-edge:#a3e635;
 --display:'Fraunces',Georgia,serif; --body:'Geist',system-ui,sans-serif;
 --fs-display:clamp(40px,calc(40px + 38 * ((100vw - 375px) / 1065)),78px); --fs-h2:clamp(34px,calc(34px + 26 * ((100vw - 375px) / 1065)),60px);
}
.hero-bg{background:url(images/contours.webp) center -40px/1600px auto no-repeat}
.wrap{max-width:1392px;margin:0 auto;padding:0 24px}
.nav{display:flex;align-items:center;justify-content:space-between;height:67px;gap:16px}
.brand{display:inline-flex;align-items:center;gap:8px;font-weight:600;font-size:21px;letter-spacing:-.03em;color:#000;text-decoration:none} .brand svg{width:34px;height:34px}
.links{display:flex;gap:32px;margin-left:120px} .links a{color:#262626;text-decoration:none;font-size:17px}
.navr{display:flex;align-items:center;gap:22px} .navr .si{font-size:17px;text-decoration:none;color:#262626}
.btn{display:inline-flex;align-items:center;gap:8px;height:44px;padding:0 16px;background:#a3e635;color:#000;border:1px solid #262626;border-radius:4px;box-shadow:2px 2px 0 0 #262626;font:500 18px/1 var(--body);text-decoration:none}
.btn-nav{height:36px;font-size:16px;padding:0 12px}
.hero{padding:80px 0 0;text-align:center}
.badge{display:inline-flex;align-items:center;gap:10px;height:34px;padding:0 14px 0 4px;border:1px solid var(--line);border-radius:999px;background:#fff;color:#262626;font-size:14px;text-decoration:none}
.badge .tag{background:#a3e635;color:#000;border-radius:999px;padding:3px 10px;font-weight:600;font-size:13px}
h1{font-family:var(--display);font-size:var(--fs-display);font-weight:420;line-height:1;letter-spacing:-.034em;color:#000;margin:30px auto 0;max-width:12.5em}
.sub{max-width:31em;color:#262626;font-size:21px;line-height:1.52;margin:28px auto 30px}
.small{display:flex;justify-content:center;flex-wrap:wrap;gap:8px 28px;margin:22px 0 0;font-size:14px;color:#262626} .small span{display:inline-flex;align-items:center;gap:8px}
.small svg{width:16px;height:16px;fill:none;stroke:#262626;stroke-width:1.3}
.window{max-width:1312px;margin:64px auto 0;background:var(--sheet-2);border:1px solid #262626;border-radius:10px;box-shadow:6px 6px 0 0 #262626;text-align:left;overflow:hidden;display:grid;grid-template-columns:60px 1fr;grid-template-rows:auto 1fr}
.window-bar{grid-column:1/3;display:flex;justify-content:space-between;align-items:center;padding:14px 20px;font-size:15px;color:#5e5e5e}
.crumb{display:flex;align-items:center;gap:10px} .crumb b{color:#000;font-weight:600} .crumb i{width:1px;height:18px;background:var(--line)} .wm{display:inline-flex;align-items:center;gap:6px} .wm svg{width:22px;height:22px}
.status{display:inline-flex;align-items:center;gap:8px;padding:5px 12px;border-radius:999px;background:#ecf8ef;border:1px solid #bce3ca;color:#1b7f46;font-weight:500;font-size:14px} .status i{width:7px;height:7px;border-radius:50%;background:#1b7f46}
.rail{display:flex;flex-direction:column;align-items:center;gap:10px;padding:8px 0}
.rail button{width:38px;height:38px;border-radius:8px;border:0;background:transparent;display:grid;place-items:center;cursor:pointer;color:#262626}
.rail button.on{background:#a3e635;border:1px solid #262626}
.rail svg{width:18px;height:18px;fill:none;stroke:currentColor;stroke-width:1.5}
.window-body{display:grid;grid-template-columns:1.15fr 1fr;margin:0 20px 20px 0;background:#fff;border:1px solid #e6e6e1;border-radius:10px}
.view{padding:22px 26px} .axis-note{margin:0 0 8px;color:#737373;font-size:14px}
.steps{border-left:1px solid #e6e6e1;padding:26px 30px} .steps h3{margin:0 0 18px;font-size:17px;font-weight:600;color:#000;padding-bottom:16px;border-bottom:1px solid var(--line)}
.steps ol{list-style:none;margin:0;padding:0}
.steps li{position:relative;display:flex;justify-content:space-between;gap:16px;align-items:baseline;padding:0 0 22px 40px;font-size:16px}
.steps li::before{content:"";position:absolute;left:0;top:-2px;width:26px;height:26px;border-radius:50%;background:#111 url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'%3E%3Cpath d='M4.5 8.3l2.2 2.2 4.8-5' fill='none' stroke='white' stroke-width='1.8'/%3E%3C/svg%3E") center/14px no-repeat}
.steps li::after{content:"";position:absolute;left:12.5px;top:24px;bottom:-2px;width:1.5px;background:#111} .steps li:last-child::after{display:none}
.steps li b{font-weight:500;color:#000} .steps li span{flex:none;color:#737373;font-size:14px}
.steps .foot{display:flex;gap:10px;align-items:baseline;margin:6px 0 0;padding-top:16px;border-top:1px solid var(--line);font-size:15px;color:#000;font-weight:500} .steps .foot i{flex:none;width:8px;height:8px;border-radius:50%;background:#1b7f46}
.tryrow{display:flex;flex-wrap:wrap;align-items:center;gap:10px;max-width:1312px;margin:22px auto 0;font-size:14px;color:#262626}
.pill{display:inline-flex;align-items:center;height:38px;padding:0 14px;border:1px solid #d4d4d4;border-radius:999px;background:#fff;color:#000;font:500 14px var(--body);cursor:pointer;text-decoration:none} .pill.on{border-color:#262626;box-shadow:2px 2px 0 0 #262626}
/* section 02: logo-stat band -> our four numbers */
.band{background:#fff;border-top:1px solid var(--line);border-bottom:1px solid var(--line);margin-top:96px}
.stats{display:grid;grid-template-columns:repeat(4,1fr);max-width:1392px;margin:0 auto}
.stat{padding:56px 26px} .stat+.stat{border-left:1px solid var(--line)} .stat .v{font-family:var(--display);font-size:var(--fs-h2);font-weight:420;letter-spacing:-.034em;line-height:1;color:#000} .stat .l{font-size:15px;color:#262626;margin-top:14px}
/* section 03: split, big serif h2 left + chips -> what to fund */
.sec{padding:122px 0} .sec h2{font-family:var(--display);font-weight:420;font-size:var(--fs-h2);letter-spacing:-.03em;line-height:1.05;color:#000;margin:0 0 18px;max-width:14em}
.lede{font-size:17px;color:#262626;max-width:36em;margin:0 0 34px}
.verdicts{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:14px}
.verdict{background:#fff;border:1px solid #e6e6e1;border-radius:10px;padding:20px}
.verdict .p{font-weight:600;color:#000} .verdict .vv{display:inline-block;margin:10px 0;padding:2px 10px;border-radius:999px;font-size:13px;font-weight:600}
.verdict .vv.no{background:#f1eefc;color:#352c63} .verdict .vv.yes{background:#ecf8ef;color:#1b7f46} .verdict .d{font-size:15px} .verdict .o{font-size:14px;color:#737373;margin-top:12px}
/* section 04: dark band #0b0b10 with light cards -> April list + churn */
.dark{background:#0b0b10;color:#f5f4ff;--line:#2a2a36;--sheet:#131320;--sheet-2:#1a1a2a;--ink:#f5f4ff;--ink-2:#f5f4ff;--muted:#a3a3b8;--other:#4a4a5e;--hot:#a3e635}
.dark h2{color:#f5f4ff} .dark .lede{color:#d6d4ea} .dark .panel,.dark .tablewrap{background:#131320;border-color:#2a2a36} .dark td,.dark th{border-color:#2a2a36} .dark th{background:#131320}
/* section 05: light split with window -> station explorer; 08: footer */
.trust{display:grid;grid-template-columns:repeat(3,1fr);gap:24px;font-size:15px} .trust div{border-top:1px solid #262626;padding-top:14px}
footer{padding:40px 0 64px;color:#737373;font-size:14px;border-top:1px solid var(--line)}
@media (max-width:820px){.links,.navr .si{display:none} .window{grid-template-columns:1fr} .rail{flex-direction:row;justify-content:center;grid-row:2} .window-bar{flex-wrap:wrap} .crumb>b.wm,.crumb>i{display:none}
 .window-body{grid-template-columns:1fr;margin:0 10px 10px} .steps{border-left:0;border-top:1px solid #e6e6e1;padding:20px} .stats{grid-template-columns:1fr 1fr} .stat:nth-child(3){border-left:0} .stat{padding:28px 16px} .sub{font-size:18px} .trust{grid-template-columns:1fr} .sec{padding:72px 0}}
"""
    rail = (f'<nav class="rail" aria-label="Views"><button class="on" data-show="bt" title="Back-test"><svg viewBox="0 0 20 20"><path d="M3 17L17 3"/><circle cx="6" cy="13" r="1.8"/><circle cx="13" cy="6" r="2.4"/></svg></button>'
            f'<button data-show="mech" title="Heat mechanism"><svg viewBox="0 0 20 20"><path d="M10 3v9"/><circle cx="10" cy="14.5" r="3"/><path d="M7.5 5h-2M7.5 8h-2"/></svg></button>'
            f'<button onclick="location.hash=\'explore\'" title="Stations"><svg viewBox="0 0 20 20"><rect x="4" y="3" width="12" height="14" rx="2"/><path d="M4 7h12M7 10.5h6M7 13.5h6"/></svg></button></nav>')
    stats = "".join(f'<div class="stat"><div class="v">{v}</div><div class="l">{html.escape(l)}</div></div>' for v, l in STATS)
    verdicts = "".join(
        f'<div class="verdict"><div class="p">{html.escape(v["proposal"])}</div><span class="vv {"no" if v["verdict"].startswith(("No", "Not")) else "yes"}">{html.escape(v["verdict"])}</span>'
        f'<div class="d">{html.escape(v["do this instead"])}</div><div class="o">Owner: {html.escape(v["owner"])}<br>Confidence: {html.escape(v["confidence"])}</div></div>' for v in VERDICTS)
    body = f"""<div class="hero-bg"><div class="wrap">
<header class="nav"><a class="brand" href="#">{MARK}<span>Next April</span></a>
<nav class="links"><a href="#win">Why</a><a href="#fund">What to fund</a><a href="#explore">Stations</a><a href="#trust">How it's checked</a></nav>
<div class="navr"><a class="si" href="Next_April_report.pdf">Report</a><a class="btn btn-nav" href="#explore">Look up a station <span aria-hidden="true">&rarr;</span></a></div></header>
<div class="hero">
<a class="badge" href="#win"><span class="tag">Back-tested</span>A summer 2024 rule, scored on summer 2025 <span aria-hidden="true">&rarr;</span></a>
<h1>The same {B36} cabinets will fail next April.</h1>
<p class="sub">Every April to June, the oldest cabinets in VoltRelay&rsquo;s EV battery-swap network overheat in three cities and turn delivery riders away. Fix those {B36} first.</p>
<a class="btn" href="#explore">Look up a station <span aria-hidden="true">&rarr;</span></a>
<div class="small"><span>{CHECK_ICON}Runs top to bottom in Colab</span><span>{CHECK_ICON}Every number re-checked by tests</span></div>
<div class="window" id="win"><div class="window-bar"><span class="crumb"><b class="wm">{MARK}Next April</b><i></i>Back-tests<span aria-hidden="true">&rsaquo;</span><b id="wtitle">Summer 2024 rule vs summer 2025</b></span><span class="status"><i></i><span id="wstatus">R² {R2} out of sample</span></span></div>
{rail}<div class="window-body"><div class="view" data-view="bt"><p class="axis-note">Failed attempts, % of attempts. Each bubble is one charger generation in one city; black is Gen1 in the three hottest cities.</p><svg id="bt" viewBox="0 0 520 340"></svg></div>
<div class="view" data-view="mech" hidden><p class="axis-note">Average minutes to charge a pack, by cabinet temperature.</p><svg id="mech" viewBox="0 0 520 340"></svg></div>
<div class="steps" data-for="bt"><h3>How the rule works</h3><ol>{STEPS_BT}</ol><p class="foot"><i></i>The {B36} Gen1 stations in the hottest cities failed on {n("hot_gen1_fail24_pct")}% of summer attempts in 2024 and {n("hot_gen1_fail25_pct")}% in 2025.</p></div>
<div class="steps" data-for="mech" hidden><h3>Why they fail</h3><ol>{STEPS_MECH}</ol><p class="foot"><i></i>Fix the cabinet, not the stock.</p></div></div></div>
<div class="tryrow"><span>Try another view</span><button class="pill on" data-show="bt">Back-test</button><button class="pill" data-show="mech">Heat mechanism</button><a class="pill" href="#explore">One station</a></div>
</div></div></div>
<div class="band"><div class="stats">{stats}</div></div>
<div class="wrap"><section class="sec" id="fund"><h2>Fund the cabinets, not more stations.</h2><p class="lede">A verdict on each of the four budget proposals, with an owner and a confidence level. The data is the organisers&rsquo; synthetic VoltRelay dataset.</p><div class="verdicts">{verdicts}</div></section></div>
<div class="dark"><div class="wrap"><section class="sec"><h2>The April 2026 list.</h2><p class="lede">Wave 1: Gen1 in Jaipur and Delhi NCR. Wave 2: Gen1 in Hyderabad. On the right, why it matters for new riders.</p>
<div class="two"><div class="tablewrap"><table><tr><th>Wave</th><th>Station</th><th>City</th><th style="text-align:right">Failed, summer 2025</th></tr>{STATIONS_ROWS}</table></div>
<div class="panel"><h3>New riders who hit failures leave</h3><p>Churn by the share of a new rider's attempts that failed in their first 14 days.</p><svg id="churn" viewBox="0 0 520 300"></svg></div></div></section></div></div>
<div class="wrap"><section class="sec" id="explore"><h2>Look up any station.</h2><p class="lede">Filter, then pick a station to see its monthly failure rate against its charger generation in its city.</p>{EXPLORER}</section>
<section class="sec" id="trust" style="padding-top:0"><h2>Why the numbers hold.</h2><div class="trust">{"".join(f"<div>{t}</div>" for t in TRUST)}</div></section>
<footer>Synthetic VoltRelay dataset provided by Gradient Learnings. AI coding assistance used; every number checked by the notebook, tests and a number-tracing script.</footer></div>"""
    return shell("a", "Next April", fonts, css, body)


if __name__ == "__main__":
    out = os.path.join(ROOT, "site")
    os.makedirs(out, exist_ok=True)
    open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(page_a())
    __import__("shutil").copy(os.path.join(ROOT, "report", "Next_April_report.pdf"), os.path.join(out, "Next_April_report.pdf"))
    print("built site/index.html")
