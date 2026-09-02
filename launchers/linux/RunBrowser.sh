#!/usr/bin/env bash
# Launch the Run Browser window.
#
# Works from anywhere and through a symlink: it resolves its own real path,
# steps up to the project folder (two levels), and runs the module from there
# — which is what `python3 -m run_browser` needs in order to find the code.
#
# If the project has a .venv, it is used automatically.
set -e

here="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
root="$(cd "$here/../.." && pwd)"
cd "$root"

if [ -x "$root/.venv/bin/python3" ]; then
    exec "$root/.venv/bin/python3" -m run_browser "$@"
fi

exec python3 -m run_browser "$@"
