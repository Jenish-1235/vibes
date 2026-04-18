#!/bin/bash
set -e

REPO="jenish-1235/vibes"
BINARY="vibes"
INSTALL_DIR="/usr/local/bin"

# ---------- detect platform ----------

OS=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m)

case "$ARCH" in
  x86_64)          ARCH="amd64" ;;
  arm64|aarch64)   ARCH="arm64" ;;
  *) echo "error: unsupported architecture: $ARCH" && exit 1 ;;
esac

case "$OS" in
  darwin|linux) ;;
  *) echo "error: unsupported OS: $OS" && exit 1 ;;
esac

ASSET="${BINARY}-${OS}-${ARCH}"
URL="https://github.com/${REPO}/releases/latest/download/${ASSET}"

# ---------- download ----------

TMP=$(mktemp)
trap 'rm -f "$TMP"' EXIT

echo "Downloading vibes (${OS}/${ARCH})..."
if command -v curl &>/dev/null; then
  curl -fsSL "$URL" -o "$TMP"
elif command -v wget &>/dev/null; then
  wget -qO "$TMP" "$URL"
else
  echo "error: curl or wget is required" && exit 1
fi

chmod +x "$TMP"

# ---------- verify (optional checksum) ----------

if command -v sha256sum &>/dev/null || command -v shasum &>/dev/null; then
  CHECKSUM_URL="https://github.com/${REPO}/releases/latest/download/checksums.txt"
  CHECKSUM_TMP=$(mktemp)
  trap 'rm -f "$TMP" "$CHECKSUM_TMP"' EXIT

  if curl -fsSL "$CHECKSUM_URL" -o "$CHECKSUM_TMP" 2>/dev/null; then
    EXPECTED=$(grep "${ASSET}$" "$CHECKSUM_TMP" | awk '{print $1}')
    if [ -n "$EXPECTED" ]; then
      if command -v sha256sum &>/dev/null; then
        ACTUAL=$(sha256sum "$TMP" | awk '{print $1}')
      else
        ACTUAL=$(shasum -a 256 "$TMP" | awk '{print $1}')
      fi
      if [ "$EXPECTED" != "$ACTUAL" ]; then
        echo "error: checksum mismatch — download may be corrupted"
        exit 1
      fi
      echo "Checksum verified."
    fi
  fi
fi

# ---------- install ----------

if [ -w "$INSTALL_DIR" ]; then
  mv "$TMP" "${INSTALL_DIR}/${BINARY}"
else
  echo "Installing to ${INSTALL_DIR} (sudo required)..."
  sudo mv "$TMP" "${INSTALL_DIR}/${BINARY}"
fi

echo ""
echo "✓ vibes installed to ${INSTALL_DIR}/${BINARY}"
echo ""
echo "  vibes create      — define a new vibe"
echo "  vibes set <name>  — switch to a vibe"
echo "  vibes list        — show all vibes"
echo "  vibes down        — tear down the active vibe"
echo "  vibes --help      — full command reference"
