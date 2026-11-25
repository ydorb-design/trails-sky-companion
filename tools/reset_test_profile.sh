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
mkdir -p "$PROFILE/user/config"
cp -a --reflink=auto "$REAL_DATA/keys" "$REAL_DATA/nand" "$PROFILE/user/"
cp "$REAL_CFG" "$PROFILE/user/config/"
# The test profile always has the gdbstub on (tools/gdbmem.py); the real config is untouched.
# Both lines matter: "<key>\default=true" makes Eden ignore the value and use the default.
sed -i 's/^use_gdbstub\\default=true$/use_gdbstub\\default=false/; s/^use_gdbstub=false$/use_gdbstub=true/' \
    "$PROFILE/user/config/sdl2-config.ini"
echo "test profile reset at $PROFILE/user"
