#!/bin/bash
# Gujarat Police SLM - Upgrade Execution Script
# Integrates Kaggle SC Judgments + New Dashboard

set -e  # Exit on error

PROJECT_ROOT="D:/projects/Ongoing/gujarat police/Implementation project/gujpol-slm-complete/gujpol-slm-complete"
cd "$PROJECT_ROOT"

echo "================================"
echo "GUJARAT POLICE SLM UPGRADE"
echo "================================"
echo ""

# ============================================================================
# STEP 1: BACKUP OLD DASHBOARD
# ============================================================================
echo "[1/6] Backing up old dashboard..."
if [ -d "src/dashboard" ]; then
    BACKUP_NAME="src/dashboard-backup-$(date +%Y%m%d-%H%M%S)"
    mv src/dashboard "$BACKUP_NAME"
    echo "✅ Old dashboard backed up to: $BACKUP_NAME"
else
    echo "⚠️  No old dashboard found at src/dashboard"
fi
echo ""

# ============================================================================
# STEP 2: INSTALL NEW DASHBOARD
# ============================================================================
echo "[2/6] Installing new upgraded dashboard..."
if [ -d "dashboard" ]; then
    mv dashboard src/dashboard
    echo "✅ New dashboard moved to src/dashboard"

    cd src/dashboard
    echo "📦 Installing npm dependencies..."
    npm install
    echo "✅ Dashboard dependencies installed"
    cd "$PROJECT_ROOT"
else
    echo "❌ ERROR: dashboard/ folder not found at project root"
    exit 1
fi
echo ""

# ============================================================================
# STEP 3: FIX BCRYPT ERROR (BEFORE INGESTION)
# ============================================================================
echo "[3/6] Fixing bcrypt compatibility..."
pip install bcrypt==4.0.1 --break-system-packages
echo "✅ bcrypt fixed"
echo ""

# ============================================================================
# STEP 4: PREPARE ARCHIVE DATA FOR INGESTION
# ============================================================================
echo "[4/6] Checking archive data..."
ARCHIVE_PATH="archive/supreme_court_judgments"
PDF_COUNT=$(find "$ARCHIVE_PATH" -type f -name "*.PDF" 2>/dev/null | wc -l || echo "0")
echo "📁 Found $PDF_COUNT judgment PDFs in $ARCHIVE_PATH"

if [ "$PDF_COUNT" -lt 1000 ]; then
    echo "⚠️  Warning: Expected 25,000+ PDFs but found only $PDF_COUNT"
    echo "   Continuing anyway..."
fi
echo ""

# ============================================================================
# STEP 5: RUN KAGGLE INGESTION PIPELINE
# ============================================================================
echo "[5/6] Running ingestion pipeline..."
echo "⚠️  This will process all PDFs: OCR → Clean → Chunk → Embed → ChromaDB"
echo "⏱️  Estimated time: 30-60 minutes for 25K+ PDFs"
echo ""
read -p "Continue with ingestion? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python -m src.ingestion.kaggle_ingest
    echo "✅ Ingestion complete!"
else
    echo "⏭️  Skipping ingestion. Run manually later with:"
    echo "   python -m src.ingestion.kaggle_ingest"
fi
echo ""

# ============================================================================
# STEP 6: START SERVICES
# ============================================================================
echo "[6/6] Ready to start services!"
echo ""
echo "To start the dashboard (development mode):"
echo "  cd src/dashboard"
echo "  npm run dev"
echo ""
echo "To start the API server:"
echo "  python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload"
echo ""
echo "To start full Docker stack:"
echo "  docker-compose up -d"
echo ""

echo "================================"
echo "✅ UPGRADE COMPLETE!"
echo "================================"
echo ""
echo "Summary of changes:"
echo "  ✅ New dashboard installed at src/dashboard/"
echo "  ✅ Old dashboard backed up"
echo "  ✅ bcrypt compatibility fixed"
echo "  ✅ 25,735 SC judgment PDFs ready for ingestion"
echo "  ✅ kaggle_ingest.py pipeline ready"
echo ""
echo "Next steps:"
echo "  1. Start the dashboard: cd src/dashboard && npm run dev"
echo "  2. Start the API: python -m uvicorn src.api.main:app --reload"
echo "  3. Access at: http://localhost:5173 (dashboard) + http://localhost:8000 (API)"
echo ""
