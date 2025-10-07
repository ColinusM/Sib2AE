#!/bin/bash

# Import notation exports to Brain/Base with timestamp folder
# Usage: Run via Keyboard Maestro shortcut

# Configuration
EXPORT_DIR="/Users/colinmignot/Documents/Partitions"
BASE_DIR="/Users/colinmignot/Claude Code/Sib2Ae/Brain/Base"
LOG_FILE="/tmp/import_notation_export.log"
TIMESTAMP=$(date +%H%M%S)
DEST_DIR="${BASE_DIR}/${TIMESTAMP}"

# Log function
log() {
    echo "[$(date +%H:%M:%S)] $1" >> "$LOG_FILE"
    echo "$1"
}

log "=== Import started ==="
log "Export dir: $EXPORT_DIR"

# Find 3 most recent files (musicxml, svg, mid) in export directory
FILES=()
while IFS= read -r file; do
    FILES+=("$file")
    log "Found: $file"
done < <(find "$EXPORT_DIR" -maxdepth 1 -type f \( -name "*.musicxml" -o -name "*.svg" -o -name "*.mid" \) -print0 2>>"$LOG_FILE" | xargs -0 ls -t 2>>"$LOG_FILE" | head -3)

# Validate exactly 3 files found
log "Total files found: ${#FILES[@]}"
if [ ${#FILES[@]} -ne 3 ]; then
    log "✗ Found ${#FILES[@]} files (expected 3)"
    exit 1
fi

# Check destination doesn't already exist
if [ -d "$DEST_DIR" ]; then
    log "✗ Folder Brain/Base/${TIMESTAMP}/ already exists"
    exit 1
fi

# Create destination folder
mkdir -p "$DEST_DIR"
log "Created: $DEST_DIR"

# Move files
for file in "${FILES[@]}"; do
    mv "$file" "${DEST_DIR}/"
    log "Moved: $(basename "$file")"
done

# Verify
COUNT=$(ls "$DEST_DIR" | wc -l | xargs)
log "Verification: $COUNT files in destination"
if [ "$COUNT" -eq 3 ]; then
    log "✓ Imported 3 files to Brain/Base/${TIMESTAMP}/"
    exit 0
else
    log "✗ Import failed: found $COUNT files in destination"
    exit 1
fi
