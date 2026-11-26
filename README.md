# Trails in the Sky 2nd Chapter: dual-screen companion

A second-screen companion for **Trails in the Sky 2nd Chapter** (Switch, title
`01007A2027548000`, update 1.0.3) in Eden Duo and Peanuts Native (runtime 24 or newer), e.g. on
an AYN Thor.

- **Party page:** each member's portrait, name, level, HP/EP/CP (with an S-Craft badge at
  100+ CP), Mira, the Brave Gauge and your current location.
- **Battle page:** every enemy's icon, name, level, HP and weak elements, the targeted enemy, the Brave Gauge,
  and the party's HP/EP/CP. It switches to this page by itself when a command battle starts.

No game files are included. Portraits and icons are read from your own copy of the game while
it runs.

## Install

1. Download `01007A2027548000.dsmod.zip` from the
   [latest release](../../releases/latest).
2. In Peanuts or Eden Duo: Settings > Screens > Dual-screen companions > Install from file,
   then pick the zip.

## Not done yet

Turn order, and which party members are active vs. in reserve. See `PLAN.md` and
`design/DATA.md` for the reverse-engineering notes.

## Building

`tools/build_package.sh` regenerates `package/` and writes `dist/01007A2027548000.dsmod.zip`
(needs Python 3 with Pillow).
