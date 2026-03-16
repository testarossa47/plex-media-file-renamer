#!/bin/bash
set -euo pipefail

# ── Configuration ──────────────────────────────────────────────
PKG_NAME="plex-file-renamer"
PKG_VERSION="2.0.3"
PKG_ARCH="all"
MAINTAINER="testarossa47 <testarossa47@users.noreply.github.com>"
DESCRIPTION="GUI tool for renaming video files for Plex Media Server"
LONG_DESC=" A GTK3 Python application styled to match Linux Mint's Nemo file
 manager. Batch-renames video files into Plex-compatible
 'Series - S01E01.ext' format with live preview and undo support."

# ── Paths ──────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="$(mktemp -d)"
PKG_DIR="${BUILD_DIR}/${PKG_NAME}_${PKG_VERSION}_${PKG_ARCH}"
OUTPUT_DIR="${PROJECT_DIR}/dist"

echo "Building ${PKG_NAME} ${PKG_VERSION}..."
echo "Staging directory: ${PKG_DIR}"

# ── Create directory structure ─────────────────────────────────
mkdir -p "${PKG_DIR}/DEBIAN"
mkdir -p "${PKG_DIR}/usr/bin"
mkdir -p "${PKG_DIR}/usr/share/applications"
mkdir -p "${PKG_DIR}/usr/share/doc/${PKG_NAME}"
mkdir -p "${PKG_DIR}/usr/share/icons/hicolor/scalable/apps"
for sz in 16 22 24 32 48 64 128 256 512; do
    mkdir -p "${PKG_DIR}/usr/share/icons/hicolor/${sz}x${sz}/apps"
done

# ── Install the application script ─────────────────────────────
cp "${PROJECT_DIR}/file_renamer.py" "${PKG_DIR}/usr/bin/${PKG_NAME}"
chmod 755 "${PKG_DIR}/usr/bin/${PKG_NAME}"

# ── Install the desktop file ──────────────────────────────────
cp "${PROJECT_DIR}/plex-file-renamer.desktop" "${PKG_DIR}/usr/share/applications/${PKG_NAME}.desktop"
chmod 644 "${PKG_DIR}/usr/share/applications/${PKG_NAME}.desktop"

# ── Install icons ─────────────────────────────────────────────
# SVG (scalable)
cp "${PROJECT_DIR}/icons/${PKG_NAME}.svg" \
   "${PKG_DIR}/usr/share/icons/hicolor/scalable/apps/${PKG_NAME}.svg"
chmod 644 "${PKG_DIR}/usr/share/icons/hicolor/scalable/apps/${PKG_NAME}.svg"

# PNGs at each size
for sz in 16 22 24 32 48 64 128 256 512; do
    cp "${PROJECT_DIR}/icons/${PKG_NAME}-${sz}.png" \
       "${PKG_DIR}/usr/share/icons/hicolor/${sz}x${sz}/apps/${PKG_NAME}.png"
    chmod 644 "${PKG_DIR}/usr/share/icons/hicolor/${sz}x${sz}/apps/${PKG_NAME}.png"
done

# ── Install documentation ─────────────────────────────────────
cp "${PROJECT_DIR}/README.md" "${PKG_DIR}/usr/share/doc/${PKG_NAME}/"
cp "${SCRIPT_DIR}/copyright" "${PKG_DIR}/usr/share/doc/${PKG_NAME}/"
chmod 644 "${PKG_DIR}/usr/share/doc/${PKG_NAME}/"*

# ── Calculate installed size (in KB) ──────────────────────────
INSTALLED_SIZE=$(du -sk "${PKG_DIR}" | cut -f1)

# ── Write DEBIAN/postinst (refresh icon + desktop caches) ─────
cat > "${PKG_DIR}/DEBIAN/postinst" << 'POSTINST'
#!/bin/sh
set -e
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -f -t /usr/share/icons/hicolor 2>/dev/null || true
fi
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database /usr/share/applications 2>/dev/null || true
fi
POSTINST
chmod 755 "${PKG_DIR}/DEBIAN/postinst"

# ── Write DEBIAN/control ──────────────────────────────────────
cat > "${PKG_DIR}/DEBIAN/control" << EOF
Package: ${PKG_NAME}
Version: ${PKG_VERSION}
Section: utils
Priority: optional
Architecture: ${PKG_ARCH}
Depends: python3 (>= 3.6), python3-gi, gir1.2-gtk-3.0
Installed-Size: ${INSTALLED_SIZE}
Maintainer: ${MAINTAINER}
Homepage: https://github.com/testarossa47/plex-media-file-renamer
Description: ${DESCRIPTION}
${LONG_DESC}
EOF

# ── Build the .deb ────────────────────────────────────────────
mkdir -p "${OUTPUT_DIR}"
dpkg-deb --build --root-owner-group "${PKG_DIR}" "${OUTPUT_DIR}/${PKG_NAME}_${PKG_VERSION}_${PKG_ARCH}.deb"

echo ""
echo "Package built successfully:"
echo "  ${OUTPUT_DIR}/${PKG_NAME}_${PKG_VERSION}_${PKG_ARCH}.deb"
echo ""
echo "Install with:"
echo "  sudo dpkg -i ${OUTPUT_DIR}/${PKG_NAME}_${PKG_VERSION}_${PKG_ARCH}.deb"
echo ""
echo "Remove with:"
echo "  sudo apt remove ${PKG_NAME}"

# ── Cleanup ───────────────────────────────────────────────────
rm -rf "${BUILD_DIR}"
