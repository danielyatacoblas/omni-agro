'use strict';
const $ = (id) => document.getElementById(id);
const api = (p, o) => fetch(p, o).then(r => r.json());

/* ── Iconos (SVG inline, estilo Lucide, sin CDN) ───────────────────────── */
const ICONS = {
  scan:'<path d="M3 7V5a2 2 0 0 1 2-2h2"/><path d="M17 3h2a2 2 0 0 1 2 2v2"/><path d="M21 17v2a2 2 0 0 1-2 2h-2"/><path d="M7 21H5a2 2 0 0 1-2-2v-2"/><path d="M7 12h10"/>',
  cpu:'<rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/><path d="M15 2v2M15 20v2M2 15h2M2 9h2M20 15h2M20 9h2M9 2v2M9 20v2"/>',
  clock:'<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',
  film:'<rect width="18" height="18" x="3" y="3" rx="2"/><path d="M7 3v18M3 7.5h4M3 12h18M3 16.5h4M17 3v18M17 7.5h4M17 16.5h4"/>',
  play:'<polygon points="6 3 20 12 6 21 6 3"/>',
  stop:'<rect width="14" height="14" x="5" y="5" rx="2"/>',
  undo:'<path d="M9 14 4 9l5-5"/><path d="M4 9h10.5a5.5 5.5 0 0 1 0 11H11"/>',
  trash:'<path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><path d="M10 11v6M14 11v6"/>',
  route:'<circle cx="6" cy="19" r="3"/><path d="M9 19h8.5a3.5 3.5 0 0 0 0-7h-11a3.5 3.5 0 0 1 0-7H15"/><circle cx="18" cy="5" r="3"/>',
  layers:'<path d="M12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.91a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.83Z"/><path d="m22 12.5-9.17 4.16a2 2 0 0 1-1.66 0L2 12.5"/><path d="m22 17.5-9.17 4.16a2 2 0 0 1-1.66 0L2 17.5"/>',
  download:'<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" x2="12" y1="15" y2="3"/>',
  alert:'<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4M12 17h.01"/>',
  activity:'<path d="M22 12h-4l-3 9L9 3l-3 9H2"/>',
  eye:'<path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/>',
  sprout:'<path d="M7 20h10"/><path d="M10 20c5.5-2.5.8-6.4 3-10"/><path d="M9.5 9.4c1.1.8 1.8 2.2 2.3 3.7-2 .4-3.5.4-4.8-.3-1.2-.6-2.3-1.9-3-4.2 2.8-.5 4.4 0 5.5.8z"/><path d="M14.1 6a7 7 0 0 0-1.1 4c1.9-.1 3.3-.6 4.3-1.4 1-1 1.6-2.3 1.7-4.6-3.7.3-4.9 1.9-4.9 2z"/>',
  bug:'<path d="m8 2 1.88 1.88"/><path d="M14.12 3.88 16 2"/><path d="M9 7.13v-1a3.003 3.003 0 1 1 6 0v1"/><path d="M12 20c-3.3 0-6-2.7-6-6v-3a4 4 0 0 1 4-4h4a4 4 0 0 1 4 4v3c0 3.3-2.7 6-6 6"/><path d="M12 20v-9"/><path d="M6.53 9C4.6 8.8 3 7.1 3 5"/><path d="M6 13H2"/><path d="M3 21c0-2.1 1.7-3.9 3.8-4"/><path d="M20.97 5c0 2.1-1.6 3.8-3.5 4"/><path d="M22 13h-4"/><path d="M17.2 17c2.1.1 3.8 1.9 3.8 4"/>',
  grid:'<rect width="18" height="18" x="3" y="3" rx="2"/><path d="M3 9h18M3 15h18M9 3v18M15 3v18"/>',
  sliders:'<line x1="4" x2="4" y1="21" y2="14"/><line x1="4" x2="4" y1="10" y2="3"/><line x1="12" x2="12" y1="21" y2="12"/><line x1="12" x2="12" y1="8" y2="3"/><line x1="20" x2="20" y1="21" y2="16"/><line x1="20" x2="20" y1="12" y2="3"/><line x1="1" x2="7" y1="14" y2="14"/><line x1="9" x2="15" y1="8" y2="8"/><line x1="17" x2="23" y1="16" y2="16"/>',
  'mouse-pointer':'<path d="M12.586 12.586 19 19"/><path d="M3.688 3.037a.497.497 0 0 0-.651.651l6.5 15.999a.501.501 0 0 0 .947-.062l1.569-6.083a2 2 0 0 1 1.448-1.479l6.124-1.579a.5.5 0 0 0 .063-.947z"/>',
  timer:'<line x1="10" x2="14" y1="2" y2="2"/><line x1="12" x2="12" y1="14" y2="9"/><circle cx="12" cy="14" r="8"/>',
  x:'<path d="M18 6 6 18M6 6l12 12"/>',
};
function svg(n){ return `<svg viewBox="0 0 24 24">${ICONS[n]||''}</svg>`; }
function hydrateIcons(root){ (root||document).querySelectorAll('i[data-ico]').forEach(el=>{ if(!el.firstChild) el.innerHTML=svg(el.dataset.ico); }); }

