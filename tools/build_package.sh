#!/bin/bash
# Generate the package source (tools/gen_package.py) and build the installable zip into dist/.
# usage: tools/build_package.sh [version=0.1.0]
set -euo pipefail
cd "$(dirname "$0")/.."
VERSION=${1:-0.1.0}
COMPANIONS=${COMPANIONS:-$HOME/Projects/eden/eden-duo-companions}
python3 -I tools/gen_package.py >/dev/null
rm -rf dist
python3 -I "$COMPANIONS/tools/build_dualscreen_package.py" --package package --output dist \
    --version "$VERSION"
