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
const user = 'Routes85'+Date.now().toString().slice(-7);
const browser = await chromium.launch({headless:true});
const context = await browser.newContext();
const response = await context.request.post(base+'/signup',{data:{username:user,password:'geometry-test-only',password2:'geometry-test-only'}});
if (!response.ok()) throw Error('signup failed: '+response.status());
const page = await context.newPage();
const errors=[];page.on('pageerror',e=>errors.push(e.message));
const all=[];
for (let floor=1;floor<=10;floor++) {
 for (const opt of ['talk','keep','gate']) {
  const seed = spawnSync(path.join(root,'luna/.venv/bin/python'),[path.join(root,'luna/dojo/tests/labs-arena/seed.py'),user,String(floor),'warrior'],{encoding:'utf8',env:{...process.env,ASCENT_GAME_PATH:path.join(root,'plugin-linear-ascent'),SEED_LEVEL:'99'}});
  if(seed.status!==0) throw Error(seed.stderr);
  await page.setViewportSize({width:760,height:1000});
  await page.goto(base+'/play');
  const button=page.locator(`button.mk[data-opt="${opt}"]`);
  await button.waitFor({state:'visible'});
  const [reply] = await Promise.all([page.waitForResponse(r=>r.url().endsWith('/act')),button.click()]);
  const card=await reply.json();
  await page.waitForFunction(()=>!document.querySelector('.mapwrap'));
  const content=await page.locator('#game').innerText();
  const result={floor,opt,status:reply.status(),headline:card.headline,hasMap:await page.locator('.mapwrap').count(),content:content.slice(0,4000)};
  all.push(result);
  await page.screenshot({path:path.join(out,`route-${floor}-${opt}.png`)});
  console.log(JSON.stringify(result));
  fs.writeFileSync(path.join(out,'routes.json'),JSON.stringify({account:user,all,errors},null,2));
 }
}
await browser.close();
