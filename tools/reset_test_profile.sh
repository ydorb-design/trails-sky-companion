#!/bin/bash
# (Re)create the isolated Eden profile used by headless_run.sh from the real one:
# keys, nand (firmware, installed update, saves) and the SDL config.
# Only the test profile is replaced; the real ~/.local/share/eden is only read.
#
# usage: tools/reset_test_profile.sh [profile_dir=~/trails-files/test-profile]
set -euo pipefail

PROFILE=${1:-$HOME/trails-files/test-profile}
REAL_DATA=${XDG_DATA_HOME:-$HOME/.local/share}/eden
REAL_CFG=${XDG_CONFIG_HOME:-$HOME/.config}/eden/sdl2-config.ini

if pgrep -x eden-cli >/dev/null; then
    echo "eden-cli is running; close it first" >&2
    exit 1
fi

rm -rf "$PROFILE/user"
mkdir -p "$PROFILE/user/config" "$PROFILE/user/load" "$PROFILE/user/sdmc" "$PROFILE/user/dump"
cp -a --reflink=auto "$REAL_DATA/keys" "$REAL_DATA/nand" "$PROFILE/user/"
CFG="$PROFILE/user/config/sdl2-config.ini"
cp "$REAL_CFG" "$CFG"
# The test profile always has the gdbstub on (tools/gdbmem.py); the real config is untouched.
# Both lines matter: "<key>\default=true" makes Eden ignore the value and use the default.
sed -i 's/^use_gdbstub\\default=true$/use_gdbstub\\default=false/; s/^use_gdbstub=false$/use_gdbstub=true/' \
    "$CFG"
# Test runs are silent: mute the emulator's audio (the real config is untouched).
sed -i -e 's/^volume\\default=true$/volume\\default=false/' -e 's/^volume=.*/volume=0/' \
    -e 's/^audio_muted\\default=true$/audio_muted\\default=false/' \
    -e 's/^audio_muted=.*/audio_muted=true/' "$CFG"
# Storage paths in the copied config are absolute and point at the REAL profile (saves live in
# nand). A portable ./user folder does not override them, so rewrite every one.
for d in nand sdmc load dump tas; do
    sed -i -e "s|^${d}_directory\\\\default=.*|${d}_directory\\\\default=false|" \
           -e "s|^${d}_directory=.*|${d}_directory=$PROFILE/user/$d|" "$CFG"
done
"$(dirname "$0")/check_test_profile.sh" "$PROFILE"
echo "test profile reset at $PROFILE/user"
