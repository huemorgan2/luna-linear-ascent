// base-mock v4 — walled town, wider spacing, braziers on the wall corners,
// stairs visible beyond the gate, boars + a wolf prowling outside.
// Sunlit, shadow maps, black ink outlines + Bayer dither at 640×400.
// HUD sits above the canvas, [1] [2] options below — like the chat cards.
import * as THREE from "three";
import { GLTFLoader } from "./vendor/GLTFLoader.js";
import * as SkeletonUtils from "./vendor/SkeletonUtils.js";

const W = 640, H = 400;
const INK = "#e6e9f2", BG = "#0b0e14";

// ── renderer + post targets ────────────────────────────────────────────────
const canvas = document.getElementById("game");
const renderer = new THREE.WebGLRenderer({ canvas, antialias: false });
renderer.setPixelRatio(1);
renderer.setSize(W, H, false);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFShadowMap;

const depthTex = new THREE.DepthTexture(W, H);
const rtColor = new THREE.WebGLRenderTarget(W, H, {
  minFilter: THREE.NearestFilter, magFilter: THREE.NearestFilter,
  depthTexture: depthTex,
});
const rtNormal = new THREE.WebGLRenderTarget(W, H, {
  minFilter: THREE.NearestFilter, magFilter: THREE.NearestFilter,
});
const normalMat = new THREE.MeshNormalMaterial();

const BAYER8 = [
  0, 32, 8, 40, 2, 34, 10, 42, 48, 16, 56, 24, 50, 18, 58, 26,
  12, 44, 4, 36, 14, 46, 6, 38, 60, 28, 52, 20, 62, 30, 54, 22,
  3, 35, 11, 43, 1, 33, 9, 41, 51, 19, 59, 27, 49, 17, 57, 25,
  15, 47, 7, 39, 13, 45, 5, 37, 63, 31, 55, 23, 61, 29, 53, 21,
];
const bayerData = new Uint8Array(64);
for (let i = 0; i < 64; i++) bayerData[i] = BAYER8[i] * 4;
const bayerTex = new THREE.DataTexture(bayerData, 8, 8, THREE.RedFormat);
bayerTex.minFilter = bayerTex.magFilter = THREE.NearestFilter;
bayerTex.wrapS = bayerTex.wrapT = THREE.RepeatWrapping;
bayerTex.needsUpdate = true;

const postScene = new THREE.Scene();
const postCam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
postScene.add(new THREE.Mesh(
  new THREE.PlaneGeometry(2, 2),
  new THREE.ShaderMaterial({
    uniforms: {
      tScene: { value: rtColor.texture },
      tNormal: { value: rtNormal.texture },
      tDepth: { value: depthTex },
      tBayer: { value: bayerTex },
      texel: { value: new THREE.Vector2(1 / W, 1 / H) },
      inkColor: { value: new THREE.Color(INK) },
      bgColor: { value: new THREE.Color(BG) },
    },
    vertexShader: `
      varying vec2 vUv;
      void main(){ vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }`,
    fragmentShader: `
      uniform sampler2D tScene, tNormal, tDepth, tBayer;
      uniform vec2 texel;
      uniform vec3 inkColor, bgColor;
      varying vec2 vUv;
      void main(){
        float d0 = texture2D(tDepth, vUv).x;
        float dx = abs(texture2D(tDepth, vUv + vec2(texel.x, 0.0)).x - d0)
                 + abs(texture2D(tDepth, vUv - vec2(texel.x, 0.0)).x - d0);
        float dy = abs(texture2D(tDepth, vUv + vec2(0.0, texel.y)).x - d0)
                 + abs(texture2D(tDepth, vUv - vec2(0.0, texel.y)).x - d0);
        float depthEdge = step(0.0045, dx + dy);
        vec3 n0 = texture2D(tNormal, vUv).xyz;
        vec3 nx = texture2D(tNormal, vUv + vec2(texel.x, 0.0)).xyz;
        vec3 ny = texture2D(tNormal, vUv + vec2(0.0, texel.y)).xyz;
        float normalEdge = step(0.85, length(n0 - nx) + length(n0 - ny));
        float edge = max(depthEdge, normalEdge);

        vec3 c = texture2D(tScene, vUv).rgb;
        float lum = max(c.r, max(c.g, c.b));
        lum = pow(clamp(lum * 1.18, 0.0, 1.0), 0.95);
        float t = texture2D(tBayer, gl_FragCoord.xy / 8.0).r + 0.002;
        float on = step(t, lum) * (1.0 - edge);   // edges force black
        gl_FragColor = vec4(mix(bgColor, inkColor, on), 1.0);
      }`,
  })));

function fit() {
  let s = Math.min((window.innerWidth - 2) / W,
                   (window.innerHeight - 190) / H);
  s = s >= 1 ? Math.floor(s) : Math.max(0.45, s);
  canvas.style.width = Math.round(W * s) + "px";
  canvas.style.height = Math.round(H * s) + "px";
}
window.addEventListener("resize", fit); fit();

// ── scene, camera, sun ─────────────────────────────────────────────────────
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x000000);

const camera = new THREE.OrthographicCamera(0, 0, 0, 0, 0.1, 120);
const VIEW_H = 16;
camera.left = -VIEW_H * (W / H) / 2; camera.right = VIEW_H * (W / H) / 2;
camera.top = VIEW_H / 2; camera.bottom = -VIEW_H / 2;
camera.updateProjectionMatrix();
const CAM_OFF = new THREE.Vector3(0, 16, 11);

