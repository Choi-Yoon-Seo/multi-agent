#!/usr/bin/env bash
# 강의자료 변환 (강사용 빌드 도구): weekXX.md → weekXX.html (+ weekXX.pdf)
#
# ─── OS 환경 ───────────────────────────────────────────────────────
# 본 스크립트는 macOS/Linux 강사 환경용이다. 학생이 실행할 필요 없음.
# (학생에겐 빌드된 .html/.pdf만 배포한다.)
# Windows 강사는 WSL2(Ubuntu)에서 그대로 실행하거나, pandoc + Chrome을
# 직접 호출하는 PowerShell 명령을 별도로 작성한다.
# ──────────────────────────────────────────────────────────────────
#
# 사용:
#   ./build.sh                 # 모든 week-*.md 변환
#   ./build.sh week-10         # 특정 주차만
#   ./build.sh week-10 --html  # HTML만 (PDF 생략)
#
# 출력 위치: class/ 바로 아래 (week-XX.md와 같은 폴더)
#  - class/week-10.html  (단일 파일, 다이어그램 base64 임베드)
#  - class/week-10.pdf   (Chrome headless 렌더)
#  더블클릭으로 바로 열린다.
#
# 의존성: pandoc, /Applications/Google Chrome.app (macOS)
# - HTML: pandoc --embed-resources 로 PNG 모두 base64 임베드 → 단일 파일
# - PDF: HTML을 Chrome headless로 print-to-pdf

set -euo pipefail
cd "$(dirname "$0")"

OUT_DIR="."

# CSS 임시 파일 (process substitution 대신 — pandoc embed 호환성)
CSS_FILE="$(mktemp -t buildsh_css.XXXX.css)"
trap 'rm -f "$CSS_FILE"' EXIT
cat > "$CSS_FILE" <<'CSS'
body { max-width: 900px; margin: 2em auto; padding: 0 1em; font-family: -apple-system, "Helvetica Neue", "Apple SD Gothic Neo", "Noto Sans KR", sans-serif; line-height: 1.6; color: #222; }
h1, h2, h3, h4 { color: #111; margin-top: 1.6em; }
h1 { border-bottom: 2px solid #333; padding-bottom: 0.3em; }
h2 { border-bottom: 1px solid #ccc; padding-bottom: 0.2em; }
code { background: #f3f4f6; padding: 0.1em 0.3em; border-radius: 3px; font-size: 0.95em; }
pre { background: #f3f4f6; padding: 0.8em 1em; border-radius: 6px; overflow-x: auto; }
pre code { background: none; padding: 0; font-size: 0.88em; }
img { max-width: 100%; display: block; margin: 1em auto; }
table { border-collapse: collapse; margin: 1em 0; }
th, td { border: 1px solid #ddd; padding: 0.5em 0.8em; }
th { background: #f8f9fa; }
blockquote { border-left: 4px solid #93c5fd; padding: 0.4em 1em; background: #eff6ff; color: #1e3a8a; margin: 1em 0; }
@media print {
  body { max-width: 100%; }
  h2 { page-break-before: auto; }
  pre, img, table { page-break-inside: avoid; }
}
CSS

CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
HTML_ONLY=false

# 인자 파싱
TARGETS=()
for arg in "$@"; do
  case "$arg" in
    --html) HTML_ONLY=true ;;
    *) TARGETS+=("$arg") ;;
  esac
done
[ ${#TARGETS[@]} -eq 0 ] && TARGETS=(week-*.md)

build_one() {
  local md="$1"
  local base="${md%.md}"
  local html="$OUT_DIR/$base.html"
  local pdf="$OUT_DIR/$base.pdf"

  [ -f "$md" ] || { echo "skip: $md not found"; return; }

  echo "→ $md → $html"
  pandoc "$md" \
    -o "$html" \
    --standalone \
    --embed-resources \
    --resource-path=. \
    --metadata title="$base" \
    --css="$CSS_FILE"

  if ! $HTML_ONLY; then
    if [ -x "$CHROME" ]; then
      echo "→ $html → $pdf"
      "$CHROME" --headless --disable-gpu --no-sandbox \
        --print-to-pdf="$pdf" \
        --print-to-pdf-no-header \
        "file://$(pwd)/$html" >/dev/null 2>&1 || echo "  ⚠ PDF 생성 실패 (HTML은 생성됨)"
    else
      echo "  ⚠ Chrome 없음 — PDF 생략 (HTML만 생성)"
    fi
  fi
}

for t in "${TARGETS[@]}"; do
  # week-10 또는 week-10.md 둘 다 허용
  [[ "$t" != *.md ]] && t="$t.md"
  build_one "$t"
done

echo ""
echo "✔ 완료. 산출물: $OUT_DIR/"
ls -la "$OUT_DIR" 2>/dev/null | tail -n +2 | awk '{print "  " $NF, "(" $5 " bytes)"}'
