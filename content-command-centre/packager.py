"""
packager.py — Builds a full content package from a scored ContentOpportunity.

Each package folder contains:
  manifest.json, caption_instagram.txt, caption_x.txt,
  brief_summary.md, posting_instructions.txt, image_01-03.jpg

On each run the packager loads caption_performance.json and
variant_performance.json (if they exist) and biases template selection
and variant ordering toward historically high-engagement choices.
"""
from __future__ import annotations
import json, logging, math, os, random, re
from datetime import datetime
from researcher import ContentOpportunity
from media_processor import generate_images
import config

logger = logging.getLogger(__name__)

# Rotating CTAs — keeps the feed fresh, same core message
_CTAS_IG = [
    "\n\n🆓 Free early access is live — join at scoringzone.net 👇",
    "\n\n⛳ Start for free today at scoringzone.net 👇",
    "\n\n🎯 Track every drill, score every session — free at scoringzone.net 👇",
    "\n\n🆓 No cost. No card. Just better golf. Sign up at scoringzone.net 👇",
    "\n\n📲 Get instant free access at scoringzone.net 👇",
    "\n\n⛳ Join golfers already improving their short game — scoringzone.net 👇",
    "\n\n🆓 Early access is free right now. Don't wait → scoringzone.net 👇",
    "\n\n🎯 Free to join. scoringzone.net 👇",
]

_CTAS_X = [
    "\n\nFree early access: scoringzone.net",
    "\n\nStart free → scoringzone.net",
    "\n\nJoin free at scoringzone.net",
    "\n\nFree access live now: scoringzone.net",
    "\n\nNo cost. Just better golf. scoringzone.net",
    "\n\nGet early access free → scoringzone.net",
    "\n\nTrack it. Score it. Fix it. scoringzone.net",
    "\n\nFree to join: scoringzone.net",
]

IG_HASHTAGS = (
    "#golf #shortgame #golfpractice #golftips #golfdrills "
    "#scoringzone #lowscores #golflife #improveyourgolf #golfer"
)

X_HASHTAGS = "#golf #shortgame #scoringzone #golfpractice"


def _load_caption_performance() -> dict:
    """Load caption_performance.json if it exists. Returns templates dict or {}."""
    path = os.path.join(config.BASE_DIR, "caption_performance.json")
    try:
        if os.path.exists(path):
            with open(path) as f:
                return json.load(f).get("templates", {})
    except Exception:
        pass
    return {}


def _load_variant_preference() -> int | None:
    """Load variant_performance.json and return preferred variant number, or None."""
    path = os.path.join(config.BASE_DIR, "variant_performance.json")
    try:
        if os.path.exists(path):
            with open(path) as f:
                data = json.load(f)
            return data.get("variants", {}).get("preferred_variant")
    except Exception:
        pass
    return None


def _weighted_template_key(
    kw: str,
    hooks: dict,
    caption_perf: dict,
) -> tuple[str | None, str]:
    """Select a template key for the given keyword.

    Falls back to exact-match logic first. If multiple keys match (rare),
    or if no key matches and we need to pick from the best-performing defaults,
    uses softmax weights from caption_performance.json.

    Returns (matched_key_or_None, template_label_for_manifest).
    """
    # Find candidate matching keys
    candidates = [k for k in hooks if k in kw]

    if len(candidates) == 1:
        return candidates[0], candidates[0]

    if len(candidates) > 1 and caption_perf:
        # Multiple matches — pick by performance weight
        weights = [caption_perf.get(c, {}).get("selection_weight", 1.0) for c in candidates]
        chosen  = random.choices(candidates, weights=weights, k=1)[0]
        return chosen, chosen

    if len(candidates) == 1:
        return candidates[0], candidates[0]

    # No match — bias toward best-performing template key if data available
    if caption_perf:
        keys    = list(caption_perf.keys())
        weights = [caption_perf[k].get("selection_weight", 1.0) for k in keys]
        chosen  = random.choices(keys, weights=weights, k=1)[0]
        return None, chosen   # None signals "use fallback body"

    return None, "default"


