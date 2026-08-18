// arena3d — 067: the Labs "Arena": a PERSISTENT, turn-based 3D stage
// for floors 6–7 (feature flag on the player doc, see engine/labs.py).
//
// The engine records every fight beat as an ordered script and the card
// carries it in data-arena='{"v":1,"phase","foe","me","start","range",
// "events":[…],"log":[…],"tint"}' (combat → arena.payload → render.py).
// The card's .banner.arena slot ships bare (black, 320x300) with the
// HUD and an .afloats layer already in it; the option tiles are real
// buttons; the log lines are real text. This module ADDS the picture:
//
//   • one 320x300 stage (fight3d.createStage, same px-per-unit as the
//     kill scene, so the SAME rigs stand at the same size — only the
//     frame is taller and the scenery is the 300-row sheet);
//   • player and monster face each other in idle stances, kept alive
//     across card swaps for the same fight (the canvas is re-attached
//     into every new card of that fight);
//   • the script plays beat by beat: the player's turn (approach —
//     swing/shoot/cast — impact or MISS — back to the mark), then the
//     creature's (charge — lunge — "-XX HP" over the climber, or
//     BLOCKED, or a dodge — back to its mark). Numbers float over the
//     heads as HTML (.afloat), the HUD bars tween, the log line lands
//     under the scene as each beat resolves, and the tiles are held
//     (.arena-opts.busy + disabled) until the script has played;
//   • victory: the kill scene's banish (burst + beam, freed native pops
//     back); death: the climber falls, the frame goes dark; fled: the
//     climber walks out of frame.
//
// Degrade law: no WebGL, a missing GLB → the card is still a working
// fight (buttons, HUD, log); only the picture stays black.
//
// Isolation: fight3d.js is imported through the "fight3d" import-map
// entry — the SAME URL webplay.py loads it from — so there is ONE
// module instance (one kill observer, one asset cache). Nothing here
// touches the kill scene's state; the arena owns its own stage.
import * as THREE from "three";
import { createStage, renderFrame, ensureFor, buildPlayer, tripoMonster,
         burst, banishFx, arrowFx, magicFx, MONSTERS3D, SPECIES, STRIKES,
         PLAYER_YAW } from "fight3d";

const W = 320, H = 300;
const FLOOR_FRAC = 0.80;             // the ground fills the lower third
const BG_DIR = "backgrounds300";
const P_MARK0 = -1.05;               // the climber's mark, close range
const GAP_UNIT = 0.95;               // one "length" of open ground
const WALK = 1.5, GALLOP = 3.6;      // world units per second
const EDGE = 3.4;                    // marks never leave the frame

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const clamp = (v, a, b) => Math.min(Math.max(v, a), b);
const ease = (k) => k * k * (3 - 2 * k);

// ── the one stage ─────────────────────────────────────────────────────────
let GL = null, glBroken = false;
function stage() {
  if (GL) return GL;
  if (glBroken) return null;
  try {
    GL = createStage({ W, H, floorFrac: FLOOR_FRAC });
    GL.canvas.classList.add("a3d");
    renderFrame(GL);                    // compile the shaders now, not mid-fight
    return GL;
  } catch {
    glBroken = true;
    return null;
  }
}

// ── the live fight ────────────────────────────────────────────────────────
// F is the persistent fight: rigs on the stage, marks, and the frame-loop
// state. It survives card swaps; it is torn down when a card without
// data-arena arrives (the fight ended or the climber left).
let F = null;
let genCounter = 0;                  // bumps per mount: a stale play() exits
let raf = 0;
let effects = [];
let tweens = [];

function tween(dur, fn) {
  // per-frame fn(k) with k eased 0..1; resolves when done
  return new Promise((res) => {
    tweens.push({ t: 0, dur: Math.max(dur, 0.001), fn, res });
  });
}
function slide(group, x, speed, min = 0.15) {
  const x0 = group.position.x;
  const dur = Math.max(Math.abs(x - x0) / speed, min);
  return tween(dur, (k) => { group.position.x = x0 + (x - x0) * k; });
}

