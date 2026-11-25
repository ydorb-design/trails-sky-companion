# Data names (the reverse-engineering checklist)

Every value a page shows, with the reference value it had when the save was made. "Ref" values
come from the game's own menus/HUD in the test saves (2026-11-25), and they're what each search
is checked against. Status: `-` not found yet, `found` located for one boot, `chain` stable
pointer chain confirmed on a second boot, `checked` passed the sentinel test
(PORTING_A_GAME.md §3).

## Where the data lives (build 5EA394E096752EE3, update 1.0.3)

- **Character table:** `[main+0x879628] + 0x1145A4 + id * 0x39C0` is that character's **HP**
  (u32). The record around it:

  | Offset from HP | Type | Meaning |
  |---|---|---|
  | -0x08 | u32 | level |
  | -0x04 | u32 | EXP (probably; 70820 / 70121 at Lv.25) |
  | +0x00 | u32 | HP |
  | +0x04 | u32 | max HP |
  | +0x08 / +0x0C | u32 | EP / max EP |
  | +0x10 / +0x14 | u32 | CP / max CP |
  | +0x18 ... | u32 | stats (368, 333, 292, ... for Estelle; order not mapped yet) |

  Estelle is id 0 and Anelace id 1 in both test saves. A character who hasn't joined yet reads
  as all zeros. The table is indexed by **character**, not party slot: party order still has
  to be found (`party.*` below).
- `main+0x879628` points to a big game-state object in the **alias region** (`0x11...`), not
  the heap. That's why the console's `findi`/`cscan` (heap only, and capped) never found it.
  Found by diffing two full memory snapshots (`tools/gdbmem.py snap` + `tools/memdiff.py`).
- `object` below means `[main+0x879628]`, the game-state object.
- **Mira** (2026-11-25): `object+0x20B648`, u32. Found by comparing the object across the
  battle save (1000) and the town save (0) on different boots (`tools/objdiff.py`), then
  sentinel-tested: wrote 4321, the camp menu showed MIRA 4321, wrote 0 back.
- **Party order: not found yet (2026-11-25).** Swapping Estelle and Anelace with Change
  Formation (D-pad Down in the camp menu, then A, D-pad Right, A, B) changed no neighbouring
  pair in the object (0..0xC60000) and no field between their two records. Full-snapshot
  diffs (`tools/swapfind.py`, snapshots F1 = Anelace first, F2 = Estelle first) only found a
  thread-stack local (`[1,0]`->`[0,1]` in a `Stack` mapping, not durable) and render/UI
  buffers. Next try: a save with more members than party slots, where "in party" vs "joined"
  differ.
- **v1 workaround:** show every character whose record has level > 0 (joined), in table order.
  Right at this point of the story (Estelle, Anelace); wrong once reserves exist.
