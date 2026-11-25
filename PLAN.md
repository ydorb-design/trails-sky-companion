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
- [ ] Base game dump `~/trails-files/Trails in the Sky 2nd Chapter.xci` (still copying as
      `.xci.part` on 2026-11-25).
- [ ] Build and play it in Peanuts Native on the Thor; start a new game (see Save data).
- [ ] Copy the Thor save to the desktop.
- [ ] Confirm the game also boots in Eden Duo on the desktop (needed for the dev tools).

### Phase 1: Dev environment
- [x] Clone eden-duo and eden-duo-companions (in `~/Projects/eden/`).
- [x] Install the missing build libraries:
      `yay -S --needed boost catch2 enet vulkan-utility-libraries spirv-headers`.
- [ ] Build `eden-cli` (Linux, `EDEN_DSMOD_BUILD_DEV_TOOLS=ON`) from eden-duo. Configure with
      `-DENABLE_QT=OFF -DYUZU_TESTS=OFF -Dzstd_FORCE_BUNDLED=ON -Dlz4_FORCE_BUNDLED=ON
      -DVulkanHeaders_FORCE_BUNDLED=ON`: the companions modules project compiles zstd and lz4
      from eden-duo's `.cache/cpm`, which stays empty when the system copies are used.
- [x] Build the companions' native modules project once to prove the toolchain (dq3 and
      wonder built, in `~/Projects/eden/build-mods`).
- [x] Keys and firmware 22.1.0 installed in `~/.local/share/eden`.
- [ ] Run an existing companion headless (`--aux-virtual`) to learn the screenshot/input loop.
- [ ] Dump romfs/exefs of Trails (`eden-cli --dump-romfs`), record the **build ID** of the
      1.0.3 build (base + update, not the base NSO).

### Phase 2: Design (your strength)
- [ ] Pick a v1 scope. Suggested: **Battle panel** (turn order, enemy HP, party HP/EP/CP)
      plus **Party status** outside battle. Map and quests later.
- [ ] Check what the game's own menus and battle HUD show (screenshots from the Thor) to set
      the design target.
- [ ] Design pages in Figma at the companion canvas size: **1240x1080**, one layout only
      (unless `canvas_alt` is confirmed in Peanuts).
- [ ] Map every on-screen value to a data name (e.g. `p0.hp`, `p0.cp`, `turn.0.unit`). This
      list becomes the reverse-engineering checklist.

### Phase 3: Find the data (reverse engineering)
- [ ] Start from public cheats for anchors (HP, mira, party), if any exist for 1.0.3.
- [ ] Use the live memory console (`findi`, `snap`/`diff`, `ptrto`) to locate values.
- [ ] Turn each value into a stable pointer chain; confirm on a second boot.
- [ ] Decide: plain JSON pointer chains vs a native module (probably needed for battle).
- [ ] Look into the game's file formats (fonts, text tables, portraits) for later art decoding.

### Phase 4: Build the package
- [ ] `package.json`, `manifest.json`, `<BUILD16>.json` (+ module if needed).
- [ ] Decode art/fonts from the game's own files (no shipped assets), once formats are known.
- [ ] Build with `tools/build_dualscreen_package.py`.

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