scene.add(new THREE.AmbientLight(0xffffff, 0.72));
const sun = new THREE.DirectionalLight(0xffffff, 1.5);
sun.position.set(-9, 32, 9);
sun.castShadow = true;
sun.shadow.mapSize.set(2048, 2048);
sun.shadow.camera.left = -30; sun.shadow.camera.right = 30;
sun.shadow.camera.top = 32; sun.shadow.camera.bottom = -32;
sun.shadow.camera.near = 2; sun.shadow.camera.far = 80;
sun.shadow.bias = -0.0015;
scene.add(sun);
const fill = new THREE.DirectionalLight(0xffffff, 0.5);
fill.position.set(6, 12, 20);
scene.add(fill);

// town geometry: walls at ±13.5 / z -19.5..14.5, gate north, square z<-10
const WALL_X = 15, WALL_ZN = -19.5, WALL_ZS = 19.5;
const BOUND = { x0: -14.2, x1: 14.2, z0: -18.6, z1: 18.7 };
const FOUNTAIN = { x: 0, z: -14.5 };

function groundTexture() {
  const c = document.createElement("canvas"); c.width = 512; c.height = 384;
  const g = c.getContext("2d");
  const px = (x) => (x + 32) * 8, py = (z) => (z + 24) * 8;
  g.fillStyle = "#181b23"; g.fillRect(0, 0, 512, 384);
  // interior
  g.fillStyle = "#565c6b";
  g.fillRect(px(-WALL_X), py(WALL_ZN), WALL_X * 2 * 8, (WALL_ZS - WALL_ZN) * 8);
  // avenue
  const av = g.createLinearGradient(px(-3.4), 0, px(3.4), 0);
  av.addColorStop(0, "#6f7585"); av.addColorStop(0.5, "#9aa0ae");
  av.addColorStop(1, "#6f7585");
  g.fillStyle = av;
  g.fillRect(px(-3.4), py(-10), 6.8 * 8, (WALL_ZS - (-10)) * 8);
  // the square, radial around the fountain
  const sq = g.createRadialGradient(px(FOUNTAIN.x), py(FOUNTAIN.z), 8,
                                    px(FOUNTAIN.x), py(FOUNTAIN.z), 92);
  sq.addColorStop(0, "#b8bdc9"); sq.addColorStop(0.55, "#8a90a0");
  sq.addColorStop(1, "#565c6b");
  g.fillStyle = sq;
  g.fillRect(px(-11), py(WALL_ZN), 22 * 8, (WALL_ZN * -1 - 10) * 8);
  // chasm outside the gate (the stairs read against it)
  g.fillStyle = "#0a0c12";
  g.fillRect(px(-3.0), py(-26.5), 6.0 * 8, 7.2 * 8);
  // wheel ruts
  g.strokeStyle = "#5e6473"; g.lineWidth = 3;
  for (const rx of [-1.3, 1.3]) {
    g.beginPath(); g.moveTo(px(rx), py(19));
    g.quadraticCurveTo(px(rx + 0.2), py(2), px(rx), py(-9)); g.stroke();
  }
  for (let i = 0; i < 2400; i++) {
    g.fillStyle = Math.random() < 0.5 ? "rgba(255,255,255,0.05)"
                                      : "rgba(0,0,0,0.10)";
    g.fillRect(Math.random() * 512, Math.random() * 384, 2, 2);
  }
  const t = new THREE.CanvasTexture(c);
  t.magFilter = t.minFilter = THREE.NearestFilter;
  return t;
}
const ground = new THREE.Mesh(
  new THREE.PlaneGeometry(64, 48),
  new THREE.MeshLambertMaterial({ map: groundTexture() }));
ground.rotateX(-Math.PI / 2);
ground.receiveShadow = true;
scene.add(ground);

// lamps along the avenue + square
const lampLights = [];
function lamp(x, z) {
  const m = new THREE.MeshLambertMaterial({ color: 0x666e80 });
  const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.09, 2.6), m);
  pole.position.set(x, 1.3, z); pole.castShadow = true; scene.add(pole);
  const head = new THREE.Mesh(new THREE.SphereGeometry(0.16),
    new THREE.MeshLambertMaterial({ color: 0xffffff, emissive: 0xffffff, emissiveIntensity: 1.2 }));
  head.position.set(x, 2.65, z); scene.add(head);
  const l = new THREE.PointLight(0xffffff, 4, 8, 1.7);
  l.position.set(x, 2.6, z); scene.add(l);
  lampLights.push(l);
}
lamp(-3.2, 16); lamp(3.2, 11); lamp(-3.2, 4.5); lamp(3.2, -2);
lamp(-3.2, -8);
lamp(-4.8, -14.5); lamp(4.8, -14.5);

// braziers — open fires with the shimmering glow pools
const fires = [];
function brazier(x, z, y = 0) {
  const metal = new THREE.MeshLambertMaterial({ color: 0x6a7080 });
  const base = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.2, 1.0, 6), metal);
  base.position.set(x, y + 0.5, z); base.castShadow = true; scene.add(base);
  const bowl = new THREE.Mesh(new THREE.CylinderGeometry(0.4, 0.22, 0.3, 6), metal);
  bowl.position.set(x, y + 1.1, z); bowl.castShadow = true; scene.add(bowl);
  const flame = new THREE.Mesh(
    new THREE.ConeGeometry(0.26, 0.65, 6),
    new THREE.MeshLambertMaterial({ color: 0xffffff, emissive: 0xffffff,
                                    emissiveIntensity: 2.6 }));
  flame.position.set(x, y + 1.55, z);
  scene.add(flame);
  const l = new THREE.PointLight(0xffffff, 9, 14, 1.5);
  l.position.set(x, y + 1.8, z);
  scene.add(l);
  fires.push({ flame, light: l, seed: Math.random() * 100 });
}
brazier(-2.9, -18.3); brazier(2.9, -18.3);        // flanking the gate

