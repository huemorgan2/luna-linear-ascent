// 3d-fight demo1 — live 3D combatants over the animated 1-bit background.
// Side view, orthographic. Renders into a transparent 480x270 buffer,
// post pass = sobel ink outlines (depth+normal) + Bayer dither — same
// discipline as base-mock/threejs, but only character pixels are opaque
// so the canvas overlays the background GIF on one shared pixel grid.
import * as THREE from "three";
import { GLTFLoader } from "./vendor/GLTFLoader.js";
import * as SkeletonUtils from "./vendor/SkeletonUtils.js";

const W = 480, H = 270;
const FLOOR_FRAC = 0.78;              // combatants' feet, fraction of H

// ── fights (floor 1 — The Fencerows) ──────────────────────────────────────
const FIGHTS = {
  grey_wolf: {
    name: "Grey wolf", monster: () => quadruped({ kind: "wolf" }),
    mx: 2.3, desc: "It has learned that climbers carry meat.",
  },
  feral_boar: {
    name: "Feral boar", monster: () => quadruped({ kind: "boar", s: 1.35 }),
    mx: 2.5, desc: "It charges first and decides why later.",
  },
  hedge_rat: {
    name: "Hedgerow rat", monster: () => quadruped({ kind: "rat", s: 0.8 }),
    mx: 2.1, desc: "Grown fat on abandoned granaries, teeth first.",
  },
  lane_wolf: {
    name: "The last pack", monster: () => pack(),
    mx: 2.4, desc: "The steading's own sheepdogs, feral and silent.",
  },
  goblin_straggler: {
    name: "Goblin straggler", monster: "goblin",
    mx: 2.3, desc: "Sets its feet behind the sword anyway, and grins.",
  },
  ember_shade: {
    name: "Hedge-wight", monster: () => emberShade(),
    mx: 2.6, desc: "Blackthorn snarled into shoulders and arms.",
  },
  warden: {
    name: "Warden Brackjaw", monster: () => warden(),
    mx: 2.7, desc: "Servos ticking, it lowers its head to charge.",
  },
};

// ── renderer + post targets ───────────────────────────────────────────────
const canvas = document.getElementById("chars");
const renderer = new THREE.WebGLRenderer({ canvas, antialias: false, alpha: true });
renderer.setPixelRatio(1);
renderer.setSize(W, H, false);
renderer.setClearColor(0x000000, 0);
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
    transparent: true,
    uniforms: {
      tScene: { value: rtColor.texture },
      tNormal: { value: rtNormal.texture },
      tDepth: { value: depthTex },
      tBayer: { value: bayerTex },
      texel: { value: new THREE.Vector2(1 / W, 1 / H) },
    },
    vertexShader: `
      varying vec2 vUv;
      void main(){ vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }`,
    fragmentShader: `
      uniform sampler2D tScene, tNormal, tDepth, tBayer;
      uniform vec2 texel;
      varying vec2 vUv;
      void main(){
        vec4 s = texture2D(tScene, vUv);
        float t = texture2D(tBayer, gl_FragCoord.xy / 8.0).r + 0.002;
        if (s.a < 0.03) {
          // black halo: 2px ink contour just outside the silhouette
          float near = 0.0;
          for (int i = 0; i < 8; i++) {
            float ang = 0.785398 * float(i);
            vec2 dir = vec2(cos(ang), sin(ang));
            near = max(near, texture2D(tScene, vUv + dir * texel).a);
            near = max(near, texture2D(tScene, vUv + dir * texel * 2.0).a);
          }
          gl_FragColor = near > 0.97
            ? vec4(0.0, 0.0, 0.0, 1.0) : vec4(0.0);
          return;
        }
        if (s.a < 0.97) {
          // shadow catcher: dithered contact shadow, pure black ink
          float on = step(t, s.a * 0.55);
          gl_FragColor = vec4(0.0, 0.0, 0.0, on);
          return;
        }
        float d0 = texture2D(tDepth, vUv).x;
        float dx = abs(texture2D(tDepth, vUv + vec2(texel.x, 0.0)).x - d0)
                 + abs(texture2D(tDepth, vUv - vec2(texel.x, 0.0)).x - d0);
        float dy = abs(texture2D(tDepth, vUv + vec2(0.0, texel.y)).x - d0)
                 + abs(texture2D(tDepth, vUv - vec2(0.0, texel.y)).x - d0);
        float depthEdge = step(0.0045, dx + dy);
        vec3 n0 = texture2D(tNormal, vUv).xyz;
        vec3 nx = texture2D(tNormal, vUv + vec2(texel.x, 0.0)).xyz;
        vec3 ny = texture2D(tNormal, vUv + vec2(0.0, texel.y)).xyz;
        float normalEdge = step(1.1, length(n0 - nx) + length(n0 - ny));
        float edge = max(depthEdge, normalEdge);
        float lum = max(s.r, max(s.g, s.b));
        lum = pow(clamp(lum * 1.35, 0.0, 1.0), 0.95);
        float on = step(t, lum) * (1.0 - edge);
        gl_FragColor = vec4(vec3(on), 1.0);
      }`,
  })));

