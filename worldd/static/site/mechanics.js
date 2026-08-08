/* The mechanics ledger — renders mechanics-data.js and runs the fight
   simulator. The sim mirrors engine/combat.py: player strikes first,
   rolls uniform in [stat/2, stat], chip floor ceil(raw/4), armor/resist
   tier multipliers, dodge from speed advantage, the bow range ladder. */
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
    "(accepted ≥" + C.winAcceptPct + "%), fought by the class the " +
    "creature does not counter — ⚔ blade, ➶ bow (flyers), ✦ staff " +
    "(armored shapes). <b>RNDS / HP LOST</b> are the " +
    "averages at that bar. Energy allows ~" + C.fightsPerDay +
    " wilds fights per day (1 energy / " + C.energyRegenMin + " min).";

  const cols = ["MONSTER", "KIND", "TRAITS", "SPAWN%", "ATK", "DEF",
    "HP", "ARM", "RES", "SPD", "XP", "GOLD", "KILL BAR", "WIN%",
    "RNDS", "HP LOST"];
  let html = '<table class="mech"><thead><tr>' + cols.map((c, i) =>
    `<th${i < 3 ? ' class="l"' : ""}>${c}</th>`).join("") +
    "</tr></thead><tbody>";
  for (const f of M.floors) {
    html += `<tr class="floorhead" id="floor-${f.floor}">` +
      `<td colspan="${cols.length}">FLOOR ${f.floor} · ` +
      `${f.zone.toUpperCase()} — ${f.biome} · gate: ${f.gateTown}` +
      `</td></tr>`;
    for (const m of f.monsters) {
      const kglyph = {melee: "⚔", ranged: "➶", magic: "✦"}[m.killType] || "";
      const kl = m.killLevel === null ? '<td class="hard">—</td>' :
        `<td class="${m.killLevel <= f.floor ? "easy" : "hard"}">` +
        `${m.killLevel}<span class="dim"> ${kglyph}</span></td>`;
      const flags = (m.flying ? " ✈" : "") + (m.bulwark ? " ▣" : "");
      html += "<tr>" +
        `<td class="l">${m.name}${flags}</td>` +
        `<td class="l dim">${m.kind}</td>` +
        `<td class="l dim">${m.traits.join(" ") || "—"}</td>` +
        `<td>${m.spawnPct}</td><td>${m.atk}</td><td>${m.def}</td>` +
        `<td>${fmt(m.hp)}</td>` +
        `<td>${m.armor === "none" ? "·" : m.armor}</td>` +
        `<td>${m.resist === "none" ? "·" : m.resist}</td>` +
        `<td>${m.speed}</td>` +
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
    "<b>BASE</b> = naked stats + starter weapon (+" +
    C.starterWeaponBonus + "); <b>REFERENCE</b> = the at-level forge " +
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

  $("offmult").textContent = M.shops.offClassPriceMult;

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
    `<td class="l dim">off-class archery only</td></tr>`;
  $("shop-table").innerHTML = sh + "</tbody></table>";

  // ── the simulator ─────────────────────────────────────────────────────
  const TIER = C.tierMult;
  const ri = (lo, hi) => lo + Math.floor(Math.random() * (hi - lo + 1));

  function typedDamage(dtype, raw, mdef, m) {
    if (dtype === "melee" && m.flying) return 0;
    let base, mult;
    if (dtype === "magic") { base = raw; mult = TIER[m.resist]; }
    else { base = raw - (mdef >> 1); mult = TIER[m.armor]; }
    return Math.max(1, Math.round(Math.max(1, base) * mult));
  }

  function dodgePct(pspd, mspd) {
    const adv = Math.max(0, pspd - mspd);
    return Math.min(12, Math.round(7 * Math.log2(1 + adv)));
  }

  function fight(P, mon, dtype) {
    // P = {atk, def, hp}; mon = {atk, def, hp, armor, resist, flying,
    // speed}. Returns {won, rounds, hpLost}.
    let php = P.hp, mhp = mon.hp, gap = 1, atRange = true, rounds = 0;
    const ranged = dtype === "ranged";
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
      const mult = ranged ?
        (atRange ? (C.bowGapMult[gap] || 1.5) : C.bowCloseMult) : 1.0;
      const raw = ri(P.atk >> 1, P.atk);
      mhp -= typedDamage(dtype, Math.round(raw * mult), mon.def, mon);
      if (mhp <= 0) return { won: 1, rounds, hpLost: P.hp - php };
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
    let dtype = $("sim-class").value;
    if (m.flying && dtype === "melee") {
      $("simout").textContent =
        "A sword cannot reach " + m.name + " — it flies. Take the bow.";
      return;
    }
    const mon = {
      atk: Math.round(m.atk * spec.atk), def: m.def,
      hp: Math.round(m.hp * spec.hp),
      armor: m.armor, resist: m.resist, flying: m.flying,
      speed: m.speed + (selSpec.value === "alpha" ? 1 : 0),
    };
    const n = Math.max(100, Math.min(20000, +$("sim-n").value));
    let wins = 0, rsum = 0, hsum = 0;
    for (let i = 0; i < n; i++) {
      const r = fight(P, mon, dtype);
      wins += r.won; rsum += r.rounds; hsum += r.hpLost;
    }
    const winPct = (100 * wins / n);
    const xp = m.xpAvg;                       // specimen never scales XP
    const gold = m.goldAvg * spec.gold;
    const killsBar = L.xpNeed / xp;
    const days = killsBar / (winPct / 100 || 1e-9) / C.fightsPerDay;
    $("simout").textContent =
      `${n} fights vs ${selSpec.value} ${m.name} ` +
      `(ATK ${mon.atk} DEF ${mon.def} HP ${fmt(mon.hp)})\n` +
      `player bar ${bar} (L${B.level}) ` +
      `${gear === "ref" ? "reference" : "starter"} set: ` +
      `ATK ${P.atk} DEF ${P.def} HP ${P.hp} — ${dtype}\n\n` +
      `WIN ${winPct.toFixed(1)}%   avg rounds ${(rsum / n).toFixed(1)}` +
      `   avg HP lost ${(hsum / n).toFixed(1)} / ${P.hp}\n` +
      `per kill ≈ ${xp} xp, ${Math.round(gold)} gold ` +
      `(±${C.xpJitterPct}% / ±${C.goldJitterPct}% rolls)\n` +
      `level bar (${fmt(L.xpNeed)} xp) ≈ ${Math.ceil(killsBar)} kills ` +
      `of this monster ≈ ${days.toFixed(2)} days at ` +
      `${C.fightsPerDay} fights/day`;
  };
})();
