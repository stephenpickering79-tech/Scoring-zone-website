"""
researcher.py — Discovers trending golf short-game topics from YouTube + Google Trends.
"""
from __future__ import annotations
import logging, os, time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

# ── Keywords to seed research ─────────────────────────────────────────────────
SEED_KEYWORDS = [
    "golf chipping tips",
    "golf putting tips",
    "bunker shot technique",
    "golf short game",
    "stop 3 putting",
    "golf chipping drills",
    "lag putting drill",
    "golf pitching tips",
    "golf around the green",
    "short game practice",
    "golf wedge shots",
    "golf scoring tips",
    "lower golf scores",
    "golf practice drills",
    "golf beginner tips",
]


@dataclass
class ContentOpportunity:
    keyword:          str
    topic:            str
    youtube_views:    int   = 0
    youtube_likes:    int   = 0
    video_count:      int   = 0
    trend_score:      float = 0.0
    trend_direction:  str   = "steady"   # "rising" | "steady" | "falling"
    opportunity_score: float = 0.0
    top_video_title:  str   = ""
    top_video_id:     str   = ""
    top_channel:      str   = ""
    search_date:      str   = field(default_factory=lambda: datetime.utcnow().isoformat())
    raw_videos:       list  = field(default_factory=list)


class YouTubeResearcher:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self._service = None

    def _get_service(self):
        if self._service is None:
            from googleapiclient.discovery import build
            self._service = build("youtube", "v3", developerKey=self.api_key)
        return self._service

    def search_keyword(self, keyword: str, max_results: int = 10) -> dict:
        """Search YouTube for a keyword, return aggregated stats."""
        try:
            svc = self._get_service()
            resp = svc.search().list(
                q=keyword,
                part="snippet",
                type="video",
                order="viewCount",
                maxResults=max_results,
                relevanceLanguage="en",
                publishedAfter="2023-01-01T00:00:00Z",
            ).execute()

            items = resp.get("items", [])
            if not items:
                return {"views": 0, "likes": 0, "count": 0, "videos": [],
                        "top_title": "", "top_id": "", "top_channel": ""}

            # Get video IDs for stats
            video_ids = [i["id"]["videoId"] for i in items if "videoId" in i.get("id", {})]
            if not video_ids:
                return {"views": 0, "likes": 0, "count": 0, "videos": [],
                        "top_title": "", "top_id": "", "top_channel": ""}

            stats_resp = svc.videos().list(
                part="statistics,snippet",
                id=",".join(video_ids),
            ).execute()

            total_views = 0
            total_likes = 0
            videos = []
            for vid in stats_resp.get("items", []):
                s = vid.get("statistics", {})
                v = int(s.get("viewCount", 0))
                l = int(s.get("likeCount", 0))
                total_views += v
                total_likes += l
                videos.append({
                    "id":      vid["id"],
                    "title":   vid["snippet"]["title"],
                    "channel": vid["snippet"]["channelTitle"],
                    "views":   v,
                    "likes":   l,
                })

            videos.sort(key=lambda x: x["views"], reverse=True)
            top = videos[0] if videos else {}

            return {
                "views":       total_views,
                "likes":       total_likes,
                "count":       len(videos),
                "videos":      videos,
                "top_title":   top.get("title", ""),
                "top_id":      top.get("id", ""),
                "top_channel": top.get("channel", ""),
            }

        except Exception as e:
            logger.warning(f"YouTube search failed for '{keyword}': {e}")
            return {"views": 0, "likes": 0, "count": 0, "videos": [],
                    "top_title": "", "top_id": "", "top_channel": ""}


class TrendsResearcher:
    def __init__(self):
        self._pytrends = None

    def _get_pytrends(self):
        if self._pytrends is None:
            from pytrends.request import TrendReq
            self._pytrends = TrendReq(hl="en-US", tz=0, timeout=(10, 25))
        return self._pytrends

    def get_trend_score(self, keyword: str) -> tuple[float, str]:
        """Return (score 0-100, direction: rising/steady/falling)."""
        try:
            pt = self._get_pytrends()
            pt.build_payload([keyword], timeframe="now 3-m", geo="")
            df = pt.interest_over_time()
            if df.empty or keyword not in df.columns:
                return 50.0, "steady"

            vals = df[keyword].tolist()
            if not vals:
                return 50.0, "steady"

            recent   = vals[-4:]   # last ~month
            earlier  = vals[:4]    # first ~month
            avg_recent  = sum(recent)  / len(recent)  if recent  else 50
            avg_earlier = sum(earlier) / len(earlier) if earlier else 50
            current_avg = sum(vals[-8:]) / len(vals[-8:]) if vals else 50

            if avg_earlier > 0:
                change_pct = (avg_recent - avg_earlier) / avg_earlier
            else:
                change_pct = 0

            direction = "rising" if change_pct > 0.15 else "falling" if change_pct < -0.15 else "steady"
            score = min(100.0, max(0.0, float(current_avg)))

            return score, direction

        except Exception as e:
            logger.warning(f"Trends lookup failed for '{keyword}': {e}")
            return 50.0, "steady"


def run_research(
    youtube_api_key: str,
    keywords: list[str] | None = None,
    max_yt_results: int = 10,
    use_trends: bool = True,
) -> list[ContentOpportunity]:
    """
    Run the full research pipeline. Returns a list of ContentOpportunity objects,
    unsorted and unscored (scoring is done in scorer.py).
    """
    if keywords is None:
        keywords = SEED_KEYWORDS

    yt = YouTubeResearcher(youtube_api_key)
    tr = TrendsResearcher() if use_trends else None

    opportunities: list[ContentOpportunity] = []

    for kw in keywords:
        logger.info(f"  Researching: {kw}")

        yt_data = yt.search_keyword(kw, max_results=max_yt_results)

        trend_score, trend_dir = (50.0, "steady")
        if tr:
            time.sleep(1.5)   # rate limit for pytrends
            trend_score, trend_dir = tr.get_trend_score(kw)

        # Derive a clean topic name from the keyword
        topic = kw.title()

        opp = ContentOpportunity(
            keyword=kw,
            topic=topic,
            youtube_views=yt_data["views"],
            youtube_likes=yt_data["likes"],
            video_count=yt_data["count"],
            trend_score=trend_score,
            trend_direction=trend_dir,
            top_video_title=yt_data["top_title"],
            top_video_id=yt_data["top_id"],
            top_channel=yt_data["top_channel"],
            raw_videos=yt_data["videos"],
        )
        opportunities.append(opp)

    return opportunities
