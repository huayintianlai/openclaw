#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
HEIC -> JPG 本地转换脚本

用法:
  heic_to_jpg.sh --input <file_or_dir> [--output-dir <dir>] [--quality <1-100>] [--recursive]

参数:
  --input       输入文件或目录（必填）
  --output-dir  输出目录（默认: 与原图同目录）
  --quality     JPG 质量，默认 90
  --recursive   输入为目录时，递归处理子目录中的 .heic/.HEIC
  -h, --help    显示帮助
EOF
}

INPUT=""
OUTPUT_DIR=""
QUALITY="90"
RECURSIVE="0"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --input)
      INPUT="${2:-}"
      shift 2
      ;;
    --output-dir)
      OUTPUT_DIR="${2:-}"
      shift 2
      ;;
    --quality)
      QUALITY="${2:-}"
      shift 2
      ;;
    --recursive)
      RECURSIVE="1"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "未知参数: $1" >&2
      usage
      exit 2
      ;;
  esac
done

if [[ -z "$INPUT" ]]; then
  echo "错误: --input 必填" >&2
  usage
  exit 2
fi

if ! [[ "$QUALITY" =~ ^[0-9]+$ ]] || (( QUALITY < 1 || QUALITY > 100 )); then
  echo "错误: --quality 需为 1-100 的整数" >&2
  exit 2
fi

if [[ ! -e "$INPUT" ]]; then
  echo "错误: 输入路径不存在: $INPUT" >&2
  exit 2
fi

if [[ -n "$OUTPUT_DIR" ]]; then
  mkdir -p "$OUTPUT_DIR"
fi

convert_one() {
  local src="$1"
  local dir base out
  dir="$(dirname "$src")"
  base="$(basename "$src")"
  base="${base%.*}"

  if [[ -n "$OUTPUT_DIR" ]]; then
    out="$OUTPUT_DIR/$base.jpg"
  else
    out="$dir/$base.jpg"
  fi

  if command -v sips >/dev/null 2>&1; then
    if sips -s format jpeg -s formatOptions "$QUALITY" "$src" --out "$out" >/dev/null 2>&1; then
      echo "OK|$src|$out"
      return 0
    fi
  fi

  if command -v magick >/dev/null 2>&1; then
    if magick "$src" -quality "$QUALITY" "$out" >/dev/null 2>&1; then
      echo "OK|$src|$out"
      return 0
    fi
  fi

  echo "FAIL|$src|conversion_failed"
  return 1
}

FILES=()
while IFS= read -r line; do
  [[ -n "$line" ]] && FILES+=("$line")
done < <(
  if [[ -f "$INPUT" ]]; then
    printf '%s\n' "$INPUT"
  else
    if [[ "$RECURSIVE" == "1" ]]; then
      find "$INPUT" -type f \( -iname '*.heic' \)
    else
      find "$INPUT" -maxdepth 1 -type f \( -iname '*.heic' \)
    fi
  fi
)

if [[ ${#FILES[@]} -eq 0 ]]; then
  echo "未找到 HEIC 文件: $INPUT"
  exit 0
fi

success=0
failed=0

for f in "${FILES[@]}"; do
  if convert_one "$f"; then
    ((success++))
  else
    ((failed++))
  fi
done

echo "SUMMARY|success=$success|failed=$failed|total=${#FILES[@]}"

if (( failed > 0 )); then
  exit 1
fi
