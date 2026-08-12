/* The admin desk console — PLAYERS and FEEDBACK, behind X-Admin-Key.
   No framework: fetch + innerHTML, same as the public site. The key
   lives in localStorage and rides every request as a header; a 401
   drops back to the gate.

   Every view owns a hash URL (#/players, #/player/{tenant}/{player},
   #/feedback, #/feedback/{fid}) — navigation is a real location change,
   so the browser back button, reload, and open-in-new-tab all work. */
"use strict";

const $ = (id) => document.getElementById(id);
const KEY_STORE = "ascent_admin_key";
let weaponsCache = null;

function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;",
    '"': "&quot;", "'": "&#39;" }[c]));
}

function note(text) {
  const n = $("note");
  n.textContent = text;
  n.style.display = "block";
  clearTimeout(note._t);
  note._t = setTimeout(() => { n.style.display = "none"; }, 2500);
}

async function api(path, opts = {}) {
  // an admin session cookie rides along on its own — the key header is
  // only for desks without one
  const key = localStorage.getItem(KEY_STORE) || "";
  const r = await fetch(path, {
    ...opts,
    headers: { ...(key ? { "X-Admin-Key": key } : {}),
               ...(opts.body ? { "Content-Type": "application/json" } : {}),
               ...(opts.headers || {}) },
  });
  if (r.status === 401) {
    gate(key ? "that key does not turn" : "");
    throw new Error("401");
  }
  if (!r.ok) {
    let msg = r.statusText;
    try { msg = (await r.json()).detail || msg; } catch (e) { /* text */ }
    note(msg);
    throw new Error(msg);
  }
  return r;
}

const apiJson = async (path, opts) => (await api(path, opts)).json();

// ── Routing ─────────────────────────────────────────────────────────────

function playersHash(q) {
  return "#/players" + (q ? "?q=" + encodeURIComponent(q) : "");
}

function playerHash(tenant, player, q) {
  return `#/player/${encodeURIComponent(tenant)}/` +
         encodeURIComponent(player) +
         (q ? "?q=" + encodeURIComponent(q) : "");
}