// the fountain
{
  const stone = new THREE.MeshLambertMaterial({ color: 0x9aa2b5 });
  const basin = new THREE.Mesh(
    new THREE.CylinderGeometry(1.5, 1.62, 0.55, 8), stone);
  basin.position.set(FOUNTAIN.x, 0.27, FOUNTAIN.z);
  basin.castShadow = basin.receiveShadow = true;
  scene.add(basin);
  const water = new THREE.Mesh(
    new THREE.CircleGeometry(1.28, 16),
    new THREE.MeshLambertMaterial({ color: 0x99a1b4, emissive: 0xaab2c4,
                                    emissiveIntensity: 0.1 }));
  water.rotateX(-Math.PI / 2);
  water.position.set(FOUNTAIN.x, 0.56, FOUNTAIN.z);
  scene.add(water);
  const column = new THREE.Mesh(
    new THREE.CylinderGeometry(0.13, 0.2, 1.4, 8), stone);
  column.position.set(FOUNTAIN.x, 1.0, FOUNTAIN.z);
  column.castShadow = true;
  scene.add(column);
  const bowl = new THREE.Mesh(
    new THREE.CylinderGeometry(0.42, 0.28, 0.22, 8), stone);
  bowl.position.set(FOUNTAIN.x, 1.7, FOUNTAIN.z);
  bowl.castShadow = true;
  scene.add(bowl);
}

// stairs beyond the gate, descending into the dark
{
  for (let i = 0; i < 9; i++) {
    const shade = Math.max(0.08, 0.85 - i * 0.095);
    const step = new THREE.Mesh(
      new THREE.BoxGeometry(3.6, 0.06, 0.5),
      new THREE.MeshLambertMaterial({
        color: new THREE.Color(shade, shade * 1.03, shade * 1.12) }));
    step.position.set(0, 0.03, -21.2 - i * 0.55);
    step.receiveShadow = true;
    scene.add(step);
  }
}

// ── asset loading ──────────────────────────────────────────────────────────
const loader = new GLTFLoader();
const load = (url) => new Promise((res, rej) => loader.load(url, res, undefined, rej));

function shadowify(root) {
  root.traverse((o) => {
    if (o.isMesh || o.isSkinnedMesh) { o.castShadow = true; o.receiveShadow = true; }
  });
}

const CHAR_FILES = ["Knight", "Barbarian", "Mage", "Rogue", "Rogue_Hooded"];
const WEAPON_FILES = ["sword_1handed", "axe_2handed", "axe_1handed", "staff",
                      "crossbow_1handed", "dagger", "wand", "shield_round"];

const BUILDINGS = [
  // file, hub name, x, z, rotY, footprint, interactable?
  ["building_tavern_blue", "the lodge", -10, 9, Math.PI / 2, 6.5, true],
  ["building_blacksmith_blue", "the forge", -10, 0.8, Math.PI / 2, 5.5, true],
  ["building_home_A_blue", "the bunkhouse", -10, -6.2, Math.PI / 2, 4.5, true],
  ["building_home_B_blue", "the homestead", -10, 16, Math.PI / 2, 5.0, true],
  ["building_castle_blue", "the vault", 10, 8.5, -Math.PI / 2, 6.5, true],
  ["building_church_blue", "the medlab", 10, 0.5, -Math.PI / 2, 5.5, true],
  ["building_market_blue", "the market", 10, -7, -Math.PI / 2, 5.0, true],
  ["building_windmill_blue", "the mill", 10, 15.5, -Math.PI / 2, 6.0, true],
];
const WALLS = ["wall_straight", "wall_straight_gate"];

const VARIANTS = {
  "human ♂":    { base: "Knight",       s: [1.00, 1.00, 1.00], main: "sword_1handed", off: "shield_round" },
  "human ♀":    { base: "Knight",       s: [0.92, 0.97, 0.92], main: "sword_1handed" },
  "elf ♂":      { base: "Rogue_Hooded", s: [0.94, 1.09, 0.94], main: "crossbow_1handed" },
  "elf ♀":      { base: "Rogue",        s: [0.88, 1.06, 0.88], main: "staff" },
  "dwarf ♂":    { base: "Barbarian",    s: [1.14, 0.78, 1.14], main: "axe_2handed" },
  "dwarf ♀":    { base: "Barbarian",    s: [1.06, 0.75, 1.06], main: "axe_1handed", off: "shield_round" },
  "halfling ♂": { base: "Rogue",        s: [0.74, 0.58, 0.74], main: "dagger" },
  "halfling ♀": { base: "Mage",         s: [0.72, 0.60, 0.72], main: "wand" },
};

const bases = {}, weapons = {}, clipsFor = {};
const colliders = [];

function spawnCharacter(variantName, x, z) {
  const v = VARIANTS[variantName];
  const src = bases[v.base];
  const model = SkeletonUtils.clone(src.scene);
  const wrap = new THREE.Group();
  const box = new THREE.Box3().setFromObject(model);
  const k = 1.75 / (box.max.y - box.min.y);
  model.scale.setScalar(k);
  wrap.add(model);
  wrap.scale.set(v.s[0], v.s[1], v.s[2]);
  wrap.position.set(x, 0, z);
  shadowify(wrap);
  scene.add(wrap);

  for (const [slot, file] of [["handslot.r", v.main], ["handslot.l", v.off]]) {
    if (!file) continue;
    const node = model.getObjectByName(slot);
    if (node) { const w = weapons[file].clone(); shadowify(w); node.add(w); }
  }

  const mixer = new THREE.AnimationMixer(model);
  const clips = clipsFor[v.base];
  const action = (n) => {
    const c = clips.find((c) => c.name === n);
    return c ? mixer.clipAction(c) : null;
  };
  const acts = { idle: action("Idle"), walk: action("Walking_A"),
                 run: action("Running_A"), lie: action("Lie_Idle") };
  acts.idle && acts.idle.play();
  return { wrap, model, mixer, acts, cur: "idle",
           x, z, tx: x, tz: z, speed: 3.4, yaw: 0, variant: variantName };
}