// ── scene, side camera, key light ─────────────────────────────────────────
const scene = new THREE.Scene();

const VH = 4.7;                        // world units of view height
const camera = new THREE.OrthographicCamera(
  -VH * (W / H) / 2, VH * (W / H) / 2, VH / 2, -VH / 2, 0.1, 120);
const camTarget = new THREE.Vector3(0, 1.1, 0);
camera.position.set(0, 2.4, 26);       // slight tilt: ground catches shadows
camera.lookAt(camTarget);

// nudge the camera so world y=0 (the feet) lands on the GIF floor line
function alignFloor(frac) {
  for (let i = 0; i < 4; i++) {
    camera.updateMatrixWorld(true);
    const p = new THREE.Vector3(0, 0, 0).project(camera);
    const want = 1 - 2 * frac;                    // NDC y of the floor line
    const dy = (p.y - want) * VH / 2;
    camera.position.y += dy; camTarget.y += dy;
    camera.lookAt(camTarget);
    camera.updateMatrixWorld();
  }
}

scene.add(new THREE.AmbientLight(0xffffff, 0.55));
const key = new THREE.DirectionalLight(0xffffff, 3.4);
key.position.set(-6, 9, 12);
key.castShadow = true;
key.shadow.mapSize.set(1024, 1024);
key.shadow.camera.left = -6; key.shadow.camera.right = 6;
key.shadow.camera.top = 6; key.shadow.camera.bottom = -2;
key.shadow.camera.near = 2; key.shadow.camera.far = 40;
key.shadow.bias = -0.002;
scene.add(key);
const rim = new THREE.DirectionalLight(0xffffff, 1.1);
rim.position.set(8, 4, -6);
scene.add(rim);

const catcher = new THREE.Mesh(
  new THREE.PlaneGeometry(24, 10),
  new THREE.ShadowMaterial({ opacity: 0.85 }));
catcher.rotateX(-Math.PI / 2);
catcher.receiveShadow = true;
scene.add(catcher);

// ── asset loading (KayKit, vendored from base-mock) ───────────────────────
const loader = new GLTFLoader();
const assets = {};
async function loadAssets() {
  const [knight, rogue, sword] = await Promise.all([
    loader.loadAsync("./assets/Knight.glb"),
    loader.loadAsync("./assets/Rogue_Hooded.glb"),
    loader.loadAsync("./assets/sword_1handed.gltf"),
  ]);
  assets.knight = knight; assets.rogue = rogue;
  assets.sword = sword.scene;
}

function shadowify(o) {
  o.traverse((c) => { if (c.isMesh) { c.castShadow = true; } });
}

function rigged(src, { h = 1.75, sx = 1, sy = 1, sz = 1, sword = true }) {
  const model = SkeletonUtils.clone(src.scene);
  const wrap = new THREE.Group();
  const box = new THREE.Box3().setFromObject(model);
  model.scale.setScalar(h / (box.max.y - box.min.y));
  wrap.add(model);
  wrap.scale.set(sx, sy, sz);
  shadowify(wrap);
  if (sword) {
    const node = model.getObjectByName("handslot.r");
    if (node) { const w = assets.sword.clone(); shadowify(w); node.add(w); }
  }
  const mixer = new THREE.AnimationMixer(model);
  const idle = src.animations.find((c) => c.name === "Idle");
  if (idle) mixer.clipAction(idle).play();
  return { group: wrap, update: (dt) => mixer.update(dt) };
}

