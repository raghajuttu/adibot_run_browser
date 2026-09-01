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
<div class="modal" id="modal"><div class="mbox">
  <div class="ttl"><span id="mttl"></span><button onclick="closeModal()">close</button></div>
  <div class="panel" style="cursor:default"><canvas id="mcanvas" height="420"></canvas></div>
</div></div>
<script>
const DATA=__DATA__;
const HI_ERR=__HI_ERR__, HI_NM=__HI_NM__;
const V_SPLICE=__V_SPLICE__, V_DEPTH=__V_DEPTH__;
const runs=DATA.runs, names=Object.keys(runs);
let runA=names[0], runB="", view="track", side="all", page="signals";
let vp=null;               // shared viewport {t0,t1}; null = full range
let modalJoint=null;       // joint shown in the enlarged modal, or null
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
function viewRange(){
  if(vp)return[vp.t0,vp.t1];
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
    g.strokeStyle=css("--cmd"); g.lineWidth=.6;
    g.globalAlpha=vb.length>40?.15:.45;
    g.beginPath();
    vb.forEach(k=>{g.moveTo(X(bounds[k]),padT);g.lineTo(X(bounds[k]),padT+ih)});
    g.stroke(); g.globalAlpha=1;
  }
  sers.forEach(s=>drawSeries(g,s,X,Y,s.i0,s.i1,iw));
  // mid zoom: chunk labels; close zoom: splice size in mrad
  const rawA=runs[runA].raw;
  if(vb.length&&vb.length<=14){
    g.fillStyle=css("--cmd"); g.globalAlpha=.8;
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
  g.restore();
  g.fillStyle=css("--muted");
  g.fillText(ymax.toFixed(2),2,padT+8); g.fillText(ymin.toFixed(2),2,padT+ih);
  g.fillText(t1.toFixed(t1-t0<5?2:0)+"s",W0-padR-34,H-4); g.fillText(t0.toFixed(t1-t0<5?2:0),padL,H-4);
}
function redrawAll(){
  panelReg.forEach(p=>drawPanel(p.cv,p.joint,p.big));
}
let rafPending=false;
function scheduleRedraw(){
  if(rafPending)return; rafPending=true;
  requestAnimationFrame(()=>{rafPending=false;redrawAll()});
}

