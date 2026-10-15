#!/usr/bin/env bash
# ==============================================================================
# PreviewGen - macOS & Linux 1-Click Installer
# Run in Terminal:
# curl -fsSL https://raw.githubusercontent.com/Mustaqeem66/Freepik-Prewview-Generator/main/install.sh | bash
# ==============================================================================

set -e

REPO="Mustaqeem66/Freepik-Prewview-Generator"
APP_NAME="PreviewGen"
OS="$(uname -s)"

echo ""
echo -e "\033[1;36m==========================================================\033[0m"
echo -e "\033[1;33m       PreviewGen - One-Click Installer ($OS)            \033[0m"
echo -e "\033[1;36m==========================================================\033[0m"
echo ""

case "$OS" in
  Darwin*)
    # ── macOS ──
    echo -e "\033[1;34m[1/4] Downloading latest macOS release...\033[0m"
    DMG_URL="https://github.com/$REPO/releases/latest/download/PreviewGen-macOS.dmg"
    TEMP_DIR="$(mktemp -d)"
    TEMP_DMG="$TEMP_DIR/PreviewGen.dmg"

    curl -fL "$DMG_URL" -o "$TEMP_DMG" --progress-bar

    echo -e "\033[1;34m[2/4] Mounting and installing to /Applications...\033[0m"
    MOUNT_DIR="$(mktemp -d)"
    hdiutil attach "$TEMP_DMG" -mountpoint "$MOUNT_DIR" -nobrowse -quiet

    # Target directory
    if [ -d "$MOUNT_DIR/$APP_NAME.app" ]; then
      SRC_APP="$MOUNT_DIR/$APP_NAME.app"
    elif [ -d "$MOUNT_DIR/dist/$APP_NAME.app" ]; then
      SRC_APP="$MOUNT_DIR/dist/$APP_NAME.app"
    else
      SRC_APP="$(find "$MOUNT_DIR" -maxdepth 2 -name "*.app" | head -n 1)"
    fi

    if [ -n "$SRC_APP" ] && [ -d "$SRC_APP" ]; then
      rm -rf "/Applications/$APP_NAME.app"
      cp -R "$SRC_APP" "/Applications/"
    else
      echo -e "\033[1;31mError: Could not locate $APP_NAME.app inside the DMG.\033[0m"
      hdiutil detach "$MOUNT_DIR" -quiet || true
      rm -rf "$TEMP_DIR" "$MOUNT_DIR"
      exit 1
    fi

    hdiutil detach "$MOUNT_DIR" -quiet || true
    rm -rf "$TEMP_DIR" "$MOUNT_DIR"

    echo -e "\033[1;34m[3/4] Removing Gatekeeper quarantine (bypassing certificate blocks)...\033[0m"
    # This command removes the Apple Quarantine flag, allowing the app to run without notarization/certificate!
    xattr -cr "/Applications/$APP_NAME.app" 2>/dev/null || true

    # Create Desktop shortcut / alias
    ln -sf "/Applications/$APP_NAME.app" "$HOME/Desktop/$APP_NAME" 2>/dev/null || true

    echo -e "\033[1;34m[4/4] Launching $APP_NAME...\033[0m"
    open "/Applications/$APP_NAME.app"

    echo ""
    echo -e "\033[1;32m==========================================================\033[0m"
    echo -e "\033[1;32m   PreviewGen installed successfully into /Applications!  \033[0m"
    echo -e "\033[1;37m   Desktop shortcut created: ~/Desktop/$APP_NAME          \033[0m"
    echo -e "\033[1;37m   Gatekeeper quarantine removed — runs seamlessly.       \033[0m"
    echo -e "\033[1;32m==========================================================\033[0m"
    echo ""
    ;;

  Linux*)
    # ── Linux ──
    echo -e "\033[1;34m[1/4] Downloading latest Linux AppImage...\033[0m"
    APPIMAGE_URL="https://github.com/$REPO/releases/latest/download/PreviewGen-Linux.AppImage"
    BIN_DIR="$HOME/.local/bin"
    APPS_DIR="$HOME/.local/share/applications"
    ICONS_DIR="$HOME/.local/share/icons/hicolor/256x256/apps"
    mkdir -p "$BIN_DIR" "$APPS_DIR" "$ICONS_DIR"

    TARGET_BIN="$BIN_DIR/previewgen"
    curl -fL "$APPIMAGE_URL" -o "$TARGET_BIN" --progress-bar
    chmod +x "$TARGET_BIN"

    echo -e "\033[1;34m[2/4] Downloading application icon...\033[0m"
    curl -fsSL "https://raw.githubusercontent.com/$REPO/main/app.ico" -o "$ICONS_DIR/previewgen.ico" 2>/dev/null || true

    echo -e "\033[1;34m[3/4] Creating application menu and desktop entries...\033[0m"
    DESKTOP_ENTRY="[Desktop Entry]
Name=PreviewGen
GenericName=Preview Generator
Comment=Turn transparent PNG files into marketplace JPG previews
Exec=$TARGET_BIN
Icon=$ICONS_DIR/previewgen.ico
Terminal=false
Type=Application
Categories=Graphics;Photography;2DGraphics;
"
    echo "$DESKTOP_ENTRY" > "$APPS_DIR/previewgen.desktop"
    chmod +x "$APPS_DIR/previewgen.desktop"

    if [ -d "$HOME/Desktop" ]; then
      echo "$DESKTOP_ENTRY" > "$HOME/Desktop/PreviewGen.desktop"
      chmod +x "$HOME/Desktop/PreviewGen.desktop"
      # GNOME / KDE trust desktop file
      gio set "$HOME/Desktop/PreviewGen.desktop" metadata::trusted true 2>/dev/null || true
    fi

    # Update desktop database
    update-desktop-database "$APPS_DIR" 2>/dev/null || true

    echo -e "\033[1;34m[4/4] Launching PreviewGen...\033[0m"
    "$TARGET_BIN" & disown 2>/dev/null || true

    echo ""
    echo -e "\033[1;32m==========================================================\033[0m"
    echo -e "\033[1;32m   PreviewGen installed successfully!                     \033[0m"
    echo -e "\033[1;37m   Executable installed to: ~/.local/bin/previewgen       \033[0m"
    echo -e "\033[1;37m   Desktop shortcut created: ~/Desktop/PreviewGen.desktop \033[0m"
    echo -e "\033[1;32m==========================================================\033[0m"
    echo ""
    ;;

  *)
    echo "Unsupported OS: $OS"
    exit 1
    ;;
esac
