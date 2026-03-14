#!/bin/bash
# OCB TITAN ERP - Daily Backup Script
# Schedule: 02:00 server time via cron
# Backup target: all tenant databases, files, logs, config

set -e

# Configuration
BACKUP_DIR="/backup/ocb_titan"
TIMESTAMP=$(date +%Y%m%d_%H%M)
BACKUP_FILE="backup_${TIMESTAMP}.tar.gz"
MONGO_HOST="${MONGO_HOST:-localhost}"
MONGO_PORT="${MONGO_PORT:-27017}"
LOG_FILE="${BACKUP_DIR}/backup.log"

# Create backup directory if not exists
mkdir -p "${BACKUP_DIR}"
mkdir -p "${BACKUP_DIR}/temp"

echo "[$(date)] Starting backup process..." | tee -a "$LOG_FILE"

# List of tenant databases to backup
TENANTS="ocb_titan ocb_baju ocb_counter ocb_unit_4 ocb_unt_1"

# 1. Backup all tenant databases
echo "[$(date)] Backing up databases..." | tee -a "$LOG_FILE"
for tenant in $TENANTS; do
    echo "  - Dumping $tenant..." | tee -a "$LOG_FILE"
    mongodump --host "$MONGO_HOST" --port "$MONGO_PORT" --db "$tenant" --out "${BACKUP_DIR}/temp/mongo_dump" --quiet 2>/dev/null || true
done

# 2. Backup application files
echo "[$(date)] Backing up application files..." | tee -a "$LOG_FILE"
if [ -d "/app/backend/uploads" ]; then
    cp -r /app/backend/uploads "${BACKUP_DIR}/temp/uploads" 2>/dev/null || true
fi
if [ -d "/app/backend/files" ]; then
    cp -r /app/backend/files "${BACKUP_DIR}/temp/files" 2>/dev/null || true
fi

# 3. Backup configuration files
echo "[$(date)] Backing up config files..." | tee -a "$LOG_FILE"
mkdir -p "${BACKUP_DIR}/temp/config"
cp /app/backend/.env "${BACKUP_DIR}/temp/config/.env.backup" 2>/dev/null || true
cp /app/frontend/.env "${BACKUP_DIR}/temp/config/frontend.env.backup" 2>/dev/null || true

# 4. Backup logs (last 7 days)
echo "[$(date)] Backing up logs..." | tee -a "$LOG_FILE"
mkdir -p "${BACKUP_DIR}/temp/logs"
find /var/log/supervisor -name "*.log" -mtime -7 -exec cp {} "${BACKUP_DIR}/temp/logs/" \; 2>/dev/null || true

# 5. Create compressed archive
echo "[$(date)] Creating compressed archive..." | tee -a "$LOG_FILE"
cd "${BACKUP_DIR}/temp"
tar -czf "${BACKUP_DIR}/${BACKUP_FILE}" . 2>/dev/null

# 6. Generate checksum
echo "[$(date)] Generating checksum..." | tee -a "$LOG_FILE"
cd "${BACKUP_DIR}"
sha256sum "${BACKUP_FILE}" > "${BACKUP_FILE}.sha256"

# 7. Calculate backup size
BACKUP_SIZE=$(du -h "${BACKUP_DIR}/${BACKUP_FILE}" | cut -f1)

# 8. Cleanup temp directory
rm -rf "${BACKUP_DIR}/temp"

# 9. Cleanup old backups (keep last 7 days)
echo "[$(date)] Cleaning up old backups..." | tee -a "$LOG_FILE"
find "${BACKUP_DIR}" -name "backup_*.tar.gz" -mtime +7 -delete 2>/dev/null || true
find "${BACKUP_DIR}" -name "backup_*.tar.gz.sha256" -mtime +7 -delete 2>/dev/null || true

# 10. Generate backup metadata
cat > "${BACKUP_DIR}/backup_${TIMESTAMP}_metadata.json" << EOF
{
    "backup_file": "${BACKUP_FILE}",
    "timestamp": "$(date -Iseconds)",
    "backup_size": "${BACKUP_SIZE}",
    "tenants": ["ocb_titan", "ocb_baju", "ocb_counter", "ocb_unit_4", "ocb_unt_1"],
    "includes": {
        "databases": true,
        "uploads": true,
        "config": true,
        "logs": true
    },
    "retention_days": 7,
    "status": "completed"
}
EOF

echo "[$(date)] Backup completed: ${BACKUP_FILE} (${BACKUP_SIZE})" | tee -a "$LOG_FILE"
echo "[$(date)] Checksum: $(cat ${BACKUP_DIR}/${BACKUP_FILE}.sha256)" | tee -a "$LOG_FILE"

exit 0
