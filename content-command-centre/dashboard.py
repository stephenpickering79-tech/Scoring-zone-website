"""
dashboard.py — ScoringZone Content Command Centre

A local web server that provides:
  - Visual review of all generated content packages
  - Approve / reject / edit captions before posting
  - One-click post to Instagram and X
  - Trigger new research cycles
  - View cycle history and scores

Run with:
  python3 dashboard.py

Then open http://localhost:5050 in your browser.
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import subprocess
import sys
import threading
import time as time_module
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from flask import Flask, jsonify, request, send_file, send_from_directory, abort

import config
from poster import InstagramPoster, XPoster, FacebookPoster

# ─────────────────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s — %(message)s")
logger = logging.getLogger("dashboard")

app = Flask(__name__, static_folder=None)

PACKAGES_DIR = config.PACKAGES_DIR
DB_PATH      = os.path.join(config.BASE_DIR, "post_status.db")

instagram      = InstagramPoster()
x_poster       = XPoster()
facebook_poster = FacebookPoster()

# ─────────────────────────────────────────────────────────────────────────────
# Database
# ─────────────────────────────────────────────────────────────────────────────

def get_db():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    # Use in-memory journaling so SQLite doesn't need to create
    # a -journal sidecar file (the mount filesystem may not allow it)
    db.execute("PRAGMA journal_mode=MEMORY")
    return db


def init_db():
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS post_status (
                package_id          TEXT PRIMARY KEY,
                status              TEXT DEFAULT 'pending',
                caption_instagram   TEXT,
                caption_x           TEXT,
                caption_facebook    TEXT,
                instagram_post_id   TEXT,
                x_post_id           TEXT,
                facebook_post_id    TEXT,
                approved_at         TEXT,
                posted_instagram_at TEXT,
                posted_x_at         TEXT,
                posted_facebook_at  TEXT,
                notes               TEXT
            )
        """)
        # Migrate existing tables — add new columns if missing
        for col, definition in [
            ("caption_facebook",   "TEXT"),
            ("facebook_post_id",   "TEXT"),
            ("posted_facebook_at", "TEXT"),
            ("scheduled_for",      "TEXT"),   # ISO UTC timestamp when to auto-post
            ("schedule_status",    "TEXT"),   # NULL | 'scheduled' | 'posting' | 'posted' | 'failed'
            ("schedule_error",     "TEXT"),   # Last scheduler error message
        ]:
            try:
                db.execute(f"ALTER TABLE post_status ADD COLUMN {col} {definition}")
            except Exception:
                pass  # Column already exists
        db.execute("""
            CREATE TABLE IF NOT EXISTS cycle_runs (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                started_at  TEXT,
                finished_at TEXT,
                status      TEXT DEFAULT 'running',
                cycle_num   INTEGER,
                top_topic   TEXT,
                top_score   REAL,
                log_tail    TEXT
            )
        """)
        db.commit()


# ─────────────────────────────────────────────────────────────────────────────
# Scheduler helpers  (UAE = UTC+4)
# ─────────────────────────────────────────────────────────────────────────────

UAE_TZ = ZoneInfo("Asia/Dubai")   # UTC+4, no DST

# Optimal posting windows in UAE local time (hour, minute)
OPTIMAL_SLOTS = [
    (7,   0),   # 7:00 AM  — Early morning golfers / commute
    (12, 30),   # 12:30 PM — Lunchtime scroll
    (20,  0),   # 8:00 PM  — Prime evening social browsing
]
MIN_ADVANCE_MINUTES = 10   # Don't schedule anything sooner than this


def get_next_slot(after_utc: datetime | None = None) -> datetime:
    """Return the next optimal UAE posting slot as a UTC-aware datetime.

    Scans OPTIMAL_SLOTS for today and tomorrow (UAE time) and returns the
    first slot that is at least MIN_ADVANCE_MINUTES in the future and not
    already taken by another scheduled post.
    """
    if after_utc is None:
        after_utc = datetime.now(timezone.utc)

    now_uae  = after_utc.astimezone(UAE_TZ)
    min_time = after_utc + timedelta(minutes=MIN_ADVANCE_MINUTES)

    # Collect already-taken slots from DB (within next 48 h)
    taken: set[str] = set()
    with get_db() as db:
        rows = db.execute(
            "SELECT scheduled_for FROM post_status "
            "WHERE schedule_status = 'scheduled' AND scheduled_for IS NOT NULL"
        ).fetchall()
        taken = {r["scheduled_for"] for r in rows}

    # Try slots over the next 3 days
    for day_offset in range(3):
        candidate_date = (now_uae + timedelta(days=day_offset)).date()
        for hour, minute in OPTIMAL_SLOTS:
            slot_uae = datetime(
                candidate_date.year, candidate_date.month, candidate_date.day,
                hour, minute, 0, tzinfo=UAE_TZ,
            )
            slot_utc = slot_uae.astimezone(timezone.utc)
            if slot_utc <= min_time:
                continue
            # Check not already taken (compare ISO strings, truncate to minute)
            slot_key = slot_utc.strftime("%Y-%m-%dT%H:%M")
            if any(t.startswith(slot_key) for t in taken):
                continue
            return slot_utc

    # Fallback: 8 PM UAE tomorrow + 1 day
    fallback_uae = now_uae.replace(hour=20, minute=0, second=0, microsecond=0) + timedelta(days=3)
    return fallback_uae.astimezone(timezone.utc)


