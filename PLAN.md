# FF Resonance companion: plan

A second-screen companion for **Final Fantasy Resonance** (Switch 1 version) running in
[Eden Duo](https://github.com/igawa6/eden-duo), built the same way as the packages in
[eden-duo-companions](https://github.com/igawa6/eden-duo-companions).

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
- [ ] Own the **Switch 1** version (Eden can't run the Switch 2 edition).
- [ ] Dump it from your own Switch: game NSP (base + latest update), `prod.keys`, firmware.
- [ ] A Linux machine for the desktop dev build (native Linux, or WSL2 on Windows; to confirm).
- [ ] A dual-screen Android handheld for final testing (or a phone/tablet, since Eden Duo 1.4.0
      supports single-screen shared mode).
- [ ] Confirm the game boots and is playable in Eden Duo. If it doesn't, stop here.

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
- [ ] Test on device (Android runs NCE, which behaves differently from desktop).

### Phase 6: Share
- [ ] Open a PR/issue on eden-duo-companions with title ID, game version, Eden Duo version
      and screenshots of both screens.

## Open questions
- Exact title ID and current update version.
- Does it boot in Eden Duo today?
- Read-only companion first, or touch actions (e.g. healing) later?
