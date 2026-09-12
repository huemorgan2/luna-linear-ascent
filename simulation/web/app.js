'use strict';
const $ = id => document.getElementById(id);
const state = {run:null, compare:null, policies:{}, config:{}, cohort:'all', metric:'mean_days', range:'full', floor:1, runs:[], jobRunning:false, loadedJob:null};
const colors = {cyan:'#63d5c2', gold:'#e0c17a', purple:'#c9a6ec', ink:'#e3e4d5'};
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt = (x,d=1) => x == null || !Number.isFinite(x) ? 'Not reached' : x.toLocaleString(undefined,{maximumFractionDigits:d});
const pct = x => x == null ? 'No sample' : `${fmt(x*100)}%`;
const human = s => s.replaceAll('_',' ').replace(/^./,c=>c.toUpperCase());
const sum = (xs, fn) => xs.reduce((a,x)=>a+(fn(x)||0),0);
const median = xs => { const a=[...xs].sort((a,b)=>a-b); return a.length ? (a[Math.floor((a.length-1)/2)]+a[Math.floor(a.length/2)])/2 : null; };
async function api(path, options) { const r=await fetch(path, options); const d=await r.json(); if(!r.ok) throw Error(d.error||`Request failed (${r.status})`); return d; }
function error(message='') { $('error').textContent=message; $('error').hidden=!message; }
const stringSettings=['model_revision','decision_model','recovery_mode','warden_pool'];
const advanced = {
 durability_scale:['Weapon durability ×',.25,10,.25], heal_cost_scale:['Healing prices ×',0,4,.1], repair_reserve:['Upkeep reserve share',0,.8,.05],
 attendance:['Daily attendance',.1,1,.05], activity_spread:['Activity variation',0,.8,.05], action_seconds:['Seconds / action',1,60,1], energy_regen_minutes:['Minutes / energy',1,180,1], sleep_hours:['Sleep hours',0,12,1],
 group_hp_scale:['Group enemy HP ×',.1,5,.05], group_size_scale:['Group size ×',.5,2,.1], exhaustion_damage:['Exhausted damage ×',.05,1,.05], exhaustion_speed:['Exhausted speed loss',0,8,1], max_combat_actions:['Max actions / enemy',8,160,1],
 gold_scale:['Gold rewards ×',.1,20,.1], material_scale:['Material quantity ×',.1,20,.1], upgrade_cost_scale:['Weapon costs ×',.1,10,.1], defense_cost_scale:['Defense costs ×',.1,10,.1], repair_fraction:['Full repair cost share',0,1,.01], death_gold_loss:['Death purse loss share',0,1,.05], death_condition_loss:['Death condition loss',0,.9,.05], bank_interest_daily:['Daily bank interest',0,.1,.005],
 readiness_trials:['Readiness probes',4,32,1], readiness_threshold:['Readiness win threshold',.5,1,.05],
 warden_hp_scale:['Warden HP ×',.05,100,.05], warden_heal_start:['Healing starts / floor',1,101,1], warden_heal_reference:['Healing / reference DPS',0,20,.05], warden_heal_growth:['Healing growth / floor',1,1.15,.005], warden_cadence_seconds:['Seconds / warden strike',1,30,1], warden_energy_per_strike:['Energy / warden strike',1,12,1], warden_max_party:['Party search limit',1,512,1], warden_trials:['Trials / party size',1,8,1], warden_success_threshold:['Party win threshold',.5,1,.01]
};
function setupForm(defaults) {
 state.config=defaults.config; state.policies=defaults.policies;
 $('cpu-label').textContent=`${defaults.cpus} CPUs available · automatic`;
 $('policy-inputs').innerHTML=Object.entries(state.policies).map(([id,p])=>`<label class="policy-option" style="--policy:${p.color}" title="${esc(p.description)}"><input type="checkbox" name="policies" value="${id}" checked>${esc(p.name)}</label>`).join('');
 $('advanced-fields').innerHTML=Object.entries(advanced).map(([key,[label,min,max,step]])=>`<label>${label}<input type="number" name="${key}" value="${state.config[key]}" min="${min}" max="${max}" step="${step}" required></label>`).join('');
}
function readSettings() {
 const data=new FormData($('run-form')), cfg={...state.config, workers:0};
 for(const [key,value] of data.entries()) if(key!=='policies') cfg[key]=stringSettings.includes(key)?value:Number(value);
 cfg.policies=data.getAll('policies'); cfg.warden_pool=data.get('warden_pool');
 if(!cfg.policies.length) throw Error('Select at least one player strategy.');
 return cfg;
}
function useSettings() {
 if(!state.run) return;
 state.config={...state.config,...state.run.config,workers:0,model_revision:state.run.config.model_revision||'proposal-v1',decision_model:state.run.config.decision_model||'original',recovery_mode:state.run.config.recovery_mode||'none'};
 for(const el of $('run-form').elements) {
  if(el.name==='policies') el.checked=state.config.policies.includes(el.value);
  else if(stringSettings.includes(el.name)) el.checked=el.value===state.config[el.name];
  else if(el.name && el.name in state.config) el.value=state.config[el.name];
 }
 $('run-form').scrollIntoView({behavior:'smooth'});
}
function runLabel(r) { return `${r.run_id} · ${r.config.players} players / ${r.config.days} days`; }
async function refreshRuns(selectId) {
 const data=await api('/api/runs'); state.runs=data.runs;
 const wanted=selectId||state.run?.run_id;
 $('run-select').innerHTML=state.runs.map(r=>`<option value="${r.run_id}">${esc(runLabel(r))}</option>`).join('')||'<option value="">No saved runs</option>';
 $('compare-select').innerHTML='<option value="">No comparison</option>'+state.runs.map(r=>`<option value="${r.run_id}">${esc(runLabel(r))}</option>`).join('');
 if(state.compare) $('compare-select').value=state.compare.run_id;
 if(data.errors.length) error(`Some run files could not be read: ${data.errors.join('; ')}`);
 if(wanted && state.runs.some(r=>r.run_id===wanted)) $('run-select').value=wanted;
 if($('run-select').value) await loadRun($('run-select').value);
 else { $('empty').hidden=false; $('results').hidden=true; }
}
let loadSerial=0, compareSerial=0;
async function loadRun(id) {
 const serial=++loadSerial, run=await api(`/api/runs/${id}`);
 if(serial!==loadSerial) return;
 state.run=run; state.floor=Math.min(state.floor,run.config.max_floor);
 if(state.cohort!=='all' && !run.config.policies.includes(state.cohort)) state.cohort='all';
 $('results').hidden=false; $('empty').hidden=true; $('download').hidden=false;
 $('download').href=`/api/runs/${id}.json`; $('download').download=`${id}.json`;
 $('floor-number').max=$('floor-slider').max=run.config.max_floor;
 render();
}
function members(run=state.run) { return run.players.filter(p=>state.cohort==='all'||p.policy===state.cohort); }
function row(run,floor) { const r=run?.floors[floor-1]; return !r ? null : state.cohort==='all' ? r : r.policies[state.cohort]||null; }
function chart(id, series, options={}) {
 const el=$(id), width=Math.max(270,el.clientWidth), height=260, pad={left:52,right:18,top:20,bottom:38};
 const maxReady=players=>players.reduce((high,p)=>Math.max(high,p.ready_floor),1);
 const reached=Math.max(maxReady(members()),state.compare?maxReady(members(state.compare)):1);
 const n=state.range==='reached'?Math.min(state.run.config.max_floor,Math.max(10,Math.ceil(reached/10)*10)):state.run.config.max_floor;
 $('graph-range-label').textContent=`Floors 1–${n}`;
 const values=series.flatMap(s=>s.values.slice(0,n).filter(v=>v!=null&&Number.isFinite(v)));
 const max=options.max || Math.max(1,...values)*1.1;
 const X=f=>pad.left+(f-1)/Math.max(1,n-1)*(width-pad.left-pad.right);
 const Y=v=>height-pad.bottom-v/max*(height-pad.top-pad.bottom);
 let html=`<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="${esc(options.title)}"><title>${esc(options.title)}. Select a floor below for exact values.</title>`;
 for(let i=0;i<=4;i++) { const v=max*i/4; html+=`<line x1="${pad.left}" x2="${width-pad.right}" y1="${Y(v)}" y2="${Y(v)}" stroke="#34434b" stroke-dasharray="2 5"/><text x="${pad.left-10}" y="${Y(v)+5}" text-anchor="end">${v>=1000?fmt(v/1000,1)+'k':fmt(v,0)}</text>`; }
 const ticks=[...new Set([1,...[.25,.5,.75,1].map(x=>Math.max(1,Math.round(n*x)))])];
 for(const f of ticks) html+=`<text x="${X(f)}" y="${height-10}" text-anchor="middle">${f}</text>`;
 for(const s of series) {
  let d='', previous=false;
  s.values.slice(0,n).forEach((v,i)=>{ if(v==null||!Number.isFinite(v)){previous=false;return;} d+=`${previous?'L':'M'}${X(i+1).toFixed(2)},${Y(v).toFixed(2)} `; previous=true; });
  html+=`<path d="${d}" fill="none" stroke="${s.color}" stroke-width="${s.bold?3:2}" ${s.dash?'stroke-dasharray="6 5"':''}/>`;
  s.values.slice(0,n).forEach((v,i)=>{if(v!=null&&Number.isFinite(v)) html+=`<circle cx="${X(i+1)}" cy="${Y(v)}" r="${n<20?3:1.8}" fill="${s.color}"/>`;});
 }
 if(!values.length) html+=`<text x="${width/2}" y="${height/2}" text-anchor="middle">No qualified sample in this run</text>`;
 html+=`<line class="cursor" x1="${X(Math.min(n,state.floor))}" x2="${X(Math.min(n,state.floor))}" y1="${pad.top}" y2="${height-pad.bottom}" stroke="#e3e4d5" opacity=".35"/><rect x="${pad.left}" y="${pad.top}" width="${width-pad.left-pad.right}" height="${height-pad.top-pad.bottom}" fill="transparent"/></svg>`;
 el.innerHTML=html;
 const floorAt=e=>Math.max(1,Math.min(n,Math.round(1+(e.clientX-el.getBoundingClientRect().left-pad.left)/(width-pad.left-pad.right)*Math.max(1,n-1))));
 el.onpointermove=e=>{
  const f=floorAt(e), tip=$('tooltip');
  tip.innerHTML=`<strong>Floor ${f}</strong>\n`+series.map(s=>`${esc(s.name)}: ${s.values[f-1]==null?'No observation':fmt(s.values[f-1])+(options.suffix||'')}`).join('\n');
  tip.hidden=false; tip.style.left=`${Math.max(8,Math.min(e.clientX+16,window.innerWidth-tip.offsetWidth-12))}px`; tip.style.top=`${Math.max(8,Math.min(e.clientY+16,window.innerHeight-tip.offsetHeight-12))}px`;
  const line=el.querySelector('.cursor'); line.setAttribute('x1',X(f)); line.setAttribute('x2',X(f));
 };
 el.onpointerleave=()=>{$('tooltip').hidden=true;};
 el.onclick=e=>setFloor(floorAt(e));
}
function huntRate(run,floor) {
 const stats=members(run).map(p=>p.floors[floor]||{}), attempts=sum(stats,s=>s.attempts);
 return attempts?100*sum(stats,s=>s.wins)/attempts:null;
}
function renderCharts() {
 if(!state.run) return;
 const run=state.run, seriesFor=(key,scale=1)=>{
  const rows=run.floors.map(r=>row(run,r.floor)), out=[];
  if(state.cohort==='all') for(const p of run.config.policies) out.push({name:run.policy_definitions[p].name,color:run.policy_definitions[p].color,values:run.floors.map(r=>r.policies[p][key]==null?null:r.policies[p][key]*scale)});
  out.push({name:state.cohort==='all'?'Whole swarm':run.policy_definitions[state.cohort].name,color:colors.ink,bold:true,values:rows.map(r=>r?.[key]==null?null:r[key]*scale)});
  if(state.compare) out.push({name:'Compared run',color:colors.gold,dash:true,values:run.floors.map(r=>{const x=row(state.compare,r.floor)?.[key];return x==null?null:x*scale;})});
  return out;
 };
 chart('days-chart',seriesFor(state.metric),{title:'Days to hunting readiness',suffix:' days'});
 chart('reach-chart',seriesFor('reach_fraction',100),{title:'Percent of players ready by floor',max:100,suffix:'%'});
 const difficulty=[{name:'Actual hunt wins',color:colors.cyan,values:run.floors.map(r=>huntRate(run,r.floor))},{name:'Reference gear probes',color:colors.gold,dash:true,values:run.wardens.map(b=>b.reference.hunting_win_rate*100)}];
 if(state.compare) difficulty.push({name:'Compared hunt wins',color:colors.ink,dash:true,values:run.floors.map(r=>r.floor<=state.compare.config.max_floor?huntRate(state.compare,r.floor):null)});
 chart('difficulty-chart',difficulty,{title:'Group win rates',max:100,suffix:'%'});
 const boss=[{name:'Qualified hunters (all strategies)',color:colors.cyan,values:run.wardens.map(b=>b.available_players)},{name:'Required peers (all strategies)',color:colors.purple,values:run.wardens.map(b=>b.observed.required)},{name:'Reference equipment, may fail hunts',color:colors.gold,dash:true,values:run.wardens.map(b=>b.reference.required)}];
 if(state.compare) boss.push({name:'Compared required peers',color:colors.ink,dash:true,values:run.floors.map(r=>state.compare.wardens[r.floor-1]?.observed.required??null)});
 chart('boss-chart',boss,{title:'Qualified hunter availability and warden party demand across the whole swarm'});
}
function metric(label,value,detail) { return `<div class="metric"><span>${esc(label)}</span><strong>${esc(value)}</strong><span>${esc(detail)}</span></div>`; }
function render() {
 const run=state.run, c=run.config, ps=members();
 $('run-meta').textContent=`${c.model_revision||'proposal-v1'} / ${c.decision_model||'original'} · Enemy HP ×${c.group_hp_scale} · ${c.players} players · ${c.days} days · ${c.minutes_per_day} min/day · ${c.sessions_per_day} sessions/day · ${fmt(run.duration_seconds)}s to compute · ${run.execution?.workers??c.workers??'legacy'} CPU workers`;
 $('cohort-filters').innerHTML=[['all','Whole swarm',colors.ink],...c.policies.map(p=>[p,run.policy_definitions[p].name,run.policy_definitions[p].color])].map(([id,name,color])=>`<button data-policy="${id}" class="${id===state.cohort?'active':''}" style="color:${color}" aria-pressed="${id===state.cohort}">${esc(name)}</button>`).join('');
 const reachedTop=ps.filter(p=>p.ready_floor>=c.max_floor).length;
 $('metrics').innerHTML=metric('Median final ready floor',fmt(median(ps.map(p=>p.ready_floor))),`${ps.length} players in selected cohort`)+metric(`Reached floor ${c.max_floor}`,`${reachedTop} / ${ps.length}`,`${ps.length-reachedTop} still censored at day ${c.days}`)+metric('Mean active play',`${fmt(sum(ps,p=>p.active_minutes)/ps.length)} minutes`,'Combat time actually used per player')+metric('Readiness requirement',`${Math.ceil(c.readiness_trials*c.readiness_threshold-1e-9)} / ${c.readiness_trials} groups`,'Prepared HP/energy · owned gear');
 $('provenance').textContent=`Rules: ${run.assumptions.ruleset}\nSource: ${JSON.stringify(run.source)}\nSimulator: ${run.simulator_version} · ${run.code_commit||'uncommitted'}\nInput SHA256: ${run.input_sha256}\nCode SHA256: ${run.code_sha256}\nSeeded result SHA256: ${run.deterministic_sha256}`;
 $('saved-settings').textContent=JSON.stringify(c,null,2);
 const other=state.compare;
 $('compare-meta').hidden=!other;
 if(other) {
  const diffs=Object.keys(c).filter(k=>k!=='workers'&&JSON.stringify(c[k])!==JSON.stringify(other.config[k]));
  const mismatches=[run.input_sha256!==other.input_sha256?'input data':null,run.code_sha256!==other.code_sha256?'simulator code':null].filter(Boolean);
  $('compare-meta').textContent=`Dashed comparison: ${other.run_id}. Setting differences: ${diffs.length?diffs.map(k=>`${human(k)} ${JSON.stringify(other.config[k])} → ${JSON.stringify(c[k])}`).join(' · '):'none'}.${mismatches.length?' Different '+mismatches.join(' and ')+'; this is not an isolated parameter comparison.':''}`;
 }
 const get=k=>sum(ps,p=>p.counters[k]);
 $('resource-summary').innerHTML=metric('Gold earned',fmt(get('earned_gold')),'Secured by complete group victories')+metric('Gold spent',fmt(sum(ps,p=>sum(Object.entries(p.counters).filter(([k])=>k.startsWith('spent_')),kv=>kv[1]))),'Training, gear, repairs and supplies')+metric('XP / active minute',fmt(get('earned_xp')/(sum(ps,p=>p.active_minutes)||1)),'Kill XP retained through failed groups')+metric('Exhausted enemies',fmt(sum(ps,p=>sum(Object.values(p.floors),f=>f.exhausted))),'Unfunded enemies fought at reduced performance');
 const blocks={}; for(const p of ps) for(const [k,v] of Object.entries(p.bottlenecks)) blocks[k]=(blocks[k]||0)+v;
 const biggest=Math.max(1,...Object.values(blocks));
 $('bottlenecks').innerHTML=Object.entries(blocks).sort((a,b)=>b[1]-a[1]).map(([k,v])=>`<div><div class="bar-label"><span>${esc(human(k))}</span><span>${fmt(v,0)}</span></div><div class="bar-track"><span style="width:${v/biggest*100}%"></span></div></div>`).join('')||'<p>No blocked decisions recorded.</p>';
 $('player-table').innerHTML=ps.slice(0,100).map(p=>`<tr><td>#${p.id}</td><td>${esc(run.policy_definitions[p.policy].name)}</td><td>${p.ready_floor}</td><td>Level ${p.final.level}</td><td>${fmt(p.final.gold+p.final.bank)}</td><td>${p.final.deck.map(w=>`${esc(human(w.family))} · ${['Common','Rare','Epic','Legendary'][w.grade]} +${w.level} · ${fmt(w.condition*100,0)}%`).join('<br>')}</td></tr>`).join('');
 renderCharts(); renderFloor(); renderDiagnostics();
}
function setFloor(f) { state.floor=Math.max(1,Math.min(state.run.config.max_floor,Number(f)||1)); renderFloor(); }
function renderFloor() {
 const run=state.run,f=state.floor,r=row(run,f),b=run.wardens[f-1];
 $('floor-number').value=$('floor-slider').value=f;
 const observed=b.observed.required==null?b.observed.status:`${b.observed.required} peers · ${b.observed.status}`;
 $('floor-detail').innerHTML=`<div><h3>Floor ${f} / Preparation</h3><p>Reached: ${r?.reached||0} / ${r?.players||0} (${pct(r?.reach_fraction)})</p><p>Mean among reached: ${r?.mean_days==null?'Not reached':fmt(r.mean_days)+' days'}</p><p>Population median: ${r?.population_median==null?'Not reached':fmt(r.population_median)+' days'}</p><p>Restricted mean ≥ ${fmt(r?.restricted_mean_days)} days</p></div><div><h3>${esc(b.name)} / Whole swarm</h3><p>${b.available_players} qualified hunters</p><p>Required: ${esc(observed)}</p><p>HP ${fmt(b.hp,0)} · DEF ${fmt(b.defense,0)}</p><p>Healing ${fmt(b.heal_per_second)} HP/sec</p></div><div><h3>Reference equipment benchmark</h3><p>${b.reference.required==null?'Above party search limit':b.reference.required+' peers'}</p><p>Normal group wins: ${pct(b.reference.hunting_win_rate)}</p><p class="${b.reference.qualified?'cyan':'gold'}">${b.reference.qualified?'Reference passes readiness probes.':'Reference FAILS hunting readiness. These are not qualified hunters.'}</p><p>Party requires ${Math.ceil(run.config.warden_trials*run.config.warden_success_threshold-1e-9)} / ${run.config.warden_trials} successful trials.</p></div>`;
 $('cohort-table').innerHTML=run.config.policies.map(p=>{
  const x=run.floors[f-1].policies[p]; return `<tr><td style="color:${run.policy_definitions[p].color}">${esc(run.policy_definitions[p].name)}</td><td>${x.reached}/${x.players} · ${pct(x.reach_fraction)}</td><td>${fmt(x.mean_days)}</td><td>${fmt(x.median_days)}</td><td>${fmt(x.p90_days)}</td><td>${fmt(x.mean_active_minutes)}</td></tr>`;
 }).join('');
}
async function poll() {
 try {
  const j=await api('/api/status'); state.jobRunning=j.status==='running';
  $('run-button').disabled=state.jobRunning; $('progress').hidden=!state.jobRunning; $('progress').value=j.fraction||0;
  $('study-start').disabled=state.jobRunning;
  if(state.jobRunning) $('job-label').textContent=`${human(j.stage)} ${j.completed??0}/${j.total??'…'} · ${j.workers} CPUs · ${fmt((j.fraction||0)*100,0)}%`;
  if(j.status==='complete') {
   $('job-label').textContent=`Saved · ${fmt(j.seconds)} seconds`;
   if(j.run_id!==state.loadedJob) { state.loadedJob=j.run_id; await refreshRuns(j.run_id); if(j.study_id)await refreshStudies(j.study_id); }
  }
  if(j.status==='error') { $('job-label').textContent='Run failed'; error(j.error); }
 } catch(e) { error(`Server unavailable: ${e.message}`); }
 setTimeout(poll,1000);
}
$('run-form').addEventListener('submit',async e=>{e.preventDefault();error();try { $('run-button').disabled=true; $('job-label').textContent='Starting…'; await api('/api/runs',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(readSettings())}); } catch(e) {error(e.message);$('run-button').disabled=false;} });
$('copy-settings').onclick=useSettings;
$('diagnostic-player').onchange=renderDiagnostics;
$('run-select').onchange=e=>loadRun(e.target.value).catch(e=>error(e.message));
$('compare-select').onchange=async e=>{const serial=++compareSerial;try{const run=e.target.value?await api(`/api/runs/${e.target.value}`):null;if(serial!==compareSerial)return;state.compare=run;render();}catch(e){error(e.message);}};
$('cohort-filters').onclick=e=>{const button=e.target.closest('[data-policy]');if(button){state.cohort=button.dataset.policy;render();}};
$('metric-buttons').onclick=e=>{const b=e.target.closest('[data-metric]');if(b){state.metric=b.dataset.metric;for(const el of $('metric-buttons').children)el.classList.toggle('active',el===b);renderCharts();}};
$('range-buttons').onclick=e=>{const b=e.target.closest('[data-range]');if(b){state.range=b.dataset.range;for(const el of $('range-buttons').querySelectorAll('button'))el.classList.toggle('active',el===b);renderCharts();}};
$('floor-slider').oninput=e=>setFloor(e.target.value);$('floor-number').oninput=e=>setFloor(e.target.value);
let resize;window.addEventListener('resize',()=>{clearTimeout(resize);resize=setTimeout(renderCharts,100);});
(async()=>{try{setupForm(await api('/api/defaults'));await refreshRuns();await refreshStudies();poll();}catch(e){error(e.message);}})();

