#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

DOCS_DIR="${DOCS_DIR:-${PROJECT_ROOT}/documents}"
RESP_DIR="${RESP_DIR:-${PROJECT_ROOT}/response}"
SERVICE_URL="${SERVICE_URL:-http://127.0.0.1:8000/convert}"

if [[ ! -d "${DOCS_DIR}" ]]; then
  echo "Documents directory not found: ${DOCS_DIR}" >&2
  exit 1
fi

mkdir -p "${RESP_DIR}"

processed=0
failed=0

shopt -s nullglob
for file_path in "${DOCS_DIR}"/*; do
  [[ -f "${file_path}" ]] || continue

  ext="$(printf '%s' "${file_path##*.}" | tr '[:upper:]' '[:lower:]')"

  case "${ext}" in
    pdf|docx|xlsx|pptx|html|txt|rtf|epub|md|csv|tsv|jpg|jpeg|png|gif|bmp|webp|tiff) ;;
    *)
      echo "Skipping unsupported file: $(basename "${file_path}")"
      continue
      ;;
  esac

  base_name="$(basename "${file_path}")"
  stem="${base_name%.*}"
  output_path="${RESP_DIR}/${stem}.md"

  echo "Processing ${base_name} -> $(basename "${output_path}")"
  if curl -sS -f -X POST -F "file=@${file_path}" "${SERVICE_URL}" -o "${output_path}"; then
    processed=$((processed + 1))
  else
    echo "Failed to process: ${base_name}" >&2
    failed=$((failed + 1))
  fi
done
shopt -u nullglob

echo "Completed. Processed=${processed}, Failed=${failed}, Output=${RESP_DIR}"
if [[ "${processed}" -eq 0 ]]; then
  echo "No supported files were processed." >&2
fi

if [[ "${failed}" -gt 0 ]]; then
  exit 1
fi
