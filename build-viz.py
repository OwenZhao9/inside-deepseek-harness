#!/usr/bin/env python3
"""Build the research visualization page from viz-data.json."""
import json, pathlib

HERE = pathlib.Path(__file__).parent
data = json.loads((HERE / 'viz-data.json').read_text(encoding='utf-8'))

TOTALS = {
    'subs': len(data['subs']),
    'me': sum(len(s['me']) for s in data['subs']),
    'ci': sum(len(s['ci']) for s in data['subs']),
    'tp': sum(len(s['tp']) for s in data['subs']),
    'uv': sum(len(s['uv']) for s in data['subs']),
    'bad': len(data['bad']),
    'kf': sum(len(s['kf']) for s in data['subs']),
}

HTML = r'''<title>DeepSeek Harness 源码勘探报告</title>
<style>
:root{
  --ground:#F4F7F7; --surface:#FFFFFF; --surface-2:#E8EFEF; --sunk:#DCE6E6;
  --ink:#0C1A1E; --body:#22383D; --muted:#5D6E73; --faint:#8A9A9E;
  --line:#CFDCDC; --line-soft:#E2EAEA;
  --accent:#0C7F80; --accent-ink:#065E5F; --accent-soft:#DAEFEF;
  --warn:#A8462F; --warn-soft:#F8E7E2; --warn-line:#E6C4BA;
  --shadow:0 1px 2px rgba(12,26,30,.05), 0 8px 24px -12px rgba(12,26,30,.14);
}
@media (prefers-color-scheme: dark){
  :root{
    --ground:#080F12; --surface:#0E1A1E; --surface-2:#152428; --sunk:#0A1417;
    --ink:#EAF4F4; --body:#C2D6D7; --muted:#87A0A2; --faint:#5F7679;
    --line:#22373B; --line-soft:#182A2E;
    --accent:#3FD3C6; --accent-ink:#7EE8DE; --accent-soft:#10312F;
    --warn:#E08268; --warn-soft:#2A1712; --warn-line:#4A2519;
    --shadow:0 1px 2px rgba(0,0,0,.4), 0 10px 30px -14px rgba(0,0,0,.7);
  }
}
:root[data-theme="light"]{
  --ground:#F4F7F7; --surface:#FFFFFF; --surface-2:#E8EFEF; --sunk:#DCE6E6;
  --ink:#0C1A1E; --body:#22383D; --muted:#5D6E73; --faint:#8A9A9E;
  --line:#CFDCDC; --line-soft:#E2EAEA;
  --accent:#0C7F80; --accent-ink:#065E5F; --accent-soft:#DAEFEF;
  --warn:#A8462F; --warn-soft:#F8E7E2; --warn-line:#E6C4BA;
  --shadow:0 1px 2px rgba(12,26,30,.05), 0 8px 24px -12px rgba(12,26,30,.14);
}
:root[data-theme="dark"]{
  --ground:#080F12; --surface:#0E1A1E; --surface-2:#152428; --sunk:#0A1417;
  --ink:#EAF4F4; --body:#C2D6D7; --muted:#87A0A2; --faint:#5F7679;
  --line:#22373B; --line-soft:#182A2E;
  --accent:#3FD3C6; --accent-ink:#7EE8DE; --accent-soft:#10312F;
  --warn:#E08268; --warn-soft:#2A1712; --warn-line:#4A2519;
  --shadow:0 1px 2px rgba(0,0,0,.4), 0 10px 30px -14px rgba(0,0,0,.7);
}

*{box-sizing:border-box}
body{
  margin:0; background:var(--ground); color:var(--body);
  font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Hiragino Sans GB","Microsoft YaHei","Noto Sans CJK SC",sans-serif;
  font-size:15px; line-height:1.72; -webkit-font-smoothing:antialiased;
}
.mono{font-family:ui-monospace,"SF Mono",SFMono-Regular,Menlo,Consolas,"Liberation Mono",monospace}

/* ---------- masthead ---------- */
.mast{border-bottom:1px solid var(--line); background:var(--surface)}
.mast-in{max-width:1400px; margin:0 auto; padding:26px 24px 0; display:flex; flex-direction:column; gap:18px}
.eyebrow{
  font-family:ui-monospace,"SF Mono",Menlo,monospace; font-size:11px; letter-spacing:.16em;
  text-transform:uppercase; color:var(--accent); display:flex; align-items:center; gap:10px; flex-wrap:wrap;
}
.eyebrow::before{content:""; width:22px; height:1px; background:var(--accent); flex:none}
h1{
  margin:0; font-size:clamp(25px,3.4vw,38px); line-height:1.18; color:var(--ink);
  font-weight:700; letter-spacing:-.015em; text-wrap:balance;
}
.dek{margin:0; max-width:66ch; color:var(--muted); font-size:14.5px}
.dek b{color:var(--body); font-weight:600}

/* ---------- stat strip ---------- */
.stats{display:flex; flex-wrap:wrap; gap:0; border-top:1px solid var(--line-soft); margin-top:4px}
.stat{padding:14px 26px 16px 0; margin-right:26px; border-right:1px solid var(--line-soft)}
.stat:last-child{border-right:0}
.stat .v{
  font-family:ui-monospace,"SF Mono",Menlo,monospace; font-size:24px; font-weight:600;
  color:var(--ink); font-variant-numeric:tabular-nums; line-height:1.1; display:block;
}
.stat.is-warn .v{color:var(--warn)}
.stat .k{font-size:11.5px; color:var(--faint); letter-spacing:.06em; margin-top:3px; display:block}

.provenance{
  border-top:1px solid var(--line-soft); padding:11px 0 13px; font-size:11.5px; color:var(--faint);
  font-family:ui-monospace,"SF Mono",Menlo,monospace; display:flex; gap:8px 20px; flex-wrap:wrap;
}
.provenance span{white-space:nowrap}

/* ---------- shell ---------- */
.shell{max-width:1400px; margin:0 auto; padding:24px; display:grid; grid-template-columns:262px minmax(0,1fr); gap:32px; align-items:start}
@media (max-width:940px){ .shell{grid-template-columns:1fr; gap:18px; padding:16px} }

/* ---------- rail ---------- */
.rail{position:sticky; top:16px; display:flex; flex-direction:column; gap:3px}
@media (max-width:940px){
  .rail{position:static; flex-direction:row; overflow-x:auto; gap:8px; padding-bottom:6px; scrollbar-width:thin}
  .rail-h{display:none}
}
.rail-h{
  font-family:ui-monospace,"SF Mono",Menlo,monospace; font-size:10.5px; letter-spacing:.15em;
  text-transform:uppercase; color:var(--faint); padding:0 10px 8px;
}
.nav{
  display:flex; align-items:baseline; gap:9px; width:100%; text-align:left; cursor:pointer;
  background:transparent; border:0; border-radius:7px; padding:9px 11px; color:var(--muted);
  font:inherit; font-size:13.5px; line-height:1.35; transition:background .12s, color .12s;
}
.nav:hover{background:var(--surface-2); color:var(--body)}
.nav[aria-current="true"]{background:var(--accent-soft); color:var(--accent-ink); font-weight:600}
.nav .idx{
  font-family:ui-monospace,"SF Mono",Menlo,monospace; font-size:10.5px; color:var(--faint);
  font-variant-numeric:tabular-nums; flex:none; width:15px;
}
.nav[aria-current="true"] .idx{color:var(--accent)}
.nav .lbl{flex:1; min-width:0}
.nav .ct{
  font-family:ui-monospace,"SF Mono",Menlo,monospace; font-size:11px; color:var(--faint);
  font-variant-numeric:tabular-nums; flex:none;
}
.nav.warn[aria-current="true"]{background:var(--warn-soft); color:var(--warn)}
.nav.warn[aria-current="true"] .idx,.nav.warn[aria-current="true"] .ct{color:var(--warn)}
.rail-sep{height:1px; background:var(--line-soft); margin:9px 10px}
@media (max-width:940px){ .rail-sep{width:1px; height:auto; margin:4px 2px} .nav{white-space:nowrap; width:auto} }

/* ---------- controls ---------- */
.controls{display:flex; gap:10px; align-items:center; flex-wrap:wrap; margin-bottom:18px}
.search{
  flex:1; min-width:200px; background:var(--surface); border:1px solid var(--line); border-radius:8px;
  padding:9px 13px; color:var(--ink); font:inherit; font-size:14px;
}
.search::placeholder{color:var(--faint)}
.search:focus{outline:2px solid var(--accent); outline-offset:1px; border-color:transparent}
.chips{display:flex; gap:6px; flex-wrap:wrap}
.chip{
  cursor:pointer; background:var(--surface); border:1px solid var(--line); border-radius:99px;
  padding:6px 13px; color:var(--muted); font:inherit; font-size:12.5px; transition:all .12s;
  display:inline-flex; align-items:center; gap:6px;
}
.chip:hover{border-color:var(--accent); color:var(--body)}
.chip[aria-pressed="true"]{background:var(--accent); border-color:var(--accent); color:var(--ground); font-weight:600}
.chip .n{font-family:ui-monospace,Menlo,monospace; font-size:11px; opacity:.72; font-variant-numeric:tabular-nums}
.chip:focus-visible,.nav:focus-visible{outline:2px solid var(--accent); outline-offset:2px}

/* ---------- section head ---------- */
.sec-head{margin:0 0 18px; padding-bottom:14px; border-bottom:2px solid var(--ink)}
.sec-head h2{margin:0 0 8px; font-size:21px; color:var(--ink); font-weight:700; letter-spacing:-.01em; text-wrap:balance}
.sec-head .one{margin:0; color:var(--muted); font-size:14px; max-width:74ch}

.grp{margin:0 0 14px; display:flex; align-items:center; gap:10px}
.grp .t{
  font-family:ui-monospace,"SF Mono",Menlo,monospace; font-size:11px; letter-spacing:.14em;
  text-transform:uppercase; color:var(--accent); white-space:nowrap;
}
.grp .r{flex:1; height:1px; background:var(--line-soft)}
.grp .n{font-family:ui-monospace,Menlo,monospace; font-size:11px; color:var(--faint); font-variant-numeric:tabular-nums}
.grp.warn .t{color:var(--warn)}

/* ---------- cards ---------- */
.cards{display:flex; flex-direction:column; gap:9px; margin-bottom:34px}
.card{
  background:var(--surface); border:1px solid var(--line-soft); border-radius:9px;
  padding:15px 17px; box-shadow:var(--shadow);
}
.card h3{margin:0 0 7px; font-size:15px; color:var(--ink); font-weight:650; line-height:1.45; text-wrap:balance}
.card p{margin:0; font-size:13.8px; color:var(--body)}
.card p + p{margin-top:8px}
.ev{
  display:inline-block; margin-top:10px; font-family:ui-monospace,"SF Mono",Menlo,monospace;
  font-size:11.5px; color:var(--accent-ink); background:var(--accent-soft);
  padding:3px 9px; border-radius:5px; word-break:break-all; line-height:1.6;
}
.card.bare{padding:12px 16px; display:flex; gap:11px; align-items:flex-start}
.card.bare .bullet{
  font-family:ui-monospace,Menlo,monospace; font-size:11px; color:var(--faint);
  font-variant-numeric:tabular-nums; flex:none; padding-top:2px; min-width:20px;
}
.card.bare .txt{font-size:13.8px; color:var(--body); flex:1; min-width:0}

/* teaching levels: one hue, three values */
.lv{
  font-family:ui-monospace,Menlo,monospace; font-size:10.5px; letter-spacing:.08em; padding:2px 8px;
  border-radius:4px; flex:none; border:1px solid transparent;
}
.lv-1{background:var(--accent-soft); color:var(--accent-ink)}
.lv-2{background:transparent; color:var(--accent); border-color:var(--accent)}
.lv-3{background:var(--accent); color:var(--ground); font-weight:600}
.card.tp{display:flex; gap:12px; align-items:flex-start}
.card.tp .bd{flex:1; min-width:0}

/* rejected */
.card.bad{border-color:var(--warn-line); background:var(--warn-soft)}
.card.bad .claim{font-size:13.8px; color:var(--ink); font-weight:600; margin:0 0 9px; line-height:1.5}
.card.bad .row{display:flex; gap:9px; margin-top:9px; align-items:flex-start}
.card.bad .tag{
  font-family:ui-monospace,Menlo,monospace; font-size:10.5px; color:var(--warn); flex:none;
  padding-top:3px; letter-spacing:.06em; min-width:38px;
}
.card.bad .row p{font-size:13.5px; color:var(--body); margin:0}

/* key files */
.kf{display:flex; gap:11px; align-items:flex-start; padding:10px 0; border-bottom:1px solid var(--line-soft)}
.kf:last-child{border-bottom:0}
.kf .p{
  font-family:ui-monospace,"SF Mono",Menlo,monospace; font-size:11.8px; color:var(--accent-ink);
  flex:none; max-width:46%; word-break:break-all; line-height:1.65;
}
.kf .p .ln{color:var(--faint)}
.kf .w{font-size:13.2px; color:var(--muted); flex:1; min-width:0}
@media (max-width:700px){ .kf{flex-direction:column; gap:4px} .kf .p{max-width:100%} }

.empty{padding:52px 20px; text-align:center; color:var(--faint); font-size:14px}
.foot{
  max-width:1400px; margin:0 auto; padding:28px 24px 56px; border-top:1px solid var(--line-soft);
  color:var(--faint); font-size:12px; font-family:ui-monospace,Menlo,monospace; line-height:1.9;
}
@media (prefers-reduced-motion:reduce){ *{transition:none !important; animation:none !important} }
</style>

<header class="mast">
  <div class="mast-in">
    <div class="eyebrow">源码勘探报告 · 12 agent · 双轮验伪</div>
    <h1>DeepSeek Harness 拆解：__ME__ 条机制，__CI__ 条反直觉发现</h1>
    <p class="dek">对 <b>deepseek-ai/deepseek-harness</b>（56.4 万行 TypeScript / 226 个包）的九路并行源码勘探。每条机制都必须给出 <b>文件:行号</b> 证据；两个对抗性 agent 逐条复核后打回 <b>__BAD__</b> 条。下面是全部原始发现。</p>
    <div class="stats">
      <div class="stat"><span class="v">__SUBS__</span><span class="k">子系统</span></div>
      <div class="stat"><span class="v">__ME__</span><span class="k">核心机制</span></div>
      <div class="stat"><span class="v">__CI__</span><span class="k">反直觉发现</span></div>
      <div class="stat"><span class="v">__TP__</span><span class="k">教学点</span></div>
      <div class="stat"><span class="v">__KF__</span><span class="k">关键文件</span></div>
      <div class="stat"><span class="v">__UV__</span><span class="k">存疑未证</span></div>
      <div class="stat is-warn"><span class="v">__BAD__</span><span class="k">验伪打回</span></div>
    </div>
    <div class="provenance">
      <span>基线 v0.1.0-rc.5</span><span>877 次工具调用</span><span>279 万 token</span><span>55 分钟</span><span>0 失败</span>
    </div>
  </div>
</header>

<div class="shell">
  <nav class="rail" id="rail" aria-label="子系统"></nav>
  <main>
    <div class="controls">
      <input class="search" id="q" type="search" placeholder="搜索机制、发现、文件路径…" aria-label="搜索" />
      <div class="chips" id="chips"></div>
    </div>
    <div id="out"></div>
  </main>
</div>

<footer class="foot">
  数据源 RESEARCH-RAW.json · 九路并行深读 → 两轮对抗性验伪 → 打回项已标注<br>
  未验证栏是 agent 自己声明"没能在代码里证实"的推测，未经复核，引用前须自行核对
</footer>

<script>
const DATA = __DATA__;
const TYPES = [
  {k:'me', label:'机制',   get:s=>s.me},
  {k:'ci', label:'反直觉', get:s=>s.ci},
  {k:'tp', label:'教学点', get:s=>s.tp},
  {k:'kf', label:'关键文件',get:s=>s.kf},
  {k:'uv', label:'存疑',   get:s=>s.uv},
];
const LV = {'入门':'lv-1','进阶':'lv-2','硬核':'lv-3'};
const state = {sub:'all', types:new Set(['me','ci','tp','kf','uv']), q:''};

const esc = s => String(s==null?'':s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const hit = (s,q) => !q || String(s).toLowerCase().includes(q);

function itemText(k, it){
  if(k==='me') return it.t+' '+it.e+' '+it.v;
  if(k==='tp') return it.lv+' '+it.t+' '+it.p;
  if(k==='kf') return it.p+' '+it.w;
  return String(it);
}
function subsFor(){ return state.sub==='all' ? DATA.subs : [DATA.subs[state.sub]]; }

function countFor(k){
  const q = state.q;
  return subsFor().reduce((n,s)=> n + TYPES.find(t=>t.k===k).get(s).filter(it=>hit(itemText(k,it),q)).length, 0);
}

function buildRail(){
  const r = document.getElementById('rail');
  let h = '<div class="rail-h">子系统</div>';
  const tot = DATA.subs.reduce((n,s)=>n+s.me.length+s.ci.length+s.tp.length+s.kf.length+s.uv.length,0);
  h += `<button class="nav" data-s="all" aria-current="${state.sub==='all'}"><span class="idx">◆</span><span class="lbl">全部</span><span class="ct">${tot}</span></button>`;
  h += '<div class="rail-sep"></div>';
  DATA.subs.forEach((s,i)=>{
    const n = s.me.length+s.ci.length+s.tp.length+s.kf.length+s.uv.length;
    h += `<button class="nav" data-s="${i}" aria-current="${state.sub===i}"><span class="idx">${String(i+1).padStart(2,'0')}</span><span class="lbl">${esc(s.n)}</span><span class="ct">${n}</span></button>`;
  });
  h += '<div class="rail-sep"></div>';
  h += `<button class="nav warn" data-s="bad" aria-current="${state.sub==='bad'}"><span class="idx">✕</span><span class="lbl">验伪打回</span><span class="ct">${DATA.bad.length}</span></button>`;
  r.innerHTML = h;
  r.querySelectorAll('.nav').forEach(b=>b.onclick=()=>{
    const v=b.dataset.s; state.sub = (v==='all'||v==='bad') ? v : +v;
    buildRail(); buildChips(); render(); window.scrollTo({top:0,behavior:'smooth'});
  });
}

function buildChips(){
  const c = document.getElementById('chips');
  if(state.sub==='bad'){ c.innerHTML=''; return; }
  c.innerHTML = TYPES.map(t=>
    `<button class="chip" data-t="${t.k}" aria-pressed="${state.types.has(t.k)}">${t.label}<span class="n">${countFor(t.k)}</span></button>`
  ).join('');
  c.querySelectorAll('.chip').forEach(b=>b.onclick=()=>{
    const k=b.dataset.t;
    if(state.types.has(k)) state.types.delete(k); else state.types.add(k);
    if(state.types.size===0) TYPES.forEach(t=>state.types.add(t.k));
    buildChips(); render();
  });
}

function cardFor(k, it, i){
  if(k==='me') return `<article class="card"><h3>${esc(it.t)}</h3><p>${esc(it.e)}</p><span class="ev">${esc(it.v)}</span></article>`;
  if(k==='ci') return `<article class="card bare"><span class="bullet">${String(i+1).padStart(2,'0')}</span><div class="txt">${esc(it)}</div></article>`;
  if(k==='uv') return `<article class="card bare"><span class="bullet">?</span><div class="txt">${esc(it)}</div></article>`;
  if(k==='tp') return `<article class="card tp"><span class="lv ${LV[it.lv]||'lv-1'}">${esc(it.lv)}</span><div class="bd"><h3>${esc(it.t)}</h3><p>${esc(it.p)}</p></div></article>`;
  const ln = it.l ? `<span class="ln">:${it.l}</span>` : '';
  return `<div class="kf"><div class="p">${esc(it.p)}${ln}</div><div class="w">${esc(it.w)}</div></div>`;
}

function render(){
  const out = document.getElementById('out'); const q = state.q;

  if(state.sub==='bad'){
    const rows = DATA.bad.filter(b=>hit(b.c+' '+b.p+' '+b.f, q));
    out.innerHTML = `<div class="sec-head"><h2>验伪打回：${DATA.bad.length} 条</h2>
      <p class="one">两个对抗性 agent 逐条复核了 140 项论断。一个打开文件核对路径与行号，一个扮演熟悉 Claude Code / LangGraph 的怀疑者，专挑"把行业标配包装成独有"的说法。以下论断未通过复核，已从书稿大纲中剔除。</p></div>`
      + `<div class="grp warn"><span class="t">被剔除的论断</span><span class="r"></span><span class="n">${rows.length}</span></div>`
      + (rows.length ? `<div class="cards">` + rows.map(b=>
          `<article class="card bad"><p class="claim">${esc(b.c)}</p>
           <div class="row"><span class="tag">问题</span><p>${esc(b.p)}</p></div>
           <div class="row"><span class="tag">订正</span><p>${esc(b.f)}</p></div></article>`).join('') + `</div>`
        : `<div class="empty">没有匹配的条目</div>`);
    return;
  }

  const list = subsFor(); let h = '';
  if(state.sub!=='all'){
    const s = list[0];
    h += `<div class="sec-head"><h2>${esc(s.full)}</h2><p class="one">${esc(s.one)}</p></div>`;
  } else {
    h += `<div class="sec-head"><h2>全部子系统</h2><p class="one">九路并行勘探的完整结果，按子系统顺序排列。用上方筛选器切换类型，或用搜索框跨全部内容检索。</p></div>`;
  }

  let total = 0;
  list.forEach((s,si)=>{
    let block = '';
    if(state.sub==='all') block += `<div class="grp"><span class="t">${String(si+1).padStart(2,'0')} · ${esc(s.n)}</span><span class="r"></span></div>`;
    TYPES.forEach(t=>{
      if(!state.types.has(t.k)) return;
      const rows = t.get(s).filter(it=>hit(itemText(t.k,it), q));
      if(!rows.length) return;
      total += rows.length;
      block += `<div class="grp"><span class="t">${t.label}</span><span class="r"></span><span class="n">${rows.length}</span></div>`
             + `<div class="cards">` + rows.map((it,i)=>cardFor(t.k,it,i)).join('') + `</div>`;
    });
    h += block;
  });
  out.innerHTML = total ? h : h + `<div class="empty">没有匹配的条目</div>`;
}

document.getElementById('q').addEventListener('input', e=>{
  state.q = e.target.value.trim().toLowerCase();
  buildChips(); render();
});
buildRail(); buildChips(); render();
</script>
'''

html = HTML.replace('__DATA__', json.dumps(data, ensure_ascii=False, separators=(',', ':')))
for k, v in TOTALS.items():
    html = html.replace('__' + k.upper() + '__', str(v))

out = HERE / 'research-viz.html'
out.write_text(html, encoding='utf-8')
print('%s  %.0f KB' % (out.name, out.stat().st_size / 1024))
