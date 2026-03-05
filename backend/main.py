"""
Main entry point — starts the scheduler for background scanning and weekly reports.
Run with: python main.py
"""
import os
import signal
import sys
import time

from pathlib import Path
from dotenv import load_dotenv
from loguru import logger

_BACKEND = Path(__file__).resolve().parent
load_dotenv(_BACKEND.parent / ".env")  # repo root
load_dotenv(_BACKEND / ".env")

logger.remove()
logger.add(sys.stderr, level="INFO",
           format="<green>{time:HH:mm:ss}</green> | <level>{level:<8}</level> | {message}")

os.makedirs("data", exist_ok=True)
logger.add("data/agent.log", rotation="5 MB", retention="30 days", level="DEBUG")

from config import SCAN_INTERVAL_MINUTES
from database.db import DatabaseManager
from services.ai_service import AIService
from services.email_service import EmailService
from services.scheduler_service import SchedulerService
from engine import ScanEngine


def main():
    logger.info("=" * 60)
    logger.info("  Levera — Real Estate Agent is starting")
    logger.info("=" * 60)

    db = DatabaseManager()
    ai = AIService()
    email_svc = EmailService()
    engine = ScanEngine(db=db, ai=ai, email=email_svc)
    scheduler = SchedulerService()

    scheduler.add_scan_job(engine.run_scan_for_all_users, SCAN_INTERVAL_MINUTES)
    scheduler.add_weekly_report_job(engine.send_weekly_reports)
    scheduler.start()

    logger.info("Running initial scan...")
    engine.run_scan_for_all_users()

    logger.info("Agent is running. Press Ctrl+C to stop.")
    logger.info(f"Scan interval: every {SCAN_INTERVAL_MINUTES} minutes")
    logger.info("Weekly report: Thursday 21:00 (Israel time)")
    logger.info("Sources: Yad2, Madlan, Homeless, WinWin")

    for job in scheduler.get_jobs():
        logger.info(f"  Job: {job['name']} | Next run: {job['next_run']}")

    def shutdown(sig, frame):
        logger.info("Shutting down...")
        scheduler.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    while True:
        time.sleep(60)


if __name__ == "__main__":
    main()