const PALETTE = ['#6FA80C','#2D6CDF','#129A6B','#E19100','#7C5CE0','#E5484D','#0EA5A5'];
const SEV = { critical:'#E5484D', warning:'#E19100', info:'#2D6CDF', ok:'#129A6B' };
const MODCOL = { Despoblamiento:'#E19100', Malezas:'#E5484D', Conteo:'#6FA80C' };

/* Config por caso de uso — todos comparten el detector agro; cambia el modo
   de clases: conteo/despoblamiento tratan todo como planta, malezas usa crop/weed. */
const UC = {
  conteo:         { classMode:'cultivo', title:'Conteo de plantas' },
  malezas:        { classMode:'modelo',  title:'Presión de maleza' },
  despoblamiento: { classMode:'cultivo', title:'Despoblamiento (huecos)' },
};

const st = { usecase:'conteo', video:null, tool:null, zones:[], draft:[], streaming:false, statusTimer:null };

/* ── init ──────────────────────────────────────────────────────────────── */
(async function init(){
  hydrateIcons();
  const d = await api('/api/videos');
  $('devicePill').textContent = d.device;
  const sel = $('videoSelect');
  sel.innerHTML = d.videos.length
    ? d.videos.map(v=>`<option>${v}</option>`).join('')
    : '<option value="">(coloca .mp4 en videos/)</option>';
  const ds=$('detectorSelect');
  ds.innerHTML=(d.detectors||[]).map(x=>`<option value="${x.kind}">${x.label}</option>`).join('');
  ds.value=d.default_detector||'agro';
  $('confRange').value = d.default_conf ?? 0.05;
  $('confVal').textContent = (+$('confRange').value).toFixed(2);
  tickClock(); setInterval(tickClock, 1000);
  applyUsecase();
  if (d.videos.length){ sel.value=d.videos[0]; await loadVideo(d.videos[0]); }
})();
function tickClock(){ $('clock').textContent = new Date().toLocaleTimeString('es-PE',{hour:'2-digit',minute:'2-digit',second:'2-digit'}); }
$('confRange').addEventListener('input', e=>{ $('confVal').textContent=(+e.target.value).toFixed(2); });

/* ── caso de uso ───────────────────────────────────────────────────────── */
document.querySelectorAll('.uc').forEach(b=>b.onclick=()=>{
  if(st.streaming){ toast('Detén el proceso para cambiar de módulo'); return; }
  document.querySelectorAll('.uc').forEach(x=>x.classList.remove('active'));
  b.classList.add('active');
  st.usecase=b.dataset.uc; st.tool=null; st.draft=[];
  applyUsecase();
});
function applyUsecase(){
  const u=UC[st.usecase];
  $('ucTitle').textContent=u.title;
  $('drawBtn').dataset.active='0';
  document.querySelectorAll('.mod-panel').forEach(p=>p.style.display=(p.dataset.mod===st.usecase)?'block':'none');
  renderChips(); redraw(); updateSteps();
}