function play(ch, name, fade = 0.18) {
  if (ch.cur === name || !ch.acts[name]) return;
  const prev = ch.acts[ch.cur];
  ch.acts[name].reset().fadeIn(fade).play();
  if (prev) prev.fadeOut(fade);
  ch.cur = name;
}

// procedural beasts for outside the wall
const beasts = [];
function beast(kind, x, z) {
  const boar = kind === "boar";
  const bodyCol = boar ? 0x7d8294 : 0xaab0c0;
  const g = new THREE.Group();
  const mat = new THREE.MeshLambertMaterial({ color: bodyCol });
  const body = new THREE.Mesh(new THREE.SphereGeometry(1, 10, 8), mat);
  body.scale.set(boar ? 0.5 : 0.42, boar ? 0.42 : 0.38, boar ? 0.72 : 0.95);
  body.position.y = boar ? 0.52 : 0.58;
  g.add(body);
  const head = new THREE.Mesh(new THREE.SphereGeometry(boar ? 0.3 : 0.24, 8, 6), mat);
  head.position.set(0, boar ? 0.55 : 0.68, boar ? 0.78 : 0.95);
  g.add(head);
  const snout = new THREE.Mesh(new THREE.BoxGeometry(0.16, 0.14, boar ? 0.22 : 0.34), mat);
  snout.position.set(0, boar ? 0.46 : 0.62, boar ? 1.05 : 1.2);
  g.add(snout);
  if (!boar) {
    const tail = new THREE.Mesh(new THREE.BoxGeometry(0.1, 0.1, 0.55), mat);
    tail.position.set(0, 0.68, -1.05); tail.rotation.x = -0.5;
    g.add(tail);
  }
  const legs = [];
  const legLen = boar ? 0.42 : 0.55;
  for (const [lx, lz] of [[-0.22, 0.42], [0.22, 0.42], [-0.22, -0.42], [0.22, -0.42]]) {
    const hip = new THREE.Group();
    hip.position.set(lx, legLen, lz * (boar ? 1 : 1.5));
    const leg = new THREE.Mesh(new THREE.BoxGeometry(0.1, legLen, 0.1), mat);
    leg.position.y = -legLen / 2;
    hip.add(leg); g.add(hip); legs.push(hip);
  }
  g.position.set(x, 0, z);
  shadowify(g);
  scene.add(g);
  beasts.push({ g, legs, x, z, tx: x, tz: z, yaw: 0,
                speed: boar ? 2.6 + Math.random() : 4.6,
                phase: Math.random() * 7 });
}
beast("boar", -19, 2); beast("boar", -17, -10); beast("boar", 17, -3);
beast("wolf", 5, -26);

function outsideTown(x, z) {
  return !(Math.abs(x) < WALL_X + 1.2 &&
           z > WALL_ZN - 1.2 && z < WALL_ZS + 1.2);
}
function beastTarget(b) {
  // short local hops that never cut through the town
  for (let i = 0; i < 24; i++) {
    const x = THREE.MathUtils.clamp(b.x + (Math.random() - 0.5) * 14, -29, 29);
    const z = THREE.MathUtils.clamp(b.z + (Math.random() - 0.5) * 14, -23, 21);
    const mx = (b.x + x) / 2, mz = (b.z + z) / 2;
    if (outsideTown(x, z) && outsideTown(mx, mz)) { b.tx = x; b.tz = z; return; }
  }
}

// ── UI plumbing ────────────────────────────────────────────────────────────
const labels = document.getElementById("labels");
const promptEl = document.getElementById("prompt");
const toastEl = document.getElementById("toast");
const tags = new Map();
function tagFor(key, cls) {
  if (!tags.has(key)) {
    const d = document.createElement("div");
    d.className = "tag " + cls; d.textContent = key; labels.appendChild(d);
    tags.set(key, d);
  }
  return tags.get(key);
}
function place(el, pos, lift = 2.1) {
  const v = pos.clone(); v.y += lift; v.project(camera);
  const r = canvas.getBoundingClientRect();
  el.style.left = (v.x * 0.5 + 0.5) * r.width + "px";
  el.style.top = (-v.y * 0.5 + 0.5) * r.height + "px";
  el.style.display = Math.abs(v.x) < 1.05 && Math.abs(v.y) < 1.05 ? "" : "none";
}
let toastTimer = 0;
function toast(msg, ms = 3200) {
  toastEl.textContent = msg; toastEl.style.opacity = 1;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => (toastEl.style.opacity = 0), ms);
}
let bubbleEl = null, bubbleUntil = 0, bubbleTarget = null;
function bubble(target, text) {
  if (bubbleEl) bubbleEl.remove();
  bubbleEl = document.createElement("div");
  bubbleEl.className = "bubble"; bubbleEl.textContent = text;
  labels.appendChild(bubbleEl);
  bubbleTarget = target; bubbleUntil = performance.now() + 3800;
}

