#!/usr/bin/env bash
# Install (or refresh) the desktop launcher for the current user.
#
# A .desktop file needs an ABSOLUTE Exec path, which depends on where you
# cloned the repo — so the shipped file is a template and this script fills in
# the real paths. Run it once after cloning:
#
#     ./launchers/linux/install-launcher.sh
#
# The app then appears in the applications menu as "Adibot Run Browser" and
# can be pinned to the dock. Re-run it if you move the repo.
# Uninstall with:  rm ~/.local/share/applications/adibot-run-browser.desktop
set -e

here="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
apps="$HOME/.local/share/applications"
dest="$apps/adibot-run-browser.desktop"

chmod +x "$here/RunBrowser.sh"
mkdir -p "$apps"

# A generic stock icon, so the entry looks right without shipping artwork.
icon="utilities-system-monitor"

sed -e "s|@EXEC@|$here/RunBrowser.sh|" \
    -e "s|@ICON@|$icon|" \
    "$here/adibot-run-browser.desktop.in" > "$dest"
chmod 644 "$dest"

# Refresh the menu cache where the tool exists; harmless if it does not.
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$apps" >/dev/null 2>&1 || true
fi

echo "Installed: $dest"
echo "Points at: $here/RunBrowser.sh"
echo "Search your applications for 'Adibot Run Browser'."
