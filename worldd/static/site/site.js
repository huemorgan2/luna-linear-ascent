/* linearascent.net — the page's moving parts (plan 003).
   Everything here is decoration on top of a page that already works:
   scripts off, the lore reads, the form posts, the world stands. */

(function () {
  "use strict";

  var $ = function (id) { return document.getElementById(id); };
  var STILL = matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ── bars drawn in the only ink we own: ▓ and ░ ─────────────────── */
  function bar(pct, width) {
    var full = Math.round(width * Math.max(0, Math.min(100, pct)) / 100);
    return new Array(full + 1).join("▓")
      + new Array(width - full + 1).join("░");
  }

  /* ── the live world ─────────────────────────────────────────────── */
  function fillWorld(w) {
    var c = w.climbers || {};
    var line = "DAY " + w.day + " · " + (c.total || 0) + " CLIMBERS ON THE TOWER"
      + (c.online ? " · " + c.online + " ON THE FLOORS THIS HOUR" : "")
      + " · THE FRONTIER STANDS AT FLOOR " + w.frontier;
    var hero = document.querySelector('[data-live="hero"]');
    if (hero) hero.textContent = "… " + line.toLowerCase() + " …";

    var barRight = $("bar-right");
    if (barRight) barRight.textContent =
      "DAY " + w.day + " · " + (c.total || 0) + " CLIMBERS · F" + w.frontier;

    var parts = [line];
    if (w.warden) parts.push("WARDEN " + w.warden.name.toUpperCase()
      .replace(/^WARDEN /, "") + " AT " + w.warden.pct + "%"
      + (w.warden.blades.length ? ", " + w.warden.blades.length
        + " BLADES ON IT" : " — UNCUT"));
    (w.crier || []).forEach(function (l) { parts.push(l.toUpperCase()); });
    parts.push("FREE — A USERNAME AND A PASSWORD, LIKE THE OLD DAYS");
    var tick = $("ticker-inner");
    if (tick) tick.textContent = "  ····  " + parts.join("  ····  ");

    if (w.warden) {
      $("warden-name").textContent = w.warden.name.toUpperCase()
        + " — FLOOR " + w.warden.floor;
      $("warden-pct").textContent = w.warden.pct + "%";
      $("warden-blades").textContent = w.warden.blades.length
        ? "blades in the wound: " + w.warden.blades.join(", ")
        : "the wound waits for its first blade — it could carry your name";
      animateWound(w.warden.pct);
    } else {
      $("warden-name").textContent = "FLOOR " + w.frontier
        + " — A MILESTONE KEEP";
      $("warden-pct").textContent = "";
      $("warden-bar").textContent = "═══ THE WAR PARTY IS MUSTERING ═══";
      $("warden-blades").textContent =
        "the great Wardens do not fall to one blade — climbers are pledging now";
    }

    if (w.stone && w.stone.length) {
      $("stone-lines").textContent = "   ═══ THE STONE ═══\n"
        + w.stone.map(function (l) { return "   " + l; }).join("\n");
    }
    if (w.eras && w.eras.length) {
      $("era-lines").textContent = "closed ledgers: " + w.eras.map(
        function (e) {
          return "ERA " + e.era + " — fell on day " + e.day + " to "
            + e.finisher + (e.blades ? " and " + e.blades + " blades" : "");
        }).join(" · ");
    }

    var crier = $("crier-lines");
    if (crier && w.crier && w.crier.length) {
      crier.innerHTML = "";
      w.crier.forEach(function (l) {
        var p = document.createElement("p");
        p.textContent = l;
        crier.appendChild(p);
      });
    }
    $("crier-day").textContent = "DAY " + w.day + ", AT THE FRONTIER";
    $("foot-version").textContent = "· v" + w.game + " · day " + w.day;
    $("foot-era").textContent = "ERA " + w.era + " — the tower stands.";
  }

  var woundTimer = null;
  function animateWound(pct) {
    var el = $("warden-bar"), width = 24;
    if (STILL) { el.textContent = bar(pct, width); return; }
    var cur = 100;
    clearInterval(woundTimer);
    woundTimer = setInterval(function () {
      cur = Math.max(pct, cur - 3);
      el.textContent = bar(cur, width);
      if (cur <= pct) clearInterval(woundTimer);
    }, 60);
  }

  fetch("/v1/public/world").then(function (r) { return r.json(); })
    .then(fillWorld).catch(function () { /* the page stands anyway */ });

  /* ── the eyebrow follows the climb ──────────────────────────────── */
  var sections = document.querySelectorAll("section[data-floor]");
  if ("IntersectionObserver" in window) {
    var iob = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting)
          $("bar-left").textContent = e.target.getAttribute("data-floor");
      });
    }, { rootMargin: "-40% 0px -55% 0px" });
    sections.forEach(function (s) { iob.observe(s); });

    /* cards materialize; lore lines type themselves */
    var cob = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        cob.unobserve(e.target);
        e.target.classList.remove("veil");
        e.target.classList.add("on");
        typeCard(e.target);
      });
    }, { rootMargin: "0px 0px -10% 0px" });
    document.querySelectorAll(".card, .strip figure").forEach(function (c) {
      c.classList.add("veil");
      cob.observe(c);
    });
  }

  /* ── typewriter, the ANSI soul ──────────────────────────────────── */
  function typeCard(card) {
    var lines = [].slice.call(card.querySelectorAll("p.t"));
    if (!lines.length || STILL) return;
    lines.forEach(function (p) {
      p.dataset.full = p.textContent;
      p.textContent = "";
      p.classList.add("untyped");
    });
    var li = 0;
    (function nextLine() {
      if (li >= lines.length) return;
      var p = lines[li++], full = p.dataset.full, i = 0;
      p.classList.remove("untyped");
      p.classList.add("caret");
      (function tick() {
        i = Math.min(full.length, i + 2);
        p.textContent = full.slice(0, i);
        if (i < full.length) setTimeout(tick, 8);
        else { p.classList.remove("caret"); setTimeout(nextLine, 120); }
      })();
    })();
  }

  /* ── the fight that plays itself (real engine flavor, scripted) ─── */
  var W = 10;
  function meters(you, youMax, wolf, wolfMax) {
    return "YOU  " + bar(100 * you / youMax, W) + " " + you + "/" + youMax
      + " · WOLF " + bar(100 * wolf / wolfMax, W) + " " + wolf + "/" + wolfMax;
  }
  var DEMO = [
    { line: "A grey wolf slides out of the hedgerow, low and patient.",
      you: 24, wolf: 14 },
    { line: "You close the gap.", opt: "attack", you: 24, wolf: 14 },
    { line: "Your blade bites — the wolf staggers.", opt: "attack",
      you: 24, wolf: 9 },
    { line: "Teeth find your forearm. It costs you.", you: 19, wolf: 9 },
    { line: "You set your feet behind your shield.", opt: "brace",
      you: 19, wolf: 9 },
    { line: "The lunge breaks on your guard. Your opening —", opt: "attack",
      you: 19, wolf: 4 },
    { line: "The killing blow is yours.", opt: "attack", you: 19, wolf: 0,
      headline: "The grey wolf is down", art: "wolf_kill_melee_320x112.gif",
      hold: 3200 },
    { line: "The fencerows go quiet. The pelt is yours — and the tower "
        + "is still there, over the hedge, holding your home.",
      you: 19, wolf: 0, hold: 3600, reset: true }
  ];
  var demoStep = 0;
  function demoTick() {
    var d = DEMO[demoStep];
    var lines = $("demo-lines");
    if (!lines) return;
    if (d.reset === undefined && demoStep === 0) {
      $("demo-headline").textContent = "A grey wolf circles";
      $("demo-art").src = "/static/site/art/grey_wolf_320x112.png";
      lines.innerHTML = "";
    }
    if (d.headline) $("demo-headline").textContent = d.headline;
    if (d.art) $("demo-art").src = "/static/site/art/" + d.art;
    var p = document.createElement("p");
    p.textContent = d.line;
    lines.appendChild(p);
    while (lines.children.length > 4) lines.removeChild(lines.firstChild);
    $("demo-meters").textContent = meters(d.you, 30, d.wolf, 14);
    ["attack", "brace", "run"].forEach(function (o) {
      $("demo-opt-" + o).classList.toggle("hot", d.opt === o);
    });
    demoStep = (demoStep + 1) % DEMO.length;
    setTimeout(demoTick, d.hold || 1900);
  }
  if (!STILL && $("demo-card")) setTimeout(demoTick, 1200);

  /* ── the door ───────────────────────────────────────────────────── */
  var form = $("door-form"), note = $("door-note");

  function doorKnown(name) {
    form.style.display = "none";
    note.classList.remove("err");
    note.innerHTML = "The door knows you, <span class='bright'>" + name
      + "</span>. Your name is held in the world — the browser climb "
      + "lands on this page next. ";
    var out = document.createElement("a");
    out.textContent = "[ leave by the door ]";
    out.href = "#";
    out.onclick = function (ev) {
      ev.preventDefault();
      fetch("/logout", { method: "POST",
                         headers: { "Accept": "application/json" } })
        .then(function () { location.reload(); });
    };
    note.appendChild(out);
  }

  fetch("/me").then(function (r) { return r.json(); })
    .then(function (m) { if (m.username) doorKnown(m.username); })
    .catch(function () {});

  if (form) {
    /* Two doors, one form: sign-up asks for the password twice, sign-in
       once. With scripts off both submit buttons are in the markup with
       their own formaction, so the page still opens either door. */
    var setMode = function (m) {
      var up = m === "signup";
      form.setAttribute("action", up ? "/signup" : "/login");
      $("label-pw").textContent = up ? "NEW PASSWORD" : "PASSWORD";
      $("row-pw2").style.display = up ? "" : "none";
      form.elements.password2.required = up;
      form.elements.password.setAttribute(
        "autocomplete", up ? "new-password" : "current-password");
      $("door-signup").style.display = up ? "" : "none";
      $("door-login").style.display = up ? "none" : "";
      $("door-login").classList.toggle("gold-opt", !up);
      $("door-login").classList.toggle("dim2", up);
      $("tab-signup").classList.toggle("on", up);
      $("tab-signup").classList.toggle("dim2", !up);
      $("tab-signin").classList.toggle("on", !up);
      $("tab-signin").classList.toggle("dim2", up);
    };
    $("tab-signup").addEventListener("click", function () {
      setMode("signup");
    });
    $("tab-signin").addEventListener("click", function () {
      setMode("signin");
    });
    setMode("signup");

    var doorPost = function (path) {
      var body = {
        username: form.elements.username.value,
        password: form.elements.password.value
      };
      if (path === "/signup") {
        body.password2 = form.elements.password2.value;
      }
      fetch(path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
      }).then(function (r) {
        return r.json().then(function (j) { return { ok: r.ok, j: j }; });
      }).then(function (res) {
        if (res.ok) return doorKnown(res.j.username);
        note.classList.add("err");
        note.textContent = "▮ " + (res.j.detail || "the door stays shut");
      }).catch(function () {
        note.classList.add("err");
        note.textContent = "▮ the relay dropped the letter — try again";
      });
    };
    form.addEventListener("submit", function (ev) {
      ev.preventDefault();
      var path = form.getAttribute("action");
      if (path === "/signup"
          && form.elements.password2.value !== form.elements.password.value) {
        note.classList.add("err");
        note.textContent = "▮ the two passwords differ";
        return;
      }
      doorPost(path);
    });
    $("door-login").addEventListener("click", function (ev) {
      ev.preventDefault();
      doorPost("/login");
    });

    /* a plain form POST landed us back with ?door_err=… — say it */
    var err = new URLSearchParams(location.search).get("door_err");
    if (err) {
      note.classList.add("err");
      note.textContent = "▮ " + err.replace(/\+/g, " ");
    }
  }
})();
