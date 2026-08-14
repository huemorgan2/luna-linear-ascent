// fight3d — the live 3D kill finisher (PLAN3). Website-only: webplay.py
// injects this module next to funnel.js; the Luna chat card never sees it.
//
// A victory card arrives with data-kill3d='{"id","race","line","breed",
// "specimen","tint"}' on the card div (combat._victory → render.py). This
// module watches #game for such cards, loads the player + monster GLBs on
// demand, mounts a 320x112 canvas over the fx banner, and plays the demo2
// liberation sequence ONCE — strike arc and tempo rolled fresh every kill
// (wild mode), ink colored with the SAME tint the banner mask uses.
//
// Degrade law: no WebGL, a missing GLB, a parse error — do nothing; the
// GIF underneath plays exactly as before this module existed.
//
// Players are Tripo3D-generated rigs (research/3d-fight "3d models"), the
// monsters are Tripo models WITHOUT rigs — walked, lunged and flinched
// procedurally (tripoMonster), which is why quadrupeds are no problem.
import * as THREE from "three";
import { GLTFLoader } from "./vendor/GLTFLoader.js";

const W = 320, H = 112;
const FLOOR_FRAC = 0.91;              // combatants' feet, fraction of H
const PLAYER_YAW = 1.05;              // 3/4 turn toward the monster
const BASE = new URL(".", import.meta.url);

// floor-1 monster registry: normalized height, stance width, start x.
// A creature absent here (or whose GLB 404s) simply keeps its GIF.
const MONSTERS3D = {
  grey_wolf:        { h: 1.70, wide: 1.12, mx: 2.0 },
  feral_boar:       { h: 1.55, wide: 1.10, mx: 2.2 },
  hedge_rat:        { h: 1.05, wide: 1.10, mx: 1.8 },
  lane_wolf:        { h: 1.60, wide: 1.10, mx: 2.1 },
  goblin_straggler: { h: 1.70, wide: 1.05, mx: 2.0 },
  ember_shade:      { h: 2.15, wide: 1.05, mx: 2.3 },
};

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
const KIND_OF = { blade: "slash", bow: "shoot", staff: "cast" };

// motion: always the demo2 "wild" profile — lively secondary action PLUS
// per-kill randomness (strike arc, impact tempo, the monster's own
// attack), so no two finishers read the same.
const AP = () => ({ lean: 1, counter: 1, bob: 1, antic: 1, follow: 1,
                    breathe: 1, squash: 1, vary: 1, knock: 0.9 });

