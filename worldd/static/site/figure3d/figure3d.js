// figure3d — 071 Labs: the 3D climber in the profile portrait slot.
// Isolated folder. Does not import fight3d. Drop = delete this directory.
//
// A card arrives with <canvas.portrait.figure3d data-figure3d='…'>.
// This module mounts a 100×200 (giant 140×260) 1-bit stage, plays a
// calm idle, and hangs worn gear by the hold grammar: blade on the hip,
// bow on the back, staff in the hand, charm on the neck, boots on the
// feet. Hovering a gear-map slot tints that piece (the one colour
// exception). No WebGL → unhide the fallback <img>.
import * as THREE from "three";
import { GLTFLoader } from "./vendor/GLTFLoader.js";

const BASE = new URL(".", import.meta.url);
const INK = new THREE.Color(0xdfe4ee);
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

function boneMap(root) {
  const B = {};
  root.traverse((o) => {
    if (!o.isBone) return;
    B[o.name] = o;
  });
  return B;
}

function pickBone(B, names) {
  for (const n of names) {
    if (B[n]) return B[n];
    const k = Object.keys(B).find((x) => x.toLowerCase() === n.toLowerCase());
    if (k) return B[k];
  }
  return null;
}

function shadowify(o) {
  o.traverse((c) => { if (c.isMesh) c.castShadow = true; });
}

