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
| `mira` | money | 1000 (battle save), 0 (town save) | - |
| `brave` | Brave Gauge points (field HUD gear, 0..5) | 5 | - |
| `area.name` | current area (text id) | Balstar Channel | - |
| `quest.objective` | objective line under the minimap (text id) | Explore the Balstar Channel | - |
| `mode` | field / field battle / command battle / menu / cutscene | field | - |

## Battle (field battle and command battle)

The remake fights first in real time on the field (enemy HP bars over heads, Brave Rush with
ZR), and can switch to turn-based command battles with a turn order. Enemies, `e` = 0..7.

| Name | Meaning | Ref | Status |
|---|---|---|---|
| `enemy.count` | enemies alive | 4 at the start of the Balstar fight | - |
| `e{e}.id` | enemy type (name from the game's text) | - | - |
| `e{e}.hp` / `e{e}.hp_max` | enemy HP | - | - |
| `turn.{i}.unit` | command battle: who acts i-th | - | - |
| `turn.{i}.bonus` | command battle: turn bonus on that slot | - | - |
