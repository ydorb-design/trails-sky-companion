# Trails in the Sky 2nd Chapter companion: plan

A second-screen companion for **Trails in the Sky 2nd Chapter** (Switch, title ID
`01007A2027548000`, update **1.0.3 / v327680**) that runs in both:

- [Peanuts Native](https://github.com/igawa6/peanuts-native): rewrites the game to run natively on
  Android. Lists Trails 2nd Chapter at update 1.0.3 with **bring-up** status, so expect rough
  edges on the Peanuts side.
- [Eden Duo](https://github.com/igawa6/eden-duo): the emulator. It uses the same package format,
  and the dev and reverse-engineering tools live there.

Built the same way as the packages in
[eden-duo-companions](https://github.com/igawa6/eden-duo-companions).

> History: this repo started as an FF Resonance companion. Dropped on 2026-11-25 because one was
> already published (1.0.0 by danielcamilo1). Checked the same day: eden-duo-companions'
> `catalog.json` has nothing for `01007A2027548000`. The repo is being renamed to
> `trails-sky-companion` (local folder is still `~/trails-companion`).

## Peanuts Native compatibility rules

Peanuts Native embeds the Eden Duo companion runtime, so one package can serve both. These rules
come from its dev notes (PEANUTS.md, Nov 2026) and from what the FF Resonance companion showed:

- **Runtime.** PEANUTS.md said runtime 24 (Eden Duo 1.3.5.1). But the FF Resonance companion
  needs runtime 25 and is tested on Peanuts on the Thor, so Peanuts has probably moved to 25.
  Confirm the exact version on the Thor before using any runtime-25 feature (`@screen.*`,
  `canvas_alt`, `L3`/`R3` buttons). Check again before release.
- **Native modules work** (`modules/android-arm64-v8a/<title>.so`).
- **No guest calls** from the runtime (calling the game's own functions directly). Treat it like
  Android NCE: memory reads, guarded writes or button presses only.
- **Guest helpers / load plans do work**, with one catch: the FF Resonance helper only installs
  if frame generation is **off** when the game starts (it can be turned on afterwards). Still,
  start read-only and add a helper only if a feature really needs one.
- **Build ID.** Target the 1.0.3 (v327680) update build, the one Peanuts supports. Peanuts passes
  the full build ID to modules (`PN_BUILD_ID`).
- **Bring-up status.** Peanuts doesn't fully support this game yet. Note any crashes or glitches
  on the Thor separately from companion bugs, and re-test when Peanuts updates.
- **Engine: no template.** Trails 2nd Chapter runs on Falcom's own engine, and no existing
  companion uses it (the HD-2D/Unreal modules such as `ffr_*` and `ot0_*` don't apply). Asset
  formats (fonts, text, art, maps) have to be worked out from scratch. So the first versions
  rely on memory reads and the runtime's own widgets, and decoded game art comes later.
- **Final testing happens on the handheld in Peanuts**, not just in Eden Duo. Peanuts needs
  Android 13+, a Snapdragon GPU with Vulkan 1.3 and 12 GB RAM (developed on the AYN Thor).

## How a companion works (short version)

- Eden Duo runs the game on screen 1 and draws a **companion page** on screen 2.
- The companion is a `.dsmod.zip` package:
  - `manifest.json`: the pages, widgets (rect, label, value, bar, button, image, map, chart...),
    data bindings and touch actions. This is the "design" layer.
  - `<BUILD16>.json`: where each value lives in the game's memory, for one exact game build.
  - optional native module (`.so`, C/C++): for data too complex for simple pointer chains.
- Packages ship **no game assets**. Art, fonts and text are decoded at runtime from the
  player's own game dump.

## Why this is a good candidate

- Turn-based battles with turn order and party HP/EP/CP, Arts and Crafts: a battle panel is a
  natural fit for a second screen. (Check on the Thor how the remake's battle HUD presents turn
  order before designing around it.)
- Field info that the main screen hides behind menus: party status, mira, the Bracer notebook
  (quests), orbment/quartz setup, area map.
- No existing companion and no template means more reverse-engineering, but also nothing to
  duplicate.

## Save data

- There's no Switch save yet. The old save is from the Steam version, which isn't the same game
  build, so it can't be used here.
- Start a **new game on the Thor** (in Peanuts), then copy that save to Eden Duo on the desktop
  so both run from the same state.
- Early-game saves are enough for Phases 1-3 (party, HP, mira, first battles). Keep a few
  save slots at useful moments (just before a battle, in town, in a dungeon) for repeatable
  tests.

## Phases

### Phase 0: Prerequisites (you)
- [x] Dual-screen handheld: **AYN Thor** (Peanuts Native's own test device).
- [x] Dev machine: **CachyOS** (Arch-based) with Hyprland and an RTX 3070. Install packages
      with `yay -S <pkg>` (not apt, and never `sudo yay`). Windows isn't a supported dev path:
      companion modules only load as `linux-x86_64` or `android-arm64-v8a`, so a Windows Eden
      can't run ours, and the docs, tools and headless test loop assume Linux. WSL2 can't
      reliably run the game (GPU).
- [x] Claude Code installed on the Linux machine, this repo cloned there.
- [x] `prod.keys`, `title.keys` and firmware 22.1.0 in `~/trails-files/` (outside the repo,
      never committed).
- [x] Update 1.0.3 in `~/trails-files/update/v-trails_in_the_sky_2nd_chapter_v327680.nsp`.
- [x] Base game dump `~/trails-files/Trails in the Sky 2nd Chapter.xci`.
- [ ] Build and play it in Peanuts Native on the Thor.
- [x] First save, made on the desktop in Eden instead of the Thor (same build): after the
      opening cutscenes, Estelle alone in the field, objective "Look for Cassius". Backed up to
      `~/trails-files/saves/2026-11-25-after-opening/` (slots `save000`, `save015`).
- [x] More saves, backed up to `~/trails-files/saves/2026-11-25-battle-and-town/`:
      `save002` Balstar Channel dungeon, Estelle + Anelace Lv.25 (**battle save**);
      `save001` City of Rolent (**town save**); `save015` is the autosave. On the Load screen
      (Title > Load Game) slots are listed autosave first, then newest first.
- [x] Confirm the game also boots in Eden Duo on the desktop: reaches the title screen
      (Ver.1.03) with the update applied, menu input works (2026-11-25).

### Phase 1: Dev environment
- [x] Clone eden-duo and eden-duo-companions (in `~/Projects/eden/`).
- [x] Install the missing build libraries:
      `yay -S --needed boost catch2 enet vulkan-utility-libraries spirv-headers`.
- [x] Build `eden-cli` (Linux, `EDEN_DSMOD_BUILD_DEV_TOOLS=ON`) from eden-duo. Configure with
      `-DENABLE_QT=OFF -DYUZU_TESTS=OFF -Dzstd_FORCE_BUNDLED=ON -Dlz4_FORCE_BUNDLED=ON
      -DVulkanHeaders_FORCE_BUNDLED=ON`: the companions modules project compiles zstd and lz4
      from eden-duo's `.cache/cpm`, which stays empty when the system copies are used.
      **Local patch needed with GCC:** `src/core/mods/mod_actions.cpp:300` declares `pad` but
      never uses it, which fails under `-Werror`; marked `[[maybe_unused]]` (eden-duo
      `ba7c910`). Reapply after updating eden-duo; worth reporting upstream.
- [x] Build the companions' native modules project once to prove the toolchain (dq3 and
      wonder built, in `~/Projects/eden/build-mods`).
- [x] Keys and firmware 22.1.0 installed in `~/.local/share/eden`.
- [x] Learn the headless screenshot/input loop (`--aux-virtual`). Done with Trails itself, since
      the existing companions need dumps of their own games: `tools/headless_run.sh`.
- [x] Isolated test profile (`~/trails-files/test-profile`, made by
      `tools/reset_test_profile.sh`), so test runs and memory writes never touch the real saves.
      Note the gdbstub listens on all interfaces (0.0.0.0:6543) during test runs.
      **Fixed 2026-11-25:** the copied config's absolute `nand/sdmc/load/dump_directory` paths
      kept pointing at the real profile (a portable `./user` doesn't override them), so earlier
      sessions used the real save folder. The real saves were checked and are byte-identical to
      the backups (no autosave happened). The reset script now rewrites those paths, and
      `tools/check_test_profile.sh` refuses to boot unless they're inside the test profile.
- [x] Install the update into Eden: `eden-cli --install <update.nsp>` (loader then reports
      "Update (v0.5.0) applied", i.e. v327680).
- [x] Record the **build ID** of the 1.0.3 `main`:
      `5EA394E096752EE3D04DEBFCEA6BF9114277D0B4`, so the data file is
      **`5EA394E096752EE3.json`**. Confirmed at runtime. Exefs is in `~/trails-files/dump/update/`.
- [ ] Dump the romfs. The update NSP alone gives a mostly empty 25 GB tree (an update is only a
      delta), so take files from the running game with `EDEN_DSMOD_DUMP_ROMFS`, or dump the
      base romfs from the XCI and overlay changed files. Not needed until Phase 3/4.

### Phase 2: Design (Claude, since 2026-11-25; you review when you have time)
- [x] Mockups as images at 1240x1080 in `design/` (instead of Figma), based on screenshots from
      the desktop test runs: `design/field.png`, `design/battle.png`, drawn by
      `design/render.py` from the runtime's own primitives (rects, labels, values, bars).
      First drafts; your review is welcome but doesn't block the next phases.
- [ ] Pick a v1 scope. Suggested: **Battle panel** (turn order, enemy HP, party HP/EP/CP)
      plus **Party status** outside battle. Map and quests later.
- [ ] Check what the game's own menus and battle HUD show (screenshots from the Thor) to set
      the design target.
- [ ] Design pages in Figma at the companion canvas size: **1240x1080**, one layout only
      (unless `canvas_alt` is confirmed in Peanuts).
- [x] Map every on-screen value to a data name: `design/DATA.md`, which is also the
      reverse-engineering checklist and records where each value lives.

### Phase 3: Find the data (reverse engineering)
- [ ] Start from public cheats for anchors (HP, mira, party), if any exist for 1.0.3.
- [x] Locate values. The console's heap scanners don't work for this game: its state lives in
      the **alias region** (`0x11...`), outside the heap they search. What works: full memory
      snapshots over the gdbstub (`tools/gdbmem.py snap`, ~3.5 min for 2.6 GB) compared with
      `tools/memdiff.py`. The test profile has the gdbstub on; with it on, the game waits at
      boot until a debugger continues it (`tools/gdbmem.py info` does that).
- [x] **Character table found and verified** (details in `design/DATA.md`):
      `[main+0x879628] + 0x1145A4 + id*0x39C0` = HP, with level, EXP, max HP, EP, CP nearby.
      Confirmed on two boots with two saves, sentinel-tested (CP write showed on the HUD).
- [x] Mira found and sentinel-tested.
- [x] **Battle data (2026-11-25):** Y switches a field fight to a command battle. The battle
      slot array under `[main+0x879470]` gives every enemy's level and live HP (chain checked
      on four boots, companion followed a test write); slot 0 being filled marks a command
      battle; Brave Gauge and the targeted enemy's name found too. Details in `design/DATA.md`.
- [x] **Enemy names (2026-11-26):** every battle unit points at its static record
      (`[unit+0x1b0]`, name pointer at `+0x198`), so no romfs decoding is needed.
- [ ] Still open: party order (needs a save with a different party), turn order (ruled out so
      far: unit-pointer lists, slot-index arrays, a render list; see `design/DATA.md`).
- [x] Plain JSON pointer chains are enough so far; no native module needed.
- [ ] Look into the game's file formats (fonts, text tables, portraits) for later art decoding.

### Phase 4: Build the package
- [x] **v0.1.0 (2026-11-25): Party page.** `tools/gen_package.py` writes `package/` (manifest,
      `5EA394E096752EE3.json`, original artwork from `design/render.py`);
      `tools/build_package.sh` builds `dist/01007A2027548000.dsmod.zip`. No native module,
      `min_runtime` 24. Shows level, HP/EP/CP with bars for every joined character, and mira.
      Tested headless in Eden Duo: loads, values match the game, updates live (HP write showed
      within a second).
- [x] **v0.2.0 (2026-11-25): Battle page.** Enemy rows (level, HP number and bar, packed so
      empty slots leave no gap), target name, Brave Gauge, party strip; Brave Gauge also on the
      Party page; Party/Battle tabs; switches to Battle by itself when a command battle starts
      and back afterwards. Tested headless on the slug fight. Turn order shows "not found yet".
- [x] **v0.3.0 (2026-11-26): Enemy names.** Each enemy row shows the monster's name next to its
      level. The target panel was checked on screen ("Sticky Slug"). Tested headless on two
      boots.
- [x] **v0.4.0 (2026-11-26): The game's own pictures.** Romfs dumped with
      `eden-cli --dump-romfs` (hactool can't read this game's compressed NCAs). Textures are raw
      NVN XTX (`asset/nx/image`), which the runtime decodes from `romfs:` at run time, so
      nothing is shipped. Party page: busts (`avfc<id>`); battle page: AT-bar faces for the
      party (`at_c<id>`) and every enemy's AT icon via `sprite_map` keyed by the record's icon
      key (457 keys, `design/at_icon_keys.txt`). Tested headless. Whether Peanuts' runtime 24
      decodes plain `romfs:` XTX is untested; if it doesn't, the pictures are just missing.
- [ ] Party order (who is in the active party).
- [ ] Decode art/fonts from the game's own files (no shipped game assets), once formats are
      known. Until then: built-in pixel font, placeholder portraits.

### Phase 5: Validate
- [ ] Every value matches the game's own menu (sentinel test: change a value in RAM, check both
      screens follow, then restore it).
- [ ] Test on device in **Peanuts Native** (install via Settings > Screens > Dual-screen
      companions > Install from file), and in Eden Duo on Android.

### Phase 6: Share
- [ ] Open a PR/issue on eden-duo-companions with title ID, game version, Eden Duo version
      and screenshots of both screens.

## Open questions
- Does it boot in Eden Duo on desktop? If not, the reverse-engineering tools are a problem.
- What runtime version does the Thor's Peanuts build carry now?
- How stable is the game in Peanuts at bring-up status?
- Which file formats hold the fonts, text and portraits, and are any documented publicly?
- Read-only companion first, or touch actions (e.g. battle commands by button press) later?
