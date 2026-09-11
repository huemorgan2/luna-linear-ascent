# Floor maps 1–10 — isolated local QA preflight

2026-09-09. Baseline inspection only. Changed-feature acceptance is pending phase 3.

## Running services

| Consumer | Local URL | Process / exec session | Database |
|---|---|---|---|
| worldd + website | http://127.0.0.1:8600/play | PID 95598 / session 81189 | `ascent_maps_browser` |
| QA Luna + rich Chat UI | http://127.0.0.1:8799 | PID 98723 / session 41165 | `luna_maps_qa85` |

worldd health returned `ok: true`, `db: true`, game `0.110.3` before integration. Its `ASCENT_GAME_PATH` explicitly points to the plugin source checkout. No production database, session, or worldd credentials are in use.

The new `ascent-floor-maps-qa` Docker container uses Postgres 16, bound only at `127.0.0.1:55440`, with user `ascent_qa` and **test-only password** `ascent_qa_only`. It contains two deliberately separate databases:

- Browser play: `postgresql://ascent_qa:ascent_qa_only@127.0.0.1:55440/ascent_maps_browser`
- Destructive/full-suite tests: `postgresql://ascent_qa:ascent_qa_only@127.0.0.1:55440/ascent_maps_tests`

The browser database contains disposable website account `MapsQA85` (test-only password `maps-qa-only`), and tenant `maps-qa-luna` with test-only secret `maps-qa-shared-only`. No existing player was reset.

QA Luna uses a newly created database on the existing local `luna-postgres` container: `postgresql+asyncpg://luna:luna@127.0.0.1:5433/luna_maps_qa85`. Its isolated files are in `/tmp/ascent-maps-qa85/`: `serve-luna.py`, `luna.log`, `managed/`, and `image-set/`. The image-set symlinks the existing source Ascent plugin and existing rich Chat UI plugin. The launcher loads only LLM provider keys from the local Luna `.env`; it supplies isolated database, JWT, vault, Redis DB 13, managed directory, and worldd configuration itself. It runs with `/tmp/ascent-maps-qa85` as CWD so unrelated `.env` settings are not loaded.

QA Luna account: `mapsqa85`, test-only password `maps-qa-luna-only`. Setup completion was applied only to that account in the new database. Full chat is visible and ready at conversation `ce080e20-79c7-4281-929d-a17b540d5a1f`. No LLM turn has been sent yet. The UI's default model is Claude Sonnet 4.5; provider availability is configured, but a successful provider response has not yet been verified.

## Commands / restart notes

Create the isolated worldd container and test database (already done):

```sh
docker run --name ascent-floor-maps-qa -e POSTGRES_USER=ascent_qa -e POSTGRES_PASSWORD=ascent_qa_only -e POSTGRES_DB=ascent_maps_browser -p 127.0.0.1:55440:5432 -d postgres:16-alpine
docker exec ascent-floor-maps-qa createdb -U ascent_qa ascent_maps_tests
```

From the repository's `worldd` directory:

```sh
env DATABASE_URL=postgresql://ascent_qa:ascent_qa_only@127.0.0.1:55440/ascent_maps_browser ASCENT_SHARED_SECRET=maps-qa-shared-only ASCENT_ADMIN_KEY=maps-qa-admin-only ASCENT_GAME_PATH=/Users/roy/Documents/my-projects-docs/luna-linear-ascent/plugin-linear-ascent GOOGLE_CLIENT_ID= GOOGLE_CLIENT_SECRET= .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8600
```

Use `python -m uvicorn`: the venv's standalone uvicorn script has a stale shebang referencing the former Google Drive path.

Restart QA Luna after changed tool registration/implementation:

```sh
/Users/roy/Documents/my-projects-docs/luna/.venv/bin/python /tmp/ascent-maps-qa85/serve-luna.py > /tmp/ascent-maps-qa85/luna.log 2>&1
```

When invoking worldd tests, explicitly set both `ASCENT_TEST_DATABASE_URL` and `DATABASE_URL` to the **ascent_maps_tests** URL. The suite must never use the browser DB.

## Baseline observations

All screenshots were opened/read. Browser interaction used CUA's real in-app browser. Chrome was unavailable; in-app browser works in this subagent with a background tab. Tab 1 is the website, tab 2 is Luna; both are marked for handoff.

1. Fresh creation worked: nine story cards, tower gate, warrior lineage, Roothollow. Floor-1 introduction has readable 1-bit banner and numbered Next / Skip options.
2. The baseline camp is a conventional numbered list. Labs exposes `Floor maps — off`, `switch on · floors 1`. Switching it on replaces the camp with the current floor-1 map.
3. The map renders a large realm view with black overlaid labels: `[1] HUNT 1`, `[2] BRACKJAW`, `[3] CAMP`, `[4] GATE`, `[5] ROOTHOLLOW`. Navigating Gate and Roothollow works.
4. The elevator defect is reproduced. On Roothollow → Gate → Floor 1, the animated machinery appears over a translucent dark veil; the next map, labels, character, meters, and bottom buttons remain visible behind it. See `screenshots/03-baseline-lift-translucent.png`.
5. Re-selecting the same floor through Gate alone does not trigger the elevator; changing from Roothollow does. This matters when reproducing the transition.
6. Server truth after the baseline: website player `mapsqa85`, floor 1, location `gate_town`, HP 80, coins 50, energy 24, level 1; Labs `floormap: true`. Navigation did not spend gold or energy.
7. QA Luna loaded the source Ascent plugin with `ascent_scene`, `ascent_choose`, and `ascent_character` registered and enabled. Its package manifest advertises 0.99.0 while code is 0.110.3 (pre-existing version drift). The initial built-in basic chat was replaced by the existing local rich Chat UI 0.29.4 via the isolated image-set; no Luna implementation files were changed.

## Preservation / limitations

The existing Luna checkout's dirty `luna/plugins/boot.py`, untracked `luna/data/first_conversation.py`, untracked corresponding test, and dirty dojoP state were preserved. No branches, commits, deployment, or implementation edits were made by the QA subagent.

Luna's optional memory embedder warm-up timed out twice at boot; no chat turn was attempted. This is an observed preflight limitation, not a demonstrated game blocker.

Pending acceptance after phase 3: maps 1–10 on by default; floor-11 fallback; 320px/390px chip and tooltip clipping; instant hover/focus explanations; mixed-row numeric routing; floor-10 GNARL label; black lift at first frame and midride; hidden input blocked; real Luna query `show me floor 2`, then the displayed GATE number. The live walk-through must include actual model turns and server-state checks before completion.
