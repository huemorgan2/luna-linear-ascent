# 009 — the port: the whole game under the terminal law

Reskin the live game (`render.py` SCENE_CSS + `pane.py` shell) to the
look approved in the mock (`worldd/static/site/mock/roothollow.html`,
plan 008). **Layout, DOM and behavior stay; only the skin changes.**
Below, every area of the game is taken in turn: what it looks like
now, and the concrete design it gets.

## The law (final state of mock.css)

- ONE font: WebPlus IBM VGA 8×16, 16px, line-height 1.5,
  font-smoothing off. Every `font-size:9–18px` in SCENE_CSS/pane
  (≈20) dies; hierarchy is redone with caps / bright / dim / reverse
  video. The Crier's Georgia serif dies: brown-ink VGA.
- Tokens:

      --bg      #000000   the only background
      --fg      #adaba0   body text
      --dim     #5b5952   dim ink and every border
      --bright  #fbfbf7   white — labels, headlines
      --gold    #f5b825   yolk yellow — keys, coins, accent, hover
      --hp      #8ed24a   green — HP, the climb
      --en      #45d0c0   cyan — energy, notifications, tips, badges
      --xp      #d967c8   magenta — XP, aether/violet things
      --hurt    #f26541   vermilion — damage, foe
      --brown   #b5722f   the Crier only
      --art     #d9d9d3   banners, creatures, icons, faces
      --artbright #fbfbf7 the player portrait

- No border-radius, no fades, no shadows, no color-mix panels.
- **Pixel icons and pixel art everywhere — a must.** Every 1-bit
  masked glyph stays: coin, bolt, lock, aether, sword/shield/bolt
  pips, item icons, race faces, faction sigils. Every image stays
  too: room banners, creature art, portraits, fx reels, strip
  bands, gallery art — same assets, same sizes, same placement.
  The port only changes tint (currentColor / --art / the token
  inks); nothing is swapped for text characters or emoji, nothing
  is dropped, and `image-rendering:pixelated` is non-negotiable on
  all of it.
- Font shipping: the scene card renders in two hosts (web pane and
  the legacy chat card), so the 22 KB woff is **base64-embedded as a
  data: @font-face inside SCENE_CSS** — both hosts get it, no route.

## Token map (keep constant names, swap values)

| constant | now | becomes |
|---|---|---|
| INK | #0b0e14 | #000000 |
| PANEL / PANEL2 | #11151f / #161b28 | #000000 |
| BORDER | #232a3a | #5b5952 |
| DIM | #8b93a7 | #5b5952 |
| FAINT | #5b6275 | #5b5952 (folds into DIM) |
| TEXT | #e6e9f2 | #adaba0 |
| GOLD | #f5a524 | #f5b825 |
| AETHER | #5eaefc | #45d0c0 |
| VIOLET / VIOLET_SOFT | #8b5cf6 / #a78bfa | #d967c8 |
| RED | #f4645f | #f26541 |
| OK | #3ad29f | #8ed24a |
| ORANGE | #ff9a3c | #f5b825 (folds into GOLD) |
| new: BRIGHT / ART / ARTBRIGHT | — | #fbfbf7 / #d9d9d3 / #fbfbf7 |

`_coin`, `_xp`, `_stat_gain`, `_paint_amounts`, banner/variant tint
maps all read these constants — they port for free.

---

# Area by area

## A. The scene card frame (every screen)

Now: `.card` blue-gray panel `#11151f`, 14px system mono, 1px
`#232a3a` border; `.eyebrow` small caps in dim ink on the panel.

Design: black card, `1px solid var(--dim)` border, padding kept.
`.eyebrow` becomes a true reverse-video bar — `background:var(--fg);
color:#000`, full card width, caps — exactly the mock's
`ROOTHOLLOW · THE SQUARE` bar sitting flush under the banner art.
`.headline` bright, `.support` fg, `.body` fg, `.later` dim.
Banner art: mask tint moves from DIM-gray to `var(--art)` near-white;
`border-bottom:1px solid var(--dim)` separates it from the eyebrow.
Tint exceptions keep meaning in the new inks: death→hurt,
present/loot→gold, alpha→gold, tough→xp, runt→dim.

## B. Option rows (every menu in the game)

Now: `.opt` bordered button rows, panel background, hover lightens.

Design: the mock's door idiom, one line per option —

    [ 1] The Lodge · · · · · · · · · · · pay ◎ 10/night [i]