// sword attacks — full-body keyframe tables over the swing phase (impact
// lands at p 0.75). d = world arm/blade aim, y = body lift (+leap /
// -crouch), ln = torso lean (+forward), lg = forward lunge. One is
// rolled at random for every liberation.
const REST = { p: 0, d: [-0.5, 0.15, 0.3], y: 0, ln: 0, lg: 0 };
const STRIKES = {
  overhead: { label: "OVERHEAD", keys: [ REST,
    { p: 0.35, d: [-0.55, 0.55, 0.25], y: -0.06, ln: -0.25, lg: 0 },
    { p: 0.55, d: [0.05, 1, 0.1], y: 0.17, ln: 0.1, lg: 0.1 },
    { p: 0.75, d: [0.6, -0.75, 0], y: 0.07, ln: 0.32, lg: 0.28 },
    { p: 0.92, d: [0.7, -0.55, 0], y: -0.11, ln: 0.24, lg: 0.22 },
    { p: 1.3, d: REST.d, y: 0, ln: 0, lg: 0 } ] },
  back: { label: "BACKSWING", keys: [ REST,
    { p: 0.35, d: [-0.95, 0.1, 0.3], y: -0.04, ln: -0.3, lg: -0.1 },
    { p: 0.62, d: [-0.7, 0.6, 0.35], y: -0.06, ln: -0.38, lg: -0.12 },
    { p: 0.75, d: [1, 0.05, 0], y: 0.02, ln: 0.32, lg: 0.24 },
    { p: 0.95, d: [0.45, -0.35, -0.45], y: -0.05, ln: 0.36, lg: 0.16 },
    { p: 1.3, d: REST.d, y: 0, ln: 0, lg: 0 } ] },
  rising: { label: "RISING", keys: [ REST,
    { p: 0.35, d: [-0.55, -0.5, 0.25], y: -0.17, ln: 0.28, lg: 0.05 },
    { p: 0.62, d: [-0.4, -0.65, 0.2], y: -0.26, ln: 0.38, lg: 0.12 },
    { p: 0.75, d: [0.8, 0.45, 0], y: -0.13, ln: 0.16, lg: 0.3 },
    { p: 0.95, d: [0.45, 0.85, 0], y: 0.06, ln: -0.16, lg: 0.2 },
    { p: 1.3, d: REST.d, y: 0, ln: 0, lg: 0 } ] },
  thrust: { label: "THRUST", keys: [ REST,
    { p: 0.4, d: [-0.85, 0, 0.25], y: -0.06, ln: -0.22, lg: -0.1 },
    { p: 0.68, d: [-0.8, 0.05, 0.2], y: -0.07, ln: -0.24, lg: -0.12 },
    { p: 0.78, d: [1, 0.08, 0], y: -0.03, ln: 0.42, lg: 0.42 },
    { p: 1.0, d: [0.95, 0, 0], y: -0.03, ln: 0.3, lg: 0.3 },
    { p: 1.3, d: REST.d, y: 0, ln: 0, lg: 0 } ] },
};
let curStrike = "overhead";

// ── lazy GL singleton ─────────────────────────────────────────────────────
// Everything WebGL lives here, created ONCE on the first kill card and
// reused forever — innerHTML swaps destroy the canvas's place in the DOM
// but never the canvas or the context.
let GL = null, glBroken = false;

function initGL() {
  if (GL) return GL;
  if (glBroken) return null;
  try {
    const canvas = document.createElement("canvas");
    const renderer = new THREE.WebGLRenderer(
      { canvas, antialias: false, alpha: true });
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
    // the demo2 1-bit post pass with ONE change (PLAN3 Part F): the ink
    // is a uniform, set per kill to the same hex the banner mask tints
    const postMat = new THREE.ShaderMaterial({
      transparent: true,
      uniforms: {
        tScene: { value: rtColor.texture },
        tNormal: { value: rtNormal.texture },
        tDepth: { value: depthTex },
        tBayer: { value: bayerTex },
        texel: { value: new THREE.Vector2(1 / W, 1 / H) },
        uInk: { value: new THREE.Color(0xdfe4ee) },
      },
      vertexShader: `
        varying vec2 vUv;
        void main(){ vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }`,
      fragmentShader: `
        uniform sampler2D tScene, tNormal, tDepth, tBayer;
        uniform vec2 texel;
        uniform vec3 uInk;
        varying vec2 vUv;
        void main(){
          vec4 s = texture2D(tScene, vUv);
          float t = texture2D(tBayer, gl_FragCoord.xy / 8.0).r + 0.002;
          if (s.a < 0.03) {
            // outer silhouette outline: background pixels touching a
            // body ink black so the contour reads on the bright banner
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
          // half-pixel ink: only the NEAR side of a depth step is inked,
          // so contours and interior creases stay one pixel wide
          float d0 = texture2D(tDepth, vUv).x;
          float behind = max(
            max(texture2D(tDepth, vUv + vec2(texel.x, 0.0)).x,
                texture2D(tDepth, vUv - vec2(texel.x, 0.0)).x),
            max(texture2D(tDepth, vUv + vec2(0.0, texel.y)).x,
                texture2D(tDepth, vUv - vec2(0.0, texel.y)).x)) - d0;
          float edge = step(0.010, behind);
          float lum = dot(s.rgb, vec3(0.2126, 0.7152, 0.0722));
          lum = pow(clamp(lum, 0.0, 1.0), 0.4545);
          float shade = smoothstep(0.03, 0.95, lum);
          shade = floor(shade * 6.0 + 0.5) / 6.0;      // 6-step posterize
          float fill = step(t, shade);
          // the kicker's sliver: contour pixels facing the monster (+x)
          // catch the backlight solid instead of ink
          vec3 n = texture2D(tNormal, vUv).xyz * 2.0 - 1.0;
          float rimlit = edge * step(0.30, n.x);
          float hot = step(0.99, shade);
          float edgeInk = edge * step(t, 0.9);
          float on = max(fill * (1.0 - edgeInk), max(rimlit, hot));
          gl_FragColor = vec4(uInk * on, 1.0);
        }`,
    });
    postScene.add(new THREE.Mesh(new THREE.PlaneGeometry(2, 2), postMat));

    const scene = new THREE.Scene();
    const VH = 2.8;
    const camera = new THREE.OrthographicCamera(
      -VH * (W / H) / 2, VH * (W / H) / 2, VH / 2, -VH / 2, 0.1, 120);
    const camTarget = new THREE.Vector3(0, 1.0, 0);
    camera.position.set(0, 2.0, 26);
    camera.lookAt(camTarget);
    // nudge the camera so world y=0 (the feet) lands on the floor line
    for (let i = 0; i < 4; i++) {
      camera.updateMatrixWorld(true);
      const p = new THREE.Vector3(0, 0, 0).project(camera);
      const want = 1 - 2 * FLOOR_FRAC;
      const dy = (p.y - want) * VH / 2;
      camera.position.y += dy; camTarget.y += dy;
      camera.lookAt(camTarget);
      camera.updateMatrixWorld();
    }

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

    GL = { canvas, renderer, rtColor, rtNormal, normalMat, postScene,
           postCam, postMat, scene, camera, clock: new THREE.Clock() };
    Object.assign(canvas.style, {
      position: "absolute", inset: "0", width: "100%", height: "100%",
      imageRendering: "pixelated", zIndex: "1",
    });
    return GL;
  } catch {
    glBroken = true;
    return null;
  }
}

