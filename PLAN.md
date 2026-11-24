# FF Resonance companion: plan

A second-screen companion for **Final Fantasy Resonance** (Switch 1 version, title ID
`0100606026F12000`) that runs in both:

- [Peanuts Native](https://github.com/igawa6/peanuts-native): rewrites the game to run natively on
  Android. Lists FF Resonance as supported (update 1.0.1) with no companion yet.
- [Eden Duo](https://github.com/igawa6/eden-duo): the emulator. Same package format, and it's where
  the dev and reverse-engineering tools live.

Built the same way as the packages in
[eden-duo-companions](https://github.com/igawa6/eden-duo-companions).

## Peanuts Native compatibility rules

Peanuts Native embeds the Eden Duo companion runtime, so one package can serve both. From its
dev notes (PEANUTS.md, Nov 2026), it differs in ways that constrain our design:

- **Runtime 24 max.** It carries Eden Duo 1.3.5.1's runtime (24). Keep `min_runtime` at 24 or
  below, so no runtime-25 features (`@screen.*`, `canvas_alt`, `L3`/`R3` buttons) unless it
  updates. Re-check before release.
- **Native modules work** (`modules/android-arm64-v8a/<title>.so`).
- **No guest calls** (calling the game's own functions). Treat it like Android NCE: use memory
  reads, guarded writes or button presses only.
- **Load plans / guest helper code: unconfirmed.** DQ3 and Octopath 0 rely on them. Avoid
  depending on one until we've verified it works in Peanuts.
- **Build ID.** Target the 1.0.1 update build, the one Peanuts supports. Peanuts passes the full
  build ID to modules (`PN_BUILD_ID`).
- **Unreal Engine confirmed.** Peanuts decodes FF Resonance's Unreal assets, which matches the
  HD-2D templates.
- **Final testing happens on the handheld in Peanuts**, not just in Eden Duo. Peanuts needs
  Android 13+, a Snapdragon GPU with Vulkan 1.3, and 12 GB RAM (developed on the AYN Thor).

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

- FF Resonance is HD-2D, like **Dragon Quest III HD-2D** and **Octopath Traveler 0**, which
  already have companions. Their modules (`dq3_*`, `ot0_*`, `01005270232F2000.cpp`) are the
  closest templates for party, battle, map and font decoding.
- Turn-based with weakness/stagger: a battle panel (enemy HP, weaknesses, stagger, party
  status) is a natural fit for a second screen.
- Assumption to confirm: it is Unreal Engine like the other HD-2D titles.

## Phases

### Phase 0: Prerequisites (you)
- [x] Own the **Switch 1** version and dump it (NSP + update, `prod.keys`, firmware).
- [x] Dual-screen handheld: **AYN Thor** (Peanuts Native's own test device).
- [x] Build and play FF Resonance in Peanuts Native on the Thor.
- [ ] Dev machine: **native Linux** (the Eden Duo docs and tools are written for it).
- [ ] Claude Code installed on the Linux machine, this repo cloned there.
- [ ] Copy the NSP, update, `prod.keys` and firmware to `~/ffres-files/` (outside the repo,
      never committed).
- [ ] Confirm the game also boots in Eden Duo on the desktop (needed for the dev tools).

### Phase 1: Dev environment
- [ ] Build `eden-cli` (Linux, dev tools on) from eden-duo.
- [ ] Clone eden-duo-companions; build the native modules project once to prove the toolchain.
- [ ] Run an existing companion headless (`--aux-virtual`) to learn the screenshot/input loop.
- [ ] Dump romfs/exefs of FF Resonance, record the **title ID** and **build ID**.

### Phase 2: Design (your strength)
- [ ] Pick a v1 scope. Suggested: **Party status** + **Battle panel**. Map and items later.
- [ ] Design pages in Figma at the companion canvas size (1240x1080, plus a narrow
      `canvas_alt` layout if we want phone/foldable support).
- [ ] Map every on-screen value to a data name (e.g. `p0.hp`, `e1.weak.fire`). This list
      becomes the reverse-engineering checklist.

### Phase 3: Find the data (reverse engineering)
- [ ] Start from public cheats for anchors (HP, gil, party).
- [ ] Use the live memory console (`findi`, `snap`/`diff`, `ptrto`) to locate values.
- [ ] Turn each value into a stable pointer chain; confirm on a second boot.
- [ ] Decide: plain JSON pointer chains vs a native module (likely needed for battle and
      Unreal objects, as DQ3/OT0 did).

### Phase 4: Build the package
- [ ] `package.json`, `manifest.json`, `<BUILD16>.json` (+ module if needed).
- [ ] Decode art/fonts from the game's own files (no shipped assets).
- [ ] Build with `tools/build_dualscreen_package.py`.

### Phase 5: Validate
- [ ] Every value matches the game's own menu (sentinel test: change a value in RAM, both
      screens follow, then restore).
- [ ] Test on device in **Peanuts Native** (install via Settings > Screens > Dual-screen
      companions > Install from file), and in Eden Duo on Android.

### Phase 6: Share
- [ ] Open a PR/issue on eden-duo-companions with title ID, game version, Eden Duo version
      and screenshots of both screens.

## Open questions
- Does it boot in Eden Duo on desktop? If not, the reverse-engineering tools are a problem.
- Do load plans work in Peanuts Native?
- Read-only companion first, or touch actions (e.g. healing) later?