// options bar under the canvas — [1] [2] buttons like the chat cards
const acts = {};
function setPrompt(options) {
  Object.keys(acts).forEach((k) => delete acts[k]);
  if (!options || !options.length) {
    promptEl.innerHTML = '<span class="hint">walk close to things to act</span>';
    return;
  }
  promptEl.innerHTML = options.map(([key, label]) =>
    `<button class="opt" data-k="${key}">` +
    `<span class="key">[${key}]</span> ${label}</button>`
  ).join("");
  for (const [key, , fn] of options) acts[key] = fn;
  promptEl.querySelectorAll(".opt").forEach((el) =>
    el.addEventListener("pointerdown", (e) => {
      e.stopPropagation(); if (acts[el.dataset.k]) acts[el.dataset.k]();
    }));
}
promptEl.innerHTML = '<span class="hint">loading the town…</span>';

// ── input ──────────────────────────────────────────────────────────────────
const keys = new Set();
window.addEventListener("keydown", (e) => {
  const k = e.key.toLowerCase();
  if (["arrowup", "arrowdown", "arrowleft", "arrowright", "w", "a", "s", "d"].includes(k)) {
    keys.add(k); e.preventDefault();
  } else if (acts[k === "enter" ? "enter" : k]) {
    acts[k === "enter" ? "enter" : k]();
  }
});
window.addEventListener("keyup", (e) => keys.delete(e.key.toLowerCase()));

const ray = new THREE.Raycaster();
const groundPlane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0);
canvas.addEventListener("pointerdown", (e) => {
  if (!player) return;
  const r = canvas.getBoundingClientRect();
  const p = new THREE.Vector2(((e.clientX - r.left) / r.width) * 2 - 1,
                              -((e.clientY - r.top) / r.height) * 2 + 1);
  ray.setFromCamera(p, camera);
  const hit = new THREE.Vector3();
  if (ray.ray.intersectPlane(groundPlane, hit)) {
    player.tx = THREE.MathUtils.clamp(hit.x, BOUND.x0, BOUND.x1);
    player.tz = THREE.MathUtils.clamp(hit.z, BOUND.z0, BOUND.z1);
  }
});

// ── world state ────────────────────────────────────────────────────────────
let player = null;
let autoEnter = null;
const mobileMQ = window.matchMedia("(max-width: 700px)");
mobileMQ.addEventListener("change", () => { current = undefined; });
const chipByName = new Map();
function markNear(name) {
  for (const [n, el] of chipByName)
    el.classList.toggle("near", n === name);
}
const walkers = [];
const sleepers = [];
const interactables = [];
let ready = false;

const MESSAGES = ["gg — sleep tight.", "the boar on 1 is mine.",
  "meet at the gate at world-dawn."];
let msgIdx = 0;

function zzzSprite() {
  const c = document.createElement("canvas"); c.width = 5; c.height = 4;
  const g = c.getContext("2d"); g.fillStyle = "#fff";
  [[0,0],[1,0],[2,0],[3,0],[2,1],[1,2],[0,3],[1,3],[2,3],[3,3]]
    .forEach(([x,y]) => g.fillRect(x, y, 1, 1));
  const t = new THREE.CanvasTexture(c);
  t.magFilter = t.minFilter = THREE.NearestFilter;
  const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: t, transparent: true }));
  s.scale.set(0.34, 0.28, 1); scene.add(s);
  return s;
}

