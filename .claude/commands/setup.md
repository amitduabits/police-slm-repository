Set up the complete Gujarat Police SLM development environment:

1. Check Python 3.11+ is available, install if needed
2. Install poetry if not present, then run `poetry install`
3. Install system packages: tesseract-ocr tesseract-ocr-hin tesseract-ocr-guj poppler-utils
4. Create all required directories under data/, configs/, logs/, models/, backups/
5. Copy .env.example to .env if .env doesn't exist
6. Generate the IPC↔BNS, CrPC↔BNSS, IEA↔BSA section mapping JSON files in configs/
7. Initialize the PostgreSQL database by running docker-compose up db-postgres and applying docker/init-db.sql
8. Start ChromaDB and Redis via docker-compose
9. Run `python -m src.cli health` to verify everything works
10. Print a summary of what's ready and what needs manual configuration

If any step fails, log the error clearly and continue with the next step.
At the end, print "SETUP COMPLETE" with next steps.
