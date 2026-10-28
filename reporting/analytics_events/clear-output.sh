#!/usr/bin/env bash
set -euo pipefail

# Deletes the contents of reporting/analytics_events/output/, leaving the directory itself in place.

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_DIR="$ROOT/output"

if [[ -d "$OUTPUT_DIR" ]]; then
  find "$OUTPUT_DIR" -mindepth 1 -delete
  echo "Cleared $OUTPUT_DIR"
else
  echo "Nothing to clear: $OUTPUT_DIR does not exist"
fi