async function build() {
  const [chars, weps, blds, walls] = await Promise.all([
    Promise.all(CHAR_FILES.map((n) => load(`./assets/characters/${n}.glb`))),
    Promise.all(WEAPON_FILES.map((n) => load(`./assets/weapons/${n}.gltf`))),
    Promise.all(BUILDINGS.map(([f]) => load(`./assets/buildings/${f}.gltf`))),
    Promise.all(WALLS.map((f) => load(`./assets/buildings/${f}.gltf`))),
  ]);
  CHAR_FILES.forEach((n, i) => {
    bases[n] = chars[i]; clipsFor[n] = chars[i].animations;
  });
  WEAPON_FILES.forEach((n, i) => { weapons[n] = weps[i].scene; });

  BUILDINGS.forEach(([file, name, x, z, rotY, foot, interactive], i) => {
    const m = blds[i].scene;
    const box = new THREE.Box3().setFromObject(m);
    const size = box.getSize(new THREE.Vector3());
    const k = foot / Math.max(size.x, size.z);
    m.scale.setScalar(k);
    m.rotation.y = rotY;
    m.updateMatrixWorld(true);
    const b = new THREE.Box3().setFromObject(m);
    m.position.set(x - (b.min.x + b.max.x) / 2, -b.min.y,
                   z - (b.min.z + b.max.z) / 2);
    shadowify(m);
    scene.add(m);
    m.updateMatrixWorld(true);
    const wb = new THREE.Box3().setFromObject(m);
    const hit = { x0: wb.min.x - 0.25, x1: wb.max.x + 0.25,
                  z0: wb.min.z - 0.25, z1: wb.max.z + 0.25 };
    colliders.push(hit);
    if (interactive)
      interactables.push({ name, box: hit, r: 1.6, kind: "building" });
  });

  // town wall with the gate at the north end
  const wallSrc = walls[0].scene, gateSrc = walls[1].scene;
  const wbox = new THREE.Box3().setFromObject(wallSrc);
  const wsize = wbox.getSize(new THREE.Vector3());
  const SEG = 4.5;
  const wk = SEG / Math.max(wsize.x, wsize.z);
  const alongX = wsize.x >= wsize.z;
  function wallSeg(src, x, z, rotY) {
    const m = src.clone();
    m.scale.setScalar(wk);
    m.rotation.y = rotY;
    m.updateMatrixWorld(true);
    const b = new THREE.Box3().setFromObject(m);
    m.position.set(x - (b.min.x + b.max.x) / 2, -b.min.y,
                   z - (b.min.z + b.max.z) / 2);
    shadowify(m);
    scene.add(m);
  }
  const yawNS = alongX ? Math.PI / 2 : 0;
  const yawEW = alongX ? 0 : Math.PI / 2;
  for (let z = WALL_ZN + SEG / 2; z < WALL_ZS; z += SEG) {
    wallSeg(wallSrc, -WALL_X, z, yawNS);
    wallSeg(wallSrc, WALL_X, z, yawNS);
  }
  for (let x = -WALL_X + SEG / 2; x < WALL_X; x += SEG)
    wallSeg(wallSrc, x, WALL_ZS, yawEW);
  for (const x of [-WALL_X + SEG / 2, -WALL_X + SEG * 1.5, -WALL_X + SEG * 2.5])
    wallSeg(wallSrc, x, WALL_ZN, yawEW);
  for (const x of [WALL_X - SEG / 2, WALL_X - SEG * 1.5, WALL_X - SEG * 2.5])
    wallSeg(wallSrc, x, WALL_ZN, yawEW);
  wallSeg(gateSrc, 0, WALL_ZN, yawEW);
  const wallTop = wsize.y * wk;
  brazier(-WALL_X, WALL_ZN, wallTop);            // fires on the wall corners
  brazier(WALL_X, WALL_ZN, wallTop);
  brazier(-WALL_X, WALL_ZS, wallTop);
  brazier(WALL_X, WALL_ZS, wallTop);
  interactables.push({ name: "the tower gate", x: 0, z: WALL_ZN + 1.7,
                       r: 2.6, kind: "gate" });

  colliders.push({ x0: -1.8, x1: 1.8,
                   z0: FOUNTAIN.z - 1.9, z1: FOUNTAIN.z + 1.9 });

  player = spawnCharacter("human ♂", 0, 12);

  const npcDefs = [
    ["Maro", "dwarf ♂", -2, 5, [[-2, 5], [-5, -1], [2, -8], [-3.5, -13]],
      ["Floor 6 wardens hit like carts. Bring pity gold.",
       "You the one Cortana rides with? Heard about the boar."]],
    ["Sable", "elf ♀", 3, -4, [[3, -4], [5, -12], [-3, -16], [2, 1]],
      ["The Vault pays 5% a day. Sleeping gold is safe gold.",
       "Lost my blade honing greedy. Don't hone greedy."]],
    ["Petra", "human ♀", -2, -11, [[-2, -11], [4, -15.5], [-5, -16.5], [0, -8]],
      ["Market's short on iron since the mine flooded."]],
    ["Bruna", "dwarf ♀", 2.5, 8.5, [[2.5, 8.5], [-2, 11.5], [3, 3], [-3, 6.5]],
      ["My axe has a name. You don't get to know it."]],
    ["Pip", "halfling ♂", -5, 2, [[-5, 2], [-13.4, -1], [-13.4, 5], [-4, -4.5]],
      ["I'm not short, the tower's tall."]],
    ["Vess", "elf ♂", 6, -8.5, [[6, -8.5], [13.4, -11], [13.4, -2], [5, -13.5]],
      ["Crossbow beats sword above floor 30. Ask me how I know."]],
  ];
  for (const [name, variant, x, z, wps, lines] of npcDefs) {
    const c = spawnCharacter(variant, x, z);
    c.speed = 1.6 + Math.random();
    walkers.push({ c, name, waypoints: wps, lines });
  }

  for (const [name, variant, x, z] of [
    ["Wex", "halfling ♀", -3.4, 13.2], ["Brannock", "human ♂", 5.6, -17.2]]) {
    const c = spawnCharacter(variant, x, z);
    play(c, "lie", 0.01);
    c.wrap.rotation.y = Math.random() * 6.28;
    sleepers.push({ c, name, looted: false, zz: zzzSprite(),
                    x, z, r: 1.9, kind: "sleeper" });
  }
  interactables.push(...sleepers);

  // build the destination list — every enterable place, tappable
  const destEl = document.getElementById("dest");
  let destIdx = 0;
  for (const it of interactables) {
    if (it.kind !== "building" && it.kind !== "gate") continue;
    const b = document.createElement("button");
    b.className = "chip";
    b.innerHTML = `<span class="key">[${++destIdx}]</span> ${it.name}`;
    chipByName.set(it.name, b);
    b.addEventListener("pointerdown", (e) => {
      e.stopPropagation();
      let tx, tz;
      if (it.box) {
        const cx = (it.box.x0 + it.box.x1) / 2;
        tz = (it.box.z0 + it.box.z1) / 2;
        tx = cx < 0 ? it.box.x1 + 1.0 : it.box.x0 - 1.0;   // face the avenue
        tz = THREE.MathUtils.clamp(tz, BOUND.z0, BOUND.z1);
      } else { tx = it.x; tz = it.z; }
      player.tx = tx; player.tz = tz;
      autoEnter = it;
      toast(`walking to ${it.name}…`, 1800);
    });
    destEl.appendChild(b);
  }
  setPrompt(null);
  ready = true;
}
build().catch((e) => {
  promptEl.innerHTML = '<span class="hint">load failed: ' + e.message + "</span>";
  console.error(e);
});

