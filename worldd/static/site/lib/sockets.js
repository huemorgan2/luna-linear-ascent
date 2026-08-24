// sockets — named attachment points for character rigs (plan 079).
//
// The industry pattern (Unreal "skeletal sockets"): a named anchor on the
// skeleton + items whose pivot sits at their grip point. Our Tripo GLBs
// have neither, so this module fakes both:
//   SOCKETS        named anchor -> candidate bone names (one table covers
//                  human/elf/giant — they share a skeleton)
//   normalizeProp  gives a prop the missing pivot convention (grip point
//                  at origin, long axis up / flat face out)
//   attachToSocket snaps a prepared prop onto a socket, oriented and
//                  offset in CHARACTER space (x = character's screen-right
//                  when facing you, y = up, z = facing) — never bone-local,
//                  bone axes twist unpredictably joint to joint; never
//                  world, the fight scene faces sideways.
//   GRIPS          per item family: which socket, how to normalize, how
//                  big (fractions of character height, so a giant's staff
//                  towers with the giant), how to orient.
//
// Both 3D scenes import this; placement knowledge lives here and only here.
import * as THREE from "three";

export const SOCKETS = {
  hand_r:    { bones: ["R_Hand", "RightHand"],
               re: /righthand$|hand[._]?r$|r[._]?hand$/i },
  hand_l:    { bones: ["L_Hand", "LeftHand"],
               re: /lefthand$|hand[._]?l$|l[._]?hand$/i },
  forearm_l: { bones: ["L_Forearm", "LeftForeArm", "L_Hand"] },
  forearm_r: { bones: ["R_Forearm", "RightForeArm", "R_Hand"] },
  hip_r:     { bones: ["R_Thigh", "RightUpLeg", "Hips"] },
  hip_l:     { bones: ["L_Thigh", "LeftUpLeg", "Hips"] },
  back:      { bones: ["Spine02", "Spine01", "Spine"] },
  chest:     { bones: ["Spine02", "Spine01", "Spine"] },
  neck:      { bones: ["Neck", "Head", "Spine02"] },
  waist:     { bones: ["Hips", "Pelvis", "Spine"] },
  foot_l:    { bones: ["L_Foot", "LeftFoot"] },
  foot_r:    { bones: ["R_Foot", "RightFoot"] },
};

// Grip specs per item family. Units are FRACTIONS OF CHARACTER HEIGHT
// (len and offset), so every body size wears the same table. orient is a
// character-space euler; grip is the pivot's fraction along the prop's
// normalized axis (0 = bottom); mode: "long" (Tripo long-axis up),
// "flat" (thin axis faces +z — shields), "none".
// lift is the emissive floor scenes apply so dark props survive their
// tone curves. Per-item overrides shallow-merge over the family entry.
export const GRIPS = {
  blade:   { socket: "hip_r", mode: "long", len: 0.55, grip: 0.15,
             orient: [0.10, 0, -2.95], offset: [-0.085, 0.012, 0.073],
             lift: 0.24 },
  blade_l: { socket: "hip_l", mode: "long", len: 0.55, grip: 0.15,
             orient: [0.10, 0, 2.95], offset: [0.085, 0.012, 0.073],
             lift: 0.24 },
  bow:     { socket: "back", mode: "long", len: 0.73, grip: 0.50,
             orient: [0.15, 0, 0.55], offset: [0, 0.04, -0.085],
             lift: 0.24 },
  staff:   { socket: "hand_r", mode: "long", len: 0.66, grip: 0.40,
             orient: [0, 0, -0.10], offset: [0.056, 0.010, 0.056],
             lift: 0.24 },
  shield:  { socket: "forearm_l", mode: "flat", len: 0.19, grip: 0.50,
             orient: [0.15, 0.45, 0], offset: [0.075, -0.065, 0.060],
             lift: 0.24 },
  focus:   { socket: "hand_l", mode: "long", len: 0.10, grip: 0.50,
             orient: [0, 0, 0], offset: [0.025, 0.018, 0.030],
             lift: 0.24 },
  armor:   { socket: "chest", mode: "long", len: 0.29, grip: 0.50,
             orient: [0, 0, 0], offset: [0, 0.012, 0.042], lift: 0.10 },
  boots_l: { socket: "foot_l", mode: "long", len: 0.11, grip: 0.30,
             orient: [0.2, 0, 0], offset: [0, 0.012, 0.024], lift: 0.10 },
  boots_r: { socket: "foot_r", mode: "long", len: 0.11, grip: 0.30,
             orient: [0.2, 0, 0], offset: [0, 0.012, 0.024], lift: 0.10 },
  charm:   { socket: "neck", mode: "long", len: 0.067, grip: 0.50,
             orient: [0, 0, 0], offset: [0, -0.018, 0.042], lift: 0.10 },
  potion:  { socket: "waist", mode: "long", len: 0.091, grip: 0.50,
             orient: [0.2, 0, 0.25], offset: [0.073, 0.012, 0.030],
             lift: 0.10 },
};