def _slot_display(scheduled_for: str | None) -> str | None:
    """Convert a UTC ISO string to a UAE-friendly display string."""
    if not scheduled_for:
        return None
    try:
        slot_uae = datetime.fromisoformat(scheduled_for).astimezone(UAE_TZ)
        return slot_uae.strftime("%a %d %b · %I:%M %p UAE")
    except Exception:
        return scheduled_for


def assign_schedule(package_id: str) -> str:
    """Pick the next optimal slot for a package and write it to the DB.
    Returns the ISO UTC string of the scheduled time.
    """
    slot_utc = get_next_slot()
    slot_iso = slot_utc.isoformat()
    with get_db() as db:
        db.execute(
            "UPDATE post_status SET scheduled_for = ?, schedule_status = 'scheduled' WHERE package_id = ?",
            (slot_iso, package_id),
        )
        db.commit()
    logger.info(f"  Scheduled {package_id} for {slot_iso} UTC")
    return slot_iso


# ─────────────────────────────────────────────────────────────────────────────
# Background auto-poster
# ─────────────────────────────────────────────────────────────────────────────

def _post_package_to_all(package_id: str):
    """Post an approved package to Instagram, Facebook, and X.
    Called by the scheduler thread. Updates DB with results.
    """
    packages = scan_packages()
    pkg = next((p for p in packages if p["id"] == package_id), None)
    if not pkg:
        logger.error(f"Scheduler: package {package_id} not found")
        return

    status = get_package_status(package_id)
    errors = []

    # ── Instagram ──────────────────────────────────────
    portrait = next((i for i in pkg["images"] if "portrait" in i), None)
    square   = next((i for i in pkg["images"] if "square" in i), None)
    ig_img   = portrait or square or (pkg["images"][0] if pkg["images"] else None)

    if ig_img and instagram.is_configured() and not status.get("posted_instagram_at"):
        ig_result = instagram.post(
            os.path.join(pkg["folder"], ig_img),
            status.get("caption_instagram") or pkg["ig_caption"],
        )
        if ig_result["success"]:
            with get_db() as db:
                db.execute(
                    "UPDATE post_status SET instagram_post_id=?, posted_instagram_at=? WHERE package_id=?",
                    (ig_result["post_id"], datetime.utcnow().isoformat(), package_id),
                )
                db.commit()
            logger.info(f"  Scheduled post: Instagram OK ({ig_result['post_id']})")
        else:
            errors.append(f"IG: {ig_result['error']}")
            logger.error(f"  Scheduled post: Instagram FAILED — {ig_result['error']}")

    # ── Facebook ──────────────────────────────────────
    fb_img = square or portrait or (pkg["images"][0] if pkg["images"] else None)

    if fb_img and facebook_poster.is_configured() and not status.get("posted_facebook_at"):
        fb_result = facebook_poster.post(
            os.path.join(pkg["folder"], fb_img),
            status.get("caption_facebook") or status.get("caption_instagram") or pkg["ig_caption"],
        )
        if fb_result["success"]:
            with get_db() as db:
                db.execute(
                    "UPDATE post_status SET facebook_post_id=?, posted_facebook_at=? WHERE package_id=?",
                    (fb_result["post_id"], datetime.utcnow().isoformat(), package_id),
                )
                db.commit()
            logger.info(f"  Scheduled post: Facebook OK ({fb_result['post_id']})")
        else:
            errors.append(f"FB: {fb_result['error']}")
            logger.error(f"  Scheduled post: Facebook FAILED — {fb_result['error']}")

    # ── X / Twitter ────────────────────────────────────
    x_landscape = next((i for i in pkg["images"] if "x_landscape" in i), None)
    x_img = x_landscape or (pkg["images"][0] if pkg["images"] else None)

    if x_img and x_poster.is_configured() and not status.get("posted_x_at"):
        x_result = x_poster.post(
            os.path.join(pkg["folder"], x_img),
            status.get("caption_x") or pkg["x_caption"],
        )
        if x_result["success"]:
            with get_db() as db:
                db.execute(
                    "UPDATE post_status SET x_post_id=?, posted_x_at=? WHERE package_id=?",
                    (x_result["post_id"], datetime.utcnow().isoformat(), package_id),
                )
                db.commit()
            logger.info(f"  Scheduled post: X OK ({x_result['post_id']})")
        else:
            errors.append(f"X: {x_result['error']}")
            logger.error(f"  Scheduled post: X FAILED — {x_result['error']}")

    # ── Finalise ───────────────────────────────────────
    final_status   = "posted"
    schedule_status = "posted"
    error_msg      = "; ".join(errors) if errors else None

    if errors and not any([
        status.get("posted_instagram_at"), status.get("posted_facebook_at"), status.get("posted_x_at"),
    ]):
        # All platforms failed
        final_status    = "approved"   # Keep as approved so user can retry
        schedule_status = "failed"

    with get_db() as db:
        db.execute(
            "UPDATE post_status SET status=?, schedule_status=?, schedule_error=? WHERE package_id=?",
            (final_status, schedule_status, error_msg, package_id),
        )
        db.commit()
    logger.info(f"  Scheduled post complete: {package_id} → {final_status}")