/* ── carga de video ────────────────────────────────────────────────────── */
async function loadVideo(name){
  st.video=name; st.streaming=false; stopStream();
  $('placeholder').style.display='none';
  const img=$('frameImg'); img.style.display='block';
  img.onload=()=>{ sizeEditor(); redraw(); };
  img.src=`/api/video/${encodeURIComponent(name)}/frame?t=${Date.now()}`;
  const cfg=await api(`/api/video/${encodeURIComponent(name)}/zones`);
  st.zones=(cfg.zones||[]).map((z,i)=>({...z,color:z.color||PALETTE[i%PALETTE.length]}));
  st.draft=[]; renderChips(); redraw(); updateSteps();
}
$('videoSelect').addEventListener('change', e=>{ if(e.target.value) loadVideo(e.target.value); });

/* ── geometría editor ──────────────────────────────────────────────────── */
function imgRect(){
  const img=$('frameImg'), vp=$('viewport');
  const cw=vp.clientWidth, ch=vp.clientHeight;
  const nw=img.naturalWidth||cw, nh=img.naturalHeight||ch;
  const s=Math.min(cw/nw, ch/nh), w=nw*s, h=nh*s;
  return { x:(cw-w)/2, y:(ch-h)/2, w, h };
}
function sizeEditor(){ const vp=$('viewport'), cv=$('editor'); cv.width=vp.clientWidth; cv.height=vp.clientHeight; }
window.addEventListener('resize', ()=>{ sizeEditor(); redraw(); });
function toNorm(cx,cy){ const r=imgRect(); return [(cx-r.x)/r.w,(cy-r.y)/r.h]; }
function toPx(nx,ny){ const r=imgRect(); return [r.x+nx*r.w, r.y+ny*r.h]; }

/* ── herramienta de dibujo (ROI polígono) ──────────────────────────────── */
$('drawBtn').onclick=()=>toggleTool();
function toggleTool(){
  st.tool=(st.tool==='roi')?null:'roi'; st.draft=[];
  $('drawBtn').dataset.active=st.tool?'1':'0';
  const h=$('hint');
  if(st.tool){ h.style.display='block'; h.textContent='Clic para marcar puntos del lote · doble clic para cerrar'; }
  else h.style.display='none';
  redraw();
}
$('editor').addEventListener('click', e=>{
  if(!st.tool||st.streaming) return;
  const r=$('editor').getBoundingClientRect();
  const [nx,ny]=toNorm(e.clientX-r.left, e.clientY-r.top);
  if(nx<0||nx>1||ny<0||ny>1) return;
  st.draft.push([nx,ny]);
  redraw();
});
$('editor').addEventListener('dblclick', e=>{
  if(!st.tool||st.streaming) return;
  if(st.draft.length<3){ toast('Marca al menos 3 puntos'); return; }
  const name=prompt('Nombre del lote (ej. "Lote A"):');
  if(!name) return;
  const color=PALETTE[st.zones.length%PALETTE.length];
  st.zones.push({ id:'r'+(st.zones.length+1)+'_'+Date.now().toString(36), name, type:'roi', color, points:st.draft.slice() });
  st.draft=[]; toggleTool(); afterEdit();
});
$('undoBtn').onclick=()=>{
  if(st.draft.length){ st.draft.pop(); redraw(); return; }
  if(st.zones.length){ st.zones.pop(); }
  afterEdit();
};
$('clearBtn').onclick=()=>{ st.zones=[]; st.draft=[]; afterEdit(); };
function afterEdit(){ renderChips(); redraw(); updateSteps(); }

