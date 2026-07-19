#!/usr/bin/env bash
# ==============================================================================
# GHUP (GitHub Uploader) Updater
# ==============================================================================

set -e

INSTALL_DIR="$HOME/.ghup"
echo "[+] Updating GHUP..."

if [ -d "$INSTALL_DIR" ]; then
    cp -r . "$INSTALL_DIR/"
    python3 -m pip install -r "$INSTALL_DIR/requirements.txt"
    echo "[+] GHUP updated successfully!"
else
    echo "[-] GHUP installation directory not found at $INSTALL_DIR. Please run install.sh."
    exit 1
fi
