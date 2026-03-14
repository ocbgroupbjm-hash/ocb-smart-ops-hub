#!/bin/bash
# OCB TITAN ERP - Automated Backup Script
# Runs daily at 02:00 server time via cron
# Backup target: tenants database, files, logs

set -e

# Configuration
BACKUP_DIR="/backup/ocb_titan"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="backup_${TIMESTAMP}"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"
LOG_FILE="${BACKUP_DIR}/backup_log.txt"

# MongoDB connection
MONGO_HOST="${MONGO_HOST:-localhost}"
MONGO_PORT="${MONGO_PORT:-27017}"

echo "================================================" >> $LOG_FILE
echo "BACKUP STARTED: $(date)" >> $LOG_FILE
echo "================================================" >> $LOG_FILE

# Create backup directory
mkdir -p "${BACKUP_PATH}/databases"
mkdir -p "${BACKUP_PATH}/files"
mkdir -p "${BACKUP_PATH}/logs"

# 1. Backup all OCB tenant databases
echo "[$(date)] Starting MongoDB backup..." >> $LOG_FILE

# Get list of all ocb_ databases
DATABASES=$(mongosh --quiet --eval "db.adminCommand('listDatabases').databases.map(d => d.name).filter(n => n.startsWith('ocb_') || n === 'erp_db').join(' ')")

for DB in $DATABASES; do
    echo "[$(date)] Backing up database: $DB" >> $LOG_FILE
    mongodump --host $MONGO_HOST --port $MONGO_PORT --db $DB --out "${BACKUP_PATH}/databases/" 2>> $LOG_FILE
done

# 2. Backup application files
echo "[$(date)] Backing up application files..." >> $LOG_FILE
if [ -d "/app/uploads" ]; then
    cp -r /app/uploads "${BACKUP_PATH}/files/" 2>> $LOG_FILE || true
fi

# 3. Backup logs
echo "[$(date)] Backing up logs..." >> $LOG_FILE
if [ -d "/var/log/supervisor" ]; then
    cp -r /var/log/supervisor "${BACKUP_PATH}/logs/" 2>> $LOG_FILE || true
fi

# 4. Create metadata file
cat > "${BACKUP_PATH}/backup_metadata.json" << EOF
{
    "backup_name": "${BACKUP_NAME}",
    "timestamp": "${TIMESTAMP}",
    "created_at": "$(date -Iseconds)",
    "databases": "$(echo $DATABASES | tr ' ' ',')",
    "server": "$(hostname)",
    "mongo_version": "$(mongosh --version 2>/dev/null | head -1 || echo 'unknown')"
}
EOF

# 5. Create compressed archive
echo "[$(date)] Creating compressed archive..." >> $LOG_FILE
cd "${BACKUP_DIR}"
tar -czf "${BACKUP_NAME}.tar.gz" "${BACKUP_NAME}"

# 6. Calculate checksum
CHECKSUM=$(sha256sum "${BACKUP_NAME}.tar.gz" | awk '{print $1}')
echo "$CHECKSUM ${BACKUP_NAME}.tar.gz" > "${BACKUP_NAME}.tar.gz.sha256"

# 7. Cleanup uncompressed folder
rm -rf "${BACKUP_PATH}"

# 8. Cleanup old backups (keep last 7 days)
find "${BACKUP_DIR}" -name "backup_*.tar.gz" -mtime +7 -delete 2>> $LOG_FILE || true
find "${BACKUP_DIR}" -name "backup_*.tar.gz.sha256" -mtime +7 -delete 2>> $LOG_FILE || true

# Report
BACKUP_SIZE=$(du -h "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" | awk '{print $1}')
echo "[$(date)] BACKUP COMPLETED" >> $LOG_FILE
echo "  - Archive: ${BACKUP_NAME}.tar.gz" >> $LOG_FILE
echo "  - Size: ${BACKUP_SIZE}" >> $LOG_FILE
echo "  - Checksum: ${CHECKSUM}" >> $LOG_FILE
echo "================================================" >> $LOG_FILE

# Output for verification
echo "{\"status\": \"success\", \"backup_name\": \"${BACKUP_NAME}.tar.gz\", \"size\": \"${BACKUP_SIZE}\", \"checksum\": \"${CHECKSUM}\", \"timestamp\": \"${TIMESTAMP}\"}"