function frame() {
  raf = requestAnimationFrame(frame);
  const gl = GL;
  const dt = Math.min(gl.clock.getDelta(), 0.1);
  const t = gl.clock.elapsedTime;
  gl.postMat.uniforms.uBGFrame.value = Math.floor((t % 2.4) / 0.1) % 24;
  if (F) {
    if (F.player) F.player.update(dt, t);
    if (F.monster) F.monster.update(dt, t + 3.1);
    if (F.freed) F.freed.update(dt, t + 1.7);
  }
  const running = tweens;
  tweens = [];
  const keep = [];
  for (const tw of running) {
    tw.t += dt;
    const k = Math.min(tw.t / tw.dur, 1);
    try { tw.fn(ease(k), k); } catch (err) { console.warn(err); }
    if (k >= 1) tw.res(); else keep.push(tw);
  }
  tweens = keep.concat(tweens);
  const fx = effects;
  effects = [];
  effects = fx.filter((e) => {
    try { return e.update(dt); } catch (err) { console.warn(err); return false; }
  }).concat(effects);
  renderFrame(gl);
}
function startLoop() {
  if (raf) return;
  GL.clock.getDelta();
  frame();
}
function stopLoop() {
  if (raf) cancelAnimationFrame(raf);
  raf = 0;
}

function teardown() {
  stopLoop();
  if (F && GL) {
    if (F.player) GL.scene.remove(F.player.group);
    if (F.monster) GL.scene.remove(F.monster.group);
    if (F.freed) GL.scene.remove(F.freed.group);
  }
  for (const e of effects) { try { e.update(1e3); } catch { /* */ } }
  effects = [];
  for (const tw of tweens) { try { tw.res(); } catch { /* */ } }
  tweens = [];
  if (GL) { GL.canvas.remove(); GL.canvas.style.opacity = ""; }
  F = null;
}

// ── HTML over the canvas: floats, HUD bars, log ───────────────────────────
function screenOf(v3) {
  const p = v3.clone().project(GL.camera);
  return { x: (p.x + 1) / 2 * 100, y: (1 - p.y) / 2 * 100 };
}
function headOf(who) {
  if (!F) return new THREE.Vector3(0, 1.5, 0);
  if (who === "me" && F.player) {
    return new THREE.Vector3(F.player.group.position.x, F.pHeight + 0.25, 0);
  }
  const m = F.monster || F.freed;
  if (m) {
    const box = new THREE.Box3().setFromObject(m.group);
    return new THREE.Vector3((box.min.x + box.max.x) / 2,
                             Math.max(box.max.y, 0.6) + 0.2, 0);
  }
  return new THREE.Vector3(1.2, 1.5, 0);
}
function chestOf(who) {
  const h = headOf(who);
  h.y = Math.max(h.y * 0.62, 0.4);
  return h;
}
function floatText(who, text, cls = "") {
  const layer = F?.card?.querySelector(".afloats");
  if (!layer || !GL) return;
  const s = screenOf(headOf(who));
  const el = document.createElement("div");
  el.className = "afloat " + cls;
  el.dataset.who = who;
  el.textContent = text;
  el.style.left = clamp(s.x, 8, 92) + "%";
  el.style.top = clamp(s.y, 12, 90) + "%";
  // 067 phase 5 (roy): a second float over the same head — BLOCKED next
  // to the damage — sits BESIDE the live one, never on top of it
  const live = [...layer.querySelectorAll(`.afloat[data-who="${who}"]`)];
  layer.appendChild(el);
  if (live.length) {
    const last = live[live.length - 1];
    const dx = (+last.dataset.dx || 0) + last.offsetWidth / 2 + el.offsetWidth / 2 + 6;
    el.dataset.dx = String(dx);
    el.style.setProperty("--dx", `${dx}px`);
  }
  // 3 s travel (render.py @keyframes afloat / ajitter) + a margin
  setTimeout(() => el.remove(), 3200);
}
function setBar(which, hp) {
  const bar = F?.card?.querySelector(`.abar.${which}`);
  if (!bar || hp == null) return;
  const cap = Math.max(1, +bar.dataset.max || 1);
  const v = clamp(Math.round(hp), 0, cap);
  bar.dataset.hp = String(v);
  // 067 phase 5: the bar is the regular fight's ▓░ line (render._blocks,
  // 10 cells) — rewrite the blocks and the number, recolour the slab
  const blocks = bar.querySelector(".blocks");
  const num = bar.querySelector(".anum");
  const cells = 10, filled = Math.round(cells * v / cap);
  if (blocks) {
    blocks.textContent = "";
    blocks.append("▓".repeat(filled));
    const off = document.createElement("span");
    off.className = "off";
    off.textContent = "░".repeat(cells - filled);
    blocks.appendChild(off);
  }
  // the card's own palette (render.py OK / GOLD / RED)
  bar.style.color = v >= cap ? "#8ed24a" : (v * 3 > cap ? "#f5b825" : "#f26541");
  if (num) num.textContent = `${v}/${cap}`;
}
async function typeLine(el) {
  if (!el) return;
  const full = el.textContent;
  el.classList.remove("pending");
  el.textContent = "";
  for (let c = 3; c < full.length + 3; c += 3) {
    el.textContent = full.slice(0, Math.min(c, full.length));
    await sleep(6);
    if (!el.isConnected) return;
  }
}