def _scheduler_loop():
    """Background thread: fire scheduled posts when their time arrives."""
    logger.info("Scheduler thread started (UAE UTC+4 optimal slots)")
    while True:
        try:
            now_utc = datetime.now(timezone.utc)
            with get_db() as db:
                due = db.execute(
                    """SELECT package_id FROM post_status
                       WHERE schedule_status = 'scheduled'
                         AND scheduled_for IS NOT NULL
                         AND scheduled_for <= ?""",
                    (now_utc.isoformat(),),
                ).fetchall()

            for row in due:
                pkg_id = row["package_id"]
                logger.info(f"Scheduler: firing post for {pkg_id}")
                # Mark as 'posting' to prevent double-fire
                with get_db() as db:
                    db.execute(
                        "UPDATE post_status SET schedule_status='posting' WHERE package_id=?",
                        (pkg_id,),
                    )
                    db.commit()
                # Post in a separate thread to avoid blocking the loop
                threading.Thread(
                    target=_post_package_to_all,
                    args=(pkg_id,),
                    daemon=True,
                    name=f"auto-post-{pkg_id}",
                ).start()

        except Exception as exc:
            logger.error(f"Scheduler loop error: {exc}")

        time_module.sleep(30)   # Poll every 30 seconds


# Scheduler thread is started after init_db() in the __main__ block below
_scheduler_thread = threading.Thread(
    target=_scheduler_loop, daemon=True, name="scheduler"
)


# ─────────────────────────────────────────────────────────────────────────────
# Package helpers
# ─────────────────────────────────────────────────────────────────────────────

def scan_packages() -> list[dict]:
    """Scan the packages directory and return all package metadata."""
    packages = []
    if not os.path.isdir(PACKAGES_DIR):
        return packages

    for folder_name in sorted(os.listdir(PACKAGES_DIR)):
        folder = os.path.join(PACKAGES_DIR, folder_name)
        if not os.path.isdir(folder):
            continue

        manifest_path = os.path.join(folder, "manifest.json")
        manifest = {}
        if os.path.exists(manifest_path):
            try:
                with open(manifest_path) as f:
                    manifest = json.load(f)
            except Exception:
                pass

        # Read captions
        ig_caption_path = os.path.join(folder, "caption_instagram.txt")
        x_caption_path  = os.path.join(folder, "caption_x.txt")
        ig_caption = open(ig_caption_path).read().strip() if os.path.exists(ig_caption_path) else ""
        x_caption  = open(x_caption_path).read().strip()  if os.path.exists(x_caption_path)  else ""

        # Find images and videos
        images = sorted([
            f for f in os.listdir(folder)
            if f.endswith((".jpg", ".jpeg", ".png")) and not f.startswith(".")
        ])
        videos = sorted([
            f for f in os.listdir(folder)
            if f.endswith(".mp4") and not f.startswith(".")
        ])

        # Score from manifest
        score = manifest.get("opportunity_score", 0)
        topic = manifest.get("topic", folder_name.replace("_", " ").title())
        trend = manifest.get("trend_direction", "")

        packages.append({
            "id":               folder_name,
            "topic":            topic,
            "score":            score,
            "trend":            trend,
            "folder":           folder,
            "images":           images,
            "videos":           videos,
            "ig_caption":       ig_caption,
            "x_caption":        x_caption,
            "created_at":       manifest.get("created_at", ""),
            "cycle":            manifest.get("cycle_number", ""),
        })

    return packages


