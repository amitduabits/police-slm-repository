#!/bin/bash
# Gujarat Police SLM - Backup Script
# Backs up: PostgreSQL, ChromaDB data, configs, models

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-./backups}"
RETENTION_DAYS="${RETENTION_DAYS:-90}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_PATH="${BACKUP_DIR}/${TIMESTAMP}"

echo "=== Gujarat Police SLM Backup ==="
echo "Timestamp: ${TIMESTAMP}"
echo "Backup to: ${BACKUP_PATH}"

mkdir -p "${BACKUP_PATH}"

# 1. PostgreSQL Backup
echo "[1/4] Backing up PostgreSQL..."
PGPASSWORD="${POSTGRES_PASSWORD:-changeme}" pg_dump \
    -h "${POSTGRES_HOST:-localhost}" \
    -U "${POSTGRES_USER:-gujpol_admin}" \
    -d "${POSTGRES_DB:-gujpol_slm}" \
    --format=custom \
    --compress=9 \
    -f "${BACKUP_PATH}/postgres_${TIMESTAMP}.dump" 2>/dev/null && \
    echo "  ✅ PostgreSQL backup complete" || \
    echo "  ⚠️ PostgreSQL backup failed (service may not be running)"

# 2. ChromaDB Backup
echo "[2/4] Backing up ChromaDB..."
if [ -d "/chroma-data" ]; then
    tar -czf "${BACKUP_PATH}/chroma_${TIMESTAMP}.tar.gz" -C /chroma-data . 2>/dev/null && \
        echo "  ✅ ChromaDB backup complete" || \
        echo "  ⚠️ ChromaDB backup failed"
elif [ -d "data/embeddings/chroma" ]; then
    tar -czf "${BACKUP_PATH}/chroma_${TIMESTAMP}.tar.gz" -C data/embeddings/chroma . 2>/dev/null && \
        echo "  ✅ ChromaDB backup complete" || \
        echo "  ⚠️ ChromaDB backup failed"
else
    echo "  ⏭️ No ChromaDB data found, skipping"
fi

# 3. Configs Backup
echo "[3/4] Backing up configs..."
if [ -d "configs" ]; then
    tar -czf "${BACKUP_PATH}/configs_${TIMESTAMP}.tar.gz" configs/ .env 2>/dev/null && \
        echo "  ✅ Configs backup complete" || \
        echo "  ⚠️ Configs backup failed"
fi

# 4. Model Checkpoints
echo "[4/4] Backing up model metadata..."
if [ -d "models" ]; then
    # Only backup model metadata, not the full GGUF (too large)
    find models/ -name "*.json" -o -name "*.yaml" -o -name "*.txt" | \
        tar -czf "${BACKUP_PATH}/model_meta_${TIMESTAMP}.tar.gz" -T - 2>/dev/null && \
        echo "  ✅ Model metadata backup complete" || \
        echo "  ⚠️ Model metadata backup failed"
fi

# Create manifest
echo "Creating backup manifest..."
cat > "${BACKUP_PATH}/manifest.json" <<EOF
{
    "timestamp": "${TIMESTAMP}",
    "files": $(ls -la "${BACKUP_PATH}" | tail -n +4 | awk '{print "\"" $NF "\""}' | paste -sd,),
    "total_size": "$(du -sh "${BACKUP_PATH}" | cut -f1)"
}
EOF

echo "  ✅ Manifest created"

# Cleanup old backups
echo ""
echo "Cleaning up backups older than ${RETENTION_DAYS} days..."
find "${BACKUP_DIR}" -maxdepth 1 -type d -mtime +${RETENTION_DAYS} -exec rm -rf {} + 2>/dev/null
echo "  ✅ Cleanup complete"

echo ""
echo "=== Backup Complete ==="
echo "Location: ${BACKUP_PATH}"
echo "Size: $(du -sh "${BACKUP_PATH}" | cut -f1)"
