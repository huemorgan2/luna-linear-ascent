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

  /* ── the vendor's loader snippet, verbatim ──────────────────────── */
  (function (m, a, r, k, e, t) { m['FunnelFighters'] = e; m[e] = m[e] || function () {
    (m[e].q = m[e].q || []).push(arguments); }; m[e].l = 1 * new Date(); t = a.createElement(r);
    var s = a.getElementsByTagName(r)[0]; t.async = 1; t.src = k; s.parentNode.insertBefore(t, s);
  })(window, document, 'script', FF_SDK, 'funnelfighters');

  /* pre-load, funnelfighters is the queue function; post-load the SDK
     owns it. Call methods when they exist, queue when they don't. */
  function call(method, a1, a2) {
    try {
      var f = window.funnelfighters;
      if (!f) return;
      if (typeof f[method] === "function") f[method](a1, a2);
      else f(method, a1, a2);
    } catch (err) { /* a tracker never breaks the site */ }
  }

  call("init", FF_SITE, { api_host: FF_HOST });

  /* ── the whole public API ───────────────────────────────────────── */
  var ff = window.ff = {
    /* page_view {page} — every tracked page, fired below on load */
    page: function () {
      var p = PAGES[location.pathname];
      if (p) call("track", "page_view", { page: p });
    },
    /* door_view {tab: signup|signin} — the door is on screen */
    door: function (tab) { call("track", "door_view", { tab: tab }); },
    /* signup_try / signup_ok / signup_err {reason} */
    signup: function (step, reason) {
      call("track", "signup_" + step, reason ? { reason: reason } : {});
    },
    /* signin_ok — a climber came back through the door */
    signin: function () { call("track", "signin_ok", {}); },
    /* enter_game — /play actually opened, fired below on load */
    enter: function () { call("track", "enter_game", {}); },
    /* names the visitor so return visits line up with the account */
    who: function (u) { if (u) call("identify", u); }
  };

  /* auto: the page announces itself; /play is the game opening, and
     its script tag carries data-user so no extra fetch is needed */
  ff.page();
  if (location.pathname === "/play") {
    ff.enter();
    var tag = document.querySelector('script[src*="funnel.js"][data-user]');
    if (tag) ff.who(tag.getAttribute("data-user"));
  }
})();