def _cta_ig(seed: str = "") -> str:
    import hashlib
    idx = int(hashlib.md5(seed.encode()).hexdigest(), 16) % len(_CTAS_IG) if seed else 0
    return _CTAS_IG[idx]


def _cta_x(seed: str = "") -> str:
    import hashlib
    idx = int(hashlib.md5(seed.encode()).hexdigest(), 16) % len(_CTAS_X) if seed else 0
    return _CTAS_X[idx]


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")[:40]


# ── Caption generators ────────────────────────────────────────────────────────

def _ig_caption(
    opp: ContentOpportunity,
    context_snippets: list[str] | None = None,
    caption_perf: dict | None = None,
) -> tuple[str, str]:
    """Build the Instagram caption.  Returns (caption_text, template_key_used)."""
    kw = opp.keyword.lower()
    caption_perf = caption_perf or {}

    hooks = {
        "putt":   "Three putts don't just cost you strokes. They cost you momentum, confidence, and the round you were building.",
        "3-putt": "Ninety percent of three putts come from lag putts finishing too long or too short — not from missing the line.",
        "chip":   "The short game is where most rounds are won and lost. Not on the tee. Not on the fairway.",
        "bunker": "Most golfers fear bunkers. Tour pros love them. Here's the difference.",
        "pitch":  "Shots inside 100 yards make up the majority of strokes in your round. Are you practising them?",
        "wedge":  "From 100 yards in — this is where your scorecard gets written.",
        "score":  "Breaking 90 isn't about longer drives. It's about getting up and down more often.",
        "break":  "60-65 of your shots per round happen inside 100 yards. That's where scoring lives.",
        "short":  "Most golfers practise the short game wrong. Here's what actually works.",
        "practice": "The problem isn't discipline — it's that your practice has no structure, no score, and no stakes.",
    }

    matched_key, template_key = _weighted_template_key(kw, hooks, caption_perf)
    hook = (
        hooks[matched_key]
        if matched_key and matched_key in hooks
        else f"Here's what the data shows about {opp.topic.lower()} — and how to fix it fast."
    )

    bodies = {
        "putt": (
            "The Lag Putting Ladder — done in 20 minutes:\n"
            "→ 5 balls from 20 ft, 30 ft & 40 ft\n"
            "→ Every putt must finish within 3 feet\n"
            "→ Score 12/15 to pass the drill\n\n"
            "Tour pros leave every lag putt within 3 feet from 30+ft.\n"
            "2 weeks of this and your 3-putts disappear."
        ),
        "chip": (
            "Fix it in one 20-minute session:\n"
            "✅ Weight forward 60/40 at address\n"
            "✅ Shaft leaning toward the target\n"
            "✅ Small shoulder turn — zero wrist flip\n"
            "✅ Low, quiet follow-through\n\n"
            "Track your up-&-down % and aim for 40% first.\n"
            "Tour pros convert 60-65%. You can get there."
        ),
        "bunker": (
            "The Bunker Escape Formula (works every time):\n"
            "✅ Open the clubface FIRST, then grip\n"
            "✅ Aim 2 inches behind the ball\n"
            "✅ Swing THROUGH — never decelerate\n"
            "✅ Finish HIGH, every single time\n\n"
            "20 repetitions. Bunkers stop being scary."
        ),
        "pitch": (
            "The 30-yard Pitching Drill:\n"
            "→ Start 30 yards from the pin\n"
            "→ Hinge wrists early in the backswing\n"
            "→ Hold the face open — let the loft work\n"
            "→ Land every ball within 6 feet\n\n"
            "3 sessions/week × 20 mins = measurable improvement in 2-3 weeks."
        ),
        "score": (
            "The fastest path to lower scores:\n"
            "→ 20-30 min sessions, 3× per week\n"
            "→ Session 1: putting\n"
            "→ Session 2: chipping\n"
            "→ Session 3: mixed\n\n"
            "Not more practice. Smarter practice. Scored practice."
        ),
        "practice": (
            "The structure that makes practice addictive:\n"
            "✅ 10 min block practice (groove the movement)\n"
            "✅ 10 min variable practice (different targets)\n"
            "✅ 10 min scored challenge (personal best to beat)\n\n"
            "When practice has a score, motivation takes care of itself."
        ),
    }
    body = next((v for k, v in bodies.items() if k in kw),
                f"The {opp.topic} drill that works:\n"
                "→ Start simple — 10 balls, one target\n"
                "→ Score every session\n"
                "→ Chase your personal best\n\n"
                "One focused session beats ten scattered ones.")

    caption = f"{hook}\n\n{body}{_cta_ig(opp.keyword)}\n\n{IG_HASHTAGS}"
    return caption, template_key