// ── layout ────────────────────────────────────────────────────────────────
function initMarks(range, gap) {
  const g = range === "at_range" ? Math.max(1, gap | 0) : 0;
  F.pMark = clamp(P_MARK0 - 0.45 * g, -EDGE, EDGE);
  F.mMark = clamp(F.pMark + F.sep + GAP_UNIT * g, -EDGE, EDGE);
}

// ── beats ─────────────────────────────────────────────────────────────────
// each beat: animate, spawn floats at the right instant, tween the bar,
// then return everyone to their marks. `text` lands via reveal().
async function beatMeStrike(ev, reveal) {
  const P = F.player, M = F.monster;
  if (!P || !M) { reveal(); return; }
  const path = ev.path || F.line;
  const scene = GL.scene;
  const outcome = ev.outcome;
  const hit = outcome === "hit";
  const onImpact = () => {
    if (outcome === "miss") {
      floatText("foe", "MISS", "miss");
      // the creature slips the blow: a quick hop back and forth
      const x0 = M.group.position.x;
      tween(0.12, (k) => { M.group.position.x = x0 + 0.38 * k; })
        .then(() => tween(0.28, (k) => { M.group.position.x = x0 + 0.38 * (1 - k); }));
    } else if (hit && (ev.dmg | 0) > 0) {
      effects.push(spark(chestOf("foe"), scene, 0.9));
      floatText("foe", `-${ev.dmg} HP`);
      const s0 = M.group.scale.y, x0 = M.group.position.x;
      tween(0.3, (k) => {
        const q = Math.sin(k * Math.PI);
        M.group.scale.y = s0 * (1 - 0.18 * q);
        M.group.position.x = x0 + 0.22 * q;
      });
      if (ev.foe_hp != null) setBar("foe", ev.foe_hp);
    } else {
      // glance / blocked / 0 damage
      effects.push(spark(chestOf("foe"), scene, 0.5));
      floatText("foe", ev.blocked ? `BLOCKED ${ev.blocked}` : "0", "blocked");
      if (ev.foe_hp != null) setBar("foe", ev.foe_hp);
    }
    reveal();
  };
  const homeX = P.group.position.x;
  if (path === "blade") {
    const arcs = Object.keys(STRIKES);
    P.setStrike?.(arcs[(Math.random() * arcs.length) | 0]);
    const impactAt = 0.55, swClock = impactAt / 0.75;
    // reach: close the last hand-width so the blade lands on the body
    const reach = Math.max(0, (M.group.position.x - F.sep) - homeX - 0.05);
    let fired = false;
    await tween(impactAt + 0.45, (k, raw) => {
      const tt = raw * (impactAt + 0.45);
      P.swing?.(tt / swClock);
      const fwd = tt < impactAt ? Math.min(tt / (impactAt - 0.15), 1)
        : 1 - Math.min((tt - impactAt) / 0.35, 1);
      P.group.position.x = homeX + reach * ease(clamp(fwd, 0, 1));
      if (!fired && tt >= impactAt) { fired = true; onImpact(); }
    });
    P.swing?.(-1);
    if (!fired) onImpact();
    P.group.position.x = homeX;
    await sleep(120);
  } else if (path === "bow") {
    P.play("shoot");
    await sleep(480);
    P.release?.();
    const from = new THREE.Vector3(P.group.position.x + 0.5, 1.25, 0);
    const tgt = chestOf("foe");
    if (outcome === "miss") tgt.y += 0.9;      // the arrow sails high
    let done;
    const p = new Promise((r) => { done = r; });
    effects.push(arrowFx(from, tgt, 0.25, () => { onImpact(); done(); }, scene));
    await p;
    await sleep(320);
    P.idle();
  } else {
    const dur = P.play("cast") || 0;
    await sleep(350);
    const from = new THREE.Vector3(P.group.position.x + 0.5, 1.45, 0);
    let done;
    const p = new Promise((r) => { done = r; });
    effects.push(magicFx(from, () => chestOf("foe"), 0.8,
                         () => { onImpact(); done(); }, scene));
    await p;
    await sleep(Math.max(250, dur * 1000 - 800));
    P.idle();
  }
}