def get_package_status(package_id: str) -> dict:
    """Get the post status record for a package, creating it if needed."""
    with get_db() as db:
        row = db.execute(
            "SELECT * FROM post_status WHERE package_id = ?", (package_id,)
        ).fetchone()

        if row is None:
            # Seed with captions from files
            pkg = next((p for p in scan_packages() if p["id"] == package_id), None)
            ig_cap = pkg["ig_caption"] if pkg else ""
            x_cap  = pkg["x_caption"]  if pkg else ""
            db.execute(
                "INSERT INTO post_status (package_id, status, caption_instagram, caption_x, caption_facebook) VALUES (?, 'pending', ?, ?, ?)",
                (package_id, ig_cap, x_cap, ig_cap),  # Facebook defaults to same caption as Instagram
            )
            db.commit()
            row = db.execute(
                "SELECT * FROM post_status WHERE package_id = ?", (package_id,)
            ).fetchone()

        return dict(row)


# ─────────────────────────────────────────────────────────────────────────────
# API Routes
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_file(os.path.join(config.BASE_DIR, "dashboard.html"))


@app.route("/api/status")
def api_status():
    packages = scan_packages()
    statuses = {p["id"]: get_package_status(p["id"]) for p in packages}
    pending  = sum(1 for s in statuses.values() if s["status"] == "pending")
    approved = sum(1 for s in statuses.values() if s["status"] == "approved")
    posted   = sum(1 for s in statuses.values() if s["status"] == "posted")

    with get_db() as db:
        last_cycle = db.execute(
            "SELECT * FROM cycle_runs ORDER BY id DESC LIMIT 1"
        ).fetchone()
        last_cycle = dict(last_cycle) if last_cycle else None

    return jsonify({
        "total_packages":  len(packages),
        "pending":         pending,
        "approved":        approved,
        "posted":          posted,
        "last_cycle":      last_cycle,
        "instagram_ready": instagram.is_configured(),
        "x_ready":         x_poster.is_configured(),
        "facebook_ready":  facebook_poster.is_configured(),
    })


@app.route("/api/packages")
def api_packages():
    packages = scan_packages()
    result = []
    for pkg in packages:
        status = get_package_status(pkg["id"])
        # Merge status into package
        pkg["status"]              = status["status"]
        pkg["caption_instagram"]   = status["caption_instagram"] or pkg["ig_caption"]
        pkg["caption_x"]           = status["caption_x"]         or pkg["x_caption"]
        pkg["caption_facebook"]    = status.get("caption_facebook") or pkg["ig_caption"]
        pkg["instagram_post_id"]   = status["instagram_post_id"]
        pkg["x_post_id"]           = status["x_post_id"]
        pkg["facebook_post_id"]    = status.get("facebook_post_id")
        pkg["approved_at"]         = status["approved_at"]
        pkg["posted_instagram_at"] = status["posted_instagram_at"]
        pkg["posted_x_at"]         = status["posted_x_at"]
        pkg["posted_facebook_at"]  = status.get("posted_facebook_at")
        pkg["scheduled_for"]       = status.get("scheduled_for")
        pkg["schedule_status"]     = status.get("schedule_status")
        pkg["schedule_error"]      = status.get("schedule_error")
        # Generate UAE display string for scheduled time
        if pkg["scheduled_for"]:
            try:
                slot_uae = datetime.fromisoformat(pkg["scheduled_for"]).astimezone(UAE_TZ)
                pkg["slot_display"] = slot_uae.strftime("%a %d %b · %I:%M %p UAE")
            except Exception:
                pkg["slot_display"] = pkg["scheduled_for"]
        else:
            pkg["slot_display"] = None
        # Don't send full captions in list view (bandwidth)
        pkg["ig_caption"] = pkg["caption_instagram"][:120] + "..." if len(pkg["caption_instagram"]) > 120 else pkg["caption_instagram"]
        result.append(pkg)
    return jsonify(result)


