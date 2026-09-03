"""The dashboard page: all HTML, CSS and JS live here and nowhere else.

Edit the look, the layout, or the interactions in this file. It knows nothing
about CSVs — builder.py hands it a finished JSON blob and a few display
options, and render() splices them in.

Zooming: the page embeds the RAW cmd/actual arrays (analysis.py, size-guarded)
and decimates AT DRAW TIME for the visible window only — zooming in reveals
real samples, chunk labels, splice sizes and horizon indices instead of bigger
pixels. Velocity/effort stay decimated (read as envelopes), and a run whose
raw was omitted for size falls back to the decimated traces everywhere.
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
    html = html.replace("__DIRCOS_REF__", str(cfg.dircos_reference))
    html = html.replace("__DIRCOS_WARN__", str(cfg.dircos_warn_below))
    html = html.replace("__DIRCOS_USABLE__", str(cfg.dircos_usable_min))
    html = html.replace("__PLANS_WINDOW__", str(cfg.plans_window_s))
    html = html.replace("__PLAN_MIN_PX__", str(cfg.plan_min_px_per_chunk))
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
--cut:#33424F;--ghost:#63768A;--tail:#7B5EA7;--bound:#C2185B;
--mono:"IBM Plex Mono",ui-monospace,Consolas,monospace;--disp:"Archivo","Helvetica Neue",Arial,sans-serif}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--ground:#10161C;--surface:#171F27;--ink:#D8E1E8;--muted:#8A99A6;--hairline:#2A3540;--accent:#41B6C0;--accent-soft:#14333A;--warn:#E09A3E;--warn-soft:#3A2A14;--good:#6FB479;--cmd:#ff6b6b;--act:#5aa9e6;--b2:#b48be0;--cut:#C8D6E0;--ghost:#7E8FA0;--tail:#c9a6f0;--bound:#FF7AC8}}
:root[data-theme="dark"]{--ground:#10161C;--surface:#171F27;--ink:#D8E1E8;--muted:#8A99A6;--hairline:#2A3540;--accent:#41B6C0;--accent-soft:#14333A;--warn:#E09A3E;--warn-soft:#3A2A14;--good:#6FB479;--cmd:#ff6b6b;--act:#5aa9e6;--b2:#b48be0;--cut:#C8D6E0;--ghost:#7E8FA0;--tail:#c9a6f0;--bound:#FF7AC8}
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
.runrow{display:flex;align-items:center;gap:2px}
.runrow .runbtn{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.eye{flex:0 0 auto;background:none;border:none;color:var(--muted);cursor:pointer;font-size:11px;padding:3px 5px;line-height:1;border-radius:3px}
.eye:hover{color:var(--accent);background:var(--accent-soft)}
.runrow.off .runbtn{opacity:.4;text-decoration:line-through}
.runrow.off .eye{color:var(--warn)}
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
.grid.one{grid-template-columns:1fr}
.panel{background:var(--surface);border:1px solid var(--hairline);border-radius:4px;padding:6px 8px 2px}
.panel:hover{border-color:var(--accent)}
.panel .ttl{font-family:var(--mono);font-size:10.5px;color:var(--muted);margin-bottom:2px;cursor:zoom-in}
.panel .ttl:hover{color:var(--accent)}
.panel canvas{cursor:crosshair}
canvas{width:100%;display:block}
h2{font-size:14px;font-weight:700;margin:26px 0 8px}
table{border-collapse:collapse;font-family:var(--mono);font-size:11.5px;width:100%}
th{text-align:left;font-size:9.5px;letter-spacing:.07em;text-transform:uppercase;color:var(--muted);font-weight:500;padding:4px 12px 4px 0;border-bottom:1px solid var(--ink);white-space:nowrap}
td{padding:3px 12px 3px 0;border-bottom:1px solid var(--hairline);white-space:nowrap;font-variant-numeric:tabular-nums}
td.r,th.r{text-align:right}
td.hi{color:var(--warn);font-weight:600}
tr.jump{cursor:pointer}
tr.jump:hover td{background:var(--accent-soft)}
.cols{display:flex;gap:26px;flex-wrap:wrap}
.cols>div{flex:1 1 340px;min-width:0}
.scrollbox{overflow-x:auto;max-width:100%}
#factsbox td{white-space:normal}
#factsbox td.r{white-space:normal;word-break:break-word}
.sec{margin:0 0 6px}
.sechead{cursor:pointer;user-select:none;display:flex;align-items:center;gap:8px}
.sechead .caret{font-size:10px;color:var(--muted);transition:transform .12s;display:inline-block}
.sec.collapsed .caret{transform:rotate(-90deg)}
.sec.collapsed .secbody{display:none}
.sechead:hover .caret{color:var(--accent)}
.legend{font-family:var(--mono);font-size:10.5px;color:var(--muted);margin:6px 0 10px}
.legend i{display:inline-block;width:14px;height:3px;vertical-align:middle;margin:0 4px 0 10px}
.legend .hint{opacity:.75;margin-left:14px}
.modal{position:fixed;inset:0;background:rgba(0,0,0,.5);display:none;align-items:center;justify-content:center;z-index:10}
.modal.on{display:flex}
.mbox{background:var(--ground);border:1px solid var(--hairline);border-radius:6px;padding:14px;width:min(1100px,94vw)}
.mbox .ttl{font-family:var(--mono);font-size:12px;margin-bottom:6px;display:flex;justify-content:space-between}
.mbox button{font-family:var(--mono);background:none;border:1px solid var(--hairline);color:var(--ink);border-radius:3px;cursor:pointer;padding:2px 10px}
.note{font-family:var(--mono);font-size:10.5px;color:var(--muted);margin-top:4px}
#tip{position:fixed;z-index:30;pointer-events:none;display:none;background:var(--ground);
  border:1px solid var(--accent);border-radius:3px;padding:4px 7px;font-family:var(--mono);
  font-size:10.5px;line-height:1.45;color:var(--ink);box-shadow:0 2px 8px rgba(0,0,0,.25);white-space:nowrap}
#tip b{color:var(--accent);font-weight:600}
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
    <button data-p="plans">plans</button>
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
    <button data-v="dcmd">cmd step</button>
  </div>
  <div class="grp">Joints</div>
  <div class="seg" id="sides">
    <button data-s="all" class="on">all</button>
    <button data-s="left">left</button>
    <button data-s="right">right</button>
  </div>
  <label class="chk"><input type="checkbox" id="cbBounds" checked> chunk boundaries</label>
  <label class="chk"><input type="checkbox" id="cbGrasp" checked> grasp shading</label>
</aside>
<main>
  <div id="pageSignals">
    <div class="chips" id="chips"></div>
    <div class="sec" data-sec="plots"><h2 class="sechead"><span class="caret">&#9662;</span><span id="plotsTitle">Commanded vs actual position</span></h2>
      <div class="secbody">
        <div class="legend" id="legend"></div>
        <div class="grid" id="grid"></div>
      </div>
    </div>
    <div class="cols">
      <div>
        <div class="sec" data-sec="tracking"><h2 class="sechead"><span class="caret">&#9662;</span>Tracking (mrad)</h2>
          <div class="secbody scrollbox" id="statsbox"></div></div>
        <div class="sec" data-sec="facts"><h2 class="sechead"><span class="caret">&#9662;</span>Run facts</h2>
          <div class="secbody scrollbox" id="factsbox"></div></div>
        <div class="sec" data-sec="dist"><h2 class="sechead"><span class="caret">&#9662;</span>Step distribution (mrad)</h2>
          <div class="secbody">
            <div class="panel" style="cursor:default"><canvas id="histcv" height="150"></canvas></div>
            <div class="note">|&Delta;cmd| per tick, within chunks (teal) vs at chunk switches (amber), normalised. Shows whether a splice ratio is a consistent offset or a few outliers.</div>
          </div></div>
      </div>
      <div>
        <div class="sec" data-sec="profile"><h2 class="sechead"><span class="caret">&#9662;</span>Chunk profile</h2>
          <div class="secbody">
            <div class="panel" style="cursor:default"><canvas id="profcv" height="180"></canvas></div>
            <div class="note" style="margin-bottom:8px">error (solid, offset-corrected) and cmd step (dashed) vs horizon_idx — the knee is where late steps stop being trustworthy. Purple = compare run.</div>
            <div class="scrollbox" id="profbox"></div>
          </div></div>
        <div class="sec" data-sec="contacts"><h2 class="sechead"><span class="caret">&#9662;</span>Contacts</h2>
          <div class="secbody scrollbox" id="ctcbox"></div></div>
        <div class="sec" data-sec="grasps"><h2 class="sechead"><span class="caret">&#9662;</span>Grasps</h2>
          <div class="secbody scrollbox" id="graspbox"></div></div>
      </div>
    </div>
  </div>
  <div id="pagePlans" style="display:none">
    <div class="chips" id="planChips"></div>
    <div class="sec" data-sec="predq"><h2 class="sechead"><span class="caret">&#9662;</span>What the model predicted &mdash; quality across the horizon</h2>
      <div class="secbody">
        <div class="legend" id="hzcosLg"></div>
        <div class="panel" style="cursor:default"><canvas id="hzcos" height="230"></canvas></div>
        <div class="note">Direction continuity <b>inside a single predicted chunk</b>, at each step of the horizon. Nothing here depends on the execution horizon, the prefetch skip, or where the chunk boundaries fell &mdash; it is the policy's own output. Near <b>+1</b> the plan carries straight on; <b>0</b> is a right-angle turn every tick; <b>below 0</b> the plan doubles back on itself. Human demonstrations sit at the dashed line.</div>
        <div class="legend" id="hzaccLg" style="margin-top:12px"></div>
        <div class="panel" style="cursor:default"><canvas id="hzacc" height="205"></canvas></div>
        <div class="note">How far the plan moves per tick, and its acceleration (the deployment guide's intra-chunk metric). Acceleration rising while movement stays flat means the plan is shaking rather than travelling.</div>
      </div></div>
    <div class="sec" data-sec="planagg"><h2 class="sechead"><span class="caret">&#9662;</span>Disagreement between consecutive plans</h2>
      <div class="secbody">
        <div class="legend" id="aggLg"></div>
        <div class="panel" style="cursor:default"><canvas id="aggcv" height="220"></canvas></div>
        <div class="note">How far apart two consecutive chunks are about the same instant, by how many steps past the switch it is. Line = median over every chunk pair, band = p10&ndash;p90. Flat and low means each new plan continues the old one.</div>
      </div></div>
    <div class="sec" data-sec="planjoints"><h2 class="sechead"><span class="caret">&#9662;</span>Every plan, per joint</h2>
      <div class="secbody">
        <div class="legend" id="planLegend"></div>
        <div class="note" id="planHint" style="margin-bottom:6px"></div>
        <div class="grid" id="plangrid"></div>
      </div></div>
  </div>
  <div id="pageMatrix" style="display:none">
    <div class="sec" data-sec="matrix"><h2 class="sechead" style="margin-top:0"><span class="caret">&#9662;</span>Run matrix</h2>
      <div class="secbody">
        <div class="note" style="margin-bottom:8px">One row per run: configuration (from the .meta.json sidecar) + measured behaviour. Verdicts: a run failing any chip is not a valid comparison point.</div>
        <div class="tblwrap" style="overflow-x:auto"><div id="matrixbox"></div></div>
      </div></div>
    <div class="cols" style="margin-top:18px">
      <div class="sec" data-sec="sc1"><h2 class="sechead"><span class="caret">&#9662;</span>Splice ratio vs replan cycle</h2>
        <div class="secbody"><div class="panel" style="cursor:default"><canvas id="sc1" height="260"></canvas></div></div></div>
      <div class="sec" data-sec="sc2"><h2 class="sechead"><span class="caret">&#9662;</span>Grasp success vs executed depth p95</h2>
        <div class="secbody"><div class="panel" style="cursor:default"><canvas id="sc2" height="260"></canvas></div></div></div>
    </div>
  </div>
</main>
</div>
<div id="tip"></div>
<div class="modal" id="modal"><div class="mbox">
  <div class="ttl"><span id="mttl"></span><button onclick="closeModal()">close</button></div>
  <div class="panel" style="cursor:default"><canvas id="mcanvas" height="420"></canvas></div>
</div></div>
<script>
const DATA=__DATA__;
const HI_ERR=__HI_ERR__, HI_NM=__HI_NM__;
const V_SPLICE=__V_SPLICE__, V_DEPTH=__V_DEPTH__, PLANS_WINDOW=__PLANS_WINDOW__;
const PLAN_MIN_PX=__PLAN_MIN_PX__;
const DIRCOS_REF=__DIRCOS_REF__, DIRCOS_WARN=__DIRCOS_WARN__, DIRCOS_USABLE=__DIRCOS_USABLE__;
const runs=DATA.runs, names=Object.keys(runs);
let runA=names[0], runB="", view="track", side="all", page="signals";
// Two viewports, on purpose. `vp` belongs to the grid and is only ever set
// programmatically (jumpTo, from a table row) - dragging one small panel used
// to pan all sixteen, which is not what anyone means by panning a chart.
// `mvp` belongs to the enlarged view and is the only one pointer input writes.
// Closing the enlarged view discards it, so the grid never silently inherits
// someone else's zoom.
let vp=null;               // grid viewport {t0,t1}; null = full range
let mvp=null;              // enlarged-view viewport; null = full range
let modalJoint=null;       // joint shown in the enlarged modal, or null
let modalKind=null;        // "signals" | "plans" - which drawer the modal uses
const panelReg=[];         // [{cv, joint, big}] canvases to redraw on viewport change
const errCache=new Map();  // run|joint -> Float64Array err (mrad) computed from raw
const dash=v=>(v==null||v==="")?"—":v;
// Descriptive name for each signal view — used for the section heading and
// the enlarged-panel title, so the page says what is plotted rather than
// "signal plots".
const VIEW_TITLES={
  track:"Commanded vs actual position (rad)",
  err:"Tracking error — commanded minus actual (mrad)",
  vel:"Measured joint velocity (rad/s)",
  eff:"Measured joint effort (Nm)",
  dcmd:"Command step per tick — |Δcmd|, max over arm joints (mrad)"};
// Runs hidden from the sidebar, matrix and compare list. Persisted per browser.
let hiddenRuns={};
try{hiddenRuns=JSON.parse(localStorage.getItem("rb_hidden")||"{}")||{}}catch(e){}
const visibleNames=()=>names.filter(n=>!hiddenRuns[n]);
function setHidden(n,off){
  if(off&&visibleNames().length<=1)return;          // never hide the last run
  if(off)hiddenRuns[n]=1; else delete hiddenRuns[n];
  try{localStorage.setItem("rb_hidden",JSON.stringify(hiddenRuns))}catch(e){}
  if(hiddenRuns[runA]){runA=visibleNames()[0];vp=null}
  if(hiddenRuns[runB])runB="";
  render();
}
const esc=s=>String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
const $=id=>document.getElementById(id);
function updateGen(){
  const h=names.length-visibleNames().length;
  $("gen").textContent=names.length+" run"+(names.length===1?"":"s")
    +(h?" · "+h+" hidden":"")+" · built "+DATA.generated;
}
updateGen();

function css(v){return getComputedStyle(document.documentElement).getPropertyValue(v).trim()}
function joints(){
  if(view==="dcmd")return["__dcmd__"];
  const all=runs[runA].joints;
  return side==="all"?all:all.filter(j=>j.includes(side));
}
function short(j){
  if(j==="__dcmd__")return"|Δcmd| per tick — max over arm joints";
  return j.replace("openarm_","").replace("_joint"," j").replace("finger j1","grip");
}
function runRange(r){
  const raw=runs[r].raw;
  if(raw&&raw.t.length)return[raw.t[0],raw.t[raw.t.length-1]];
  let t1=0;
  const tr=runs[r].traces;
  for(const j in tr){const tt=tr[j].cmd[0]; if(tt.length)t1=Math.max(t1,tt[tt.length-1])}
  return[0,t1||1];
}
function viewRange(big){
  const v=big?mvp:vp;
  if(v)return[v.t0,v.t1];
  const[a0,a1]=runRange(runA);
  if(!runB)return[a0,a1];
  const[b0,b1]=runRange(runB);
  return[Math.min(a0,b0),Math.max(a1,b1)];
}
function bisect(t,x){       // first index with t[i] >= x
  let lo=0,hi=t.length;
  while(lo<hi){const m=(lo+hi)>>1; if(t[m]<x)lo=m+1; else hi=m}
  return lo;
}
function errSeries(run,j){
  const key=run+"|"+j, hit=errCache.get(key);
  if(hit)return hit;
  const raw=runs[run].raw;
  if(!raw||!raw.j[j]||!raw.j[j].act)return null;
  const c=raw.j[j].cmd,a=raw.j[j].act,out=new Array(c.length);
  for(let i=0;i<c.length;i++)
    out[i]=(c[i]==null||a[i]==null)?null:Math.round((c[i]-a[i])*1e4)/10;
  errCache.set(key,out);
  return out;
}
// series list for one run+joint under the current view: [{t,y,c,w,dash,raw}]
function seriesFor(run,j){
  const R=runs[run], raw=R.raw;
  if(view==="dcmd"){
    if(!raw||!R.dstep)return[];
    return[{t:raw.t.slice(1),y:R.dstep,c:css("--act"),w:1,zero:1,raw:1}];
  }
  const tr=R.traces[j]; if(!tr&&!raw)return[];
  if(view==="track"){
    if(raw&&raw.j[j]){
      const s=[];
      if(raw.j[j].act)s.push({t:raw.t,y:raw.j[j].act,c:css("--act"),w:1.2,raw:1});
      s.push({t:raw.t,y:raw.j[j].cmd,c:css("--cmd"),w:1,raw:1,isCmd:1});
      return s;
    }
    return tr?[{t:tr.act[0],y:tr.act[1],c:css("--act"),w:1.2},{t:tr.cmd[0],y:tr.cmd[1],c:css("--cmd"),w:1,isCmd:1}]:[];
  }
  if(view==="err"){
    const e=errSeries(run,j);
    if(e)return[{t:raw.t,y:e,c:css("--act"),w:1.2,zero:1,raw:1}];
    return tr&&tr.err?[{t:tr.err[0],y:tr.err[1],c:css("--act"),w:1.2,zero:1}]:[];
  }
  const key=view; // vel | eff — decimated only, read as envelopes
  return tr&&tr[key]?[{t:tr[key][0],y:tr[key][1],c:css("--act"),w:1,zero:1}]:[];
}

// ---------------------------------------------------------------- drawing
function drawSeries(g,s,X,Y,i0,i1,W){
  const n=i1-i0;
  g.strokeStyle=s.c; g.lineWidth=s.w; g.setLineDash(s.dash?[4,3]:[]);
  if(n>2*W){                       // far: min/max bucket per pixel column
    g.beginPath();
    let started=false;
    for(let px=0;px<W;px++){
      const a=i0+Math.floor(n*px/W), b=i0+Math.floor(n*(px+1)/W);
      let mn=Infinity,mx=-Infinity,tmn=0,tmx=0;
      for(let i=a;i<b;i++){const v=s.y[i]; if(v==null)continue;
        if(v<mn){mn=v;tmn=s.t[i]} if(v>mx){mx=v;tmx=s.t[i]}}
      if(mn===Infinity)continue;
      const p1=tmn<=tmx?[tmn,mn,tmx,mx]:[tmx,mx,tmn,mn];
      if(!started){g.moveTo(X(p1[0]),Y(p1[1]));started=true}else g.lineTo(X(p1[0]),Y(p1[1]));
      g.lineTo(X(p1[2]),Y(p1[3]));
    }
    g.stroke();
  }else{                           // near: every sample
    g.beginPath();
    let started=false;
    for(let i=i0;i<i1;i++){const v=s.y[i]; if(v==null){started=false;continue}
      const x=X(s.t[i]),y=Y(v);
      if(!started){g.moveTo(x,y);started=true}else g.lineTo(x,y)}
    g.stroke();
    if(n<=W/6){                    // close: a dot per sample
      g.fillStyle=s.c;
      for(let i=i0;i<i1;i++){const v=s.y[i]; if(v==null)continue;
        g.beginPath();g.arc(X(s.t[i]),Y(v),2,0,7);g.fill()}
    }
  }
  g.setLineDash([]);
}
function drawPanel(cv,j,big){
  const dpr=window.devicePixelRatio||1, W0=cv.clientWidth, H=big?420:(view==="dcmd"?260:150);
  if(!W0)return;
  cv.width=W0*dpr; cv.height=H*dpr; cv.style.height=H+"px";
  const g=cv.getContext("2d"); g.scale(dpr,dpr);
  const padL=46,padR=6,padT=6,padB=16, iw=W0-padL-padR, ih=H-padT-padB;
  let sers=seriesFor(runA,j).map(s=>({...s,run:runA}));
  if(runB) sers=sers.concat(seriesFor(runB,j).map(s=>({...s,run:runB,dash:1,
    c:s.isCmd?css("--warn"):css("--b2")})));
  g.fillStyle=css("--muted"); g.font="9px "+css("--mono").split(",")[0];
  if(!sers.length){g.fillText(runs[runA].raw_omitted?"raw omitted (run too large) — no data for this view":"no data for this signal",padL,H/2);return}
  const[t0,t1]=viewRange();
  // visible index range + y-range per series
  let ymin=Infinity,ymax=-Infinity;
  sers.forEach(s=>{
    s.i0=Math.max(0,bisect(s.t,t0)-1); s.i1=Math.min(s.t.length,bisect(s.t,t1)+1);
    for(let i=s.i0;i<s.i1;i++){const v=s.y[i]; if(v==null)continue;
      if(v<ymin)ymin=v; if(v>ymax)ymax=v}
  });
  if(!isFinite(ymin)){ymin=-1;ymax=1}
  if(sers.some(s=>s.zero)){ymin=Math.min(ymin,0);ymax=Math.max(ymax,0)}
  if(ymax-ymin<1e-9){ymax+=1;ymin-=1}
  const pad=(ymax-ymin)*.06; ymin-=pad; ymax+=pad;
  const X=t=>padL+iw*(t-t0)/(t1-t0), Y=v=>padT+ih*(1-(v-ymin)/(ymax-ymin));
  g.save(); g.beginPath(); g.rect(padL,padT,iw,ih); g.clip();
  // grasp shading (finger panels, run A)
  if($("cbGrasp").checked&&runs[runA].grasps[j]){
    g.fillStyle=css("--good"); g.globalAlpha=.15;
    runs[runA].grasps[j].forEach(([a,b])=>g.fillRect(X(a),padT,Math.max(X(b)-X(a),2),ih));
    g.globalAlpha=1;
  }
  // boundaries with level-of-detail (run A)
  const bounds=runs[runA].bounds, bseq=runs[runA].bound_seq||[];
  const vb=[];
  if($("cbBounds").checked)
    for(let k=0;k<bounds.length;k++) if(bounds[k]>=t0&&bounds[k]<=t1) vb.push(k);
  if(vb.length){
    g.strokeStyle=css("--bound"); g.lineWidth=1;
    g.globalAlpha=vb.length>40?.3:.7;
    g.beginPath();
    vb.forEach(k=>{g.moveTo(X(bounds[k]),padT);g.lineTo(X(bounds[k]),padT+ih)});
    g.stroke(); g.globalAlpha=1;
  }
  sers.forEach(s=>drawSeries(g,s,X,Y,s.i0,s.i1,iw));
  // mid zoom: chunk labels; close zoom: splice size in mrad
  const rawA=runs[runA].raw;
  // Labels need room, not just a small count: eleven "c12 Δ48.3mr" labels in a
  // 250 px panel overlap into an unreadable band across the top. The enlarged
  // view is four times wider and shows them.
  if(vb.length&&vb.length<=14&&iw/vb.length>=58){
    g.fillStyle=css("--bound"); g.globalAlpha=.95;
    vb.forEach(k=>{
      let lbl="c"+(bseq[k]!=null?bseq[k]:k);
      if(rawA&&runs[runA].dstep&&(view==="track"||view==="dcmd"||view==="err")){
        const i=bisect(rawA.t,bounds[k]-1e-6);
        const d=i>0?runs[runA].dstep[i-1]:null;   // dstep[i-1] spans the switch into row i
        if(d!=null&&k>0)lbl+=" Δ"+d+"mr";
      }
      g.fillText(lbl,Math.min(X(bounds[k])+2,W0-padR-52),padT+9);
    });
    g.globalAlpha=1;
  }
  // closest zoom: horizon_idx under each sample (track view, raw runs).
  // Only when there is room for a label per dot — threshold scales with the
  // panel width so labels never smear into each other.
  const first=sers[0];
  if(rawA&&view==="track"&&first&&first.raw&&(first.i1-first.i0)<=iw/14){
    g.fillStyle=css("--muted");
    for(let i=first.i0;i<first.i1;i++)
      g.fillText(String(rawA.hi[i]),X(rawA.t[i])-3,padT+ih-3);
  }
  // reference line: within-chunk median on the cmd-step view
  if(view==="dcmd"){
    const m=(runs[runA].smooth||{}).step_within_p50;
    if(m!=null&&m>=ymin&&m<=ymax){
      g.strokeStyle=css("--good"); g.setLineDash([5,4]); g.lineWidth=1;
      g.beginPath();g.moveTo(padL,Y(m));g.lineTo(W0-padR,Y(m));g.stroke();g.setLineDash([]);
      g.fillStyle=css("--good"); g.fillText("within-chunk median "+m,padL+4,Y(m)-3);
    }
  }
  if(ymin<0&&ymax>0){g.strokeStyle=css("--hairline");g.lineWidth=1;g.beginPath();g.moveTo(padL,Y(0));g.lineTo(W0-padR,Y(0));g.stroke()}
  drawCrosshair(g,cv,padL,padT,iw,ih);
  g.restore();
  g.fillStyle=css("--muted");
  g.fillText(ymax.toFixed(2),2,padT+8); g.fillText(ymin.toFixed(2),2,padT+ih);
  g.fillText(t1.toFixed(t1-t0<5?2:0)+"s",W0-padR-34,H-4); g.fillText(t0.toFixed(t1-t0<5?2:0),padL,H-4);

  // hover readout: nearest sample of each series at the cursor's time
  const unit=view==="track"?"rad":view==="err"?"mrad":view==="vel"?"rad/s":view==="eff"?"Nm":"mrad";
  cv._probe=(px,py)=>{
    if(px<padL||px>padL+iw||py<padT||py>padT+ih)return null;
    const tq=t0+(px-padL)/iw*(t1-t0);
    const lines=[`<b>${short(j)}</b> @ ${tq.toFixed(tq<100?2:1)}s`];
    let snap=null, any=false;
    sers.forEach(s2=>{
      let k=bisect(s2.t,tq); if(k>=s2.t.length)k=s2.t.length-1;
      if(k>0&&Math.abs(s2.t[k-1]-tq)<Math.abs(s2.t[k]-tq))k--;
      const v=s2.y[k]; if(v==null)return;
      any=true; if(snap==null)snap=X(s2.t[k]);
      const who=(runB?s2.run+" ":"")+(s2.isCmd?"commanded":sers.length>1&&view==="track"?"actual":"value");
      lines.push(`${who}: <b>${v.toFixed(Math.abs(v)<10?3:1)}</b> ${unit}`);
    });
    if(!any)return null;
    // which chunk this instant belongs to, when the run carries raw indices
    const R=runs[runA].raw;
    if(R&&R.seq&&R.t){
      let k=bisect(R.t,tq); if(k>=R.t.length)k=R.t.length-1;
      if(k>0&&Math.abs(R.t[k-1]-tq)<Math.abs(R.t[k]-tq))k--;
      lines.push(`chunk <b>${R.seq[k]}</b> · step <b>${R.hi[k]}</b>`);
    }
    return {lines,snapX:snap};
  };
}
// ---------------------------------------------------------------- hover readout
// Each draw function stashes a probe on its canvas: pixel -> {lines,[x,y]}.
// One document-level listener turns that into a tooltip plus a crosshair, so
// every plot on the page reports its values the same way.
const tip=$("tip");
let hoverCv=null, hoverPx=null;
function showTip(e,cv){
  const probe=cv._probe;
  if(!probe){tip.style.display="none";return}
  const rect=cv.getBoundingClientRect();
  const px=e.clientX-rect.left, py=e.clientY-rect.top;
  const r=probe(px,py);
  if(!r){tip.style.display="none"; if(hoverCv){hoverCv=null;scheduleRedraw()} return}
  tip.innerHTML=r.lines.join("<br>");
  tip.style.display="block";
  const tw=tip.offsetWidth, th=tip.offsetHeight;
  let x=e.clientX+14, y=e.clientY+14;
  if(x+tw>innerWidth-6)x=e.clientX-tw-14;
  if(y+th>innerHeight-6)y=e.clientY-th-14;
  tip.style.left=x+"px"; tip.style.top=y+"px";
  if(hoverCv!==cv||hoverPx==null||Math.abs(hoverPx-px)>0.5){
    hoverCv=cv; hoverPx=r.snapX!=null?r.snapX:px; scheduleRedraw();
  }
}
document.addEventListener("pointermove",e=>{
  const cv=e.target&&e.target.tagName==="CANVAS"?e.target:null;
  if(!cv||!cv._probe){
    if(tip.style.display!=="none"){tip.style.display="none"}
    if(hoverCv){hoverCv=null;scheduleRedraw()}
    return;
  }
  showTip(e,cv);
});
document.addEventListener("pointerleave",()=>{tip.style.display="none";
  if(hoverCv){hoverCv=null;scheduleRedraw()}});
function drawCrosshair(g,cv,padL,padT,iw,ih){
  if(hoverCv!==cv||hoverPx==null)return;
  if(hoverPx<padL||hoverPx>padL+iw)return;
  g.save();g.strokeStyle=css("--accent");g.globalAlpha=.5;g.lineWidth=1;
  g.setLineDash([3,3]);g.beginPath();g.moveTo(hoverPx,padT);g.lineTo(hoverPx,padT+ih);
  g.stroke();g.restore();
}

function redrawAll(){
  panelReg.forEach(p=>p.plans?drawPlanPanel(p.cv,p.joint,p.big):drawPanel(p.cv,p.joint,p.big));
  if(page==="plans"){drawPredCharts(); drawAgg(); const h=$("planHint"); if(h)h.textContent=planHintText();}
}
let rafPending=false;
function scheduleRedraw(){
  if(rafPending)return; rafPending=true;
  requestAnimationFrame(()=>{rafPending=false;redrawAll()});
}

// ------------------------------------------------------------ interaction
function clampVp(big){
  const v=big?mvp:vp;
  if(!v)return;
  const[r0,r1]=(()=>{const a=runRange(runA); if(!runB)return a;
    const b=runRange(runB); return[Math.min(a[0],b[0]),Math.max(a[1],b[1])]})();
  const span=Math.max(v.t1-v.t0,0.02);
  v.t0=Math.max(r0,Math.min(v.t0,r1-span));
  v.t1=Math.min(r1,Math.max(v.t1,v.t0+0.02));
  if(v.t0<=r0&&v.t1>=r1){if(big)mvp=null;else vp=null}   // fully zoomed out again
}
// Attached ONLY to the enlarged canvas. Grid panels open the enlarged view on
// click instead; a 250 px panel is too small to aim a zoom at anyway.
function attachZoom(cv){
  cv.addEventListener("wheel",e=>{
    e.preventDefault();
    const rect=cv.getBoundingClientRect();
    const frac=Math.min(1,Math.max(0,(e.clientX-rect.left-46)/(rect.width-52)));
    const[t0,t1]=viewRange(true);
    const cursorT=t0+frac*(t1-t0);
    const f=Math.pow(1.25,e.deltaY>0?1:-1);       // >0 = zoom out
    mvp={t0:cursorT-(cursorT-t0)*f, t1:cursorT+(t1-cursorT)*f};
    clampVp(true); scheduleRedraw();
  },{passive:false});
  let dragX=null,dragVp=null;
  cv.addEventListener("pointerdown",e=>{dragX=e.clientX;const[a,b]=viewRange(true);dragVp=[a,b];cv.setPointerCapture(e.pointerId)});
  cv.addEventListener("pointermove",e=>{
    if(dragX==null)return;
    const rect=cv.getBoundingClientRect();
    const dt=(e.clientX-dragX)/(rect.width-52)*(dragVp[1]-dragVp[0]);
    mvp={t0:dragVp[0]-dt,t1:dragVp[1]-dt};
    clampVp(true); scheduleRedraw();
  });
  const end=e=>{dragX=null;dragVp=null};
  cv.addEventListener("pointerup",end); cv.addEventListener("pointercancel",end);
  cv.addEventListener("dblclick",()=>{mvp=null;scheduleRedraw()});
}
function jumpTo(t,halfSpan){
  page="signals";
  vp={t0:t-(halfSpan||2),t1:t+(halfSpan||2)};
  render();               // render() keeps vp; also switches page if needed
  window.scrollTo({top:0,behavior:"smooth"});
}
function seqTime(seq){
  const i=(runs[runA].bound_seq||[]).indexOf(seq);
  return i>=0?runs[runA].bounds[i]:null;
}
function drawWhenSized(cv,fn,tries){
  if(cv.clientWidth>0){fn();return}
  if((tries||0)>20)return;          // genuinely hidden; nothing to draw onto
  requestAnimationFrame(()=>drawWhenSized(cv,fn,(tries||0)+1));
}
function closeModal(){
  $("modal").classList.remove("on");
  modalJoint=null; modalKind=null; mvp=null;
  for(let i=panelReg.length-1;i>=0;i--)if(panelReg[i].big)panelReg.splice(i,1);
}
// kind: "signals" (command vs actual) or "plans" (every predicted chunk).
function openModal(j,kind){
  modalJoint=j; modalKind=kind||"signals"; mvp=null;
  $("modal").classList.add("on");
  $("mttl").textContent=short(j)+" — "+(modalKind==="plans"
    ? "every plan" : (VIEW_TITLES[view]||view))
    +"   ·   scroll to zoom, drag to pan, double-click to reset";
  const cv=$("mcanvas");
  if(!cv._zoomed){attachZoom(cv);cv._zoomed=true}
  panelReg.push({cv,joint:j,big:true,plans:modalKind==="plans"});
  drawWhenSized(cv,()=>modalKind==="plans"?drawPlanPanel(cv,j,true):drawPanel(cv,j,true));
}

// ---------------------------------------------------------------- sidebar
function buildSidebar(){
  updateGen();
  const rl=$("runlist"); rl.innerHTML="";
  names.forEach(n=>{
    const off=!!hiddenRuns[n];
    const row=document.createElement("div");
    row.className="runrow"+(off?" off":"");
    const b=document.createElement("button");
    b.className="runbtn"+(n===runA?" sel":"")+(n===runB?" selB":"");
    b.textContent=n; b.title=n;
    b.onclick=()=>{if(off){setHidden(n,false);return}
      if(runA!==n){runA=n;vp=null} if(runB===n)runB=""; render()};
    const eye=document.createElement("button");
    eye.className="eye"; eye.textContent=off?"+":"×";
    eye.title=off?"show this run":"hide this run";
    eye.onclick=e=>{e.stopPropagation(); setHidden(n,!off)};
    row.appendChild(b); row.appendChild(eye); rl.appendChild(row);
  });
  const cs=$("cmpsel"); cs.innerHTML='<option value="">&mdash; none &mdash;</option>';
  visibleNames().filter(n=>n!==runA).forEach(n=>{
    const o=document.createElement("option"); o.value=n; o.textContent=n;
    if(n===runB)o.selected=true; cs.appendChild(o);
  });
}
$("cmpsel").onchange=e=>{runB=e.target.value; render()};
document.querySelectorAll("#views button").forEach(b=>b.onclick=()=>{view=b.dataset.v; render()});
document.querySelectorAll("#sides button").forEach(b=>b.onclick=()=>{side=b.dataset.s; render()});
document.querySelectorAll("#pages button").forEach(b=>b.onclick=()=>{page=b.dataset.p; render()});
// render(), not scheduleRedraw: these two now appear in the legend, and
// scheduleRedraw only repaints canvases — the legend is HTML.
const onOverlayToggle=()=>{page==="signals"?render():scheduleRedraw()};
$("cbBounds").onchange=onOverlayToggle; $("cbGrasp").onchange=onOverlayToggle;

// ---- collapsible sections: click any heading to hide/show its content ----
// Collapsed set persists per browser (best effort — private windows etc. may
// refuse storage, in which case toggling still works for the session).
let collapsed = {};
try { collapsed = JSON.parse(localStorage.getItem("rb_collapsed") || "{}") || {}; } catch (e) {}
function applyCollapsed(){
  document.querySelectorAll(".sec").forEach(el=>{
    el.classList.toggle("collapsed", !!collapsed[el.dataset.sec]);
  });
}
document.addEventListener("click", e=>{
  const head = e.target.closest(".sechead");
  if (!head) return;
  const sec = head.parentElement;
  const key = sec.dataset.sec;
  collapsed[key] = !collapsed[key];
  try { localStorage.setItem("rb_collapsed", JSON.stringify(collapsed)); } catch (err) {}
  sec.classList.toggle("collapsed", !!collapsed[key]);
  // Canvases inside a hidden section have zero width; re-render on expand so
  // plots draw at their real size.
  if (!collapsed[key]) render();
});
applyCollapsed();

function metaChip(name,cls){
  const r=runs[name], m=r.meta, sc=r.schedule||{}, sm=r.smooth||{}, cfg=r.cfg;
  const lat=m.lat_p50==null?"":` · lat p50 <b>${m.lat_p50}ms</b>`;
  let mode="";
  // How the run actually behaved. rtc_enable is deliberately not appended:
  // the flag changes nothing the server does, so "+RTC" would name a mode
  // that does not exist. The config line below still records that it was set.
  if(cfg) mode=` · ${cfg.prefetch_enable?"prefetch":"blocking"}`;
  else if(m.stalled_run!=null) mode=` · ${m.stalled_run?"blocking?":"prefetch?"}`;
  const depth=sc.depth_p95!=null?` · depth p95 <b>${sc.depth_p95}</b>`:"";
  const spl=sm.splice_ratio!=null?` · splice <b>×${sm.splice_ratio}</b>`:"";
  const st=sc.stall_count!=null?` · stalls ${sc.stall_count}`:"";
  const rawNote=r.raw_omitted?" · raw omitted (too large)":"";
  return `<span class="chip ${cls}"><b>${esc(name)}</b> · ${m.dur_s}s · ${m.chunks} chunks${mode}${lat}${depth}${spl}${st}${rawNote}</span>`;
}
function graspSummary(r){
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
  if(sc.stall_count!=null&&!isBlocking(r))out.push({k:"stalls 0",ok:sc.stall_count===0});
  if(sm.splice_ratio!=null)out.push({k:"splice <"+V_SPLICE,ok:sm.splice_ratio<V_SPLICE});
  if(sc.depth_p95!=null)out.push({k:"depth <"+V_DEPTH,ok:sc.depth_p95<V_DEPTH});
  const v=Math.max(vi.left||0,vi.right||0);
  if(vi.left!=null||vi.right!=null)out.push({k:"limits 0",ok:v===0});
  return out;
}

// ------------------------------------------------------------------ render
function render(){
  buildSidebar();
  document.querySelectorAll("#views button").forEach(b=>b.classList.toggle("on",b.dataset.v===view));
  document.querySelectorAll("#sides button").forEach(b=>b.classList.toggle("on",b.dataset.s===side));
  document.querySelectorAll("#pages button").forEach(b=>b.classList.toggle("on",b.dataset.p===page));
  $("plotsTitle").textContent=VIEW_TITLES[view]||view;
  $("pageSignals").style.display=page==="signals"?"":"none";
  $("pagePlans").style.display=page==="plans"?"":"none";
  $("pageMatrix").style.display=page==="matrix"?"":"none";
  if(page==="matrix"){renderMatrix();return}
  if(page==="plans"){renderPlans();return}
  $("chips").innerHTML=metaChip(runA,"")+(runB?metaChip(runB,"b"):"");
  const unit=view==="track"?"rad":view==="vel"?"rad/s":view==="eff"?"Nm":"mrad";
  let lg=`<b>${unit}</b>`;
  if(view==="track")lg+=`<i style="background:${css("--act")}"></i>actual<i style="background:${css("--cmd")}"></i>commanded`;
  else lg+=`<i style="background:${css("--act")}"></i>${esc(runA)}`;
  if(runB)lg+=`<i style="background:${css("--b2")}"></i>${esc(runB)} (dashed)`;
  if($("cbBounds").checked)lg+=`<i style="background:${css("--bound")}"></i>chunk boundary`;
  if($("cbGrasp").checked)lg+=`<i style="background:${css("--good")}"></i>holding something`;
  lg+=`<span class="hint">click a plot to enlarge it — scroll to zoom and drag to pan inside</span>`;
  $("legend").innerHTML=lg;
  const grid=$("grid"); grid.innerHTML="";
  panelReg.length=0;
  grid.classList.toggle("one",view==="dcmd");
  joints().forEach(j=>{
    const p=document.createElement("div"); p.className="panel";
    const ttl=document.createElement("div"); ttl.className="ttl"; ttl.textContent=short(j);
    ttl.title="enlarge"; ttl.onclick=()=>openModal(j,"signals");
    p.appendChild(ttl);
    const cv=document.createElement("canvas"); p.appendChild(cv); grid.appendChild(p);
    cv.style.cursor="zoom-in"; cv.title="click to enlarge, then scroll to zoom";
    cv.onclick=()=>openModal(j,"signals");
    panelReg.push({cv,joint:j,big:false});
    requestAnimationFrame(()=>drawPanel(cv,j,false));
  });
  if(modalJoint!=null){
    const mc=$("mcanvas");
    panelReg.push({cv:mc,joint:modalJoint,big:true,plans:modalKind==="plans"});
    drawWhenSized(mc,()=>modalKind==="plans"
      ? drawPlanPanel(mc,modalJoint,true)
      : drawPanel(mc,modalJoint,true))}
  renderTables();
  requestAnimationFrame(()=>{drawProfile();drawHist()});
}

function statTable(run){
  const s=runs[run].stats.filter(r=>side==="all"||r.j.includes(side));
  let h=`<table><tr><th>joint</th><th class="r">p50</th><th class="r">p95</th><th class="r">lag ms</th><th class="r">mid</th><th class="r">bnd</th></tr>`;
  s.forEach(r=>{h+=`<tr><td>${short(r.j)}</td><td class="r ${r.p50>HI_ERR?'hi':''}">${dash(r.p50)}</td><td class="r">${dash(r.p95)}</td><td class="r">${dash(r.lag)}</td><td class="r">${dash(r.mid)}</td><td class="r">${dash(r.bnd)}</td></tr>`});
  return h+"</table>";
}
function renderTables(){
  let sb=`<div class="note">${esc(runA)}</div>`+statTable(runA);
  if(runB)sb+=`<div class="note" style="margin-top:10px">${esc(runB)}</div>`+statTable(runB);
  $("statsbox").innerHTML=sb;

  const p=runs[runA].profile;
  let ph=`<table><tr><th class="r">step</th><th class="r">err mrad</th><th class="r">cmd step</th>`;
  if(runB)ph+=`<th class="r">err (B)</th><th class="r">step (B)</th>`;
  ph+=`</tr>`;
  const pb=runB?runs[runB].profile:null;
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
  ct.slice(0,20).forEach(e=>{ch+=`<tr class="jump" data-t="${e.t}" title="jump to this moment"><td class="r">${e.t}</td><td class="r">${e.dur}</td><td>${short(e.j)}</td><td class="r ${Math.abs(e.nm)>HI_NM?'hi':''}">${e.nm}</td></tr>`});
  if(ct.length)ch+="</table>"+(ct.length>20?`<div class="note">+${ct.length-20} more</div>`:"");
  $("ctcbox").innerHTML=ch;

  const gr=runs[runA].grasps;
  let gh="";
  const fingers=Object.keys(gr);
  if(!fingers.length)gh="<div class='note'>no gripper columns</div>";
  const fstat=runs[runA].finger_status||{};
  fingers.forEach(n=>{
    const sp=gr[n], why=fstat[n];
    if(why){gh+=`<div class="note">${short(n)}: <span style="color:var(--warn)">not measured</span> — ${esc(why)}</div>`}
    else gh+=`<div class="note">${short(n)} held: ${sp.length?sp.map(([a,b])=>`<a href="#" data-t="${a}" class="jl">${a}–${b}s</a>`).join(", "):"never"}</div>`;
  });
  const ge=runs[runA].grasp_events||{};
  Object.keys(ge).forEach(n=>{
    ge[n].forEach(e=>{
      const ok=e.success==null?"outcome not measurable":(e.success?"✓ held":"✗ air");
      gh+=`<div class="note"><a href="#" data-t="${e.t}" class="jl">${short(n)} close @ ${e.t}s</a> · step ${e.hi} · rise ${dash(e.rise_ms)}ms · ${ok}</div>`;
    });
  });
  $("graspbox").innerHTML=gh;

  const sc=runs[runA].schedule||{}, sm=runs[runA].smooth||{}, vi=runs[runA].violations||{}, cfg=runs[runA].cfg;
  let fh="<table>";
  const row=(k,v,jumpSeq)=>`<tr${jumpSeq!=null?` class="jump" data-seq="${jumpSeq}" title="jump to this chunk"`:""}><td>${k}</td><td class="r">${dash(v)}</td></tr>`;
  fh+=row("replan cycle (steps, p50/p95)",sc.cycle_p50!=null?`${sc.cycle_p50} / ${sc.cycle_p95}`:null);
  fh+=row("skip on arrival (p50)",sc.skip_p50!=null?sc.skip_p50+(sc.skip_logged_p50!=null?` (logged ${sc.skip_logged_p50})`:""):null);
  fh+=row("executed depth (p50/p95/max)",sc.depth_p50!=null?`${sc.depth_p50} / ${sc.depth_p95} / ${sc.depth_max}`:null);
  fh+=row("server chunk length (p50)",sc.chunk_len_p50);
  fh+=row("stalls >100ms / time stalled",sc.stall_count!=null?`${sc.stall_count} / ${(100*(sc.stalled_frac||0)).toFixed(1)}%`:null);
  fh+=row("starved ticks (buffer=0)",sc.starved_ticks);
  fh+=row("effective rate (Hz)",sc.effective_hz);
  fh+=row("cmd step within / at splice (mrad)",sm.step_within_p50!=null?`${sm.step_within_p50} / ${dash(sm.step_splice_p50)}`:null);
  fh+=row("splice ratio",sm.splice_ratio!=null?`×${sm.splice_ratio}${sm.splice_ratio>=V_SPLICE?" ⚠":""}${runs[runA].meta.stalled_run?" (spans a stall — compare with blocking runs only)":""}`:null);
  fh+=row("splice p95 / max (mrad)",sm.splice_p95!=null?`${sm.splice_p95} / ${sm.splice_max} (chunk ${sm.splice_max_seq})`:null,sm.splice_max_seq);
  const ov=runs[runA].overlap||{};
  fh+=row("chunk overlap disagreement p50/p95 (mrad)",ov.disagree_p50!=null?`${ov.disagree_p50} / ${dash(ov.disagree_p95)} over ${ov.pairs} pairs`:null);
  fh+=row("worst overlap disagreement (mrad)",ov.disagree_max!=null?`${ov.disagree_max} (chunk ${ov.disagree_max_seq})`:null,ov.disagree_max_seq);
  fh+=row("discarded-tail error vs later cmd (mrad)",ov.tail_err_p50);
  fh+=row("cmd jerk within / at splice",sm.jerk_within_p50!=null?`${sm.jerk_within_p50} / ${dash(sm.jerk_splice_p50)}`:null);
  fh+=row("reversing joints at splice / within (median)",sm.rev_joints_splice_p50!=null?`${sm.rev_joints_splice_p50} / ${dash(sm.rev_joints_within_p50)}`:null);
  // Direction continuity is the sharpest smoothness signal: within-chunk tells
  // you whether the MODEL is smooth, at-splice whether the seam is.
  fh+=row("direction continuity within chunk (cos)",sm.dircos_within!=null
    ?`${sm.dircos_within}${sm.dircos_within<=DIRCOS_WARN?" ⚠":""} <span class="dim">(demos ${DIRCOS_REF})</span>`:null);
  fh+=row("direction continuity at splice (cos)",sm.dircos_splice!=null
    ?`${sm.dircos_splice}${sm.dircos_splice<=DIRCOS_WARN?" ⚠":""}`:null);
  // The same question asked of the model's own output rather than of the
  // executed stream. Only these can separate "the policy is noisy" from
  // "our scheduling is stitching it badly".
  const pr=runs[runA].pred||{};
  fh+=row("model plan: direction continuity (cos)",pr.dircos_p50!=null
    ?`${pr.dircos_p50}${pr.dircos_p50<=DIRCOS_WARN?" ⚠":""} <span class="dim">(demos ${DIRCOS_REF}) over ${pr.n_chunks} chunks</span>`:null);
  fh+=row("model plan: steps that reverse",pr.reversal_frac!=null
    ?`${(pr.reversal_frac*100).toFixed(0)}%`:null);
  fh+=row("model plan: acceleration p50/p95 (mrad/tick²)",pr.accel_p50!=null
    ?`${pr.accel_p50} / ${dash(pr.accel_p95)} <span class="dim">on ${dash(pr.step_p50)} mrad steps</span>`:null);
  fh+=row("model plan: last usable horizon step",bestHorizon(runs[runA]));
  if(runs[runA].chunk_reject)
    fh+=row("chunk store",`<span class="warn">rejected</span> <span class="dim">${esc(runs[runA].chunk_reject)}</span>`);
  fh+=row("velocity spike at splice (×median)",sm.vel_spike_ratio_p50);
  fh+=row("limit-guard held left / right",(vi.left!=null||vi.right!=null)?`${(100*(vi.left||0)).toFixed(1)}% / ${(100*(vi.right||0)).toFixed(1)}%`:null);
  fh+="</table>";
  if(cfg){
    fh+=`<div class="note" style="margin-top:6px">config: ${esc(dash(cfg.checkpoint_label)||"?")} · exec ${esc(dash(cfg.execution_horizon))} · prefetch ${cfg.prefetch_enable?("on, lead "+esc(dash(cfg.prefetch_lead))):"off"}${cfg.rtc_enable?' · <span class="dim">rtc_enable was set (no effect: the server drops it)</span>':""} · v${esc(dash(cfg.package_version))}</div>`;
    if(cfg.notes)fh+=`<div class="note">notes: ${esc(cfg.notes)}</div>`;
  }else{
    fh+=`<div class="note" style="margin-top:6px">config unknown — no .meta.json sidecar (log predates logger v0.4)</div>`;
  }
  $("factsbox").innerHTML=fh;

  // cross-links: any timestamped row jumps the viewport there
  document.querySelectorAll("[data-t]").forEach(el=>{
    el.onclick=e=>{e.preventDefault();jumpTo(parseFloat(el.dataset.t))};
  });
  document.querySelectorAll("[data-seq]").forEach(el=>{
    el.onclick=()=>{const t=seqTime(parseInt(el.dataset.seq)); if(t!=null)jumpTo(t,1)};
  });
}

// ------------------------------------------------- profile + distribution
function drawProfile(){
  const cv=$("profcv"); if(!cv||page!=="signals")return;
  const dpr=window.devicePixelRatio||1,W=cv.clientWidth,H=180;
  if(!W)return;
  cv.width=W*dpr;cv.height=H*dpr;cv.style.height=H+"px";
  const g=cv.getContext("2d");g.scale(dpr,dpr);
  const padL=36,padR=8,padT=8,padB=18,iw=W-padL-padR,ih=H-padT-padB;
  g.fillStyle=css("--muted");g.font="9px "+css("--mono").split(",")[0];
  const pa=runs[runA].profile, pb=runB?runs[runB].profile:null;
  const tail=(runs[runA].overlap||{}).tail||null;
  const ks=[...new Set([...pa.k,...(pb?pb.k:[]),...(tail?tail.k:[])])].sort((a,b)=>a-b);
  if(!ks.length){g.fillText("no profile",padL,H/2);return}
  let ymax=1;
  [pa,pb].forEach(p=>{if(p)p.err.concat(p.step).forEach(v=>{if(v!=null&&v>ymax)ymax=v})});
  if(tail)tail.err.forEach(v=>{if(v!=null&&v>ymax)ymax=v});
  ymax*=1.1;
  const kmin=ks[0],kmax=ks[ks.length-1]||1;
  const X=k=>padL+iw*(k-kmin)/Math.max(kmax-kmin,1), Y=v=>padT+ih*(1-v/ymax);
  g.strokeStyle=css("--hairline");g.strokeRect(padL,padT,iw,ih);
  function line(p,key,color,dashed){
    if(!p)return;
    g.strokeStyle=color;g.lineWidth=1.3;g.setLineDash(dashed?[4,3]:[]);
    g.beginPath();let st=false;
    p.k.forEach((k,i)=>{const v=p[key][i]; if(v==null){st=false;return}
      const x=X(k),y=Y(v); st?g.lineTo(x,y):g.moveTo(x,y); st=true});
    g.stroke();g.setLineDash([]);
  }
  line(pa,"err",css("--accent"),false);
  line(pa,"step",css("--accent"),true);
  line(pb,"err",css("--b2"),false);
  line(pb,"step",css("--b2"),true);
  if(tail){
    g.strokeStyle=css("--warn");g.lineWidth=1.3;g.setLineDash([2,3]);
    g.beginPath();let st2=false;
    tail.k.forEach((k,i)=>{const v=tail.err[i]; if(v==null){st2=false;return}
      const x=X(k),y=Y(v); st2?g.lineTo(x,y):g.moveTo(x,y); st2=true});
    g.stroke();g.setLineDash([]);
    g.fillStyle=css("--warn");
    g.fillText("unexecuted tail vs later cmd",padL+4,padT+10);
  }
  g.fillStyle=css("--muted");
  g.fillText(String(Math.round(ymax)),2,padT+8);g.fillText("0",padL-10,padT+ih);
  g.fillText("horizon_idx "+kmin,padL,H-5);g.fillText(String(kmax),W-padR-18,H-5);
  drawCrosshair(g,cv,padL,padT,iw,ih);
  cv._probe=(px,py)=>{
    if(px<padL||px>padL+iw||py<padT||py>padT+ih)return null;
    const kq=kmin+(px-padL)/Math.max(iw,1)*Math.max(kmax-kmin,1);
    let best=null,bd=1e9;
    ks.forEach(k=>{const d=Math.abs(k-kq); if(d<bd){bd=d;best=k}});
    if(best==null)return null;
    const ia=pa.k.indexOf(best), ib=pb?pb.k.indexOf(best):-1;
    const lines=[`step <b>${best}</b> of the chunk`];
    if(ia>=0)lines.push(`${runB?esc(runA)+" ":""}error <b>${dash(pa.err[ia])}</b> mrad · cmd step <b>${dash(pa.step[ia])}</b> mrad`);
    if(ib>=0)lines.push(`${esc(runB)} error <b>${dash(pb.err[ib])}</b> mrad · cmd step <b>${dash(pb.step[ib])}</b> mrad`);
    if(tail){const it=tail.k.indexOf(best);
      if(it>=0&&tail.err[it]!=null)lines.push(`tail vs later cmd: <b>${tail.err[it]}</b> mrad`)}
    return {lines,snapX:X(best)};
  };
}
function drawHist(){
  const cv=$("histcv"); if(!cv||page!=="signals")return;
  const dpr=window.devicePixelRatio||1,W=cv.clientWidth,H=150;
  if(!W)return;
  cv.width=W*dpr;cv.height=H*dpr;cv.style.height=H+"px";
  const g=cv.getContext("2d");g.scale(dpr,dpr);
  const padL=8,padR=8,padT=8,padB=18,iw=W-padL-padR,ih=H-padT-padB;
  g.fillStyle=css("--muted");g.font="9px "+css("--mono").split(",")[0];
  const R=runs[runA], raw=R.raw, ds=R.dstep;
  if(!raw||!ds){g.fillText("needs raw data (omitted for this run)",padL,H/2);return}
  const within=[],at=[];
  for(let i=0;i<ds.length;i++){
    if(ds[i]==null)continue;
    (raw.seq[i+1]!==raw.seq[i]?at:within).push(ds[i]);
  }
  if(!within.length){g.fillText("no data",padL,H/2);return}
  const all=within.concat(at).sort((a,b)=>a-b);
  const xmax=all[Math.floor(all.length*.99)]||1;
  const NB=40;
  function bins(v){const b=new Array(NB).fill(0);
    v.forEach(x=>{b[Math.min(NB-1,Math.floor(x/xmax*NB))]++});
    const m=Math.max(...b,1); return b.map(x=>x/m)}
  const bw=bins(within), ba=at.length?bins(at):null;
  const X=i=>padL+iw*i/NB, Y=v=>padT+ih*(1-v);
  function strip(b,color){
    g.strokeStyle=color;g.lineWidth=1.4;g.beginPath();
    b.forEach((v,i)=>{const x=X(i),y=Y(v); i?g.lineTo(x,y):g.moveTo(x,y)});
    g.stroke();
    g.globalAlpha=.12;g.fillStyle=color;g.beginPath();g.moveTo(X(0),Y(0));
    b.forEach((v,i)=>g.lineTo(X(i),Y(v)));g.lineTo(X(NB-1),Y(0));g.closePath();g.fill();g.globalAlpha=1;
  }
  strip(bw,css("--accent"));
  if(ba)strip(ba,css("--warn"));
  g.fillStyle=css("--muted");
  g.fillText("0",padL,H-5);g.fillText(Math.round(xmax)+" mrad (p99)",W-padR-70,H-5);
  drawCrosshair(g,cv,padL,padT,iw,ih);
  const nW=within.length, nA=at.length;
  cv._probe=(px,py)=>{
    if(px<padL||px>padL+iw||py<padT||py>padT+ih)return null;
    const bi=Math.min(NB-1,Math.max(0,Math.floor((px-padL)/iw*NB)));
    const lo=(bi*xmax/NB), hi2=((bi+1)*xmax/NB);
    const cw=within.filter(v=>v>=lo&&v<hi2).length;
    const ca=at.filter(v=>v>=lo&&v<hi2).length;
    return {lines:[
      `step size <b>${lo.toFixed(1)}–${hi2.toFixed(1)}</b> mrad`,
      `within chunks: <b>${cw}</b> ticks (${nW?(100*cw/nW).toFixed(1):0}%)`,
      `at splices: <b>${ca}</b> ticks (${nA?(100*ca/nA).toFixed(1):0}%)`],
      snapX:X(bi)+iw/NB/2};
  };
}

// ------------------------------------------------------------------- plans
// Which region of its chunk step k belongs to. Derived on the page (not in
// the analysis) so recolouring never means recomputing:
//   skipped  - expired in flight, discarded on arrival (the prefetch cut)
//   executed - actually drove the arm
//   tail     - predicted, then replaced by the next chunk
//
// There is deliberately no "RTC frozen" or "RTC ramp" region. Setting
// rtc_enable only makes the CLIENT send the previous chunk back; the stock
// server drops it (Gr00tPolicy.get_action documents `options` as unused, and
// rebuilds the observation from video/state/language alone, discarding the
// action the client attached). Colouring a band "frozen" would claim the
// model was constrained there when nothing constrained it. The empirical
// check for this is the frozen-region mismatch in Run facts: a large value
// is the evidence that the freeze request had no effect.
function regionOf(k,skip,depth,cfg){
  if(k<skip)return "skipped";
  if(depth>=0&&k<=depth)return "executed";
  return "tail";
}
const REGION_COLOR={skipped:"--ghost",executed:"--accent",tail:"--tail"};
const REGION_LABEL={skipped:"skipped (prefetch cut)",
                    executed:"executed",tail:"discarded tail"};
function planStore(){const P=runs[runA].plans; return (P&&!P.omitted)?P:null}
function planHintText(){
  return "Each line is one chunk's whole plan, coloured by region. Click a panel "
    +"to enlarge it, then scroll to zoom and drag to pan inside it — the grid "
    +"itself no longer moves. A panel too narrow to separate its plans says so.";
}

function drawPlanPanel(cv,j,big){
  const dpr=window.devicePixelRatio||1,W=cv.clientWidth,H=big?420:190;
  if(!W)return;
  cv.width=W*dpr;cv.height=H*dpr;cv.style.height=H+"px";
  const g=cv.getContext("2d");g.scale(dpr,dpr);
  const padL=52,padR=8,padT=8,padB=18,iw=W-padL-padR,ih=H-padT-padB;
  const mono=css("--mono").split(",")[0];
  g.fillStyle=css("--muted");g.font=(big?11:10)+"px "+mono;
  const P=planStore();
  if(!P){g.fillText("no chunk file for this run",padL,H/2);return}
  const arrs=P.j[j];
  if(!arrs){g.fillText("joint not in the chunk store",padL,H/2);return}
  const[t0,t1]=viewRange(big);
  const cfg=runs[runA].cfg;
  let ymin=Infinity,ymax=-Infinity;const vis=[];
  for(let c=0;c<P.seq.length;c++){
    const a=P.t0[c], b=a+(P.H-1)*P.tick_s;
    if(b<t0||a>t1)continue;
    vis.push(c);
    arrs[c].forEach(v=>{if(v==null)return; if(v<ymin)ymin=v; if(v>ymax)ymax=v});
  }
  if(!isFinite(ymin)){g.fillText("no plans in this window",padL,H/2);return}
  if(ymax-ymin<1e-9){ymax+=.01;ymin-=.01}
  const pd=(ymax-ymin)*.08;ymin-=pd;ymax+=pd;
  const X=t=>padL+iw*(t-t0)/(t1-t0), Y=v=>padT+ih*(1-(v-ymin)/(ymax-ymin));

  // Whether a plan is legible depends on PIXELS per chunk, not on seconds.
  // The old rule hid every plan whenever the window exceeded a fixed number of
  // seconds, which meant a panel at full range drew nothing but the red
  // commanded line and looked broken. Now the same run is drawn in the small
  // panel or not according to how much room each chunk actually gets, and the
  // enlarged view - being four times wider - shows plans the grid cannot.
  const spacing=iw/Math.max(vis.length,1);
  const drawPlans=spacing>=PLAN_MIN_PX;

  // gridlines, so a value can be read off this panel like any other
  g.textAlign="right";
  niceTicks(ymin,ymax,big?5:3).forEach(v=>{
    const y=Y(v);
    g.strokeStyle=css("--hairline");g.globalAlpha=.4;g.lineWidth=1;
    g.beginPath();g.moveTo(padL,y);g.lineTo(padL+iw,y);g.stroke();g.globalAlpha=1;
    g.fillStyle=css("--muted");g.fillText(v.toFixed(2),padL-6,y+3);
  });
  g.textAlign="left";

  g.save();g.beginPath();g.rect(padL,padT,iw,ih);g.clip();
  if(drawPlans){
    // Alpha falls as more plans overlap so a dense window stays readable, but
    // never below the floor that made these invisible in the first place.
    const al=Math.max(.55,Math.min(.95,18/Math.max(vis.length,1)));
    // Weight follows what each region MEANS, because chunks overlap: a later
    // chunk's skipped head is drawn over the previous chunk's executed steps,
    // so if skipped were the boldest it would bury the one line that actually
    // drove the arm. Executed loudest, then the discarded tail (where the
    // interesting divergence is), then the head that never had a chance to run.
    const WEIGHT={executed:{a:1.0,w:2.4},tail:{a:.8,w:1.7},skipped:{a:.45,w:1.2}};
    vis.forEach(c=>{
      const skip=P.skip[c],depth=P.depth[c],y=arrs[c],base=P.t0[c];
      let k=0;
      while(k<P.H-1){
        const reg=regionOf(k,skip,depth,cfg);
        let k2=k;
        while(k2<P.H-1&&regionOf(k2,skip,depth,cfg)===reg)k2++;
        const wt=WEIGHT[reg]||WEIGHT.skipped;
        g.strokeStyle=css(REGION_COLOR[reg]);
        g.globalAlpha=Math.min(1,al*wt.a+(reg==="executed"?.15:0));
        g.lineWidth=wt.w;
        g.setLineDash(reg==="tail"?[4,3]:[]);
        g.beginPath();let st=false;
        for(let i=k;i<=k2&&i<P.H;i++){
          const v=y[i]; if(v==null){st=false;continue}
          const x=X(base+i*P.tick_s),yy=Y(v);
          st?g.lineTo(x,yy):g.moveTo(x,yy); st=true;
        }
        g.stroke();g.setLineDash([]);
        k=k2;
      }
      // the prefetch cut: everything left of here expired while the request
      // was in flight and was discarded on arrival.
      // Drawn as a tick on the bottom axis, not a full-height rule. One rule
      // per chunk is a picket fence: measured on a 24-chunk window they used
      // more pixels than the executed plan itself and became the loudest thing
      // on the panel, which is the opposite of what an annotation should be.
      if(skip>0){
        const xs=X(base+skip*P.tick_s);
        g.strokeStyle=css("--cut");g.globalAlpha=.8;g.lineWidth=1.4;
        g.beginPath();g.moveTo(xs,padT+ih);g.lineTo(xs,padT+ih-9);g.stroke();
      }
      // where the next chunk superseded this one
      if(depth>=0&&depth<P.H-1){
        const xc=X(base+(depth+1)*P.tick_s);
        g.strokeStyle=css("--cut");g.globalAlpha=.55;g.lineWidth=1.2;
        g.setLineDash([2,2]);g.beginPath();g.moveTo(xc,padT);g.lineTo(xc,padT+9);
        g.stroke();g.setLineDash([]);
      }
      g.globalAlpha=1;
    });
  }
  // The commanded trace goes on top as the reference, but at a weight that
  // reads as one line among many rather than a wall of red over the plans.
  const tr=runs[runA].traces[j];
  if(tr&&tr.cmd){
    const tt=tr.cmd[0],yy=tr.cmd[1];
    g.strokeStyle=css("--cmd");g.lineWidth=drawPlans?1.3:2;g.globalAlpha=drawPlans?.7:1;
    g.beginPath();
    let st=false;
    for(let i=0;i<tt.length;i++){
      if(tt[i]<t0||tt[i]>t1){st=false;continue}
      const x=X(tt[i]),v=Y(yy[i]); st?g.lineTo(x,v):g.moveTo(x,v); st=true;
    }
    g.stroke();g.globalAlpha=1;
  }
  g.restore();
  g.strokeStyle=css("--hairline");g.strokeRect(padL,padT,iw,ih);
  if(!drawPlans){
    const msg=big?"plans hidden - zoom in (scroll) to separate them"
                 :"click to enlarge and see every plan";
    const w=g.measureText(msg).width;
    g.fillStyle=css("--surface");g.globalAlpha=.9;
    g.fillRect(padL+4,padT+4,w+10,15);g.globalAlpha=1;
    g.fillStyle=css("--muted");g.fillText(msg,padL+9,padT+15);
  }
  g.fillStyle=css("--muted");
  g.fillText(t0.toFixed(1)+"s",padL,H-5);
  g.textAlign="right";g.fillText(t1.toFixed(1)+"s",padL+iw,H-5);g.textAlign="left";
  drawCrosshair(g,cv,padL,padT,iw,ih);

  g.restore();
  g.fillStyle=css("--muted");
  g.fillText(ymax.toFixed(2),2,padT+8);g.fillText(ymin.toFixed(2),2,padT+ih);
  g.fillText(t1.toFixed(t1-t0<5?2:0)+"s",W-padR-34,H-4);
  g.fillText(t0.toFixed(t1-t0<5?2:0),padL,H-4);
  cv._probe=(px,py)=>{
    if(px<padL||px>padL+iw||py<padT||py>padT+ih)return null;
    const tq=t0+(px-padL)/iw*(t1-t0);
    const lines=["<b>"+short(j)+"</b> @ "+tq.toFixed(2)+"s"];
    let hits=0;
    vis.forEach(c=>{
      const k=Math.round((tq-P.t0[c])/P.tick_s);
      if(k<0||k>=P.H)return;
      const v=arrs[c][k]; if(v==null)return;
      hits++;
      if(hits<=4){
        const reg=regionOf(k,P.skip[c],P.depth[c],cfg);
        lines.push("chunk <b>"+P.seq[c]+"</b> step "+k+" · <b>"+v.toFixed(3)+"</b> · "+REGION_LABEL[reg]);
      }
    });
    if(hits>4)lines.push("… and "+(hits-4)+" more plans here");
    return hits?{lines:lines}:null;
  };
}

// ------------------------------------------- "across the horizon" charts
// One generic line chart over horizon step k, shared by the two prediction
// panels. Everything that varies between them is passed in, so adding a
// series or changing a colour is a one-line edit and never a new draw
// function.
//   series: [{v:[...], color:"--accent", label:"…", dash:bool, dp:int}]
//   opts:   {ymin, ymax, unit, refs:[{v,color,label}], height}
// Round tick values covering [lo,hi] at roughly `want` intervals, so a reader
// can put a number on any point instead of interpolating between the two
// endpoint labels the earlier version drew.
function niceTicks(lo,hi,want){
  const span=hi-lo; if(!(span>0))return [lo];
  const raw=span/Math.max(want,1), mag=Math.pow(10,Math.floor(Math.log10(raw)));
  const step=[1,2,2.5,5,10].map(m=>m*mag).find(v=>v>=raw)||10*mag;
  const out=[]; for(let v=Math.ceil(lo/step)*step; v<=hi+1e-9; v+=step)out.push(Math.round(v/step)*step);
  return out;
}
function fmtTick(v,unit){
  const a=Math.abs(v);
  const s=a>=100?v.toFixed(0):a>=10?v.toFixed(1):v.toFixed(2).replace(/0$/,"");
  return s.replace(/\.0+$/,"");
}
// Swatch legend rendered as HTML above the canvas, not painted inside it in
// 9px type over the data.
function legendHTML(items){
  return items.map(i=>'<i style="background:'+css(i.color)
    +(i.alpha!=null?';opacity:'+i.alpha+';outline:1px solid '+css(i.color):"")
    +(i.dash?';height:0;border-top:2px dashed '+css(i.color):"")+'"></i>'+esc(i.label)).join("");
}

function drawAcrossHorizon(cv,series,opts){
  const dpr=window.devicePixelRatio||1,W=cv.clientWidth,H=opts.height;
  if(!W)return;
  cv.width=W*dpr;cv.height=H*dpr;cv.style.height=H+"px";
  const g=cv.getContext("2d");g.scale(dpr,dpr);
  const padL=58,padR=12,padT=26,padB=30,iw=W-padL-padR,ih=H-padT-padB;
  const mono=css("--mono").split(",")[0];
  g.font="10px "+mono;
  const P=runs[runA].pred;
  if(!P){g.fillStyle=css("--muted");g.font="12px "+css("--disp").split(",")[0];
    g.fillText("no chunk file for this run — nothing to read the plan from",padL,H/2);return}
  const kmax=Math.max(...series.map(s=>s.v.length))-1;
  if(kmax<1){g.fillStyle=css("--muted");g.fillText("chunks too short to measure",padL,H/2);return}
  const X=k=>padL+iw*k/Math.max(kmax,1);
  const Y=v=>padT+ih*(1-(v-opts.ymin)/Math.max(opts.ymax-opts.ymin,1e-9));

  const S=planStore(), sch=runs[runA].schedule||{}, cfg=runs[runA].cfg;
  const med=a=>{const b=a.slice().sort((x,y)=>x-y);return b.length?b[Math.floor(b.length/2)]:0};
  const skipMed=S?med(S.skip):(sch.skip_p50!=null?Math.round(sch.skip_p50):0);
  const depthMed=S?med(S.depth):(sch.depth_p95!=null?Math.round(sch.depth_p95):-1);

  // region bands, and their names ABOVE the plot so they never sit on the data
  let k=0;
  while(k<=kmax){
    const reg=regionOf(k,skipMed,depthMed,cfg);
    let k2=k; while(k2<=kmax&&regionOf(k2,skipMed,depthMed,cfg)===reg)k2++;
    g.fillStyle=css(REGION_COLOR[reg]);g.globalAlpha=.16;
    g.fillRect(X(k),padT,Math.max(X(k2)-X(k),1),ih);g.globalAlpha=1;
    const w=X(k2)-X(k);
    if(w>10){
      g.fillStyle=css(REGION_COLOR[reg]);
      g.fillRect(X(k),padT-14,Math.max(w-1,1),3);
      const lab=REGION_LABEL[reg];
      if(w>g.measureText(lab).width+8)g.fillText(lab,X(k)+3,padT-5);
    }
    k=k2;
  }

  // horizontal gridlines with labelled ticks — the point of this rewrite
  const ticks=niceTicks(opts.ymin,opts.ymax,4);
  g.textAlign="right";
  ticks.forEach(v=>{
    const y=Y(v);
    g.strokeStyle=css("--hairline");g.globalAlpha=v===0?.9:.45;g.lineWidth=1;
    g.beginPath();g.moveTo(padL,y);g.lineTo(padL+iw,y);g.stroke();g.globalAlpha=1;
    g.fillStyle=css("--muted");g.fillText(fmtTick(v,opts.unit),padL-6,y+3);
  });
  g.textAlign="left";
  if(opts.unit){g.fillStyle=css("--muted");g.fillText(opts.unit,padL-6-g.measureText(opts.unit).width,padT-5)}

  // Reference lines carry no in-plot text: the legend above names them, and a
  // label inside the frame necessarily sits on top of the curve it explains.
  (opts.refs||[]).forEach(r=>{
    if(r.v<opts.ymin||r.v>opts.ymax)return;
    const y=Y(r.v);
    g.strokeStyle=css(r.color);g.globalAlpha=.9;g.lineWidth=1.2;g.setLineDash([5,4]);
    g.beginPath();g.moveTo(padL,y);g.lineTo(padL+iw,y);g.stroke();
    g.setLineDash([]);g.globalAlpha=1;
  });

  if(opts.markUsable){
    const w=usableWindow(runs[runA]);
    if(w){
      g.strokeStyle=css("--good");g.lineWidth=2.5;
      g.beginPath();g.moveTo(X(w.from),padT+3);g.lineTo(X(w.to),padT+3);g.stroke();
      [w.from,w.to].forEach(kk=>{g.beginPath();g.moveTo(X(kk),padT);g.lineTo(X(kk),padT+8);g.stroke()});
    }
  }
  g.strokeStyle=css("--hairline");g.globalAlpha=1;g.strokeRect(padL,padT,iw,ih);

  series.forEach(s=>{
    g.strokeStyle=css(s.color);g.lineWidth=1.8;
    if(s.dash)g.setLineDash([3,3]);
    g.beginPath();let started=false;
    s.v.forEach((val,i)=>{if(val==null){started=false;return}
      const x=X(i),y=Y(val); started?g.lineTo(x,y):g.moveTo(x,y); started=true});
    g.stroke();g.setLineDash([]);
  });

  // x axis
  g.fillStyle=css("--muted");
  niceTicks(0,kmax,6).forEach(v=>{
    if(v<0||v>kmax)return;
    g.fillText(String(Math.round(v)),X(v)-4,padT+ih+13);
  });
  g.fillText("horizon step k  (0 = first step of the chunk)",padL,H-4);
  drawCrosshair(g,cv,padL,padT,iw,ih);
  cv._probe=(px,py)=>{
    if(px<padL||px>padL+iw||py<padT||py>padT+ih)return null;
    const kq=Math.max(0,Math.min(kmax,Math.round((px-padL)/iw*kmax)));
    const lines=["horizon step <b>"+kq+"</b> — "+REGION_LABEL[regionOf(kq,skipMed,depthMed,cfg)]];
    series.forEach(s=>{const v=s.v[kq];
      // an explicit empty unit means "unitless", not "fall back to the axis"
      if(v!=null)lines.push(s.label+": <b>"+v.toFixed(s.dp)+"</b> "
        +(s.unit!==undefined?s.unit:opts.unit))});
    return {lines,snapX:X(kq)};
  };
}

// The stretch of the horizon the policy actually plans coherently: the longest
// unbroken run of steps whose direction cosine holds at or above
// DIRCOS_USABLE. This is the window an execution horizon should sit inside —
// executing past its end means driving the arm with the part of the plan the
// model was no longer predicting a trajectory in.
function usableWindow(r){
  const P=r.pred; if(!P||!P.dircos_k)return null;
  const d=P.dircos_k;
  let bi=-1,bl=0,i=0;
  while(i<d.length){
    if(d[i]==null||d[i]<DIRCOS_USABLE){i++;continue}
    let j=i; while(j<d.length&&d[j]!=null&&d[j]>=DIRCOS_USABLE)j++;
    if(j-i>bl){bl=j-i;bi=i}
    i=j;
  }
  return bi<0?null:{from:bi,to:bi+bl-1,len:bl};
}
// Where this run's execution actually landed on the horizon — measured, not
// configured. It starts at the prefetch cut and ends at the deepest step
// reached before the next chunk took over; with prefetch that is well short of
// the configured execution horizon, which is only the fallback. Clamped to the
// chunk, which cannot be executed past its last step.
function execSpan(r){
  const sch=r.schedule||{}, H=(r.pred||{}).H;
  const from=sch.skip_p50!=null?Math.round(sch.skip_p50):0;
  let to=sch.depth_p95!=null?Math.round(sch.depth_p95):null;
  if(to==null&&r.cfg&&r.cfg.execution_horizon!=null)to=from+r.cfg.execution_horizon-1;
  if(to==null)return null;
  if(H)to=Math.min(to,H-1);
  return to>=from?{from:from,to:to}:null;
}
function bestHorizon(r){
  const P=r.pred; if(!P||!P.dircos_k)return null;
  const w=usableWindow(r);
  if(!w)return '<span class="warn">none</span> <span class="dim">— no run of steps holds '
    +DIRCOS_USABLE+'; the plan is noisy end to end</span>';
  let out='k='+w.from+'–'+w.to+' <span class="dim">('+w.len+' steps at or above '+DIRCOS_USABLE+')</span>';
  const e=execSpan(r);
  if(e){
    const outside=Math.max(0,w.from-e.from)+Math.max(0,e.to-w.to);
    out+='<br><span class="dim">this run executed k='+e.from+'–'+e.to+' — '
      +(outside?'<b>'+outside+' of those '+(e.to-e.from+1)+' steps sit outside it</b> ⚠':'inside it')+'</span>';
  }
  return out;
}

function drawPredCharts(){
  if(page!=="plans")return;
  const P=runs[runA].pred, cos=$("hzcos"), acc=$("hzacc");
  const lgc=$("hzcosLg"), lga=$("hzaccLg");
  if(lgc)lgc.innerHTML=legendHTML([{color:"--cmd",label:"direction cosine of the plan"},
    {color:"--good",label:"demonstrations ("+DIRCOS_REF+")",dash:true},
    {color:"--accent",label:"executed"},{color:"--ghost",label:"skipped (prefetch cut)"},
    {color:"--tail",label:"discarded tail"}]);
  if(lga)lga.innerHTML=legendHTML([{color:"--act",label:"movement per step (mrad)"},
    {color:"--warn",label:"acceleration (mrad/tick²)"},
    {color:"--accent",label:"executed"},{color:"--ghost",label:"skipped (prefetch cut)"},
    {color:"--tail",label:"discarded tail"}]);
  if(cos)drawAcrossHorizon(cos,P?[{v:P.dircos_k,color:"--cmd",label:"direction cosine",dp:2,unit:""}]:[{v:[],color:"--cmd",label:"",dp:2}],
    {ymin:-1,ymax:1,unit:"cos",height:230,markUsable:true,
     refs:[{v:DIRCOS_REF,color:"--good"}]});
  if(acc){
    const mx=P?Math.max(1,...[...(P.accel_k||[]),...(P.step_k||[])].filter(v=>v!=null)):1;
    drawAcrossHorizon(acc,P?[{v:P.step_k,color:"--act",label:"movement per step",dp:1,unit:"mrad"},
                             {v:P.accel_k,color:"--warn",label:"acceleration",dp:1,unit:"mrad/tick²"}]:[{v:[],color:"--act",label:"",dp:1}],
      {ymin:0,ymax:Math.ceil(mx*1.1),unit:"mrad",height:205,markUsable:true});
  }
}

function drawAgg(){
  const cv=$("aggcv"); if(!cv||page!=="plans")return;
  const alg=$("aggLg");
  if(alg)alg.innerHTML=legendHTML([
    {color:"--act",label:"median over every chunk pair"},
    {color:"--act",label:"p10–p90 band",alpha:.22},
    {color:"--accent",label:"executed"},{color:"--ghost",label:"skipped (prefetch cut)"},
    {color:"--tail",label:"discarded tail"},
    {color:"--cut",label:"prefetch cut"}]);
  const dpr=window.devicePixelRatio||1,W=cv.clientWidth,H=220;
  if(!W)return;
  cv.width=W*dpr;cv.height=H*dpr;cv.style.height=H+"px";
  const g=cv.getContext("2d");g.scale(dpr,dpr);
  const padL=58,padR=12,padT=18,padB=22,iw=W-padL-padR,ih=H-padT-padB;
  g.fillStyle=css("--muted");g.font="10px "+css("--mono").split(",")[0];
  const P=planStore(), agg=P&&P.agg;
  if(!agg){g.fillText(P?"not enough chunk pairs to aggregate":"no chunk file for this run",padL,H/2);return}
  const cfg=runs[runA].cfg;
  const kmax=agg.k[agg.k.length-1]||1;
  let ymax=1; agg.p90.forEach(v=>{if(v>ymax)ymax=v}); ymax*=1.1;
  const X=k=>padL+iw*k/Math.max(kmax,1), Y=v=>padT+ih*(1-v/ymax);
  const med=a=>{const b=a.slice().sort((x,y)=>x-y);return b.length?b[Math.floor(b.length/2)]:0};
  const skipMed=med(P.skip), depthMed=med(P.depth);
  let k=0;
  while(k<=kmax){
    const reg=regionOf(k,skipMed,depthMed,cfg);
    let k2=k; while(k2<=kmax&&regionOf(k2,skipMed,depthMed,cfg)===reg)k2++;
    g.fillStyle=css(REGION_COLOR[reg]);g.globalAlpha=.10;
    g.fillRect(X(k),padT,Math.max(X(k2)-X(k),1),ih);
    g.globalAlpha=1;
    if(X(k2)-X(k)>56){g.fillStyle=css(REGION_COLOR[reg]);g.fillText(REGION_LABEL[reg],X(k)+3,padT+10)}
    k=k2;
  }
  if(skipMed>0&&skipMed<=kmax){
    g.strokeStyle=css("--cut");g.lineWidth=1.2;g.beginPath();
    g.moveTo(X(skipMed),padT);g.lineTo(X(skipMed),padT+ih);g.stroke();
    g.fillStyle=css("--cut");g.fillText("prefetch cut",X(skipMed)+3,padT+ih-4);
  }
  if(depthMed>=0&&depthMed<kmax){
    g.strokeStyle=css("--cut");g.globalAlpha=.6;g.lineWidth=1;g.setLineDash([2,2]);
    g.beginPath();g.moveTo(X(depthMed+1),padT);g.lineTo(X(depthMed+1),padT+ih);
    g.stroke();g.setLineDash([]);g.globalAlpha=1;
  }
  // labelled gridlines, same as the horizon charts
  niceTicks(0,ymax,4).forEach(v=>{
    const y=Y(v);
    g.strokeStyle=css("--hairline");g.globalAlpha=.45;g.lineWidth=1;
    g.beginPath();g.moveTo(padL,y);g.lineTo(padL+iw,y);g.stroke();g.globalAlpha=1;
    g.fillStyle=css("--muted");g.textAlign="right";g.fillText(fmtTick(v),padL-6,y+3);g.textAlign="left";
  });
  g.strokeStyle=css("--hairline");g.strokeRect(padL,padT,iw,ih);
  g.fillStyle=css("--act");g.globalAlpha=.22;g.beginPath();
  agg.k.forEach((kk,i)=>{const x=X(kk),y=Y(agg.p90[i]); i?g.lineTo(x,y):g.moveTo(x,y)});
  for(let i=agg.k.length-1;i>=0;i--)g.lineTo(X(agg.k[i]),Y(agg.p10[i]));
  g.closePath();g.fill();g.globalAlpha=1;
  g.strokeStyle=css("--act");g.lineWidth=2;g.beginPath();
  agg.k.forEach((kk,i)=>{const x=X(kk),y=Y(agg.p50[i]); i?g.lineTo(x,y):g.moveTo(x,y)});
  g.stroke();
  g.fillStyle=css("--muted");
  g.fillText("mrad",2,padT-4);
  g.fillText("steps past the chunk switch",padL+iw/2-62,H-5);
  g.fillText(String(kmax),W-padR-14,H-5);g.fillText("0",padL,H-5);
  drawCrosshair(g,cv,padL,padT,iw,ih);
  cv._probe=(px,py)=>{
    if(px<padL||px>padL+iw||py<padT||py>padT+ih)return null;
    const kq=Math.round((px-padL)/iw*kmax);
    const i=agg.k.indexOf(kq); if(i<0)return null;
    return {lines:["<b>"+kq+"</b> steps past the switch",
      "median <b>"+agg.p50[i]+"</b> mrad · p10–p90 "+agg.p10[i]+"–"+agg.p90[i],
      REGION_LABEL[regionOf(kq,skipMed,depthMed,cfg)]+" · "+agg.n[i]+" chunk pairs"],
      snapX:X(kq)};
  };
}

function renderPlans(){
  const P=runs[runA].plans;
  let chips=metaChip(runA,"");
  if(P&&P.omitted)chips+='<span class="chip">plans omitted — '+P.n_chunks+' chunks, over the size budget</span>';
  else if(runs[runA].chunk_reject)chips+='<span class="chip warn">chunk store rejected — '+esc(runs[runA].chunk_reject)+'</span>';
  else if(!P)chips+='<span class="chip">no .chunks.npz — this run predates chunk logging</span>';
  $("planChips").innerHTML=chips;
  let lg="";
  ["executed","skipped","tail"].forEach(r=>{
    lg+='<i style="background:'+css(REGION_COLOR[r])+'"></i>'+REGION_LABEL[r];
  });
  lg+='<i style="background:'+css("--cut")+';outline:1px solid '+css("--hairline")+'"></i>axis ticks: prefetch cut (below) / superseded (above)';
  lg+='<i style="background:'+css("--cmd")+'"></i>actually commanded';
  $("planLegend").innerHTML=lg;
  $("planHint").textContent=planHintText();
  const grid=$("plangrid"); grid.innerHTML="";
  panelReg.length=0;
  joints().forEach(j=>{
    const pnl=document.createElement("div"); pnl.className="panel";
    pnl.innerHTML='<div class="ttl" title="enlarge">'+short(j)+'</div>';
    pnl.firstChild.onclick=()=>openModal(j,"plans");
    const cv=document.createElement("canvas"); pnl.appendChild(cv); grid.appendChild(pnl);
    cv.style.cursor="zoom-in"; cv.title="click to enlarge, then scroll to zoom";
    cv.onclick=()=>openModal(j,"plans");
    panelReg.push({cv:cv,joint:j,plans:true,big:false});
    requestAnimationFrame(()=>drawPlanPanel(cv,j,false));
  });
  // renderPlans() clears panelReg, so an open enlarged view has to be put back
  // or the next resize/run-switch orphans it and it stops redrawing.
  if(modalJoint!=null&&modalKind==="plans"){
    const mc=$("mcanvas");
    panelReg.push({cv:mc,joint:modalJoint,big:true,plans:true});
    drawWhenSized(mc,()=>drawPlanPanel(mc,modalJoint,true));
  }
  requestAnimationFrame(drawPredCharts);
  requestAnimationFrame(drawAgg);
}

// ------------------------------------------------------------------ matrix
function renderMatrix(){
  const cols=[
    ["run",r=>esc(r.name)],["ckpt",r=>r.cfg?esc(dash(r.cfg.checkpoint_label)):"—"],
    ["mode",r=>r.cfg?(r.cfg.prefetch_enable?"prefetch":"blocking"):"—"],
    ["exec",r=>r.cfg?dash(r.cfg.execution_horizon):"—"],
    ["cycle p50",r=>dash((r.schedule||{}).cycle_p50)],
    ["skip p50",r=>dash((r.schedule||{}).skip_p50)],
    ["depth p95",r=>dash((r.schedule||{}).depth_p95)],
    ["splice ×",r=>dash((r.smooth||{}).splice_ratio)],
    ["dir cos in/splice",r=>{const s=r.smooth||{};
      return s.dircos_within==null?"—":`${s.dircos_within} / ${dash(s.dircos_splice)}`}],
    ["overlap mrad",r=>dash((r.overlap||{}).disagree_p50)],
    ["plan cos",r=>dash((r.pred||{}).dircos_p50)],
    ["usable k",r=>{const w=usableWindow(r); if(!w)return "—";
      const e=execSpan(r), bad=e&&(e.from<w.from||e.to>w.to);
      return `${w.from}–${w.to}${bad?" ⚠":""}`}],
    ["stalls",r=>dash((r.schedule||{}).stall_count)],
    ["eff Hz",r=>dash((r.schedule||{}).effective_hz)],
    ["grasp ✓/att",r=>{const g=graspSummary(r);return g.att?`${g.succ}/${g.att}`:"—"}],
    ["lat p50/p95",r=>r.meta.lat_p50!=null?`${r.meta.lat_p50}/${dash((r.schedule||{}).lat_p95)}`:"—"],
    ["limit %",r=>{const v=r.violations||{};return (v.left!=null||v.right!=null)?(100*Math.max(v.left||0,v.right||0)).toFixed(1):"—"}],
  ];
  let h="<table><tr>"+cols.map(c=>`<th${c[0]==="run"?"":' class="r"'}>${c[0]}</th>`).join("")+"<th>verdicts</th></tr>";
  visibleNames().forEach(n=>{
    const r={...runs[n],name:n};
    h+="<tr>"+cols.map((c,i)=>`<td${i?' class="r"':""}>${c[1](r)}</td>`).join("");
    const vs=verdicts(runs[n]);
    h+=`<td>${vs.length?vs.map(v=>`<span style="color:${v.ok?"var(--good)":"var(--warn)"};font-weight:600">${v.ok?"✓":"✗"} ${v.k}</span>`).join(" &nbsp;"):"—"}</td></tr>`;
  });
  $("matrixbox").innerHTML=h+"</table>";
  requestAnimationFrame(()=>{
    scatter($("sc1"),visibleNames().map(n=>({x:(runs[n].schedule||{}).cycle_p50,y:(runs[n].smooth||{}).splice_ratio,l:n})),"cycle p50 (steps)","splice ratio",{hline:V_SPLICE});
    scatter($("sc2"),visibleNames().map(n=>{const g=graspSummary(runs[n]);return {x:(runs[n].schedule||{}).depth_p95,y:g.att?g.succ/g.att:null,l:n}}),"depth p95 (steps)","grasp success rate",{vline:V_DEPTH,ymax:1});
  });
}
function scatter(cv,pts,xl,yl,opt){
  opt=opt||{};
  const dpr=window.devicePixelRatio||1,W=cv.clientWidth,H=260;
  if(!W)return;
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
  cv._probe=(px,py)=>{
    let best=null,bd=1e9;
    data.forEach(p2=>{const d=Math.hypot(X(p2.x)-px,Y(p2.y)-py); if(d<bd){bd=d;best=p2}});
    if(!best||bd>26)return null;
    return {lines:[`<b>${esc(best.l)}</b>`,
      `${xl}: <b>${best.x}</b>`,
      `${yl}: <b>${Math.round(best.y*1000)/1000}</b>`]};
  };
}
window.addEventListener("resize",()=>render());
render();
</script>
"""
