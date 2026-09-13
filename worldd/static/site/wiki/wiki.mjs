// Shared, inspectable research calculations; this module never calls game actions.
export const clamp=(lo,hi,v)=>Math.min(hi,Math.max(lo,v));
export const price=(base,factor)=>Math.ceil(base*Math.round(factor*100)/100);
// A drawing belongs to a family AND grade; never silently reuse another grade.
export function weaponArt(w,grade){
 const art=w.images[grade];
 if(!art)throw new Error(`Missing ${grade} art for ${w.id}`);
 return {...art,alt:`${grade} ${w.name}: ${art.description}`};
}
// These values are baked by the Python game resolver. The browser presents
// selections; it does not maintain a second combat or price model.
export function hitPreview(w,t,a,gap){return {...w.hitExamples[t.id][a.id][gap]};}
export function shieldPreview(data,index){return {...data.shieldExamples[index]};}
export function lootPreview(model,m,floor,deep=false,specimen='common'){
 if(floor!==m.floor)throw new Error('Creature floor mismatch');
 return m.lootByMode[deep?'deep':'normal'][specimen];
}
export function familyWeight(model,w,m){return m.familyWeights[w.id];}
export function acquisition(data,w,gi){return w.sources[data.model.grades[gi]];}
const fmt=n=>Number(n).toLocaleString('en-US');
const pct=n=>n===0?'0%':Number(n.toFixed(8)).toLocaleString('en-US',{maximumFractionDigits:8})+'%';
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let data,model,state={floor:1,enemy:'ground-power',weapon:'runestring',arrow:'arcane',gap:2,path:'All',grade:0,level:0,raw:100,armor:40,shield:80,wall:false,shieldCase:0,movement:0,players:50,efficiency:100,hunt:'normal',lootView:'drops',specimen:'common',lootFloor:'all',query:''};
const $=id=>document.getElementById(id);
const icon=key=>`<span class="ico" aria-hidden="true" style="--icon:url('${data.icons[key]||data.icons.note}')"></span>`;
const type=id=>model.types.find(x=>x.id===id);
const weapon=()=>model.weapons.find(x=>x.id===state.weapon);
const weaponPortrait=(w,gi,width,height,lazy=false)=>{const a=weaponArt(w,model.grades[gi]);return `<img src="${esc(a.src)}" alt="${esc(a.alt)}" width="${width}" height="${height}" ${lazy?'loading="lazy"':''}>`;};
const affinityIcon=t=>t.affinity==='Power'?'t_armor':t.affinity==='Magic'?'t_resist':'shard';
const badges=id=>{const t=type(id);return `<div class="badge-row"><span class="badge aff-${t.affinity.toLowerCase()}">${icon(affinityIcon(t))}${esc(t.affinity)}</span><span class="badge ${t.air?'air':''}">${icon(t.air?'t_wing':'shoes')}${t.air?'Air':'Ground'}</span></div>`;};
function table(head,rows){return `<table><thead><tr>${head.map(x=>`<th scope="col">${x}</th>`).join('')}</tr></thead><tbody>${rows.map(c=>`<tr>${c.map(x=>`<td>${x}</td>`).join('')}</tr>`).join('')}</tbody></table>`;}
function choices(target,name,label,options,value,{four=false,rarity=false}={}){
 $(target).innerHTML=`<fieldset class="choices"><legend>${label}</legend><div class="choice-grid ${four?'four':''}">${options.map((o,i)=>`<label class="choice ${rarity?'rarity-choice rarity-'+i:''}"><input type="radio" name="${name}" value="${esc(o.id)}" ${String(value)===String(o.id)?'checked':''}>${icon(o.icon||'shard')}<span>${esc(o.name)}</span></label>`).join('')}</div></fieldset>`;
}
function range(id,label,min,max,value){return `<div class="range-control"><label for="${id}" class="control-line">${label}<output id="${id}-value">${value}</output></label><input id="${id}" type="range" min="${min}" max="${max}" value="${value}"></div>`;}
function metrics(entries){return `<dl class="metric-list">${entries.map(([k,v])=>`<div><dt>${k}</dt><dd>${v}</dd></div>`).join('')}</dl>`;}
function installControls(){
 choices('enemy-choices','enemy','ENEMY PROFILE',model.types.map(t=>({id:t.id,name:t.name,icon:affinityIcon(t)})),state.enemy);
 $('weapon-select').innerHTML=model.weapons.map(w=>`<option value="${w.id}" ${state.weapon===w.id?'selected':''}>${w.name} · ${w.path}</option>`).join('');
 choices('arrow-choices','arrow','ARROW PAYLOAD · BOWS ONLY',model.arrows.map(a=>({...a,icon:a.channel==='Magic'?'staff':'quiver'})),state.arrow);
 choices('distance-choices','gap','DISTANCE',[{id:0,name:'Contact'},{id:1,name:'Near'},{id:2,name:'Far'},{id:3,name:'Cover'}].map(x=>({...x,icon:'shoes'})),state.gap,{four:true});
 choices('path-choices','path','WEAPON PATH',['All','Blade','Bow','Staff'].map((x,i)=>({id:x,name:x==='All'?'All weapons':x,icon:['pack','sword','bow','staff'][i]})),state.path,{four:true});
 for(const target of ['arsenal-grade-choices','forge-grade-choices'])choices(target,target,'WEAPON GRADE',model.grades.map((g,i)=>({id:i,name:g,icon:'shard'})),state.grade,{four:true,rarity:true});
 choices('shield-controls','shieldCase','DEFENSE EXAMPLES',data.shieldExamples.map((r,i)=>({id:i,name:r.name,icon:'shield'})),state.shieldCase);
 $('raid-controls').innerHTML=range('raid-players','PLAYERS ATTACKING TOGETHER',1,100,50)+range('raid-efficiency','TACTICAL EFFICIENCY (%)',75,150,100);
 choices('hunt-choices','hunt','HUNTING GROUND',[{id:'normal',name:'Normal hunt',icon:'shoes'},{id:'deep',name:'Deep hunt · Floor 4+',icon:'sword'}],state.hunt);
 choices('loot-view-choices','lootView','TABLE VIEW',[{id:'drops',name:'Drop chances',icon:'pack'},{id:'parameters',name:'Creature parameters',icon:'t_armor'}],state.lootView);
 choices('specimen-choices','specimen','CREATURE SPECIMEN',['runt','common','tough','alpha'].map(x=>({id:x,name:x[0].toUpperCase()+x.slice(1),icon:'t_bulwark'})),state.specimen,{four:true});
 $('loot-floor').innerHTML='<option value="all">All 100 floors</option>'+data.floors.map(f=>`<option value="${f.floor}">${f.floor} · ${esc(f.zone)}</option>`).join('');
 $('counter-table').innerHTML=table(['ENEMY','BLADE / CONTACT','POWER ARROW','SPELL / ARCANE','SPEED'],model.types.map(t=>[badges(t.id),t.air?'Cannot reach':t.power+'×',t.power+'×',t.magic+'×',t.speed]));
 $('effects-table').innerHTML=table(['EFFECT','STRENGTH / DURATION','CHANNEL','RESISTANCE','RULE'],model.effects);
 $('arrow-grid').innerHTML=model.arrows.map(a=>`<article class="arrow-card"><h3>${icon(a.channel==='Magic'?'staff':'quiver')}${a.name.toUpperCase()}</h3><p>${a.channel} · ${a.impact}× impact</p><p>${esc(a.effect)}</p><p>20 Common: ${fmt(data.arrowQuotes.Common[a.id].gold)} gold</p><p>One arrow per shot, including a miss.</p></article>`).join('');
 $('material-grades').innerHTML=model.grades.map((g,i)=>`<div class="grade-info rarity-${i}">${icon('shard')}${g}<p>Floors ${i*25+1}–${i*25+25}</p><p>${model.materials[i].map(m=>icon(data.materialIcons[m])+esc(m)).join(' + ')}</p></div>`).join('');
 $('roster-count').textContent=`${data.creatureCount} CREATURES / 100 FLOORS`;
 $('source-version').textContent=`Rules generated from game ${data.gameVersion}: ${data.creatureCount} creatures, 64 weapons, 8 resource locations. Shared wardens remain a separate release phase.`;
 document.querySelectorAll('[data-icon]').forEach(el=>el.outerHTML=icon(el.dataset.icon));
 renderAcquisition();renderLootFormulas();renderGathering();
}
function renderFloor(){
 const f=data.floors[state.floor-1];
 $('floor-range').value=state.floor;$('floor-value').textContent=`${state.floor} / 100`;
 $('floor-title').textContent=`FLOOR ${String(state.floor).padStart(2,'0')} · ${f.zone.toUpperCase()}`;
 $('floor-description').textContent=f.description;$('floor-meta').textContent=`${f.biome} · ${f.town} · ${f.monsters.length} creatures · groups of ${f.groups[0]}–${f.groups[1]} · ${f.deep.unlocked?'Deep hunting available':'Deep hunting unlocks on Floor 4'}`;
 $('floor-prev').disabled=state.floor===1;$('floor-next').disabled=state.floor===100;
 $('creature-grid').innerHTML=f.monsters.map(m=>`<article class="creature-card aff-${type(m.proposedType).affinity.toLowerCase()}" data-creature-id="${m.id}"><div class="creature-image"><img src="${m.image}" alt="${esc(m.name)}" width="320" height="112"></div><div class="creature-body">${badges(m.proposedType)}<h3>${esc(m.name)}</h3><div class="stat-row"><span>${icon('heart')}${fmt(m.hp)} HP</span><span>${icon('sword')}${fmt(m.atk)} ATK</span><span>${icon('t_armor')}${fmt(m.defense)} DEF</span><span>${icon('t_speed')}${m.speed} SPD</span></div><p>${esc(m.lore)}</p><p>${esc(m.traits.join(' · ')||'No special traits')}</p><button class="details-button" data-monster="${m.id}" data-floor="${state.floor}">[ STATS & DROP CHANCES ]</button></div></article>`).join('');
 $('floor-warden').innerHTML=`<span>${icon('t_bulwark')}${esc(f.warden.name)} · LEGACY WARDEN COMPARISON</span><div class="stat-row"><span>${fmt(f.warden.hp)} HP</span><span>${fmt(f.warden.atk)} ATK</span><span>${fmt(f.warden.defense)} DEF</span></div>`;
 const group=f.groupExample;
 $('group-loot-example').innerHTML=`<p>${group.names.map(esc).join(' + ')} · Common specimens. Conditional on clearing the whole group.</p>`+table(['AT LEAST ONE','MATERIAL BUNDLE','WEAPON'],model.grades.map((g,i)=>[g,pct(group.material[i]),pct(group.weapon[i])]))+`<p class="muted">For these independent enemy rolls: 1 − product(1 − each enemy’s chance). Actual groups and specimens vary. Losing or fleeing secures none of the pending haul.</p>`;

}
function renderHit(){
 const w=weapon(),t=type(state.enemy),a=model.arrows.find(x=>x.id===state.arrow),r=hitPreview(w,t,a,state.gap);
 $('hit-preview').innerHTML=`<h3>DIRECT HIT PREVIEW</h3><div class="damage-readout">${icon('sword')} <strong>${r.damage} DAMAGE</strong><div class="pixel-meter" aria-hidden="true">${Array.from({length:20},(_,i)=>`<span class="${i<Math.round(r.damage/10)?'on':''}"></span>`).join('')}</div></div><p>${icon(r.channel==='Magic'?'staff':'sword')}${r.channel} · ${r.reach?r.multiplier+'× affinity':'OUT OF REACH'}</p>${badges(t.id)}<p>${esc(t.note)}</p><div class="hit-footer"><h3>${esc(w.name)}</h3><p>${r.reach?esc(w.path==='Bow'?a.effect:w.description):t.air?'Blades cannot hit Air. Bring a bow or staff.':'Close to contact first. Approaching spends an action.'}</p></div>`;
}
function renderWeapons(){
 const g=model.grades[state.grade];
 $('weapon-grid').innerHTML=model.weapons.filter(w=>state.path==='All'||w.path===state.path).map(w=>`<button class="weapon-card rarity-${state.grade}" data-weapon="${w.id}">${weaponPortrait(w,state.grade,60,96,true)}<span class="weapon-copy"><span>${g.toUpperCase()} · ${w.path.toUpperCase()}</span><strong>${w.name}</strong><span>${w.effect}</span><span class="muted">${w.factor}× ATK / ${w.end}× END</span></span></button>`).join('');
}
function renderForge(){
 const w=weapon(),g=model.grades[state.grade],s=w.states[g][state.level],a=acquisition(data,w,state.grade);
 $('upgrade-value').textContent='+'+state.level;
 $('forge-weapon').innerHTML=`<div class="forge-weapon rarity-${state.grade}">${weaponPortrait(w,state.grade,60,96)}<div><h3>${g} +${state.level}</h3><p>${w.name}</p><span>${w.effect} · from +0</span></div></div>`+metrics([['Floor gate',s.floor],['Full-condition ATK bonus',fmt(s.atk)],['Max endurance',fmt(s.dur)],['Shop delivers','+'+a.cfg.shopLevel+' at Floor '+a.shop.floor],['Monster drop','+'+a.cfg.dropLevel+' · '+a.cfg.dropDurabilityPct+'% endurance']]);
 $('recipe').innerHTML=`<h3>${state.level===0?'CRAFT +0 IN THE FORGE':'UPGRADE CHARGE TO +'+state.level}</h3>`+metrics([['Gold',icon('coin')+fmt(s.gold)]])+model.materials[state.grade].map((m,i)=>`<div class="material rarity-${state.grade}">${icon(data.materialIcons[m])}<span>${m}</span><span>${fmt(s.materials[m])}</span></div>`).join('')+`<div class="forge-link">${icon('t_wrench')}${state.level===20?'MAX LEVEL AFTER THIS UPGRADE':state.level===0?'CRAFT IN THE FORGE':'UPGRADE IN THE FORGE'}</div><p class="muted">An individual step charge, not a shop listing. Shop +${a.cfg.shopLevel} costs ${fmt(a.shopGold)} gold and arrives at the displayed level. See all source settings below.</p>`;
 $('upgrade-table').innerHTML=table(['LEVEL','FLOOR','GOLD / STEP',...model.materials[state.grade],'ATK','MAX CONDITION'],w.states[g].map(x=>['+'+x.level,x.floor,fmt(x.gold),...model.materials[state.grade].map(m=>fmt(x.materials[m])),fmt(x.atk),fmt(x.dur)]));
 $('upgrade-table-title').textContent=`ALL 21 ${g.toUpperCase()} LEVELS · ${w.name.toUpperCase()}`;
}
function renderShield(){
 const r=shieldPreview(data,state.shieldCase);state.raw=r.raw;
 $('damage-bar').innerHTML=`<span class="armor" style="width:${r.armor/state.raw*100}%"></span><span class="shield" style="width:${r.shield/state.raw*100}%"></span><span class="hp" style="width:${r.hp/state.raw*100}%"></span>`;
 $('shield-results').innerHTML=`<p>Incoming ${r.raw} · armor DEF ${r.armorDef} · shield DEF ${r.shieldDef} · ${r.guard?'Guard':'ordinary stance'}</p><div class="allocation"><span>Armor <b>${r.armor}</b></span><span>Shield <b>${r.shield}</b></span><span>HP lost <b class="hurt">${r.hp}</b></span><span>Shield wear <b>${r.wear}</b></span></div>`;
}
function renderMovement(){
 const active=[0,2,1][state.movement];
 $('movement-track').innerHTML=['Contact','Near','Far','Cover'].map((x,i)=>`<span class="${i===active?'on':''}">${icon(i===active?'run':'shoes')}${i}<br>${x}</span>`).join('');
 $('movement-copy').textContent=['A ground enemy is at contact. Ramguard’s shove is ready.','The shove lands: two steps back to Far. Pursuit is suppressed this phase; your next action comes first.','Switch to a bow as part of the paid attack and take the shot. The enemy then pursues one step. Escape could have used that opening instead.'][state.movement];
 $('movement-next').textContent=state.movement===0?'[ LAND A SHOVE ]':'[ TAKE A BOW SHOT ]';$('movement-next').disabled=state.movement===2;
}
function renderRaid(){
 const net=state.players*10*state.efficiency/100-300,seconds=net>0?4500/net:Infinity;
 $('raid-result').innerHTML=`<h3 class="gold">${seconds<=30?'THE GROUP CAN WIN':net<=0?'HEALING WINS':'ENERGY RUNS OUT'}</h3>`+metrics([['Group DPS',fmt(state.players*10*state.efficiency/100)],['Healing / second','300'],['Net DPS',fmt(Math.max(0,net))],['Time to defeat',Number.isFinite(seconds)?seconds.toFixed(1)+' seconds':'No progress']])+`<p>${seconds<=30?'Better preparation makes a smaller group viable.':'The group needs more sustained damage or a longer usable energy window.'}</p>`;
}
function openDialog(html){$('detail-content').innerHTML=html;if(!$('detail-dialog').open)$('detail-dialog').showModal();}
function gradeGallery(w,selected){
 return `<h3>FOUR GRADES · FOUR DESIGNS</h3><p class="muted">Select a design to see its grade settings.</p><div class="grade-gallery">${model.grades.map((g,gi)=>{const a=weaponArt(w,g);return `<button class="grade-design rarity-${gi}" data-art-weapon="${w.id}" data-art-grade="${gi}" aria-pressed="${gi===selected}" aria-label="View ${g} ${w.name}"><span class="grade-design-name">${g.toUpperCase()}</span>${weaponPortrait(w,gi,80,128)}<span class="grade-design-description">${esc(a.description)}</span><span class="grade-design-state">${gi===selected?'[ SELECTED ]':'[ VIEW GRADE ]'}</span></button>`;}).join('')}</div>`;
}
function showWeapon(id){
 const w=model.weapons.find(x=>x.id===id),gi=state.grade,g=model.grades[gi],a=acquisition(data,w,gi),next=w.states[g][Math.min(20,state.level+1)];
 openDialog(`<h2 id="detail-title">${g.toUpperCase()} · ${w.name.toUpperCase()}</h2><div class="dialog-weapon">${weaponPortrait(w,gi,72,120)}<div><p>${icon(w.path==='Blade'?'sword':w.path.toLowerCase())}${w.path} · ${w.effect}</p><p>${w.factor}× attack / ${w.end}× endurance</p></div></div><p>${w.description}</p>`+gradeGallery(w,gi)+metrics([['Technique recharge',w.cooldown?w.cooldown+' subsequent combat actions':'Passive'],['Grade recipe',w.recipe[0]+'A : '+w.recipe[1]+'B'],['Shop',`+${a.cfg.shopLevel} · ${fmt(a.shopNow)}/${fmt(a.shopMax)} END · Floor ${a.shop.floor}`],['Dropped',`+${a.cfg.dropLevel} · ${fmt(a.dropNow)}/${fmt(a.dropMax)} END (${a.cfg.dropDurabilityPct}%)`],['Shop gold',fmt(a.shopGold)],['Forge craft',`+${a.cfg.craftLevel} · ${fmt(a.craftNow)}/${fmt(a.craftMax)} END · Floor ${a.craft.floor}`],['Craft cost',`${fmt(a.craftGold)} gold<br>${model.materials[gi].map((m,i)=>fmt(a.craftQ*w.recipe[i])+' '+m).join('<br>')}`],['Drop sources',`${data.floors.filter(f=>f.floor>=a.findFloor).reduce((n,f)=>n+f.monsters.length,0)} creatures · Floor ${a.findFloor}+ find / ${a.drop.floor}+ equip`]])+`<p class="gold">Watch for: ${w.weakness}</p><div class="stock-demo rarity-${gi}"><h3>EXAMPLE PACK · NEXT UPGRADE +${next.level}</h3>${model.materials[gi].map((m,i)=>{const required=next.materials[m],owned=i===0?Math.floor(required*.6):required;return `<div class="stock-row"><div><span>${m}</span><span>${owned} / ${required}</span></div><progress value="${owned}" max="${required}"></progress></div>`;}).join('')}<p class="muted">Illustrative gathered / required amounts, not your inventory.</p></div><div class="action-row"><button class="primary" data-compare="${w.id}">[ COMPARE WEAPON ]</button><button data-forge="${w.id}">[ UPGRADE IN THE FORGE ]</button></div>`);
}
function specimenStats(m,f,deep,specimen){
 const s=f.specimens[specimen],pre=m.specimenStats?.[specimen];
 return {hp:pre?.hp??Math.round(m.hp*s.hp),atk:deep?(pre?.deepAtk??Math.round(Math.round(m.atk*s.atk)*f.deep.atk)):(pre?.atk??Math.round(m.atk*s.atk)),speed:deep?pre.deepSpeed:pre.speed};
}
function lootRows(l){return model.grades.map((g,i)=>[`<span class="badge rarity-${i}" style="color:var(--rarity)">${icon('shard')}${g}</span>`,pct(l.material[i]),pct(l.weapon[i])]);}
function showMonster(id,floor){
 const f=data.floors[floor-1],m=f.monsters.find(x=>x.id===id),deep=state.hunt==='deep',l=lootPreview(model,m,floor,deep,state.specimen),s=specimenStats(m,f,deep,state.specimen);
 openDialog(`<h2 id="detail-title">${esc(m.name.toUpperCase())} · FLOOR ${floor}</h2><div class="creature-image aff-${type(m.proposedType).affinity.toLowerCase()}"><img src="${m.image}" alt="${esc(m.name)}" width="320" height="112"></div>${badges(m.proposedType)}<p>${esc(m.lore)}</p>`+metrics([['Environment',esc(f.zone)+' · '+esc(f.town)],['Traits',esc(m.traits.join(', ')||'None')],['Combat type',esc(m.currentType)],['HP / ATK / DEF',`${fmt(s.hp)} / ${fmt(s.atk)} / ${fmt(m.defense)}`],['Speed / creature bar',`${s.speed} / ${m.bar}`],['Authored spawn share',pct(m.spawn)],['Base XP / gold',`${fmt(m.xp)} / ${fmt(m.gold)}`],['Deep hunt eligible',m.deepEligible?'Yes':'No'],['Material carrier',`${m.carrier} · A:B ${model.loot.carrierRatios[m.carrier].join(':')}`]])+`<h3>DROP CHANCES · ${state.hunt.toUpperCase()} / ${state.specimen.toUpperCase()}</h3><p>${l.eligible?'Chance after defeating this exact creature.':'This creature/specimen is not available in this hunting mode. Switch to Normal in the loot settings.'}</p><div class="table-wrap">${table(['GRADE','MATERIAL','WEAPON'],lootRows(l))}</div><p>No weapon: ${pct(l.none)}. Material grades roll independently.</p><div class="table-wrap">${table(['WEAPON FAMILY','WEIGHT','COMMON ITEM','RARE ITEM','EPIC ITEM','LEGENDARY ITEM'],model.weapons.map(w=>{const total=model.weapons.reduce((v,x)=>v+familyWeight(model,x,m),0),weight=familyWeight(model,w,m);return [w.name,weight,...l.weapon.map(p=>pct(p*weight/total))];}))}</div>`);
}
function renderLoot(){
 const deep=state.hunt==='deep';
 const selected=data.floors.filter(f=>state.lootFloor==='all'||f.floor===Number(state.lootFloor));
 const rows=[];let count=0;
 for(const f of selected)for(const m of f.monsters){
  if(state.query&&!`${m.name} ${m.id} ${m.traits.join(' ')} ${f.zone}`.toLowerCase().includes(state.query.toLowerCase()))continue;
  count++;const l=lootPreview(model,m,f.floor,deep,state.specimen),s=specimenStats(m,f,deep,state.specimen);
  const identity=[`<button class="loot-creature" data-monster="${m.id}" data-floor="${f.floor}"><span class="creature-image aff-${type(m.proposedType).affinity.toLowerCase()}"><img src="${m.image}" alt="" width="96" height="34" loading="lazy"></span><span>${esc(m.name)}</span></button>`,`${f.floor}<br>${esc(f.zone)}`];
  rows.push(state.lootView==='drops'?[...identity,...model.grades.map((g,i)=>`<span class="drop-grade rarity-${i}">${l.eligible?pct(l.material[i])+' material<br>'+pct(l.weapon[i])+' weapon':'Not in this hunt'}</span>`),l.eligible?pct(l.none):'—']:[...identity,badges(m.proposedType),esc(m.traits.join(' / ')||'None'),`${fmt(s.hp)} HP<br>${fmt(s.atk)} ATK<br>${fmt(m.defense)} DEF<br>${s.speed} SPD`,`${pct(m.spawn)}<br>bar ${m.bar}`,`${fmt(m.xp)} XP<br>${fmt(m.gold)} gold`,`${m.carrier} · ${l.species.toFixed(3)}×`,l.eligible?'Yes':'Not in this hunt']);
 }
 $('loot-table').innerHTML=table(state.lootView==='drops'?['CREATURE / IMAGE','FLOOR / ENVIRONMENT',...model.grades.map(g=>g.toUpperCase()),'NO WEAPON']:['CREATURE / IMAGE','FLOOR / ENVIRONMENT','TYPE','TRAITS','SPECIMEN STATS','AUTHORED SHARE / BAR','BASE REWARDS','CARRIER / LOOT FACTOR','ELIGIBLE'],rows);
 $('loot-count').textContent=`${count} / ${data.creatureCount} creatures · ${deep?'Deep':'Normal'} hunt · ${state.specimen} specimen · all percentages conditional on defeat`;
 $('hunt-setting-note').textContent=deep?'Deep: +20% ATK, +1 speed, 1 energy per enemy. Material rarity multipliers C/R/E/L: ×1.15/1.5/2/3; weapon multipliers: ×1.25/1.75/2.5/4. Frail/feeble creatures and runts are not in the deep roster.':'Normal: 1 energy per enemy. Loot follows floor, species body/bite and specimen; it is not equally likely from every animal.';
 const fs=state.lootFloor==='all'?data.floors[state.floor-1]:data.floors[+state.lootFloor-1];
 $('specimen-odds').textContent=`Specimen mix at Floor ${fs.floor}: `+Object.keys(fs.specimens).map(k=>`${k} ${deep?fs.deepSpecimenWeights[k]:fs.specimens[k].weight}%`).join(' · ')+(fs.deep.unlocked?`. Deep XP/gold multiplier here: ×${fs.deep.reward}.`:'. Deep hunting is unavailable here.')+' Rewards also use specimen and player XP bonuses.';
}
function renderLootFormulas(){
 const cfg=model.loot;
 $('loot-formulas').innerHTML=`<p>Interpolate the floor baseline. Multiply by body × bite × specimen and, in a deep hunt, the rarity-specific deep bonus. Cap each material roll at ${cfg.materialCapPct}%. Cap the total weapon-drop chance at ${cfg.weaponTotalCapPct}% by proportionally scaling its grade weights; the remainder is no weapon.</p><p>Specimen loot factors: ${Object.entries(cfg.specimen).map(([k,v])=>`${k} ×${v}`).join(' · ')}.</p><p>Body: ${Object.entries(cfg.body).map(([k,v])=>`${k} ×${v}`).join(' · ')}. Bite: ${Object.entries(cfg.bite).map(([k,v])=>`${k} ×${v}`).join(' · ')}. Unlisted traits use ×1.</p><p>Legendary discovery is zero below Floor ${cfg.legendaryDiscoveryFloor}. Rare and Epic discovery is possible earlier, at the small rates shown. Item equipment gates still apply; finding high-grade treasure does not grant its power early.</p><p>Bundle size Y = min(5,1+floor(max(0,floor−grade start)/6)). A carriers give 3Y:1Y; B carriers give 1Y:3Y; mixed gives 2Y:2Y. Air creatures carry A, Magic ground carries B, other ground carries mixed. A successful grade roll gives that grade's two named materials. Grade starts: 1/26/51/76.</p><div class="table-wrap">${table(['FLOOR','COMMON MAT %','RARE MAT %','EPIC MAT %','LEGENDARY MAT %'],cfg.materialKnots.map(x=>[x[0],...x.slice(1).map(pct)]))}</div><div class="table-wrap">${table(['FLOOR','COMMON WEAPON %','RARE WEAPON %','EPIC WEAPON %','LEGENDARY WEAPON %'],cfg.weaponKnots.map(x=>[x[0],...x.slice(1).map(pct)]))}</div><p>These tables are baseline percentages before species/specimen/deep modifiers. More materials per hour still depend on survival, energy and encounter selection. Smart routing is allowed to be faster.</p>`;
}
function renderAcquisition(){
 const rows=[];
 for(let gi=0;gi<4;gi++)for(const w of model.weapons){const a=acquisition(data,w,gi);rows.push([`<button class="loot-creature rarity-${gi}" data-source-weapon="${w.id}" data-grade="${gi}">${weaponPortrait(w,gi,30,48,true)}<span>${model.grades[gi]}<br>${w.name}</span></button>`,w.effect,'+'+a.cfg.shopLevel,a.shop.floor,`${fmt(a.shopNow)} / ${fmt(a.shopMax)}<br>${a.cfg.shopDurabilityPct}%`,fmt(a.shop.atk),fmt(a.shopGold),'+'+a.cfg.dropLevel,`${a.findFloor}+ find<br>${a.drop.floor}+ equip`,`${fmt(a.dropNow)} / ${fmt(a.dropMax)}<br>${a.cfg.dropDurabilityPct}%`,fmt(a.drop.atk),`+${a.cfg.craftLevel} · Floor ${a.craft.floor}<br>${fmt(a.craftNow)}/${fmt(a.craftMax)} END · ${a.cfg.craftDurabilityPct}%<br>${fmt(a.craft.atk)} ATK<br>${fmt(a.craftGold)} gold<br>${model.materials[gi].map((m,i)=>fmt(a.craftQ*w.recipe[i])+' '+m).join('<br>')}`,`Shop / Forge / ${data.floors.filter(f=>f.floor>=a.findFloor).reduce((n,f)=>n+f.monsters.length,0)} hunt creatures<br>${w.path==='Bow'?'Air':w.path==='Staff'?'Ground Power':'Ground Magic'} favored ×3`]);}
 $('acquisition-table').innerHTML=table(['WEAPON / GRADE','POWER','SHOP LEVEL','SHOP FLOOR','SHOP END: NOW / MAX','SHOP ATK','SHOP GOLD','DROP LEVEL','DROP FLOOR','DROP END: NOW / MAX','DROP ATK','FORGE CRAFT: LEVEL / FLOOR / COST','SOURCES / WEIGHT'],rows);
}
function renderGathering(){
 $('gathering-grid').innerHTML=data.sites.map(site=>`<article class="panel"><img class="site-banner" src="${site.image}" alt="${esc(site.name)}" width="320" height="112" loading="lazy"><h3>${esc(site.name)} · FLOOR ${site.floor}</h3><p>${esc(site.description)}</p>`+metrics([['Target',site.material],['Tool sold here',site.tool_name+' · '+fmt(site.price)+' gold'],['Tool condition',site.condition],['Each attempt',site.yield_pct+'% for '+site.yield_amount+' '+site.material],['Ambush chance',site.ambush_pct+'% · '+(site.ambush_size||2)+' enemies'],['Favored weapon',site.preferred],['Attempt cost','1 energy + 1 tool condition']])+`<p>Defeat every ambusher for bonus materials. Gathered and won loot stays unbanked until you extract. Fleeing or dying abandons that expedition’s haul.</p><details><summary>CREATURES GUARDING THIS PLACE</summary>`+(site.roster?table(['CREATURE','TYPE','SELECTION WEIGHT'],site.roster.map(r=>{const m=data.floors[r.floor-1].monsters.find(m=>m.id===r.id);return [esc(m.name),badges(m.proposedType),r.weight];})):'<p>Nearby floors ±2. Preferred targets receive weight5; complementary targets weight1.</p>')+`</details></article>`).join('');
}
function setGrade(gi){state.grade=gi;document.querySelectorAll('[name$="grade-choices"]').forEach(x=>x.checked=+x.value===gi);renderWeapons();renderForge();}
function chooseWeapon(id,section){state.weapon=id;$('weapon-select').value=id;renderHit();renderForge();$('detail-dialog').close();$(section).scrollIntoView({behavior:'smooth'});}
function bind(){
 document.addEventListener('change',event=>{
  const el=event.target;if(!(el instanceof HTMLInputElement||el instanceof HTMLSelectElement))return;
  if(el.name==='enemy'){state.enemy=el.value;renderHit();}
  if(el.name==='arrow'){state.arrow=el.value;renderHit();}
  if(el.name==='gap'){state.gap=+el.value;renderHit();}
  if(el.name==='path'){state.path=el.value;renderWeapons();}
  if(el.name.endsWith('grade-choices')){setGrade(+el.value);}
  if(el.id==='weapon-select'){state.weapon=el.value;renderHit();renderForge();}
  if(el.name==='shieldCase'){state.shieldCase=+el.value;renderShield();}
  if(el.name==='lootView'){state.lootView=el.value;renderLoot();}
  if(el.name==='hunt'){state.hunt=el.value;renderLoot();}
  if(el.name==='specimen'){state.specimen=el.value;renderLoot();}
  if(el.id==='loot-floor'){state.lootFloor=el.value;renderLoot();}
 });
 document.addEventListener('input',event=>{
  const el=event.target;if(!(el instanceof HTMLInputElement))return;
  if(el.id==='floor-range'){state.floor=+el.value;renderFloor();if(state.lootFloor==='all')renderLoot();}
  if(el.id==='upgrade-range'){state.level=+el.value;renderForge();}
  const map={'incoming':'raw','armor-def':'armor','shield-def':'shield','raid-players':'players','raid-efficiency':'efficiency'};
  if(map[el.id]){state[map[el.id]]=+el.value;$(el.id+'-value').textContent=el.value;el.id.startsWith('raid-')?renderRaid():renderShield();}
  if(el.id==='loot-search'){state.query=el.value;renderLoot();}
 });
 document.addEventListener('click',event=>{
  const b=event.target.closest('button');if(!b)return;
  if(b.dataset.weapon)showWeapon(b.dataset.weapon);
  if(b.dataset.artWeapon){setGrade(+b.dataset.artGrade);showWeapon(b.dataset.artWeapon);$('detail-content').querySelector('[aria-pressed="true"]')?.focus({preventScroll:true});}
  if(b.dataset.sourceWeapon){setGrade(+b.dataset.grade);showWeapon(b.dataset.sourceWeapon);}
  if(b.dataset.monster)showMonster(b.dataset.monster,+b.dataset.floor);
  if(b.dataset.compare)chooseWeapon(b.dataset.compare,'matchups');
  if(b.dataset.forge)chooseWeapon(b.dataset.forge,'forge');
  if(b.id==='floor-prev'||b.id==='floor-next'){state.floor=clamp(1,100,state.floor+(b.id==='floor-next'?1:-1));renderFloor();if(state.lootFloor==='all')renderLoot();}
  if(b.id==='dialog-close')$('detail-dialog').close();
  if(b.id==='movement-next'){state.movement=Math.min(2,state.movement+1);renderMovement();}
  if(b.id==='movement-reset'){state.movement=0;renderMovement();}
 });
}
async function init(){
 try{const res=await fetch('/static/site/wiki/data.json?v=collection-2');if(!res.ok)throw new Error('Could not load wiki data');data=await res.json();model=data.model;installControls();renderFloor();renderHit();renderWeapons();renderForge();renderShield();renderMovement();renderRaid();renderLoot();bind();$('load-status').hidden=true;$('wiki-content').hidden=false;if(location.hash)document.getElementById(location.hash.slice(1))?.scrollIntoView();}
 catch(e){$('load-status').textContent='The field guide could not load. Reload this page to try again.';console.error(e);}
}
if(typeof document!=='undefined')init();
