#!/usr/bin/env bash
# ==============================================================================
# GHUP (GitHub Uploader) Installer for Termux & Linux
# ==============================================================================

set -e

echo "[+] Starting GHUP Installation..."

# Detect Environment
if [ -d "/data/data/com.termux" ]; then
    echo "[+] Termux environment detected."
    pkg update -y || true
    # Try installing precompiled Termux packages first for speed and zero compilation errors
    pkg install -y python python-pip git libffi openssl python-requests python-rich python-typer || pkg install -y python python-pip git
else
    echo "[+] Linux/Standard environment detected."
fi

# Check Python 3
if ! command -v python3 &> /dev/null; then
    echo "[-] Python 3 is required but not installed. Please install Python 3."
    exit 1
fi

# Determine installation directory
INSTALL_DIR="$HOME/.ghup"
echo "[+] Installing GHUP files to $INSTALL_DIR..."
mkdir -p "$INSTALL_DIR"
cp -r . "$INSTALL_DIR/"

# Install Python dependencies (with --prefer-binary)
echo "[+] Installing/Verifying Python dependencies..."
if [ -d "/data/data/com.termux" ]; then
    pip install --prefer-binary -r "$INSTALL_DIR/requirements.txt" || true
else
    python3 -m pip install --upgrade pip || true
    python3 -m pip install --prefer-binary -r "$INSTALL_DIR/requirements.txt"
fi

# Create executable wrapper
BIN_PATH="/data/data/com.termux/files/usr/bin/ghup"
if [ ! -d "/data/data/com.termux/files/usr/bin" ]; then
    BIN_PATH="/usr/local/bin/ghup"
fi

echo "[+] Creating executable wrapper at $BIN_PATH..."
cat << 'EOF' > "$INSTALL_DIR/ghup_wrapper.sh"
#!/usr/bin/env bash
python3 "$HOME/.ghup/main.py" "$@"
EOF

chmod +x "$INSTALL_DIR/ghup_wrapper.sh"

if [ -w "$(dirname "$BIN_PATH")" ]; then
    ln -sf "$INSTALL_DIR/ghup_wrapper.sh" "$BIN_PATH"
else
    sudo ln -sf "$INSTALL_DIR/ghup_wrapper.sh" "$BIN_PATH"
fi

echo ""
echo "========================================================================"
echo " [SUCCESS] GHUP (GitHub Uploader) has been installed successfully!"
echo "========================================================================"
echo " Get started by running:"
echo "   ghup login"
echo "   ghup --help"
echo "========================================================================"
