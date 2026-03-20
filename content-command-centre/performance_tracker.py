"""
performance_tracker.py — Fetch engagement metrics from IG/FB/X after posting.

Called automatically by the scheduler thread in dashboard.py (every hour).
Can also be triggered manually via POST /api/fetch-metrics/<package_id>.

Platform permissions required:
  Instagram : instagram_manage_insights on INSTAGRAM_ACCESS_TOKEN
  Facebook  : read_insights on the Page access token
  X         : tweet.read + OAuth 1.0a user context (TWITTER_* env vars)
"""
from __future__ import annotations

import logging
import os
import sqlite3
from datetime import datetime, timezone, timedelta

import requests

import config

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(config.BASE_DIR, "post_status.db")
GRAPH_BASE = "https://graph.facebook.com/v19.0"

# Wait at least this many hours after posting before fetching metrics (T+24h window)
MIN_HOURS_BEFORE_FETCH = 23


# ─────────────────────────────────────────────────────────────────────────────
# DB helper
# ─────────────────────────────────────────────────────────────────────────────

def _get_db():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=MEMORY")
    return db


# ─────────────────────────────────────────────────────────────────────────────
# Platform metric fetchers
# ─────────────────────────────────────────────────────────────────────────────

def fetch_instagram_metrics(post_id: str) -> dict | None:
    """Fetch engagement metrics for an Instagram post.

    Returns dict with ig_reach, ig_impressions, ig_likes_post,
    ig_comments, ig_saves, ig_shares — or None on failure.
    Requires instagram_manage_insights permission on the access token.
    """
    token = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
    if not token:
        logger.warning("[tracker] INSTAGRAM_ACCESS_TOKEN not set — skipping IG metrics")
        return None

    try:
        # Fetch insights (reach, impressions, saves, shares)
        ins_resp = requests.get(
            f"{GRAPH_BASE}/{post_id}/insights",
            params={
                "metric": "reach,impressions,saved,shares",
                "access_token": token,
            },
            timeout=15,
        )
        metrics: dict = {}
        if ins_resp.ok:
            for item in ins_resp.json().get("data", []):
                name = item.get("name")
                # Insights can return values as a list (time-series) or a single int
                raw = item.get("values")
                if isinstance(raw, list) and raw:
                    val = raw[-1].get("value", 0)
                else:
                    val = item.get("value", 0)
                if isinstance(val, dict):
                    val = sum(val.values())
                metrics[name] = int(val) if val else 0
        else:
            err = ins_resp.json().get("error", {}).get("message", ins_resp.text[:120])
            logger.warning(f"[tracker] IG insights failed ({post_id}): {err}")

        # Fetch like_count + comments_count from media fields
        media_resp = requests.get(
            f"{GRAPH_BASE}/{post_id}",
            params={"fields": "like_count,comments_count", "access_token": token},
            timeout=15,
        )
        if media_resp.ok:
            d = media_resp.json()
            metrics["like_count"]     = d.get("like_count", 0)
            metrics["comments_count"] = d.get("comments_count", 0)

        return {
            "ig_reach":      metrics.get("reach", 0),
            "ig_impressions": metrics.get("impressions", 0),
            "ig_likes_post":  metrics.get("like_count", 0),
            "ig_comments":    metrics.get("comments_count", 0),
            "ig_saves":       metrics.get("saved", 0),
            "ig_shares":      metrics.get("shares", 0),
        }

    except Exception as e:
        logger.error(f"[tracker] IG metrics error ({post_id}): {e}")
        return None