- `[ n]` key in gold (`white-space:pre` keeps the column), label
  bright, dot-leader fill in dim (`.leader::after` with `·` content,
  `overflow:hidden`), hint right in dim, `[i]` marker last.
- Row padding `.3rem 0` (the taller-selection rule).
- Hover/focus = reverse video: black text on gold across the row.
- Locked: label+key dim, lock glyph in the hint, hover = black on dim.
- Badge (letters waiting etc.): cyan reverse video `[2]`.
- The "click a door — or reply with a number" helper line and the
  blinking caret are removed (mock decision); the input wiring stays.
- Aether-costed options keep the bolt glyph, tinted cyan.

## C. The square (town scene)

The mock is the spec, 1:1: banner, eyebrow, headline/support, NEXT
line dim, 14 door rows (key colors where the scene tags them: gold
trade / green climb / cyan town), then profile (D), presence (E),
the Crier (F). No layout change — this is what `_town_scene` already
emits, restyled.

## D. Profile: ident, meters, pips, pack

Now: `_ident_html` + `_meters_html` bars in blue-palette inks,
`_pip_row` masked pips, `_inventory_html` slot grid, portrait tinted
white on panel.

Design (mock, verified):
- Ident line: `Wick · human warrior` left, `LEVEL 1 · COINS ◎ 240`
  right, gold amounts, both ends of one flex row.
- Meters on ONE line when they fit: `HP 52/52 ▓▓▓▓▓▓▓▓ ·
  ⚡ 24/25 ▓▓▓▓▓▓▓░ · XP 120/600 ▓▓░░░░░░` — `▓░` text blocks
  colored hp-green / en-cyan / xp-magenta; low HP flips the whole
  meter to hurt.
- Pip rows: ATK gold swords, DEF fg shields, SPD cyan bolts, off
  pips dim — same masks, retinted.
- Pack: 40px cells, `1px solid var(--dim)`, dashed when empty,
  icons `var(--art)`; hand/shield labels dim lowercase. The pack
  popup menu (`.pmenu`) restyles to the tip idiom: black, cyan
  border.
- Portrait: `var(--artbright)`, no border, stretched as today.

## E. Players here (presence)

Now: `.ptile` panel tiles, tiny 10–11px name/level text.

Design (mock): 7-across grid of bordered tiles, race face masked in
`var(--art)` (giants get the bigger stamp), name bright, `L4` dim —
both at 16px now, tile just gets wider. Sleeping = cyan `Zzz` over
the face. Hover = gold reverse video, face flips to black. Tile
tooltip (`◎ 610 carried · ⚡ 25`) via the [i]/tipbox idiom.

## F. The Crier (paper)

Now: parchment texture image, Georgia serif, 12px masthead.

Design (mock): flat black sheet inside a `1px` brown border, all ink
`var(--brown)`, masthead a brown reverse-video bar
(`THE MORNING CRIER · DAY 214`), body lines with dim `·` bullets.
No texture, no serif, no second size.

## G. Fight screens (wilds, warden, boss, PvP)

Now: `.bwrap` art with floating `.echip` (HP·ATK·DEF, 12px, corner
plate), `.dx` dossier `<details>` fold, combat lines via
`_combat_html`, tally heaps.

Design (mock fight, verified):
- Headline: creature name only — stats never repeat in text.
- The plate under the art: `WOLF 10/10` + red `▓░` bar, ` · ◇ at
  range` dim, `[i]` dossier tip at line end; then ATK/DEF/SPD pip
  rows identical to the player's (gold/fg/cyan), so the two sides
  read in the same grammar; dim status line ("its blows land at
  HALF…") last.
- The `.echip` corner chip dies; its content lives in the plate.
- Dossier: the fold's text moves into the `[i]` data-tip (44ch cyan
  box). The `<details>` stays in DOM as no-JS fallback, restyled.
- Combat log: `· ` dim prefix per line; damage numbers hurt, heals
  hp-green, emphasis bright; "you take 3" whole-line hurt.
- Tally (the haul): coin glyphs gold, XP marks magenta, counts
  tabular — retint only.
- Player rail at the bottom: same one-line meters as D.

## H. Forge / Arcanum / shops (card walls)

Now: `.ggrid/.gcard` tile wall, panel tiles, 12px sub text, hover
lightens; `.gtile .gsub` dim small.

Design: tiles keep the grid (`minmax(20ch,1fr)`), go flat black with
dim borders; icon masks `var(--art)` 56px; name bright, stat line
fg, price `◎` gold, durability dim — all 16px. Hover: gold reverse
video, icon flips black (mock forge behavior). Locked tier tiles:
all-dim with lock glyph. Buy rows under the wall use idiom B.

