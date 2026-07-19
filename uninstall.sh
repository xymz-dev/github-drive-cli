#!/usr/bin/env bash
# ==============================================================================
# GHUP (GitHub Uploader) Uninstaller
# ==============================================================================

echo "[+] Uninstalling GHUP..."

BIN_PATH="/data/data/com.termux/files/usr/bin/ghup"
if [ ! -f "$BIN_PATH" ]; then
    BIN_PATH="/usr/local/bin/ghup"
fi

if [ -f "$BIN_PATH" ]; then
    rm -f "$BIN_PATH"
    echo "[+] Removed binary wrapper."
fi

INSTALL_DIR="$HOME/.ghup"
if [ -d "$INSTALL_DIR" ]; then
    rm -rf "$INSTALL_DIR"
    echo "[+] Removed installation directory $INSTALL_DIR."
fi

echo "[+] GHUP successfully uninstalled."
