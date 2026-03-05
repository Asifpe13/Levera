"""
Load test script for the real estate scanning backend.

Simulates multiple profiles running full scans concurrently and measures:
- total runtime
- per-scan timing stats
- CPU and RAM usage during the run
- impact of enabling/disabling Gemini (LLM)

Usage (from backend directory):
  python load_test.py --profiles 150 --workers 20 --enable-gemini true
"""
import argparse
import asyncio
import os
import random
import statistics
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional, Tuple

try:
    import psutil  # type: ignore
except ImportError:  # pragma: no cover - optional
    psutil = None  # type: ignore

from loguru import logger

from config import ALL_CITIES
from perf_full_scan import run_full_scan, FullScanMetrics


def _make_fake_profile(i: int) -> Dict[str, Any]:
    """Create a realistic fake user profile shaped like a user document."""
    email = f"loadtest_user_{i}@example.com"
    name = f"LoadTest User {i}"
    cities = random.sample(ALL_CITIES, k=min(3, len(ALL_CITIES)))
    search_type = random.choice(["buy", "rent", "both"])

    monthly_income = random.randint(10_000, 35_000)
    equity = random.randint(200_000, 1_000_000)
    max_repayment_ratio = random.choice([0.30, 0.33, 0.35])
    max_price = random.choice([1_200_000, 1_800_000, 2_500_000, 3_000_000])
    max_rent = random.choice([4_000, 6_000, 8_500])

    return {
        "email": email,
        "name": name,
        "target_cities": cities,
        "search_type": search_type,
        "equity": equity,
        "monthly_income": monthly_income,
        "room_range_min": 2,
        "room_range_max": 5,
        "max_price": max_price,
        "max_repayment_ratio": max_repayment_ratio,
        "rent_room_range_min": 2,
        "rent_room_range_max": 4,
        "max_rent": max_rent,
        "extra_preferences": None,
        "is_active": True,
    }


async def _monitor_resources(stop_event: asyncio.Event) -> Tuple[float, float, float]:
    """
    Monitor CPU and RAM usage while load test is running.
    Returns (cpu_peak, ram_peak_mb, cpu_over_threshold_seconds).
    """
    if not psutil:
        logger.warning("psutil not installed — resource monitoring disabled")
        return 0.0, 0.0, 0.0

    process = psutil.Process(os.getpid())  # type: ignore
    cpu_peak = 0.0
    ram_peak_mb = 0.0
    cpu_over_threshold_seconds = 0.0
    threshold = 85.0

    # Prime cpu_percent to get a baseline
    psutil.cpu_percent(interval=None)  # type: ignore

    last_check = time.time()
    while not stop_event.is_set():
        await asyncio.sleep(1.0)
        now = time.time()
        dt = now - last_check
        last_check = now

        cpu = psutil.cpu_percent(interval=None)  # type: ignore
        mem = process.memory_info().rss / (1024 * 1024)
        cpu_peak = max(cpu_peak, cpu)
        ram_peak_mb = max(ram_peak_mb, mem)
        if cpu > threshold:
            cpu_over_threshold_seconds += dt

    return cpu_peak, ram_peak_mb, cpu_over_threshold_seconds


async def _run_load_once(
    profiles: List[Dict[str, Any]],
    max_workers: int,
    enable_gemini: bool,
) -> Dict[str, Any]:
    """
    Run load test once (either with Gemini enabled or disabled).
    Returns a dict with aggregated stats.
    """
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    # Use thread pool so we don't block the event loop; run_full_scan is synchronous.
    executor = ThreadPoolExecutor(max_workers=max_workers)

    async def run_profile(profile: Dict[str, Any]) -> FullScanMetrics:
        return await loop.run_in_executor(
            executor,
            lambda: run_full_scan(profile, enable_gemini=enable_gemini),
        )

    monitor_task = asyncio.create_task(_monitor_resources(stop_event))

    started_at = time.perf_counter()
    results: List[FullScanMetrics] = []

    try:
        tasks = [asyncio.create_task(run_profile(p)) for p in profiles]
        for coro in asyncio.as_completed(tasks):
            metrics = await coro
            results.append(metrics)
    finally:
        total_duration = time.perf_counter() - started_at
        stop_event.set()
        cpu_peak, ram_peak_mb, cpu_over_thr = await monitor_task
        executor.shutdown(wait=True)

    exec_times = [r.execution_time_sec for r in results]
    failures = [r for r in results if not r.ok]

    avg_time = statistics.mean(exec_times) if exec_times else 0.0
    max_time = max(exec_times) if exec_times else 0.0

    return {
        "profiles": len(profiles),
        "duration": total_duration,
        "avg_time": avg_time,
        "max_time": max_time,
        "failures": len(failures),
        "cpu_peak": cpu_peak,
        "ram_peak_mb": ram_peak_mb,
        "cpu_over_threshold_seconds": cpu_over_thr,
        "gemini_enabled": enable_gemini,
    }


def _stability_tag(cpu_peak: float, cpu_over_thr_sec: float, failures: int) -> str:
    if failures > 0 or cpu_over_thr_sec > 10:
        return "Overloaded"
    if cpu_peak > 85:
        return "Needs Queue"
    return "Stable"


def _print_report(title: str, stats: Dict[str, Any]) -> None:
    print("====================")
    print("LOAD TEST REPORT")
    print(title)
    print()
    print(f"Total profiles simulated: {stats['profiles']}")
    print(f"Total duration: {stats['duration']:.2f} seconds")
    print(f"Average scan time: {stats['avg_time']:.2f} sec")
    print(f"Max scan time: {stats['max_time']:.2f} sec")
    print(f"CPU peak: {stats['cpu_peak']:.1f}%")
    print(f"RAM peak: {stats['ram_peak_mb']:.1f} MB")
    print(f"Failures: {stats['failures']}")
    print(f"Gemini enabled: {'Yes' if stats['gemini_enabled'] else 'No'}")
    print(f"System stability: {_stability_tag(stats['cpu_peak'], stats['cpu_over_threshold_seconds'], stats['failures'])}")

    print()


async def main_async(args: argparse.Namespace) -> None:
    random.seed(42)
    profiles = [_make_fake_profile(i) for i in range(args.profiles)]

    # First run: Gemini as per flag
    stats1 = await _run_load_once(
        profiles=profiles,
        max_workers=args.workers,
        enable_gemini=args.enable_gemini,
    )
    _print_report("Run 1", stats1)

    # Second run: opposite Gemini flag to compare impact
    stats2 = await _run_load_once(
        profiles=profiles,
        max_workers=args.workers,
        enable_gemini=not args.enable_gemini,
    )
    _print_report("Run 2 (Gemini toggled)", stats2)

    # Simple comparison summary
    diff_runtime = stats1["duration"] - stats2["duration"]
    diff_cpu = stats1["cpu_peak"] - stats2["cpu_peak"]
    diff_fail = stats1["failures"] - stats2["failures"]
    print("Comparison (Run1 - Run2):")
    print(f"Runtime difference: {diff_runtime:.2f} sec")
    print(f"CPU peak difference: {diff_cpu:.1f}%")
    print(f"Failure count difference: {diff_fail}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Load test for real estate scanning backend")
    parser.add_argument("--profiles", type=int, default=150, help="Number of simulated profiles")
    parser.add_argument("--workers", type=int, default=20, help="Max concurrent worker threads")
    parser.add_argument(
        "--enable-gemini",
        type=lambda v: str(v).lower() in ("1", "true", "yes", "y"),
        default=True,
        help="Enable Gemini calls for first run (second run automatically toggles)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()