// ── procedural monsters (grown from the base-mock beast builder) ──────────
const MAT = (c) => new THREE.MeshLambertMaterial({ color: c });

function quadruped({ kind = "wolf", s = 1 } = {}) {
  const boar = kind === "boar", rat = kind === "rat";
  const mat = MAT(boar ? 0x757b8d : rat ? 0x848b9c : 0x8f96a8);
  const g = new THREE.Group();
  let body;
  if (boar || rat) {
    body = new THREE.Mesh(new THREE.SphereGeometry(1, 10, 8), mat);
    body.scale.set(0.5, 0.42, 0.72);
    body.position.y = 0.52;
    g.add(body);
  } else {
    // wolf: deep chest + smaller rump, high shoulders, tucked belly
    body = new THREE.Mesh(new THREE.SphereGeometry(1, 10, 8), mat);
    body.scale.set(0.34, 0.42, 0.52);
    body.position.set(0, 0.72, 0.35);
    g.add(body);
    const rump = new THREE.Mesh(new THREE.SphereGeometry(1, 10, 8), mat);
    rump.scale.set(0.29, 0.34, 0.5);
    rump.position.set(0, 0.7, -0.42);
    g.add(rump);
    const neck = new THREE.Mesh(new THREE.BoxGeometry(0.22, 0.3, 0.4), mat);
    neck.position.set(0, 0.92, 0.62);
    neck.rotation.x = -0.5;
    g.add(neck);
  }
  const headG = new THREE.Group();
  headG.position.set(0, boar ? 0.55 : rat ? 0.64 : 1.02,
                     boar ? 0.78 : rat ? 1.0 : 0.82);
  const head = new THREE.Mesh(new THREE.SphereGeometry(boar ? 0.3 : rat ? 0.26 : 0.2, 8, 6), mat);
  headG.add(head);
  const snout = new THREE.Mesh(new THREE.BoxGeometry(0.15, 0.13, boar ? 0.22 : 0.42), mat);
  snout.position.set(0, -0.06, boar ? 0.27 : 0.28);
  headG.add(snout);
  if (!boar && !rat) {
    headG.rotation.x = 0.22;               // head dropped, hunting
    for (const ex of [-0.09, 0.09]) {
      const ear = new THREE.Mesh(new THREE.ConeGeometry(0.08, 0.24, 4), mat);
      ear.position.set(ex, 0.22, -0.06);
      headG.add(ear);
    }
  }
  if (boar) {
    for (const ex of [-0.09, 0.09]) {
      const tusk = new THREE.Mesh(new THREE.ConeGeometry(0.045, 0.2, 5),
        MAT(0xf0f2f6));
      tusk.position.set(ex, -0.12, 0.3);
      tusk.rotation.x = 0.9;
      headG.add(tusk);
    }
  }
  g.add(headG);
  let tail;
  if (rat) {
    tail = new THREE.Mesh(new THREE.BoxGeometry(0.07, 0.07, 0.9), mat);
    tail.position.set(0, 0.35, -1.0);
    tail.rotation.x = 0.1;
  } else {
    // bushy tail: elongated ellipsoid angled down
    tail = new THREE.Mesh(new THREE.SphereGeometry(1, 7, 6), mat);
    tail.scale.set(0.11, 0.11, 0.42);
    tail.position.set(0, boar ? 0.55 : 0.62, boar ? -0.8 : -0.95);
    tail.rotation.x = boar ? -0.3 : -0.85;
  }
  g.add(tail);
  const legLen = boar ? 0.42 : rat ? 0.4 : 0.55;
  for (const [lx, lz] of [[-0.22, 0.42], [0.22, 0.42], [-0.22, -0.42], [0.22, -0.42]]) {
    const leg = new THREE.Mesh(new THREE.BoxGeometry(0.1, legLen, 0.1), mat);
    leg.position.set(lx, legLen / 2, lz * (boar ? 1 : 1.5));
    g.add(leg);
  }
  if (rat) { g.scale.set(0.9, 0.75, 0.9); body.scale.z = 1.05; }
  g.scale.multiplyScalar(s);
  shadowify(g);
  const baseBodyY = body.scale.y, baseHeadY = headG.position.y;
  const baseHeadRX = headG.rotation.x;
  return {
    group: g,
    update: (dt, t) => {
      const b = Math.sin(t * 2.1);
      body.scale.y = baseBodyY * (1 + 0.035 * b);
      headG.position.y = baseHeadY + 0.02 * Math.sin(t * 2.1 + 0.9);
      headG.rotation.x = baseHeadRX + 0.06 * Math.sin(t * 0.7);
      tail.rotation.y = 0.15 * Math.sin(t * 1.3);
    },
  };
}

