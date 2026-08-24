// figure3d — 071 Labs: the 3D climber in the profile portrait slot.
// Own folder; imports only ../lib/sockets.js (plan 079) — never fight3d.
// Drop = delete this directory (lib/sockets.js stays for fight3d).
//
// A card arrives with <canvas.portrait.figure3d data-figure3d='…'>.
// This module mounts a 100×200 (giant 140×260) 1-bit stage, plays a
// calm idle, and hangs worn gear by the hold grammar: blade on the hip,
// bow on the back, staff in the hand, charm on the neck, boots on the
// feet. Hovering a gear-map slot tints that piece (the one colour
// exception). No WebGL → unhide the fallback <img>.
import * as THREE from "three";
import { GLTFLoader } from "./vendor/GLTFLoader.js";
import { GRIPS, gripFor, boneMap, attachToSocket } from "../lib/sockets.js";

const BASE = new URL(".", import.meta.url);
// pure white, same ink as the drawn portrait_*.png files (255,255,255)
const INK = new THREE.Color(0xffffff);
// render buffer scale relative to the portrait's px spec (100×200,
// giant 140×260). 1 = native portrait resolution; lower for chunkier
// pixels — CSS upscales either way (image-rendering: pixelated).
const RES = 1;
const SLOT_INK = {
  weapon: 0xf5b825, weapon2: 0xf5b825, weapon3: 0xf5b825,
  charm: 0x45d0c0, armor: 0xdfe4ee, shoes: 0xf26541, shield: 0xa78bfa,
};
const FAMILY = {
  blade: "blade", bow: "bow", staff: "staff",
  shield: "shield", focus: "focus", armor: "armor",
  shoes: "boots", charm: "charm", potion: "charm", item: "charm",
};

const loader = new GLTFLoader();
const cache = {};
const assets = {};

function load(rel) {
  if (!(rel in cache)) {
    cache[rel] = loader.loadAsync(new URL(rel, BASE).href).catch(() => null);
  }
  return cache[rel];
}

function shadowify(o) {
  o.traverse((c) => { if (c.isMesh) c.castShadow = true; });
}

// The 1-bit shader keeps saturated fragments coloured — that exception
// exists ONLY for the hover tint. Tripo textures carry skin/wood colour
// that leaked through it, so every material is forced to greyscale at
// load; the only saturation left in the scene is the hover ink.
const greyTexCache = new Map();

function greyscaleTexture(tex) {
  const img = tex && tex.image;
  if (!img || !img.width || tex.isCompressedTexture) return tex;
  if (greyTexCache.has(tex.uuid)) return greyTexCache.get(tex.uuid);
  const c = document.createElement("canvas");
  c.width = img.width;
  c.height = img.height;
  const ctx = c.getContext("2d");
  ctx.filter = "grayscale(1)";
  ctx.drawImage(img, 0, 0);
  const out = tex.clone();
  out.image = c;
  out.needsUpdate = true;
  greyTexCache.set(tex.uuid, out);
  return out;
}

function liftMesh(o, amt = 0.08) {
  o.traverse((m) => {
    if (!m.isMesh || !m.material) return;
    m.material = m.material.clone();
    if (m.material.map) m.material.map = greyscaleTexture(m.material.map);
    if (m.material.color) {
      const c = m.material.color;
      const l = 0.2126 * c.r + 0.7152 * c.g + 0.0722 * c.b;
      c.setRGB(l, l, l);
    }
    if (m.material.emissive) {
      m.material.emissive.set(0xffffff);
      m.material.emissiveIntensity = amt;
    }
    m.userData.baseEmissive = m.material.emissive
      ? m.material.emissive.clone() : new THREE.Color(0x000000);
    m.userData.baseEmissiveInt = m.material.emissiveIntensity || 0;
    m.userData.baseColor = m.material.color
      ? m.material.color.clone() : null;
  });
}

function tagSlot(o, slot) {
  o.traverse((m) => { if (m.isMesh) m.userData.slot = slot; });
}