// ── interactions ───────────────────────────────────────────────────────────
let current = null;
function refreshPrompt() {
  let best = null, bd = 1e9;
  for (const it of interactables) {
    let d;
    if (it.box) {
      const gx = Math.max(it.box.x0 - player.x, 0, player.x - it.box.x1);
      const gz = Math.max(it.box.z0 - player.z, 0, player.z - it.box.z1);
      d = Math.hypot(gx, gz);
    } else {
      d = Math.hypot(player.x - it.x, player.z - it.z);
    }
    if (d < it.r && d < bd) { best = it; bd = d; }
  }
  for (const wk of walkers) {
    const d = Math.hypot(player.x - wk.c.x, player.z - wk.c.z);
    if (d < 1.8 && d < bd) { best = { kind: "talk", wk }; bd = d; }
  }
  if (autoEnter && best === autoEnter) {
    const it = autoEnter; autoEnter = null;
    if (it.kind === "gate")
      toast("the gate wardens wave you through. (floor 1 loads here)");
    else toast(`${it.name} — the door grinds open. (interior scene loads here)`);
  }
  const same = best === current ||
    (best && current && best.kind === "talk" && current.kind === "talk" &&
     best.wk === current.wk);
  if (same) return;
  current = best;
  if (!best) { setPrompt(null); markNear(null); return; }
  const mobile = mobileMQ.matches;
  if (best.kind === "building" || best.kind === "gate") {
    markNear(mobile ? best.name : null);
  } else {
    markNear(null);
  }
  if (best.kind === "building") {
    if (mobile) setPrompt(null);
    else setPrompt([["1", `enter ${best.name}`, () =>
      toast(`${best.name} — the door grinds open. (interior scene loads here)`)]]);
  } else if (best.kind === "gate") {
    if (mobile) setPrompt(null);
    else setPrompt([["1", "the tower gate — descend to floor 1", () =>
      toast("the gate wardens wave you through. (floor 1 loads here)")]]);
  } else if (best.kind === "sleeper") {
    setPrompt([
      ["1", `loot ${best.name}`, () => {
        if (best.looted) { toast(`${best.name}'s pack is already empty.`); return; }
        best.looted = true;
        toast(`+◈ 3 lifted from ${best.name}'s pack — their shardmind logged your face.`);
      }],
      ["2", "leave message", () =>
        toast(`message pinned to ${best.name}: “${MESSAGES[msgIdx++ % MESSAGES.length]}”`)],
    ]);
  } else if (best.kind === "talk") {
    setPrompt([["1", `talk to ${best.wk.name}`, () =>
      bubble(best.wk.c,
        best.wk.lines[Math.floor(Math.random() * best.wk.lines.length)])]]);
  }
}

// ── simulation ─────────────────────────────────────────────────────────────
function collide(ch, dt) {
  for (const b of colliders) {
    if (ch.x <= b.x0 || ch.x >= b.x1 || ch.z <= b.z0 || ch.z >= b.z1) continue;
    const pushes = [
      [b.x0 - ch.x, 0], [b.x1 - ch.x, 0],
      [0, b.z0 - ch.z], [0, b.z1 - ch.z],
    ];
    let best = pushes[0];
    for (const p of pushes)
      if (Math.abs(p[0] + p[1]) < Math.abs(best[0] + best[1])) best = p;
    ch.x += best[0]; ch.z += best[1];
    ch.hitBox = b;
    // slide along the blocked face — toward the target side if it has one,
    // else toward the nearer corner
    const slide = ch.speed * 0.8 * dt;
    const gx = ch.gx !== undefined ? ch.gx : ch.tx;
    const gz = ch.gz !== undefined ? ch.gz : ch.tz;
    if (best[0] === 0) {
      const want = gx - ch.x;
      ch.x += slide * (Math.abs(want) > 0.3 ? Math.sign(want)
                       : (ch.x >= (b.x0 + b.x1) / 2 ? 1 : -1));
    } else {
      const want = gz - ch.z;
      ch.z += slide * (Math.abs(want) > 0.3 ? Math.sign(want)
                       : (ch.z >= (b.z0 + b.z1) / 2 ? 1 : -1));
    }
  }
}

function stepCharacter(ch, dt, kbVec) {
  let vx = 0, vz = 0, moving = false;
  if (kbVec && (kbVec.x || kbVec.z)) {
    const l = Math.hypot(kbVec.x, kbVec.z);
    vx = (kbVec.x / l) * ch.speed; vz = (kbVec.z / l) * ch.speed;
    ch.tx = ch.x; ch.tz = ch.z;
    moving = true;
  } else {
    // detour via a box corner when a collider stalls direct progress
    let gx = ch.tx, gz = ch.tz;
    if (ch.detour) {
      if (Math.hypot(ch.detour[0] - ch.x, ch.detour[1] - ch.z) < 0.5)
        ch.detour = null;
      else { gx = ch.detour[0]; gz = ch.detour[1]; }
    }
    ch.gx = gx; ch.gz = gz;
    const dx = gx - ch.x, dz = gz - ch.z;
    const d = Math.hypot(dx, dz);
    if (d > 0.1) {
      vx = (dx / d) * Math.min(ch.speed, d / dt);
      vz = (dz / d) * Math.min(ch.speed, d / dt);
      moving = true;
      const total = Math.hypot(ch.tx - ch.x, ch.tz - ch.z);
      if (ch.lastD !== undefined && total > ch.lastD - ch.speed * dt * 0.25 && ch.hitBox)
        ch.stall = (ch.stall || 0) + dt;
      else ch.stall = 0;
      ch.lastD = total;
      if (ch.stall > 0.45 && ch.hitBox) {
        const b = ch.hitBox, M = 0.9;
        let bestC = null, bestScore = 1e9;
        for (const c of [[b.x0 - M, b.z0 - M], [b.x1 + M, b.z0 - M],
                         [b.x0 - M, b.z1 + M], [b.x1 + M, b.z1 + M]]) {
          c[0] = THREE.MathUtils.clamp(c[0], BOUND.x0, BOUND.x1);
          c[1] = THREE.MathUtils.clamp(c[1], BOUND.z0, BOUND.z1);
          const score = Math.hypot(c[0] - ch.x, c[1] - ch.z) +
                        Math.hypot(ch.tx - c[0], ch.tz - c[1]);
          if (score < bestScore) { bestScore = score; bestC = c; }
        }
        ch.detour = bestC; ch.stall = 0; ch.hitBox = null;
      }
    } else { ch.stall = 0; ch.lastD = undefined; }
  }
  if (moving) {
    ch.x += vx * dt; ch.z += vz * dt;
    const want = Math.atan2(vx, vz);
    let dy = want - ch.yaw;
    while (dy > Math.PI) dy -= 2 * Math.PI;
    while (dy < -Math.PI) dy += 2 * Math.PI;
    ch.yaw += dy * Math.min(1, dt * 12);
    play(ch, Math.hypot(vx, vz) > 2.6 ? "run" : "walk");
  } else if (ch.cur !== "lie") {
    play(ch, "idle");
  }
  ch.wrap.position.set(ch.x, 0, ch.z);
  ch.wrap.rotation.y = ch.yaw;
  ch.mixer.update(dt);
  return moving;
}