def fetch_facebook_metrics(post_id: str) -> dict | None:
    """Fetch engagement metrics for a Facebook post.

    Returns dict with fb_reach, fb_reactions, fb_comments, fb_shares
    — or None on failure.  Requires read_insights on the page token.
    """
    token   = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")  # same Meta system-user token
    page_id = os.getenv("FACEBOOK_PAGE_ID", "")
    if not token or not page_id:
        logger.warning("[tracker] Facebook credentials not configured — skipping FB metrics")
        return None

    try:
        # Exchange for page access token
        pt_resp = requests.get(
            f"{GRAPH_BASE}/{page_id}",
            params={"fields": "access_token", "access_token": token},
            timeout=15,
        )
        page_token = pt_resp.json().get("access_token", token) if pt_resp.ok else token

        # Post insights
        ins_resp = requests.get(
            f"{GRAPH_BASE}/{post_id}/insights",
            params={
                "metric": "post_impressions_unique,post_reactions_by_type_total",
                "access_token": page_token,
            },
            timeout=15,
        )
        metrics: dict = {}
        if ins_resp.ok:
            for item in ins_resp.json().get("data", []):
                name = item.get("name")
                raw  = item.get("values")
                val  = (raw[-1].get("value", 0) if isinstance(raw, list) and raw else item.get("value", 0))
                metrics[name] = val

        # Shares + comments
        post_resp = requests.get(
            f"{GRAPH_BASE}/{post_id}",
            params={"fields": "shares,comments.summary(true)", "access_token": page_token},
            timeout=15,
        )
        if post_resp.ok:
            d = post_resp.json()
            metrics["shares"]   = d.get("shares", {}).get("count", 0)
            metrics["comments"] = d.get("comments", {}).get("summary", {}).get("total_count", 0)

        reactions = metrics.get("post_reactions_by_type_total", {})
        total_reactions = sum(reactions.values()) if isinstance(reactions, dict) else 0

        return {
            "fb_reach":     metrics.get("post_impressions_unique", 0),
            "fb_reactions": total_reactions,
            "fb_comments":  metrics.get("comments", 0),
            "fb_shares":    metrics.get("shares", 0),
        }

    except Exception as e:
        logger.error(f"[tracker] FB metrics error ({post_id}): {e}")
        return None


def fetch_x_metrics(tweet_id: str) -> dict | None:
    """Fetch engagement metrics for an X/Twitter tweet.

    Returns dict with x_impressions, x_likes, x_retweets, x_replies,
    x_bookmarks — or None on failure.
    Requires tweet.read + OAuth 1.0a user context.
    """
    api_key    = os.getenv("TWITTER_API_KEY", "")
    api_secret = os.getenv("TWITTER_API_SECRET", "")
    token      = os.getenv("TWITTER_ACCESS_TOKEN", "")
    secret     = os.getenv("TWITTER_ACCESS_TOKEN_SECRET", "")

    if not all([api_key, api_secret, token, secret]):
        logger.warning("[tracker] Twitter credentials not configured — skipping X metrics")
        return None

    try:
        import tweepy
    except ImportError:
        logger.warning("[tracker] tweepy not installed — skipping X metrics")
        return None

    try:
        client = tweepy.Client(
            consumer_key        = api_key,
            consumer_secret     = api_secret,
            access_token        = token,
            access_token_secret = secret,
        )
        tweet = client.get_tweet(tweet_id, tweet_fields=["public_metrics"])
        if tweet.data:
            pm = tweet.data.public_metrics or {}
            return {
                "x_impressions": pm.get("impression_count", 0),
                "x_likes":       pm.get("like_count", 0),
                "x_retweets":    pm.get("retweet_count", 0),
                "x_replies":     pm.get("reply_count", 0),
                "x_bookmarks":   pm.get("bookmark_count", 0),
            }
        return None

    except Exception as e:
        logger.error(f"[tracker] X metrics error ({tweet_id}): {e}")
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Composite score
# ─────────────────────────────────────────────────────────────────────────────

def compute_engagement_score(
    ig: dict | None,
    fb: dict | None,
    x:  dict | None,
) -> float:
    """Compute a normalised 0-100 composite engagement score.

    Saves and shares are weighted highest (signal of content value),
    followed by likes/reactions, then raw reach.
    """
    score        = 0.0
    weight_total = 0.0

    if ig:
        # 'good' IG post benchmark: ~200 weighted signal points
        ig_sig = (
            ig.get("ig_saves", 0)      * 4 +
            ig.get("ig_shares", 0)     * 3 +
            ig.get("ig_likes_post", 0) * 2 +
            ig.get("ig_comments", 0)   * 2 +
            ig.get("ig_reach", 0)      * 0.01
        )
        score        += min(1.0, ig_sig / 200.0) * 50
        weight_total += 50

    if fb:
        fb_sig = (
            fb.get("fb_shares", 0)    * 3 +
            fb.get("fb_reactions", 0) * 2 +
            fb.get("fb_comments", 0)  * 2 +
            fb.get("fb_reach", 0)     * 0.01
        )
        score        += min(1.0, fb_sig / 100.0) * 25
        weight_total += 25

    if x:
        x_sig = (
            x.get("x_bookmarks", 0)   * 4 +
            x.get("x_retweets", 0)    * 3 +
            x.get("x_likes", 0)       * 2 +
            x.get("x_replies", 0)     * 1 +
            x.get("x_impressions", 0) * 0.005
        )
        score        += min(1.0, x_sig / 50.0) * 25
        weight_total += 25

    if weight_total == 0:
        return 0.0
    return round((score / weight_total) * 100, 1)