function makePlaceholder(hold) {
  const g = new THREE.Group();
  const mat = new THREE.MeshStandardMaterial({
    color: 0xc8cdd6, roughness: 0.7, metalness: 0.05,
    emissive: 0xffffff, emissiveIntensity: 0.08,
  });
  let mesh;
  if (hold === "blade") {
    mesh = new THREE.Mesh(new THREE.BoxGeometry(0.06, 0.95, 0.02), mat);
    mesh.position.y = 0.45;
  } else if (hold === "bow") {
    const t = new THREE.TorusGeometry(0.55, 0.03, 6, 16, Math.PI);
    mesh = new THREE.Mesh(t, mat);
    mesh.rotation.z = Math.PI / 2;
  } else if (hold === "staff") {
    mesh = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.04, 1.4, 6), mat);
    mesh.position.y = 0.7;
  } else if (hold === "shield") {
    mesh = new THREE.Mesh(new THREE.CylinderGeometry(0.28, 0.28, 0.05, 12), mat);
    mesh.rotation.x = Math.PI / 2;
  } else if (hold === "focus") {
    mesh = new THREE.Mesh(new THREE.SphereGeometry(0.08, 10, 8), mat);
  } else if (hold === "armor") {
    mesh = new THREE.Mesh(new THREE.BoxGeometry(0.55, 0.5, 0.22), mat);
  } else if (hold === "shoes") {
    mesh = new THREE.Mesh(new THREE.BoxGeometry(0.12, 0.16, 0.22), mat);
  } else {
    mesh = new THREE.Mesh(new THREE.SphereGeometry(0.06, 8, 6), mat);
  }
  g.add(mesh);
  return g;
}

// All placement lives in lib/sockets.js (plan 079). This scene only
// prepares the prop for its 1-bit look (clone, shadows, greyscale +
// emissive lift) and tags it for the hover map.

function bayerTex() {
  const BAYER8 = [
    0, 32, 8, 40, 2, 34, 10, 42, 48, 16, 56, 24, 50, 18, 58, 26,
    12, 44, 4, 36, 14, 46, 6, 38, 60, 28, 52, 20, 62, 30, 54, 22,
    3, 35, 11, 43, 1, 33, 9, 41, 51, 19, 59, 27, 49, 17, 57, 25,
    15, 47, 7, 39, 13, 45, 5, 37, 63, 31, 55, 23, 61, 29, 53, 21,
  ];
  const data = new Uint8Array(64);
  for (let i = 0; i < 64; i++) data[i] = BAYER8[i] * 4;
  const tex = new THREE.DataTexture(data, 8, 8, THREE.RedFormat);
  tex.minFilter = tex.magFilter = THREE.NearestFilter;
  tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
  tex.needsUpdate = true;
  return tex;
}