async function beatFoeStrike(ev, reveal) {
  const P = F.player, M = F.monster;
  if (!P || !M) { reveal(); return; }
  const scene = GL.scene;
  const out = ev.outcome;
  if (out === "none") { reveal(); return; }
  if (out === "netted" || out === "veiled") {
    M.setClip?.("Attack");
    await sleep(140);
    floatText("foe", out === "netted" ? "NETTED" : "VEILED", "blocked");
    reveal();
    await sleep(420);
    M.setClip?.("Idle");
    return;
  }
  // charge to contact
  const mHome = M.group.position.x;
  const contact = P.group.position.x + F.sep - 0.35;
  M.setClip?.("Gallop");
  await slide(M.group, contact, GALLOP, 0.18);
  M.setClip?.("Attack");
  const pHome = P.group.position.x;
  if (out === "dodged") {
    // the climber slips back before the jaws close
    tween(0.16, (k) => { P.group.position.x = pHome - 0.5 * k; })
      .then(() => sleep(220))
      .then(() => tween(0.3, (k) => { P.group.position.x = pHome - 0.5 * (1 - k); }));
    await sleep(150);
    floatText("me", "DODGE", "blocked");
    reveal();
    await sleep(320);
  } else {
    await sleep(140);
    const dmg = ev.dmg | 0;
    if (dmg > 0) {
      effects.push(spark(chestOf("me"), scene, 0.9));
      floatText("me", `-${dmg} HP`, "foe");
      const s0 = P.group.scale.y;
      tween(0.32, (k) => {
        const q = Math.sin(k * Math.PI);
        P.group.scale.y = s0 * (1 - 0.14 * q);
        P.group.position.x = pHome - 0.24 * q;
      });
      if (ev.blocked) setTimeout(() => floatText("me", `BLOCKED ${ev.blocked}`, "blocked"), 260);
    } else {
      effects.push(spark(chestOf("me"), scene, 0.5));
      floatText("me", `BLOCKED ${ev.blocked | 0}`, "blocked");
      tween(0.25, (k) => { P.group.position.x = pHome - 0.08 * Math.sin(k * Math.PI); });
    }
    if (ev.me_hp != null) setBar("me", ev.me_hp);
    reveal();
    if (ev.riposte) {
      await sleep(260);
      floatText("foe", `-${ev.riposte} HP`);
      effects.push(spark(chestOf("foe"), scene, 0.5));
      if (ev.foe_hp != null) setBar("foe", ev.foe_hp);
    }
    await sleep(320);
  }
  // back to the mark
  M.setClip?.("Gallop");
  await slide(M.group, mHome, GALLOP, 0.18);
  M.setClip?.("Idle");
  P.group.position.x = pHome;
}