// ── asset loading (on demand, cached, 404 → null) ─────────────────────────
const loader = new GLTFLoader();
const assets = {};                       // buildPlayer's registry
const cache = {};                        // rel path -> Promise<gltf|null>

function load(rel) {
  if (!(rel in cache)) {
    cache[rel] = loader.loadAsync(new URL(rel, BASE).href)
      .catch(() => null);
  }
  return cache[rel];
}

// resolve the spec against what actually exists; null = degrade to GIF
async function ensureFor(spec) {
  const race = SPECIES[spec.race] ? spec.race : "human";
  const line = WEAPONS[spec.line] ? spec.line : "blade";
  const kind = KIND_OF[line];
  const [pg, wg, mg, cg] = await Promise.all([
    load(`players/${race}.glb`), load(`players/${line}.glb`),
    load(`monsters/${spec.id}.glb`), load(`players/${race}_${kind}.glb`),
  ]);
  if (!pg || !wg || !mg) return null;
  assets[`t_${race}`] = pg;
  assets[`w_${line}`] = wg;
  const clips = assets[`t_${race}_clips`] || (assets[`t_${race}_clips`] = {});
  if (!(kind in clips)) clips[kind] = cg ? (cg.animations[0] || null) : null;
  return { race, line, mg };
}

function shadowify(o) {
  o.traverse((c) => { if (c.isMesh) { c.castShadow = true; } });
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
  wrap.rotation.y = PLAYER_YAW;
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

  // hand-keyed bow draw: the arms aim in WORLD space — no per-rig local
  // bone axes to guess. Right arm extends at the monster, left folds
  // back to the cheek on the string.
  let draw = 0, drawTgt = 0;
  const ID_Q = new THREE.Quaternion();
  const AIM = new THREE.Vector3(0.99, 0.1, 0);
  const PULL_U = new THREE.Vector3(-0.9, 0.12, 0.1);
  const PULL_F = new THREE.Vector3(0.85, 0.1, 0.15);

  // hand-keyed sword attacks: each STRIKE is a full-body keyframe table.
  // The wrist cancel pauses during the swing so the blade sweeps with
  // the arm.
  let sw = 0, swTgt = 0, swP = 0;
  let strike = STRIKES[curStrike];
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
  // travel, so a planted foot stays planted and standing still freezes
  // the legs
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
        const c = Math.cos(gaitPh) * Math.sign(dx || 1);
        if (B.L_Calf) swingZ(B.L_Calf, -KNEE * gaitW * Math.max(0, c));
        if (B.R_Calf) swingZ(B.R_Calf, -KNEE * gaitW * Math.max(0, -c));
      }
      if (m.lean && gaitW > 0.01 && B.Spine01) {
        const lean = 0.32
          * Math.min(Math.abs(dx) / Math.max(dt, 1e-4) / 3.5, 1)
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
        aimBone(B.R_Forearm, B.R_Hand, AIM, draw);
        if (B.L_Upperarm && B.L_Forearm && B.L_Hand) {
          aimBone(B.L_Upperarm, B.L_Forearm, PULL_U, draw);
          aimBone(B.L_Forearm, B.L_Hand, PULL_F, draw);
        }
      }
      sw += (swTgt - sw) * Math.min(dt * 10, 1);
      let stY = 0, stLg = 0;
      if (sw > 0.01 && B.R_Upperarm && B.R_Hand) {
        strikeAt(swP);
        const w = Math.min(Math.max(sw, 0), 1);
        aimBone(B.R_Upperarm, B.R_Hand, SP.d, w);
        aimBone(B.R_Forearm, B.R_Hand, SP.d, w);
        if (B.Spine01) swingZ(B.Spine01, SP.ln * 0.6 * w);
        if (B.Spine02) swingZ(B.Spine02, SP.ln * 0.5 * w);
        stY = SP.y * w;
        stLg = SP.lg * w;
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
      // During a strike the cancel PAUSES and the weapon swings with
      // the hand.
      if (weapon && !striking && sw < 0.3) {
        hand.updateWorldMatrix(true, false);
        hand.getWorldQuaternion(liveQ).invert();
        weapon.wrap.quaternion.copy(liveQ).multiply(weapon.want);
      }
    },
    play: (kind) => {
      if (kind === "shoot") { drawTgt = 1; return 1.1; }   // hand-keyed
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
    release: () => { drawTgt = 0; },
    swing: (p) => {
      if (p < 0) { swTgt = 0; return; }
      swP = p;
      swTgt = 1;
    },
    setStrike: (name) => { strike = STRIKES[name] || STRIKES.overhead; },
    idle: () => {
      striking = false;
      drawTgt = 0;
      swTgt = 0;
      sw = 0; swP = 0;
      mixer.stopAllAction();
      if (idleClip) mixer.clipAction(idleClip).reset().play();
    },
  };
}