@app.route("/api/packages/<package_id>")
def api_package_detail(package_id):
    packages = scan_packages()
    pkg = next((p for p in packages if p["id"] == package_id), None)
    if not pkg:
        abort(404)
    status = get_package_status(package_id)

    # Read full posting instructions
    instructions_path = os.path.join(pkg["folder"], "posting_instructions.txt")
    instructions = open(instructions_path).read() if os.path.exists(instructions_path) else ""

    brief_path = os.path.join(pkg["folder"], "brief_summary.md")
    brief = open(brief_path).read() if os.path.exists(brief_path) else ""

    pkg.update({
        "status":              status["status"],
        "caption_instagram":   status["caption_instagram"] or pkg["ig_caption"],
        "caption_x":           status["caption_x"]         or pkg["x_caption"],
        "caption_facebook":    status.get("caption_facebook") or pkg["ig_caption"],
        "instagram_post_id":   status["instagram_post_id"],
        "x_post_id":           status["x_post_id"],
        "facebook_post_id":    status.get("facebook_post_id"),
        "approved_at":         status["approved_at"],
        "posted_instagram_at": status["posted_instagram_at"],
        "posted_x_at":         status["posted_x_at"],
        "posted_facebook_at":  status.get("posted_facebook_at"),
        "scheduled_for":       status.get("scheduled_for"),
        "schedule_status":     status.get("schedule_status"),
        "schedule_error":      status.get("schedule_error"),
        "slot_display":        _slot_display(status.get("scheduled_for")),
        "posting_instructions": instructions,
        "brief":               brief[:2000],  # First 2000 chars
    })
    return jsonify(pkg)


@app.route("/api/packages/<package_id>/image/<filename>")
def api_package_image(package_id, filename):
    packages = scan_packages()
    pkg = next((p for p in packages if p["id"] == package_id), None)
    if not pkg:
        abort(404)
    return send_from_directory(pkg["folder"], filename)


@app.route("/api/packages/<package_id>/approve", methods=["POST"])
def api_approve(package_id):
    data = request.get_json() or {}
    ig_caption = data.get("caption_instagram", "")
    x_caption  = data.get("caption_x", "")
    fb_caption = data.get("caption_facebook", "")

    should_schedule = data.get("schedule", True)   # Pass schedule=false to approve without scheduling

    with get_db() as db:
        # Ensure row exists
        get_package_status(package_id)
        db.execute("""
            UPDATE post_status
            SET status = 'approved',
                caption_instagram = ?,
                caption_x = ?,
                caption_facebook = ?,
                approved_at = ?
            WHERE package_id = ?
        """, (ig_caption, x_caption, fb_caption, datetime.utcnow().isoformat(), package_id))
        db.commit()

    if not should_schedule:
        return jsonify({"success": True, "status": "approved"})

    # Auto-assign next optimal UAE posting slot
    scheduled_for = assign_schedule(package_id)

    # Convert to UAE-friendly display string
    slot_dt_uae = datetime.fromisoformat(scheduled_for).astimezone(UAE_TZ)
    slot_display = slot_dt_uae.strftime("%a %d %b · %I:%M %p UAE")

    return jsonify({"success": True, "status": "approved", "scheduled_for": scheduled_for, "slot_display": slot_display})


@app.route("/api/packages/<package_id>/reject", methods=["POST"])
def api_reject(package_id):
    with get_db() as db:
        get_package_status(package_id)
        db.execute(
            "UPDATE post_status SET status = 'rejected' WHERE package_id = ?",
            (package_id,)
        )
        db.commit()
    return jsonify({"success": True, "status": "rejected"})


@app.route("/api/packages/<package_id>/caption", methods=["PUT"])
def api_update_caption(package_id):
    data = request.get_json() or {}
    ig_caption = data.get("caption_instagram")
    x_caption  = data.get("caption_x")
    fb_caption = data.get("caption_facebook")

    with get_db() as db:
        get_package_status(package_id)
        if ig_caption is not None:
            db.execute(
                "UPDATE post_status SET caption_instagram = ? WHERE package_id = ?",
                (ig_caption, package_id),
            )
        if x_caption is not None:
            db.execute(
                "UPDATE post_status SET caption_x = ? WHERE package_id = ?",
                (x_caption, package_id),
            )
        if fb_caption is not None:
            db.execute(
                "UPDATE post_status SET caption_facebook = ? WHERE package_id = ?",
                (fb_caption, package_id),
            )
        db.commit()

    return jsonify({"success": True})


@app.route("/api/packages/<package_id>/reschedule", methods=["POST"])
def api_reschedule(package_id):
    """Pick a new optimal slot for a package, or accept a custom ISO timestamp."""
    data        = request.get_json() or {}
    custom_time = data.get("scheduled_for")   # Optional ISO UTC string

    if custom_time:
        try:
            slot_utc = datetime.fromisoformat(custom_time).astimezone(timezone.utc)
        except ValueError:
            return jsonify({"success": False, "error": "Invalid datetime format"}), 400
    else:
        slot_utc = get_next_slot()

    slot_iso = slot_utc.isoformat()
    slot_uae = slot_utc.astimezone(UAE_TZ)
    slot_display = slot_uae.strftime("%a %d %b · %I:%M %p UAE")

    with get_db() as db:
        db.execute(
            "UPDATE post_status SET scheduled_for=?, schedule_status='scheduled', schedule_error=NULL WHERE package_id=?",
            (slot_iso, package_id),
        )
        db.commit()

    return jsonify({"success": True, "scheduled_for": slot_iso, "slot_display": slot_display})


