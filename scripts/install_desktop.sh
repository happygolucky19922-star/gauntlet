#!/usr/bin/env bash
set -euo pipefail

APP_NAME="Lucy"
INSTALL_ROOT="${HOME}/.local/share/lucy"
BIN_PATH="${INSTALL_ROOT}/lucy-launch"
DESKTOP_FILE="${HOME}/.local/share/applications/lucy.desktop"
ICON_PATH="${INSTALL_ROOT}/lucy.png"

mkdir -p "${INSTALL_ROOT}" "$(dirname "${DESKTOP_FILE}")"

cat > "${BIN_PATH}" <<'LAUNCH'
#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-/workspace/gauntlet}"

cd "${PROJECT_DIR}/backend"
exec uvicorn app.main:app --host 127.0.0.1 --port 8000
LAUNCH
chmod +x "${BIN_PATH}"

if [[ ! -f "${ICON_PATH}" ]]; then
  # lightweight placeholder icon (1x1 transparent png base64)
  base64 -d > "${ICON_PATH}" <<'PNG'
iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9pR3xZkAAAAASUVORK5CYII=
PNG
fi

cat > "${DESKTOP_FILE}" <<DESKTOP
[Desktop Entry]
Type=Application
Version=1.0
Name=${APP_NAME}
Comment=Launch Lucy local backend
Exec=${BIN_PATH}
Icon=${ICON_PATH}
Terminal=true
Categories=Development;Utility;
DESKTOP

update-desktop-database "${HOME}/.local/share/applications" >/dev/null 2>&1 || true

echo "Installed launcher: ${DESKTOP_FILE}"
echo "You can search for '${APP_NAME}' in your desktop app launcher."
