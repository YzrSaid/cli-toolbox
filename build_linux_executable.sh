#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIST_DIR="$ROOT_DIR/dist"
BUILD_DIR="$ROOT_DIR/build"
SPEC_FILE="$ROOT_DIR/cli-toolbox.spec"
BUILD_VENV_DIR="$ROOT_DIR/.build-venv"

has_shared_python() {
  local python_cmd="$1"
  "$python_cmd" -c "import sysconfig; print(int(bool(sysconfig.get_config_var('Py_ENABLE_SHARED'))))" 2>/dev/null | grep -q '^1$'
}

prepare_build_python() {
  if [[ -x "$ROOT_DIR/venv/bin/python" ]] && has_shared_python "$ROOT_DIR/venv/bin/python"; then
    echo "$ROOT_DIR/venv/bin/python"
    return
  fi

  local candidates=("${PYTHON_BIN:-python3}" "python3" "python")
  local shared_base=""

  for candidate in "${candidates[@]}"; do
    if command -v "$candidate" >/dev/null 2>&1 && has_shared_python "$candidate"; then
      shared_base="$candidate"
      break
    fi
  done

  if [[ -z "$shared_base" ]]; then
    echo "Error: No shared-library Python found for PyInstaller." >&2
    echo "Install a standard system Python (e.g. python3) and retry." >&2
    exit 1
  fi

  "$shared_base" -m venv "$BUILD_VENV_DIR"
  "$BUILD_VENV_DIR/bin/python" -m pip install -q --upgrade pip
  "$BUILD_VENV_DIR/bin/python" -m pip install -q -r "$ROOT_DIR/requirements.txt"
  echo "$BUILD_VENV_DIR/bin/python"
}

PYTHON_BIN="$(prepare_build_python)"

echo "[1/3] Building Linux executable with PyInstaller..."
"$PYTHON_BIN" -m PyInstaller \
  --noconfirm \
  --clean \
  --onefile \
  --name cli-toolbox \
  --hidden-import pillow_heif \
  --collect-all pyfiglet \
  --collect-all rich \
  "$ROOT_DIR/main.py"

rm -rf "$BUILD_DIR"
rm -f "$SPEC_FILE"

LAUNCHER_FILE="$DIST_DIR/CLI-Toolbox-Launcher.sh"
DESKTOP_FILE="$DIST_DIR/CLI-Toolbox.desktop"

echo "[2/3] Creating double-click launcher..."
cat > "$LAUNCHER_FILE" << 'EOF'
#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_BIN="$APP_DIR/cli-toolbox"

if [[ ! -x "$APP_BIN" ]]; then
  echo "Executable not found: $APP_BIN"
  exit 1
fi

if [[ -t 1 ]]; then
  "$APP_BIN"
  exit 0
fi

run_in_terminal() {
  local terminal_cmd="$1"

  case "$terminal_cmd" in
    gnome-terminal)
      gnome-terminal -- bash -lc "\"$APP_BIN\"; echo; read -rp 'Press Enter to close...'"
      ;;
    konsole)
      konsole -e bash -lc "\"$APP_BIN\"; echo; read -rp 'Press Enter to close...'"
      ;;
    xfce4-terminal)
      xfce4-terminal --hold -e "\"$APP_BIN\""
      ;;
    xterm)
      xterm -hold -e "\"$APP_BIN\""
      ;;
    kitty)
      kitty sh -lc "\"$APP_BIN\"; echo; read -rp 'Press Enter to close...'"
      ;;
    alacritty)
      alacritty -e bash -lc "\"$APP_BIN\"; echo; read -rp 'Press Enter to close...'"
      ;;
    *)
      return 1
      ;;
  esac
}

for term in gnome-terminal konsole xfce4-terminal kitty alacritty xterm; do
  if command -v "$term" >/dev/null 2>&1; then
    run_in_terminal "$term"
    exit 0
  fi
done

"$APP_BIN"
EOF

chmod +x "$LAUNCHER_FILE"
chmod +x "$DIST_DIR/cli-toolbox"

echo "[3/3] Creating desktop entry template..."
cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Type=Application
Name=CLI Toolbox
Comment=Launch CLI Toolbox
Exec=$LAUNCHER_FILE
Terminal=false
Categories=Utility;
Icon=utilities-terminal
EOF

echo
echo "Done!"
echo "Executable: $DIST_DIR/cli-toolbox"
echo "Launcher:   $LAUNCHER_FILE"
echo "Desktop:    $DESKTOP_FILE"
echo
echo "Tip: You can copy $DESKTOP_FILE to ~/.local/share/applications/"
