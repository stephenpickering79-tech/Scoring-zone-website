"""
performance_analyser.py — Correlate engagement data and output learned config files.

Reads from post_status.db (populated by performance_tracker.py) and the
package manifest files, then writes three output files to BASE_DIR:

  learned_weights.json     — scorer weight overrides
  caption_performance.json — caption template performance scores
  variant_performance.json — image variant preference per platform

Learning only kicks in once MIN_DATA_POINTS packages have metrics.
"""
from __future__ import annotations

import json
import logging
import math
import os
import sqlite3
from collections import defaultdict
from datetime import datetime

import config

logger = logging.getLogger(__name__)

DB_PATH         = os.path.join(config.BASE_DIR, "post_status.db")
LEARNED_WEIGHTS = os.path.join(config.BASE_DIR, "learned_weights.json")
CAPTION_PERF    = os.path.join(config.BASE_DIR, "caption_performance.json")
VARIANT_PERF    = os.path.join(config.BASE_DIR, "variant_performance.json")

MIN_DATA_POINTS = 10   # configurable threshold


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _get_db():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=MEMORY")
    return db


def _load_manifests(package_ids: list[str]) -> dict:
    """Load manifest.json for each package_id. Returns dict of id → manifest."""
    manifests = {}
    for pkg_id in package_ids:
        path = os.path.join(config.PACKAGES_DIR, pkg_id, "manifest.json")
        if os.path.exists(path):
            try:
                with open(path) as f:
                    manifests[pkg_id] = json.load(f)
            except Exception:
                pass
    return manifests


def _rows_with_metrics() -> list[dict]:
    """Return all posted packages that have an engagement_score."""
    with _get_db() as db:
        rows = db.execute(
            """SELECT * FROM post_status
               WHERE status = 'posted'
                 AND engagement_score IS NOT NULL
                 AND metrics_fetched_at IS NOT NULL
            """
        ).fetchall()
    return [dict(r) for r in rows]