async function beatMeMove(ev, reveal) {
  const P = F.player, M = F.monster;
  if (!P) { reveal(); return; }
  const what = ev.what;
  const g = ev.gap | 0;
  reveal();
  if (what === "open" || what === "back") {
    F.pMark = clamp(F.mMark - F.sep - GAP_UNIT * Math.max(g, 1), -EDGE, EDGE);
    F.mMark = clamp(F.pMark + F.sep + GAP_UNIT * Math.max(g, 1), -EDGE, EDGE);
    await slide(P.group, F.pMark, WALK, 0.3);
    if (M && Math.abs(M.group.position.x - F.mMark) > 0.02) {
      M.setClip?.("Gallop");
      await slide(M.group, F.mMark, GALLOP, 0.18);
      M.setClip?.("Idle");
    }
  } else if (what === "close_in") {
    F.pMark = clamp(F.mMark - F.sep, -EDGE, EDGE);
    await slide(P.group, F.pMark, WALK, 0.3);
  } else if (what === "open_fail" || what === "run_fail") {
    const x0 = P.group.position.x;
    const back = what === "run_fail" ? 0.9 : 0.5;
    await slide(P.group, x0 - back, WALK, 0.25);
    await sleep(120);
    floatText("me", what === "run_fail" ? "CUT OFF" : "NO ROOM", "blocked");
    await slide(P.group, x0, WALK * 1.4, 0.25);
  } else if (what === "run_ok") {
    await slide(P.group, -5.2, GALLOP * 0.8, 0.5);
    await fadeOut();
  } else if (what === "stand" || what === "wall") {
    floatText("me", what === "wall" ? "SHIELD WALL" : "GUARD", "blocked");
    const s0 = P.group.scale.y;
    await tween(0.4, (k) => { P.group.scale.y = s0 * (1 - 0.06 * Math.sin(k * Math.PI)); });
  } else {
    await sleep(200);
  }
}

async function beatFoeMove(ev, reveal) {
  const M = F.monster;
  if (!M) { reveal(); return; }
  const g = ev.gap | 0;
  reveal();
  if (ev.what === "close") F.mMark = clamp(F.pMark + F.sep, -EDGE, EDGE);
  else if (ev.what === "advance") {
    F.mMark = clamp(F.pMark + F.sep + GAP_UNIT * Math.max(g, 0), -EDGE, EDGE);
  } else { await sleep(250); return; }
  M.setClip?.("Gallop");
  await slide(M.group, F.mMark, GALLOP * 0.7, 0.3);
  M.setClip?.("Idle");
}

async function beatFoeDie(reveal) {
  const M = F.monster;
  if (!M) { reveal(); return; }
  const scene = GL.scene;
  const box = new THREE.Box3().setFromObject(M.group);
  const mH = Math.max(box.max.y - box.min.y, 0.2);
  const c = box.getCenter(new THREE.Vector3());
  let lastX = M.group.position.x;
  effects.push(burst(c, scene));
  effects.push(banishFx(c, mH, () => lastX, scene));
  reveal();
  const s0 = M.group.scale.clone();
  let knockV = 2.6 * 0.9 * Math.min(2, 2.2 / mH);
  await tween(0.3, (k, raw) => {
    M.group.scale.copy(s0).multiplyScalar(Math.max(1 - raw, 0.001));
    M.group.position.x += knockV * 0.016;
    knockV *= 0.9;
    lastX = M.group.position.x;
  });
  scene.remove(M.group);
  F.monster = null;
  if (F.freedMaker) {
    try {
      const fr = F.freedMaker();
      fr.group.position.set(lastX, 0, 0);
      fr.group.rotation.y += -Math.PI / 2;
      const fs = fr.group.scale.clone();
      fr.group.scale.multiplyScalar(0.001);
      scene.add(fr.group);
      F.freed = fr;
      await tween(0.25, (k) => { fr.group.scale.copy(fs).multiplyScalar(Math.max(k, 0.001)); });
    } catch (err) { console.warn(err); }
  }
  await sleep(600);
}