/* ── dibujo overlay ────────────────────────────────────────────────────── */
function redraw(){
  const cv=$('editor'); if(!cv.width) sizeEditor();
  const ctx=cv.getContext('2d'); ctx.clearRect(0,0,cv.width,cv.height);
  if(st.streaming) return;
  st.zones.forEach(z=>drawPoly(ctx,z.points,z.color,z.name));
  if(st.draft.length) drawPoly(ctx,st.draft,'#F26A21','',true);
}
function drawPoly(ctx,pts,color,label,dashed){
  if(!pts.length) return; ctx.save();
  ctx.beginPath(); pts.forEach((p,i)=>{ const [x,y]=toPx(...p); i?ctx.lineTo(x,y):ctx.moveTo(x,y); });
  if(!dashed) ctx.closePath();
  ctx.fillStyle=hexA(color,.16); ctx.fill();
  ctx.lineWidth=2.5; ctx.strokeStyle=color; if(dashed)ctx.setLineDash([7,5]); ctx.stroke();
  pts.forEach(p=>{ const [x,y]=toPx(...p); dot(ctx,x,y,color); });
  if(label){ const [x,y]=toPx(...pts[0]); ctx.setLineDash([]); ctx.fillStyle=color; ctx.font='700 13px Inter,sans-serif'; ctx.fillText(label,x+5,y-7); }
  ctx.restore();
}
function dot(ctx,x,y,c){ ctx.beginPath(); ctx.arc(x,y,4.5,0,7); ctx.fillStyle=c; ctx.fill(); ctx.lineWidth=2; ctx.strokeStyle='#fff'; ctx.stroke(); }
function hexA(h,a){ h=h.replace('#',''); return `rgba(${parseInt(h.slice(0,2),16)},${parseInt(h.slice(2,4),16)},${parseInt(h.slice(4,6),16)},${a})`; }

function renderChips(){
  const wrap=$('zoneChips'); let html='';
  st.zones.forEach((z,idx)=>{ html+=chip(z.name,z.color,'layers',idx); });
  wrap.innerHTML=html; hydrateIcons(wrap);
  $('noZones').style.display=html?'none':'inline';
  wrap.querySelectorAll('.x').forEach(el=>el.onclick=()=>{ st.zones.splice(+el.dataset.idx,1); afterEdit(); });
}
function chip(text,color,icon,idx){
  return `<span class="chip" style="background:${hexA(color,.1)};color:${color};border-color:${hexA(color,.35)}"><i data-ico="${icon}"></i>${text}<span class="x" data-idx="${idx}"><i data-ico="x"></i></span></span>`;
}

/* ── pasos ─────────────────────────────────────────────────────────────── */
function updateSteps(){
  const hasVideo=!!st.video;
  setStep(1, hasVideo?'done':'active');
  setStep(2, !hasVideo?'':(st.zones.length?'done':'active'));
  setStep(3, st.streaming?'active':(hasVideo?'active':''));
}
function setStep(n,state){ const el=document.querySelector(`.step[data-step="${n}"]`); el.className='step'+(state?' '+state:''); }

/* ── start / stop ──────────────────────────────────────────────────────── */
$('startBtn').onclick=start; $('stopBtn').onclick=stop;
async function start(){
  if(!st.video){ toast('Elige un video'); return; }
  await saveZones();
  const r=await api('/api/start',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({video:st.video, conf:+$('confRange').value,
                         detector:$('detectorSelect').value,
                         class_mode:UC[st.usecase].classMode,
                         show_grid: st.usecase!=='malezas'})});
  if(r.error){ toast(r.error); return; }
  st.streaming=true; redraw();
  $('frameImg').style.display='none';
  const s=$('stream'); s.style.display='block'; s.src='/stream?t='+Date.now();
  $('startBtn').disabled=true; $('stopBtn').disabled=false;
  $('liveDot').className='dot on'; $('liveTxt').textContent='Procesando';
  $('vpBadgeTxt').textContent='Análisis en vivo';
  $('procTxt').textContent='Cargando modelo…';
  $('procOverlay').style.display='flex';
  updateSteps();
  if(st.statusTimer) clearInterval(st.statusTimer);
  st.statusTimer=setInterval(poll,500);
}
async function stop(){ await fetch('/api/stop',{method:'POST'}); finishUI(); }
function stopStream(){ const s=$('stream'); s.style.display='none'; s.src=''; }
function finishUI(){
  st.streaming=false;
  $('procOverlay').style.display='none';
  $('startBtn').disabled=false; $('stopBtn').disabled=true;
  $('liveDot').className='dot'; $('liveTxt').textContent='Listo';
  $('vpBadgeTxt').textContent='Resultado';
  if(st.statusTimer){ clearInterval(st.statusTimer); st.statusTimer=null; }
  if(st.video) $('videoSelect').value=st.video;
  updateSteps();
}
function saveZones(){ return fetch(`/api/video/${encodeURIComponent(st.video)}/zones`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({zones:st.zones})}); }