@app.route("/api/packages/<package_id>/unschedule", methods=["POST"])
def api_unschedule(package_id):
    """Cancel the automatic schedule for a package."""
    with get_db() as db:
        db.execute(
            "UPDATE post_status SET scheduled_for=NULL, schedule_status=NULL, schedule_error=NULL WHERE package_id=?",
            (package_id,),
        )
        db.commit()
    return jsonify({"success": True})


@app.route("/api/scheduler/status")
def api_scheduler_status():
    """Return overview of all scheduled posts, enriched with topic/image info."""
    now_utc  = datetime.now(timezone.utc)
    packages = scan_packages()
    pkg_map  = {p["id"]: p for p in packages}

    with get_db() as db:
        rows = db.execute(
            """SELECT package_id, scheduled_for, schedule_status, schedule_error,
                      status, posted_instagram_at, posted_x_at, posted_facebook_at
               FROM post_status
               WHERE schedule_status IN ('scheduled','posting','posted','failed')
               ORDER BY scheduled_for ASC"""
        ).fetchall()

    items = []
    for r in rows:
        item = dict(r)
        pkg = pkg_map.get(item["package_id"], {})
        item["topic"]  = pkg.get("topic", item["package_id"])
        item["images"] = pkg.get("images", [])
        if item.get("scheduled_for"):
            try:
                slot_utc = datetime.fromisoformat(item["scheduled_for"]).astimezone(timezone.utc)
                slot_uae = slot_utc.astimezone(UAE_TZ)
                item["slot_display"]   = slot_uae.strftime("%a %d %b · %I:%M %p UAE")
                item["minutes_until"]  = int((slot_utc - now_utc).total_seconds() / 60)
            except Exception:
                item["slot_display"]   = item["scheduled_for"]
                item["minutes_until"]  = None
        items.append(item)

    scheduled_count = sum(1 for i in items if i["schedule_status"] == "scheduled")
    return jsonify({
        "scheduled":       items,
        "scheduled_count": scheduled_count,
        "server_utc":      now_utc.isoformat(),
    })


@app.route("/api/packages/<package_id>/post/now", methods=["POST"])
def api_post_now(package_id):
    """Cancel scheduled time and post immediately to all platforms."""
    packages = scan_packages()
    pkg = next((p for p in packages if p["id"] == package_id), None)
    if not pkg:
        abort(404)

    status = get_package_status(package_id)
    if status["status"] not in ("approved", "posted"):
        return jsonify({"success": False, "error": "Package must be approved before posting"}), 400

    # Mark as 'posting' to prevent double-fire from scheduler
    with get_db() as db:
        db.execute(
            "UPDATE post_status SET scheduled_for=NULL, schedule_status='posting' WHERE package_id=?",
            (package_id,),
        )
        db.commit()

    # Post in background thread (same as scheduler)
    threading.Thread(
        target=_post_package_to_all,
        args=(package_id,),
        daemon=True,
        name=f"post-now-{package_id}",
    ).start()

    return jsonify({"success": True, "message": "Posting started"})


