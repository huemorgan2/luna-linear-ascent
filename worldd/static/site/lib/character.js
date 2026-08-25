// character — the ONE player-rig pipeline (plan 080). Both 3D scenes
// (figure3d portrait, fight3d finisher + the arena stage) build their
// climber through this module: the same GLBs out of lib/models/, the same
// settle → normalize → boneMap discipline, and the same dressing loop
// through the sockets grip table. Scene stagecraft — cameras, tone-curve
// shaders, strike choreography, hover tints — stays in the scenes.
//
// Bodies are CLONED per stage (083): a plain .clone() severs skinned
// meshes from their skeletons — which is why 080 shared the scene — but
// sharing meant `Group.add()` re-parented the one body, so two same-race
// figures on a page stole it from each other (the portrait went black).
// SkeletonUtils.clone rebinds the skeleton, so every stage owns its body.
// Geometry/materials stay shared under the clones; scenes that tint
// materials clone them per mesh (the portrait's liftMesh does).
// Props are cloned per wear, as before.
import * as THREE from "three";
import { GLTFLoader } from "./vendor/GLTFLoader.js";
import { clone as cloneSkinned } from "./vendor/SkeletonUtils.js";
import { gripFor, boneMap, attachToSocket } from "./sockets.js";

const MODELS = new URL("models/", import.meta.url);
const loader = new GLTFLoader();
const cache = {};

// cached GLB load against lib/models/ — a 404 resolves null, the scenes
// carry their own degrade paths (fallback PNG / fx reel / family GLB)
export function loadModel(rel) {
  if (!(rel in cache)) {
    cache[rel] = loader.loadAsync(new URL(rel, MODELS).href)
      .catch(() => null);
  }
  return cache[rel];
}

export function shadowify(o) {
  o.traverse((c) => { if (c.isMesh) c.castShadow = true; });
}

// strip everything a previous dress pass hung on the bones — the scene is
// shared across mounts/kills, and a stale wrap would double the gear
export function unequipAll(root) {
  const gone = [];
  root.traverse((o) => { if (o.userData.rigGear) gone.push(o); });
  gone.forEach((o) => o.removeFromParent());
}

// One body pipeline: clone the cached body (083 — skinned-safe, so every
// stage owns its own), play clip 0 so the rig settles into its idle
// stance (rest pose ≠ idle pose), normalize to `height` world units
// against dims cached on the gltf, map the bones.
export function buildRig({ gltf, height }) {
  const model = cloneSkinned(gltf.scene);
  unequipAll(model);
  shadowify(model);
  const mixer = new THREE.AnimationMixer(model);
  if (gltf.animations && gltf.animations.length) {
    mixer.clipAction(gltf.animations[0]).play();
  }
  mixer.update(0.033);
  model.scale.setScalar(1);
  model.position.set(0, 0, 0);
  model.updateMatrixWorld(true);
  if (!gltf.userData.dims) {
    gltf.userData.dims = new THREE.Box3().setFromObject(model);
  }
  const box = gltf.userData.dims;
  const k = height / Math.max(0.1, box.max.y - box.min.y);
  model.scale.setScalar(k);
  model.position.set(
    -(box.min.x + box.max.x) / 2 * k, -box.min.y * k,
    -(box.min.z + box.max.z) / 2 * k);
  return { model, mixer, B: boneMap(model), k };
}

// hold grammar (engine/figure3d.py paths values) -> family fallback GLB
export const FAMILY = {
  blade: "blade", bow: "bow", staff: "staff",
  shield: "shield", focus: "focus", armor: "armor",
  shoes: "boots", charm: "charm", potion: "charm", item: "charm",
};