/* ── poll / render ─────────────────────────────────────────────────────── */
async function poll(){
  const s=await api('/api/status');
  if(st.streaming){
    if(s.has_frame){ $('procOverlay').style.display='none'; }
    else { $('procOverlay').style.display='flex'; $('procTxt').textContent=s.model_ready?'Procesando…':'Cargando modelo…'; }
  }
  $('progressBar').style.width=(100*(s.progress||0))+'%';
  $('kPlants').textContent=s.plantas_unicas??0;
  $('kFrame').textContent=s.plantas_frame??0;
  $('kWeeds').textContent=s.malezas_unicas??0;
  $('kGap').textContent=(s.gap_pct??0)+'%';
  $('ioAvg').textContent=s.plantas_frame_avg??0;
  $('ioPeak').textContent=s.peak_frame??0;
  $('ioUnique').textContent=s.plantas_unicas??0;
  // malezas
  const wp=s.weed_pressure??0;
  const wcol=wp>=25?'#E5484D':wp>=12?'#E19100':'#129A6B';
  $('weedPct').textContent=wp+'%'; $('weedPct').style.color=wcol;
  $('weedBar').style.width=Math.min(100,wp)+'%'; $('weedBar').style.background=wcol;
  $('weedDot').style.background=wcol;
  $('wUnique').textContent=s.malezas_unicas??0;
  $('wFrame').textContent=s.malezas_frame??0;
  // despoblamiento
  const gp=s.gap_pct??0;
  const gcol=gp>=15?'#E5484D':gp>=8?'#E19100':'#129A6B';
  $('gapPct').textContent=gp+'%'; $('gapPct').style.color=gcol;
  $('gapBar').style.width=Math.min(100,gp)+'%'; $('gapBar').style.background=gcol;
  $('gapDot').style.background=gcol;
  $('gapCells').textContent=s.gap_cells??0;
  $('rowCells').textContent=s.row_cells??0;
  $('liveTxt').textContent=`${s.video_time||''} / ${s.duration||''}`;
  if(s.timeline) drawFlow(s.timeline);
  renderTracks(s.active_tracks||[], s.active_count||0);
  renderAlerts(s.alerts||[]);
  if(s.finished){ finishUI(); toast('Procesamiento terminado · CSV listo'); }
}
function renderTracks(list,count){
  $('activeCount').textContent=count;
  const el=$('activePeople');
  if(!list.length){ el.innerHTML='<div class="ps-empty">Sin detecciones en cuadro todavía.</div>'; return; }
  el.innerHTML=list.map(p=>{ const c=p.tipo==='maleza'?'#E5484D':PALETTE[p.id%PALETTE.length];
    const badge = p.tipo==='maleza' ? '<span class="pbadge weed">maleza</span>' : '<span class="pbadge plant">planta</span>';
    return `<div class="person" style="border-left-color:${c}"><div class="pid"><i data-ico="sprout" style="color:${c}"></i>ID ${p.id}${badge}</div><div class="prow"><i data-ico="timer"></i>${p.seen} en cuadro</div></div>`; }).join('');
  hydrateIcons(el);
}
function renderAlerts(al){
  $('alertCount').textContent=al.length;
  $('noAlerts').style.display=al.length?'none':'block';
  $('alertRows').innerHTML=[...al].reverse().map(a=>`<tr><td style="font-variant-numeric:tabular-nums">${a.video_time}</td><td><span class="mtag" style="background:${hexA(MODCOL[a.modulo]||'#2D6CDF',.1)};color:${MODCOL[a.modulo]||'#2D6CDF'}">${a.modulo}</span></td><td><span class="sev"><span class="d" style="background:${SEV[a.severity]||'#2D6CDF'}"></span>${a.tipo}</span></td><td class="hide-sm">${a.detalle}</td></tr>`).join('');
}

