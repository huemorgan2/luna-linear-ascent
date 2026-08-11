/* The mechanics ledger — renders mechanics-data.js and runs the fight
   simulator. The sim mirrors engine/combat.py (048): player strikes
   first, the trained rank sets the miss chance and the floor of the
   roll band, chip floor ceil(raw/4), the TYPE_MULT triangle, dodge
   from speed advantage, the bow range ladder (gap>1 draw pays only
   rank-8 hands). */
(function () {
  "use strict";
  const M = window.MECH, C = M.constants;
  const $ = (id) => document.getElementById(id);
  const fmt = (n) => n.toLocaleString("en-US");

  // ── tabs ──────────────────────────────────────────────────────────────
  document.querySelectorAll(".tab").forEach((b) => {
    b.onclick = () => {
      document.querySelectorAll(".tab").forEach((x) =>
        x.classList.toggle("on", x === b));
      document.querySelectorAll(".pane").forEach((p) =>
        p.classList.toggle("on", p.id === "pane-" + b.dataset.pane));
    };
  });

  // ── FLOORS tab ────────────────────────────────────────────────────────
  $("floors-legend").innerHTML =
    "<b>ATK/DEF/HP</b> are the common specimen (runt ×" +
    "0.55 HP … alpha ×2 HP, ×1.2 ATK — table shifts with depth). " +
    "<b>XP/Gold</b> = average per kill before the ±" + C.xpJitterPct +
    "%/±" + C.goldJitterPct + "% roll — both are guaranteed drops, " +
    "there is no coin chance. <b>KILL BAR</b> is the invented number: " +
    "the ladder runs 1–" + C.barMax + ", bar B = level min(B, " +
    C.levelCap + ") in floor-B reference steel (past the level cap the " +
    "climb is gear alone). The kill bar is the lowest bar that wins a " +
    "straight full-HP fight ~" + C.winTargetPct + "% of the time " +
    "(accepted ≥" + C.winAcceptPct + "%), fought at rank-" + C.refRank +
    " hands by the weapon path the creature's TYPE does not counter — " +
    "⚔ blade, ➶ bow (flyers), ✦ staff (armoured shapes). " +
    "<b>RNDS / HP LOST</b> are the " +
    "averages at that bar. Energy allows ~" + C.fightsPerDay +
    " wilds fights per day (1 energy / " + C.energyRegenMin + " min). " +
    "<b>HITS ⚔/➶/✦</b> = attacks to kill it with blade / bow / staff " +
    "at the creature's bar (rank-" + C.refRank + " mean swing, misses " +
    "not counted; — = the path cannot land at all). <b>TYPE</b> is the " +
    "one sign a monster carries: <b>⚡</b> fly (fast — steel cannot " +
    "reach it), <b>⛨</b> armoured (slow — arrows glance, steel " +
    "halves), <b>✧</b> spellguard (slow — magic glances, arrows " +
    "halve), none = plain, every weapon bites full. <b>▣</b> bulwark " +
    "is orthogonal: an elite wall of HP, never a weapon question. " +
    "Floors 1–" + C.earlyCoinFloors + " GOLD carries the young-tower " +
    "bounty (×2.0 fading to ×1.1) — prices and fees do not ride it.";

  const cols = ["MONSTER", "KIND", "TRAITS", "SPAWN%", "ATK", "DEF",
    "HP", "TYPE", "SPD", "HITS ⚔/➶/✦", "XP", "GOLD", "KILL BAR",
    "WIN%", "RNDS", "HP LOST"];
  let html = '<table class="mech"><thead><tr>' + cols.map((c, i) =>
    `<th${i < 3 ? ' class="l"' : ""}>${c}</th>`).join("") +
    "</tr></thead><tbody>";
  const SIGN = {fly: "⚡", armoured: "⛨", magic_resist: "✧", plain: "·"};
  for (const f of M.floors) {
    const bounty = C.earlyCoinMult[f.floor];
    html += `<tr class="floorhead" id="floor-${f.floor}">` +
      `<td colspan="${cols.length}">FLOOR ${f.floor} · ` +
      `${f.zone.toUpperCase()} — ${f.biome} · gate: ${f.gateTown}` +
      (bounty ? ` · young-tower bounty ×${bounty.toFixed(1)}` : "") +
      `</td></tr>`;
    for (const m of f.monsters) {
      const kglyph = {blade: "⚔", bow: "➶", staff: "✦"}[m.killType] || "";
      const kl = m.killLevel === null ? '<td class="hard">—</td>' :
        `<td class="${m.killLevel <= f.floor ? "easy" : "hard"}">` +
        `${m.killLevel}<span class="dim"> ${kglyph}</span></td>`;
      const signs =
        (m.type !== "plain" ?
          `<span title="${m.type}">${SIGN[m.type]}</span>` : "") +
        (m.bulwark ? ` <span title="bulwark">▣</span>` : "");
      const h = (x) => x === null ? "—" : fmt(x);
      const hits = `${h(m.hitsBlade)} / ${h(m.hitsBow)} / ` +
        h(m.hitsStaff);
      html += "<tr>" +
        `<td class="l">${signs ?
          `<span class="signs">${signs}</span>` : ""}${m.name}</td>` +
        `<td class="l dim">${m.kind}</td>` +
        `<td class="l dim">${m.traits.join(" ") || "—"}</td>` +
        `<td>${m.spawnPct}</td><td>${m.atk}</td><td>${m.def}</td>` +
        `<td>${fmt(m.hp)}</td>` +
        `<td>${SIGN[m.type]}</td>` +
        `<td>${m.speed}</td>` +
        `<td>${hits}</td>` +
        `<td>${m.xpAvg}</td><td>${fmt(Math.round(m.goldAvg))}</td>` +
        kl +
        `<td>${m.killLevel === null ? "0" : m.killPct}</td>` +
        `<td>${m.killLevel === null ? "—" : m.killRounds}</td>` +
        `<td>${m.killLevel === null ? "—" : m.killHpLost}</td>` +
        "</tr>";
    }
    const w = f.warden;
    html += `<tr class="warden"><td class="l">⚑ ${w.name} (Warden)</td>` +
      `<td class="l">boss</td><td class="l">—</td><td>—</td>` +
      `<td>${w.atk}</td><td>${w.def}</td><td>${fmt(w.hp)}</td>` +
      `<td colspan="3">—</td><td>${w.xp}</td><td>${fmt(w.gold)}</td>` +
      `<td colspan="4">energy 3 + 3/strike</td></tr>`;
  }
  $("floors-table").innerHTML = html + "</tbody></table>";

  $("floor-jump").onchange = function () {
    const el = $("floor-" + this.value);
    if (el) el.scrollIntoView({ behavior: "smooth" });
  };

  // ── LEVELS tab ────────────────────────────────────────────────────────
  $("levels-legend").innerHTML =
    "<b>XP NEED</b> = round(24·L^1.5) — a full bar is a licence to " +
    "train, overflow XP is discarded. <b>TRAIN</b> = gold the guild " +
    "asks to grant the level. <b>DAYS</b> = the practical pace: the " +
    "bar filled by hunting the matching floor at ~" + C.fightsPerDay +
    " fights/day (spawn-weighted average XP, common specimens). " +
    "<b>BASE</b> = the gate-issue set every fresh character carries: " +
    "starter weapon (+" + C.starterWeaponBonus + ") plus the free " +
    "buckler and jerkin; <b>REFERENCE</b> = the at-level forge " +
    "set the balance is tuned against.";

  let lv = '<table class="mech"><thead><tr><th>LV</th><th>XP NEED</th>' +
    "<th>TRAIN ◈</th><th>DAYS</th><th>GRIND FLR</th>" +
    "<th>BASE ATK/DEF/HP</th><th>REF ATK/DEF/HP</th></tr></thead><tbody>";
  let cumDays = 0;
  for (const l of M.levels) {
    cumDays += l.daysToFill || 0;
    lv += `<tr><td>${l.level}</td><td>${fmt(l.xpNeed)}</td>` +
      `<td>${fmt(l.trainGold)}</td>` +
      `<td>${l.daysToFill ?? "—"}</td><td>${l.grindFloor}</td>` +
      `<td>${l.baseAtk} / ${l.baseDef} / ${l.baseHp}</td>` +
      `<td>${l.refAtk} / ${l.refDef} / ${l.refHp}</td></tr>`;
  }
  lv += `<tr class="floorhead"><td colspan="7">TOTAL CLIMB TO CAP ≈ ` +
    `${cumDays.toFixed(1)} DAYS OF FULL-TIME HUNTING (fights only — ` +
    `train gold, gear gold and wardens not counted)</td></tr>`;
  $("levels-table").innerHTML = lv + "</tbody></table>";

  const slots = ["weapon", "shield", "armor", "shoes"];
  let gh = "";
  for (const slot of slots) {
    const rows = M.gear.filter((g) =>
      g.slot === slot && g.price > 0 && !g.style);
    gh += `<h3 class="slot">${slot}S</h3>` +
      '<table class="mech"><thead><tr><th class="l">NAME</th>' +
      '<th class="l">LINE</th><th>TIER</th><th>RUNG</th>' +
      `<th>${slot === "shoes" ? "+SPD" : "+BONUS"}</th>` +
      "<th>PRICE ◈</th><th>LVL</th><th>FLR</th></tr></thead><tbody>" +
      rows.map((g) =>
        `<tr><td class="l">${g.name}</td>` +
        `<td class="l dim">${g.line || "shared"}</td>` +
        `<td>${g.tier}</td><td>${g.rung || "—"}</td>` +
        `<td>${slot === "shoes" ? g.speed : g.bonus}</td>` +
        `<td>${fmt(g.price)}</td>` +
        `<td>${g.levelReq || "—"}</td><td>${g.floorReq || "—"}</td>` +
        "</tr>").join("") + "</tbody></table>";
  }
  $("gear-table").innerHTML = gh;

  let sh = '<table class="mech"><thead><tr><th class="l">ITEM</th>' +
    '<th>PRICE ◈</th><th class="l">EFFECT</th></tr></thead><tbody>' +
    M.shops.apothecary.map((i) =>
      `<tr><td class="l">${i.name}</td><td>${fmt(i.price)}</td>` +
      `<td class="l dim">${i.effect}${i.note ? " — " + i.note : ""}` +
      "</td></tr>").join("");
  sh += M.shops.relics.map((r) =>
    `<tr><td class="l">${r.name} <span class="dim">(relic)</span></td>` +
    `<td>${r.di}× daily income</td>` +
    `<td class="l dim">price scales with your frontier — e.g. ` +
    `${fmt(Math.round(r.di * C.dailyIncome[10]))} at floor 10, ` +
    `${fmt(Math.round(r.di * C.dailyIncome[30]))} at floor 30` +
    "</td></tr>").join("");
  sh += `<tr><td class="l">Honing (per +1)</td>` +
    `<td>${Math.round(M.shops.honePricePct * 100)}% daily income</td>` +
    `<td class="l dim">weapon ×3 / shield ×2 / armor ×2 per hone</td></tr>` +
    `<tr><td class="l">Repair</td>` +
    `<td>${Math.round(M.shops.repairPricePct * 100)}% × item price × ` +
    `missing</td><td class="l dim">broken gear works at half bonus` +
    `</td></tr>` +
    `<tr><td class="l">Arrow pack (${M.shops.arrowPack.size})</td>` +
    `<td>${M.shops.arrowPack.price}</td>` +
    `<td class="l dim">the quiver — any hands may draw (048)</td></tr>`;
  $("shop-table").innerHTML = sh + "</tbody></table>";

  // ── the simulator ─────────────────────────────────────────────────────
  const ri = (lo, hi) => lo + Math.floor(Math.random() * (hi - lo + 1));

  function typedDamage(path, raw, mdef, mtype) {
    if (path === "blade" && mtype === "fly") return 0;
    const mult = C.typeMult[mtype][path];
    const base = path === "staff" ? raw : raw - (mdef >> 1);
    return Math.max(1, Math.round(Math.max(1, base) * mult));
  }

  function dodgePct(pspd, mspd) {
    const adv = Math.max(0, pspd - mspd);
    return Math.min(12, Math.round(7 * Math.log2(1 + adv)));
  }

  function fight(P, mon, path, rank) {
    // P = {atk, def, hp}; mon = {atk, def, hp, type, speed}.
    // Returns {won, rounds, hpLost}. 048: the rank sets the miss
    // chance and the floor of the roll band.
    let php = P.hp, mhp = mon.hp, gap = 1, atRange = true, rounds = 0;
    const ranged = path === "bow";
    const miss = C.trainMissPct[rank] / 100;
    const rollLo = Math.round(C.trainRollFloor[rank] * P.atk);
    const dodge = dodgePct(C.playerSpeed, mon.speed);
    const pClose = Math.min(0.95, Math.max(0.05,
      0.25 + 0.15 * (mon.speed - C.playerSpeed)));
    while (rounds < 400) {
      rounds++;
      if (atRange && !ranged) {              // melee crossing
        atRange = false;
        if (!(dodge && Math.random() < dodge / 100)) {
          const raw = ri(mon.atk >> 1, mon.atk);
          const chip = Math.max(1, Math.ceil(raw / C.chipDivisor));
          php -= Math.max(chip, raw - (P.def >> 1)) >> 1;
        }
        if (php <= 0) return { won: 0, rounds, hpLost: P.hp };
        continue;
      }
      if (!(miss && Math.random() < miss)) { // a miss eats the round
        let mult = ranged ?
          (atRange ? (C.bowGapMult[gap] || 1.5) : C.bowCloseMult) : 1.0;
        if (mult > 1 && rank < C.gapDrawRank) mult = 1.0;
        const raw = ri(rollLo, P.atk);
        mhp -= typedDamage(path, Math.round(raw * mult), mon.def,
          mon.type);
        if (mhp <= 0) return { won: 1, rounds, hpLost: P.hp - php };
      }
      if (atRange) {                         // the gap is armor
        if (Math.random() < pClose) { gap--; if (gap <= 0) atRange = false; }
        continue;
      }
      if (!(dodge && Math.random() < dodge / 100)) {
        const raw2 = ri(mon.atk >> 1, mon.atk);
        const chip = Math.max(1, Math.ceil(raw2 / C.chipDivisor));
        php -= Math.max(chip, raw2 - (P.def >> 1));
      }
      if (php <= 0) return { won: 0, rounds, hpLost: P.hp };
    }
    return { won: 0, rounds, hpLost: P.hp - Math.max(php, 0) };
  }

  const selFloor = $("sim-floor"), selMon = $("sim-monster"),
    selSpec = $("sim-spec");
  selFloor.innerHTML = M.floors.map((f) =>
    `<option value="${f.floor}">${f.floor} — ${f.zone}</option>`).join("");
  function fillMonsters() {
    const f = M.floors.find((x) => x.floor === +selFloor.value);
    selMon.innerHTML = f.monsters.map((m, i) =>
      `<option value="${i}">${m.name}</option>`).join("");
    selSpec.innerHTML = Object.entries(f.specimens).map(([k, s]) =>
      `<option value="${k}"${k === "common" ? " selected" : ""}>` +
      `${k} (${s.weight}%)</option>`).join("");
  }
  selFloor.onchange = fillMonsters;
  fillMonsters();

  $("sim-run").onclick = () => {
    const f = M.floors.find((x) => x.floor === +selFloor.value);
    const m = f.monsters[+selMon.value];
    const spec = f.specimens[selSpec.value];
    const bar = Math.max(1, Math.min(C.barMax, +$("sim-level").value));
    const B = M.bars[bar - 1];
    const L = M.levels[B.level - 1];
    const gear = $("sim-gear").value;
    const P = gear === "ref" ?
      { atk: B.refAtk, def: B.refDef, hp: B.refHp } :
      { atk: B.baseAtk, def: B.baseDef, hp: B.baseHp };
    const path = $("sim-path").value;
    const rank = Math.max(0, Math.min(10, +$("sim-rank").value));
    if (m.type === "fly" && path === "blade") {
      $("simout").textContent =
        "Steel cannot reach " + m.name + " — it flies. " +
        "Take the bow (full) or a staff (more than half).";
      return;
    }
    const mon = {
      atk: Math.round(m.atk * spec.atk), def: m.def,
      hp: Math.round(m.hp * spec.hp),
      type: m.type,
      speed: m.speed + (selSpec.value === "alpha" ? 1 : 0),
    };
    const n = Math.max(100, Math.min(20000, +$("sim-n").value));
    let wins = 0, rsum = 0, hsum = 0;
    for (let i = 0; i < n; i++) {
      const r = fight(P, mon, path, rank);
      wins += r.won; rsum += r.rounds; hsum += r.hpLost;
    }
    const winPct = (100 * wins / n);
    const xp = m.xpAvg;                       // specimen never scales XP
    const gold = m.goldAvg * spec.gold;
    const killsBar = L.xpNeed / xp;
    const days = killsBar / (winPct / 100 || 1e-9) / C.fightsPerDay;
    const mult = C.typeMult[m.type][path];
    $("simout").textContent =
      `${n} fights vs ${selSpec.value} ${m.name} ` +
      `(ATK ${mon.atk} DEF ${mon.def} HP ${fmt(mon.hp)} ` +
      `SPD ${mon.speed})\n` +
      `player bar ${bar} (L${B.level}) ` +
      `${gear === "ref" ? "reference" : "gate-issue"} set: ` +
      `ATK ${P.atk} DEF ${P.def} HP ${P.hp} — ${path} rank ${rank} ` +
      `(miss ${C.trainMissPct[rank]}%, worst swing ` +
      `${Math.round(100 * C.trainRollFloor[rank])}%, ×${mult} vs ` +
      `${m.type})\n\n` +
      `WIN ${winPct.toFixed(1)}%   avg rounds ${(rsum / n).toFixed(1)}` +
      `   avg HP lost ${(hsum / n).toFixed(1)} / ${P.hp}\n` +
      `per kill ≈ ${xp} xp, ${Math.round(gold)} gold ` +
      `(±${C.xpJitterPct}% / ±${C.goldJitterPct}% rolls)\n` +
      `level bar (${fmt(L.xpNeed)} xp) ≈ ${Math.ceil(killsBar)} kills ` +
      `of this monster ≈ ${days.toFixed(2)} days at ` +
      `${C.fightsPerDay} fights/day`;
  };

  // ── TRAINING tab ──────────────────────────────────────────────────────
  const T = M.training;
  $("training-legend").innerHTML =
    "The School sells RANK 0–10 per weapon path — the hand's skill, " +
    "never the weapon's. Rank buys consistency: <b>MISS%</b> (an " +
    "attack that goes wide, the round spent, the counter landing) " +
    "falls " + T.missPct0 + "% → 0%, and <b>WORST SWING</b> (the " +
    "floor of the damage roll) rises " + T.rollFloorPct0 + "% → 70% " +
    "of full power. <b>XP</b> is spent from the same hard bar that " +
    "buys levels; <b>FITS L</b> is the fits-the-bar law: the lowest " +
    "body level whose single bar can pay the rank — every gate below " +
    "is honest. <b>GOLD</b> rides the pillar of the frontier floor " +
    "(shown at floor 10 / floor 30).";
  let tr = '<table class="mech"><thead><tr><th>RANK</th><th>XP</th>' +
    "<th>CUM XP</th><th>GOLD @F10</th><th>GOLD @F30</th>" +
    "<th>MISS%</th><th>WORST SWING</th><th>FITS L</th></tr></thead><tbody>";
  for (const r of T.ranks) {
    tr += `<tr><td>${r.rank}</td><td>${fmt(r.xp)}</td>` +
      `<td>${fmt(r.cumXp)}</td>` +
      `<td>${fmt(r.gold10)}</td><td>${fmt(r.gold30)}</td>` +
      `<td>${r.missPct}</td><td>${r.rollFloorPct}%</td>` +
      `<td>${r.fitLevel} <span class="dim">(bar ` +
      `${fmt(r.fitXpNeed)})</span></td></tr>`;
  }
  tr += "</tbody></table>";
  tr += '<h3 class="slot">RANK GATES — what the hands unlock</h3>' +
    '<table class="mech"><thead><tr><th class="l">PATH</th>' +
    '<th class="l">OPTION</th><th>RANK</th></tr></thead><tbody>' +
    T.gates.map((g) =>
      `<tr><td class="l">${g.path}</td><td class="l">${g.name}</td>` +
      `<td>${g.rank}</td></tr>`).join("") + "</tbody></table>";
  tr += '<h3 class="slot">SCHOOL MERCHANDISE</h3>' +
    '<table class="mech"><thead><tr><th class="l">ITEM</th>' +
    "<th>XP</th><th>GOLD</th><th>LEVEL GATE</th><th>FITS L</th>" +
    "</tr></thead><tbody>" +
    T.merch.map((x) =>
      `<tr><td class="l">${x.name}</td><td>${fmt(x.xp)}</td>` +
      `<td>${x.gold !== null ? fmt(x.gold) :
        (x.goldAnchor ? fmt(x.goldAnchor) + " × pillar(frontier)"
          : "—")}</td>` +
      `<td>${x.level ?? "rank 10"}</td><td>${x.fitLevel}</td></tr>`)
      .join("") + "</tbody></table>" +
    `<div class="legend">A master pays ${Math.round(100 *
      T.masteryDiscount)}% on the OTHER paths' ranks 1–` +
    `${T.masteryDiscountMaxRank}. Mastery teeth: blade riposte ` +
    `returns ${Math.round(100 * T.masteryTeeth.riposteReturn)}% of a ` +
    `blocked mean swing; the bow's gap-3 top-roll ` +
    `${Math.round(100 * T.masteryTeeth.longDrawTop)}% crits ` +
    `×${T.masteryTeeth.longDrawCritMult}; the staff's half-answers ` +
    `cast at ×${T.masteryTeeth.focusMult} (focus).</div>`;
  $("training-table").innerHTML = tr;
})();
