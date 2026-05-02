"""
scheduler.py — Orchestrator Pipeline
Urutan eksekusi: Scrape → Simpan ke DB → Analisis & Scoring

Dijalankan oleh:
  1. Manual  : python scheduler.py
  2. GitHub Actions : otomatis setiap 6 jam (lihat .github/workflows/scrape.yml)
  3. APScheduler (lokal terus-menerus) : jalankan dengan --loop
"""

import sys
import logging
import argparse
from datetime import datetime

from scraper import run_all_scrapers
from database import init_db, save_articles
from analyzer import analyze_all

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def run_pipeline():
    """Satu siklus lengkap: scrape → simpan → analisis."""
    start = datetime.now()
    logger.info("=" * 55)
    logger.info(f"  Pipeline dimulai: {start.strftime('%d %B %Y %H:%M:%S')}")
    logger.info("=" * 55)

    # Step 1: Scraping
    logger.info("[1/3] Memulai scraping berita...")
    articles = run_all_scrapers()
    logger.info(f"      Total artikel ditemukan: {len(articles)}")

    if not articles:
        logger.warning("  Tidak ada artikel yang di-scrape. Cek koneksi & selector.")
        return

    # Step 2: Simpan ke database
    logger.info("[2/3] Menyimpan ke database...")
    saved = save_articles(articles)
    logger.info(f"      Artikel baru tersimpan: {saved}")

    # Step 3: Analisis & scoring
    logger.info("[3/3] Menjalankan analisis & scoring...")
    analyze_all()

    elapsed = (datetime.now() - start).seconds
    logger.info(f"  Pipeline selesai dalam {elapsed} detik.")
    logger.info("=" * 55)


def run_with_scheduler(interval_hours: int = 6):
    """Jalankan pipeline secara periodik menggunakan APScheduler."""
    try:
        from apscheduler.schedulers.blocking import BlockingScheduler
    except ImportError:
        logger.error("APScheduler tidak terinstall. Jalankan: pip install apscheduler")
        sys.exit(1)

    logger.info(f"Scheduler aktif — interval: {interval_hours} jam")
    run_pipeline()  # langsung jalankan sekali

    scheduler = BlockingScheduler(timezone="Asia/Jakarta")
    scheduler.add_job(run_pipeline, "interval", hours=interval_hours, id="mbg_pipeline")
    logger.info(f"Job berikutnya dijadwalkan setiap {interval_hours} jam.")

    try:
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("Scheduler dihentikan oleh pengguna.")
        scheduler.shutdown()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MBG Early Warning Pipeline")
    parser.add_argument(
        "--loop",
        action="store_true",
        help="Jalankan terus-menerus dengan APScheduler (default: sekali jalan)"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=6,
        help="Interval scraping dalam jam jika --loop aktif (default: 6)"
    )
    args = parser.parse_args()

    # Inisialisasi DB (hanya efektif di mode SQLite)
    init_db()

    if args.loop:
        run_with_scheduler(interval_hours=args.interval)
    else:
        run_pipeline()