function liftMesh(o, amt = 0.08) {
  o.traverse((m) => {
    if (!m.isMesh || !m.material) return;
    m.material = m.material.clone();
    if (m.material.emissive) {
      m.material.emissive.set(0xffffff);
      m.material.emissiveIntensity = amt;
    }
    m.userData.baseEmissive = m.material.emissive
      ? m.material.emissive.clone() : new THREE.Color(0x000000);
    m.userData.baseEmissiveInt = m.material.emissiveIntensity || 0;
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

// long-axis normalize + grip, same idea as fight3d.equipTripo
function wrapProp(src, { len = 0.8, grip = 0.5, rot = [0, 0, 0],
                         pos = [0, 0, 0] } = {}, bone) {
  const model = src.clone ? src.clone(true) : src;
  shadowify(model);
  liftMesh(model, 0.10);
  model.updateMatrixWorld(true);
  const pts = [];
  model.traverse((m) => {
    if (!m.isMesh || !m.geometry?.attributes?.position) return;
    const posA = m.geometry.attributes.position;
    for (let i = 0; i < posA.count; i += 5) {
      pts.push(new THREE.Vector3().fromBufferAttribute(posA, i)
        .applyMatrix4(m.matrixWorld));
    }
  });
  const inner = new THREE.Group();
  if (pts.length >= 2) {
    const centroid = pts.reduce((a, p) => a.add(p), new THREE.Vector3())
      .divideScalar(pts.length);
    let A = pts[0], best = -1;
    for (const p of pts) {
      const d = p.distanceToSquared(centroid);
      if (d > best) { best = d; A = p; }
    }
    let B = pts[0]; best = -1;
    for (const p of pts) {
      const d = p.distanceToSquared(A);
      if (d > best) { best = d; B = p; }
    }
    const axis = B.clone().sub(A).normalize();
    if (axis.y < 0) axis.negate();
    inner.quaternion.setFromUnitVectors(axis, new THREE.Vector3(0, 1, 0));
  }
  inner.add(model);
  const nbox = new THREE.Box3().setFromObject(inner);
  const nlen = Math.max(0.01, nbox.max.y - nbox.min.y);
  const boneScale = bone ? (bone.getWorldScale(new THREE.Vector3()).y || 1) : 1;
  const s = len / nlen / boneScale;
  inner.position.y = -(nbox.min.y + grip * nlen);
  const gripG = new THREE.Group();
  gripG.add(inner);
  gripG.scale.setScalar(s);
  const wrap = new THREE.Group();
  wrap.quaternion.setFromEuler(new THREE.Euler(...rot));
  wrap.position.set(...pos);
  wrap.add(gripG);
  return wrap;
}

const HOLD = {
  blade: {
    bones: ["L_Thigh", "LeftUpLeg", "Hips"],
    len: 0.90, grip: 0.12, rot: [0.15, 0.2, 1.55], pos: [0.11, 0.04, 0.07],
  },
  bladeR: {
    bones: ["R_Thigh", "RightUpLeg", "Hips"],
    len: 0.90, grip: 0.12, rot: [0.15, -0.2, -1.55], pos: [-0.11, 0.04, 0.07],
  },
  bow: {
    bones: ["Spine02", "Spine01", "Spine"],
    len: 1.20, grip: 0.50, rot: [0.15, 1.15, 0.35], pos: [0.02, 0.06, -0.14],
  },
  staff: {
    bones: ["R_Hand", "RightHand"],
    len: 1.40, grip: 0.42, rot: [0.05, 0, -0.1], pos: [0.06, 0.02, 0.08],
  },
  staffBack: {
    bones: ["Spine02", "Spine01"],
    len: 1.35, grip: 0.50, rot: [0.1, 0.4, 0.2], pos: [-0.08, 0.04, -0.12],
  },
  shield: {
    bones: ["L_Forearm", "LeftForeArm", "L_Hand"],
    len: 0.50, grip: 0.50, rot: [1.15, 0.2, 0.1], pos: [0.02, 0.06, 0.05],
  },
  focus: {
    bones: ["L_Hand", "LeftHand"],
    len: 0.16, grip: 0.50, rot: [0, 0, 0], pos: [0.03, 0.03, 0.05],
  },
  armor: {
    bones: ["Spine02", "Spine01", "Spine"],
    len: 0.48, grip: 0.50, rot: [0, 0, 0], pos: [0, 0.02, 0.07],
  },
  shoes: {
    bones: ["L_Foot", "LeftFoot"],
    len: 0.18, grip: 0.30, rot: [0.2, 0, 0], pos: [0, 0.02, 0.04],
  },
  shoesR: {
    bones: ["R_Foot", "RightFoot"],
    len: 0.18, grip: 0.30, rot: [0.2, 0, 0], pos: [0, 0.02, 0.04],
  },
  charm: {
    bones: ["Neck", "Head", "Spine02"],
    len: 0.11, grip: 0.50, rot: [0, 0, 0], pos: [0, -0.03, 0.07],
  },
  potion: {
    bones: ["Hips", "Spine"],
    len: 0.15, grip: 0.50, rot: [0.2, 0, 0.25], pos: [0.12, 0.02, 0.05],
  },
};

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
        float shade = floor(smoothstep(0.03, 0.95, lum) * 6.0 + 0.5) / 6.0;
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
  const pxPerUnit = H / 2.55;
  const VH = H / pxPerUnit;
  const camera = new THREE.OrthographicCamera(
    -VH * (W / H) / 2, VH * (W / H) / 2, VH / 2, -VH / 2, 0.1, 80);
  const target = new THREE.Vector3(0, 1.05, 0);
  camera.position.set(0.55, 1.45, 8.5);
  camera.lookAt(target);
  // plant feet near the bottom of the frame
  for (let i = 0; i < 4; i++) {
    camera.updateMatrixWorld(true);
    const p = new THREE.Vector3(0, 0, 0).project(camera);
    const want = 1 - 2 * 0.93;
    camera.position.y += (p.y - want) * VH / 2;
    target.y += (p.y - want) * VH / 2;
    camera.lookAt(target);
  }
  scene.add(new THREE.AmbientLight(0xffffff, 0.22));
  const key = new THREE.DirectionalLight(0xffffff, 5.4);
  key.position.set(-4, 7, 6);
  key.castShadow = true;
  scene.add(key);
  scene.add(new THREE.DirectionalLight(0xffffff, 1.1)).position.set(5, 2, 3);

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

function attach(B, src, holdKey, slot) {
  const spec = HOLD[holdKey];
  if (!spec) return null;
  const bone = pickBone(B, spec.bones);
  if (!bone) return null;
  const wrap = wrapProp(src, spec, bone);
  tagSlot(wrap, slot);
  bone.add(wrap);
  return wrap;
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
  const wantH = race === "giant" ? 2.15 : race === "elf" ? 1.95 : 1.78;
  const k = wantH / Math.max(0.1, box.max.y - box.min.y);
  model.scale.setScalar(k);
  model.position.set(
    -(box.min.x + box.max.x) / 2 * k, -box.min.y * k,
    -(box.min.z + box.max.z) / 2 * k);
  const wrap = new THREE.Group();
  wrap.add(model);
  wrap.rotation.y = 0.38;
  wrap.updateMatrixWorld(true);
  const B = boneMap(model);

  const worn = spec.worn || {};
  const paths = spec.paths || {};
  const lead = spec.lead || worn.weapon;
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
      attach(B, src, hold === "bow" ? "bow" : hold, key);
    }
  }
  for (let i = 0; i < blades.length; i++) {
    const src = await loadProp(blades[i].slug, "blade");
    attach(B, src, i === 0 ? "blade" : "bladeR", blades[i].key);
  }
  for (let i = 0; i < staffs.length; i++) {
    const src = await loadProp(staffs[i].slug, "staff");
    attach(B, src, i === 0 ? "staff" : "staffBack", staffs[i].key);
  }
  if (worn.shield) {
    const h = paths[worn.shield] || "shield";
    attach(B, await loadProp(worn.shield, h), h === "focus" ? "focus" : "shield",
           "shield");
  }
  if (worn.armor) {
    attach(B, await loadProp(worn.armor, "armor"), "armor", "armor");
  }
  if (worn.shoes) {
    const boot = await loadProp(worn.shoes, "shoes");
    attach(B, boot, "shoes", "shoes");
    attach(B, boot, "shoesR", "shoes");
  }
  if (worn.charm) {
    const h = paths[worn.charm] || "charm";
    attach(B, await loadProp(worn.charm, h),
           h === "charm" ? "charm" : "potion", "charm");
  }

  gl.scene.add(wrap);
  return { wrap, mixer, B, model };
}

const lives = new Map();   // canvas -> { gl, specKey, figure, raf }

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
      }
    });
  }
}

