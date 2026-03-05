import os
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

from loguru import logger

try:
    import psutil  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    psutil = None  # type: ignore

from database.db import DatabaseManager
from services.ai_service import AIService
from services.email_service import EmailService
from engine import ScanEngine


@dataclass
class FullScanMetrics:
    profile_id: str
    ok: bool
    error: Optional[str]
    execution_time_sec: float
    listings_processed: int
    matches_count: int
    gemini_enabled: bool
    mem_rss_before_mb: float
    mem_rss_after_mb: float


def run_full_scan(profile: Dict[str, Any], enable_gemini: bool = True) -> FullScanMetrics:
    """
    Perform a full scan for a given profile (compatible with existing user dicts).

    Measures:
    - total execution time
    - memory RSS before/after
    - number of listings processed (raw_count from engine)
    - whether Gemini client was enabled
    """
    profile_id = profile.get("email") or profile.get("id") or "unknown"

    process = psutil.Process(os.getpid()) if psutil else None  # type: ignore
    rss_before = (process.memory_info().rss / (1024 * 1024)) if process else 0.0  # MB

    db = DatabaseManager()
    ai = AIService(enabled=enable_gemini)
    email_svc = EmailService()
    engine = ScanEngine(db=db, ai=ai, email=email_svc)

    start = time.perf_counter()
    error: Optional[str] = None
    raw_count = 0
    matches_count = 0
    try:
        logger.info(f"[perf] Starting full scan for profile {profile_id} (enable_gemini={enable_gemini})")
        result = engine.run_scan_for_user(profile)
        if isinstance(result, dict):
            raw_count = int(result.get("raw_count", 0))
            matches_count = int(result.get("matches_count", 0))
        ok = True
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception(f"[perf] Full scan failed for profile {profile_id}: {exc}")
        error = str(exc)
        ok = False
    finally:
        elapsed = time.perf_counter() - start

    rss_after = (process.memory_info().rss / (1024 * 1024)) if process else 0.0  # MB
    gemini_on = bool(ai.client)

    logger.info(
        f"[perf] Full scan for {profile_id} completed in {elapsed:.2f}s, "
        f"raw={raw_count}, matches={matches_count}, gemini_on={gemini_on}"
    )

    return FullScanMetrics(
        profile_id=str(profile_id),
        ok=ok,
        error=error,
        execution_time_sec=elapsed,
        listings_processed=raw_count,
        matches_count=matches_count,
        gemini_enabled=gemini_on,
        mem_rss_before_mb=rss_before,
        mem_rss_after_mb=rss_after,
    )