@app.route("/api/packages/<package_id>/post/local", methods=["POST"])
def api_post_local(package_id):
    """Mark a package as posted locally — no API credentials required.
    Records it as posted in the DB and writes a 'posted_locally.txt' receipt file.
    """
    packages = scan_packages()
    pkg = next((p for p in packages if p["id"] == package_id), None)
    if not pkg:
        abort(404)

    status = get_package_status(package_id)
    data       = request.get_json() or {}
    platform   = data.get("platform", "all")   # "instagram", "x", "facebook", or "all"
    notes      = data.get("notes", "")
    posted_at  = datetime.utcnow().isoformat()

    # Write a receipt file into the package folder
    receipt_path = os.path.join(pkg["folder"], "posted_locally.txt")
    ig_cap = status["caption_instagram"] or pkg["ig_caption"]
    x_cap  = status["caption_x"]         or pkg["x_caption"]
    fb_cap = status.get("caption_facebook") or pkg["ig_caption"]
    receipt = (
        f"POSTED LOCALLY — {pkg['topic']}\n"
        f"{'='*50}\n"
        f"Posted at : {posted_at}\n"
        f"Platform  : {platform}\n"
        f"Notes     : {notes or '—'}\n\n"
        f"── INSTAGRAM CAPTION ──\n{ig_cap}\n\n"
        f"── X / TWITTER CAPTION ──\n{x_cap}\n\n"
        f"── FACEBOOK CAPTION ──\n{fb_cap}\n"
    )
    with open(receipt_path, "w") as f:
        f.write(receipt)

    with get_db() as db:
        updates = ["status = 'posted'", "notes = ?"]
        params  = [f"Posted locally ({platform}) at {posted_at}. {notes}".strip()]

        if platform in ("instagram", "all", "both"):
            updates.append("posted_instagram_at = ?")
            params.append(posted_at)
        if platform in ("x", "all", "both"):
            updates.append("posted_x_at = ?")
            params.append(posted_at)
        if platform in ("facebook", "all"):
            updates.append("posted_facebook_at = ?")
            params.append(posted_at)

        params.append(package_id)
        db.execute(
            f"UPDATE post_status SET {', '.join(updates)} WHERE package_id = ?",
            params,
        )
        db.commit()

    return jsonify({
        "success":  True,
        "platform": platform,
        "posted_at": posted_at,
        "receipt":  receipt_path,
    })


@app.route("/api/packages/<package_id>/post/instagram", methods=["POST"])
def api_post_instagram(package_id):
    packages = scan_packages()
    pkg = next((p for p in packages if p["id"] == package_id), None)
    if not pkg:
        abort(404)

    status = get_package_status(package_id)
    if status["status"] not in ("approved", "posted"):
        return jsonify({"success": False, "error": "Package must be approved before posting"}), 400

    # If the caller specifies which image file to use, respect that choice.
    # Otherwise fall back to the auto-selection (portrait > square > first image).
    data = request.get_json(silent=True) or {}
    requested_file = data.get("image_file")
    if requested_file and requested_file in pkg["images"]:
        image_file = requested_file
    else:
        portrait   = next((i for i in pkg["images"] if "portrait" in i), None)
        square     = next((i for i in pkg["images"] if "square" in i), None)
        image_file = portrait or square or (pkg["images"][0] if pkg["images"] else None)

    if not image_file:
        return jsonify({"success": False, "error": "No image found in package"}), 400

    image_path = os.path.join(pkg["folder"], image_file)
    caption    = status["caption_instagram"] or pkg["ig_caption"]

    result = instagram.post(image_path, caption)

    if result["success"]:
        with get_db() as db:
            db.execute("""
                UPDATE post_status
                SET instagram_post_id = ?,
                    posted_instagram_at = ?
                WHERE package_id = ?
            """, (result["post_id"], datetime.utcnow().isoformat(), package_id))
            db.commit()

    return jsonify(result)


@app.route("/api/packages/<package_id>/post/x", methods=["POST"])
def api_post_x(package_id):
    packages = scan_packages()
    pkg = next((p for p in packages if p["id"] == package_id), None)
    if not pkg:
        abort(404)

    status = get_package_status(package_id)
    if status["status"] not in ("approved", "posted"):
        return jsonify({"success": False, "error": "Package must be approved before posting"}), 400

    # If the caller specifies which image file to use, respect that choice.
    data = request.get_json(silent=True) or {}
    requested_file = data.get("image_file")
    if requested_file and requested_file in pkg["images"]:
        image_file = requested_file
    else:
        landscape  = next((i for i in pkg["images"] if "x_landscape" in i), None)
        image_file = landscape or (pkg["images"][0] if pkg["images"] else None)

    if not image_file:
        return jsonify({"success": False, "error": "No image found in package"}), 400

    image_path = os.path.join(pkg["folder"], image_file)
    caption    = status["caption_x"] or pkg["x_caption"]

    result = x_poster.post(image_path, caption)

    if result["success"]:
        with get_db() as db:
            db.execute("""
                UPDATE post_status
                SET x_post_id = ?,
                    posted_x_at = ?
                WHERE package_id = ?
            """, (result["post_id"], datetime.utcnow().isoformat(), package_id))
            db.commit()

    return jsonify(result)


