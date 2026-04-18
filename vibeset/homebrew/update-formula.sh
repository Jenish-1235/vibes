#!/bin/bash
# Update vibes.rb with real SHA256 checksums for a given release version.
# Usage: ./update-formula.sh 0.2.0
set -e

VERSION="${1:?usage: ./update-formula.sh <version>}"
REPO="jenish-1235/vibes"
FORMULA="$(dirname "$0")/vibes.rb"

fetch_sha256() {
  local asset="$1"
  local url="https://github.com/${REPO}/releases/download/vibeset-v${VERSION}/${asset}"
  echo "Fetching ${asset}..." >&2
  curl -fsSL "$url" | sha256sum | awk '{print $1}'
}

ARM64=$(fetch_sha256 "vibes-darwin-arm64")
AMD64=$(fetch_sha256 "vibes-darwin-amd64")
LINUX=$(fetch_sha256 "vibes-linux-amd64")

sed -i.bak \
  -e "s/version \".*\"/version \"${VERSION}\"/" \
  -e "s/PLACEHOLDER_ARM64_SHA256/${ARM64}/" \
  -e "s/PLACEHOLDER_AMD64_SHA256/${AMD64}/" \
  -e "s/PLACEHOLDER_LINUX_SHA256/${LINUX}/" \
  "$FORMULA"

rm -f "${FORMULA}.bak"
echo "Updated ${FORMULA} for v${VERSION}"