function pack() {
  const g = new THREE.Group();
  const dogs = [];
  for (const [dx, dz, ds] of [[0, 0.6, 1], [0.9, -0.7, 0.92], [-0.4, -1.4, 0.85]]) {
    const d = quadruped({ kind: "wolf", s: ds * 0.9 });
    d.group.position.set(dx, 0, dz);
    d.group.rotation.y = 0.15 * dz;
    g.add(d.group);
    dogs.push(d);
  }
  return { group: g,
           update: (dt, t) => dogs.forEach((d, i) => d.update(dt, t + i * 1.7)) };
}

function emberShade() {
  const mat = MAT(0x8a90a2);
  const g = new THREE.Group();
  const torso = new THREE.Mesh(new THREE.BoxGeometry(0.8, 1.1, 0.45), mat);
  torso.position.y = 1.45;
  g.add(torso);
  const hips = new THREE.Mesh(new THREE.BoxGeometry(0.5, 0.4, 0.4), mat);
  hips.position.y = 0.85;
  g.add(hips);
  for (const lx of [-0.18, 0.18]) {
    const leg = new THREE.Mesh(new THREE.BoxGeometry(0.2, 0.75, 0.24), mat);
    leg.position.set(lx, 0.37, 0);
    g.add(leg);
  }
  const shoulders = new THREE.Mesh(new THREE.BoxGeometry(1.45, 0.3, 0.5), mat);
  shoulders.position.y = 1.95;
  g.add(shoulders);
  g.rotation.x = 0.08;                     // leans toward the player
  const arms = [];
  for (const ax of [-0.68, 0.68]) {
    const arm = new THREE.Mesh(new THREE.BoxGeometry(0.2, 1.05, 0.22), mat);
    arm.geometry.translate(0, -0.5, 0);
    arm.position.set(ax, 1.95, 0);
    arm.rotation.z = ax > 0 ? -0.5 : 0.5;
    g.add(arm);
    arms.push(arm);
  }
  const head = new THREE.Mesh(new THREE.BoxGeometry(0.32, 0.36, 0.32), mat);
  head.position.y = 2.32;
  g.add(head);
  // blackthorn: thorn cones snarled over shoulders, back and head
  const thorn = MAT(0x6a7080);
  const rand = (a, b) => a + Math.random() * (b - a);
  for (let i = 0; i < 26; i++) {
    const th = new THREE.Mesh(
      new THREE.ConeGeometry(rand(0.03, 0.07), rand(0.25, 0.6), 5), thorn);
    const zone = Math.random();
    if (zone < 0.5) {
      th.position.set(rand(-0.7, 0.7), rand(1.8, 2.15), rand(-0.25, 0.1));
    } else if (zone < 0.8) {
      th.position.set(rand(-0.35, 0.35), rand(1.1, 1.9), rand(-0.35, -0.15));
    } else {
      th.position.set(rand(-0.2, 0.2), rand(2.25, 2.5), rand(-0.15, 0.15));
    }
    th.rotation.set(rand(-1.6, -0.4) * (zone < 0.8 ? 1 : 0.4),
                    0, rand(-0.9, 0.9));
    g.add(th);
  }
  const eyeM = new THREE.MeshLambertMaterial(
    { color: 0xffffff, emissive: 0xffffff, emissiveIntensity: 2.0 });
  for (const ex of [-0.08, 0.08]) {
    const eye = new THREE.Mesh(new THREE.SphereGeometry(0.035), eyeM);
    eye.position.set(ex, 2.34, 0.17);
    g.add(eye);
  }
  g.scale.multiplyScalar(1.25);
  shadowify(g);
  return {
    group: g,
    update: (dt, t) => {
      g.rotation.z = 0.02 * Math.sin(t * 0.8);
      torso.rotation.y = 0.04 * Math.sin(t * 0.55);
      arms[0].rotation.z = 0.5 + 0.06 * Math.sin(t * 0.8 + 1);
      arms[1].rotation.z = -0.5 - 0.06 * Math.sin(t * 0.8 + 2);
    },
  };
}

