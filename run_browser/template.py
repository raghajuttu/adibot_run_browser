"""The dashboard page: all HTML, CSS and JS live here and nowhere else.

Edit the look, the layout, or the interactions in this file. It knows nothing
about CSVs — builder.py hands it a finished JSON blob and a few display
options, and render() splices them in.
"""

import json

from .config import Options


def render(data: dict, cfg: Options) -> str:
    html = TEMPLATE
    html = html.replace("__TITLE__", cfg.page_title)
    html = html.replace("__HI_ERR__", str(cfg.hi_error_mrad))
    html = html.replace("__HI_NM__", str(cfg.hi_contact_nm))
    html = html.replace("__V_SPLICE__", str(cfg.verdict_splice_ratio_max))
    html = html.replace("__V_DEPTH__", str(cfg.verdict_depth_max_steps))
    # "</" inside a string value (a note, a task description) would terminate
    # the <script> block early; escape it inside the JSON payload.
    payload = json.dumps(data, separators=(",", ":")).replace("</", "<\\/")
    html = html.replace("__DATA__", payload)
    return html


TEMPLATE = r"""<meta charset="utf-8">
<title>__TITLE__</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@600;700;800&family=IBM+Plex+Mono:wght@400;500;600&display=swap">
<style>
:root{--ground:#FBFCFD;--surface:#F2F5F7;--ink:#1C2733;--muted:#5A6B7A;--hairline:#DCE3E8;
--accent:#0E7C86;--accent-soft:#E3F1F2;--warn:#A8600F;--warn-soft:#F7EBDB;--good:#3D7A46;
--cmd:#d62728;--act:#1f77b4;--b2:#8a5fbf;
--mono:"IBM Plex Mono",ui-monospace,Consolas,monospace;--disp:"Archivo","Helvetica Neue",Arial,sans-serif}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--ground:#10161C;--surface:#171F27;--ink:#D8E1E8;--muted:#8A99A6;--hairline:#2A3540;--accent:#41B6C0;--accent-soft:#14333A;--warn:#E09A3E;--warn-soft:#3A2A14;--good:#6FB479;--cmd:#ff6b6b;--act:#5aa9e6;--b2:#b48be0}}
:root[data-theme="dark"]{--ground:#10161C;--surface:#171F27;--ink:#D8E1E8;--muted:#8A99A6;--hairline:#2A3540;--accent:#41B6C0;--accent-soft:#14333A;--warn:#E09A3E;--warn-soft:#3A2A14;--good:#6FB479;--cmd:#ff6b6b;--act:#5aa9e6;--b2:#b48be0}
*{box-sizing:border-box}
body{margin:0;background:var(--ground);color:var(--ink);font-family:var(--disp);font-size:14px}
.layout{display:flex;min-height:100vh}
aside{width:230px;flex:0 0 230px;border-right:1px solid var(--hairline);padding:14px 12px;position:sticky;top:0;height:100vh;overflow-y:auto;background:var(--surface)}
main{flex:1;padding:16px 20px 60px;min-width:0}
h1{font-size:16px;font-weight:800;letter-spacing:-.01em;margin:0 0 2px}
.sub{font-family:var(--mono);font-size:10px;color:var(--muted);margin-bottom:12px}
.grp{font-family:var(--mono);font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);margin:14px 0 5px}
.runbtn{display:block;width:100%;text-align:left;font-family:var(--mono);font-size:11.5px;padding:4px 8px;margin:1px 0;border:1px solid transparent;background:none;color:var(--ink);cursor:pointer;border-radius:3px}
.runbtn:hover{background:var(--accent-soft)}
.runbtn.sel{background:var(--accent);color:#fff}
.runbtn.selB{background:var(--b2);color:#fff}
select,.seg button{font-family:var(--mono);font-size:11.5px;background:var(--ground);color:var(--ink);border:1px solid var(--hairline);border-radius:3px;padding:4px 6px}
select{width:100%}
.seg{display:flex;flex-wrap:wrap;gap:4px}
.seg button{cursor:pointer;padding:4px 9px}
.seg button.on{background:var(--accent);border-color:var(--accent);color:#fff}
label.chk{display:flex;gap:6px;align-items:center;font-family:var(--mono);font-size:11px;color:var(--muted);margin:4px 0;cursor:pointer}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 12px}
.chip{font-family:var(--mono);font-size:11px;background:var(--surface);border:1px solid var(--hairline);border-radius:3px;padding:3px 9px}
.chip b{color:var(--accent);font-weight:600}
.chip.b b{color:var(--b2)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:10px}
.panel{background:var(--surface);border:1px solid var(--hairline);border-radius:4px;padding:6px 8px 2px;cursor:pointer}
.panel:hover{border-color:var(--accent)}
.panel .ttl{font-family:var(--mono);font-size:10.5px;color:var(--muted);margin-bottom:2px}
canvas{width:100%;display:block}
h2{font-size:14px;font-weight:700;margin:26px 0 8px}
table{border-collapse:collapse;font-family:var(--mono);font-size:11.5px;width:100%}
th{text-align:left;font-size:9.5px;letter-spacing:.07em;text-transform:uppercase;color:var(--muted);font-weight:500;padding:4px 12px 4px 0;border-bottom:1px solid var(--ink);white-space:nowrap}
td{padding:3px 12px 3px 0;border-bottom:1px solid var(--hairline);white-space:nowrap;font-variant-numeric:tabular-nums}
td.r,th.r{text-align:right}
td.hi{color:var(--warn);font-weight:600}
.cols{display:flex;gap:26px;flex-wrap:wrap}
.cols>div{flex:1;min-width:300px}
.legend{font-family:var(--mono);font-size:10.5px;color:var(--muted);margin:6px 0 10px}
.legend i{display:inline-block;width:14px;height:3px;vertical-align:middle;margin:0 4px 0 10px}
.modal{position:fixed;inset:0;background:rgba(0,0,0,.5);display:none;align-items:center;justify-content:center;z-index:10}
.modal.on{display:flex}
.mbox{background:var(--ground);border:1px solid var(--hairline);border-radius:6px;padding:14px;width:min(1100px,94vw)}
.mbox .ttl{font-family:var(--mono);font-size:12px;margin-bottom:6px;display:flex;justify-content:space-between}
.mbox button{font-family:var(--mono);background:none;border:1px solid var(--hairline);color:var(--ink);border-radius:3px;cursor:pointer;padding:2px 10px}
.note{font-family:var(--mono);font-size:10.5px;color:var(--muted);margin-top:4px}
@media (max-width:760px){.layout{flex-direction:column}aside{width:100%;height:auto;position:static;flex:none}}
</style>
<div class="layout">
<aside>
  <h1>__TITLE__</h1>
  <div class="sub" id="gen"></div>
  <div class="grp">Page</div>
  <div class="seg" id="pages">
    <button data-p="signals" class="on">signals</button>
    <button data-p="matrix">run matrix</button>
  </div>
  <div class="grp">Run</div>
  <div id="runlist"></div>
  <div class="grp">Compare with</div>
  <select id="cmpsel"><option value="">&mdash; none &mdash;</option></select>
  <div class="grp">Signal</div>
  <div class="seg" id="views">
    <button data-v="track" class="on">position</button>
    <button data-v="err">error</button>
    <button data-v="vel">velocity</button>
    <button data-v="eff">effort</button>
  </div>
  <div class="grp">Joints</div>
  <div class="seg" id="sides">
    <button data-s="all" class="on">all</button>
    <button data-s="left">left</button>
    <button data-s="right">right</button>
  </div>
  <label class="chk"><input type="checkbox" id="cbBounds"> chunk boundaries</label>
  <label class="chk"><input type="checkbox" id="cbGrasp" checked> grasp shading</label>
</aside>
<main>
  <div id="pageSignals">
    <div class="chips" id="chips"></div>
    <div class="legend" id="legend"></div>
    <div class="grid" id="grid"></div>
    <div class="cols">
      <div><h2>Tracking (mrad)</h2><div id="statsbox"></div>
           <h2>Run facts</h2><div id="factsbox"></div></div>
      <div><h2>Chunk profile</h2><div id="profbox"></div>
           <h2>Contacts</h2><div id="ctcbox"></div>
           <h2>Grasps</h2><div id="graspbox"></div></div>
    </div>
  </div>
  <div id="pageMatrix" style="display:none">
    <h2 style="margin-top:0">Run matrix</h2>
    <div class="note" style="margin-bottom:8px">One row per run: configuration (from the .meta.json sidecar) + measured behaviour. Verdicts: a run failing any chip is not a valid comparison point.</div>
    <div class="tblwrap" style="overflow-x:auto"><div id="matrixbox"></div></div>
    <div class="cols" style="margin-top:18px">
      <div><h2>Splice ratio vs replan cycle</h2><div class="panel" style="cursor:default"><canvas id="sc1" height="260"></canvas></div></div>
      <div><h2>Grasp success vs executed depth p95</h2><div class="panel" style="cursor:default"><canvas id="sc2" height="260"></canvas></div></div>
    </div>
  </div>
</main>
</div>
<div class="modal" id="modal"><div class="mbox">
  <div class="ttl"><span id="mttl"></span><button onclick="document.getElementById('modal').classList.remove('on')">close</button></div>
  <div class="panel" style="cursor:default"><canvas id="mcanvas" height="420"></canvas></div>
</div></div>
<script>
const DATA=__DATA__;
const HI_ERR=__HI_ERR__, HI_NM=__HI_NM__;
const V_SPLICE=__V_SPLICE__, V_DEPTH=__V_DEPTH__;
const runs=DATA.runs, names=Object.keys(runs);
let runA=names[0], runB="", view="track", side="all", page="signals";
const dash=v=>(v==null||v==="")?"—":v;
const esc=s=>String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
const $=id=>document.getElementById(id);
$("gen").textContent=names.length+" run"+(names.length===1?"":"s")+" · built "+DATA.generated;

function css(v){return getComputedStyle(document.documentElement).getPropertyValue(v).trim()}
function joints(){
  const all=runs[runA].joints;
  return side==="all"?all:all.filter(j=>j.includes(side));
}
function short(j){return j.replace("openarm_","").replace("_joint"," j").replace("finger j1","grip")}

function buildSidebar(){
  const rl=$("runlist"); rl.innerHTML="";
  names.forEach(n=>{
    const b=document.createElement("button");
    b.className="runbtn"+(n===runA?" sel":"")+(n===runB?" selB":"");
    b.textContent=n; b.onclick=()=>{runA=n; if(runB===n) runB=""; render()};
    rl.appendChild(b);
  });
  const cs=$("cmpsel"); cs.innerHTML='<option value="">&mdash; none &mdash;</option>';
  names.filter(n=>n!==runA).forEach(n=>{
    const o=document.createElement("option"); o.value=n; o.textContent=n;
    if(n===runB)o.selected=true; cs.appendChild(o);
  });
}
$("cmpsel").onchange=e=>{runB=e.target.value; render()};
document.querySelectorAll("#views button").forEach(b=>b.onclick=()=>{view=b.dataset.v; render()});
document.querySelectorAll("#sides button").forEach(b=>b.onclick=()=>{side=b.dataset.s; render()});
document.querySelectorAll("#pages button").forEach(b=>b.onclick=()=>{page=b.dataset.p; render()});
$("cbBounds").onchange=render; $("cbGrasp").onchange=render;

function seriesFor(run,j){
  const tr=runs[run].traces[j];
  if(!tr)return[];
  if(view==="track")return[{d:tr.act,c:css("--act"),w:1.2},{d:tr.cmd,c:css("--cmd"),w:1}];
  const key=view; // err | vel | eff
  if(!tr[key])return[];
  return[{d:tr[key],c:css("--act"),w:view==="err"?1.2:1,zero:1}];
}
function drawPanel(cv,j,big){
  const dpr=window.devicePixelRatio||1, W=cv.clientWidth, H=big?420:150;
  cv.width=W*dpr; cv.height=H*dpr; cv.style.height=H+"px";
  const g=cv.getContext("2d"); g.scale(dpr,dpr);
  const padL=44,padR=6,padT=6,padB=16, iw=W-padL-padR, ih=H-padT-padB;
  let sers=seriesFor(runA,j).map(s=>({...s,run:runA}));
  if(runB) sers=sers.concat(
    seriesFor(runB,j).map(s=>({...s,run:runB,c:s.c===css("--cmd")?css("--warn"):css("--b2"),dash:1})));
  if(!sers.length){g.fillStyle=css("--muted");g.font="10px sans-serif";
    g.fillText("no data for this signal",padL,H/2);return}
  let xmax=0,ymin=Infinity,ymax=-Infinity;
  sers.forEach(s=>{const[t,y]=s.d; if(t.length)xmax=Math.max(xmax,t[t.length-1]);
    for(const v of y){if(v<ymin)ymin=v; if(v>ymax)ymax=v}});
  if(!isFinite(ymin)){ymin=-1;ymax=1}
  if(sers.some(s=>s.zero)){ymin=Math.min(ymin,0);ymax=Math.max(ymax,0)}
  if(ymax-ymin<1e-9){ymax+=1;ymin-=1}
  if(xmax<=0)xmax=1;
  const pad=(ymax-ymin)*.06; ymin-=pad; ymax+=pad;
  const X=t=>padL+iw*t/xmax, Y=v=>padT+ih*(1-(v-ymin)/(ymax-ymin));
  if($("cbGrasp").checked&&runs[runA].grasps[j]){
    g.fillStyle=css("--good"); g.globalAlpha=.15;
    runs[runA].grasps[j].forEach(([a,b])=>g.fillRect(X(a),padT,Math.max(X(b)-X(a),2),ih));
    g.globalAlpha=1;
  }
  if($("cbBounds").checked){
    g.strokeStyle=css("--cmd"); g.globalAlpha=.18; g.lineWidth=.5; g.beginPath();
    runs[runA].bounds.forEach(t=>{g.moveTo(X(t),padT); g.lineTo(X(t),padT+ih)});
    g.stroke(); g.globalAlpha=1;
  }
  if(ymin<0&&ymax>0){g.strokeStyle=css("--hairline");g.lineWidth=1;g.beginPath();g.moveTo(padL,Y(0));g.lineTo(W-padR,Y(0));g.stroke()}
  sers.forEach(s=>{
    const[t,y]=s.d; g.strokeStyle=s.c; g.lineWidth=s.w; g.setLineDash(s.dash?[4,3]:[]);
    g.beginPath();
    for(let i=0;i<t.length;i++){const x=X(t[i]),yy=Y(y[i]); i?g.lineTo(x,yy):g.moveTo(x,yy)}
    g.stroke(); g.setLineDash([]);
  });
  g.fillStyle=css("--muted"); g.font="9px "+css("--mono").split(",")[0];
  g.fillText(ymax.toFixed(2),2,padT+8); g.fillText(ymin.toFixed(2),2,padT+ih);
  g.fillText(Math.round(xmax)+"s",W-padR-22,H-4); g.fillText("0",padL,H-4);
}
function metaChip(name,cls){
  const r=runs[name], m=r.meta, sc=r.schedule||{}, sm=r.smooth||{}, cfg=r.cfg;
  const lat=m.lat_p50==null?"":` · lat p50 <b>${m.lat_p50}ms</b>`;
  let mode="";
  if(cfg) mode=` · ${cfg.prefetch_enable?"prefetch":"blocking"}${cfg.rtc_enable?"+RTC":""}`;
  else if(m.stalled_run!=null) mode=` · ${m.stalled_run?"blocking?":"prefetch?"}`;
  const depth=sc.depth_p95!=null?` · depth p95 <b>${sc.depth_p95}</b>`:"";
  const spl=sm.splice_ratio!=null?` · splice <b>×${sm.splice_ratio}</b>`:"";
  const st=sc.stall_count!=null?` · stalls ${sc.stall_count}`:"";
  return `<span class="chip ${cls}"><b>${esc(name)}</b> · ${m.dur_s}s · ${m.chunks} chunks${mode}${lat}${depth}${spl}${st}</span>`;
}
function graspSummary(r){
  // only attempts whose outcome was measurable count toward the rate
  const ev=r.grasp_events||{};
  let att=0,succ=0;
  Object.values(ev).forEach(list=>list.forEach(e=>{
    if(e.success!=null){att++; if(e.success)succ++}}));
  return {att,succ};
}
function isBlocking(r){
  return r.cfg?!r.cfg.prefetch_enable:!!(r.meta&&r.meta.stalled_run);
}
function verdicts(r){
  const sc=r.schedule||{}, sm=r.smooth||{}, vi=r.violations||{};
  const out=[];
  // a blocking run stalls at every boundary by design — the stalls verdict
  // only applies where a stall means starvation (prefetch runs)
  if(sc.stall_count!=null&&!isBlocking(r))out.push({k:"stalls 0",ok:sc.stall_count===0});
  if(sm.splice_ratio!=null)out.push({k:"splice <"+V_SPLICE,ok:sm.splice_ratio<V_SPLICE});
  if(sc.depth_p95!=null)out.push({k:"depth <"+V_DEPTH,ok:sc.depth_p95<V_DEPTH});
  const v=Math.max(vi.left||0,vi.right||0);
  if(vi.left!=null||vi.right!=null)out.push({k:"limits 0",ok:v===0});
  return out;
}
function render(){
  buildSidebar();
  document.querySelectorAll("#views button").forEach(b=>b.classList.toggle("on",b.dataset.v===view));
  document.querySelectorAll("#sides button").forEach(b=>b.classList.toggle("on",b.dataset.s===side));
  document.querySelectorAll("#pages button").forEach(b=>b.classList.toggle("on",b.dataset.p===page));
  document.getElementById("pageSignals").style.display=page==="signals"?"":"none";
  document.getElementById("pageMatrix").style.display=page==="matrix"?"":"none";
  if(page==="matrix"){renderMatrix();return}
  $("chips").innerHTML=metaChip(runA,"")+(runB?metaChip(runB,"b"):"");
  const unit=view==="track"?"rad":view==="err"?"mrad":view==="vel"?"rad/s":"Nm";
  let lg=`<b>${unit}</b>`;
  if(view==="track")lg+=`<i style="background:${css("--act")}"></i>actual<i style="background:${css("--cmd")}"></i>commanded`;
  else lg+=`<i style="background:${css("--act")}"></i>${runA}`;
  if(runB)lg+=`<i style="background:${css("--b2")}"></i>${runB} (dashed)`;
  $("legend").innerHTML=lg;
  const grid=$("grid"); grid.innerHTML="";
  joints().forEach(j=>{
    const p=document.createElement("div"); p.className="panel";
    p.innerHTML=`<div class="ttl">${short(j)}</div>`;
    const cv=document.createElement("canvas"); p.appendChild(cv); grid.appendChild(p);
    p.onclick=()=>{$("modal").classList.add("on"); $("mttl").textContent=short(j)+" — "+view;
      requestAnimationFrame(()=>drawPanel($("mcanvas"),j,true))};
    requestAnimationFrame(()=>drawPanel(cv,j,false));
  });
  renderTables();
}
function statTable(run){
  const s=runs[run].stats.filter(r=>side==="all"||r.j.includes(side));
  let h=`<table><tr><th>joint</th><th class="r">p50</th><th class="r">p95</th><th class="r">lag ms</th><th class="r">mid</th><th class="r">bnd</th></tr>`;
  s.forEach(r=>{h+=`<tr><td>${short(r.j)}</td><td class="r ${r.p50>HI_ERR?'hi':''}">${r.p50}</td><td class="r">${r.p95}</td><td class="r">${r.lag==null?"—":r.lag}</td><td class="r">${r.mid==null?"—":r.mid}</td><td class="r">${r.bnd==null?"—":r.bnd}</td></tr>`});
  return h+"</table>";
}
function renderTables(){
  let sb=`<div class="note">${runA}</div>`+statTable(runA);
  if(runB)sb+=`<div class="note" style="margin-top:10px">${runB}</div>`+statTable(runB);
  $("statsbox").innerHTML=sb;
  const p=runs[runA].profile;
  let ph=`<table><tr><th class="r">step</th><th class="r">err mrad</th><th class="r">cmd step</th>`;
  if(runB)ph+=`<th class="r">err (B)</th><th class="r">step (B)</th>`;
  ph+=`</tr>`;
  const pb=runB?runs[runB].profile:null;
  // iterate the union of both runs' steps, so a longer horizon in either run
  // (e.g. execution_horizon 25 vs 16) is fully shown
  const steps=[...new Set([...p.k,...(pb?pb.k:[])])].sort((a,b)=>a-b);
  const ia=Object.fromEntries(p.k.map((k,i)=>[k,i]));
  const ib=pb?Object.fromEntries(pb.k.map((k,i)=>[k,i])):{};
  steps.forEach(k=>{
    const i=ia[k], j=ib[k];
    ph+=`<tr><td class="r">${k}</td><td class="r">${i==null?"—":(p.err[i]??"—")}</td><td class="r">${i==null?"—":(p.step[i]??"—")}</td>`;
    if(pb)ph+=`<td class="r">${j==null?"—":(pb.err[j]??"—")}</td><td class="r">${j==null?"—":(pb.step[j]??"—")}</td>`;
    ph+=`</tr>`});
  $("profbox").innerHTML=ph+"</table>";
  const ct=runs[runA].contacts;
  let ch=ct.length?`<table><tr><th class="r">t (s)</th><th class="r">dur ms</th><th>joint</th><th class="r">peak Nm</th></tr>`:"<div class='note'>none detected</div>";
  ct.slice(0,20).forEach(e=>{ch+=`<tr><td class="r">${e.t}</td><td class="r">${e.dur}</td><td>${short(e.j)}</td><td class="r ${Math.abs(e.nm)>HI_NM?'hi':''}">${e.nm}</td></tr>`});
  if(ct.length)ch+="</table>"+(ct.length>20?`<div class="note">+${ct.length-20} more</div>`:"");
  $("ctcbox").innerHTML=ch;
  const gr=runs[runA].grasps;
  let gh="";
  const fingers=Object.keys(gr);
  if(!fingers.length)gh="<div class='note'>no gripper columns</div>";
  fingers.forEach(n=>{
    const sp=gr[n];
    gh+=`<div class="note">${short(n)} held: ${sp.length?sp.map(([a,b])=>a+"–"+b+"s").join(", "):"never"}</div>`;
  });
  const ge=runs[runA].grasp_events||{};
  Object.keys(ge).forEach(n=>{
    ge[n].forEach(e=>{
      const ok=e.success==null?"?":(e.success?"✓ held":"✗ air");
      const ov=e.in_overlap==null?"":(e.in_overlap?" · in RTC overlap":" · outside overlap");
      gh+=`<div class="note">${short(n)} close @ ${e.t}s · step ${e.hi} · rise ${dash(e.rise_ms)}ms · ${ok}${ov}</div>`;
    });
  });
  $("graspbox").innerHTML=gh;

  // Run facts: scheduling, smoothness, safety — degrade to "—" for old logs.
  const sc=runs[runA].schedule||{}, sm=runs[runA].smooth||{}, vi=runs[runA].violations||{}, cfg=runs[runA].cfg;
  let fh="<table>";
  const row=(k,v)=>`<tr><td>${k}</td><td class="r">${dash(v)}</td></tr>`;
  fh+=row("replan cycle (steps, p50/p95)",sc.cycle_p50!=null?`${sc.cycle_p50} / ${sc.cycle_p95}`:null);
  fh+=row("skip on arrival (p50)",sc.skip_p50!=null?sc.skip_p50+(sc.skip_logged_p50!=null?` (logged ${sc.skip_logged_p50})`:""):null);
  fh+=row("executed depth (p50/p95/max)",sc.depth_p50!=null?`${sc.depth_p50} / ${sc.depth_p95} / ${sc.depth_max}`:null);
  fh+=row("server chunk length (p50)",sc.chunk_len_p50);
  fh+=row("stalls >100ms / time stalled",sc.stall_count!=null?`${sc.stall_count} / ${(100*(sc.stalled_frac||0)).toFixed(1)}%`:null);
  fh+=row("starved ticks (buffer=0)",sc.starved_ticks);
  fh+=row("effective rate (Hz)",sc.effective_hz);
  fh+=row("RTC applied (fraction of chunks)",sc.rtc_applied_frac);
  fh+=row("cmd step within / at splice (mrad)",sm.step_within_p50!=null?`${sm.step_within_p50} / ${dash(sm.step_splice_p50)}`:null);
  fh+=row("splice ratio",sm.splice_ratio!=null?`×${sm.splice_ratio}${sm.splice_ratio>=V_SPLICE?" ⚠":""}${runs[runA].meta.stalled_run?" (spans a stall — compare with blocking runs only)":""}`:null);
  fh+=row("splice p95 / max (mrad)",sm.splice_p95!=null?`${sm.splice_p95} / ${sm.splice_max} (chunk ${sm.splice_max_seq})`:null);
  fh+=row("cmd jerk within / at splice",sm.jerk_within_p50!=null?`${sm.jerk_within_p50} / ${dash(sm.jerk_splice_p50)}`:null);
  fh+=row("reversing joints at splice / within (median)",sm.rev_joints_splice_p50!=null?`${sm.rev_joints_splice_p50} / ${dash(sm.rev_joints_within_p50)}`:null);
  fh+=row("velocity spike at splice (×median)",sm.vel_spike_ratio_p50);
  fh+=row("limit-guard held left / right",(vi.left!=null||vi.right!=null)?`${(100*(vi.left||0)).toFixed(1)}% / ${(100*(vi.right||0)).toFixed(1)}%`:null);
  fh+="</table>";
  if(cfg){
    fh+=`<div class="note" style="margin-top:6px">config: ${esc(dash(cfg.checkpoint_label)||"?")} · exec ${esc(dash(cfg.execution_horizon))} · prefetch ${cfg.prefetch_enable?("on, lead "+esc(dash(cfg.prefetch_lead))):"off"} · RTC ${cfg.rtc_enable?("on, overlap "+esc(dash(cfg.rtc_overlap_steps))+", frozen "+esc(dash(cfg.rtc_frozen_steps))):"off"} · v${esc(dash(cfg.package_version))}</div>`;
    if(cfg.notes)fh+=`<div class="note">notes: ${esc(cfg.notes)}</div>`;
  }else{
    fh+=`<div class="note" style="margin-top:6px">config unknown — no .meta.json sidecar (log predates logger v0.4)</div>`;
  }
  $("factsbox").innerHTML=fh;
}

function renderMatrix(){
  const cols=[
    ["run",r=>esc(r.name)],["ckpt",r=>r.cfg?esc(dash(r.cfg.checkpoint_label)):"—"],
    ["mode",r=>r.cfg?((r.cfg.prefetch_enable?"prefetch":"blocking")+(r.cfg.rtc_enable?"+RTC":"")):"—"],
    ["exec",r=>r.cfg?dash(r.cfg.execution_horizon):"—"],
    ["cycle p50",r=>dash((r.schedule||{}).cycle_p50)],
    ["skip p50",r=>dash((r.schedule||{}).skip_p50)],
    ["depth p95",r=>dash((r.schedule||{}).depth_p95)],
    ["splice ×",r=>dash((r.smooth||{}).splice_ratio)],
    ["stalls",r=>dash((r.schedule||{}).stall_count)],
    ["eff Hz",r=>dash((r.schedule||{}).effective_hz)],
    ["grasp ✓/att",r=>{const g=graspSummary(r);return g.att?`${g.succ}/${g.att}`:"—"}],
    ["lat p50/p95",r=>r.meta.lat_p50!=null?`${r.meta.lat_p50}/${dash((r.schedule||{}).lat_p95)}`:"—"],
    ["limit %",r=>{const v=r.violations||{};return (v.left!=null||v.right!=null)?(100*Math.max(v.left||0,v.right||0)).toFixed(1):"—"}],
  ];
  let h="<table><tr>"+cols.map(c=>`<th${c[0]==="run"?"":' class="r"'}>${c[0]}</th>`).join("")+"<th>verdicts</th></tr>";
  names.forEach(n=>{
    const r={...runs[n],name:n};
    h+="<tr>"+cols.map((c,i)=>`<td${i?' class="r"':""}>${c[1](r)}</td>`).join("");
    const vs=verdicts(runs[n]);
    h+=`<td>${vs.length?vs.map(v=>`<span style="color:${v.ok?"var(--good)":"var(--warn)"};font-weight:600">${v.ok?"✓":"✗"} ${v.k}</span>`).join(" &nbsp;"):"—"}</td></tr>`;
  });
  $("matrixbox").innerHTML=h+"</table>";
  requestAnimationFrame(()=>{
    scatter($("sc1"),names.map(n=>({x:(runs[n].schedule||{}).cycle_p50,y:(runs[n].smooth||{}).splice_ratio,l:n})),"cycle p50 (steps)","splice ratio",{hline:V_SPLICE});
    scatter($("sc2"),names.map(n=>{const g=graspSummary(runs[n]);return {x:(runs[n].schedule||{}).depth_p95,y:g.att?g.succ/g.att:null,l:n}}),"depth p95 (steps)","grasp success rate",{vline:V_DEPTH,ymax:1});
  });
}

function scatter(cv,pts,xl,yl,opt){
  opt=opt||{};
  const dpr=window.devicePixelRatio||1,W=cv.clientWidth,H=260;
  cv.width=W*dpr;cv.height=H*dpr;cv.style.height=H+"px";
  const g=cv.getContext("2d");g.scale(dpr,dpr);
  const padL=44,padR=10,padT=10,padB=26,iw=W-padL-padR,ih=H-padT-padB;
  const data=pts.filter(p=>p.x!=null&&p.y!=null);
  g.fillStyle=css("--muted");g.font="9px "+css("--mono").split(",")[0];
  if(!data.length){g.fillText("no runs with these metrics yet",padL,H/2);return}
  let xmin=Math.min(...data.map(p=>p.x)),xmax=Math.max(...data.map(p=>p.x));
  let ymin=0,ymax=opt.ymax!=null?opt.ymax:Math.max(...data.map(p=>p.y));
  if(opt.vline!=null){xmin=Math.min(xmin,opt.vline);xmax=Math.max(xmax,opt.vline)}
  if(opt.hline!=null)ymax=Math.max(ymax,opt.hline);
  if(xmax-xmin<1e-9){xmin-=1;xmax+=1}
  if(ymax-ymin<1e-9)ymax+=1;
  const xpad=(xmax-xmin)*.08;xmin-=xpad;xmax+=xpad;ymax*=1.08;
  const X=v=>padL+iw*(v-xmin)/(xmax-xmin),Y=v=>padT+ih*(1-(v-ymin)/(ymax-ymin));
  g.strokeStyle=css("--hairline");g.strokeRect(padL,padT,iw,ih);
  if(opt.hline!=null){g.strokeStyle=css("--warn");g.setLineDash([4,3]);g.beginPath();g.moveTo(padL,Y(opt.hline));g.lineTo(W-padR,Y(opt.hline));g.stroke();g.setLineDash([])}
  if(opt.vline!=null){g.strokeStyle=css("--warn");g.setLineDash([4,3]);g.beginPath();g.moveTo(X(opt.vline),padT);g.lineTo(X(opt.vline),padT+ih);g.stroke();g.setLineDash([])}
  data.forEach(p=>{
    g.fillStyle=css("--accent");g.beginPath();g.arc(X(p.x),Y(p.y),4,0,7);g.fill();
    g.fillStyle=css("--muted");g.fillText(p.l.slice(0,14),X(p.x)+6,Y(p.y)+3);
  });
  g.fillStyle=css("--muted");
  g.fillText(xl,W/2-20,H-6);
  g.save();g.translate(10,H/2+20);g.rotate(-Math.PI/2);g.fillText(yl,0,0);g.restore();
  g.fillText(String(Math.round(xmin*10)/10),padL,H-14);g.fillText(String(Math.round(xmax*10)/10),W-padR-24,H-14);
  g.fillText(String(Math.round(ymax*100)/100),2,padT+8);
}
window.addEventListener("resize",()=>render());
render();
</script>
"""