def _pearson(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 2:
        return 0.0
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx  = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy  = math.sqrt(sum((y - my) ** 2 for y in ys))
    return num / (dx * dy) if dx * dy > 0 else 0.0


# ─────────────────────────────────────────────────────────────────────────────
# Analysis functions
# ─────────────────────────────────────────────────────────────────────────────

def correlate_opportunity_vs_engagement(rows: list[dict], manifests: dict) -> dict:
    """Correlate each scoring component with actual engagement.

    Returns a dict of weight overrides for the scorer, or {} if insufficient data.
    Blends 60% learned + 40% default to avoid wild swings early on.
    """
    pairs = []
    for row in rows:
        manifest = manifests.get(row["package_id"], {})
        eng = row.get("engagement_score")
        if eng is None:
            continue
        pairs.append({
            "eng":             eng,
            "youtube_views":   manifest.get("youtube_views", 0),
            "youtube_likes":   manifest.get("youtube_likes", 0),
            "trend_score":     manifest.get("trend_score", 50),
            "trend_direction": manifest.get("trend_direction", "steady"),
        })

    if len(pairs) < MIN_DATA_POINTS:
        return {}

    engs   = [p["eng"] for p in pairs]
    views  = [p["youtube_views"] for p in pairs]
    likes  = [p["youtube_likes"] for p in pairs]
    trends = [p["trend_score"] for p in pairs]
    dirs   = [
        1.0 if p["trend_direction"] == "rising"
        else 0.5 if p["trend_direction"] == "steady"
        else 0.1
        for p in pairs
    ]

    corr_views  = max(0.01, abs(_pearson(views,  engs)))
    corr_likes  = max(0.01, abs(_pearson(likes,  engs)))
    corr_trends = max(0.01, abs(_pearson(trends, engs)))
    corr_dirs   = max(0.01, abs(_pearson(dirs,   engs)))
    corr_volume = 0.05   # volume has no direct engagement signal; hold steady

    total = corr_views + corr_trends + corr_likes + corr_volume + corr_dirs

    defaults = {"views": 0.35, "trend": 0.30, "likes": 0.15, "volume": 0.10, "direction": 0.10}
    blend    = 0.6

    weights = {
        "views":     blend * (corr_views  / total) + (1 - blend) * defaults["views"],
        "trend":     blend * (corr_trends / total) + (1 - blend) * defaults["trend"],
        "likes":     blend * (corr_likes  / total) + (1 - blend) * defaults["likes"],
        "volume":    blend * (corr_volume / total) + (1 - blend) * defaults["volume"],
        "direction": blend * (corr_dirs   / total) + (1 - blend) * defaults["direction"],
    }

    # Normalise so weights sum to 1.0
    total_w = sum(weights.values())
    return {k: round(v / total_w, 3) for k, v in weights.items()}


def rank_caption_templates(rows: list[dict], manifests: dict) -> dict:
    """Rank caption templates by average engagement.

    Returns dict of template_key → {n, avg_engagement, max_engagement, selection_weight}.
    selection_weight is a softmax-derived probability for use in packager.py.
    """
    template_scores: dict[str, list[float]] = defaultdict(list)

    for row in rows:
        manifest = manifests.get(row["package_id"], {})
        # caption_template may be in DB row or in manifest (written by packager.py)
        template = row.get("caption_template") or manifest.get("caption_template")
        eng      = row.get("engagement_score")
        if template and eng is not None:
            template_scores[template].append(eng)

    if not template_scores:
        return {}

    result = {}
    for key, scores in template_scores.items():
        result[key] = {
            "n":              len(scores),
            "avg_engagement": round(sum(scores) / len(scores), 1),
            "max_engagement": round(max(scores), 1),
        }

    # Softmax selection weights
    avgs    = [v["avg_engagement"] for v in result.values()]
    max_avg = max(avgs) if avgs else 1.0
    keys    = list(result.keys())
    normed  = [v["avg_engagement"] / max(max_avg, 0.001) for v in result.values()]
    exp_v   = [math.exp(n) for n in normed]
    total_e = sum(exp_v)
    for key, ev in zip(keys, exp_v):
        result[key]["selection_weight"] = round(ev / total_e, 3)

    return result


def rank_image_variants(rows: list[dict]) -> dict:
    """Rank image variants (1/2/3) by average engagement.

    Returns dict with per-variant stats and a 'preferred_variant' key.
    """
    variant_scores: dict[int, list[float]] = defaultdict(list)

    for row in rows:
        variant = row.get("image_variant_used")
        eng     = row.get("engagement_score")
        if variant is not None and eng is not None:
            variant_scores[int(variant)].append(eng)

    result = {}
    for v, scores in variant_scores.items():
        result[str(v)] = {
            "n":              len(scores),
            "avg_engagement": round(sum(scores) / len(scores), 1),
        }

    if result:
        best = max(result, key=lambda k: result[k]["avg_engagement"])
        result["preferred_variant"] = int(best)

    return result


def rank_keywords(rows: list[dict], manifests: dict) -> dict:
    """Which seed keywords reliably produce high-engagement content?"""
    kw_scores: dict[str, list[float]] = defaultdict(list)

    for row in rows:
        manifest = manifests.get(row["package_id"], {})
        keyword  = manifest.get("keyword", "")
        eng      = row.get("engagement_score")
        if keyword and eng is not None:
            kw_scores[keyword].append(eng)

    result = {}
    for kw, scores in kw_scores.items():
        result[kw] = {
            "n":              len(scores),
            "avg_engagement": round(sum(scores) / len(scores), 1),
        }

    return dict(sorted(result.items(), key=lambda x: x[1]["avg_engagement"], reverse=True))


def rank_posting_times(rows: list[dict]) -> dict:
    """Which UTC hour drove the most engagement?"""
    hour_scores: dict[int, list[float]] = defaultdict(list)

    for row in rows:
        ts  = row.get("posted_instagram_at") or row.get("posted_x_at") or row.get("posted_facebook_at")
        eng = row.get("engagement_score")
        if ts and eng is not None:
            try:
                hour_scores[datetime.fromisoformat(ts).hour].append(eng)
            except Exception:
                pass

    result = {}
    for hour, scores in hour_scores.items():
        result[str(hour)] = {
            "n":              len(scores),
            "avg_engagement": round(sum(scores) / len(scores), 1),
        }

    return dict(sorted(result.items(), key=lambda x: x[1]["avg_engagement"], reverse=True))


# ─────────────────────────────────────────────────────────────────────────────
# File writers
# ─────────────────────────────────────────────────────────────────────────────

def _write_json(path: str, data: dict):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def generate_learned_weights(weights: dict, n: int):
    _write_json(LEARNED_WEIGHTS, {
        "n":         n,
        "updated_at": datetime.utcnow().isoformat(),
        "weights":   weights,
    })
    logger.info(f"[analyser] learned_weights.json written (n={n}, weights={weights})")


def generate_caption_performance(templates: dict, n: int):
    _write_json(CAPTION_PERF, {
        "n":         n,
        "updated_at": datetime.utcnow().isoformat(),
        "templates": templates,
    })
    logger.info(f"[analyser] caption_performance.json written ({len(templates)} templates)")


def generate_variant_performance(variants: dict, n: int):
    _write_json(VARIANT_PERF, {
        "n":         n,
        "updated_at": datetime.utcnow().isoformat(),
        "variants":  variants,
    })
    logger.info(f"[analyser] variant_performance.json written")


# ─────────────────────────────────────────────────────────────────────────────
# Main entry points
# ─────────────────────────────────────────────────────────────────────────────

def run_analysis() -> bool:
    """Run full analysis pipeline. Returns True if learning threshold was met
    and output files were written.
    """
    rows = _rows_with_metrics()
    n    = len(rows)

    logger.info(f"[analyser] {n} packages with metrics (threshold={MIN_DATA_POINTS})")

    if n < MIN_DATA_POINTS:
        logger.info(f"[analyser] Not enough data yet ({n}/{MIN_DATA_POINTS}) — skipping")
        return False

    pkg_ids   = [r["package_id"] for r in rows]
    manifests = _load_manifests(pkg_ids)

    # 1. Recalibrate scorer weights
    weights = correlate_opportunity_vs_engagement(rows, manifests)
    if weights:
        generate_learned_weights(weights, n)

    # 2. Caption template performance
    templates = rank_caption_templates(rows, manifests)
    if templates:
        generate_caption_performance(templates, n)
        best = max(templates, key=lambda k: templates[k]["avg_engagement"])
        logger.info(f"[analyser] Best caption template: '{best}' (avg={templates[best]['avg_engagement']})")

    # 3. Image variant performance
    variants = rank_image_variants(rows)
    if variants:
        generate_variant_performance(variants, n)
        if "preferred_variant" in variants:
            logger.info(f"[analyser] Preferred image variant: #{variants['preferred_variant']}")

    logger.info(f"[analyser] Learning update complete — cycle n={n}")
    return True


def get_analysis_summary() -> dict:
    """Return a summary dict for the dashboard Performance view."""
    rows = _rows_with_metrics()
    n    = len(rows)

    if n == 0:
        return {"n": 0, "ready": False, "threshold": MIN_DATA_POINTS}

    pkg_ids   = [r["package_id"] for r in rows]
    manifests = _load_manifests(pkg_ids)

    avg_eng = round(sum(r["engagement_score"] for r in rows) / n, 1)

    templates     = rank_caption_templates(rows, manifests)
    variants      = rank_image_variants(rows)
    keywords      = rank_keywords(rows, manifests)
    posting_times = rank_posting_times(rows)

    return {
        "n":                      n,
        "ready":                  n >= MIN_DATA_POINTS,
        "threshold":              MIN_DATA_POINTS,
        "avg_engagement":         avg_eng,
        "top_keywords":           list(keywords.items())[:5],
        "templates":              templates,
        "variants":               variants,
        "posting_times":          posting_times,
        "learned_weights_active": os.path.exists(LEARNED_WEIGHTS),
        "caption_perf_active":    os.path.exists(CAPTION_PERF),
        "variant_perf_active":    os.path.exists(VARIANT_PERF),
    }