async function beatMeDie(reveal) {
  const P = F.player;
  reveal();
  if (P) {
    const y0 = P.group.position.y;
    await tween(0.7, (k) => {
      P.group.rotation.z = -1.35 * k;
      P.group.position.y = y0 + 0.15 * Math.sin(k * Math.PI) - 0.1 * k;
    });
  }
  await sleep(500);
  await fadeOut(0.3);
}

function fadeOut(to = 0.25) {
  return tween(0.9, (k) => { if (GL) GL.canvas.style.opacity = String(1 - (1 - to) * k); });
}

// a small hit spark — the kill burst is for the kill
function spark(center, scene, size = 1) {
  const n = 22;
  const posA = new Float32Array(n * 3);
  const vel = [];
  for (let i = 0; i < n; i++) {
    const a = Math.random() * Math.PI * 2;
    const sp = (0.8 + Math.random() * 2.2) * size;
    vel.push(new THREE.Vector3(Math.cos(a) * sp, Math.sin(a) * sp * 0.8 + 0.8, 0));
    posA.set([center.x, center.y, center.z], i * 3);
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.BufferAttribute(posA, 3));
  const pts = new THREE.Points(geo, new THREE.PointsMaterial(
    { color: 0xffffff, size: 3, sizeAttenuation: false }));
  pts.frustumCulled = false;
  const flash = new THREE.Mesh(new THREE.CircleGeometry(0.22 * size, 12),
    new THREE.MeshBasicMaterial({ color: 0xffffff }));
  flash.position.copy(center);
  scene.add(pts, flash);
  let life = 0;
  return { update(dt) {
    life += dt;
    flash.visible = life < 0.1;
    for (let i = 0; i < n; i++) {
      vel[i].y -= 5 * dt;
      posA[i * 3] += vel[i].x * dt;
      posA[i * 3 + 1] += vel[i].y * dt;
    }
    geo.attributes.position.needsUpdate = true;
    if (life > 0.45) { scene.remove(pts, flash); return false; }
    return true;
  } };
}

// ── the script ────────────────────────────────────────────────────────────
async function play(card, spec) {
  const events = Array.isArray(spec.events) ? spec.events : [];
  const lines = [...card.querySelectorAll(".alog .aline")];
  lines.forEach((l) => l.classList.add("pending"));
  const opts = card.querySelector(".arena-opts");
  const tiles = [...card.querySelectorAll(".arena-opts button.opt")];
  const hold = events.length > 0;
  if (hold && opts) {
    opts.classList.add("busy");
    tiles.forEach((b) => { b.disabled = true; });
  }
  const release = () => {
    if (!card.isConnected) return;
    opts?.classList.remove("busy");
    tiles.forEach((b) => { b.disabled = false; });
    lines.forEach((l) => l.classList.remove("pending"));
  };
  // the bars start where the round started and walk forward with the beats
  if (spec.start) {
    setBar("me", spec.start.me_hp);
    setBar("foe", spec.start.foe_hp);
  }
  let li = 0;
  const gen = F.gen;
  try {
    for (const ev of events) {
      if (!card.isConnected || !F || F.gen !== gen) return;
      const line = ev.text ? lines[li++] : null;
      let revealed = false;
      const reveal = () => {
        if (revealed) return;
        revealed = true;
        if (line) typeLine(line);
      };
      // a strike with a weapon the climber is not holding on the stage
      // (a side-arm promoted this round): re-arm before the swing
      if (ev.who === "me" && ev.kind === "strike" && ev.path && ev.path !== F.line) {
        await rearm(ev.path);
      }
      if (ev.kind === "strike" && ev.who === "me") await beatMeStrike(ev, reveal);
      else if (ev.kind === "strike") await beatFoeStrike(ev, reveal);
      else if (ev.kind === "move" && ev.who === "me") await beatMeMove(ev, reveal);
      else if (ev.kind === "move") await beatFoeMove(ev, reveal);
      else if (ev.kind === "die" && ev.who === "foe") await beatFoeDie(reveal);
      else if (ev.kind === "die") await beatMeDie(reveal);
      else { reveal(); await sleep(250); }
      reveal();
      // everyone back on their marks between turns
      if (F && F.player && F.gen === gen && ev.kind !== "die"
          && !(ev.kind === "move" && ev.what === "run_ok")) {
        F.player.group.position.x = F.pMark;
        F.player.group.scale.y = 1;
        if (F.monster) F.monster.group.position.x = F.mMark;
      }
      await sleep(160);
    }
    // the card's final numbers are the truth
    if (spec.me) setBar("me", spec.me.hp);
    if (spec.foe) setBar("foe", spec.foe.hp);
  } finally {
    release();
  }
}

