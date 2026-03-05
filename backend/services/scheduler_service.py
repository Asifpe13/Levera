import os
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger


class SchedulerService:
    def __init__(self):
        self.scheduler = BackgroundScheduler(timezone="Asia/Jerusalem")

    def add_scan_job(self, func, interval_minutes: int = None):
        """Schedule periodic property scanning."""
        interval = interval_minutes or int(os.getenv("SCAN_INTERVAL_MINUTES", "60"))
        self.scheduler.add_job(
            func,
            trigger=IntervalTrigger(minutes=interval),
            id="property_scan",
            replace_existing=True,
            name="Property Scanner",
        )
        logger.info(f"Scan job scheduled every {interval} minutes")

    def add_weekly_report_job(self, func):
        """Schedule weekly report for Thursday 21:00 Israel time."""
        self.scheduler.add_job(
            func,
            trigger=CronTrigger(day_of_week="thu", hour=21, minute=0),
            id="weekly_report",
            replace_existing=True,
            name="Weekly Report (Thursday 21:00)",
        )
        logger.info("Weekly report scheduled for Thursday 21:00")

    def start(self):
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler started")

    def stop(self):
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler stopped")

    def get_jobs(self) -> list[dict]:
        jobs = self.scheduler.get_jobs()
        return [
            {
                "id": job.id,
                "name": job.name,
                "next_run": str(job.next_run_time),
                "trigger": str(job.trigger),
            }
            for job in jobs
        ]