# ─────────────────────────────────────────────────────────────────────────────
# Batch / single fetch
# ─────────────────────────────────────────────────────────────────────────────

def fetch_metrics_for_package(package_id: str) -> bool:
    """Fetch and store all available metrics for a specific package.
    Returns True if at least one platform returned data.
    """
    with _get_db() as db:
        row = db.execute(
            "SELECT * FROM post_status WHERE package_id = ?", (package_id,)
        ).fetchone()

    if not row:
        logger.warning(f"[tracker] Package {package_id} not found")
        return False

    row = dict(row)
    ig_metrics = fb_metrics = x_metrics = None

    if row.get("instagram_post_id"):
        ig_metrics = fetch_instagram_metrics(row["instagram_post_id"])
    if row.get("facebook_post_id"):
        fb_metrics = fetch_facebook_metrics(row["facebook_post_id"])
    if row.get("x_post_id"):
        x_metrics = fetch_x_metrics(row["x_post_id"])

    if not any([ig_metrics, fb_metrics, x_metrics]):
        logger.info(f"[tracker] No metrics retrieved for {package_id}")
        return False

    eng_score = compute_engagement_score(ig_metrics, fb_metrics, x_metrics)
    now_iso   = datetime.now(timezone.utc).isoformat()

    updates: dict = {"metrics_fetched_at": now_iso, "engagement_score": eng_score}
    if ig_metrics:
        updates.update(ig_metrics)
    if fb_metrics:
        updates.update(fb_metrics)
    if x_metrics:
        updates.update(x_metrics)

    set_clause = ", ".join(f"{k} = ?" for k in updates)
    vals       = list(updates.values()) + [package_id]

    with _get_db() as db:
        db.execute(
            f"UPDATE post_status SET {set_clause} WHERE package_id = ?",
            vals,
        )
        db.commit()

    logger.info(f"[tracker] {package_id} → engagement_score={eng_score:.1f}")
    return True


def fetch_all_pending_metrics() -> int:
    """Scan DB for posted packages that haven't had metrics fetched yet.

    Only fetches for packages posted at least MIN_HOURS_BEFORE_FETCH hours ago.
    Returns number of packages updated.
    """
    now_utc   = datetime.now(timezone.utc)
    threshold = now_utc - timedelta(hours=MIN_HOURS_BEFORE_FETCH)

    with _get_db() as db:
        rows = db.execute(
            """SELECT package_id, posted_instagram_at, posted_x_at, posted_facebook_at
               FROM post_status
               WHERE status = 'posted'
                 AND metrics_fetched_at IS NULL
            """
        ).fetchall()

    updated = 0
    for row in rows:
        row = dict(row)
        # Use the earliest post time across platforms
        earliest = None
        for field in ("posted_instagram_at", "posted_x_at", "posted_facebook_at"):
            ts = row.get(field)
            if ts:
                try:
                    dt = datetime.fromisoformat(ts)
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    if earliest is None or dt < earliest:
                        earliest = dt
                except Exception:
                    pass

        if earliest and earliest <= threshold:
            pkg_id = row["package_id"]
            logger.info(f"[tracker] Fetching metrics: {pkg_id} (posted {earliest.date()})")
            if fetch_metrics_for_package(pkg_id):
                updated += 1

    if updated:
        logger.info(f"[tracker] Updated metrics for {updated} package(s)")
    return updated