- A second, stale copy of the same records sits about 6.5 MB later (doesn't follow damage);
  probably the loaded save. Don't use it.
- Checks done (2026-11-25):
  - boot 1 (main at 0x80A23000), battle save: HP 1607 -> 1543 after a hit, both seen in
    the game menu, both read through the chain.
  - boot 2 (main at 0x800E8000, different ASLR), town save: Estelle Lv.25 2035/2035 HP,
    85/85 EP, 0/200 CP, matching the HUD; Anelace's slot all zeros (not joined yet).
  - sentinel on boot 2: wrote CP 0 -> 50 through the chain, the game's HUD showed 50, wrote it
    back to 0. Nothing saved.

## Party (field page and battle page)

Slots are party order (leader first), `n` = 0..3.

| Name | Meaning | Ref (battle save) | Status |
|---|---|---|---|
| `party.count` | members in the party | 2 | - |
| `party.{n}.id` | character id in slot n (indexes the character table) | 0, 1 | - |
| `c{id}.lv` | level | 25, 25 | chain |
| `c{id}.hp` / `c{id}.hp_max` | HP | 1607/2035, 1544/2090 | checked (via CP write, same record) |
| `c{id}.ep` / `c{id}.ep_max` | EP | 85/85, 80/80 | chain |
| `c{id}.cp` / `c{id}.cp_max` | CP | 200/200, 200/200 | checked |
| `c{id}.status` | status-effect bits (poison, sleep, ...) | none | - |

Note: max HP isn't 1607/1544 as first assumed from "full-looking" bars; the menu shows only
current HP. The bars had a dark tail.

## General

| Name | Meaning | Ref | Status |
|---|---|---|---|
| `mira` | money: u32 at `object+0x20B648` | 1000 (battle save), 0 (town save) | checked |
| `playtime` | f64 seconds at `object+0x20B650` (counts up while playing) | ~729 s | found |
| `brave` | Brave Gauge points (field HUD gear, 0..5): see Battle | 5 | chain |
| `area.name` | current area (text id) | Balstar Channel | - |
| `quest.objective` | objective line under the minimap (text id) | Explore the Balstar Channel | - |
| `mode` | field / field battle / command battle / menu / cutscene | field | - |

## Battle (field battle and command battle)

The remake fights first in real time on the field (enemy HP bars over heads, Brave Rush with
ZR). **Y** switches a field fight to a turn-based command battle (from the game's own
"Preemptive Brave Attack" tutorial; scripted fights may start in command mode directly).

### Battle slot array (found 2026-11-25; chain checked on four boots: main at 0x80552000, 0x801cc000, 0x80a94000, 0x801f0000)

`R = [main+0x879470]`. From `R+0xba0` there is an array of 0x30-byte **battle slots**:

| Slot field | Meaning |
|---|---|
| `+0x00` | model/field actor (0 when the slot is empty) |
| `+0x10` | pointer `S`; `[S+0]` = the **battle unit** `U` (0 when empty) |

Party members fill the first slots (leader first), enemies follow. Party units and enemy units
are different classes:

- **enemy unit:** `[U+0x1d00]` = its live stats record `st`. `st+0x0` u32 unit id (same as the
  spawn table's), `st+0x4` level, `st+0x8` EXP reward, **`st+0xc` HP**, `st+0x10` max HP,
  then EP/max, CP/max, stats: the same layout as the character table from level onwards.
  `st+0x74` f32 = damage taken this battle. For party units `[U+0x1d00]` is 0, so a
  "+0x1d00" chain simply fails on party slots.
- **party unit:** `[U+0x3440]` = that character's record in the character table (level field
  minus 4, i.e. HP-0xc).

**In a command battle or not:** slot 0's unit `[[R+0xbb0]+0]` is non-zero only during a
command battle (empty in the field, during a real-time field fight, and after the battle).
`R+0xb90` is NOT a battle flag (1 in the frog fight, 0 in the slug fight). Dead enemies drop
out of their slot (it reads empty); reinforcements can land in later slots, leaving gaps
(frog fight: slots 2, 3, then 5, 6 with 4 empty), so the page scans slots 0-11 and packs.

Data-file chain for enemy HP in slot i: `["main+0x879470", {offset 0xbb0, stride 0x30,
index $i}, "0x0", "0x1d00", "0x0"]`, offset `0xc`. Checked live against the game's target
panel in two different fights: slugs (Sticky Slug 272/1676) and frogs (Ripple Frog
2608/3007, the other frog 904/3007).

### Other battle findings

- **Targeted enemy's name:** the target panel's text sits inline at
  `[[main+0x8791a8]+0x238]+0x720` ("Sticky Slug", "Ripple Frog"). The runtime's `cstring` type
  needs an address that holds a *pointer* to the text, so the package uses the UI's own pointer
  to that buffer: `[[[main+0x8791a0]+0x1f08]+0x92d0]+0xfd68` -> text (found on boot 1, checked
  on boot 4). Before anything is targeted the buffer holds stale text (the game's title).
- **Brave Gauge** (field HUD gear, 0..5): u32 at `[[main+0x879470]+0x6540]+0x4c`. Followed
  5 -> 3 -> 1 -> 2 -> 0 through two Brave Rushes (ZR, -2 each) and attacks (refill); shows 5 on
  a second boot. It may be the HUD gear's own number rather than the battle state, but it is
  what the player sees. The partial fill between points is not mapped.
- **Spawn table** at `object+0x260024` (stride 0x2F0, HP-relative like the character table):
  every monster spawned on the map. `HP-0x3c` (s32) is non-zero for monsters in the current
  battle (9 in the scripted slug fight, 1 in the frog fight). `HP-0x38` u32 = species key
  (0xb6f62854 Sticky Slug, 0x0e4a4f31 Ripple Frog; not a crc32/fnv/djb2/murmur3 of any string
  tried), `HP-0x30` = unit id, `HP-0x5c` = model name ("mon5201"). Its HP is the value at
  battle start, not live. Dead monsters are removed (the table compacts).
- **Monster groups:** `[[main+0x879470]+0xb40]+0x60` is a list of 0x20-byte groups
  {descriptor, actor vector, count, capacity}. The scripted slug fight's group count went 4 ->
  3 -> 1 -> 0 as slugs died, but groups mix actor types, so the battle slot array is the
  better source.
- Enemy names for every slot need the monster table (species key -> name). The game's parsed
  monster table is in memory ("mon5201 ... Mini Slug / Sticky Slug / Sticky Slug+"), but no
  pointer from a unit leads to it. Options: decode the table from the romfs, or show only the
  target's name.

| Name | Meaning | Ref | Status |
|---|---|---|---|
| `enemy.count` | enemies alive | 4 at the start of the Balstar fight | found (group count) |
| `e{e}.id` | enemy type (species key) | 0xb6f62854 | found (spawn table) |
| `e{e}.hp` / `e{e}.hp_max` | enemy HP | 272/1676 | checked (4 boots; companion followed a write of 999) |
| `target.name` | targeted enemy's name | Ripple Frog | chain (2 boots) |
| `brave` | Brave Gauge points | 5 | chain (2 boots) |
| `in_battle` | command battle running | - | chain (slot 0 unit) |
| `turn.{i}.unit` | command battle: who acts i-th. Not found: no per-unit delay field changed in the enemy units across a turn, and the arrays holding several unit pointers (e.g. one at 0x119fcb9a40 = FrogA, Estelle, Anelace, FrogB) did not follow the on-screen order | - | - |
| `turn.{i}.bonus` | command battle: turn bonus on that slot | - | - |

### Test-harness notes (2026-11-25)

- After a failed read the gdbstub can leave the game halted even though the script sent `c`:
  every screenshot shows the same frame. `tools/gdbmem.py info` continues it.
- The game autosaves (save015) after battles, in the test profile. Reset the test profile's
  saves from `~/trails-files/saves/2026-11-25-battle-and-town/savedata` before a run that needs
  the pre-fight state; the Load list's 2nd entry is then the pre-slug battle save again.
- Field positions: the leader's recent positions are a ring of xyz floats at
  `object+0x20b6a0` (newest = last changed entry); scratch navigation tools used it.