export function gripFor(family, overrides) {
  const base = GRIPS[family];
  if (!base) return null;
  return overrides ? { ...base, ...overrides } : base;
}

export function boneMap(root) {
  const B = {};
  root.traverse((o) => { if (o.isBone) B[o.name] = o; });
  return B;
}

export function resolveBone(B, socketName) {
  const sock = SOCKETS[socketName];
  if (!sock) return null;
  const keys = Object.keys(B);
  for (const n of sock.bones) {
    if (B[n]) return B[n];
    const k = keys.find((x) => x.toLowerCase() === n.toLowerCase());
    if (k) return B[k];
  }
  if (sock.re) {
    const k = keys.find((x) => sock.re.test(x));
    if (k) return B[k];
  }
  return null;
}

// Give a raw prop the pivot convention its GLB lacks: returns a group
// whose origin is the GRIP POINT, axis normalized, centred on ALL three
// axes (an off-centre-authored GLB otherwise lands beside the bone).
// The returned group is unscaled; attachToSocket sizes it.
export function normalizeProp(model, { mode = "long", grip = 0.5 } = {}) {
  model.updateMatrixWorld(true);
  const inner = new THREE.Group();
  if (mode === "flat") {
    // discs: the THINNEST bbox axis is the facing; the "long axis" of a
    // shield is a random diameter and mounts it like a cylinder
    const bb = new THREE.Box3().setFromObject(model);
    const ext = [bb.max.x - bb.min.x, bb.max.y - bb.min.y,
                 bb.max.z - bb.min.z];
    const axes = [new THREE.Vector3(1, 0, 0), new THREE.Vector3(0, 1, 0),
                  new THREE.Vector3(0, 0, 1)];
    inner.quaternion.setFromUnitVectors(axes[ext.indexOf(Math.min(...ext))],
                                        new THREE.Vector3(0, 0, 1));
  } else if (mode === "long") {
    // Tripo props often lie DIAGONALLY in their bbox: the true long axis
    // is the farthest vertex pair, rotated onto +Y
    const pts = [];
    model.traverse((m) => {
      if (!m.isMesh || !m.geometry?.attributes?.position) return;
      const posA = m.geometry.attributes.position;
      for (let i = 0; i < posA.count; i += 5) {
        pts.push(new THREE.Vector3().fromBufferAttribute(posA, i)
          .applyMatrix4(m.matrixWorld));
      }
    });
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
  }
  inner.add(model);
  const nbox = new THREE.Box3().setFromObject(inner);
  const nlen = Math.max(0.01, nbox.max.y - nbox.min.y);
  inner.position.set(
    -(nbox.min.x + nbox.max.x) / 2,
    -(nbox.min.y + grip * nlen),
    -(nbox.min.z + nbox.max.z) / 2);
  const pivot = new THREE.Group();
  pivot.add(inner);
  return { pivot, nlen };
}

// Snap a PREPARED prop (already cloned/lit by the scene) onto a socket.
//   charRoot   the group that faces the character's forward (+z when the
//              figure looks at you) — orientation and offset are read in
//              its frame, so one tuning serves every staging.
//   charHeight world height of the character; grip len/offset scale by it.
// Returns the wrap Group (remove it to unequip), or null without a bone.
export function attachToSocket({ charRoot, charHeight, boneIndex, prop,
                                 grip }) {
  const bone = resolveBone(boneIndex, grip.socket);
  if (!bone) return null;
  const { pivot, nlen } = normalizeProp(prop, grip);
  const boneScale = bone.getWorldScale(new THREE.Vector3()).y || 1;
  pivot.scale.setScalar((grip.len * charHeight) / nlen / boneScale);
  const wrap = new THREE.Group();
  wrap.add(pivot);
  bone.add(wrap);
  bone.updateWorldMatrix(true, false);
  charRoot.updateWorldMatrix(true, false);
  // orient in character space: world = qChar * orient, so local =
  // qBone^-1 * qChar * orient
  const qBone = bone.getWorldQuaternion(new THREE.Quaternion()).invert();
  const qChar = charRoot.getWorldQuaternion(new THREE.Quaternion());
  wrap.quaternion.copy(qBone).multiply(qChar).multiply(
    new THREE.Quaternion().setFromEuler(new THREE.Euler(...grip.orient)));
  // offset in character space -> bone-local, translation-free (linear
  // part only), through whatever scales sit between the two frames
  const toBone = new THREE.Matrix4().copy(bone.matrixWorld).invert()
    .multiply(charRoot.matrixWorld);
  wrap.position.copy(new THREE.Vector3(...grip.offset)
    .multiplyScalar(charHeight / (charRoot.getWorldScale(
      new THREE.Vector3()).y || 1))
    .applyMatrix3(new THREE.Matrix3().setFromMatrix4(toBone)));
  return wrap;
}
