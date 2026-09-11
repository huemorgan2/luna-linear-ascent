// Supplement to the human-judged CUA walkthrough: live web DOM at three widths.
// Explicitly requires a disposable local DB and creates its own QA account.
import { createRequire } from 'node:module';
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
const root = process.cwd();
const { chromium } = createRequire(path.join(root,'luna/dojo/package.json'))('playwright');
const out = path.join(root,'dojo/results/0062-085-floor-maps-standard-2026-09-09/geometry');
fs.mkdirSync(out,{recursive:true});
const base = 'http://127.0.0.1:8600';
if (!process.env.DATABASE_URL?.includes('127.0.0.1:55440/ascent_maps_browser')) throw Error('requires isolated browser DB');
const user = 'Geometry85'+Date.now().toString().slice(-7);
const browser = await chromium.launch({headless:true});
const context = await browser.newContext();
const response = await context.request.post(base+'/signup',{data:{username:user,password:'geometry-test-only',password2:'geometry-test-only'}});
if (!response.ok()) throw Error('signup failed: '+response.status());
const page = await context.newPage();
const errors=[];page.on('pageerror',e=>errors.push(e.message));
const all=[];
for (let floor=1;floor<=10;floor++) {
 const seed = spawnSync(path.join(root,'luna/.venv/bin/python'),[path.join(root,'luna/dojo/tests/labs-arena/seed.py'),user,String(floor),'warrior'],{encoding:'utf8',env:{...process.env,ASCENT_GAME_PATH:path.join(root,'plugin-linear-ascent'),SEED_LEVEL:'99'}});
 if(seed.status!==0) throw Error(seed.stderr);
 for (const width of [760,390,320]) {
  await page.setViewportSize({width,height:1000});
  await page.goto(base+'/play');
  await page.waitForFunction(()=>document.querySelector('.mapwrap img')?.complete && getComputedStyle(document.querySelector('.mapwrap')).opacity==='1');
  await page.screenshot({path:path.join(out,`floor-${floor}-${width}.png`)});
  const state = await page.evaluate(()=>{
   const rect=e=>{const r=e.getBoundingClientRect();return {x:r.x,y:r.y,w:r.width,h:r.height,right:r.right,bottom:r.bottom}};
   const chips=[...document.querySelectorAll('button.mk')].map(b=>({opt:b.dataset.opt,...rect(b)}));
   return {scrollWidth:document.documentElement.scrollWidth,viewport:innerWidth,chips,src:document.querySelector('.mapwrap img').src,overlaps:chips.flatMap((a,i)=>chips.slice(i+1).filter(b=>Math.min(a.right,b.right)>Math.max(a.x,b.x)+.5&&Math.min(a.bottom,b.bottom)>Math.max(a.y,b.y)+.5).map(b=>[a.opt,b.opt]))};
  });
  state.floor=floor;state.width=width;state.tips=[];
  for (const chip of state.chips) {
   await page.locator(`button.mk[data-opt="${chip.opt}"]`).hover();
   state.tips.push(await page.locator(`button.mk[data-opt="${chip.opt}"] .mtip`).evaluate(t=>{const r=t.getBoundingClientRect();return {opt:t.parentElement.dataset.opt,x:r.x,y:r.y,right:r.right,bottom:r.bottom,display:getComputedStyle(t).display,delay:getComputedStyle(t).transitionDelay}}));
  }
  all.push(state);fs.writeFileSync(path.join(out,'geometry.json'),JSON.stringify({account:user,all,errors},null,2));
  console.log(JSON.stringify({floor,width,overlaps:state.overlaps,overflow:state.scrollWidth>width,clippedTips:state.tips.filter(t=>t.x<0||t.right>width||t.y<0||t.bottom>1000)}));
 }
}
await browser.close();