let studySerial=0;
async function refreshStudies(id) {
 const {studies}=await api('/api/studies'),selected=id||$('study-select').value;
 $('study-select').innerHTML=studies.map(s=>`<option value="${s.study_id}">${esc(s.study_id)} · ${s.status} · ${s.variants.length} variants / ${s.seeds.length} seeds</option>`).join('')||'<option value="">No saved studies</option>';
 if(studies.some(s=>s.study_id===selected))$('study-select').value=selected;
 if($('study-select').value)await loadStudy($('study-select').value);
}
async function loadStudy(id) {
 const serial=++studySerial,s=await api(`/api/studies/${id}`);if(serial!==studySerial)return;
 $('study-download').hidden=false;$('study-download').href=`/api/studies/${id}`;$('study-download').download=`${id}.json`;
 const vs=s.analysis?.variants||{},max=Math.max(1,...Object.values(vs).map(v=>v.median_floor));
 const bars=Object.entries(vs).map(([k,v])=>`<div><div class="bar-label"><span>${esc(v.name)}</span><span>Floor ${fmt(v.median_floor)} · seed medians ${v.seed_median_range.map(x=>fmt(x)).join('–')}</span></div><div class="bar-track"><span style="width:${100*v.median_floor/max}%"></span></div></div>`).join('');
 const rows=Object.entries(vs).map(([k,v])=>`<tr><td>${esc(v.name)}</td><td>${v.players} / ${v.runs}</td><td>${fmt(v.median_floor)} / ${v.max_floor}</td><td>${v.broken_final}</td><td>${pct(v.upkeep_income_share)}</td><td>${v.paired.players?`${fmt(v.paired.mean_floor_gain)} vs ${esc(vs[v.parent]?.name||v.parent)}`:'No matched parent'}</td></tr>`).join('');
 const targets=Object.entries(vs).flatMap(([k,v])=>Object.entries(v.target_floors).map(([f,r])=>`<tr><td>${esc(v.name)}</td><td>${f}</td><td>${r.reached}/${r.players} · ${pct(r.reach_fraction)}</td><td>${fmt(r.population_median)} / ${fmt(r.population_p90)}</td><td>${s.analysis.targets[f].min_days}–${s.analysis.targets[f].max_days} days</td></tr>`)).join('');
 $('study-detail').innerHTML=`<p class="note">${esc(s.status)} · ${s.completed.length}/${s.jobs.length} saved runs · ${s.jobs[0].config.days} calendar days · ${s.jobs[0].config.minutes_per_day} minutes/day. Seeds: ${s.seeds.join(', ')}.</p><h3>Median final readiness / across all sampled players</h3><div class="bars">${bars||'<p>Waiting for first saved member run.</p>'}</div><div class="table-scroll"><table><thead><tr><th>Variant</th><th>Players / seeds</th><th>Median / max floor</th><th>No working weapon</th><th>Heal + repair / income</th><th>Paired mean floor gain</th></tr></thead><tbody>${rows}</tbody></table></div><p class="chart-note">${esc(s.analysis?.caveat||'Results appear after each member run.')}</p><details><summary>Milestone reach & provisional pacing ranges</summary><p>These ranges are planning assumptions, not approved targets. Missing quantiles mean too few players arrived within the study horizon.</p><div class="table-scroll"><table><thead><tr><th>Variant</th><th>Floor</th><th>Reached</th><th>Population median / P90 days</th><th>Provisional range</th></tr></thead><tbody>${targets}</tbody></table></div></details><details><summary>Strategies, exact settings & member runs</summary><pre>${esc(JSON.stringify({policyMedians:Object.fromEntries(Object.entries(vs).map(([k,v])=>[k,v.policy_medians])),code_sha256:s.code_sha256,input_sha256:s.input_sha256,jobs:s.jobs},null,2))}</pre><div class="study-links">${s.completed.map(r=>`<button data-study-run="${r.run_id}">${esc(r.variant)} · seed ${r.seed}</button>`).join('')}</div></details>`;
}
$('study-select').onchange=e=>loadStudy(e.target.value).catch(e=>error(e.message));
$('study-refresh').onclick=()=>refreshStudies().catch(e=>error(e.message));
$('study-detail').onclick=e=>{const b=e.target.closest('[data-study-run]');if(b)refreshRuns(b.dataset.studyRun).then(()=>$('run-select').scrollIntoView({behavior:'smooth'})).catch(e=>error(e.message));};
$('study-start').onclick=async()=>{error();try{if(!$('run-form').reportValidity())return;const seeds=$('study-seeds').value.split(',').map(x=>Number(x.trim()));if(seeds.some(x=>!Number.isInteger(x)))throw Error('Enter integer seeds separated by commas.');await api('/api/studies',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({base:readSettings(),seeds})});$('study-start').disabled=true;}catch(e){error(e.message);}};

