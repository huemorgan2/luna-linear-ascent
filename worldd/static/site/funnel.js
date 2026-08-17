/* Funnel Fighters — the ONLY file where the tracker lives.
   The rest of the site calls window.ff.* — tiny wrappers that no-op
   when the SDK is blocked and never throw. Tracked: visits, the door
   (signup/signin), entering the game. Nothing inside the game. */
(function () {
  "use strict";

  /* ── config, all of it ─────────────────────────────────────────── */
  var FF_SITE = "4a62eb26-43d4-464e-835e-b11481d24645";
  var FF_HOST = "https://funnelfighters.io";
  var FF_SDK = FF_HOST + "/sdk/funnelfighters.js";
  var PAGES = { "/": "home", "/mechanics": "mechanics", "/play": "play" };

  /* ── our own queue, NOT the vendor's ───────────────────────────────
     The vendor snippet queues calls on window.funnelfighters.q and the
     SDK is meant to replay them on load. It doesn't: its drainQueue()
     reads a `root` that is out of scope inside the SDK's factory, so
     the queue is silently dropped — init included, which is why zero
     events ever arrived (verified 2026-08-17 in headless Chrome:
     _accountKey null after load). So we queue here and flush ourselves
     the moment the SDK script fires onload. */
  var pending = [];

  function sdk() {
    var f = window.funnelfighters;
    return f && typeof f.init === "function" && typeof f.track === "function" ? f : null;
  }

  function call(method, a1, a2) {
    try {
      var f = sdk();
      if (f) f[method](a1, a2);
      else pending.push([method, a1, a2]);
    } catch (err) { /* a tracker never breaks the site */ }
  }

  function flush() {
    var f = sdk();
    if (!f) return;
    var q = pending; pending = [];
    for (var i = 0; i < q.length; i++) {
      try { f[q[i][0]](q[i][1], q[i][2]); } catch (err) { /* same */ }
    }
  }

  /* async loader: the vendor's script tag, plus onload → flush */
  try {
    var t = document.createElement("script");
    var s = document.getElementsByTagName("script")[0];
    t.async = 1; t.src = FF_SDK; t.onload = flush;
    s.parentNode.insertBefore(t, s);
  } catch (err) { /* blocked → every call below stays a no-op */ }
  window.addEventListener("load", flush);

  call("init", FF_SITE, { api_host: FF_HOST });

  /* ── the whole public API ───────────────────────────────────────── */
  var ff = window.ff = {
    /* page_view {page} — every tracked page, fired below on load */
    page: function () {
      var p = PAGES[location.pathname];
      if (p) call("track", "page_view", { page: p });
    },
    /* door_view {tab} — the door is on screen (gmail = the 010 door) */
    door: function (tab) { call("track", "door_view", { tab: tab }); },
    /* door_click {button} — a way in was chosen (gmail button, login form) */
    knock: function (button) { call("track", "door_click", { button: button }); },
    /* signup {method} — the canonical Funnel Fighters milestone: an
       account exists. Fired on the first /play after the Gmail door. */
    signup: function (method) { call("track", "signup", { method: method }); },
    /* signin_ok {method} — a climber came back through the door */
    signin: function (method) {
      call("track", "signin_ok", { method: method || "password" });
    },
    /* enter_game — /play actually opened, fired below on load */
    enter: function () { call("track", "enter_game", {}); },
    /* names the visitor so return visits line up with the account */
    who: function (u) { if (u) call("identify", u); }
  };

  /* auto: the page announces itself; /play is the game opening, and
     its script tag carries data-user (and data-door=signup|signin when
     the Gmail door just landed us here) so no extra fetch is needed */
  ff.page();
  if (location.pathname === "/play") {
    var tag = document.querySelector('script[src*="funnel.js"][data-user]');
    if (tag) {
      ff.who(tag.getAttribute("data-user"));
      var door = tag.getAttribute("data-door");
      if (door === "signup") ff.signup("google");
      else if (door === "signin") ff.signin("google");
    }
    ff.enter();
  }
})();
