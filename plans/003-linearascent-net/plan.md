# 003 — linearascent.net: the tower has a front door

## Decisions (revised)

- **Same server.** worldd serves the site itself — FastAPI routes on the
  existing service. No second service, no CDN, no framework. We don't
  have millions of users; a page render is nothing next to a game turn.
- **Old-days accounts.** Signup is a username and a password. Nothing
  else. No email, no oauth, no verification mail.
- **One font, one size, everywhere.** The whole site is a terminal:
  IBM VGA 8×16 (The Ultimate Oldschool PC Font Pack, CC BY-SA — vendor
  the woff2, no external font hosts). Hierarchy is done the ANSI way:
  ALL CAPS, bright/dim, reverse video, box-drawing borders — never a
  second font or a second size.
- **1-bit art only.** Every image on the page comes from (or goes
  through) the existing Bayer-dither pipeline. If a new image is
  needed, it's generated with `tools/generate_event_gifs.py` art
  direction: 1-bit, gold-tinted where the game gold-tints.

## What the comps teach (researched 2026-08-02)

- **Kingdom of Loathing**: signup lives ON the homepage and is one
  click deep; a live "290 players logged in" line does more selling
  than any feature list. Free + instant is the whole funnel.
- **Urban Dead**: one paragraph of atmosphere + a LIVE world counter
  sells a persistent shared world. Its death counter was the pitch.
