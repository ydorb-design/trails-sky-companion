#!/bin/bash
# Refuse to go on unless the test profile is really isolated from the real Eden profile:
# every storage path in its config must point inside the test profile, and none at
# ~/.local/share/eden (where the real saves are).
#
# usage: tools/check_test_profile.sh [profile_dir=~/trails-files/test-profile]
set -euo pipefail

PROFILE=${1:-$HOME/trails-files/test-profile}
REAL_DATA=${XDG_DATA_HOME:-$HOME/.local/share}/eden
CFG="$PROFILE/user/config/sdl2-config.ini"

fail() { echo "test profile NOT isolated: $*" >&2; exit 1; }

[ -f "$CFG" ] || fail "no config at $CFG (run tools/reset_test_profile.sh)"
if grep -q "$REAL_DATA" "$CFG"; then
    fail "config still names the real profile: $(grep -n "$REAL_DATA" "$CFG" | tr '\n' ' ')"
fi
for d in nand sdmc load dump; do
    grep -qx "${d}_directory\\\\default=false" "$CFG" || fail "${d}_directory uses Eden's default"
    grep -qx "${d}_directory=$PROFILE/user/$d" "$CFG" || fail "${d}_directory is not $PROFILE/user/$d"
done
# Saves follow nand_directory when save_directory is empty (frontend_common/config.cpp).
save=$(grep -m1 '^save_directory=' "$CFG" | cut -d= -f2-)
if [ -n "$save" ] && [[ "$save" != "$PROFILE/user/"* ]]; then
    fail "save_directory=$save is outside the test profile"
fi
exit 0