function createStage(W, H) {
  // One world scale for every frame: the giant (2.15 units tall) fills
  // his 260px box top to bottom; a 200px box shows the same px-per-unit,
  // so the shorter races stand proportionally smaller, feet on the same
  // baseline. 2.20 leaves ~2% breathing room around the giant.
  const VH = 2.20 * H / 260;
  // W×H is the portrait's display size; the actual buffer is RES× smaller
  W = Math.max(1, Math.round(W * RES));
  H = Math.max(1, Math.round(H * RES));
  const canvas = document.createElement("canvas");
  const renderer = new THREE.WebGLRenderer(
    { canvas, antialias: false, alpha: true });
  renderer.setPixelRatio(1);
  renderer.setSize(W, H, false);
  renderer.setClearColor(0x000000, 0);
  renderer.shadowMap.enabled = true;

  const depthTex = new THREE.DepthTexture(W, H);
  const rtColor = new THREE.WebGLRenderTarget(W, H, {
    minFilter: THREE.NearestFilter, magFilter: THREE.NearestFilter,
    depthTexture: depthTex,
  });
  const rtNormal = new THREE.WebGLRenderTarget(W, H, {
    minFilter: THREE.NearestFilter, magFilter: THREE.NearestFilter,
  });
  const normalMat = new THREE.MeshNormalMaterial();
  const postScene = new THREE.Scene();
  const postCam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
  const postMat = new THREE.ShaderMaterial({
    transparent: true,
    uniforms: {
      tScene: { value: rtColor.texture },
      tNormal: { value: rtNormal.texture },
      tDepth: { value: depthTex },
      tBayer: { value: bayerTex() },
      texel: { value: new THREE.Vector2(1 / W, 1 / H) },
      uInk: { value: INK.clone() },
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
        if (s.a < 0.03) { gl_FragColor = vec4(0.0); return; }
        // hover colour exception: a saturated fragment keeps its ink
        float mx = max(s.r, max(s.g, s.b));
        float mn = min(s.r, min(s.g, s.b));
        if (mx - mn > 0.22 && s.a > 0.5) {
          gl_FragColor = vec4(s.rgb, 1.0); return;
        }
        float d0 = texture2D(tDepth, vUv).x;
        float behind = max(
          max(texture2D(tDepth, vUv + vec2(texel.x, 0.0)).x,
              texture2D(tDepth, vUv - vec2(texel.x, 0.0)).x),
          max(texture2D(tDepth, vUv + vec2(0.0, texel.y)).x,
              texture2D(tDepth, vUv - vec2(0.0, texel.y)).x)) - d0;
        float edge = step(0.010, behind);
        float lum = pow(clamp(dot(s.rgb, vec3(0.2126, 0.7152, 0.0722)),
                              0.0, 1.0), 0.4545);
        // continuous ramp, like the drawn portraits: the Bayer matrix
        // itself draws the gradient. The steep S-curve is the look —
        // lit surfaces saturate to solid white, the shadow side thins
        // to sparse dots, and the midtones roll between them
        float shade = smoothstep(0.28, 0.75, lum);
        float fill = step(t, shade);
        vec3 n = texture2D(tNormal, vUv).xyz * 2.0 - 1.0;
        float rimlit = edge * step(0.25, n.x);
        float hot = step(0.99, shade);
        float edgeInk = edge * step(t, 0.9);
        float on = max(fill * (1.0 - edgeInk), max(rimlit, hot));
        gl_FragColor = vec4(uInk * on, on);
      }`,
  });
  postScene.add(new THREE.Mesh(new THREE.PlaneGeometry(2, 2), postMat));

  const scene = new THREE.Scene();
  const camera = new THREE.OrthographicCamera(
    -VH * (W / H) / 2, VH * (W / H) / 2, VH / 2, -VH / 2, 0.1, 80);
  const target = new THREE.Vector3(0, VH / 2, 0);
  // dead-on, like the drawn portraits — no side offset
  camera.position.set(0, VH / 2 + 0.4, 8.5);
  camera.lookAt(target);
  // plant feet on the bottom edge of the frame
  for (let i = 0; i < 4; i++) {
    camera.updateMatrixWorld(true);
    const p = new THREE.Vector3(0, 0, 0).project(camera);
    const want = 1 - 2 * 0.985;
    camera.position.y += (p.y - want) * VH / 2;
    target.y += (p.y - want) * VH / 2;
    camera.lookAt(target);
  }
  // ONE strong directional key models the volume (1bit-images.md); the
  // fill is just bright enough that the shadow side thins to sparse
  // dither instead of solid black — the drawn-portrait look.
  scene.add(new THREE.AmbientLight(0xffffff, 0.15));
  const key = new THREE.DirectionalLight(0xffffff, 6.0);
  key.position.set(-6, 8, 4);
  key.castShadow = true;
  scene.add(key);
  const fill = new THREE.DirectionalLight(0xffffff, 0.7);
  fill.position.set(5, 2, 3);
  scene.add(fill);

  return { canvas, renderer, rtColor, rtNormal, normalMat, postScene,
           postCam, postMat, scene, camera, clock: new THREE.Clock() };
}

function renderFrame(gl) {
  const { renderer, scene, camera, rtColor, rtNormal, normalMat,
          postScene, postCam } = gl;
  renderer.setRenderTarget(rtColor);
  renderer.render(scene, camera);
  scene.overrideMaterial = normalMat;
  renderer.setRenderTarget(rtNormal);
  renderer.render(scene, camera);
  scene.overrideMaterial = null;
  renderer.setRenderTarget(null);
  renderer.render(postScene, postCam);
}

async function loadProp(slug, hold) {
  const fam = FAMILY[hold] || "charm";
  const own = await load(`models/items/${slug}.glb`);
  if (own) return own.scene;
  const fb = await load(`models/items/${fam}.glb`);
  if (fb) return fb.scene;
  return makePlaceholder(hold);
}

// fig = { B, wrap, h } from buildFigure. Prepares the prop for the 1-bit
// look, then delegates ALL placement to the sockets module.
function equip(fig, src, family, slot) {
  const grip = gripFor(family);
  if (!grip) return null;
  const model = src.clone ? src.clone(true) : src;
  shadowify(model);
  liftMesh(model, grip.lift ?? 0.10);
  const w = attachToSocket({ charRoot: fig.wrap, charHeight: fig.h,
                             boneIndex: fig.B, prop: model, grip });
  if (w) tagSlot(w, slot);
  return w;
}

async function buildFigure(gl, spec) {
  const race = spec.race && ["human", "elf", "giant"].includes(spec.race)
    ? spec.race : "human";
  const gltf = await load(`models/players/${race}.glb`);
  if (!gltf) return null;
  const model = gltf.scene;
  shadowify(model);
  liftMesh(model, 0.07);
  const mixer = new THREE.AnimationMixer(model);
  if (gltf.animations && gltf.animations.length) {
    mixer.clipAction(gltf.animations[0]).play();
  }
  mixer.update(0.033);
  model.scale.setScalar(1);
  model.position.set(0, 0, 0);
  model.updateMatrixWorld(true);
  const box = new THREE.Box3().setFromObject(model);
  // the giant fills his frame; human and elf stand the same height,
  // two (human) head-sizes — 0.5 world units — shorter than him
  const wantH = race === "giant" ? 2.15 : 1.65;
  const k = wantH / Math.max(0.1, box.max.y - box.min.y);
  model.scale.setScalar(k);
  model.position.set(
    -(box.min.x + box.max.x) / 2 * k, -box.min.y * k,
    -(box.min.z + box.max.z) / 2 * k);
  const wrap = new THREE.Group();
  wrap.add(model);
  // the rigs' animated idle faces +x; -90° turns them to the camera,
  // full face like the drawn portraits
  wrap.rotation.y = -Math.PI / 2;
  wrap.updateMatrixWorld(true);
  // centre the faced BODY and keep it inside the frame (gear hangs on
  // bones later — a staff may kiss the edge, like the drawn portraits;
  // fitting the body keeps the giant tall instead of shrinking him to
  // make room for his weapon)
  const rbox = new THREE.Box3().setFromObject(wrap);
  wrap.position.x = -(rbox.min.x + rbox.max.x) / 2;
  wrap.position.z = -(rbox.min.z + rbox.max.z) / 2;
  const frameW = gl.camera.right - gl.camera.left;
  const rw = rbox.max.x - rbox.min.x;
  let rwFinal = rw;
  if (rw > frameW * 0.96) {
    // the giant rig is far wider than his 140×260 frame allows at full
    // height. Slim him (screen-width only; wrap-local z maps to screen x
    // after the -90° turn) up to 25% before uniform-shrinking, so he
    // keeps towering over the human instead of shrinking to fit his arms.
    const need = (frameW * 0.96) / rw;
    const squash = Math.max(need, 0.75);
    wrap.scale.z *= squash;
    wrap.position.x *= squash;
    const fit = Math.min(1, need / squash);
    wrap.scale.multiplyScalar(fit);
    wrap.position.x *= fit;
    wrap.position.z *= fit;
    rwFinal = rw * squash * fit;
  }
  // stand the figure right of centre by 1/8 frame width, but never push
  // the body past the frame edge: a width-fit figure has no slack and
  // stays put
  const slack = Math.max(0, (frameW - rwFinal) / 2 - frameW * 0.02);
  wrap.position.x += Math.min(frameW / 8, slack);
  wrap.updateMatrixWorld(true);
  const fig = { B: boneMap(model), wrap, h: wantH };

  const worn = spec.worn || {};
  const paths = spec.paths || {};
  const blades = [];
  const staffs = [];
  for (const key of ["weapon", "weapon2", "weapon3"]) {
    const slug = worn[key];
    if (!slug) continue;
    const hold = paths[slug] || "blade";
    if (hold === "blade") blades.push({ slug, key });
    else if (hold === "staff") staffs.push({ slug, key });
    else {
      const src = await loadProp(slug, hold);
      equip(fig, src, hold === "bow" ? "bow" : hold, key);
    }
  }
  for (let i = 0; i < blades.length; i++) {
    const src = await loadProp(blades[i].slug, "blade");
    equip(fig, src, i === 0 ? "blade" : "blade_l", blades[i].key);
  }
  for (let i = 0; i < staffs.length; i++) {
    const src = await loadProp(staffs[i].slug, "staff");
    equip(fig, src, i === 0 ? "staff" : "staff_back", staffs[i].key);
  }
  if (worn.shield) {
    const h = paths[worn.shield] || "shield";
    equip(fig, await loadProp(worn.shield, h),
          h === "focus" ? "focus" : "shield", "shield");
  }
  if (worn.armor) {
    equip(fig, await loadProp(worn.armor, "armor"), "armor", "armor");
  }
  if (worn.shoes) {
    const boot = await loadProp(worn.shoes, "shoes");
    equip(fig, boot, "boots_l", "shoes");
    equip(fig, boot, "boots_r", "shoes");
  }
  if (worn.charm) {
    const h = paths[worn.charm] || "charm";
    equip(fig, await loadProp(worn.charm, h),
          h === "charm" ? "charm" : "potion", "charm");
  }

  gl.scene.add(wrap);
  return { wrap, mixer, B: fig.B, model };
}

const lives = new Map();   // canvas -> { gl, specKey, figure, raf }
// harness-only introspection: ?fig3ddebug exposes the live stages so hold
// transforms can be tuned in the console; /play never passes the flag
if (typeof location !== "undefined"
    && location.search.includes("fig3ddebug")) {
  window.fig3dLives = lives;
  window.fig3dTHREE = THREE;
  window.fig3dGRIPS = GRIPS;
}
const FRAME_MS = 1000 / 15; // pixel-art idle does not need display-rate redraws
// mount() replaces the declarative canvas with its WebGL canvas before its
// models finish loading. The game's MutationObserver sees that replacement;
// keep the replacement marked until the async build completes so it does not
// recursively mount itself and monopolise the browser event loop.
const mounting = new WeakSet();

function degrade(host) {
  const fb = host.parentElement
    && host.parentElement.querySelector(".figure3d-fallback");
  if (fb) fb.hidden = false;
  host.style.display = "none";
}

function setHighlight(slot, root) {
  const targets = root
    ? [...lives.entries()].filter(([c]) => root.contains(c)).map(([, L]) => L)
    : [...lives.values()];
  for (const L of targets) {
    if (!L.gl) continue;
    L.gl.scene.traverse((m) => {
      if (!m.isMesh || !m.material || !m.material.emissive) return;
      const on = slot && m.userData.slot === slot;
      if (on) {
        m.material.emissive.setHex(SLOT_INK[slot] || 0xf5b825);
        m.material.emissiveIntensity = 0.95;
        if (m.material.color) m.material.color.setHex(SLOT_INK[slot] || 0xf5b825);
      } else if (m.userData.baseEmissive) {
        m.material.emissive.copy(m.userData.baseEmissive);
        m.material.emissiveIntensity = m.userData.baseEmissiveInt || 0.07;
        if (m.userData.baseColor && m.material.color) {
          m.material.color.copy(m.userData.baseColor);
        }
      }
    });
  }
}

function tick(L, now) {
  if (!L || L.dead) return;
  const { gl, figure } = L;
  if (!gl.canvas.isConnected) {
    drop(gl.canvas);
    return;
  }
  L.raf = requestAnimationFrame((next) => tick(L, next));
  if (now - L.lastFrame < FRAME_MS) return;
  L.lastFrame = now;
  const rect = gl.canvas.getBoundingClientRect();
  if (document.hidden || rect.bottom <= 0 || rect.top >= innerHeight
      || rect.right <= 0 || rect.left >= innerWidth) return;
  const dt = Math.min(gl.clock.getDelta(), 0.05);
  const tt = gl.clock.elapsedTime;
  if (figure) {
    figure.mixer.update(dt);
    const B = figure.B;
    if (B.Spine02) {
      const q = new THREE.Quaternion().setFromAxisAngle(
        new THREE.Vector3(0, 0, 1),
        Math.sin(tt * 1.15) * 0.018 + Math.sin(tt * 0.7) * 0.01);
      B.Spine02.quaternion.multiply(q);
    }
    if (B.Head) {
      const q = new THREE.Quaternion().setFromAxisAngle(
        new THREE.Vector3(0, 1, 0), Math.sin(tt * 0.55) * 0.03);
      B.Head.quaternion.multiply(q);
    }
  }
  renderFrame(gl);
}

function disposeStage(gl, figure) {
  if (!gl) return;
  figure?.mixer?.stopAllAction();
  gl.postScene.traverse((o) => {
    if (o.isMesh) o.geometry?.dispose();
  });
  gl.postMat.uniforms.tBayer.value?.dispose();
  gl.postMat.dispose();
  gl.normalMat.dispose();
  gl.rtColor.dispose();
  gl.rtNormal.dispose();
  gl.scene.clear();
  gl.postScene.clear();
  gl.renderer.dispose();
  gl.renderer.forceContextLoss();
}

function drop(canvas) {
  const L = lives.get(canvas);
  if (!L) return;
  L.dead = true;
  cancelAnimationFrame(L.raf);
  lives.delete(canvas);
  disposeStage(L.gl, L.figure);
}

function dropGone() {
  for (const canvas of [...lives.keys()]) {
    if (!canvas.isConnected) drop(canvas);
  }
}

async function mount(host) {
  if (mounting.has(host)) return;
  let spec;
  try { spec = JSON.parse(host.dataset.figure3d || "{}"); }
  catch { spec = {}; }
  const key = host.dataset.figure3d || "";
  const existing = lives.get(host);
  if (existing && existing.specKey === key) return;
  if (existing) drop(host);
  const W = spec.px ? spec.px[0] : (parseInt(host.width, 10) || 100);
  const H = spec.px ? spec.px[1] : (parseInt(host.height, 10) || 200);
  // Most game acts replace the whole card but leave race and worn gear
  // unchanged. Rebind that live stage during this mutation microtask instead
  // of compiling a fresh WebGL renderer for every selection.
  const reusable = [...lives.entries()].find(([canvas, L]) =>
    !canvas.isConnected && !L.dead && L.specKey === key);
  if (reusable) {
    const [canvas] = reusable;
    host.replaceWith(canvas);
    canvas.className = host.className;
    canvas.dataset.figure3d = key;
    canvas.classList.remove("waiting");
    canvas.classList.add("shown");
    return;
  }
  mounting.add(host);
  let gl;
  try { gl = createStage(W, H); }
  catch (e) {
    mounting.delete(host);
    degrade(host);
    return;
  }
  host.replaceWith(gl.canvas);
  mounting.add(gl.canvas);
  gl.canvas.className = host.className;
  gl.canvas.dataset.figure3d = key;
  // buffer stays at the RES-scaled size createStage picked; CSS upscales
  let figure = null;
  try {
    figure = await buildFigure(gl, spec);
    if (!figure || !gl.canvas.isConnected) {
      degrade(gl.canvas);
      disposeStage(gl, figure);
      return;
    }
    const L = {
      gl, specKey: key, figure, raf: 0, dead: false, lastFrame: 0,
    };
    lives.set(gl.canvas, L);
    // pane.runFX captured the declarative canvas before mount replaced it.
    // Its delayed reveal therefore targets the detached node; carrying the
    // transient `waiting` class onto this canvas would leave it opacity:0
    // forever. The loaded WebGL figure is the completion of that reveal.
    gl.canvas.classList.remove("waiting");
    gl.canvas.classList.add("shown");
    renderFrame(gl);
    L.raf = requestAnimationFrame((now) => tick(L, now));
  } catch (e) {
    degrade(gl.canvas);
    disposeStage(gl, figure);
  } finally {
    mounting.delete(host);
    mounting.delete(gl.canvas);
  }
}

function scan(root) {
  root.querySelectorAll("canvas.figure3d[data-figure3d]").forEach(mount);
}

function bindHover(root) {
  root.addEventListener("mouseover", (e) => {
    const el = e.target.closest && e.target.closest(".gearmap [data-key]");
    if (el) setHighlight(el.getAttribute("data-key"),
                         el.closest(".gearmap")?.parentElement || root);
  });
  root.addEventListener("mouseout", (e) => {
    const el = e.target.closest && e.target.closest(".gearmap [data-key]");
    if (!el) return;
    const to = e.relatedTarget;
    if (to && el.contains(to)) return;
    setHighlight(null, el.closest(".gearmap")?.parentElement || root);
  });
}

function boot() {
  const game = document.getElementById("game") || document.body;
  scan(game);
  bindHover(game);
  const obs = new MutationObserver(() => {
    // scan first: mount() can rebind a compatible stage detached by the same
    // card replacement. Anything still disconnected afterwards is obsolete.
    scan(game);
    dropGone();
  });
  obs.observe(game, { childList: true, subtree: true });
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", boot);
} else {
  boot();
}

function diagnostics() {
  return {
    live: lives.size,
    connected: [...lives.keys()].filter((canvas) => canvas.isConnected).length,
  };
}

export { createStage, renderFrame, buildFigure, mount, diagnostics };