def _x_caption(opp: ContentOpportunity) -> str:
    kw = opp.keyword.lower()

    posts = {
        "putt": (
            "90% of 3-putts are a distance control problem, not a technique problem.\n\n"
            "Lag Ladder drill: 5 balls from 20/30/40ft. Every putt within 3 feet. Score 12/15.\n\n"
            "2 weeks. 3-putts gone."
        ),
        "3-putt": (
            "Most golfers aim at the hole and hope the speed takes care of itself.\n\n"
            "It doesn't.\n\n"
            "Lag Ladder: 5 balls at 20/30/40ft → every putt within 3ft → score 12/15 to pass."
        ),
        "chip": (
            "90% of amateurs flip their wrists through impact when chipping.\n\n"
            "Fix: weight forward, shaft lean at address, shoulder turn only.\n\n"
            "Takes 20 minutes to rewire. Changes everything."
        ),
        "bunker": (
            "You're still in the bunker because you're trying to hit the ball.\n\n"
            "Hit the SAND 2 inches behind it. Open face → swing through → finish high.\n\n"
            "That's the whole secret."
        ),
        "pitch": (
            "Pitching is 30% of your score and about 5% of your practice time.\n\n"
            "Start from 30 yards. Hinge early. Hold the face open. Land within 6 feet.\n\n"
            "3 sessions/week × 20 mins. Done in 2 weeks."
        ),
        "score": (
            "60-65 of your shots per round happen inside 100 yards.\n\n"
            "That's where breaking 90 lives. Not on the tee.\n\n"
            "3 x 20-min short game sessions per week is all it takes."
        ),
        "break": (
            "Breaking 90 isn't about longer drives.\n\n"
            "It's about: fewer 3-putts + more up-and-downs.\n\n"
            "That's it. 2-3 months of smart practice and you're there."
        ),
        "practice": (
            "Boring practice won't fix your game.\n\n"
            "Structure: 10 min block → 10 min variable → 10 min scored challenge.\n\n"
            "When practice has a score, you actually show up."
        ),
    }
    body = next((v for k, v in posts.items() if k in kw),
                f"The {opp.topic} insight that changes how you practice:\n\n"
                "Score every session. Chase your personal best.\n\n"
                "One focused session beats ten scattered ones.")

    return f"{body}{_cta_x(opp.keyword)}\n\n{X_HASHTAGS}"


def _brief(opp: ContentOpportunity) -> str:
    return f"""# Content Brief: {opp.topic}

## Opportunity Score: {opp.opportunity_score}/100

## Data Signal
| Metric | Value |
|---|---|
| Primary keyword | `{opp.keyword}` |
| YouTube views (top {opp.video_count} results) | {opp.youtube_views:,} |
| YouTube likes | {opp.youtube_likes:,} |
| Google Trends score | {opp.trend_score:.0f}/100 |
| Trend direction | **{opp.trend_direction.upper()}** |

## Top YouTube Video
**{opp.top_video_title}**
Channel: {opp.top_channel}
https://youtube.com/watch?v={opp.top_video_id}

## Content Strategy
High intent search. Golfers actively looking to solve this problem.
Target: 8–18 HCP recreational golfer.
Hook with the pain point, deliver the drill, CTA to Scoring Zone.

## Recommended Posting Time
- **Instagram**: Tuesday or Thursday 7–9am / 6–8pm
- **X / Twitter**: Monday or Wednesday 7–9am

## Caption Notes
- Instagram: use full drill breakdown with steps
- X: punchy, one clear insight, 240 chars max body
- Both: end with CTA → scoringzone.net
"""