// ------------------------------------------------------------ interaction
function clampVp(){
  if(!vp)return;
  const[r0,r1]=(()=>{const a=runRange(runA); if(!runB)return a;
    const b=runRange(runB); return[Math.min(a[0],b[0]),Math.max(a[1],b[1])]})();
  const span=Math.max(vp.t1-vp.t0,0.02);
  vp.t0=Math.max(r0,Math.min(vp.t0,r1-span));
  vp.t1=Math.min(r1,Math.max(vp.t1,vp.t0+0.02));
  if(vp.t0<=r0&&vp.t1>=r1)vp=null;   // fully zoomed out again
}
function attachZoom(cv){
  cv.addEventListener("wheel",e=>{
    e.preventDefault();
    const rect=cv.getBoundingClientRect();
    const frac=Math.min(1,Math.max(0,(e.clientX-rect.left-46)/(rect.width-52)));
    const[t0,t1]=viewRange();
    const cursorT=t0+frac*(t1-t0);
    const f=Math.pow(1.25,e.deltaY>0?1:-1);       // >0 = zoom out
    vp={t0:cursorT-(cursorT-t0)*f, t1:cursorT+(t1-cursorT)*f};
    clampVp(); scheduleRedraw();
  },{passive:false});
  let dragX=null,dragVp=null;
  cv.addEventListener("pointerdown",e=>{dragX=e.clientX;const[a,b]=viewRange();dragVp=[a,b];cv.setPointerCapture(e.pointerId)});
  cv.addEventListener("pointermove",e=>{
    if(dragX==null)return;
    const rect=cv.getBoundingClientRect();
    const dt=(e.clientX-dragX)/(rect.width-52)*(dragVp[1]-dragVp[0]);
    vp={t0:dragVp[0]-dt,t1:dragVp[1]-dt};
    clampVp(); scheduleRedraw();
  });
  const end=e=>{dragX=null;dragVp=null};
  cv.addEventListener("pointerup",end); cv.addEventListener("pointercancel",end);
  cv.addEventListener("dblclick",()=>{vp=null;scheduleRedraw()});
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
function closeModal(){
  $("modal").classList.remove("on");
  modalJoint=null;
  for(let i=panelReg.length-1;i>=0;i--)if(panelReg[i].big)panelReg.splice(i,1);
}
function openModal(j){
  modalJoint=j;
  $("modal").classList.add("on");
  $("mttl").textContent=short(j)+" — "+(VIEW_TITLES[view]||view);
  panelReg.push({cv:$("mcanvas"),joint:j,big:true});
  requestAnimationFrame(()=>drawPanel($("mcanvas"),j,true));
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
$("cbBounds").onchange=scheduleRedraw; $("cbGrasp").onchange=scheduleRedraw;

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
  if(cfg) mode=` · ${cfg.prefetch_enable?"prefetch":"blocking"}${cfg.rtc_enable?"+RTC":""}`;
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
  $("pageMatrix").style.display=page==="matrix"?"":"none";
  if(page==="matrix"){renderMatrix();return}
  $("chips").innerHTML=metaChip(runA,"")+(runB?metaChip(runB,"b"):"");
  const unit=view==="track"?"rad":view==="vel"?"rad/s":view==="eff"?"Nm":"mrad";
  let lg=`<b>${unit}</b>`;
  if(view==="track")lg+=`<i style="background:${css("--act")}"></i>actual<i style="background:${css("--cmd")}"></i>commanded`;
  else lg+=`<i style="background:${css("--act")}"></i>${esc(runA)}`;
  if(runB)lg+=`<i style="background:${css("--b2")}"></i>${esc(runB)} (dashed)`;
  lg+=`<span class="hint">scroll = zoom · drag = pan · double-click = reset · click a title to enlarge</span>`;
  $("legend").innerHTML=lg;
  const grid=$("grid"); grid.innerHTML="";
  panelReg.length=0;
  grid.classList.toggle("one",view==="dcmd");
  joints().forEach(j=>{
    const p=document.createElement("div"); p.className="panel";
    const ttl=document.createElement("div"); ttl.className="ttl"; ttl.textContent=short(j);
    ttl.title="enlarge"; ttl.onclick=()=>openModal(j);
    p.appendChild(ttl);
    const cv=document.createElement("canvas"); p.appendChild(cv); grid.appendChild(p);
    attachZoom(cv);
    panelReg.push({cv,joint:j,big:false});
    requestAnimationFrame(()=>drawPanel(cv,j,false));
  });
  if(modalJoint!=null){panelReg.push({cv:$("mcanvas"),joint:modalJoint,big:true});
    requestAnimationFrame(()=>drawPanel($("mcanvas"),modalJoint,true))}
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
      const ov=e.in_overlap==null?"":(e.in_overlap?" · in RTC overlap":" · outside overlap");
      gh+=`<div class="note"><a href="#" data-t="${e.t}" class="jl">${short(n)} close @ ${e.t}s</a> · step ${e.hi} · rise ${dash(e.rise_ms)}ms · ${ok}${ov}</div>`;
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
  fh+=row("RTC applied (fraction of chunks)",sc.rtc_applied_frac);
  fh+=row("cmd step within / at splice (mrad)",sm.step_within_p50!=null?`${sm.step_within_p50} / ${dash(sm.step_splice_p50)}`:null);
  fh+=row("splice ratio",sm.splice_ratio!=null?`×${sm.splice_ratio}${sm.splice_ratio>=V_SPLICE?" ⚠":""}${runs[runA].meta.stalled_run?" (spans a stall — compare with blocking runs only)":""}`:null);
  fh+=row("splice p95 / max (mrad)",sm.splice_p95!=null?`${sm.splice_p95} / ${sm.splice_max} (chunk ${sm.splice_max_seq})`:null,sm.splice_max_seq);
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
  const ks=[...new Set([...pa.k,...(pb?pb.k:[])])].sort((a,b)=>a-b);
  if(!ks.length){g.fillText("no profile",padL,H/2);return}
  let ymax=1;
  [pa,pb].forEach(p=>{if(p)p.err.concat(p.step).forEach(v=>{if(v!=null&&v>ymax)ymax=v})});
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
  g.fillStyle=css("--muted");
  g.fillText(String(Math.round(ymax)),2,padT+8);g.fillText("0",padL-10,padT+ih);
  g.fillText("horizon_idx "+kmin,padL,H-5);g.fillText(String(kmax),W-padR-18,H-5);
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
}

// ------------------------------------------------------------------ matrix
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
}
window.addEventListener("resize",()=>render());
render();
</script>
"""
