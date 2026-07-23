---
name: gemini-image
description: >-
  Generate or edit images with Google's Gemini image models (Nano Banana /
  Nano Banana Pro) via a stdlib-only script — and know when NOT to use it:
  Linear Ascent in-game banners go through the dedicated 1-bit pipeline
  (tools/generate_banners.py), not this script. Use this skill when the user
  asks to generate, create, make, or edit an image, illustration, banner,
  marketing visual, asset, texture, or background.
---

# Gemini image generation (Nano Banana)

Generates and edits images through Google's Gemini image API. The
`user-nano-banana` MCP is pinned to a retired model id
(`gemini-2.5-flash-image-preview`, now 404), so use the script here instead —
it targets current models and resolves the key itself.

## ⚠️ In-game banners have their own pipeline

**Do not use this script directly for Linear Ascent scene banners.** The
game's 320×112 white-ink 1-bit banners are produced by the dedicated
pipeline (Gemini → crop → Bayer 1-bit → white ink on alpha):

```bash
cd plugin-linear-ascent
LUNA_GEMINI_API_KEY=... python tools/generate_banners.py [slug ...]
```

Styleguide: `plugin-linear-ascent/design/pixel_art.md`. Requires PIL + httpx
and a sibling checkout of `plugin-image-gen`. Model originals land in
`content/art/banners/raw/` (untracked — regenerable); dithered results in
`content/art/banners/`. Review banners as a sheet, tinted on `--panel`;
regenerate by slug until every banner reads at a glance.

Use the script below for everything else: marketing/listing visuals, README
imagery, mockups, one-off references.

## Quick start

List current image-capable models:

```bash
python3 .cursor/skills/gemini-image/scripts/gen.py --list-models
```

Generate a new image (writes the file path to stdout):

```bash
python3 .cursor/skills/gemini-image/scripts/gen.py \
  --prompt "PROMPT HERE" --out path/to/image.png --aspect 16:9
```

Edit / restyle an existing image (pass it as `--ref`; repeat for multiple
references):

```bash
python3 .cursor/skills/gemini-image/scripts/gen.py \
  --prompt "make the tower taller, add mist around the base" \
  --ref path/to/image.png --out path/to/image-v2.png
```

After generating, **view the result** (Read the image file) to confirm
quality before moving on. Embed it in the reply with `![alt](absolute_path)`
so the user sees it.

## Models

- `gemini-3-pro-image` — "Nano Banana Pro", highest quality, best at clean
  composition and obeying "no text". **Default.**
- `gemini-2.5-flash-image` — cheaper/faster; fine for simple abstract visuals.
- Pick with `--model`. Aspect ratios: `1:1 16:9 9:16 4:3 3:2 21:9`.

## Key resolution

The script finds the key automatically (no need to ask the user), in order:
`--api-key` → `$GEMINI_API_KEY` → `~/.cursor/mcp.json` → `./.env` or
`../luna/.env`.

## Prompting for clean, narrative visuals

These rules produce simple images that *explain* rather than decorate:

- State the **subject + one idea** only. One concept per image.
- Always end with: **"no text, no words, no letters, no logos, no icons, no
  emojis"** unless text is explicitly wanted (Nano Banana Pro can render
  text well if asked).
- Specify **style + palette + mood + background** for a cohesive set. Reuse
  the same style sentence across a series so they look like one family.
- Specify **composition / negative space** (e.g. "lots of negative space,
  subject centered, room for a headline on the left").
- For a matching set, generate the first, then pass it as `--ref` to anchor
  the style of the rest.

Example style anchor (Linear Ascent marketing aesthetic — the game's world,
not its in-game 1-bit look):
> "...frontier village at the foot of a colossal arcanotech tower, dusk
> light, muted earth tones with faint aether-cyan accents, painterly and
> weathered, fine film grain, minimal, no text, no logos, no icons, no
> emojis."
