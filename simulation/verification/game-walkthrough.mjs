// Real browser walkthrough of the local actual-engine explorer.
import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
const {chromium}=await import(pathToFileURL(process.env.PLAYWRIGHT_PATH).href);
const out=path.resolve('simulation/verification/003');await fs.mkdir(out,{recursive:true});
const base=process.env.SIMULATION_URL||'http://127.0.0.1:8766';
const browser=await chromium.launch({headless:true});const page=await browser.newPage({viewport:{width:1440,height:1050},deviceScaleFactor:1});
const notes={date:new Date().toISOString(),steps:[],screenshots:[]};const errors=[];page.on('pageerror',e=>errors.push(e.message));
let inspector=null;page.on('response',async r=>{if(r.url().endsWith('/api/game/inspect')&&r.ok())inspector=await r.json();});
const record=(name,data)=>notes.steps.push({name,data});
const shot=async(name,loc)=>{await (loc||page).screenshot({path:path.join(out,name+'.png')});notes.screenshots.push(name+'.png');};
async function gameAction(id){const response=page.waitForResponse(r=>r.url().endsWith('/api/game/inspect')&&r.ok());await page.locator(`[data-game-action="${id}"]`).click();const r=await response;inspector=await r.json();await page.waitForFunction(hash=>document.querySelector('#inspect-state').textContent.includes(hash.slice(0,16)),inspector.state_sha256);record(id,{headline:inspector.receipt.headline,meters:inspector.scene.meters,events:inspector.events,rng:inspector.rng_counter});}
try{
 await page.goto(base);await page.waitForFunction(()=>document.querySelector('#engine-version').textContent.includes('Imported game'));await page.evaluate(()=>document.fonts.ready);
 record('Actual source',await page.locator('#source-panel').innerText());await shot('01-engine-dashboard');
 await page.locator('#inspect-start').click();await page.locator('[data-game-action="gate"]').waitFor();
 await gameAction('gate');await gameAction('floor_1');if(await page.locator('[data-game-action="skip"]').count())await gameAction('skip');
 const before=inspector.scene.meters.energy;await gameAction('hunt');
 if(inspector.scene.meters.energy!==before-1)throw Error('Actual ordinary hunt did not spend one energy');
 await page.locator('.engine-enemy img').waitFor();await page.waitForFunction(()=>document.querySelector('.engine-enemy img').complete&&document.querySelector('.engine-enemy img').naturalWidth>0);
 await shot('02-actual-monster',page.locator('#inspector'));
 for(let turn=0;turn<60&&inspector.scene.enemy;turn++){
  if(await page.locator('[data-game-action="close_in"]:not(:disabled)').count())await gameAction('close_in');
  else if(await page.locator('[data-game-action="attack"]:not(:disabled)').count())await gameAction('attack');
  else await gameAction('run');
 }
 if(inspector.scene.enemy)throw Error('Fight did not resolve in 60 actions');
 record('Fight verdict',inspector.receipt);await shot('03-engine-verdict',page.locator('#inspector'));
 // Show the real clock: a wait makes the engine calculate recovery.
 const wait=page.waitForResponse(r=>r.url().endsWith('/api/game/inspect')&&r.ok());await page.locator('[data-game-wait="2700"]').click();await wait;
 // Start a tiny actual-engine run through the visible form.
 await page.locator('[name="players"]').fill('2');await page.locator('[name="days"]').fill('1');await page.locator('[name="minutes_per_day"]').fill('1');await page.locator('[name="max_floor"]').fill('10');
 const previousDownload=await page.locator('#game-download').getAttribute('href');
 const posted=page.waitForResponse(r=>r.url().endsWith('/api/game/runs')&&r.request().method()==='POST');await page.locator('#game-run').click();const initial=await (await posted).json();record('Start engine run',initial);
 await page.waitForFunction(old=>document.querySelector('#game-status').textContent.startsWith('Saved in')&&document.querySelector('#game-download').getAttribute('href')!==old,previousDownload,{timeout:60000});
 const status=await (await page.request.get(base+'/api/status')).json();await page.waitForFunction(id=>document.querySelector('#game-download').href.includes(id),status.run_id);
 const run=await (await page.request.get(base+'/api/game/runs/'+status.run_id)).json();
 if(run.backend!=='actual-game-engine')throw Error('Wrong backend');record('Saved engine run',{id:run.run_id,source:run.engine_source.sha256,workers:run.execution.workers});
 await page.locator('#game-floor').fill('10');const text=await page.locator('#game-floor-detail').innerText();record('Unreached floor and warden boundary',text);
 if(!text.includes('0 / 2 ready')||!text.includes('Not reached')||!text.includes('Not measured'))throw Error('Unavailable results mislabeled');
 await page.locator('#game-focus').click();await shot('04-actual-charts',page.locator('.chart-grid'));
 await page.locator('#game-replay').click();await page.waitForFunction(()=>document.querySelector('#game-replay-status').textContent.startsWith('MATCH:'),{},{timeout:60000});record('Full-state replay',await page.locator('#game-replay-status').innerText());
 const [download]=await Promise.all([page.waitForEvent('download'),page.locator('#game-download').click()]);const saved=JSON.parse(await fs.readFile(await download.path(),'utf8'));if(saved.deterministic_sha256!==run.deterministic_sha256)throw Error('Downloaded run mismatch');
 await page.locator('#game-compare').selectOption(run.run_id);await page.locator('#game-comparison').waitFor({state:'visible'});record('Same source comparison',await page.locator('#game-comparison').innerText());
 await page.setViewportSize({width:390,height:844});await page.evaluate(()=>scrollTo(0,0));await shot('05-mobile-source');
 await page.locator('#game-days-chart').scrollIntoViewIfNeeded();await page.waitForFunction(()=>Math.abs(document.querySelector('#game-days-chart svg').viewBox.baseVal.width-document.querySelector('#game-days-chart').clientWidth)<1);await shot('06-mobile-chart');
 const overflow=await page.evaluate(()=>({width:innerWidth,body:document.documentElement.scrollWidth,font:getComputedStyle(document.body).fontFamily}));record('Mobile geometry',overflow);if(overflow.body>overflow.width+1){record('Overflowing elements',await page.evaluate(()=>[...document.querySelectorAll('*')].filter(e=>e.getBoundingClientRect().right>innerWidth+.5).map(e=>({id:e.id,tag:e.tagName,right:e.getBoundingClientRect().right,text:e.textContent.slice(0,100)}))));throw Error('Horizontal overflow');}
 await page.goto(base+'/proposal');await page.locator('#model-disclosure').waitFor();record('Historical model disclosure',await page.locator('#model-disclosure').innerText());
 if(errors.length)throw Error(errors.join('; '));notes.status='PASS';
}catch(e){notes.status='FAIL';notes.error=e.stack;await shot('failure');process.exitCode=1;}finally{notes.errors=errors;await fs.writeFile(path.join(out,'browser-observations.json'),JSON.stringify(notes,null,2));await browser.close();}
console.log(JSON.stringify({status:notes.status,error:notes.error,steps:notes.steps.length,screenshots:notes.screenshots}));
