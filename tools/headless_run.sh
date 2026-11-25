#!/bin/bash
# Boot Trails in Eden Duo with a virtual second screen, take screenshots of both screens
# every INTERVAL seconds, then stop the emulator.
#
# usage: tools/headless_run.sh <rundir> [seconds=180] [interval=30]
#
# While it runs, send input by writing <rundir>/p.btn atomically, one step per line, e.g.
#   printf 'DDown 100\nwait 400\nA 100\n' > <rundir>/p.btn.tmp && mv <rundir>/p.btn.tmp <rundir>/p.btn
# Live memory console commands go in <rundir>/cmd.in (EDEN_DSMOD_CMD).
#
# Env overrides: EDEN_CLI (eden-cli path), GAME (game image path).
set -euo pipefail

RUN=${1:?usage: headless_run.sh <rundir> [seconds] [interval]}
SECS=${2:-180}
STEP=${3:-30}
EDEN_CLI=${EDEN_CLI:-$HOME/Projects/eden/eden-duo/build/bin/eden-cli}
GAME=${GAME:-$HOME/trails-files/Trails in the Sky 2nd Chapter.xci}

mkdir -p "$RUN"
RUN=$(cd "$RUN" && pwd)

env EDEN_VSYNC=0 EDEN_DSMOD_CMD="$RUN/cmd.in" EDEN_DSMOD_GPU_READBACK=1 \
    "$EDEN_CLI" --aux-virtual --screenshot-prefix "$RUN/p" --filter "*:Info" "$GAME" \
    > "$RUN/stdout.log" 2>&1 &
PID=$!
trap 'kill "$PID" 2>/dev/null || true; wait "$PID" 2>/dev/null || true' EXIT

for ((t = STEP; t <= SECS; t += STEP)); do
    sleep "$STEP"
    if ! kill -0 "$PID" 2>/dev/null; then
        echo "eden-cli exited early (before ${t}s); see $RUN/stdout.log"
        exit 1
    fi
    touch "$RUN/p.shot"
    sleep 2
    for n in 1 2; do
        src="$RUN/p-screen$n.png"
        [ -f "$src" ] && mv "$src" "$(printf '%s/screen%d-%04ds.png' "$RUN" "$n" "$t")"
    done
done
echo "done: screenshots and stdout.log in $RUN"