function warden() {
  const base = quadruped({ kind: "wolf", s: 1.2 });
  const g = base.group;
  const plate = MAT(0x596070);
  for (const [pz, pw] of [[0.35, 0.66], [-0.05, 0.6], [-0.45, 0.52]]) {
    const slab = new THREE.Mesh(new THREE.BoxGeometry(pw, 0.12, 0.34), plate);
    slab.position.set(0, 1.1, pz);
    slab.rotation.x = -0.06;
    g.add(slab);
  }
  const mask = new THREE.Mesh(new THREE.BoxGeometry(0.32, 0.18, 0.38), plate);
  mask.position.set(0, 1.12, 0.86);
  g.add(mask);
  const eyeM = new THREE.MeshLambertMaterial(
    { color: 0xffffff, emissive: 0xffffff, emissiveIntensity: 2.4 });
  const eye = new THREE.Mesh(new THREE.SphereGeometry(0.05), eyeM);
  eye.position.set(0.1, 0.98, 1.06);
  g.add(eye);
  shadowify(g);
  const outer = new THREE.Group();
  outer.add(g);
  return {
    group: outer,
    update: (dt, t) => {
      base.update(dt, t * 0.8);
      // servo tick: the head sweep moves in quantized steps
      const sweep = Math.sin(t * 0.5);
      g.rotation.y = Math.round(sweep * 5) / 5 * 0.1;
    },
  };
}

// ── stage control ─────────────────────────────────────────────────────────
let player = null, monster = null, monsterId = null;

function clearActor(a) {
  if (a) scene.remove(a.group);
}

export async function setFight(id) {
  const f = FIGHTS[id];
  if (!f || id === monsterId) return;
  monsterId = id;
  clearActor(monster);
  monster = f.monster === "goblin"
    ? rigged(assets.rogue, { h: 1.75, sx: 0.85, sy: 0.72, sz: 0.85 })
    : f.monster();
  monster.group.position.set(f.mx, 0, 0);
  monster.group.rotation.y += -Math.PI / 2;   // face left, side-on
  scene.add(monster.group);
}

export function fights() { return FIGHTS; }

// ── run ───────────────────────────────────────────────────────────────────
await loadAssets();
alignFloor(FLOOR_FRAC);

player = rigged(assets.knight, { h: 1.75 });
player.group.position.set(-2.4, 0, 0);
player.group.rotation.y = Math.PI / 2;        // face right
scene.add(player.group);

const clock = new THREE.Clock();
function frame() {
  requestAnimationFrame(frame);
  const dt = Math.min(clock.getDelta(), 0.1);
  const t = clock.elapsedTime;
  if (player) player.update(dt, t);
  if (monster) monster.update(dt, t + 3.1);

  renderer.setRenderTarget(rtColor);
  renderer.setClearColor(0x000000, 0);
  renderer.clear();
  renderer.render(scene, camera);
  scene.overrideMaterial = normalMat;
  renderer.setRenderTarget(rtNormal);
  renderer.clear();
  renderer.render(scene, camera);
  scene.overrideMaterial = null;
  renderer.setRenderTarget(null);
  renderer.clear();
  renderer.render(postScene, postCam);
}
frame();
