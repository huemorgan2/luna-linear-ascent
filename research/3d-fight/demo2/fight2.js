// 3d-fight demo2 — game-exact 320x112 stage, real rigs, loadout choice.
// Players: Tripo3D-generated characters (../3d models pipeline — textured
// for the 1-bit look, auto-rigged, baked breathing idle), weapons are
// Tripo props attached to the right-hand bone. Species and weapon are
// selectable: elf | giant | human  ×  blade | bow | staff, matching the
// game's event-art matrix. Monsters: rigged Quaternius animals (CC0).
import * as THREE from "three";
import { GLTFLoader } from "./vendor/GLTFLoader.js";
import * as SkeletonUtils from "./vendor/SkeletonUtils.js";

const W = 320, H = 112;
const FLOOR_FRAC = 0.91;              // combatants' feet, fraction of H
const PLAYER_YAW = 1.05;              // 3/4 turn toward the monster

// ── fights (floor 1 — The Fencerows) ──────────────────────────────────────
// Every monster is an aether-infected creature: LARGE, dark, thorn-grown.
// LIBERATE plays the strike; the infection blows away and the small
// natural animal that was inside remains.
const INK = 0x33384a;                    // infected body: dense dark dither
const CLEAN = 0xd2d6e0;                  // liberated body: near-white
const FIGHTS = {
  grey_wolf: {
    name: "Grey wolf",
    monster: () => animalRig("wolf", { h: 1.7, wide: 1.18,
      clip: "Idle_2_HeadLow", color: INK, thorns: 12 }),
    freed: () => animalRig("wolf", { h: 0.85, clip: "Idle_2", color: CLEAN }),
    mx: 2.0, desc: "It has learned that climbers carry meat.",
    freedDesc: "The thorns fall away. A lean grey dog-wolf remains.",
  },
  feral_boar: {
    name: "Feral boar",
    monster: () => animalRig("bull", { h: 1.9, wide: 1.12,
      clip: "Idle_Headlow", color: INK, thorns: 12 }),
    freed: () => animalRig("bull", { h: 1.0, clip: "Idle", color: CLEAN }),
    mx: 2.2, desc: "It charges first and decides why later.",
    freedDesc: "Just a boar again, small and winded.",
  },
  hedge_rat: {
    name: "Hedgerow rat",
    monster: () => animalRig("ratm", { h: 1.05, wide: 1.15,
      clip: "Rat_Idle", color: INK, thorns: 8 }),
    freed: () => animalRig("ratm", { h: 0.42, clip: "Rat_Idle", color: CLEAN }),
    mx: 1.8, desc: "Grown fat on abandoned granaries, teeth first.",
    freedDesc: "A field rat, blinking in the floodlight.",
  },
  lane_wolf: {
    name: "The last pack",
    monster: () => pack(),
    freed: () => animalRig("husky", { h: 0.6, clip: "Idle", color: CLEAN }),
    mx: 2.1, desc: "The steading's own sheepdogs, feral and silent.",
    freedDesc: "One sheepdog left, tail low, waiting for a name.",
  },
  goblin_straggler: {
    name: "Goblin straggler", monster: "goblin",
    freed: () => animalRig("ratm", { h: 0.4, clip: "Rat_Idle", color: CLEAN }),
    mx: 2.0, desc: "Sets its feet behind the sword anyway, and grins.",
    freedDesc: "A hedge rat scurries out of the empty armor.",
  },
  ember_shade: {
    name: "Hedge-wight", monster: () => wightRig(),
    freed: () => animalRig("husky", { h: 0.5, clip: "Idle_2", color: CLEAN }),
    mx: 2.3, desc: "Blackthorn snarled into shoulders and arms.",
    freedDesc: "A pup steps out of the fallen blackthorn.",
  },
  warden: {
    name: "Warden Brackjaw", monster: () => warden(),
    freed: () => animalRig("bull", { h: 0.9, clip: "Idle", color: CLEAN }),
    mx: 2.3, desc: "Servos ticking, it lowers its head to charge.",
    freedDesc: "A young bullock, unarmored and unimpressed.",
  },
};

// players: Tripo3D-generated characters ("3d models" pipeline — textured,
// auto-rigged with mixamo names, baked breathing idle)
const SPECIES = {
  giant: { label: "Giant", key: "t_giant", h: 2.05, x: -2.3 },
  elf:   { label: "Elf",   key: "t_elf",   h: 1.9,  x: -2.1 },
  human: { label: "Human", key: "t_human", h: 1.72, x: -2.1 },
};