- **Stoneshard**: concrete numbers beat adjectives ("200+ abilities,
  400+ equipment pieces"). A tagline of three imperatives. Real
  screenshots, many.
- **Loop Hero**: the page's FORM mirrors the game's core mechanic
  (the site literally loops). Ours must do the same: **the homepage is
  the tower — scrolling is climbing.** Sections are floors, the page
  chrome is the game's scene-card chrome, and a fixed status line
  plays the part of the in-game eyebrow.

## How we sell it

**Primary hook (the Urban Dead move):** *One tower. One world.
Everyone climbs the same one.* — backed instantly by live numbers:
`DAY 214 · 289 CLIMBERS · THE FRONTIER STANDS AT FLOOR 3 · WARDEN
IRONHOWL AT 62%, 4 BLADES ON IT`. The world is provably alive before
the visitor reads a single feature.

**Secondary hooks:**
1. *Your deeds outlive the world* — the Stone of Eras: when the tower
   is finished, the era closes and the finishers' names are carved
   forever. Permanence is rare; sell it hard.
2. *It plays where you already are* — a full MMO that fits in a chat
   window. Scene cards, not clients. Nothing to install to try it.
3. *The old-school covenant* (the KoL move): free, a username and a
   password like the old days, no email, no tracking, no launcher.
   Say this explicitly on the signup card — for this audience,
   the ABSENCE of friction is a feature worth advertising.

**Numbers to state plainly (the Stoneshard move):** 100 floors · 3
classes · one shared Warden per frontier · seasons ("eras") that end
and are remembered · the exact energy/day economy. Real numbers from
`economy.py`, never rounded up.

## The page, floor by floor

The nav is a gate. The scroll is the climb. A fixed one-line status
bar (the "eyebrow") rewrites itself as you pass each section, exactly
like the in-game eyebrow: `FLOOR 0 · THE GATE`, `FLOOR 1 · THE WORLD
THAT WAS`, … Every section is typeset as a scene card: box-drawing
border, eyebrow, HEADLINE, support line, body, options-as-links.

0. **THE GATE (hero).** The intro reel, full-bleed. Logotype over it.
   One line: *A tower. One world. Everyone climbs the same one.*
   Two options, rendered as game options: `[ CLIMB — free, no email ]`
   → signup, `[ WATCH ]` → scrolls to the lore. Below, live and dim:
   the climbers-online line (the KoL signal).
1. **THE WORLD THAT WAS (lore).** The intro movie retold as beats:
   each beat's GIF still + 2–3 typewriter lines. The world before,
   the tower's appearance, the gates, the Wardens, why everyone
   climbs. Ends on: *The tower does not care whose name is on the
   blade. The Stone does.*
2. **ONE WORLD (the differentiator).** The shared Warden explained
   with a live-animated wound bar: one HP pool, many named blades
   cutting it, damage that persists when you flee. Real current
   frontier Warden embedded with its real hp% and real striker names.
   Copy: *When it falls, the floor opens — for everyone.*
3. **YOUR CLIMB (how it plays).** The three classes as portraits
   (warrior / archer / sorcerer) with one honest line each. Beside
   them, a scene card that PLAYS ITSELF: a looped, scripted fight —
   typed lines, meters draining, an option row highlighting — built
   from real engine output, not mockups.
4. **THE FLOORS (content breadth).** The 10 floor-movie world stills
   as a horizontal strip; biome + gate town + Warden name under each.
   *One hundred floors. Ten of them filmed so far. The frontier
   decides how fast the rest matter.*
5. **THE SOCIETY.** Factions and banners, letters by relay, the
   fields (yes, you can be robbed in your sleep — say it; danger
   sells), the Guildhall, the Morning Crier. Four small scene-card
   screenshots, real ones.
6. **THE STONE OF ERAS (live).** The carved ledger, typeset like the
   in-game Stone. Every closed era: number, finisher, days it took.
   Copy: *This page will outlive the current world. So could you.*
7. **THE CRIER (live).** Three real gossip lines from today's paper +
   today's world-day. Proof of life, updated on every page load.
8. **THE DOOR (signup).** A terminal form, centered, nothing else on
   screen: `USERNAME ▮`, `PASSWORD ▮`, `[ ENTER THE TOWER ]`.
   Under it, dim: *A username and a password. Like the old days.
   Free. No email. Your name is your legend — choose it well.*
9. **FOOTER.** Version (live from /health's `game`), marketplace /
   Luna install link, FAQ, the era number. No social icons unless a
   Discord actually exists.

## Animations (all CSS/JS on real assets — no canvas, no libraries)

- **Typewriter** body lines with the caret block ▮ (the ANSI soul).
- **Dither-wipe reveals**: sections materialize through a Bayer-matrix
  threshold sweep (CSS steps() on a dither mask), not fades — fades
  are anti-1-bit.
- **The wound bar**: the shared-Warden HP pool draining under named
  cuts, looped.
- **The self-playing fight card** in §3.
- **The status-bar eyebrow** rewriting per section (single line,
  fixed top, reverse video).
- **The ticker marquee** with live world data.
- **GIF reels** carry the heavy motion (intro, floor beats) — they
  already exist and already loop.
- Respect `prefers-reduced-motion`: everything settles to stills.

## Art inventory

**Already in the repo (reuse as-is):**
intro movie reel + loop · floor world/keep beats ×10 · warden_fall ·
race/class portraits · warden art (`warden_001`…) · item/relic art ·
faction banners · strips and gate-town art.

**To generate (through the existing Veo → dither pipeline):**
1. `warden_slain` reel — already queued from plan 033.
2. **Logotype** — "LINEAR ASCENT" as 1-bit art (carved-stone or
   phosphor-glow treatment), plus a plain box-drawing text fallback.
3. **The tower cross-section** — one TALL 1-bit image (320×~2000),
   the whole tower cut open, floors visible; used as the page's
   scroll-spine in the margin, current scroll position = a lit floor.
   This is the site's signature piece.
4. **Class trio** — the three silhouettes together at the gate
   (echoes the warden_slain composition; same prompt family).
5. **OG card** 1200×630 — logotype + tower + one line, dithered, so
   Discord/Twitter unfurls look like the game.

**Font:** Web Plus IBM VGA 8×16 woff2, vendored into
`worldd/static/site/` (CC BY-SA 4.0 — credit in footer).

## Build

### Phase A — routes & accounts (worldd)
- `GET /` serves the page; `worldd/static/site/` holds css/js/art
  (static mount already exists).
- `GET /v1/public/world` — day, frontier, climbers, warden
  (name/floor/pct/blades), stone lines, crier lines, era list, game
  version. No HMAC, CORS open, 60s in-process cache.
- `POST /signup` — username + password. `ascent_accounts` table
  (username citext unique, pw bcrypt, created_at). Username rules =
  climber-name rules (it becomes the climber name — one identity).
  Session = signed cookie (itsdangerous-style HMAC, secret from env).
  `POST /login`, `POST /logout`. Rate-limit signup per IP (reuse the
  existing rate-limit shape).
- What an account IS at launch: the reserved climber name + the door.
  RECOMMENDED next plan: a browser client — worldd already computes
  scene cards; rendering them in HTML and POSTing options back is a
  thin page, and turns the site from brochure into the game itself.
  This plan ships the door; the room behind it is plan 004.

### Phase B — the page
- One `index.html`, one `site.css`, one `site.js`. No build step.
- Jinja not needed: the page is static except the live blocks, which
  `site.js` fills from `/v1/public/world`; JS-off leaves honest
  placeholders ("the world is alive; turn on scripts to watch it").

### Phase C — art
- Generate the five new pieces through the pipeline; wire the tower
  cross-section scroll-spine.

### Phase D — domain & ship
- Render dashboard: add linearascent.net + www to ascent-worldd
  (custom domains on the existing service — the one browser step).
- Registrar: apex ALIAS/A + www CNAME → onrender hostname. TLS auto.
- Verify: site live on the domain over TLS; `/health` game version
  unchanged by site deploys; signup → row present; ticker matches
  `/health`/world state; page under 1.5 MB first load with the hero
  reel, everything self-hosted.

## Acceptance

- [ ] linearascent.net (apex + www) serves the page from worldd, TLS.
- [ ] Signup: username+password creates an account; dup username says
      so in the card; session cookie survives refresh; logout works.
- [ ] `/v1/public/world` cached (60s) and CORS-open; ticker, wound
      bar, Stone, and Crier sections show REAL current data.
- [ ] One font, one size — verified by inspecting computed styles;
      zero external requests (fonts, analytics, CDNs: none).
- [ ] All art 1-bit/dithered; GIF reels loop; `prefers-reduced-motion`
      honored.
- [ ] JS disabled: full lore/sections readable, live blocks show
      placeholders, signup form still posts (plain form POST).
- [ ] Game untouched: worldd tests green; `/health` `game` unchanged
      by the site ship.

## Open questions

1. Browser play (plan 004): green-light designing the account →
   climber bridge now, or keep accounts as name-reservation until the
   web client exists?
2. Is there a Discord (or do we start one) before the footer ships?
3. Domain registrar choice — Cloudflare still recommended.