function route() {
  if ($("console").hidden) return;          // the gate holds until the key
  const [path, qs] = location.hash.replace(/^#\/?/, "").split("?");
  const parts = path.split("/").map(decodeURIComponent).filter(Boolean);
  const q = new URLSearchParams(qs || "").get("q") || "";
  if (parts[0] === "player" && parts.length >= 3)
    renderPlayer(parts[1], parts.slice(2).join("/"), q);
  else if (parts[0] === "feedback" && parts[1])
    renderThread(Number(parts[1]));
  else if (parts[0] === "feedback") renderFeedback();
  else renderPlayers(q);
}

window.addEventListener("hashchange", route);

function nav(h) {
  // same hash twice fires no hashchange — re-render by hand
  if (location.hash === h) route(); else location.hash = h;
}

// ── The gate ────────────────────────────────────────────────────────────

function gate(err) {
  $("console").hidden = true;
  $("keygate").hidden = false;
  $("keyerr").textContent = err || "";
  $("keyin").focus();
}

async function enter() {
  localStorage.setItem(KEY_STORE, $("keyin").value.trim());
  try { await api("/admin/api/players?limit=1"); } catch (e) { return; }
  $("keygate").hidden = true;
  $("console").hidden = false;
  route();                                  // honor a deep link past the gate
}

// ── Tabs ────────────────────────────────────────────────────────────────

function setTab(name) {
  $("tabPlayers").classList.toggle("on", name === "players");
  $("tabFeedback").classList.toggle("on", name === "feedback");
}

// ── PLAYERS ─────────────────────────────────────────────────────────────

function ago(iso) {
  if (!iso) return "—";
  const days = Math.max(0, Math.floor((Date.now() - Date.parse(iso)) / 864e5));
  return days === 0 ? "today" : `${days}d`;
}

async function renderPlayers(query = "") {
  setTab("players");
  $("main").innerHTML = `
    <div class="bar">
      <input id="q" placeholder="search name or player key…"
             value="${esc(query)}" style="flex:1; min-width:200px">
      <button class="act" id="go">SEARCH</button>
      <a class="ghost" href="#/players"
         style="padding:5px 14px; border:1px solid var(--line);
                text-decoration:none">TOP 100</a>
    </div>
    <div id="list" class="scroll"><p class="dim">…</p></div>`;
  $("go").onclick = () => nav(playersHash($("q").value.trim()));
  $("q").onkeydown = (e) => { if (e.key === "Enter") $("go").click(); };
  const data = await apiJson(
    "/admin/api/players?limit=100&q=" + encodeURIComponent(query));
  const rows = data.players.map((p, i) => `
    <tr class="row" data-href="${playerHash(p.tenant, p.player, query)}">
      <td class="num dim">${i + 1}</td>
      <td><a href="${playerHash(p.tenant, p.player, query)}"
             style="text-decoration:none">${esc(p.name)}</a></td>
      <td class="dim">${esc(p.race)}</td>
      <td class="num">${p.level}</td>
      <td class="num">${p.xp.toLocaleString()}</td>
      <td class="num">${p.gold.toLocaleString()}</td>
      <td class="num">${p.bank.toLocaleString()}</td>
      <td class="num">${p.floor}</td>
      <td class="dim">${esc(p.stage)}</td>
      <td class="dim">${ago(p.updated_at)}</td>
      <td class="dim">${esc(p.tenant)}:${esc(p.player)}</td>
    </tr>`).join("");
  $("list").innerHTML = data.players.length ? `
    <table>
      <tr><th class="num">#</th><th>name</th><th>race</th>
          <th class="num">lv</th><th class="num">xp</th>
          <th class="num">gold</th><th class="num">bank</th>
          <th class="num">floor</th><th>stage</th><th>seen</th>
          <th>key</th></tr>
      ${rows}
    </table>
    <p class="dim">${data.players.length} shown · ${data.total} in the world</p>`
    : `<p class="dim">nobody by that name</p>`;
  for (const tr of $("list").querySelectorAll("tr.row"))
    tr.onclick = (e) => {
      if (e.target.closest("a")) return;    // the anchor handles itself
      location.hash = tr.dataset.href;
    };
}

function kv(pairs) {
  return `<div class="kv">` + pairs.map(([k, v]) =>
    `<b>${esc(k)}</b><span>${v}</span>`).join("") + `</div>`;
}

async function renderPlayer(tenant, player, backQuery = "") {
  setTab("players");
  $("main").innerHTML = `<p class="dim">…</p>`;
  const [p, weapons] = await Promise.all([
    apiJson(`/admin/api/player?tenant=${encodeURIComponent(tenant)}` +
            `&player=${encodeURIComponent(player)}`),
    weaponsCache || apiJson("/admin/api/weapons"),
  ]);
  weaponsCache = weapons;
  const byLine = {};
  for (const w of weapons.weapons)
    (byLine[w.line] = byLine[w.line] || []).push(w);
  const groups = Object.keys(byLine).sort().map((line) => `
    <optgroup label="${esc(line)}">` + byLine[line].map((w) => `
      <option value="${esc(w.slug)}">T${w.tier}${w.style ? " " + esc(w.style) : ""}
        — ${esc(w.name)} (+${w.bonus})</option>`).join("") +
    `</optgroup>`).join("");
  const energy = p.energy === null ? "—" : `${p.energy} / ${p.energy_cap}`;
  $("main").innerHTML = `
    <a class="back" href="${playersHash(backQuery)}">← back to the list</a>
    <h2 style="margin:0 0 2px">${esc(p.name)}
      <span class="dim" style="font-size:13px">· ${esc(p.race)} ·
        level ${p.level} · floor ${p.floor} · ${esc(p.stage)}</span></h2>
    <p class="dim" style="margin-top:2px">${esc(p.tenant)}:${esc(p.player)}
      ${p.luna_user ? " · " + esc(p.luna_user) : ""} ·
      seen ${ago(p.updated_at)}</p>
    <div class="cardgrid">
      <div class="card">
        <h3>Parameters</h3>
        <div class="field"><label>energy</label>
          <input id="fEnergy" type="number" min="0"
                 placeholder="${esc(energy)}"></div>
        <div class="field"><label>xp</label>
          <input id="fXp" type="number" min="0"
                 placeholder="${p.xp.toLocaleString()}"></div>
        <div class="field"><label>gold</label>
          <input id="fGold" type="number" min="0"
                 placeholder="${p.gold.toLocaleString()}"></div>
        <div class="field"><label>bank</label>
          <input id="fBank" type="number" min="0"
                 placeholder="${p.bank.toLocaleString()}"></div>
        <button class="act" id="save">SAVE</button>
        <p class="dim" style="font-size:12px">empty fields stay as they
          are · energy ${esc(energy)} · hp ${p.hp ?? "—"}</p>
      </div>
      <div class="card">
        <h3>Grant a weapon</h3>
        <select id="wsel" style="width:100%">${groups}</select>
        <p><button class="act" id="grant">GRANT → PACK</button></p>
        <p class="dim" style="font-size:12px">arrives in the pack with a
          full durability pool, like a bought spare</p>
      </div>
      <div class="card">
        <h3>Carried</h3>
        ${kv([
          ...Object.entries(p.gear).map(([slot, g]) =>
            [slot, esc(g.name || g.slug)]),
          ["held", p.held.map((h) => esc(h.name)).join(", ") || "—"],
          ["slots", p.slots],
          ["training", Object.entries(p.training).map(([l, r]) =>
            `${esc(l)} ${r}`).join(" · ") || "—"],
        ])}
      </div>
      <div class="card">
        <h3>Pack</h3>
        ${p.inventory.length ? kv(p.inventory.map((it) =>
          [esc(it.name || it.slug), "× " + it.count])) :
          `<span class="dim">empty</span>`}
      </div>
    </div>`;

  const edit = async (body) => {
    body.tenant = p.tenant; body.player = p.player;
    const out = await apiJson("/admin/api/player",
                              { method: "POST", body: JSON.stringify(body) });
    note(out.changes.join(" · "));
    renderPlayer(tenant, player, backQuery);   // same URL — no history entry
  };
  $("save").onclick = () => {
    const body = {};
    const grab = (id, k) => {
      const v = $(id).value.trim();
      if (v !== "") body[k] = Number(v);
    };
    grab("fEnergy", "energy"); grab("fXp", "xp");
    grab("fGold", "gold"); grab("fBank", "bank");
    if (!Object.keys(body).length) { note("nothing to change"); return; }
    edit(body);
  };
  $("grant").onclick = () => edit({ grant: [$("wsel").value] });
}

// ── FEEDBACK ────────────────────────────────────────────────────────────

async function renderFeedback() {
  setTab("feedback");
  $("main").innerHTML = `<div id="list" class="scroll">
    <p class="dim">…</p></div>`;
  const data = await apiJson("/admin/api/feedback");
  $("list").innerHTML = data.threads.length ? `
    <table>
      <tr><th>subject</th><th>from</th><th>key</th><th>last line</th>
          <th>last</th><th class="num">unread</th></tr>
      ${data.threads.map((t) => `
        <tr class="row" data-href="#/feedback/${t.id}">
          <td><a href="#/feedback/${t.id}"
                 style="text-decoration:none">${esc(t.subject)}</a></td>
          <td>${esc(t.author)}</td>
          <td class="dim">${esc(t.tenant)}:${esc(t.player)}</td>
          <td class="dim" style="white-space:normal">${esc(t.last_line)}</td>
          <td class="dim">${ago(t.last_msg_at)}
            ${t.last_sender === "player" ? "· them" : "· you"}</td>
          <td class="num">${t.unread ?
            `<span class="unread">${t.unread}</span>` : ""}</td>
        </tr>`).join("")}
    </table>` : `<p class="dim">the postbox is empty</p>`;
  for (const tr of $("list").querySelectorAll("tr.row"))
    tr.onclick = (e) => {
      if (e.target.closest("a")) return;
      location.hash = tr.dataset.href;
    };
}

async function renderThread(fid) {
  setTab("feedback");
  $("main").innerHTML = `<p class="dim">…</p>`;
  const t = await apiJson(`/admin/api/feedback/${fid}`);
  $("main").innerHTML = `
    <a class="back" href="#/feedback">← back to the postbox</a>
    <h2 style="margin:0">${esc(t.subject)}</h2>
    <p class="dim" style="margin-top:2px">${esc(t.author)} ·
      ${esc(t.tenant)}:${esc(t.player)}</p>
    <div id="msgs"></div>
    <div class="bar" style="margin-top:14px">
      <textarea id="reply" rows="3" style="flex:1"
        placeholder="reply as the desk…"></textarea>
      <button class="act" id="send">SEND</button>
    </div>`;
  $("msgs").innerHTML = t.messages.map((m) => `
    <div class="msg ${m.sender === "admin" ? "admin" : ""}">
      <div class="who">
        <span class="${m.sender === "admin" ? "adm" : ""}">
          ${esc(m.author)}${m.sender === "admin" ? " · desk" : ""}</span>
        · ${new Date(m.at).toLocaleString()}</div>
      <div>${esc(m.body)}</div>
      <div class="atts" data-atts='${esc(JSON.stringify(
        m.attachments.map((a) => a.id)))}'></div>
    </div>`).join("");
  // attachments need the key header — fetch as blobs, not <img src>
  for (const box of $("msgs").querySelectorAll(".atts")) {
    for (const id of JSON.parse(box.dataset.atts)) {
      try {
        const r = await api(`/admin/api/feedback/attachment/${id}`);
        const img = document.createElement("img");
        img.src = URL.createObjectURL(await r.blob());
        box.appendChild(img);
      } catch (e) { /* skip a broken image */ }
    }
  }
  $("send").onclick = async () => {
    const body = $("reply").value.trim();
    if (!body) return;
    $("send").disabled = true;
    try {
      await apiJson(`/admin/api/feedback/${fid}/reply`,
                    { method: "POST", body: JSON.stringify({ body }) });
      renderThread(fid);                    // same URL — no history entry
    } finally { $("send").disabled = false; }
  };
}

// ── Boot ────────────────────────────────────────────────────────────────

$("keygo").onclick = enter;
$("keyin").onkeydown = (e) => { if (e.key === "Enter") enter(); };
$("tabPlayers").onclick = () => nav("#/players");
$("tabFeedback").onclick = () => nav("#/feedback");
$("keyout").onclick = () => { localStorage.removeItem(KEY_STORE); gate(); };

// always knock first — an admin session cookie opens the desk without
// a key; the gate only appears when neither cookie nor stored key turns
api("/admin/api/players?limit=1").then(() => {
  $("keygate").hidden = true;
  $("console").hidden = false;
  route();
}).catch(() => {});