def _posting_instructions(opp: ContentOpportunity) -> str:
    return f"""POSTING INSTRUCTIONS — {opp.topic}
{'='*54}

INSTAGRAM
  • Primary image : image_01.jpg
  • Caption       : caption_instagram.txt (ready to copy-paste)
  • CTA           : Drive to scoringzone.net — free early access
  • Best time     : Tue/Thu 7–9am or 6–8pm

X / TWITTER
  • Primary image : image_02.jpg
  • Caption       : caption_x.txt (280-char optimised)
  • CTA           : Drive to scoringzone.net — free early access
  • Best time     : Mon/Wed 7–9am

NOTES
  • Space posts 30–60 mins apart for algorithm diversity
  • Reply to comments within the first hour for reach boost
  • Keep scoringzone.net in your IG bio link at all times
"""


# ── Main entry point ──────────────────────────────────────────────────────────

def build_package(
    opp: ContentOpportunity,
    packages_dir: str,
    cycle_number: int = 0,
    context_snippets: list[str] | None = None,
) -> str:
    """Build a complete content package. Returns the package folder path."""

    folder_name = f"cycle_{cycle_number:04d}_{_slug(opp.keyword)}"
    folder = os.path.join(packages_dir, folder_name)
    os.makedirs(folder, exist_ok=True)

    logger.info(f"  Building package: {folder_name}")

    # ── Load learning data ──
    caption_perf       = _load_caption_performance()
    preferred_variant  = _load_variant_preference()
    if caption_perf:
        logger.info(f"  [packager] Using caption performance data ({len(caption_perf)} templates)")
    if preferred_variant:
        logger.info(f"  [packager] Preferred image variant: #{preferred_variant}")

    # ── Images ──
    generate_images(
        topic=opp.topic,
        opportunity_score=opp.opportunity_score,
        trend_direction=opp.trend_direction,
        output_folder=folder,
        n_variants=3,
    )

    # ── Captions ──
    ig_cap, caption_template = _ig_caption(opp, context_snippets, caption_perf)
    x_cap  = _x_caption(opp)

    with open(os.path.join(folder, "caption_instagram.txt"), "w") as f:
        f.write(ig_cap)
    with open(os.path.join(folder, "caption_x.txt"), "w") as f:
        f.write(x_cap)

    # ── Supporting files ──
    with open(os.path.join(folder, "brief_summary.md"), "w") as f:
        f.write(_brief(opp))
    with open(os.path.join(folder, "posting_instructions.txt"), "w") as f:
        f.write(_posting_instructions(opp))

    # ── Manifest ──
    manifest = {
        "package_id":        folder_name,
        "topic":             opp.topic,
        "keyword":           opp.keyword,
        "opportunity_score": opp.opportunity_score,
        "trend_direction":   opp.trend_direction,
        "trend_score":       opp.trend_score,
        "youtube_views":     opp.youtube_views,
        "youtube_likes":     opp.youtube_likes,
        "top_video_title":   opp.top_video_title,
        "top_video_id":      opp.top_video_id,
        "top_channel":       opp.top_channel,
        "cycle_number":      cycle_number,
        "image_count":       3,
        "caption_template":  caption_template,
        "preferred_variant": preferred_variant,
        "created_at":        datetime.utcnow().isoformat(),
    }
    with open(os.path.join(folder, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)

    return folder


def build_all(
    opportunities: list[ContentOpportunity],
    packages_dir: str,
    cycle_number: int = 0,
    context_snippets: list[str] | None = None,
) -> list[str]:
    """Build packages for all opportunities. Returns list of folder paths."""
    folders = []
    for opp in opportunities:
        try:
            folder = build_package(opp, packages_dir, cycle_number, context_snippets)
            folders.append(folder)
        except Exception as e:
            logger.error(f"Failed to build package for '{opp.keyword}': {e}")
    return folders