async function rearm(line) {
  if (!F || !GL) return;
  const got = await ensureFor({ id: F.foeId, race: F.race, line }, { bgDir: BG_DIR });
  if (!got || !F) return;
  const x = F.player ? F.player.group.position.x : F.pMark;
  if (F.player) GL.scene.remove(F.player.group);
  F.player = buildPlayer(got.race, got.line);
  F.player.group.position.set(x, 0, 0);
  F.player.group.rotation.y = PLAYER_YAW;
  GL.scene.add(F.player.group);
  F.line = got.line;
}

// ── mount ─────────────────────────────────────────────────────────────────
function inkFor(tint) {
  const ink = new THREE.Color(0xdfe4ee);
  try {
    ink.set(tint || "#dfe4ee");
    const hsl = { h: 0, s: 0, l: 0 };
    ink.getHSL(hsl);
    if (hsl.l < 0.55) ink.setHSL(hsl.h, hsl.s, 0.55);
  } catch { /* bad hex: readable default */ }
  return ink;
}

async function build(card, spec) {
  // a NEW fight (or the first live card of one): rigs on the stage
  const foe = spec.foe || {}, me = spec.me || {};
  const reg = MONSTERS3D[foe.id];
  if (!reg) return false;
  const got = await ensureFor({ id: foe.id, race: me.race, line: me.line },
                              { bgDir: BG_DIR });
  if (!got || !card.isConnected) return false;
  const gl = stage();
  if (!gl) return false;
  teardown();
  gl.postMat.uniforms.uInk.value.copy(inkFor(spec.tint));
  gl.postMat.uniforms.tBG.value = got.bg || gl.postMat.uniforms.tBayer.value;
  gl.postMat.uniforms.uBGOn.value = got.bg ? 1 : 0;
  F = { key: fightKey(spec), gen: 0, card, foeId: foe.id, race: got.race,
        line: got.line, player: null, monster: null, freed: null,
        pHeight: (SPECIES[got.race] || SPECIES.human).h, sep: 1.4,
        pMark: P_MARK0, mMark: P_MARK0 + 1.4, freedMaker: null };
  try {
    F.player = buildPlayer(got.race, got.line);
    F.player.group.rotation.y = PLAYER_YAW;
    gl.scene.add(F.player.group);
    F.monster = tripoMonster(got.mg, reg);
    F.monster.group.rotation.y += -Math.PI / 2;
    gl.scene.add(F.monster.group);
    F.monster.group.position.set(0, 0, 0);
    F.monster.group.updateMatrixWorld(true);
    const mBox = new THREE.Box3().setFromObject(F.monster.group);
    const noseOff = 0 - mBox.min.x;
    F.sep = clamp(noseOff + 0.7, 0.9, 2.1);
    F.freedMaker = foe.breed === "native"
      ? () => tripoMonster(got.mg, { h: reg.h * 0.45, wide: reg.wide,
                                     yaw: reg.yaw, gait: reg.gait, freed: true })
      : null;
  } catch (err) {
    console.warn(err);
    teardown();
    return false;
  }
  const st = spec.start || {};
  initMarks(st.range || (spec.range || {}).state, st.gap ?? (spec.range || {}).gap);
  F.player.group.position.set(F.pMark, 0, 0);
  F.monster.group.position.set(F.mMark, 0, 0);
  return true;
}