// last-resort shapes when even the family GLB is missing
export function makePlaceholder(hold) {
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
    mesh = new THREE.Mesh(
      new THREE.CylinderGeometry(0.03, 0.04, 1.4, 6), mat);
    mesh.position.y = 0.7;
  } else if (hold === "shield") {
    mesh = new THREE.Mesh(
      new THREE.CylinderGeometry(0.28, 0.28, 0.05, 12), mat);
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

// own slug GLB -> family fallback GLB -> placeholder shape
export async function loadProp(slug, hold) {
  const fam = FAMILY[hold] || "charm";
  const own = slug ? await loadModel(`items/${slug}.glb`) : null;
  if (own) return own.scene;
  const fb = await loadModel(`items/${fam}.glb`);
  if (fb) return fb.scene;
  return makePlaceholder(hold);
}

// Clone + prepare one prop and hang it on its socket.
//   fig  = { B, wrap, h }   bone map, facing group, world height
//   prep = scene hook lighting the prop for that scene's tone curve
//          (greyscale + hover bookkeeping in the portrait, plain emissive
//          in the fight); receives (model, grip).
export function equipFigure({ fig, src, family, prep = null }) {
  const grip = gripFor(family);
  if (!grip) return null;
  const model = src.clone ? src.clone(true) : src;
  shadowify(model);
  if (prep) prep(model, grip);
  const w = attachToSocket({ charRoot: fig.wrap, charHeight: fig.h,
                             boneIndex: fig.B, prop: model, grip });
  if (w) w.userData.rigGear = true;
  return w;
}

// The worn-gear loop (071 hold grammar): lead blade on the right hip,
// second blade on the left, lead staff in the fist, spare on the back,
// bow slung, shield/focus on the left arm, armor on the chest, boots on
// both feet, charm at the neck / potion on the belt.
//   skip     hold families to leave off (the fight skips charm/potion)
//   exclude  slot keys another system owns (the fight's lead weapon)
//   tag      optional (wrap, slotKey) hook for the portrait's hover map
export async function dressFigure({ fig, worn = {}, paths = {},
                                    skip = [], exclude = [],
                                    prep = null, tag = null }) {
  const put = async (slug, hold, family, slot) => {
    const src = await loadProp(slug, hold);
    const w = equipFigure({ fig, src, family, prep });
    if (w && tag) tag(w, slot);
    return w;
  };
  const blades = [];
  const staffs = [];
  for (const key of ["weapon", "weapon2", "weapon3"]) {
    if (exclude.includes(key)) continue;
    const slug = worn[key];
    if (!slug) continue;
    const hold = paths[slug] || "blade";
    if (skip.includes(hold)) continue;
    if (hold === "blade") blades.push({ slug, key });
    else if (hold === "staff") staffs.push({ slug, key });
    else await put(slug, hold, hold === "bow" ? "bow" : hold, key);
  }
  for (let i = 0; i < blades.length; i++) {
    await put(blades[i].slug, "blade",
              i === 0 ? "blade" : "blade_l", blades[i].key);
  }
  for (let i = 0; i < staffs.length; i++) {
    await put(staffs[i].slug, "staff",
              i === 0 ? "staff" : "staff_back", staffs[i].key);
  }
  if (worn.shield && !exclude.includes("shield")) {
    const h = paths[worn.shield] || "shield";
    if (!skip.includes(h)) {
      await put(worn.shield, h, h === "focus" ? "focus" : "shield",
                "shield");
    }
  }
  if (worn.armor && !exclude.includes("armor") && !skip.includes("armor")) {
    await put(worn.armor, "armor", "armor", "armor");
  }
  if (worn.shoes && !exclude.includes("shoes") && !skip.includes("shoes")) {
    await put(worn.shoes, "shoes", "boots_l", "shoes");
    await put(worn.shoes, "shoes", "boots_r", "shoes");
  }
  if (worn.charm && !exclude.includes("charm")) {
    const h = paths[worn.charm] || "charm";
    if (!skip.includes(h)) {
      await put(worn.charm, h, h === "charm" ? "charm" : "potion", "charm");
    }
  }
}
