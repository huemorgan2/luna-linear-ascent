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
const user = 'Lift85'+Date.now().toString().slice(-7);
const browser = await chromium.launch({headless:true});
const context = await browser.newContext();
const response = await context.request.post(base+'/signup',{data:{username:user,password:'geometry-test-only',password2:'geometry-test-only'}});
if (!response.ok()) throw Error('signup failed: '+response.status());
const page = await context.newPage();
const errors=[];page.on('pageerror',e=>errors.push(e.message));
const all=[];
const seed = spawnSync(path.join(root,'luna/.venv/bin/python'),[path.join(root,'luna/dojo/tests/labs-arena/seed.py'),user,'2','warrior'],{encoding:'utf8',env:{...process.env,ASCENT_GAME_PATH:path.join(root,'plugin-linear-ascent'),SEED_LEVEL:'99'}});
if(seed.status!==0)throw Error(seed.stderr);
await page.setViewportSize({width:760,height:1000});
await page.goto(base+'/play');
await page.locator('.mapwrap').waitFor();
await page.evaluate(()=>{
 window.liftSamples=[];
 const sample=(lay,phase)=>{const s=getComputedStyle(lay),r=lay.getBoundingClientRect();window.liftSamples.push({phase,at:performance.now(),direction:lay.getAttribute('aria-label'),background:s.backgroundColor,opacity:s.opacity,pointerEvents:s.pointerEvents,inert:document.getElementById('game').inert,rect:[r.x,r.y,r.width,r.height],viewport:[innerWidth,innerHeight]});};
 new MutationObserver(records=>{
  for(const record of records)for(const n of record.addedNodes){
   if(n.id==='liftlay'){sample(n,'mount');requestAnimationFrame(()=>{sample(n,'first-animation-frame');requestAnimationFrame(()=>sample(n,'second-animation-frame'));});}
  }
 }).observe(document.body,{childList:true});
});
await page.locator('button.mk[data-opt="town"]').click();
await page.locator('#liftlay').waitFor();
await page.keyboard.press('1');
await page.screenshot({path:path.join(out,'lift-down.png')});
await page.locator('#liftlay').waitFor({state:'detached'});
await page.locator('button.opt[data-opt="gate"]').click();
await page.locator('button.opt[data-opt="floor_2"]').click();
await page.locator('#liftlay').waitFor();
await page.keyboard.press('1');
await page.screenshot({path:path.join(out,'lift-up.png')});
await page.locator('#liftlay').waitFor({state:'detached'});
const result=await page.evaluate(()=>({samples:window.liftSamples,inertAfter:document.getElementById('game').inert,overlays:document.querySelectorAll('#liftlay').length}));
fs.writeFileSync(path.join(out,'lift-frames.json'),JSON.stringify(result,null,2));
console.log(JSON.stringify(result));
await browser.close();
