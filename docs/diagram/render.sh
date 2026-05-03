#!/usr/bin/env bash
# Render all .mmd sources in this folder to PNG. (강사용 빌드 도구)
#
# OS 환경: macOS/Linux 강사 환경용. 학생이 실행할 필요 없음.
# (학생에겐 사전 렌더된 .png를 그대로 배포한다.)
# Windows 강사는 WSL2에서 실행하거나, mermaid-cli + Chrome을 별도 호출.
#
# Requires: node, npm. Auto-installs mermaid-cli locally on first run.
# Uses system Chrome (macOS) so puppeteer's Chromium download is skipped.

set -euo pipefail
cd "$(dirname "$0")"

NODE_DIR="$(pwd)/.node"
MMDC="$NODE_DIR/node_modules/.bin/mmdc"

if [ ! -x "$MMDC" ]; then
  echo "→ mermaid-cli 로컬 설치 중 (puppeteer chromium 다운로드 생략, 1~2분 소요)..."
  mkdir -p "$NODE_DIR"
  (
    cd "$NODE_DIR"
    [ -f package.json ] || npm init -y >/dev/null 2>&1
    PUPPETEER_SKIP_DOWNLOAD=true npm install @mermaid-js/mermaid-cli 2>&1 | tail -3
  )
  if [ ! -x "$MMDC" ]; then
    echo "✗ mermaid-cli 설치 실패. /tmp/mtest/node_modules/.bin/mmdc 같은 기존 설치를 직접 사용하세요."
    exit 1
  fi
fi

CONFIG="$(pwd)/puppeteer-config.json"
TARGETS=("$@")
[ ${#TARGETS[@]} -eq 0 ] && TARGETS=(*.mmd)

for src in "${TARGETS[@]}"; do
  [ -f "$src" ] || { echo "skip: $src not found"; continue; }
  out="${src%.mmd}.png"
  echo "→ $src → $out"
  "$MMDC" -i "$src" -o "$out" -p "$CONFIG" -b transparent --scale 2 >/dev/null
done

echo "✔ 완료. ls *.png"