// ── rigless Tripo monster ─────────────────────────────────────────────────
// The generated creature GLBs carry no skeleton (the Tripo rig preset is
// biped-only) — the kill scene needs only walk-in, one lunge, and the
// death flinch, so the whole body is driven procedurally: gallop bob and
// rock on the way in, a nose-first lunge for its own attack, breathing
// at rest. Black miasma puffs curl off the back exactly like demo2's
// infected forms; the freed pop-in (natives) reuses the same model small
// and bright, no smoke.
function tripoMonster(gltf, { h = 1.6, wide = 1.1, freed = false } = {}) {
  const model = gltf.scene.clone(true);
  shadowify(model);
  model.traverse((m) => {
    if (m.isMesh && m.material?.emissive) {
      m.material = m.material.clone();
      m.material.emissive.set(0xffffff);
      m.material.emissiveIntensity = freed ? 0.30 : 0.06;
    }
  });
  model.updateMatrixWorld(true);
  const box = new THREE.Box3().setFromObject(model);
  const k = h / (box.max.y - box.min.y);
  model.scale.setScalar(k);
  model.position.set(
    -(box.min.x + box.max.x) / 2 * k, -box.min.y * k,
    -(box.min.z + box.max.z) / 2 * k);
  const inner = new THREE.Group();       // procedural motion rides inner
  inner.add(model);
  const wrap = new THREE.Group();
  wrap.add(inner);
  wrap.scale.set(wide, 1, wide);
  const len = (box.max.z - box.min.z) * k;   // body length (model faces ±z)

  const puffs = [];
  let puffAcc = 0;
  const rnd = (a, b) => a + Math.random() * (b - a);
  let mode = "idle";                     // idle | run | attack
  let runPh = 0, atkT = 0;
  return {
    group: wrap,
    update: (dt, t) => {
      // breathe: the ribcage swells; smaller once it is moving
      inner.scale.y = 1 + (mode === "idle" ? 0.025 : 0.008)
        * Math.sin(t * 2.1);
      if (mode === "run") {
        runPh += dt * 11;
        inner.position.y = Math.abs(Math.sin(runPh)) * 0.055 * h;
        inner.rotation.x = 0.055 * Math.sin(runPh);      // gallop rock
      } else if (mode === "attack") {
        atkT += dt;
        const q = Math.min(atkT / 0.28, 1);
        const lunge = Math.sin(q * Math.PI);
        inner.position.z = 0.16 * h * lunge;   // local +z → at the player
        inner.rotation.x = 0.30 * lunge;       // nose-first
        inner.position.y = 0.04 * h * lunge;
      } else {
        inner.position.y *= Math.max(0, 1 - dt * 8);
        inner.rotation.x *= Math.max(0, 1 - dt * 8);
        inner.position.z *= Math.max(0, 1 - dt * 8);
      }
      if (!freed) {
        // the infection smokes: semi-transparent black circles ride up
        // off the back — the post shader turns them into rolling dither
        puffAcc += dt;
        if (puffAcc > 0.11 && puffs.length < 14) {
          puffAcc = 0;
          const p = new THREE.Mesh(new THREE.CircleGeometry(1, 8),
            new THREE.MeshBasicMaterial({ color: 0x000000,
              transparent: true, opacity: 0.45, depthWrite: false }));
          p.rotation.y = Math.PI / 2;    // wrap is yawed -90: face camera
          p.position.set(0.12,
            rnd(0.55, 0.95) * h, rnd(-0.4, 0.4) * len);
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
    // stepSeq speaks the animalRig clip names; map them onto the modes
    setClip: (name) => {
      if (/gallop|run/i.test(name)) { mode = "run"; return true; }
      if (/attack/i.test(name)) { mode = "attack"; atkT = 0; return true; }
      mode = "idle";
      return true;
    },
  };
}

// ── liberation effects (verbatim from demo2) ──────────────────────────────
const WHITE = new THREE.MeshBasicMaterial({ color: 0xffffff });
let effects = [];                       // transient fx; update(dt) -> alive?

function burst(center) {
  const scene = GL.scene;
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

function banishFx(c, h, getX) {
  const scene = GL.scene;
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
  const scene = GL.scene;
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

function magicFx(from, to, dur, onHit) {
  const scene = GL.scene;
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
let player = null, monster = null;
let curWeapon = "blade";
let curFreed = null;                    // () => freed form, natives only
let state = "infected";                 // infected | freed
let seq = null;                         // active liberation timeline
let holdUntil = 0;                      // stop the loop after the pop-in

function resetStage() {
  const scene = GL.scene;
  if (player) { scene.remove(player.group); player = null; }
  if (monster) { scene.remove(monster.group); monster = null; }
  for (const e of effects) e.update(1e3);   // let each fx tear itself down
  effects = [];
  seq = null;
  state = "infected";
  holdUntil = 0;
}

function liberate() {
  if (seq || !monster || !player || state !== "infected") return;
  seq = { t: 0, kind: curWeapon, hit: false, hitAt: 0,
          freedAt: 0, homeX: player.group.position.x, mScale0: null };
  const dur = curWeapon === "blade" ? 0
    : player.play({ bow: "shoot", staff: "cast" }[curWeapon]);
  monster.setClip?.("Gallop");
  seq.mFrom = monster.group.position.x;
  if (curWeapon === "blade") {
    // both close on a contact point; the swing is timed so the blade
    // lands right after the two arrive. The gap scales with the body.
    const mBox = new THREE.Box3().setFromObject(monster.group);
    const noseOff = seq.mFrom - mBox.min.x;
    const sep = Math.min(Math.max(noseOff + 0.7, 0.9), 2.1);
    const cx = seq.homeX + 0.55 * (seq.mFrom - seq.homeX);
    seq.meetP = cx - sep / 2;
    seq.meetM = cx + sep / 2;
    // every kill rolls its own tempo and strike arc
    const impactAt = 0.5 + Math.random() * 0.2;
    const arcs = Object.keys(STRIKES);
    player.setStrike?.(arcs[(Math.random() * arcs.length) | 0]);
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
  seq.mScale0 = (seq.mAtkScale || monster.group.scale).clone();
  seq.mLastX = monster.group.position.x;
  const box = new THREE.Box3().setFromObject(monster.group);
  seq.mH = Math.max(box.max.y - box.min.y, 0.2);
  // impulse knockback: light animals fly, heavy ones barely rock
  seq.knockV = 2.6 * AP().knock * Math.min(2, 2.2 / seq.mH);
  const c = mCenterNow();
  effects.push(burst(c));
  const sq = seq;
  effects.push(banishFx(c, seq.mH, () => sq.mLastX));
}

function stepSeq(dt) {
  const s = seq;
  s.t += dt;
  // the charge: the infected creature runs at the player until impact
  if (state === "infected" && !s.hit && s.meetM !== undefined) {
    const T = s.kind === "blade" ? s.mArriveT : s.chargeT;
    const k = Math.min(s.t / T, 1);
    monster.group.position.x = s.mFrom + (s.meetM - s.mFrom) * k;
    if (k >= 0.97 && !s.mAttacked) {
      s.mAttacked = true;
      s.atkAt = s.t;
      s.mAtkScale = monster.group.scale.clone();
      monster.setClip?.("Attack");
    }
  }
  // anticipation squash: it compresses as it launches its own strike
  if (s.atkAt !== undefined && !s.hit) {
    const q = Math.min((s.t - s.atkAt) / 0.18, 1);
    monster.group.scale.y =
      s.mAtkScale.y * (1 - 0.22 * Math.sin(q * Math.PI));
  }
  if (s.kind === "blade") {
    const k = Math.min(s.t / s.closeT, 1);
    let x = s.homeX + (s.meetP - s.homeX) * k;
    if (s.t > s.impactAt + 0.25) {
      const r = Math.min((s.t - s.impactAt - 0.25) / 0.4, 1);
      x = s.meetP + (s.homeX - s.meetP) * r;
    }
    player.group.position.x = x;
    // phase clock tuned so the swing reads 0.75 (the blow) at impactAt
    const swClock = s.impactAt / 0.75;
    player.swing?.(s.t <= s.impactAt + 0.45 ? s.t / swClock : -1);
    if (!s.hit && s.t >= s.impactAt) impact();
  } else if (s.fireAt !== undefined && s.t >= s.fireAt) {
    s.fireAt = undefined;
    const from = new THREE.Vector3(
      player.group.position.x + 0.5, s.kind === "bow" ? 1.25 : 1.45, 0);
    if (s.kind === "bow") {
      player.release?.();
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
    if (s.knockV) {
      monster.group.position.x += s.knockV * dt;
      s.knockV *= Math.max(0, 1 - dt * 6);
      s.mLastX = monster.group.position.x;
    }
    if (k <= 0) {
      GL.scene.remove(monster.group);
      state = "freed";
      monster = curFreed ? curFreed() : null;
      if (monster) {
        monster.group.position.set(s.mLastX ?? 2.0, 0, 0);
        monster.group.rotation.y += -Math.PI / 2;
        s.freedScale = monster.group.scale.clone();
        monster.group.scale.multiplyScalar(0.001);
        GL.scene.add(monster.group);
      }
      s.freedAt = s.t;
    }
  }
  // …and (natives) the small natural animal pops back to size
  if (state === "freed" && monster) {
    const k = Math.min((s.t - s.freedAt) / 0.25, 1);
    monster.group.scale.copy(s.freedScale).multiplyScalar(Math.max(k, 0.001));
  }
  if (s.t >= s.end && state === "freed") {
    player.group.position.x = s.homeX;
    player.idle();
    seq = null;
    holdUntil = GL.clock.elapsedTime + 1.6;   // let the fx tail finish,
  }                                           // then freeze the frame
}

// ── frame loop (runs only while a kill card is up) ────────────────────────
let raf = 0;

function frame() {
  raf = requestAnimationFrame(frame);
  const { renderer, scene, camera, clock,
          rtColor, rtNormal, normalMat, postScene, postCam } = GL;
  const dt = Math.min(clock.getDelta(), 0.1);
  const t = clock.elapsedTime;
  if (player) player.update(dt, t);
  if (monster) monster.update(dt, t + 3.1);
  if (seq) stepSeq(dt);
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

  if (holdUntil && t >= holdUntil && !effects.length) stopLoop();
}

function startLoop() {
  if (raf) return;
  GL.clock.getDelta();                  // flush the pause out of dt
  frame();
}

function stopLoop() {
  if (raf) cancelAnimationFrame(raf);
  raf = 0;
}

// ── mount lifecycle ───────────────────────────────────────────────────────
async function mountKill(card) {
  card.setAttribute("data-k3d-done", "1");
  let spec;
  try { spec = JSON.parse(card.dataset.kill3d); } catch { return; }
  const reg = spec && MONSTERS3D[spec.id];
  if (!reg) return;
  const slot = card.querySelector(".banner");
  if (!slot) return;
  const got = await ensureFor(spec);    // network first; GL only on success
  if (!got || !card.isConnected) return;
  const gl = initGL();
  if (!gl) return;

  stopLoop();
  resetStage();
  try {
    gl.postMat.uniforms.uInk.value.set(spec.tint || "#dfe4ee");
  } catch { /* bad hex: keep the last ink */ }
  try {
    curWeapon = got.line;
    player = buildPlayer(got.race, got.line);
    player.group.position.set(player.x, 0, 0);
    player.group.rotation.y = PLAYER_YAW;
    gl.scene.add(player.group);
    monster = tripoMonster(got.mg, reg);
    monster.group.position.set(reg.mx, 0, 0);
    monster.group.rotation.y += -Math.PI / 2;   // face the player
    gl.scene.add(monster.group);
    // natives are FREED — the small natural animal steps out; pressed
    // fall and wrongmade are evicted — nothing remains but the banish
    curFreed = spec.breed === "native"
      ? () => tripoMonster(got.mg, { h: reg.h * 0.45, wide: reg.wide,
                                     freed: true })
      : null;
  } catch {
    resetStage();
    return;
  }

  slot.style.position = "relative";
  slot.appendChild(gl.canvas);
  startLoop();
  setTimeout(() => { if (card.isConnected) liberate(); }, 550);
}

const game = document.getElementById("game");
if (game) {
  const scan = () => {
    const card = game.querySelector(".card[data-kill3d]:not([data-k3d-done])");
    if (card) { mountKill(card); return; }
    // the kill card left with an innerHTML swap: the canvas went with
    // it — stop burning frames, keep the GL singleton for the next kill
    if (!game.querySelector(".card[data-kill3d]")) stopLoop();
  };
  new MutationObserver(scan).observe(game, { childList: true, subtree: true });
  scan();
}