## I. School

Now: rank bars `▰▱` with per-weapon rows, small caps headers.

Design: keep the `▰▱` glyph bars — they are already the law; ranks
colored gold when mastered, fg otherwise; row = door idiom with the
bar where the dot leader would be. Fold (`.fold`) restyles to a dim
`▸` line that brightens on open; no animation.

## J. Vault / strips

Now: `.stripband` art band with 18px overlay text.

Design (mock vault, verified): art band masked `var(--art)` with a
centered bright line in a bordered box below (`DEPOSITED: ◎ 1,200`),
border-top dim, 16px. Interest stubs as dim `·` lines with gold
amounts; strongbox line with lock glyph; deposit/withdraw options
via idiom B.

## K. Notices, ask, toasts, error bar

- `.notices/.nrow`: cyan key column stays; 11px→16px; border dim.
- `.ask` (confirm boxes): black, cyan border (it interrupts — it
  uses the tip ink), options via idiom B.
- `showToast`: black, gold border, bright text, steps() appearance,
  no fade.
- `.errbar`: black, hurt border+ink, 16px.

## L. Interstitials: death, present, level-up, fx

Now: `.fx` full-card art moments with violet/gold tints, `.actband`
action band.

Design: keep the moments; tint via the new map (death art in hurt,
presents in gold, ascent fx in magenta); text lines centered bright
over black; `.actband` becomes a gold reverse-video bar. Any
transition that isn't `steps()` is cut.

## M. Gallery / shard / npcbox

- `.gal/.gcell`: dim-border cells, art `var(--art)`, captions dim.
- `.shard`: gone from the mock — keep the class as a plain dim line
  (engine may still emit it).
- `.npcbox` (dialog): black, dim border, speaker name bright caps,
  lines fg — a card within the card, no tint.

## N. Tooltips (both hosts)

Now: `#tipbox` dark panel, shadow, rounded, 340px.

Design: black, `1px solid var(--en)`, fg text, `.5rem 1ch` padding,
44ch max width, square corners, no shadow. `[i]` markers dim → cyan
on hover/focus; TIP_JS positioning logic untouched.

## O. The pane shell (`pane.py`)

- Base: html/body black, VGA 16px/1.5, smoothing off.
- Tabs `GAME · SCORE · COMMUNITY`: dim caps buttons, dim-border
  strip; active tab = black-on-gold reverse video (hover idiom as
  active state); hover on inactive = fg.
- `.placeholder/.panel/.membar`: black, dim border, reverse-video
  eyebrow.
- Buttons `.btn/.mini`: black, dim border, fg ink; hover/focus gold
  reverse video; minis lose their 12px.
- Inputs `input/select/textarea.ti`: black, dim border, fg text,
  cyan border on focus (the attention ink), block caret color gold.
- Sound bar `.sndbtn`: dim icon+label, fg on hover; feedback badge
  `.fbbadge`: cyan reverse video (notification ink — not red).
- Feedback panel `#fbpanel/.fbmsg`: black sheets, dim borders, meta
  lines dim caps, unread cyan; thumbs strip cells dim-bordered.
- Score tab (muster roll): rows as door lines — rank `#1` gold,
  name bright, dot leader, count right; header caps dim.
- Community tab (charters): same list idiom; faction sigils masked
  `var(--art)` 16px inline.
- Enroll/login forms: idiom K inputs + B buttons; field labels dim
  lowercase left of input, one per line.

---

# The screen inventory — every scene, its areas, its one specific note

Verified against the engine (every `*_scene` in core/social/combat/
hall and both pane hosts). Format: screen → areas that skin it →
what is specific to that screen.

**Town & shops**
- Square (`_town_scene`) → A,B,C,D,E,F — the mock 1:1.
- Forge (`_forge_scene`) → A,B,H — tier tabs as caps text, active
  gold reverse video.
- Arcanum (`_arcanum_scene`) → A,B,H — same wall, staves/charms.
- Medlab (`_medlab_scene`) → A,B — carried-items line dim, prices
  gold.
- Lodge (`_lodge_scene`) → A,B — Long Fire words as dim `·` quotes
  under a bright `▣ THE LONG FIRE` caps line (mock, verified);
  `activity` line dim.
- Sleep menu / Sleeping (`_sleep_menu_scene`, `_sleeping_scene`) →
  A,B,L — asleep screen: fx art dim-tinted (the one place art is
  NOT near-white: sleep is `var(--dim)` — it reads as night),
  wake option the only bright thing.