/* ── flow chart: plantas/frame, malezas/frame y gap% ───────────────────── */
function drawFlow(tl){
  const cv=$('flowChart'); const dpr=window.devicePixelRatio||1;
  const w=cv.clientWidth, h=cv.clientHeight; cv.width=w*dpr; cv.height=h*dpr;
  const ctx=cv.getContext('2d'); ctx.setTransform(dpr,0,0,dpr,0,0); ctx.clearRect(0,0,w,h);
  if(!tl.length) return;
  const pad={l:28,r:10,t:12,b:20}, gw=w-pad.l-pad.r, gh=h-pad.t-pad.b;
  const maxT=Math.max(1,tl[tl.length-1].t);
  const maxV=Math.max(...tl.map(p=>Math.max(p.plantas,p.malezas)),1);
  const X=t=>pad.l+(t/maxT)*gw, Y=v=>pad.t+gh-(v/maxV)*gh;
  const Yg=v=>pad.t+gh-(Math.min(100,v)/100)*gh;   // gap% en escala 0..100
  ctx.strokeStyle='#EEF1F5'; ctx.fillStyle='#8791A3'; ctx.font='10px Inter'; ctx.lineWidth=1;
  for(let i=0;i<=4;i++){ const v=maxV*i/4, y=Y(v); ctx.beginPath(); ctx.moveTo(pad.l,y); ctx.lineTo(w-pad.r,y); ctx.stroke(); ctx.fillText(Math.round(v),5,y+3); }
  // área de plantas
  ctx.beginPath(); ctx.moveTo(X(tl[0].t),Y(0)); tl.forEach(p=>ctx.lineTo(X(p.t),Y(p.plantas))); ctx.lineTo(X(tl[tl.length-1].t),Y(0)); ctx.closePath();
  const g=ctx.createLinearGradient(0,pad.t,0,pad.t+gh); g.addColorStop(0,'rgba(111,168,12,.22)'); g.addColorStop(1,'rgba(111,168,12,.02)'); ctx.fillStyle=g; ctx.fill();
  line(ctx,tl,X,Y,p=>p.plantas,'#6FA80C',2.2);
  line(ctx,tl,X,Y,p=>p.malezas,'#E5484D',1.6);
  // gap% (línea punteada ámbar, escala 0-100)
  ctx.setLineDash([4,3]);
  line(ctx,tl,X,Yg,p=>p.gap,'#E19100',1.6);
  ctx.setLineDash([]);
}
function line(ctx,tl,X,Y,f,color,lw){ ctx.beginPath(); tl.forEach((p,i)=>{const x=X(p.t),y=Y(f(p)); i?ctx.lineTo(x,y):ctx.moveTo(x,y);}); ctx.strokeStyle=color; ctx.lineWidth=lw; ctx.stroke(); }

/* ── export / toast ────────────────────────────────────────────────────── */
$('exportBtn').onclick=()=>{ window.location='/api/export?t='+Date.now(); };
let toastT=null;
function toast(msg){ const el=$('toast'); el.textContent=msg; el.classList.add('show'); clearTimeout(toastT); toastT=setTimeout(()=>el.classList.remove('show'),2600); }