function renderDiagnostics() {
 const players=members(), select=$('diagnostic-player'), previous=select.value;
 select.innerHTML=players.map(p=>`<option value="${p.id}">#${p.id} · ${esc(state.run.policy_definitions[p.policy].name)} · floor ${p.ready_floor}</option>`).join('');
 if(players.some(p=>String(p.id)===previous)) select.value=previous;
 const p=players.find(p=>String(p.id)===select.value),d=p?.diagnosis;
 if(!d){$('diagnostic-detail').innerHTML='<p class="note">This original run has no detailed diagnostic telemetry. Its existing results are preserved; run the audited model to see recovery and failure details.</p>';return;}
 const finances=d.finances, total=Object.values(finances.spending).reduce((a,b)=>a+b,0), wallet=p.final.gold+p.final.bank;
 const bars=Object.entries(finances.spending).sort((a,b)=>b[1]-a[1]).map(([k,v])=>`<div><div class="bar-label"><span>${esc(human(k))}</span><span>${fmt(v)} · ${pct(v/(total||1))}</span></div><div class="bar-track"><span style="width:${100*v/(total||1)}%"></span></div></div>`).join('');
 const req=d.requirements.weapons.map(w=>`<tr><td>${esc(human(w.family))} +${w.level}</td><td>${fmt(w.gold_missing)} / ${fmt(w.gold)}</td><td>${w.materials_missing.join(' + ')}</td><td>${w.gate_blocked?'Gate closed':w.broken?'Repair first':'Available'}</td><td>${fmt(w.repair_quote)}</td></tr>`).join('');
 const recovery=p.recovery_episodes.map(e=>`Day ${fmt(e.start_day)} → ${e.censored?'still recovering at horizon':'day '+fmt(e.end_day)} (${fmt(e.days)} days)`).join('<br>')||'No all-paid-weapons-broken episode recorded.';
 $('diagnostic-detail').innerHTML=`<p class="note">Next floor ${d.next_floor}: ${d.reasons.map(r=>esc(human(r))).join(' · ')}</p><div class="metrics">${metric('Current deck probe',pct(d.probe.win_rate),'Prepared HP/energy; owned condition/ammo')}${metric('After repairs — diagnostic',pct(d.repaired_probe.win_rate),'Disposable copy; no free repair granted')}${metric('After supplies — diagnostic',pct(d.resupplied_probe.win_rate),'Repaired copy with stocked ammunition')}${metric('Available gold',fmt(wallet),'Purse + bank; resources actually owned')}</div><p>${esc(d.counterfactual_note)}</p><div class="bars">${bars}</div><p class="chart-note">Earned hunting gold ${fmt(finances.incoming.earned_gold)} · interest ${fmt(finances.incoming.interest)} · salvage ${fmt(finances.incoming.salvage_gold)} · death loss ${fmt(finances.death_loss)} · forfeited pending haul ${fmt(finances.forfeited_pending_gold)}. Pending haul was never part of the purse. Accounting error: ${fmt(finances.conservation_error,8)}.</p><h3>Next weapon steps / missing resources</h3><div class="table-scroll"><table><thead><tr><th>Weapon</th><th>Gold missing / price</th><th>Materials missing A+B</th><th>Gate</th><th>Repair quote</th></tr></thead><tbody>${req}</tbody></table></div><p>Next training: ${d.requirements.training.level??'level cap'} · ${fmt(d.requirements.training.gold_missing)} gold missing · ${fmt(d.requirements.training.xp_missing)} XP missing.</p><h3>Recovery history</h3><p>${recovery}</p><details><summary>Weekly finances & failed encounter types</summary><pre>${esc(JSON.stringify({failedProbe:d.probe.failures,types:d.probe.types,lastRoute:d.last_route,timeline:p.timeline},null,2))}</pre></details>`;
}
