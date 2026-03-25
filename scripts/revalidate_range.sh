#!/bin/bash

# Usage:
# ./revalidate_range.sh 2026-02-13 2026-02-18

START_DATE="$1"
END_DATE="$2"

if [ -z "$START_DATE" ] || [ -z "$END_DATE" ]; then
  echo "Uso: ./revalidate_range.sh YYYY-MM-DD YYYY-MM-DD"
  exit 1
fi

PROJECT_DIR="/opt/wma-cross-alerts"
PYTHON_BIN="$PROJECT_DIR/venv/bin/python"
LOG_FILE="$PROJECT_DIR/logs/app.log"

current="$START_DATE"

while [ "$current" != "$(date -d "$END_DATE + 1 day" +%Y-%m-%d)" ]; do
  echo "Revalidando fecha: $current"

  cd "$PROJECT_DIR" || exit 1

  "$PYTHON_BIN" -m wma_cross_alerts.main \
    --date "$current" \
    --mode revalidation \
    >> "$LOG_FILE" 2>&1

  current=$(date -d "$current + 1 day" +%Y-%m-%d)
done

echo "Revalidacion completada desde $START_DATE hasta $END_DATE"