function tick(L) {
  if (!L || L.dead) return;
  const { gl, figure } = L;
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
  L.raf = requestAnimationFrame(() => tick(L));
}

function drop(canvas) {
  const L = lives.get(canvas);
  if (!L) return;
  L.dead = true;
  cancelAnimationFrame(L.raf);
  lives.delete(canvas);
}

async function mount(host) {
  let spec;
  try { spec = JSON.parse(host.dataset.figure3d || "{}"); }
  catch { spec = {}; }
  const key = host.dataset.figure3d || "";
  const existing = lives.get(host);
  if (existing && existing.specKey === key) return;
  if (existing) drop(host);
  const W = spec.px ? spec.px[0] : (parseInt(host.width, 10) || 100);
  const H = spec.px ? spec.px[1] : (parseInt(host.height, 10) || 200);
  let gl;
  try { gl = createStage(W, H); }
  catch (e) { degrade(host); return; }
  host.replaceWith(gl.canvas);
  gl.canvas.className = host.className;
  gl.canvas.dataset.figure3d = key;
  gl.canvas.width = W;
  gl.canvas.height = H;
  const figure = await buildFigure(gl, spec);
  if (!figure) { degrade(gl.canvas); return; }
  const L = { gl, specKey: key, figure, raf: 0, dead: false };
  lives.set(gl.canvas, L);
  renderFrame(gl);
  L.raf = requestAnimationFrame(() => tick(L));
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
  const obs = new MutationObserver(() => scan(game));
  obs.observe(game, { childList: true, subtree: true });
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", boot);
} else {
  boot();
}

export { createStage, renderFrame, buildFigure, mount };
