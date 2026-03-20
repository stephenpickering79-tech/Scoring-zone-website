"""
scorer.py — Scores ContentOpportunity objects and ranks them.
"""
from __future__ import annotations
import json
import logging
import os
from researcher import ContentOpportunity

import config

logger = logging.getLogger(__name__)

# ── Scoring weights — defaults (must sum to 1.0) ──────────────────────────────
W_VIEWS     = 0.35   # Raw YouTube demand signal
W_TREND     = 0.30   # Google Trends momentum
W_LIKES     = 0.15   # Engagement quality signal
W_VOLUME    = 0.10   # Number of videos (more = established niche)
W_DIRECTION = 0.10   # Trend direction bonus

# ── Benchmarks for normalisation ─────────────────────────────────────────────
MAX_VIEWS  = 2_000_000
MAX_LIKES  =   100_000
MAX_VIDEOS =        10

_LEARNED_WEIGHTS_PATH = os.path.join(config.BASE_DIR, "learned_weights.json")
_MIN_N_FOR_LEARNING   = 10


def _load_learned_weights() -> tuple[dict | None, int]:
    """Attempt to load learned_weights.json.  Returns (weights_dict, n) or (None, 0)."""
    try:
        if os.path.exists(_LEARNED_WEIGHTS_PATH):
            with open(_LEARNED_WEIGHTS_PATH) as f:
                data = json.load(f)
            n = data.get("n", 0)
            w = data.get("weights", {})
            if n >= _MIN_N_FOR_LEARNING and len(w) == 5:
                return w, n
    except Exception as exc:
        logger.warning(f"[scorer] Could not load learned weights: {exc}")
    return None, 0


# Load once at import time
_learned_weights, _learned_n = _load_learned_weights()
if _learned_weights:
    logger.info(f"[scorer] Using LEARNED weights (n={_learned_n})")
else:
    logger.info("[scorer] Using DEFAULT weights")


def _normalise(val: float, max_val: float) -> float:
    if max_val <= 0:
        return 0.0
    return min(1.0, val / max_val)


def _direction_bonus(direction: str) -> float:
    return {"rising": 1.0, "steady": 0.5, "falling": 0.1}.get(direction, 0.5)


def score_opportunity(opp: ContentOpportunity) -> float:
    """Return a 0-100 opportunity score, using learned weights if available."""
    lw = _learned_weights or {}

    w_views     = lw.get("views",     W_VIEWS)
    w_trend     = lw.get("trend",     W_TREND)
    w_likes     = lw.get("likes",     W_LIKES)
    w_volume    = lw.get("volume",    W_VOLUME)
    w_direction = lw.get("direction", W_DIRECTION)

    views_score = _normalise(opp.youtube_views, MAX_VIEWS)
    trend_score = _normalise(opp.trend_score, 100.0)
    likes_score = _normalise(opp.youtube_likes, MAX_LIKES)
    vol_score   = _normalise(opp.video_count,   MAX_VIDEOS)
    dir_score   = _direction_bonus(opp.trend_direction)

    raw = (
        views_score * w_views +
        trend_score * w_trend +
        likes_score * w_likes +
        vol_score   * w_volume +
        dir_score   * w_direction
    )
    return round(raw * 100, 1)


def score_and_rank(
    opportunities: list[ContentOpportunity],
    top_n: int = 5,
) -> list[ContentOpportunity]:
    """Score all opportunities, sort by score, return top N."""
    for opp in opportunities:
        opp.opportunity_score = score_opportunity(opp)

    ranked = sorted(opportunities, key=lambda o: o.opportunity_score, reverse=True)

    logger.info("── Top opportunities ──────────────────────────────")
    for i, opp in enumerate(ranked[:top_n], 1):
        logger.info(
            f"  #{i:02d}  {opp.opportunity_score:5.1f}  {opp.trend_direction:7s}  {opp.keyword}"
        )

    return ranked[:top_n]
