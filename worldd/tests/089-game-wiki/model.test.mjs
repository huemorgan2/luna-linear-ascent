import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {acquisition, lootPreview, familyWeight, hitPreview, shieldPreview} from '../../static/site/wiki/wiki.mjs';
const data=JSON.parse(readFileSync(new URL('../../static/site/wiki/data.json',import.meta.url)));
const model=data.model;

test('all 64 weapon source settings have valid ranks, delivered condition and progression gates',()=>{
 for(let gi=0;gi<4;gi++)for(const w of model.weapons){
  const a=acquisition(data,w,gi);
  assert.equal(a.cfg.shopLevel,[0,2,4,6][gi]);
  assert.equal(a.shop.floor,[1,28,57,84][gi]);
  assert.equal(a.cfg.craftLevel,0);
  assert.equal(a.craft.floor,[1,26,51,76][gi]);
  assert.equal(a.craftNow,a.craftMax);
  assert(a.craftQ>0&&a.craftGold>0);
  assert(a.craft.floor<=a.shop.floor);
  assert.equal(a.cfg.dropLevel,0);
  assert.equal(a.cfg.dropDurabilityPct,[40,30,20,10][gi]);
  assert.equal(a.shopNow,a.shopMax);
  assert(a.dropNow>0&&a.dropNow<a.dropMax);
  assert(a.shopGold>=a.shop.gold);
  assert.equal(a.drop.floor,[1,26,51,76][gi]);
  assert.equal(a.findFloor,gi===3?50:1);
 }
});

test('all 3400 creature/mode/specimen outcomes have coherent rarity rolls and eligibility',()=>{
 for(const f of data.floors)for(const m of f.monsters)for(const deep of [false,true])for(const specimen of ['runt','common','tough','alpha']){
  const l=lootPreview(model,m,f.floor,deep,specimen);
  assert.equal(l.eligible,!deep||(m.deepEligible&&specimen!=='runt'));
  assert(l.material.every(p=>Number.isFinite(p)&&p>=0&&p<=95));
  assert(l.weapon.every(p=>Number.isFinite(p)&&p>=0));
  const sum=l.weapon.reduce((a,b)=>a+b,0);
  assert(sum<=50+1e-9);
  assert(Math.abs(l.none+sum-100)<1e-9);
  if(f.floor<50){assert.equal(l.material[3],0);assert.equal(l.weapon[3],0);}
  if(!l.eligible)assert.equal(sum+l.material.reduce((a,b)=>a+b,0),0);
 }
});

test('early epic discovery exists, unequal species persist, deep hunts improve high rarity',()=>{
 const f1=data.floors[0],wolf=f1.monsters[0],boar=f1.monsters[1];
 const a=lootPreview(model,wolf,1),b=lootPreview(model,boar,1);
 assert(a.weapon[2]>0&&a.weapon[2]<.0001);
 assert(b.material[0]>a.material[0]);
 for(const f of data.floors)for(const m of f.monsters.filter(m=>m.deepEligible)){
  const normal=lootPreview(model,m,f.floor),deep=lootPreview(model,m,f.floor,true);
  for(let i=1;i<4;i++){assert(deep.material[i]>=normal.material[i]);assert(deep.weapon[i]>=normal.weapon[i]);}
 }
 const air=data.floors.flatMap(f=>f.monsters).find(m=>m.proposedType.startsWith('air-'));
 const bow=model.weapons.find(w=>w.path==='Bow'),blade=model.weapons.find(w=>w.path==='Blade');
 assert.equal(familyWeight(model,bow,air),3*familyWeight(model,blade,air));
});

test('all loadouts honor air reach and counters; a bow payload meaningfully changes the result',()=>{
 for(const w of model.weapons)for(const t of model.types)for(const a of model.arrows)for(let gap=0;gap<=3;gap++){
  const r=hitPreview(w,t,a,gap);
  assert.equal(r.reach,!(w.path==='Blade'&&(t.air||gap>0)));
  assert.equal(r.damage>0,r.reach);
 }
 const w=model.weapons.find(w=>w.id==='runestring'),t=model.types.find(t=>t.id==='air-power');
 assert(hitPreview(w,t,model.arrows.find(a=>a.id==='ordinary'),2).damage>hitPreview(w,t,model.arrows.find(a=>a.id==='arcane'),2).damage);
});

test('shield allocation never grants complete protection and only absorbed damage wears it',()=>{
 for(let raw=1;raw<=300;raw++)for(const armor of [0,40,200])for(const shield of [0,80,300])for(const wall of [false,true]){
  const r=shieldPreview(raw,armor,shield,wall);
  assert(r.hp>=Math.ceil(raw*.25));
  assert.equal(r.armor+r.shield+r.hp,raw);
  assert.equal(r.wear,r.shield);
 }
});
