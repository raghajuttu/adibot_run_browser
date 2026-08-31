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
    html = html.replace("__DATA__", json.dumps(data, separators=(",", ":")))
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
  <div class="chips" id="chips"></div>
  <div class="legend" id="legend"></div>
  <div class="grid" id="grid"></div>
  <div class="cols">
    <div><h2>Tracking (mrad)</h2><div id="statsbox"></div></div>
    <div><h2>Chunk profile</h2><div id="profbox"></div>
         <h2>Contacts</h2><div id="ctcbox"></div>
         <h2>Grasps</h2><div id="graspbox"></div></div>
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
const runs=DATA.runs, names=Object.keys(runs);
let runA=names[0], runB="", view="track", side="all";
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
  const m=runs[name].meta;
  const lat=m.lat_p50==null?"":` · lat p50 <b>${m.lat_p50}ms</b> p90 ${m.lat_p90} max ${m.lat_max}`;
  return `<span class="chip ${cls}"><b>${name}</b> · ${m.dur_s}s · ${m.chunks} chunks${lat}</span>`;
}
function render(){
  buildSidebar();
  document.querySelectorAll("#views button").forEach(b=>b.classList.toggle("on",b.dataset.v===view));
  document.querySelectorAll("#sides button").forEach(b=>b.classList.toggle("on",b.dataset.s===side));
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
    gh+=`<div class="note">${short(n)}: ${sp.length?sp.map(([a,b])=>a+"–"+b+"s").join(", "):"never held"}</div>`;
  });
  $("graspbox").innerHTML=gh;
}
window.addEventListener("resize",()=>render());
render();
</script>
"""
