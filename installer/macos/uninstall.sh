#!/bin/sh
# Removes Sweepito, as installed by the macOS .pkg. Run with administrator rights:
#   sudo /usr/local/lib/sweepito/uninstall.sh
# Only what the package installed is removed; your settings and project files are never touched.
set -eu

if [ "$(id -u)" -ne 0 ]; then
    echo "uninstall.sh must run as root (use sudo)." >&2
    exit 1
fi

rm -f /usr/local/bin/sweepito
rm -rf /usr/local/lib/sweepito
# Forget the installer receipt, so a later install is not treated as an upgrade of a missing copy.
pkgutil --pkgs 2>/dev/null | grep -x 'io.github.coldsofttech.sweepito' |
    while read -r id; do pkgutil --forget "$id" >/dev/null; done || true
echo "Sweepito was removed."