function fightKey(spec) {
  const foe = spec.foe || {}, me = spec.me || {};
  return `${foe.id}|${me.race}`;
}

function attach(card) {
  const slot = card.querySelector(".banner.arena[data-a3d-slot]");
  if (!slot || !GL) return false;
  slot.style.position = "relative";
  slot.style.backgroundColor = "#000";
  if (GL.canvas.parentNode !== slot) slot.insertBefore(GL.canvas, slot.firstChild);
  return true;
}

async function mountArena(card) {
  card.setAttribute("data-a3d-done", "1");
  let spec;
  try { spec = JSON.parse(card.dataset.arena); } catch { return; }
  if (!spec || !spec.foe) return;
  if (spec.phase === "opener") {
    // the close-up shows; warm the rigs, the sheet and the shaders so
    // the first strike lands on a ready stage
    ensureFor({ id: spec.foe.id, race: (spec.me || {}).race,
                line: (spec.me || {}).line }, { bgDir: BG_DIR })
      .then(() => stage());
    return;
  }
  // hold the tiles from the moment the card lands — build() may await
  // rigs and sheets; a click in that gap would double-act. Whatever
  // happens next (dead GL, a swapped card, a broken rig) the finally
  // hands the tiles back and shows the log in full.
  holdTiles(card, (spec.events || []).length > 0);
  try {
    const same = F && !F.ended && F.key === fightKey(spec) && F.player;
    if (!same) {
      const ok = await build(card, spec);
      if (!ok || !card.isConnected) return;
    } else {
      F.card = card;
      if (F.line !== (spec.me || {}).line && (spec.me || {}).line) {
        await rearm(spec.me.line);
      }
    }
    if (!F || !card.isConnected) return;
    F.card = card;
    F.gen = ++genCounter;
    if (!attach(card)) return;
    GL.canvas.style.opacity = "";
    startLoop();
    // one rendered frame first, then the beats
    await new Promise((r) => requestAnimationFrame(() => setTimeout(r, 120)));
    if (!card.isConnected || !F) return;
    await play(card, spec);
    if (spec.phase === "victory" || spec.phase === "death" || spec.phase === "fled") {
      // the fight is over — the next card tears the stage down
      F.ended = true;
    }
  } finally {
    releaseTiles(card);
  }
}

function holdTiles(card, on) {
  const opts = card.querySelector(".arena-opts");
  if (!on || !opts) return;
  opts.classList.add("busy");
  card.querySelectorAll(".arena-opts button.opt").forEach((b) => { b.disabled = true; });
}

function releaseTiles(card) {
  if (!card.isConnected) return;
  card.querySelector(".arena-opts")?.classList.remove("busy");
  card.querySelectorAll(".arena-opts button.opt").forEach((b) => { b.disabled = false; });
  card.querySelectorAll(".alog .aline.pending").forEach((l) => l.classList.remove("pending"));
}

const game = document.getElementById("game");
if (game) {
  const scan = () => {
    const card = game.querySelector(".card[data-arena]:not([data-a3d-done])");
    if (card) { mountArena(card); return; }
    if (!game.querySelector(".card[data-arena]") && F) teardown();
    else if (!game.querySelector(".card[data-arena]")) stopLoop();
  };
  new MutationObserver(scan).observe(game, { childList: true, subtree: true });
  scan();
}
