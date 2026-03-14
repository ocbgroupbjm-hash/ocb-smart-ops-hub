#!/bin/bash
# OCB TITAN ERP - Backup Verification Script
# Validates backup integrity

set -e

BACKUP_DIR="/backup/ocb_titan"
OUTPUT_FILE="${BACKUP_DIR}/backup_validation.json"

echo "Starting backup validation..."

# Find latest backup
LATEST_BACKUP=$(ls -t ${BACKUP_DIR}/backup_*.tar.gz 2>/dev/null | head -1)

if [ -z "$LATEST_BACKUP" ]; then
    echo '{"status": "error", "message": "No backup files found"}' > $OUTPUT_FILE
    exit 1
fi

BACKUP_NAME=$(basename "$LATEST_BACKUP")
CHECKSUM_FILE="${LATEST_BACKUP}.sha256"

# 1. Check if checksum file exists
if [ ! -f "$CHECKSUM_FILE" ]; then
    echo '{"status": "error", "message": "Checksum file not found"}' > $OUTPUT_FILE
    exit 1
fi

# 2. Verify checksum
echo "Verifying checksum..."
EXPECTED_CHECKSUM=$(cat "$CHECKSUM_FILE" | awk '{print $1}')
ACTUAL_CHECKSUM=$(sha256sum "$LATEST_BACKUP" | awk '{print $1}')

if [ "$EXPECTED_CHECKSUM" != "$ACTUAL_CHECKSUM" ]; then
    cat > $OUTPUT_FILE << EOF
{
    "status": "error",
    "message": "Checksum mismatch",
    "expected": "$EXPECTED_CHECKSUM",
    "actual": "$ACTUAL_CHECKSUM"
}
EOF
    exit 1
fi

# 3. Verify archive integrity
echo "Verifying archive integrity..."
if ! tar -tzf "$LATEST_BACKUP" > /dev/null 2>&1; then
    echo '{"status": "error", "message": "Archive is corrupted"}' > $OUTPUT_FILE
    exit 1
fi

# 4. List archive contents
FILE_COUNT=$(tar -tzf "$LATEST_BACKUP" | wc -l)
ARCHIVE_SIZE=$(du -h "$LATEST_BACKUP" | awk '{print $1}')

# 5. Extract and check metadata
TEMP_DIR=$(mktemp -d)
tar -xzf "$LATEST_BACKUP" -C "$TEMP_DIR" --wildcards "*/backup_metadata.json" 2>/dev/null || true

METADATA_FILE=$(find "$TEMP_DIR" -name "backup_metadata.json" 2>/dev/null | head -1)
if [ -f "$METADATA_FILE" ]; then
    METADATA=$(cat "$METADATA_FILE")
else
    METADATA="{}"
fi

rm -rf "$TEMP_DIR"

# Generate validation report
cat > $OUTPUT_FILE << EOF
{
    "status": "valid",
    "backup_file": "$BACKUP_NAME",
    "backup_path": "$LATEST_BACKUP",
    "file_size": "$ARCHIVE_SIZE",
    "file_count": $FILE_COUNT,
    "checksum_valid": true,
    "checksum": "$ACTUAL_CHECKSUM",
    "archive_integrity": "valid",
    "validated_at": "$(date -Iseconds)",
    "metadata": $METADATA
}
EOF

echo "Backup validation completed successfully!"
cat $OUTPUT_FILE
