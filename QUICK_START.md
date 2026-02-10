# Gujarat Police SLM - Quick Start Guide

## 🎯 Your Situation

You have:
- ✅ 25,735 SC judgment PDFs in `archive/supreme_court_judgments/`
- ✅ New upgraded dashboard in `dashboard/` folder
- ✅ Existing RAG system with Indian Kanoon scraper

## ⚡ Quick Start (Recommended - 30 minutes)

### Step 1: Fix bcrypt
```bash
pip install bcrypt==4.0.1 --break-system-packages
```

### Step 2: Install New Dashboard
```bash
cd "D:\projects\Ongoing\gujarat police\Implementation project\gujpol-slm-complete\gujpol-slm-complete"

# Backup old dashboard
move src\dashboard src\dashboard-old

# Install new dashboard
move dashboard src\dashboard
cd src\dashboard
npm install
cd ..\..
```

### Step 3: Start Everything

**Terminal 1 - Dashboard:**
```bash
cd src\dashboard
npm run dev
```

**Terminal 2 - API:**
```bash
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### Step 4: Access System
- 🌐 **Dashboard:** http://localhost:5173
- 📡 **API Docs:** http://localhost:8000/docs

---

## 📊 Data Options

### Option A: Use Existing Scraper (Recommended - Fast)
Your system already scrapes Indian Kanoon which has SC judgments:

```bash
python -m src.data_sources.orchestrator
```

### Option B: Process Archive PDFs (Complete but Slow)
Process your 25K PDFs with OCR (10-15 hours):

```bash
python -m src.ingestion.pdf_archive_ingest
```

---

## 🐳 Docker Deployment

```bash
docker-compose up -d
```

Services:
- Frontend: http://localhost:3000
- API: http://localhost:8000
- Grafana: http://localhost:3001

---

## 🔧 Troubleshooting

### bcrypt error
```bash
pip install bcrypt==4.0.1 --break-system-packages
```

### Port already in use
```bash
# Find and kill process on port 8000
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Dashboard won't start
```bash
cd src\dashboard
rm -rf node_modules package-lock.json
npm install
npm run dev
```

---

## 📁 Modified File Summary

### Created/Modified Files:
1. ✅ `UPGRADE_INSTRUCTIONS.md` - Complete upgrade guide
2. ✅ `QUICK_START.md` - This file
3. ✅ `upgrade_commands.sh` - Bash automation script
4. ✅ `upgrade_commands.bat` - Windows automation script
5. ✅ `src/ingestion/pdf_archive_ingest.py` - PDF processor for archive
6. ✅ `.gitignore` - Updated with comprehensive patterns

### Your Original Files:
- ✅ `archive/supreme_court_judgments/` - 25,735 PDFs (preserved)
- ✅ `dashboard/` - New upgraded UI (ready to move)
- ✅ `src/ingestion/kaggle_ingest.py` - CSV ingestion (kept)
- ✅ `UPGRADE_PLAN.md` - Your original plan (preserved)

---

## 🎨 What's New in Dashboard

- 🌑 **Dark theme** with Gujarat Police branding (navy + gold)
- 💎 **Glass morphism** UI with depth and blur effects
- 💬 **Chat-style** SOP Assistant (conversational UX)
- 📊 **Circular score charts** for chargesheet review
- 🎭 **Smooth animations** and micro-interactions
- 📱 **Responsive** mobile-first design

---

## ✅ Verification Checklist

After setup, verify:
- [ ] Dashboard loads at http://localhost:5173
- [ ] API docs load at http://localhost:8000/docs
- [ ] Can login to dashboard
- [ ] SOP Assistant responds to queries
- [ ] Search returns results
- [ ] Chargesheet review works

---

## 📞 Support

- Issues: Check `logs/` folder
- API health: http://localhost:8000/health
- Documentation: `UPGRADE_INSTRUCTIONS.md`

---

## 🚀 Next Steps

1. Start with Option A (scraper) for quick setup
2. Test all 3 features (SOP, Search, Chargesheet)
3. Later, optionally run Option B for complete archive
4. Deploy with Docker for production

**Total Setup Time: ~30 minutes** ⏱️
