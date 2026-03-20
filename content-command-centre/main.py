"""
main.py — ScoringZone Golf Content Research Engine

Usage:
  python3 main.py                            # Run one cycle (auto cycle number)
  python3 main.py --single                   # Same as above (used by dashboard)
  python3 main.py --cycle-num 5              # Specify cycle number
  python3 main.py --keywords "chip,putt"     # Override seed keywords
  python3 main.py --top-n 3                  # Generate packages for top 3 topics
  python3 main.py --no-trends                # Skip Google Trends (faster)
  python3 main.py --dry-run                  # Research only, no packages
  python3 main.py --force-analyse            # Force performance analysis run
"""
from __future__ import annotations
import argparse, json, logging, os, sqlite3, sys, time
from datetime import datetime
from pathlib import Path

# ── Set up path so modules import correctly wherever this is called from ──────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from researcher import run_research, SEED_KEYWORDS, ContentOpportunity
from scorer import score_and_rank
from packager import build_all
from performance_analyser import run_analysis, MIN_DATA_POINTS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("main")


def _count_posts_with_metrics() -> int:
    """Return the number of posted packages that have engagement metrics."""
    db_path = os.path.join(config.BASE_DIR, "post_status.db")
    if not os.path.exists(db_path):
        return 0
    try:
        db = sqlite3.connect(db_path)
        row = db.execute(
            "SELECT COUNT(*) FROM post_status WHERE status='posted' AND engagement_score IS NOT NULL"
        ).fetchone()
        db.close()
        return row[0] if row else 0
    except Exception:
        return 0


def _next_cycle_number(packages_dir: str) -> int:
    """Auto-detect next cycle number from existing package folders."""
    if not os.path.isdir(packages_dir):
        return 1
    nums = []
    for name in os.listdir(packages_dir):
        if name.startswith("cycle_"):
            try:
                nums.append(int(name.split("_")[1]))
            except (IndexError, ValueError):
                pass
    return max(nums) + 1 if nums else 1


def _save_raw(opportunities: list[ContentOpportunity], cycle_num: int):
    """Save raw research data to history/ for auditing."""
    history_dir = os.path.join(config.BASE_DIR, "history")
    os.makedirs(history_dir, exist_ok=True)
    path = os.path.join(history_dir, f"cycle_{cycle_num:04d}_raw.json")
    data = [
        {
            "keyword":          o.keyword,
            "topic":            o.topic,
            "youtube_views":    o.youtube_views,
            "youtube_likes":    o.youtube_likes,
            "video_count":      o.video_count,
            "trend_score":      o.trend_score,
            "trend_direction":  o.trend_direction,
            "opportunity_score": o.opportunity_score,
            "top_video_title":  o.top_video_title,
            "top_video_id":     o.top_video_id,
            "top_channel":      o.top_channel,
            "search_date":      o.search_date,
        }
        for o in opportunities
    ]
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    logger.info(f"Raw data saved → {path}")


def run_cycle(
    cycle_num: int,
    keywords: list[str] | None = None,
    top_n: int = 5,
    use_trends: bool = True,
    dry_run: bool = False,
) -> list[str]:
    """
    Run a full research → score → package cycle.
    Returns list of package folder paths created.
    """
    started = datetime.utcnow()

    print(f"""
╔══════════════════════════════════════════════════════╗
║   SCORING ZONE — Research Engine  (Cycle #{cycle_num:04d})    ║
╚══════════════════════════════════════════════════════╝
""")

    api_key = os.getenv("YOUTUBE_API_KEY", "")
    if not api_key:
        logger.error("YOUTUBE_API_KEY not set in .env — aborting.")
        sys.exit(1)

    kws = keywords or SEED_KEYWORDS
    logger.info(f"Keywords : {len(kws)}")
    logger.info(f"Trends   : {'on' if use_trends else 'off'}")
    logger.info(f"Top N    : {top_n}")
    logger.info(f"Packages : {config.PACKAGES_DIR}")
    print()

    # ── 1. Research ────────────────────────────────────────────────────────────
    logger.info("── Phase 1: Research ──────────────────────────────────────")
    opportunities = run_research(
        youtube_api_key=api_key,
        keywords=kws,
        max_yt_results=10,
        use_trends=use_trends,
    )
    logger.info(f"Collected {len(opportunities)} opportunities")
    print()

    # ── 2. Score & rank ────────────────────────────────────────────────────────
    logger.info("── Phase 2: Score & Rank ──────────────────────────────────")
    top_opps = score_and_rank(opportunities, top_n=top_n)
    _save_raw(opportunities, cycle_num)
    print()

    if dry_run:
        logger.info("Dry run — skipping package generation.")
        return []

    # ── 3. Package ─────────────────────────────────────────────────────────────
    logger.info("── Phase 3: Build Packages ────────────────────────────────")
    folders = build_all(
        opportunities=top_opps,
        packages_dir=config.PACKAGES_DIR,
        cycle_number=cycle_num,
    )
    print()

    # ── Summary ────────────────────────────────────────────────────────────────
    elapsed = (datetime.utcnow() - started).total_seconds()
    logger.info("── Cycle Complete ─────────────────────────────────────────")
    logger.info(f"  Packages built : {len(folders)}")
    logger.info(f"  Time elapsed   : {elapsed:.0f}s")
    logger.info(f"  Packages dir   : {config.PACKAGES_DIR}")
    print()
    for i, (opp, folder) in enumerate(zip(top_opps, folders), 1):
        print(f"  #{i}  {opp.opportunity_score:5.1f}  {opp.trend_direction:7s}  {opp.keyword}")
    print()
    print("  Open the dashboard to review → http://localhost:5050")
    print()

    # ── Learning update ────────────────────────────────────────────────────────
    n_with_metrics = _count_posts_with_metrics()
    if n_with_metrics >= MIN_DATA_POINTS:
        logger.info(f"── Learning Update (n={n_with_metrics} posts with metrics) ──────────")
        updated = run_analysis()
        if updated:
            logger.info(f"[main] Learning updated — cycle {cycle_num}, n={n_with_metrics}")
        print()
    else:
        logger.info(f"[main] Learning not yet active ({n_with_metrics}/{MIN_DATA_POINTS} posts with metrics)")

    return folders


def main():
    parser = argparse.ArgumentParser(description="ScoringZone Research Engine")
    parser.add_argument("--single",      action="store_true", help="Run one cycle (default)")
    parser.add_argument("--cycle-num",   type=int, default=None, help="Cycle number (auto-detected if omitted)")
    parser.add_argument("--keywords",    type=str, default=None, help="Comma-separated keyword overrides")
    parser.add_argument("--top-n",       type=int, default=5,    help="Number of packages to generate (default 5)")
    parser.add_argument("--no-trends",   action="store_true",    help="Skip Google Trends (faster)")
    parser.add_argument("--dry-run",       action="store_true",    help="Research only, no packages")
    parser.add_argument("--force-analyse", action="store_true",    help="Force performance analysis regardless of threshold")
    args = parser.parse_args()

    if args.force_analyse:
        logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
        logger.info("── Forced performance analysis ─────────────────────────")
        run_analysis()
        return

    cycle_num = args.cycle_num
    if cycle_num is None:
        cycle_num = _next_cycle_number(config.PACKAGES_DIR)

    keywords = None
    if args.keywords:
        keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]

    run_cycle(
        cycle_num=cycle_num,
        keywords=keywords,
        top_n=args.top_n,
        use_trends=not args.no_trends,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