let last = performance.now();
function loop(now) {
  requestAnimationFrame(loop);
  if (!ready) return;
  const dt = Math.min(0.05, (now - last) / 1000); last = now;

  const kb = { x: 0, z: 0 };
  if (keys.has("arrowleft") || keys.has("a")) kb.x -= 1;
  if (keys.has("arrowright") || keys.has("d")) kb.x += 1;
  if (keys.has("arrowup") || keys.has("w")) kb.z -= 1;
  if (keys.has("arrowdown") || keys.has("s")) kb.z += 1;
  stepCharacter(player, dt, kb);
  player.x = THREE.MathUtils.clamp(player.x, BOUND.x0, BOUND.x1);
  player.z = THREE.MathUtils.clamp(player.z, BOUND.z0, BOUND.z1);
  collide(player, dt);

  for (const wk of walkers) {
    if (!stepCharacter(wk.c, dt) && Math.random() < 0.005) {
      const wp = wk.waypoints[Math.floor(Math.random() * wk.waypoints.length)];
      wk.c.tx = wp[0]; wk.c.tz = wp[1];
    }
  }
  for (const s of sleepers) {
    s.c.mixer.update(dt);
    const t = (now / 1000) % 2;
    s.zz.position.set(s.x + 0.8, 0.8 + t * 0.4, s.z);
    s.zz.material.opacity = t < 1.6 ? 1 : (2 - t) * 2.5;
  }

  // beasts prowl outside the wall
  for (const b of beasts) {
    const dx = b.tx - b.x, dz = b.tz - b.z;
    const d = Math.hypot(dx, dz);
    if (d < 0.4) { if (Math.random() < 0.02) beastTarget(b); }
    else {
      b.x += (dx / d) * b.speed * dt;
      b.z += (dz / d) * b.speed * dt;
      const want = Math.atan2(dx, dz);
      let dy = want - b.yaw;
      while (dy > Math.PI) dy -= 2 * Math.PI;
      while (dy < -Math.PI) dy += 2 * Math.PI;
      b.yaw += dy * Math.min(1, dt * 8);
      b.phase += dt * b.speed * 3.2;
      for (let i = 0; i < b.legs.length; i++)
        b.legs[i].rotation.x = Math.sin(b.phase + (i % 2 ? Math.PI : 0)) * 0.7;
      b.g.position.y = Math.abs(Math.sin(b.phase)) * 0.05;
    }
    b.g.position.x = b.x; b.g.position.z = b.z;
    b.g.rotation.y = b.yaw;
  }

  for (let i = 0; i < lampLights.length; i++)
    lampLights[i].intensity = 4 + Math.sin(now / 90 + i * 7) * 0.4
                                + Math.sin(now / 37 + i * 3) * 0.25;
  for (const f of fires) {                      // shimmering brazier glow
    f.light.intensity = 9 + Math.sin(now / 67 + f.seed) * 2.2
                          + Math.sin(now / 29 + f.seed * 3) * 1.3;
    const s = 1 + Math.sin(now / 53 + f.seed * 7) * 0.16;
    f.flame.scale.set(s, 1 + Math.sin(now / 41 + f.seed) * 0.22, s);
  }

  const want = new THREE.Vector3(player.x, 0, player.z).add(CAM_OFF);
  camera.position.lerp(want, 1 - Math.pow(0.0018, dt));
  camera.lookAt(camera.position.x - CAM_OFF.x, 0, camera.position.z - CAM_OFF.z);

  for (const wk of walkers)
    place(tagFor(`${wk.name} · ${wk.c.variant}`, "player"), wk.c.wrap.position, 2.1);
  for (const s of sleepers)
    place(tagFor(`${s.name} · ${s.c.variant}`, ""), new THREE.Vector3(s.x, 0.4, s.z), 1.0);
  if (bubbleEl) {
    if (performance.now() > bubbleUntil) { bubbleEl.remove(); bubbleEl = null; }
    else place(bubbleEl, bubbleTarget.wrap.position, 1.9);
  }
  refreshPrompt();

  const zzz = sleepers.map((s) => s.zz);
  renderer.setRenderTarget(rtColor);
  renderer.render(scene, camera);
  zzz.forEach((s) => (s.visible = false));
  scene.overrideMaterial = normalMat;
  renderer.setRenderTarget(rtNormal);
  renderer.render(scene, camera);
  scene.overrideMaterial = null;
  zzz.forEach((s) => (s.visible = true));
  renderer.setRenderTarget(null);
  renderer.render(postScene, postCam);
}
requestAnimationFrame(loop);

window.mock = {
  walkTo: (x, z) => { player.tx = x; player.tz = z; },
  pos: () => [player.x, player.z],
  ready: () => ready,
};