@app.route("/api/packages/<package_id>/post/facebook", methods=["POST"])
def api_post_facebook(package_id):
    packages = scan_packages()
    pkg = next((p for p in packages if p["id"] == package_id), None)
    if not pkg:
        abort(404)

    status = get_package_status(package_id)
    if status["status"] not in ("approved", "posted"):
        return jsonify({"success": False, "error": "Package must be approved before posting"}), 400

    # If the caller specifies which image file to use, respect that choice.
    data = request.get_json(silent=True) or {}
    requested_file = data.get("image_file")
    if requested_file and requested_file in pkg["images"]:
        image_file = requested_file
    else:
        square   = next((i for i in pkg["images"] if "square" in i), None)
        portrait = next((i for i in pkg["images"] if "portrait" in i), None)
        image_file = square or portrait or (pkg["images"][0] if pkg["images"] else None)

    if not image_file:
        return jsonify({"success": False, "error": "No image found in package"}), 400

    image_path = os.path.join(pkg["folder"], image_file)
    caption    = status.get("caption_facebook") or status["caption_instagram"] or pkg["ig_caption"]

    result = facebook_poster.post(image_path, caption)

    if result["success"]:
        with get_db() as db:
            db.execute("""
                UPDATE post_status
                SET facebook_post_id = ?,
                    posted_facebook_at = ?
                WHERE package_id = ?
            """, (result["post_id"], datetime.utcnow().isoformat(), package_id))
            db.commit()

    return jsonify(result)


# ─────────────────────────────────────────────────────────────────────────────
# Cycle runner
# ─────────────────────────────────────────────────────────────────────────────

_cycle_lock  = threading.Lock()
_cycle_log   = []
_cycle_running = False


def _run_cycle_thread(cycle_num: int, run_id: int):
    global _cycle_running, _cycle_log
    _cycle_log = []

    try:
        process = subprocess.Popen(
            [sys.executable, "main.py", "--single", "--cycle-num", str(cycle_num)],
            cwd=config.BASE_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        for line in process.stdout:
            line = line.rstrip()
            _cycle_log.append(line)
            if len(_cycle_log) > 200:
                _cycle_log = _cycle_log[-200:]

        process.wait()
        status = "complete" if process.returncode == 0 else "failed"

        # Extract top topic from log
        top_topic = ""
        top_score = 0.0
        for line in _cycle_log:
            if "— " in line and "/" in line:
                try:
                    parts = line.strip().split("—")
                    if len(parts) >= 2:
                        score_part = parts[0].strip().split()[-1]
                        top_score = float(score_part)
                        top_topic = parts[1].strip()
                except Exception:
                    pass
                break

        with get_db() as db:
            db.execute("""
                UPDATE cycle_runs
                SET finished_at = ?, status = ?, top_topic = ?, top_score = ?, log_tail = ?
                WHERE id = ?
            """, (
                datetime.utcnow().isoformat(),
                status,
                top_topic,
                top_score,
                "\n".join(_cycle_log[-50:]),
                run_id,
            ))
            db.commit()

    except Exception as e:
        logger.error(f"Cycle thread error: {e}")
        with get_db() as db:
            db.execute(
                "UPDATE cycle_runs SET status = 'failed', finished_at = ? WHERE id = ?",
                (datetime.utcnow().isoformat(), run_id),
            )
            db.commit()
    finally:
        _cycle_running = False


@app.route("/api/cycles/run", methods=["POST"])
def api_run_cycle():
    global _cycle_running
    if _cycle_running:
        return jsonify({"success": False, "error": "A cycle is already running"}), 409

    data      = request.get_json() or {}
    cycle_num = data.get("cycle_num", 0)

    with get_db() as db:
        cursor = db.execute(
            "INSERT INTO cycle_runs (started_at, status, cycle_num) VALUES (?, 'running', ?)",
            (datetime.utcnow().isoformat(), cycle_num),
        )
        run_id = cursor.lastrowid
        db.commit()

    _cycle_running = True
    thread = threading.Thread(
        target=_run_cycle_thread,
        args=(cycle_num, run_id),
        daemon=True,
    )
    thread.start()

    return jsonify({"success": True, "run_id": run_id, "cycle_num": cycle_num})


@app.route("/api/cycles/log")
def api_cycle_log():
    return jsonify({
        "running": _cycle_running,
        "lines":   _cycle_log[-80:],
    })


@app.route("/api/cycles")
def api_cycles():
    with get_db() as db:
        rows = db.execute(
            "SELECT * FROM cycle_runs ORDER BY id DESC LIMIT 20"
        ).fetchall()
    return jsonify([dict(r) for r in rows])


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    init_db()
    _scheduler_thread.start()

    print("""
╔══════════════════════════════════════════════════════════════╗
║        SCORING ZONE — CONTENT COMMAND CENTRE                 ║
╠══════════════════════════════════════════════════════════════╣
║  Dashboard:  http://localhost:5050                           ║
║                                                              ║
║  Review → Approve → Post directly to Instagram & X          ║
╚══════════════════════════════════════════════════════════════╝
""")

    app.run(host="0.0.0.0", port=5050, debug=False)