// Tripo weapon props. grip: fraction along the long axis where the hand
// holds it; rot/pos are WORLD-space after the long axis is normalized to
// +Y — the frame loop cancels the live hand-bone rotation (it differs per
// rig), so one setting fits all three characters.
const WEAPONS = {
  blade: { label: "Blade", key: "w_blade", len: 0.95, grip: 0.14,
           rot: [0.15, 0, -0.9] },
  bow:   { label: "Bow", key: "w_bow", len: 1.30, grip: 0.50,
           rot: [0, 0, -0.15], pos: [0, 0, 0.14], lift: 0.30 },
  staff: { label: "Staff", key: "w_staff", len: 1.45, grip: 0.45,
           rot: [0, 0, -0.08], pos: [0.10, 0, 0.14] },
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
const postMat = new THREE.ShaderMaterial({
  transparent: true,
  uniforms: {
    tScene: { value: rtColor.texture },
    tNormal: { value: rtNormal.texture },
    tDepth: { value: depthTex },
    tBayer: { value: bayerTex },
    texel: { value: new THREE.Vector2(1 / W, 1 / H) },
    uStyle: { value: 0 },
  },
  vertexShader: `
    varying vec2 vUv;
    void main(){ vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }`,
  fragmentShader: `
    uniform sampler2D tScene, tNormal, tDepth, tBayer;
    uniform vec2 texel;
    uniform float uStyle;
    varying vec2 vUv;
    void main(){
      vec4 s = texture2D(tScene, vUv);
      float t = texture2D(tBayer, gl_FragCoord.xy / 8.0).r + 0.002;
      if (s.a < 0.03) {
        // outer silhouette outline: background pixels touching a body
        // ink black so the contour reads against the bright GIF too
        float na = max(
          max(texture2D(tScene, vUv + vec2(texel.x, 0.0)).a,
              texture2D(tScene, vUv - vec2(texel.x, 0.0)).a),
          max(texture2D(tScene, vUv + vec2(0.0, texel.y)).a,
              texture2D(tScene, vUv - vec2(0.0, texel.y)).a));
        if (na > 0.97 && t < 0.9) {
          gl_FragColor = vec4(0.0, 0.0, 0.0, 1.0); return;
        }
        gl_FragColor = vec4(0.0); return;
      }
      if (s.a < 0.97) {
        // shadow catcher: dithered contact shadow, pure black ink
        float on = step(t, s.a * 0.55);
        gl_FragColor = vec4(0.0, 0.0, 0.0, on);
        return;
      }
      // half-pixel ink: only the NEAR side of a depth step gets inked,
      // so contours and interior creases stay one pixel, never a band
      float d0 = texture2D(tDepth, vUv).x;
      float behind = max(
        max(texture2D(tDepth, vUv + vec2(texel.x, 0.0)).x,
            texture2D(tDepth, vUv - vec2(texel.x, 0.0)).x),
        max(texture2D(tDepth, vUv + vec2(0.0, texel.y)).x,
            texture2D(tDepth, vUv - vec2(0.0, texel.y)).x)) - d0;
      float edge = step(0.010, behind);
      // perceptual luminance, gamma lift — keeps the baked texture's
      // tonal separation instead of crushing it to the brightest channel
      float lum = dot(s.rgb, vec3(0.2126, 0.7152, 0.0722));
      lum = pow(clamp(lum, 0.0, 1.0), 0.4545);
      float shade = smoothstep(0.03, 0.95, lum);
      int st = int(uStyle + 0.5);
      // style 0 posterizes to 6 tone steps; every other style keeps the
      // full continuous gradient so the pattern can show finer detail
      if (st == 0) shade = floor(shade * 6.0 + 0.5) / 6.0;
      // graphic styles (dots/lines/hatch/ink) starve under the low-key
      // curve — lift the midtones so their pattern has tone to bite on
      if (st >= 4) shade = smoothstep(0.0, 0.72, lum);
      vec2 px = floor(gl_FragCoord.xy);
      float fill;
      if (st <= 1) {                       // bayer 8x8 (6-step / smooth)
        fill = step(t, shade);
      } else if (st == 2) {                // bayer 4x4 — tighter checker
        vec2 h = mod(px, 2.0), q = mod(floor(px / 2.0), 2.0);
        float b4 = (mod(2.0 * h.x + 3.0 * h.y, 4.0) * 4.0
                  + mod(2.0 * q.x + 3.0 * q.y, 4.0));
        fill = step((b4 + 0.5) / 16.0, shade);
      } else if (st == 3) {                // interleaved gradient noise
        float tn = fract(52.9829189
          * fract(dot(px, vec2(0.06711056, 0.00583715))));
        fill = step(tn + 0.002, shade);
      } else if (st == 4) {                // halftone dot screen
        vec2 c = fract(gl_FragCoord.xy / 4.0) - 0.5;
        fill = step(length(c), sqrt(shade) * 0.75);
      } else if (st == 5) {                // scanlines — row thickness
        fill = step(fract(gl_FragCoord.y / 3.0 + 0.16), shade);
      } else if (st == 6) {                // crosshatch — ink by darkness
        float h = 1.0;
        if (shade < 0.85) h = min(h, step(1.5, mod(px.x + px.y, 6.0)));
        if (shade < 0.60) h = min(h, step(1.5, mod(px.x - px.y + 96.0, 6.0)));
        if (shade < 0.35) h = min(h, step(1.5, mod(px.x + px.y, 3.0)));
        if (shade < 0.12) h = 0.0;
        fill = h;
      } else {                             // hard 2-tone, no dither
        fill = step(0.5, shade);
      }
      // the kicker's sliver: contour pixels whose surface faces the
      // monster (+x in view space) catch the backlight as solid white
      // instead of ink — everything else on the contour stays dark
      vec3 n = texture2D(tNormal, vUv).xyz * 2.0 - 1.0;
      float rimlit = edge * step(0.30, n.x);
      float hot = step(0.99, shade);
      // dithered outline: 90% of contour pixels ink, the rest show body
      float edgeInk = edge * step(t, 0.9);
      float on = max(fill * (1.0 - edgeInk), max(rimlit, hot));
      gl_FragColor = vec4(vec3(on), 1.0);
    }`,
});
postScene.add(new THREE.Mesh(new THREE.PlaneGeometry(2, 2), postMat));

// selectable motion systems — animation-principle experiments.
// keyed: the plain keyframed overlays. lively: anticipation, follow-
// through, torso lean, arm counter-swing, breathing, squash & stretch.
// physics: spring-damper joints (underdamped tracking = natural whip
// and overshoot) plus size-scaled impulse knockback. wild: lively plus
// per-liberation randomness — strike arc, timing, monster reaction.
const ANIMS = {
  keyed: { label: "KEYED" },
  lively: { label: "LIVELY", lean: 1, counter: 1, bob: 1, antic: 1,
    follow: 1, breathe: 1, squash: 1, knock: 0.7 },
  physics: { label: "PHYSICS", lean: 1, counter: 1, bob: 1, spring: 1,
    breathe: 1, knock: 1.3, rear: 1 },
  wild: { label: "WILD", lean: 1, counter: 1, bob: 1, antic: 1,
    follow: 1, breathe: 1, squash: 1, vary: 1, knock: 0.9 },
};
let animMode = "lively";
const AP = () => ANIMS[animMode];

// selectable sword attacks — full-body keyframe tables over the swing
// phase (impact lands at p 0.75). Each key: d = world arm/blade aim,
// y = body lift (+leap / -crouch), ln = torso lean (+forward),
// lg = forward lunge along the facing. wild mode rolls one per fight.
const REST = { p: 0, d: [-0.5, 0.15, 0.3], y: 0, ln: 0, lg: 0 };
const STRIKES = {
  overhead: { label: "OVERHEAD", keys: [ REST,
    // gather low, blade back — then leap and pierce down from the top
    { p: 0.35, d: [-0.55, 0.55, 0.25], y: -0.06, ln: -0.25, lg: 0 },
    { p: 0.55, d: [0.05, 1, 0.1], y: 0.17, ln: 0.1, lg: 0.1 },
    { p: 0.75, d: [0.6, -0.75, 0], y: 0.07, ln: 0.32, lg: 0.28 },
    { p: 0.92, d: [0.7, -0.55, 0], y: -0.11, ln: 0.24, lg: 0.22 },
    { p: 1.3, d: REST.d, y: 0, ln: 0, lg: 0 } ] },
  back: { label: "BACKSWING", keys: [ REST,
    // the arm sweeps far behind the back, torso twists away, then the
    // whole body whips the blade through level
    { p: 0.35, d: [-0.95, 0.1, 0.3], y: -0.04, ln: -0.3, lg: -0.1 },
    { p: 0.62, d: [-0.7, 0.6, 0.35], y: -0.06, ln: -0.38, lg: -0.12 },
    { p: 0.75, d: [1, 0.05, 0], y: 0.02, ln: 0.32, lg: 0.24 },
    { p: 0.95, d: [0.45, -0.35, -0.45], y: -0.05, ln: 0.36, lg: 0.16 },
    { p: 1.3, d: REST.d, y: 0, ln: 0, lg: 0 } ] },
  rising: { label: "RISING", keys: [ REST,
    // slide down into a deep crouch, rip the blade up from below,
    // then get back up
    { p: 0.35, d: [-0.55, -0.5, 0.25], y: -0.17, ln: 0.28, lg: 0.05 },
    { p: 0.62, d: [-0.4, -0.65, 0.2], y: -0.26, ln: 0.38, lg: 0.12 },
    { p: 0.75, d: [0.8, 0.45, 0], y: -0.13, ln: 0.16, lg: 0.3 },
    { p: 0.95, d: [0.45, 0.85, 0], y: 0.06, ln: -0.16, lg: 0.2 },
    { p: 1.3, d: REST.d, y: 0, ln: 0, lg: 0 } ] },
  thrust: { label: "THRUST", keys: [ REST,
    // coil the arm straight back, then a long lunging pierce
    { p: 0.4, d: [-0.85, 0, 0.25], y: -0.06, ln: -0.22, lg: -0.1 },
    { p: 0.68, d: [-0.8, 0.05, 0.2], y: -0.07, ln: -0.24, lg: -0.12 },
    { p: 0.78, d: [1, 0.08, 0], y: -0.03, ln: 0.42, lg: 0.42 },
    { p: 1.0, d: [0.95, 0, 0], y: -0.03, ln: 0.3, lg: 0.3 },
    { p: 1.3, d: REST.d, y: 0, ln: 0, lg: 0 } ] },
};
let curStrike = "random";     // "random": roll a fresh arc every LIBERATE

// selectable 1-bit shading techniques — uStyle picks the fill pattern
const SHADES = {
  bayer6: { label: "BAYER 6", style: 0 },
  bayer: { label: "BAYER ∞", style: 1 },
  bayer4: { label: "BAYER 4", style: 2 },
  noise: { label: "NOISE", style: 3 },
  dots: { label: "DOTS", style: 4 },
  scan: { label: "SCANLINE", style: 5 },
  hatch: { label: "HATCH", style: 6 },
  ink: { label: "INK", style: 7 },
};

// ── scene, side camera, key light ─────────────────────────────────────────
const scene = new THREE.Scene();

const VH = 2.8;                        // world units of view height (zoomed)
const camera = new THREE.OrthographicCamera(
  -VH * (W / H) / 2, VH * (W / H) / 2, VH / 2, -VH / 2, 0.1, 120);
const camTarget = new THREE.Vector3(0, 1.0, 0);
camera.position.set(0, 2.0, 26);       // slight tilt: ground catches shadows
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

// low-key split: the key sits on the MONSTER side (+x, barely in front)
// so the facing half of the body is lit and the camera-side half falls
// to dark dither; the kicker behind grazes the outline into a
// near-white sliver. Ambient stays a floor, not a fill.
scene.add(new THREE.AmbientLight(0xffffff, 0.18));
const key = new THREE.DirectionalLight(0xffffff, 6.0);
key.position.set(10, 6, 3);
key.castShadow = true;
key.shadow.mapSize.set(1024, 1024);
key.shadow.camera.left = -6; key.shadow.camera.right = 6;
key.shadow.camera.top = 6; key.shadow.camera.bottom = -2;
key.shadow.camera.near = 2; key.shadow.camera.far = 40;
key.shadow.bias = -0.002;
scene.add(key);
const rim = new THREE.DirectionalLight(0xffffff, 10.0);
rim.position.set(9, 5, -3);
scene.add(rim);

const catcher = new THREE.Mesh(
  new THREE.PlaneGeometry(24, 10),
  new THREE.ShadowMaterial({ opacity: 0.85 }));
catcher.rotateX(-Math.PI / 2);
catcher.receiveShadow = true;
scene.add(catcher);

// ── asset loading ─────────────────────────────────────────────────────────
const loader = new GLTFLoader();
const assets = {};

async function loadAssets() {
  const [bm, pm, ual, sword,
         tg, te, th, wb, wo, ws,
         wolf, bull, husky, ratm, husky2, husky3] =
    await Promise.all([
      loader.loadAsync("./assets/base/Superhero_Male_FullBody.gltf"),
      loader.loadAsync("./assets/outfits/Male_Peasant.gltf"),
      loader.loadAsync("./assets/anims/UAL1_Standard.glb"),
      loader.loadAsync("./assets/weapons/sword_1handed.gltf"),
      loader.loadAsync("./assets/tripo/giant.glb"),
      loader.loadAsync("./assets/tripo/elf.glb"),
      loader.loadAsync("./assets/tripo/human.glb"),
      loader.loadAsync("./assets/tripo/blade.glb"),
      loader.loadAsync("./assets/tripo/bow.glb"),
      loader.loadAsync("./assets/tripo/staff.glb"),
      loader.loadAsync("./assets/Wolf.glb"),
      loader.loadAsync("./assets/Bull.glb"),
      loader.loadAsync("./assets/Husky.glb"),
      loader.loadAsync("./assets/Rat.glb"),
      loader.loadAsync("./assets/Husky.glb"),
      loader.loadAsync("./assets/Husky.glb"),
    ]);
  Object.assign(assets, {
    base_m: bm, peasant_m: pm, ual, sword: sword.scene,
    t_giant: tg, t_elf: te, t_human: th,
    w_blade: wb, w_bow: wo, w_staff: ws,
    wolf, bull, husky, ratm, husky2, husky3,
  });
  // optional per-species strike clips (gen_clips.py retargets — same
  // mixamo skeleton, so only the AnimationClip is used); missing files ok
  await Promise.all(Object.values(SPECIES).map(async (sp) => {
    const clips = {};
    await Promise.all(["slash", "shoot", "cast"].map(async (kind) => {
      const name = sp.key.replace(/^t_/, "");
      try {
        const g = await loader.loadAsync(`./assets/tripo/${name}_${kind}.glb`);
        clips[kind] = g.animations[0] || null;
      } catch { clips[kind] = null; }
    }));
    assets[sp.key + "_clips"] = clips;
  }));
}

// flatten everything to flat-color Lambert. The Quaternius "Dark"
// base-color maps dither to solid ink at this size — at ~55px the
// texture is noise anyway; a uniform light grey plus the key light and
// ink edges is what reads (the 1bit-images.md closeup lesson).
function lambertify(root, color = 0xa2a8ba) {
  root.traverse((o) => {
    if (!o.isMesh) return;
    const conv = (m) => {
      const l = new THREE.MeshLambertMaterial({ color });
      if (m.transparent || m.alphaTest > 0) {
        l.alphaTest = Math.max(m.alphaTest || 0, 0.5);
      }
      return l;
    };
    o.material = Array.isArray(o.material)
      ? o.material.map(conv) : conv(o.material);
  });
}

function shadowify(o) {
  o.traverse((c) => { if (c.isMesh) { c.castShadow = true; } });
}

// graft skinned meshes from an outfit/hair gltf onto the base skeleton
function graft(gltf, dstRoot, bones, { skipHood = true } = {}) {
  const src = SkeletonUtils.clone(gltf.scene);
  const grafted = [];
  src.traverse((o) => {
    if (!o.isSkinnedMesh) return;
    if (skipHood && /Head_Hood/i.test(o.name)) return;
    grafted.push(o);
  });
  for (const o of grafted) {
    const mesh = o.clone();
    const newBones = o.skeleton.bones.map((b) => bones[b.name] || b);
    dstRoot.add(mesh);
    mesh.bind(new THREE.Skeleton(newBones, o.skeleton.boneInverses),
              o.bindMatrix);
    mesh.frustumCulled = false;
  }
}

// find the UAL clip and strip tracks for bones the target lacks
function clipFor(root, name) {
  const names = new Set();
  root.traverse((o) => names.add(o.name));
  const src = assets.ual.animations.find((c) => c.name === name);
  if (!src) return null;
  const clip = src.clone();
  clip.tracks = clip.tracks.filter((tr) => names.has(tr.name.split(".")[0]));
  return clip;
}

// attach a Tripo weapon prop to the hand bone. Tripo props often lie
// DIAGONALLY in their bbox, so the true long axis comes from the farthest
// vertex pair, rotated onto +Y; origin moves to the grip point; scale is
// sized in world metres and cancels the bone's world scale.
function equipTripo(handBone, neutralQ, wp) {
  const model = assets[wp.key].scene.clone(true);
  shadowify(model);
  if (wp.lift) model.traverse((m) => {
    if (!m.isMesh) return;
    m.material = m.material.clone();
    m.material.emissive.set(0xffffff);
    m.material.emissiveIntensity = wp.lift;
  });
  model.updateMatrixWorld(true);
  const pts = [];
  model.traverse((m) => {
    if (!m.isMesh) return;
    const pos = m.geometry.attributes.position;
    for (let i = 0; i < pos.count; i += 7)
      pts.push(new THREE.Vector3().fromBufferAttribute(pos, i)
        .applyMatrix4(m.matrixWorld));
  });
  const centroid = pts.reduce((a, p) => a.add(p), new THREE.Vector3())
    .divideScalar(pts.length);
  let A = pts[0], best = -1;
  for (const p of pts) { const d = p.distanceToSquared(centroid);
    if (d > best) { best = d; A = p; } }
  let B = pts[0]; best = -1;
  for (const p of pts) { const d = p.distanceToSquared(A);
    if (d > best) { best = d; B = p; } }
  const axis = B.clone().sub(A).normalize();
  if (axis.y < 0) axis.negate();
  const inner = new THREE.Group();
  inner.quaternion.setFromUnitVectors(axis, new THREE.Vector3(0, 1, 0));
  inner.add(model);
  const nbox = new THREE.Box3().setFromObject(inner);
  const nlen = nbox.max.y - nbox.min.y;
  const boneScale = handBone.getWorldScale(new THREE.Vector3()).y || 1;
  // wp.len is true world metres: boneScale (world) already contains the
  // character normalize k, so k must NOT appear here
  const s = wp.len / nlen / boneScale;
  const gripY = nbox.min.y + wp.grip * nlen;
  const grip = new THREE.Group();                // origin at the grip point
  inner.position.y = -gripY;
  grip.add(inner);
  grip.scale.setScalar(s);
  const invBone = neutralQ.clone().invert();
  const want = new THREE.Quaternion().setFromEuler(new THREE.Euler(...wp.rot));
  const wrap = new THREE.Group();
  wrap.quaternion.copy(invBone).multiply(want);
  if (wp.pos) wrap.position.copy(new THREE.Vector3(...wp.pos)
    .applyQuaternion(invBone).divideScalar(boneScale));
  wrap.add(grip);
  handBone.add(wrap);
  return { wrap, want };
}

function buildPlayer(speciesId, weaponId) {
  const sp = SPECIES[speciesId], wp = WEAPONS[weaponId];
  const src = assets[sp.key];
  const model = src.scene;                       // shared scene, not cloned
  if (model.userData.weaponWrap) {
    model.userData.weaponWrap.removeFromParent();
    model.userData.weaponWrap = null;
  }
  shadowify(model);
  // Tripo bakes dark tones; a flat lift keeps the body out of solid black
  // at 320x112 without killing the key-light falloff
  model.traverse((m) => {
    if (m.isMesh && m.material.emissive) {
      m.material.emissive.set(0xffffff);
      m.material.emissiveIntensity = 0.06;
    }
  });
  const mixer = new THREE.AnimationMixer(model);
  if (src.animations.length) mixer.clipAction(src.animations[0]).play();
  mixer.update(0.033);                   // settle: rest pose ≠ idle pose
  // idempotent normalize against the ANIMATED pose, cached per asset
  model.scale.setScalar(1);
  model.position.set(0, 0, 0);
  model.updateMatrixWorld(true);
  if (!src.userData.dims) {
    src.userData.dims = new THREE.Box3().setFromObject(model);
  }
  const box = src.userData.dims;
  const k = sp.h / (box.max.y - box.min.y);
  model.scale.setScalar(k);
  model.position.set(
    -(box.min.x + box.max.x) / 2 * k, -box.min.y * k,
    -(box.min.z + box.max.z) / 2 * k);
  const wrap = new THREE.Group();
  wrap.add(model);
  wrap.rotation.y = PLAYER_YAW;          // 3/4 view (setPlayer re-asserts)
  wrap.updateMatrixWorld(true);

  let hand = null;
  const B = {};
  model.traverse((o) => {
    if (!o.isBone) return;
    B[o.name] = o;
    if (!hand && /righthand$|hand[._]?r$|r[._]?hand$/i.test(o.name)) hand = o;
  });
  let weapon = null;
  if (hand) {
    const neutralQ = hand.getWorldQuaternion(new THREE.Quaternion());
    weapon = equipTripo(hand, neutralQ, wp);
    model.userData.weaponWrap = weapon.wrap;
  }
  const clips = assets[sp.key + "_clips"] || {};
  const idleClip = src.animations[0] || null;
  let striking = false;
  const liveQ = new THREE.Quaternion();

  // hand-keyed bow draw: the Tripo shoot preset crouches and twists, so
  // the bow instead keeps the idle and aims the arms in WORLD space —
  // no per-rig local bone axes to guess. Right arm extends at the
  // monster, left folds back to the cheek on the string.
  let draw = 0, drawTgt = 0;
  const ID_Q = new THREE.Quaternion();
  const AIM = new THREE.Vector3(0.99, 0.1, 0);
  const PULL_U = new THREE.Vector3(-0.9, 0.12, 0.1);   // elbow straight back
  const PULL_F = new THREE.Vector3(0.85, 0.1, 0.15);   // hand back to cheek

  // hand-keyed sword attacks: each STRIKE is a full-body keyframe table
  // (see module-level STRIKES). The wrist cancel pauses during the swing
  // so the blade sweeps with the arm.
  let sw = 0, swTgt = 0, swP = 0;
  let swVel = 0, dirP = 0, dirVel = 0;   // physics-mode spring state
  let strike = STRIKES[curStrike] || STRIKES.overhead;
  // sampled strike pose: arm direction, body lift (+up/-crouch),
  // torso lean, forward lunge
  const SP = { d: new THREE.Vector3(), y: 0, ln: 0, lg: 0 };
  function strikeAt(p) {
    const K = strike.keys;
    const pm = Math.min(Math.max(p, 0), K[K.length - 1].p);
    let i = 0;
    while (i < K.length - 2 && K[i + 1].p < pm) i++;
    const a = K[i], b = K[i + 1];
    let f = (pm - a.p) / (b.p - a.p || 1);
    f = Math.min(Math.max(f, 0), 1);
    f = f * f * (3 - 2 * f);               // ease each segment
    SP.d.set(a.d[0] + (b.d[0] - a.d[0]) * f,
             a.d[1] + (b.d[1] - a.d[1]) * f,
             a.d[2] + (b.d[2] - a.d[2]) * f).normalize();
    SP.y = a.y + (b.y - a.y) * f;
    SP.ln = a.ln + (b.ln - a.ln) * f;
    SP.lg = a.lg + (b.lg - a.lg) * f;
  }

  // distance-driven gait: the phase advances with the group's actual x
  // travel, so the stance leg's backward swing cancels the body's motion
  // — a planted foot stays planted, and standing still freezes the legs
  let gaitW = 0, gaitPh = 0, lastGX = null;
  const GAIT_A = 0.55, KNEE = 0.9;
  const baseY = model.position.y;
  const baseZ = model.position.z;   // model-local +z = the facing
  const Z_AX = new THREE.Vector3(0, 0, 1);
  let legLen = 0.5;
  if (B.L_Thigh && B.L_Foot) {
    legLen = B.L_Thigh.getWorldPosition(new THREE.Vector3())
      .distanceTo(B.L_Foot.getWorldPosition(new THREE.Vector3()));
  }
  function swingZ(bone, ang) {
    bone.updateWorldMatrix(true, false);
    const rot = new THREE.Quaternion().setFromAxisAngle(Z_AX, ang);
    const ow = bone.getWorldQuaternion(new THREE.Quaternion());
    const pInv = bone.parent.getWorldQuaternion(new THREE.Quaternion())
      .invert();
    bone.quaternion.copy(pInv.multiply(rot.multiply(ow)));
  }
  function aimBone(bone, tip, dir, w) {
    bone.updateWorldMatrix(true, false);
    const from = bone.getWorldPosition(new THREE.Vector3());
    const cur = tip.getWorldPosition(new THREE.Vector3())
      .sub(from).normalize();
    const delta = new THREE.Quaternion()
      .setFromUnitVectors(cur, dir.clone().normalize());
    if (w < 1) delta.slerp(ID_Q, 1 - w);
    const ow = bone.getWorldQuaternion(new THREE.Quaternion());
    const pInv = bone.parent.getWorldQuaternion(new THREE.Quaternion())
      .invert();
    bone.quaternion.copy(pInv.multiply(delta.multiply(ow)));
  }
  return {
    group: wrap, x: sp.x,
    update: (dt, tt = 0) => {
      mixer.update(dt);
      const m = AP();
      const gx = wrap.position.x;
      const dx = lastGX === null ? 0 : gx - lastGX;
      lastGX = gx;
      const moving = Math.abs(dx) > 0.0005;
      gaitW += ((moving ? 1 : 0) - gaitW) * Math.min(dt * 10, 1);
      if (moving) gaitPh += dx / (GAIT_A * legLen);
      if (gaitW > 0.01 && B.L_Thigh && B.R_Thigh) {
        const a = Math.sin(gaitPh) * GAIT_A * gaitW;
        swingZ(B.L_Thigh, a);
        swingZ(B.R_Thigh, -a);
        // the swinging (airborne) leg bends its knee to clear the ground
        const c = Math.cos(gaitPh) * Math.sign(dx || 1);
        if (B.L_Calf) swingZ(B.L_Calf, -KNEE * gaitW * Math.max(0, c));
        if (B.R_Calf) swingZ(B.R_Calf, -KNEE * gaitW * Math.max(0, -c));
      }
      // secondary action: the torso leans into the run, the head
      // counter-rotates to stay level, the free arms counter-swing the
      // legs, the body bobs on each footfall, and idle breath keeps the
      // figure alive between fights
      if (m.lean && gaitW > 0.01 && B.Spine01) {
        const lean = 0.32 * Math.min(Math.abs(dx) / Math.max(dt, 1e-4) / 3.5, 1)
          * Math.sign(dx || 1) * gaitW;
        swingZ(B.Spine01, lean * 0.55);
        if (B.Spine02) swingZ(B.Spine02, lean * 0.45);
        if (B.Head) swingZ(B.Head, -lean * 0.6);
      }
      if (m.counter && gaitW > 0.01) {
        const ca = Math.sin(gaitPh) * 0.4 * gaitW;
        if (B.L_Upperarm && draw < 0.05) swingZ(B.L_Upperarm, -ca);
        if (B.R_Upperarm && sw < 0.05 && draw < 0.05)
          swingZ(B.R_Upperarm, ca * 0.6);
      }
      const bobY = m.bob
        ? Math.abs(Math.cos(gaitPh)) * 0.035 * gaitW : 0;
      if (m.breathe && gaitW < 0.3 && B.Spine02) {
        swingZ(B.Spine02,
          Math.sin(tt * 1.7) * 0.02 + Math.sin(tt * 0.9) * 0.013);
        if (B.Head) swingZ(B.Head, Math.sin(tt * 1.3 + 1) * 0.02);
      }
      draw += (drawTgt - draw) * Math.min(dt * 8, 1);
      if (draw > 0.01 && B.R_Upperarm && B.R_Hand) {
        aimBone(B.R_Upperarm, B.R_Hand, AIM, draw);
        aimBone(B.R_Forearm, B.R_Hand, AIM, draw);   // straighten the elbow
        if (B.L_Upperarm && B.L_Forearm && B.L_Hand) {
          aimBone(B.L_Upperarm, B.L_Forearm, PULL_U, draw);
          aimBone(B.L_Forearm, B.L_Hand, PULL_F, draw);
        }
      }
      // physics mode: the weight and the phase both spring-track their
      // targets, underdamped — the arm whips, overshoots, settles
      const sdt = Math.min(dt, 0.033);
      if (m.spring) {
        swVel += (170 * (swTgt - sw) - 16 * swVel) * sdt;
        sw += swVel * sdt;
        dirVel += (140 * (swP - dirP) - 12 * dirVel) * sdt;
        dirP += dirVel * sdt;
      } else {
        sw += (swTgt - sw) * Math.min(dt * 10, 1);
        dirP = swP;
      }
      let stY = 0, stLg = 0;
      if (sw > 0.01 && B.R_Upperarm && B.R_Hand) {
        strikeAt(dirP);
        const w = Math.min(Math.max(sw, 0), 1);
        aimBone(B.R_Upperarm, B.R_Hand, SP.d, w);
        aimBone(B.R_Forearm, B.R_Hand, SP.d, w);
        // the body follows the blade: lean, crouch/leap, lunge
        if (B.Spine01) swingZ(B.Spine01, SP.ln * 0.6 * w);
        if (B.Spine02) swingZ(B.Spine02, SP.ln * 0.5 * w);
        stY = SP.y * w;
        stLg = SP.lg * w;
        // a crouch bends the knees instead of sinking through the floor
        const cr = Math.max(0, -stY) * 3.5;
        if (cr > 0.01 && B.L_Thigh && B.R_Thigh) {
          swingZ(B.L_Thigh, cr * 0.5);
          swingZ(B.R_Thigh, cr * 0.5);
          if (B.L_Calf) swingZ(B.L_Calf, -cr);
          if (B.R_Calf) swingZ(B.R_Calf, -cr);
        }
      }
      model.position.y = baseY + bobY + stY;
      model.position.z = baseZ + stLg;
      // each rig's idle twists the wrist differently — cancel the live
      // bone rotation so wp.rot stays a WORLD orientation on all three.
      // During a strike the cancel PAUSES: the grip freezes at its last
      // orientation offset and the weapon swings with the hand.
      if (weapon && !striking && sw < 0.3) {
        hand.updateWorldMatrix(true, false);
        hand.getWorldQuaternion(liveQ).invert();
        weapon.wrap.quaternion.copy(liveQ).multiply(weapon.want);
      }
    },
    // strike clips are Tripo retargets fetched by gen_clips.py; without
    // them (0 returned) the procedural dash in stepSeq carries the motion
    play: (kind) => {
      if (kind === "shoot") { drawTgt = 1; return 1.1; }   // hand-keyed draw
      const c = clips[kind];
      if (!c) return 0;
      striking = true;
      mixer.stopAllAction();
      const act = mixer.clipAction(c);
      act.reset();
      act.setLoop(THREE.LoopOnce);
      act.clampWhenFinished = true;
      act.play();
      return c.duration;
    },
    release: () => { drawTgt = 0; },       // the string lets go
    // hand-keyed swing phase from the fight clock; p < 0 lets go
    swing: (p) => {
      if (p < 0) { swTgt = 0; return; }
      swP = p;
      swTgt = 1;
    },
    // pick a strike arc for the coming swing (wild mode varies these)
    setStrike: (name) => { strike = STRIKES[name] || STRIKES.overhead; },
    idle: () => {
      striking = false;
      drawTgt = 0;
      swTgt = 0;
      sw = 0; swVel = 0; swP = 0; dirP = 0; dirVel = 0;
      mixer.stopAllAction();
      if (idleClip) mixer.clipAction(idleClip).reset().play();
    },
  };
}

// the goblin straggler: same base rig as the players, squashed to goblin
// proportions — the KayKit hooded rogue reads as a featureless dome once
// dithered, a real skeleton + Sword_Idle reads as a fighter
function goblinRig() {
  const base = SkeletonUtils.clone(assets.base_m.scene);
  const bones = {};
  base.traverse((o) => { if (o.isBone) bones[o.name] = o; });
  graft(assets.peasant_m, base, bones);
  if (bones.Head) {
    const mat = new THREE.MeshLambertMaterial({ color: INK });
    for (const ex of [-1, 1]) {
      const ear = new THREE.Mesh(new THREE.ConeGeometry(0.032, 0.17, 5), mat);
      ear.position.set(0.1 * ex, 0.05, -0.01);
      ear.rotation.z = -ex * 1.45;
      bones.Head.add(ear);
    }
  }
  lambertify(base, INK);            // infected: dark, dense dither
  if (bones.hand_r) {
    const w = assets.sword.clone();
    lambertify(w, 0x9aa0b0);
    shadowify(w);
    w.position.set(0, 0.09, 0.03);
    w.rotation.set(0, 0, -Math.PI / 2);
    bones.hand_r.add(w);
  }
  const thorn = new THREE.MeshLambertMaterial({ color: 0x14161c });
  const rand = (a, b) => a + Math.random() * (b - a);
  for (const hn of ["Head", "spine_03", "clavicle_l", "clavicle_r",
                    "upperarm_l", "upperarm_r"]) {
    const b = bones[hn];
    if (!b) continue;
    for (let i = 0; i < 2; i++) {
      const th = new THREE.Mesh(
        new THREE.ConeGeometry(rand(0.02, 0.04), rand(0.14, 0.3), 5), thorn);
      th.position.set(rand(-0.05, 0.05), rand(0, 0.06), rand(-0.05, 0.05));
      th.rotation.set(rand(-1.4, 1.4), 0, rand(-1.4, 1.4));
      b.add(th);
    }
  }
  const wrap = new THREE.Group();
  const box = new THREE.Box3().setFromObject(base);
  const k = 1.7 / (box.max.y - box.min.y);   // infected: man-sized goblin
  base.scale.setScalar(k);
  base.position.y = -box.min.y * k;
  wrap.add(base);
  wrap.scale.set(1.35, 1, 1.35);        // squat and wide
  shadowify(wrap);
  const mixer = new THREE.AnimationMixer(base);
  const clip = clipFor(base, "Sword_Idle") || clipFor(base, "Idle_Loop");
  if (clip) mixer.clipAction(clip).play();
  return { group: wrap, update: (dt) => mixer.update(dt) };
}

function wightRig() {
  const base = SkeletonUtils.clone(assets.base_m.scene);
  const bones = {};
  base.traverse((o) => { if (o.isBone) bones[o.name] = o; });
  lambertify(base, INK);
  const thorn = new THREE.MeshLambertMaterial({ color: 0x14161c });
  const rand = (a, b) => a + Math.random() * (b - a);
  const hosts = ["Head", "spine_03", "spine_02", "clavicle_l", "clavicle_r",
                 "upperarm_l", "upperarm_r", "lowerarm_l", "lowerarm_r"];
  for (const hn of hosts) {
    const b = bones[hn];
    if (!b) continue;
    for (let i = 0; i < 4; i++) {
      const th = new THREE.Mesh(
        new THREE.ConeGeometry(rand(0.02, 0.05), rand(0.18, 0.45), 5), thorn);
      th.position.set(rand(-0.05, 0.05), rand(-0.02, 0.08), rand(-0.05, 0.05));
      th.rotation.set(rand(-1.4, 1.4), 0, rand(-1.4, 1.4));
      b.add(th);
    }
  }
  const wrap = new THREE.Group();
  const box = new THREE.Box3().setFromObject(base);
  const k = 2.15 / (box.max.y - box.min.y);
  base.scale.setScalar(k);
  base.position.y = -box.min.y * k;
  wrap.add(base);
  wrap.scale.set(1.15, 1, 1.15);
  shadowify(wrap);
  const mixer = new THREE.AnimationMixer(base);
  const clip = clipFor(base, "Idle_Loop");
  if (clip) mixer.clipAction(clip).play();
  return { group: wrap, update: (dt) => mixer.update(dt) };
}

// rigged Quaternius animal (animals/easy-enemies packs, CC0): real
// quadruped silhouettes replace the demo1 box-primitive monsters.
// color sets the dither density (dark = infected, light = liberated);
// thorns > 0 grows black aether-thorns out of the spine/head bones.
function animalRig(key, { h = 1.0, clip = "Idle", wide = 1, speed = 1,
                          color = 0xa2a8ba, thorns = 0 } = {}) {
  const src = assets[key];
  const model = src.scene;
  lambertify(model, color);
  // idempotent normalize: measure the bind pose ONCE and cache — after the
  // mixer has run, skinned verts sit in an animated pose with this rig's
  // broken bone scales and Box3 collapses to centimeters (k explodes)
  model.scale.setScalar(1);
  model.position.set(0, 0, 0);
  model.updateMatrixWorld(true);
  if (!src.userData.dims) {
    const b = new THREE.Box3().setFromObject(model);
    src.userData.dims = b;
  }
  const box = src.userData.dims;
  const k = h / (box.max.y - box.min.y);
  model.scale.setScalar(k);
  model.position.y = -box.min.y * k;
  const wrap = new THREE.Group();
  wrap.add(model);
  if (thorns > 0) {
    // wrap-space spikes over the back/shoulders: the animal armature bones
    // carry broken scale (same trap as SkeletonUtils.clone), so thorns are
    // placed against the scaled bbox instead — idle sway is small enough
    const mat = new THREE.MeshLambertMaterial({ color: 0x14161c });
    const rand = (a, b) => a + Math.random() * (b - a);
    for (let i = 0; i < thorns; i++) {
      const th = new THREE.Mesh(new THREE.ConeGeometry(
        rand(0.025, 0.05) * h, rand(0.2, 0.45) * h, 5), mat);
      th.userData.thorn = true;
      th.position.set(
        (box.min.x + rand(0.25, 0.75) * (box.max.x - box.min.x)) * k,
        rand(0.5, 0.92) * h,
        (box.min.z + rand(0.2, 0.8) * (box.max.z - box.min.z)) * k);
      th.rotation.set(rand(-0.9, 0.9), 0, rand(-0.6, 0.6));
      wrap.add(th);
    }
  }
  // sinister extras on the infected form (thorns > 0): a burning white
  // aether-eye on the head bone, and black miasma curling off the spine
  const puffs = [];
  let puffAcc = 0;
  if (thorns > 0) {
    let head = null;
    model.traverse((o) => {
      if (!head && o.isBone && /head/i.test(o.name)) head = o;
    });
    if (head) {
      model.updateMatrixWorld(true);
      const bs = head.getWorldScale(new THREE.Vector3()).x || 1;
      const eye = new THREE.Mesh(
        new THREE.SphereGeometry(0.05 * h / (bs * k), 6, 5),
        new THREE.MeshBasicMaterial({ color: 0xffffff }));
      // muzzle-forward (+z model), up, and toward the camera side (+x)
      const wp = head.getWorldPosition(new THREE.Vector3())
        .add(new THREE.Vector3(0.05 * h, 0.04 * h, 0.09 * h));
      eye.position.copy(head.worldToLocal(wp));
      head.add(eye);
    }
  }
  wrap.scale.set(wide, 1, wide);
  shadowify(wrap);
  const mixer = new THREE.AnimationMixer(model);
  const find = (name) =>
    src.animations.find((a) => a.name.split("|").pop() === name);
  const c = find(clip) || src.animations[0];
  let cur = null;
  if (c) { cur = mixer.clipAction(c); cur.timeScale = speed; cur.play(); }
  const rnd = (a, b) => a + Math.random() * (b - a);
  return {
    group: wrap,
    update: (dt) => {
      mixer.update(dt);
      if (thorns > 0) {
        // the infection smokes: semi-transparent black circles ride up
        // off the back — the post shader turns them into rolling dither
        puffAcc += dt;
        if (puffAcc > 0.11 && puffs.length < 14) {
          puffAcc = 0;
          const p = new THREE.Mesh(new THREE.CircleGeometry(1, 8),
            new THREE.MeshBasicMaterial({ color: 0x000000,
              transparent: true, opacity: 0.45, depthWrite: false }));
          p.rotation.y = Math.PI / 2;      // wrap is yawed -90: face camera
          p.position.set(
            (box.min.x + rnd(0.15, 0.85) * (box.max.x - box.min.x)) * k,
            rnd(0.55, 0.95) * h, 0.12);
          p.userData = { life: 0, max: rnd(0.55, 0.85) };
          p.scale.setScalar(0.05 * h);
          wrap.add(p);
          puffs.push(p);
        }
        for (let i = puffs.length - 1; i >= 0; i--) {
          const p = puffs[i];
          p.userData.life += dt;
          const l = p.userData.life / p.userData.max;
          p.scale.setScalar((0.05 + l * 0.22) * h);
          p.position.y += dt * 0.5 * h;
          p.material.opacity = 0.45 * (1 - l);
          if (l >= 1) { wrap.remove(p); puffs.splice(i, 1); }
        }
      }
    },
    // crossfade to another clip by short name (Gallop, Attack, …);
    // silently ignores clips this animal doesn't have
    setClip: (name, { fade = 0.15, timeScale = 1 } = {}) => {
      const clip2 = find(name);
      if (!clip2) return false;
      const next = mixer.clipAction(clip2);
      next.reset();
      next.timeScale = timeScale;
      next.play();
      if (cur && cur !== next) next.crossFadeFrom(cur, fade, false);
      cur = next;
      return true;
    },
  };
}

// ── procedural monsters (carried from demo1) ──────────────────────────────
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
  const head = new THREE.Mesh(
    new THREE.SphereGeometry(boar ? 0.3 : rat ? 0.26 : 0.2, 8, 6), mat);
  headG.add(head);
  const snout = new THREE.Mesh(
    new THREE.BoxGeometry(0.15, 0.13, boar ? 0.22 : 0.42), mat);
  snout.position.set(0, -0.06, boar ? 0.27 : 0.28);
  headG.add(snout);
  if (!boar && !rat) {
    headG.rotation.x = 0.22;
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
    tail = new THREE.Mesh(new THREE.SphereGeometry(1, 7, 6), mat);
    tail.scale.set(0.11, 0.11, 0.42);
    tail.position.set(0, boar ? 0.55 : 0.62, boar ? -0.8 : -0.95);
    tail.rotation.x = boar ? -0.3 : -0.85;
  }
  g.add(tail);
  const legLen = boar ? 0.42 : rat ? 0.4 : 0.55;
  for (const [lx, lz] of [[-0.22, 0.42], [0.22, 0.42],
                          [-0.22, -0.42], [0.22, -0.42]]) {
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
  for (const [dx, dz, ds] of [[0, 0.6, 1], [0.9, -0.7, 0.92],
                              [-0.4, -1.4, 0.85]]) {
    const d = animalRig(["husky", "husky2", "husky3"][dogs.length], {
      h: 1.3 * ds, color: INK, thorns: 7,
      clip: ["Idle_2_HeadLow", "Idle", "Idle_2"][dogs.length],
      speed: 0.9 + 0.15 * dogs.length,
    });
    d.group.position.set(dx, 0, dz);
    d.group.rotation.y = 0.15 * dz;
    g.add(d.group);
    dogs.push(d);
  }
  return { group: g,
           update: (dt, t) => dogs.forEach((d, i) => d.update(dt, t + i * 1.7)),
           setClip: (name, opts) =>
             dogs.map((d) => d.setClip(name, opts)).some(Boolean) };
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
  g.rotation.x = 0.08;
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
  g.scale.multiplyScalar(0.72);
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
  const base = animalRig("bull", { h: 2.1, clip: "Idle_Headlow", speed: 0.7,
                                   color: INK, thorns: 10 });
  const g = base.group;
  const outer = new THREE.Group();
  outer.add(g);
  return {
    group: outer,
    update: (dt, t) => {
      base.update(dt);
      const sweep = Math.sin(t * 0.5);
      g.rotation.y = Math.round(sweep * 5) / 5 * 0.1;   // servo head sweep
    },
  };
}

// ── liberation effects ────────────────────────────────────────────────────
const WHITE = new THREE.MeshBasicMaterial({ color: 0xffffff });
let effects = [];                       // transient fx; update(dt) -> alive?

// magic-removal burst: white sparks thrown out plus an expanding ring
function burst(center) {
  const n = 80;
  const posA = new Float32Array(n * 3);
  const vel = [];
  for (let i = 0; i < n; i++) {
    const a = Math.random() * Math.PI * 2;
    const b = (Math.random() - 0.5) * Math.PI;
    const sp = 1.5 + Math.random() * 3.5;
    vel.push(new THREE.Vector3(
      Math.cos(a) * Math.cos(b) * sp,
      Math.sin(b) * sp * 0.9 + 1.4,
      Math.sin(a) * Math.cos(b) * sp * 0.3));
    posA.set([center.x, center.y, center.z], i * 3);
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.BufferAttribute(posA, 3));
  const pts = new THREE.Points(geo, new THREE.PointsMaterial(
    { color: 0xffffff, size: 4, sizeAttenuation: false }));
  pts.frustumCulled = false;
  const ring = new THREE.Mesh(new THREE.TorusGeometry(1, 0.06, 6, 28), WHITE);
  ring.position.copy(center);
  ring.scale.setScalar(0.15);
  // solid white flash disc — one readable pop at impact even at 320x112
  const flash = new THREE.Mesh(new THREE.CircleGeometry(0.55, 20), WHITE);
  flash.position.copy(center);
  scene.add(pts, ring, flash);
  let life = 0;
  return { update(dt) {
    life += dt;
    flash.scale.setScalar(Math.max(1 - life / 0.16, 0.001));
    flash.visible = life < 0.16;
    for (let i = 0; i < n; i++) {
      vel[i].y -= 4.5 * dt;
      posA[i * 3] += vel[i].x * dt;
      posA[i * 3 + 1] += vel[i].y * dt;
      posA[i * 3 + 2] += vel[i].z * dt;
      if (posA[i * 3 + 1] < 0.02) {
        posA[i * 3 + 1] = 0.02;
        vel[i].y *= -0.4; vel[i].x *= 0.7;
      }
    }
    geo.attributes.position.needsUpdate = true;
    ring.scale.setScalar(0.15 + life * 3.0);
    ring.visible = life < 0.32;
    if (life > 1.0) { scene.remove(pts, ring, flash); return false; }
    return true;
  } };
}

// the banishment: the same magic-dissolve plays over every liberation,
// whatever the weapon — the infection leaves the same way each time.
// A white beam shoots up out of the body and narrows away, sparks rise
// along it, and dark fog (half-alpha → black dither) rolls out low.
function banishFx(c, h, getX) {
  const g = new THREE.Group();
  const beam = new THREE.Mesh(
    new THREE.PlaneGeometry(0.2 * h, 1),
    new THREE.MeshBasicMaterial({ color: 0xffffff }));
  beam.position.z = -0.1;              // behind the freed animal's pop-in
  g.add(beam);
  const N = 40;
  const posA = new Float32Array(N * 3);
  const vel = [];
  for (let i = 0; i < N; i++) {
    posA[i * 3] = (Math.random() - 0.5) * 0.55 * h;
    posA[i * 3 + 1] = Math.random() * 0.5 * h;
    posA[i * 3 + 2] = 0.1;
    vel.push(0.7 + Math.random() * 1.5);
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.BufferAttribute(posA, 3));
  const pts = new THREE.Points(geo, new THREE.PointsMaterial(
    { color: 0xffffff, size: 3, sizeAttenuation: false }));
  pts.frustumCulled = false;
  g.add(pts);
  const fog = [];
  for (let i = 0; i < 9; i++) {
    const f = new THREE.Mesh(new THREE.CircleGeometry(1, 10),
      new THREE.MeshBasicMaterial({ color: 0x000000, transparent: true,
        opacity: 0.45, depthWrite: false }));
    f.position.set((Math.random() - 0.5) * 0.7 * h,
      (0.08 + Math.random() * 0.18) * h, 0.15);
    f.userData = { vx: (Math.random() - 0.5) * 1.3,
      s: 0.09 + Math.random() * 0.1 };
    fog.push(f);
    g.add(f);
  }
  g.position.set(c.x, 0, 0);
  scene.add(g);
  let l = 0;
  return { update(dt) {
    l += dt;
    const x = getX?.();
    if (x != null) g.position.x = x;   // the beam rides the knockback
    const up = Math.min(l / 0.25, 1);
    const bh = (0.5 + 1.9 * up) * h;
    beam.scale.y = bh;
    beam.position.y = bh / 2;
    beam.scale.x = l < 0.5 ? 1 : Math.max(0.001, 1 - (l - 0.5) / 0.3);
    beam.visible = l < 0.8;
    for (let i = 0; i < N; i++) posA[i * 3 + 1] += vel[i] * h * dt * 0.9;
    geo.attributes.position.needsUpdate = true;
    pts.visible = l < 0.9;
    for (const f of fog) {
      f.position.x += f.userData.vx * dt * h * 0.35;
      f.scale.setScalar((f.userData.s + l * 0.4) * h);
      f.material.opacity = 0.45 * Math.max(0, 1 - l / 1.1);
    }
    if (l >= 1.15) { scene.remove(g); return false; }
    return true;
  } };
}

function arrowFx(from, to, dur, onHit) {
  const m = new THREE.Mesh(new THREE.BoxGeometry(0.55, 0.07, 0.07), WHITE);
  m.position.copy(from);
  scene.add(m);
  let t = 0;
  return { update(dt) {
    t += dt;
    const k = Math.min(t / dur, 1);
    m.position.lerpVectors(from, to, k);
    m.position.y += 0.3 * Math.sin(Math.PI * k);   // slight arc
    if (k >= 1) { scene.remove(m); onHit(); return false; }
    return true;
  } };
}

// the cast: a swarm of white sparks snakes from the staff to the target
// (sine-wandering, not a straight line) while semi-transparent smoke
// puffs ride along — the post shader turns partial alpha into black
// dither, so the smoke reads as dark rolling haze around the sparks.
// `to` is a function: the target keeps moving while the spell travels.
function magicFx(from, to, dur, onHit) {
  const N = 90;
  const posA = new Float32Array(N * 3);
  const meta = [];
  for (let i = 0; i < N; i++) {
    meta.push({ t0: (i / N) * dur * 0.7, fl: 0.4 + Math.random() * 0.2,
                ph: Math.random() * Math.PI * 2,
                amp: 0.12 + Math.random() * 0.22 });
    posA.set([from.x, from.y, from.z], i * 3);
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.BufferAttribute(posA, 3));
  const pts = new THREE.Points(geo, new THREE.PointsMaterial(
    { color: 0xffffff, size: 3, sizeAttenuation: false }));
  pts.frustumCulled = false;
  const smokeMat = new THREE.MeshBasicMaterial(
    { color: 0x000000, transparent: true, opacity: 0.5, depthWrite: false });
  const puffs = [];
  const smoke = new THREE.Group();
  scene.add(pts, smoke);
  let t = 0, hit = false, spawnAcc = 0;
  return { update(dt) {
    t += dt;
    const tgt = to();
    for (let i = 0; i < N; i++) {
      const m = meta[i];
      const u = Math.min(Math.max((t - m.t0) / m.fl, 0), 1);
      const wave = Math.sin(u * 9 + m.ph) * m.amp * Math.sin(u * Math.PI);
      posA[i * 3] = from.x + (tgt.x - from.x) * u;
      posA[i * 3 + 1] = from.y + (tgt.y - from.y) * u + wave;
      posA[i * 3 + 2] = from.z + wave * 0.4;
    }
    geo.attributes.position.needsUpdate = true;
    // smoke puffs spawn along the live stream
    spawnAcc += dt;
    if (spawnAcc > 0.05 && t < dur * 0.85) {
      spawnAcc = 0;
      const u = Math.random() * Math.min(t / (dur * 0.6), 1);
      const p = new THREE.Mesh(new THREE.CircleGeometry(1, 10),
        smokeMat.clone());
      p.position.set(from.x + (tgt.x - from.x) * u,
        from.y + (tgt.y - from.y) * u + (Math.random() - 0.5) * 0.2, 0.3);
      p.userData = { life: 0, max: 0.45 + Math.random() * 0.25 };
      p.scale.setScalar(0.08);
      smoke.add(p);
      puffs.push(p);
    }
    for (let i = puffs.length - 1; i >= 0; i--) {
      const p = puffs[i];
      p.userData.life += dt;
      const l = p.userData.life / p.userData.max;
      p.scale.setScalar(0.08 + l * 0.5);
      p.position.y += dt * 0.5;
      p.material.opacity = 0.5 * (1 - l);
      if (l >= 1) { smoke.remove(p); puffs.splice(i, 1); }
    }
    if (!hit && t > dur * 0.55) { hit = true; onHit(); }
    if (t >= dur && !puffs.length) { scene.remove(pts, smoke); return false; }
    return true;
  } };
}

// ── stage control ─────────────────────────────────────────────────────────
let player = null, monster = null, monsterId = null;
let curSpecies = "human", curWeapon = "blade";
let state = "infected";                 // infected | freed
let seq = null;                         // active liberation timeline

export function setFight(id) {
  const f = FIGHTS[id];
  if (!f || (id === monsterId && state === "infected" && !seq)) return;
  if (seq) { seq = null; setPlayer(null, null); }   // cancel mid-sequence
  monsterId = id;
  state = "infected";
  if (monster) scene.remove(monster.group);
  monster = f.monster === "goblin" ? goblinRig() : f.monster();
  monster.group.position.set(f.mx, 0, 0);
  monster.group.rotation.y += -Math.PI / 2;   // face left, side-on
  scene.add(monster.group);
}

// the fight, compressed: the player strikes with the equipped weapon, the
// infection blows off in a removal burst, the natural animal remains.
// (Strike clips per weapon come next from Tripo's retarget presets; until
// then the dash/lunge in stepSeq carries the motion.)
export function liberate() {
  if (seq || !monster || !player || state !== "infected") return;
  const f = FIGHTS[monsterId];
  seq = { t: 0, kind: curWeapon, f, hit: false, hitAt: 0,
          freedAt: 0, homeX: player.group.position.x, mScale0: null };
  const dur = curWeapon === "blade" ? 0
    : player.play({ bow: "shoot", staff: "cast" }[curWeapon]);
  // the infected animal breaks into a charge the moment the player moves
  monster.setClip?.("Gallop") || monster.setClip?.("Rat_Run");
  seq.mFrom = monster.group.position.x;
  if (curWeapon === "blade") {
    // both close on a contact point; the swing is hand-keyed and timed
    // so the blade lands right after the two arrive (closeT < impactAt).
    // The gap scales with the animal's actual body — a rat is met close,
    // a stag at arm's length — so the blade reads as touching every size.
    const mBox = new THREE.Box3().setFromObject(monster.group);
    // the animal faces -x: min.x is its nose. Meet so the nose stops a
    // blade-length short of the player, whatever the animal's build.
    // +0.7: the attack clip lunges the neck past the resting-pose box
    const noseOff = seq.mFrom - mBox.min.x;
    const sep = Math.min(Math.max(noseOff + 0.7, 0.9), 2.1);
    const cx = seq.homeX + 0.55 * (seq.mFrom - seq.homeX);
    seq.meetP = cx - sep / 2;
    seq.meetM = cx + sep / 2;
    // timing: the player arrives FIRST and plants his stance mid-windup;
    // the blade then extends (the strike's own lunge) to meet the animal
    // exactly as it closes — the sword goes out to it, it never walks
    // onto a waiting blade, and its own attack comes too late
    let impactAt = 0.6;
    // wild mode — and the RANDOM strike setting — roll a fresh tempo
    // and arc for every fight, so no two liberations look the same
    if (AP().vary || curStrike === "random") {
      impactAt = 0.5 + Math.random() * 0.2;
      const arcs = Object.keys(STRIKES);
      player.setStrike?.(arcs[(Math.random() * arcs.length) | 0]);
    } else {
      player.setStrike?.(curStrike);
    }
    seq.impactAt = impactAt;
    seq.closeT = impactAt - 0.18;    // the player plants early
    seq.mArriveT = impactAt + 0.02;  // the nose meets the extended blade
    seq.end = impactAt + 1.1;
  } else {
    // the monster charges the archer/caster down — the shot meets it
    seq.meetM = seq.homeX + 1.0;
    seq.chargeT = 1.25;
    seq.fireAt = 0.45;
    seq.end = curWeapon === "bow" ? 1.7 : 1.9;
  }
  if (dur) seq.end = Math.max(seq.end, dur + 0.2);
}

function mCenterNow() {
  return new THREE.Box3().setFromObject(monster.group)
    .getCenter(new THREE.Vector3());
}

function impact() {
  if (!seq || seq.hit) return;
  seq.hit = true;
  seq.hitAt = seq.t;
  // mAtkScale is the pre-squash size — never freeze a mid-squash pose
  seq.mScale0 = (seq.mAtkScale || monster.group.scale).clone();
  seq.mLastX = monster.group.position.x;
  const box = new THREE.Box3().setFromObject(monster.group);
  seq.mH = Math.max(box.max.y - box.min.y, 0.2);
  // impulse knockback: light animals fly, heavy ones barely rock
  seq.knockV = 2.6 * (AP().knock || 0) * Math.min(2, 2.2 / seq.mH);
  const c = mCenterNow();
  effects.push(burst(c));
  const sq = seq;
  effects.push(banishFx(c, seq.mH, () => sq.mLastX));
}

function stepSeq(dt) {
  const s = seq;
  s.t += dt;
  // the charge: the infected animal runs at the player until impact
  if (state === "infected" && !s.hit && s.meetM !== undefined) {
    const T = s.kind === "blade" ? s.mArriveT : s.chargeT;
    const k = Math.min(s.t / T, 1);
    monster.group.position.x = s.mFrom + (s.meetM - s.mFrom) * k;
    // in range of the player: the animal goes for its own strike
    if (k >= 0.97 && !s.mAttacked) {
      s.mAttacked = true;
      s.atkAt = s.t;
      s.mAtkScale = monster.group.scale.clone();
      let order = ["Attack", "Attack_Headbutt", "Rat_Attack"];
      // wild mode: the animal picks its own attack, not always the same
      if (AP().vary) order = order.sort(() => Math.random() - 0.5);
      for (const c of order) if (monster.setClip?.(c)) break;
    }
  }
  // anticipation squash: the animal compresses as it launches its attack
  if (s.atkAt !== undefined && AP().squash && !s.hit) {
    const q = Math.min((s.t - s.atkAt) / 0.18, 1);
    monster.group.scale.y = s.mAtkScale.y * (1 - 0.22 * Math.sin(q * Math.PI));
  }
  if (s.kind === "blade") {
    // run in to the contact point, strike, fall back
    const k = Math.min(s.t / s.closeT, 1);
    let x = s.homeX + (s.meetP - s.homeX) * k;
    if (s.t > s.impactAt + 0.25) {
      const r = Math.min((s.t - s.impactAt - 0.25) / 0.4, 1);
      x = s.meetP + (s.homeX - s.meetP) * r;
    }
    player.group.position.x = x;
    // the hand-keyed swing: phase clock starts with the run, tuned so
    // the phase reads 0.75 (the blow) exactly at impactAt whatever the
    // rolled tempo (see buildPlayer's swing overlay)
    const swClock = s.impactAt / 0.75;
    player.swing?.(s.t <= s.impactAt + 0.45 ? s.t / swClock : -1);
    if (!s.hit && s.t >= s.impactAt) impact();
  } else if (s.fireAt !== undefined && s.t >= s.fireAt) {
    s.fireAt = undefined;
    const from = new THREE.Vector3(
      player.group.position.x + 0.5, s.kind === "bow" ? 1.25 : 1.45, 0);
    if (s.kind === "bow") {
      player.release?.();
      // lead the shot: the monster keeps coming while the arrow flies
      const tgt = mCenterNow();
      tgt.x += (s.meetM - s.mFrom) / s.chargeT * 0.2;
      effects.push(arrowFx(from, tgt, 0.25, impact));
    } else {
      effects.push(magicFx(from, () => mCenterNow(), 0.8, impact));
    }
  }
  // the infected form shrinks away under the burst…
  if (s.hit && state === "infected") {
    const k = 1 - Math.min((s.t - s.hitAt) / 0.3, 1);
    monster.group.scale.copy(s.mScale0).multiplyScalar(Math.max(k, 0.001));
    // the blow carries weight: the body is thrown back as it dissolves,
    // small animals farther than big ones (impulse over mass)
    if (s.knockV) {
      monster.group.position.x += s.knockV * dt;
      s.knockV *= Math.max(0, 1 - dt * 6);
      s.mLastX = monster.group.position.x;
    }
    // physics mode: the animal rears up off its forelegs under the hit.
    // ZYX order makes rotation.z a WORLD-z pitch on top of the yaw
    if (AP().rear) {
      monster.group.rotation.order = "ZYX";
      monster.group.rotation.z =
        -0.5 * Math.sin(Math.min((s.t - s.hitAt) / 0.3, 1) * Math.PI);
    }
    if (k <= 0) {
      scene.remove(monster.group);
      state = "freed";
      monster = s.f.freed ? s.f.freed() : null;
      if (monster) {
        // the animal appears where the infected form fell, not back home
        monster.group.position.set(s.mLastX ?? s.f.mx, 0, 0);
        monster.group.rotation.y += -Math.PI / 2;
        s.freedScale = monster.group.scale.clone();
        monster.group.scale.multiplyScalar(0.001);
        scene.add(monster.group);
      }
      s.freedAt = s.t;
    }
  }
  // …and the natural animal pops back to size
  if (state === "freed" && monster) {
    const k = Math.min((s.t - s.freedAt) / 0.25, 1);
    monster.group.scale.copy(s.freedScale).multiplyScalar(Math.max(k, 0.001));
  }
  if (s.t >= s.end && state === "freed") {
    player.group.position.x = s.homeX;
    player.idle();
    seq = null;
    document.dispatchEvent(new CustomEvent("la-freed",
      { detail: { id: monsterId, desc: s.f.freedDesc } }));
  }
}

export function setPlayer(speciesId, weaponId) {
  curSpecies = speciesId ?? curSpecies;
  curWeapon = weaponId ?? curWeapon;
  if (player) scene.remove(player.group);
  player = buildPlayer(curSpecies, curWeapon);
  player.group.position.set(player.x, 0, 0);
  player.group.rotation.y = PLAYER_YAW;       // 3/4, facing the monster
  scene.add(player.group);
}

// debug helper: tune a weapon's grip live (len/grip/rot/pos/lift), rebuild
export function setGrip(weaponId, opts = {}) {
  Object.assign(WEAPONS[weaponId], opts);
  setPlayer(null, null);
}

export function testAnimal(key, opts = {}) {
  if (monster) scene.remove(monster.group);
  monsterId = "__test";
  monster = opts.raw
    ? { group: assets[key].scene, update: () => {} }
    : animalRig(key, opts);
  monster.group.position.set(2.0, 0, 0);
  monster.group.rotation.y = -Math.PI / 2;
  scene.add(monster.group);
}

export function probe() {
  if (!monster) return null;
  const box = new THREE.Box3().setFromObject(monster.group);
  const info = [];
  monster.group.updateMatrixWorld(true);
  monster.group.traverse((o) => {
    if (!o.isMesh) return;
    const g = o.geometry;
    g.computeBoundingSphere();
    const c = g.boundingSphere.center.clone().applyMatrix4(o.matrixWorld);
    let skinned = null;
    if (o.isSkinnedMesh) {
      const v = new THREE.Vector3().fromBufferAttribute(
        g.attributes.position, 0);
      skinned = o.applyBoneTransform
        ? o.applyBoneTransform(0, v.clone()).toArray().map((x) => +x.toFixed(2))
        : "no-applyBoneTransform";
    }
    info.push({ name: o.name, visible: o.visible, skin: !!o.isSkinnedMesh,
      culled: o.frustumCulled, r: +g.boundingSphere.radius.toFixed(2),
      center: c.toArray().map((x) => +x.toFixed(2)), v0skinned: skinned });
  });
  return { min: box.min.toArray().map((x) => +x.toFixed(2)),
           max: box.max.toArray().map((x) => +x.toFixed(2)), info };
}

export function probePlayer() {
  if (!player) return null;
  const pb = new THREE.Box3().setFromObject(player.group);
  const w = assets[SPECIES[curSpecies].key].scene.userData.weaponWrap;
  const wb = w ? new THREE.Box3().setFromObject(w) : null;
  const sz = (b) => b.getSize(new THREE.Vector3()).toArray()
    .map((x) => +x.toFixed(2));
  const bones = [];
  player.group.traverse((o) => { if (o.isBone) bones.push(o.name); });
  return { player: sz(pb), weapon: wb ? sz(wb) : null,
           weaponLen: wb ? +sz(wb).reduce((a, b) => Math.max(a, b)) : null,
           bones };
}

export function clipNames(key = "ual") {
  return (assets[key]?.animations || []).map((c) => c.name);
}

export function setShade(id) {
  if (SHADES[id]) postMat.uniforms.uStyle.value = SHADES[id].style;
}
export function shades() { return SHADES; }
export function setAnim(id) { if (ANIMS[id]) animMode = id; }
export function anims() { return ANIMS; }
export function setStrike(id) {
  if (id === "random") { curStrike = id; return; }
  if (STRIKES[id]) { curStrike = id; player?.setStrike?.(id); }
}
export function strikes() {
  return { random: { label: "RANDOM" }, ...STRIKES };
}
export function fights() { return FIGHTS; }
export function species() { return SPECIES; }
export function weapons() { return WEAPONS; }

// ── run ───────────────────────────────────────────────────────────────────
await loadAssets();
alignFloor(FLOOR_FRAC);
setPlayer("human", "blade");

const clock = new THREE.Clock();
function frame() {
  requestAnimationFrame(frame);
  const dt = Math.min(clock.getDelta(), 0.1);
  const t = clock.elapsedTime;
  if (player) player.update(dt, t);
  if (monster) monster.update(dt, t + 3.1);
  if (seq) stepSeq(dt);
  // effects may push new effects from inside update (arrow onHit spawns
  // the burst) — collect pushes separately so the filter can't drop them
  const running = effects;
  effects = [];
  effects = running.filter((e) => e.update(dt)).concat(effects);

  renderer.setRenderTarget(rtColor);
  renderer.setClearColor(0x000000, 0);
  renderer.clear();
  renderer.render(scene, camera);
  renderer.setRenderTarget(rtNormal);
  renderer.clear();
  scene.overrideMaterial = normalMat;
  renderer.render(scene, camera);
  scene.overrideMaterial = null;
  renderer.setRenderTarget(null);
  renderer.clear();
  renderer.render(postScene, postCam);
}
frame();
