#!/usr/bin/env bash
# Compila assets/input.css → static/css/app.css con el CLI standalone de Tailwind.
# Descarga el binario una sola vez (a bin/, ignorado por git) y verifica su SHA256.
#   ./scripts/build_css.sh           build minificado
#   ./scripts/build_css.sh --watch   recompila al guardar
set -euo pipefail

TAILWIND_VERSION="v4.3.4"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

case "$(uname -s)-$(uname -m)" in
  Linux-x86_64)            ASSET="tailwindcss-linux-x64" ;;
  Linux-aarch64)           ASSET="tailwindcss-linux-arm64" ;;
  Darwin-arm64)            ASSET="tailwindcss-macos-arm64" ;;
  Darwin-x86_64)           ASSET="tailwindcss-macos-x64" ;;
  MINGW*|MSYS*|CYGWIN*)    ASSET="tailwindcss-windows-x64.exe" ;;
  *) echo "Plataforma no soportada: $(uname -s)-$(uname -m)" >&2; exit 1 ;;
esac

BIN="bin/tailwindcss-${TAILWIND_VERSION}-${ASSET}"
if [ ! -x "$BIN" ]; then
  mkdir -p bin
  echo "Descargando $ASSET $TAILWIND_VERSION..."
  curl -fsSL -o "$BIN.tmp" \
    "https://github.com/tailwindlabs/tailwindcss/releases/download/${TAILWIND_VERSION}/${ASSET}"
  EXPECTED="$(awk -v a="$ASSET" '$2 == a {print $1}' scripts/tailwindcss.sha256)"
  ACTUAL="$(sha256sum "$BIN.tmp" | awk '{print $1}')"
  if [ -z "$EXPECTED" ] || [ "$EXPECTED" != "$ACTUAL" ]; then
    rm -f "$BIN.tmp"
    echo "ERROR: checksum de $ASSET no coincide (esperado '$EXPECTED', obtenido '$ACTUAL')." >&2
    exit 1
  fi
  mv "$BIN.tmp" "$BIN" && chmod +x "$BIN"
fi

if [ "${1:-}" = "--watch" ]; then
  exec "$BIN" -i assets/input.css -o static/css/app.css --watch
fi
"$BIN" -i assets/input.css -o static/css/app.css --minify
