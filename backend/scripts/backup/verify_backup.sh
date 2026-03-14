#!/bin/bash
# OCB TITAN ERP - Backup Verification Script v2
# Validates backup integrity, checksum, and size

set -e

BACKUP_DIR="/backup/ocb_titan"
OUTPUT_FILE="${BACKUP_DIR}/backup_validation.json"

echo "=== OCB TITAN Backup Verification ==="

# Find latest backup
LATEST_BACKUP=$(ls -t "${BACKUP_DIR}"/backup_*.tar.gz 2>/dev/null | head -1)

if [ -z "$LATEST_BACKUP" ]; then
    echo "ERROR: No backup files found"
    cat > "$OUTPUT_FILE" << EOF
{
    "timestamp": "$(date -Iseconds)",
    "status": "FAILED",
    "error": "No backup files found",
    "checks": {}
}
EOF
    exit 1
fi

BACKUP_NAME=$(basename "$LATEST_BACKUP")
CHECKSUM_FILE="${LATEST_BACKUP}.sha256"

echo "Verifying: $BACKUP_NAME"

# Initialize results
ARCHIVE_CHECK="PASS"
CHECKSUM_CHECK="PASS"
SIZE_CHECK="PASS"
CONTENT_CHECK="PASS"
ERRORS=""

# 1. Archive Integrity Check
echo "1. Checking archive integrity..."
if gzip -t "$LATEST_BACKUP" 2>/dev/null; then
    echo "   ✓ Archive integrity: PASS"
else
    ARCHIVE_CHECK="FAIL"
    ERRORS="${ERRORS}Archive corrupted. "
    echo "   ✗ Archive integrity: FAIL"
fi

# 2. Checksum Verification
echo "2. Verifying checksum..."
if [ -f "$CHECKSUM_FILE" ]; then
    cd "$BACKUP_DIR"
    if sha256sum -c "$CHECKSUM_FILE" --quiet 2>/dev/null; then
        echo "   ✓ Checksum verification: PASS"
    else
        CHECKSUM_CHECK="FAIL"
        ERRORS="${ERRORS}Checksum mismatch. "
        echo "   ✗ Checksum verification: FAIL"
    fi
else
    CHECKSUM_CHECK="SKIP"
    echo "   - Checksum file not found, skipping"
fi

# 3. Backup Size Validation (minimum 1KB)
echo "3. Validating backup size..."
BACKUP_SIZE_BYTES=$(stat -c%s "$LATEST_BACKUP" 2>/dev/null || stat -f%z "$LATEST_BACKUP" 2>/dev/null || echo "0")
BACKUP_SIZE_HUMAN=$(du -h "$LATEST_BACKUP" | cut -f1)

if [ "$BACKUP_SIZE_BYTES" -gt 1024 ]; then
    echo "   ✓ Backup size: $BACKUP_SIZE_HUMAN (PASS)"
else
    SIZE_CHECK="FAIL"
    ERRORS="${ERRORS}Backup too small. "
    echo "   ✗ Backup size: $BACKUP_SIZE_HUMAN (FAIL - too small)"
fi

# 4. Content Verification (check archive contents)
echo "4. Verifying archive contents..."
CONTENT_LIST=$(tar -tzf "$LATEST_BACKUP" 2>/dev/null | head -20)
HAS_MONGO=$(echo "$CONTENT_LIST" | grep -c "mongo_dump" || true)
HAS_CONFIG=$(echo "$CONTENT_LIST" | grep -c "config" || true)

if [ "$HAS_MONGO" -gt 0 ] || [ "$HAS_CONFIG" -gt 0 ]; then
    echo "   ✓ Content verification: PASS"
else
    CONTENT_CHECK="WARN"
    echo "   - Content verification: WARNING (minimal content)"
fi

# Determine overall status
if [ "$ARCHIVE_CHECK" = "PASS" ] && [ "$SIZE_CHECK" = "PASS" ]; then
    OVERALL_STATUS="PASS"
else
    OVERALL_STATUS="FAIL"
fi

# Generate JSON report
cat > "$OUTPUT_FILE" << EOF
{
    "timestamp": "$(date -Iseconds)",
    "backup_file": "$BACKUP_NAME",
    "backup_path": "$LATEST_BACKUP",
    "backup_size": "$BACKUP_SIZE_HUMAN",
    "backup_size_bytes": $BACKUP_SIZE_BYTES,
    "status": "$OVERALL_STATUS",
    "checks": {
        "archive_integrity": "$ARCHIVE_CHECK",
        "checksum_verification": "$CHECKSUM_CHECK",
        "size_validation": "$SIZE_CHECK",
        "content_verification": "$CONTENT_CHECK"
    },
    "errors": "$ERRORS"
}
EOF

echo ""
echo "=== Verification Complete ==="
echo "Status: $OVERALL_STATUS"
echo "Report: $OUTPUT_FILE"

exit 0