- Board (`_board_scene`) → A,B — jobs as dim `·` lines, pay gold,
  XP magenta, progress `0/5` dim.
- Vault (`_vault_scene`) → A,B,J — the shelf strip.
- Pawn (`_pawn_scene`) → A,B — offer lines fg, amounts gold.
- School (`_school_scene`) → A,B,I — `▰▱` bars.
- Stone (`_stone_scene`) → A,B — CLIMB AHEAD ladder: LEVEL/FLOOR
  headers bright caps, `+` rows dim, costs gold.
- Relay (`relay_scene`) → A,B,K — letters as fg lines, enclosed
  gold bright; write-flow `ask` in K style.
- Fields (`fields_scene`) → A,B — attack rows: name bright, `L2 ·
  3⚡` hint with cyan bolt.
- Grant desk (`grant_scene`, `_grant_amount_scene`) → A,B,K —
  amount entry uses the K input style.

**The climb**
- Gate (`_gate_scene`, `_gate_town_scene`) → A,B — floor rows with
  region name as dim hint (mock, verified).
- Floor movie / arrival (`_floor_movie_scene`,
  `_floor_arrival_scene`) → A,L — fx reel; caption lines centered
  bright; npc greeter via M.
- Wilds fight (`fight_scene`) → A,B,G — the mock fight 1:1.
- Warden / boss (`warden_scene`, `boss_scene`, `_warden_keep_scene`,
  `_boss_keep_scene`) → A,B,G,E — players_here grid on the warden
  door (E); keep screens are G's plate without options.
- Warden slain / fallen (`_warden_slain_scene`,
  `_warden_fallen_scene`) → A,L — gold-tinted fx, tally in G style.
- NPCs (`_npc_scene`, `_keeper_scene`) → A,M — npcbox.

**Player**
- Profile (`_profile_scene`) → A,D — the square's profile block,
  full width.
- Memorial (`_memorial_scene`) → A,E,L — the fallen as E tiles with
  dim faces (not art-white); fx in hurt tint.
- Intro / creation (`_intro_scene`, `_creation_race_scene`,
  `_creation_name_scene`) → A,B,L,M — race pick: gallery cells with
  race portraits in `var(--artbright)`, chosen cell gold reverse
  video; name entry: K input, the one text field in the flow.
- Death / present / level-up fx → L.

**Guild (hall.py suite)**
- Hall home (`hall_scene`, `_home_scene`) → A,B,J — banner strip in
  J style with the faction sigil.
- Coffer / chest / chest-put (`_coffer_scene`, `_chest_scene`,
  `_chest_put_scene`) → A,B,D — chest grid reuses the pack slot
  style (D); put/take rows idiom B.
- Bulletin (`_bulletin_scene`) → A,B,K — post ask in K.
- Bunks (`_bunks_scene`) → A,B,E — bunk occupants as E tiles.
- Works / desk (`_works_scene`, `_desk_scene`) → A,B,K.
- Guildhall town door (`guildhall_scene`, `_guild_dir_scene`,
  `_banner_page_scene`, `_founding_scene`) → A,B,J,M — directory
  gallery cells = sigil masked art + name bright + dues dim.

**Pane chrome (`pane.py`)** → O — tabs, score, community, enroll,
sndbar, feedback, error bar, toasts; nothing outside O's list.

---

## Order of work (verify each before the next)

1. Token swap + BRIGHT/ART/ARTBRIGHT constants + embedded @font-face
   in SCENE_CSS + pane base font/black. (~80% of the look lands.)
2. A+B: card frame, eyebrow, door rows, N tooltips.
3. G: fight plate, dossier→tip, log, tally.
4. D+E: profile, meters, pips, pack, presence.
5. F+H+I+J: Crier, shops, school, vault strips.
6. K+L+M: notices/ask/toasts, interstitials, gallery.
7. O: pane chrome — tabs, buttons, forms, sndbar, feedback, score,
   community.
8. QA: side-by-side pane vs mock per screen; live Roothollow with a
   real player doc; chat-card host opened raw (font present via
   data: face, no fetch to worldd).

## Verify

    cd worldd && .venv/bin/uvicorn app.main:app --port 8971
    # /static/site/mock/roothollow.html vs /play — same font metrics,
    # inks, idioms; devtools: VGA 16px everywhere, zero radius, zero
    # transitions, no font-size other than 16px.
    cd worldd && .venv/bin/python -m pytest

## Out of scope

Content changes, layout changes, new screens, site.css edits. The
mock retires once this lands.
