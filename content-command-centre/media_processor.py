"""
media_processor.py — Generates Scoring Zone branded social media images.

Neon Meridian design philosophy:
  Dark space as pressurised material. One singular neon (#00ed04) is the only
  colour truth. Concentric rings as a targeting scope. Text as monumental
  architecture. The golf course breathes through the dark field.

Produces 3 image variants per topic (1080×1080 square for IG/X).
"""
from __future__ import annotations
import math
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance

# ── Paths ─────────────────────────────────────────────────────────────────────
_DIR        = os.path.dirname(os.path.abspath(__file__))
_FONT_DIR   = os.path.join(_DIR, "fonts")
_LOGO_PATH  = os.path.join(_DIR, "scoringzone_logo.png")

# Landing Page photography assets (user's own images)
# Mounted workspace is at /mnt/... — go two levels up from _DIR to reach it
_WORKSPACE  = os.path.dirname(os.path.dirname(_DIR))   # e.g. /sessions/.../mnt
_PHOTO_DIR  = os.path.join(_WORKSPACE, "Landing Page", "golf images")

BARLOW_XB   = os.path.join(_FONT_DIR, "BarlowCondensed-ExtraBold.ttf")
BARLOW_B    = os.path.join(_FONT_DIR, "BarlowCondensed-Bold.ttf")
GEIST_B     = os.path.join(_FONT_DIR, "GeistMono-Bold.ttf")
GEIST_R     = os.path.join(_FONT_DIR, "GeistMono-Regular.ttf")

# Fallback to system fonts if not present
_FALLBACK   = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"

# ── Brand constants (Neon Meridian / Scoring Zone design system) ──────────────
BG_DARK     = (2,   6,   2)        # near-black, green-tinted
GREEN       = (0,  237,  4)        # #00ed04 — primary neon (sampled from logo)
GREEN_HI    = (110, 255, 112)      # lighter variant for text
GREEN_TICK  = (0,   55,  2)        # very dark green for grid lines
TEXT_PURE   = (255, 255, 255)      # pure white for headline
TEXT_MID    = (155, 240, 157)      # tagline soft green-white
TEXT_GHOST  = (55,  115,  57)      # subtle secondary text
BAR_TEXT    = (2,   6,   2)        # text on green bar

# ── Canvas ─────────────────────────────────────────────────────────────────────
W = H = 1080
BAR_H = 52  # green top bar height


# ── Font loader ────────────────────────────────────────────────────────────────
def _fnt(path: str, size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        try:
            return ImageFont.truetype(_FALLBACK, size)
        except Exception:
            return ImageFont.load_default()


# ── Photo background system — semantic filename matching ──────────────────────
import hashlib

# Keyword weights per content category.
# Keys are topic keywords; values are lists of (filename_substring, score).
# Filenames are matched case-insensitively against these substrings.
_KEYWORD_SCORES: dict[str, list[tuple[str, int]]] = {
    # Putting
    "putt": [
        ("putt", 20), ("putting", 20), ("putter", 15), ("scotty", 12),
        ("premium putter", 14), ("lines up putt", 18), ("lining up", 16),
        ("sunset", 10), ("crowd", 8), ("tournament", 8), ("green", 6),
        ("practice", 5), ("drill", 5), ("challenge", 5),
    ],
    "3-putt": [
        ("lines up putt", 20), ("lining up", 18), ("putting", 16), ("putt", 14),
        ("crowd", 10), ("tournament", 10), ("green", 6),
    ],
    "lag": [
        ("putting", 18), ("putt", 16), ("lines up", 14), ("sunset", 10),
        ("premium putter", 12), ("scotty", 10),
    ],
    # Chipping / short game
    "chip": [
        ("short game", 20), ("practice", 18), ("chip", 20), ("drill", 12),
        ("challenge", 10), ("fairway", 8), ("walking", 6), ("scenicgolf", 4),
    ],
    "pitch": [
        ("short game", 20), ("practice", 18), ("drill", 12), ("chip", 10),
        ("fairway", 8), ("walking", 6), ("scenic", 4),
    ],
    "wedge": [
        ("short game", 18), ("practice", 16), ("drill", 12), ("putting", 8),
        ("scenic", 6), ("beautiful", 5),
    ],
    # Bunker / sand
    "bunker": [
        ("short game", 16), ("practice", 14), ("drill", 10),
        ("scenic", 8), ("cliff", 8), ("beautiful", 6), ("ireland", 6),
    ],
    "sand": [
        ("short game", 16), ("practice", 14), ("drill", 10),
        ("scenic", 8), ("cliff", 6), ("beautiful", 6),
    ],
    # Scoring / breaking scores
    "score": [
        ("stat", 20), ("stats", 20), ("celebrat", 16), ("win", 14),
        ("celebrate", 16), ("scenic", 8), ("beautiful", 6), ("cliff", 6),
        ("ireland", 5), ("walking", 5),
    ],
    "break": [
        ("celebrat", 20), ("win", 18), ("celebrate", 20), ("kid celebrat", 22),
        ("walking", 10), ("fairway", 8), ("scenic", 6), ("beautiful", 5),
    ],
    # Practice / general
    "practice": [
        ("practice", 20), ("drill", 18), ("challenge", 16), ("stat", 14),
        ("putting", 10), ("short game", 10), ("lining up", 8),
    ],
    "short": [
        ("short game", 20), ("practice", 16), ("drill", 12), ("putting", 10),
        ("chip", 8), ("challenge", 8), ("lining up", 6),
    ],
}

# Fallback: scenic / beautiful course images
_SCENIC_WORDS = ("scenic", "beautiful", "cliff", "ireland", "california",
                 "royal", "walking", "fairway", "hole")

# Cache the scanned image list so we don't re-read the directory every call
_photo_cache: list[str] | None = None


def _all_photos() -> list[str]:
    """Return sorted list of all valid image filenames in _PHOTO_DIR."""
    global _photo_cache
    if _photo_cache is not None:
        return _photo_cache
    exts = {".jpg", ".jpeg", ".png", ".webp"}
    try:
        files = [
            f for f in os.listdir(_PHOTO_DIR)
            if os.path.splitext(f.lower())[1] in exts
            and not f.startswith(".")
        ]
        _photo_cache = sorted(files)
    except Exception:
        _photo_cache = []
    return _photo_cache


def _score_photo(filename: str, weights: list[tuple[str, int]]) -> int:
    """Score a filename against a list of (substring, score) pairs."""
    name = filename.lower()
    return sum(score for kw, score in weights if kw in name)


def _get_topic_photos(topic_lower: str, n: int = 3, rotation_seed: str = "") -> list[str]:
    """
    Return n photo filenames best matched to topic_lower.

    Matching strategy (two passes, scores combined):
      1. Direct title-word match — every significant word in the topic title
         is checked against the filename directly. This is the primary signal:
         "Golf Putting Tips" → scores any file with "putting" very highly.
      2. Category weight map — the pre-defined _KEYWORD_SCORES tables add
         semantic depth (e.g. "putt" also pulls in "crowd", "tournament").

    rotation_seed shifts the starting position within the matched pool so
    different packages on the same topic use different photos.
    """
    all_files = _all_photos()
    if not all_files:
        return []

    # ── Pass 1: direct title-word scoring ────────────────────────────────────
    # Strip common stop words; weight remaining words from title directly
    _STOP = {"golf", "tips", "how", "to", "the", "a", "an", "for",
             "and", "with", "in", "on", "at", "of", "is", "your"}
    title_words = [
        w for w in topic_lower.replace("-", " ").split()
        if w not in _STOP and len(w) > 2
    ]
    # Title-word weights: exact match scores 25, contained scores 15
    direct_weights: list[tuple[str, int]] = []
    for w in title_words:
        direct_weights.append((w, 25))          # e.g. "putting" in filename

    # ── Pass 2: category keyword weights ─────────────────────────────────────
    category_weights: list[tuple[str, int]] = []
    for kw, w in _KEYWORD_SCORES.items():
        if kw in topic_lower:
            category_weights = w
            break
    if not category_weights:
        category_weights = [(w, 8) for w in _SCENIC_WORDS]

    # ── Combine and score every file ─────────────────────────────────────────
    combined: list[tuple[str, int]] = []
    for f in all_files:
        s1 = _score_photo(f, direct_weights)
        s2 = _score_photo(f, category_weights)
        combined.append((f, s1 + s2))

    combined.sort(key=lambda x: (-x[1], x[0]))

    relevant = [f for f, s in combined if s > 0]
    fallback = [f for f, s in combined if s == 0]
    pool     = relevant if len(relevant) >= n else relevant + fallback

    # ── Rotation ─────────────────────────────────────────────────────────────
    if rotation_seed and len(pool) > n:
        offset = int(hashlib.md5(rotation_seed.encode()).hexdigest(), 16) % max(1, len(pool) - n + 1)
        pool = pool[offset:] + pool[:offset]

    # Pick n distinct photos
    picks: list[str] = []
    for f in pool:
        if f not in picks:
            picks.append(f)
        if len(picks) == n:
            break

    while len(picks) < n:
        for f in all_files:
            if f not in picks:
                picks.append(f)
            if len(picks) == n:
                break
        break

    return picks


def _make_photo_bg(photo_filename: str, overlay_alpha: int = 115) -> Image.Image:
    """
    Load a golf photo, resize to 1080×1080, and apply a heavy dark overlay
    so the Neon Meridian design elements remain fully readable on top.
    Returns an RGBA image.
    """
    photo_path = os.path.join(_PHOTO_DIR, photo_filename)
    if not os.path.exists(photo_path):
        # Fallback to solid dark background
        img = Image.new("RGBA", (W, H), (*BG_DARK, 255))
        return img

    try:
        photo = Image.open(photo_path).convert("RGB")
        # Crop to square centred
        pw, ph = photo.size
        if pw != ph:
            side = min(pw, ph)
            left = (pw - side) // 2
            top  = (ph - side) // 2
            photo = photo.crop((left, top, left + side, top + side))
        photo = photo.resize((W, H), Image.LANCZOS)

        # Desaturate slightly — keep warmth but feel Neon Meridian atmospheric
        from PIL import ImageEnhance as IE
        photo = IE.Color(photo).enhance(0.75)      # keep colour warmth
        photo = IE.Brightness(photo).enhance(0.70) # visible but cinematic

        photo_rgba = photo.convert("RGBA")

        # Dark overlay — brand darkness, but let the photo breathe
        overlay = Image.new("RGBA", (W, H), (2, 6, 2, overlay_alpha))
        photo_rgba = Image.alpha_composite(photo_rgba, overlay)

        # Green tint layer
        tint = Image.new("RGBA", (W, H), (0, 24, 0, 35))
        photo_rgba = Image.alpha_composite(photo_rgba, tint)

        return photo_rgba

    except Exception:
        img = Image.new("RGBA", (W, H), (*BG_DARK, 255))
        return img


# ── Logo extraction (transparent + black hole centre) ─────────────────────────
_logo_cache: Image.Image | None = None

def _get_logo() -> Image.Image | None:
    global _logo_cache
    if _logo_cache is not None:
        return _logo_cache
    if not os.path.exists(_LOGO_PATH):
        return None
    try:
        logo_src = Image.open(_LOGO_PATH).convert("RGBA")
        la = np.array(logo_src, dtype=np.float32)
        r, g, b = la[:, :, 0], la[:, :, 1], la[:, :, 2]
        brightness = r * 0.2 + g * 0.7 + b * 0.1
        low, high = 30, 120
        alpha_mask = np.clip((brightness - low) / (high - low), 0, 1)
        la[:, :, 3] = alpha_mask * 255
        logo_transparent = Image.fromarray(la.clip(0, 255).astype(np.uint8), "RGBA")

        # Add black hole at centre (golf hole)
        lw, lh = logo_transparent.size
        dot_r = int(lw * 0.092)
        dot_layer = Image.new("RGBA", (lw, lh), (0, 0, 0, 0))
        ImageDraw.Draw(dot_layer).ellipse(
            [lw // 2 - dot_r, lh // 2 - dot_r, lw // 2 + dot_r, lh // 2 + dot_r],
            fill=(0, 0, 0, 240)
        )
        _logo_cache = Image.alpha_composite(logo_transparent, dot_layer)
        return _logo_cache
    except Exception:
        return None


# ── Drawing primitives ─────────────────────────────────────────────────────────

def _draw_grid(draw: ImageDraw.Draw, w: int, h: int, spacing: int = 40):
    """Precision engineering grid — very subtle."""
    for x in range(0, w, spacing):
        alpha = 18 if x % 200 == 0 else 8
        col = (*GREEN_TICK, alpha)
        draw.line([(x, 0), (x, h)], fill=col)
    for y in range(0, h, spacing):
        alpha = 18 if y % 200 == 0 else 8
        col = (*GREEN_TICK, alpha)
        draw.line([(0, y), (w, y)], fill=col)


def _draw_corner_brackets(draw: ImageDraw.Draw, w: int, h: int, arm: int = 26,
                           inset: int = 98, stroke: int = 2):
    """Four-corner targeting brackets."""
    col = (*GREEN, 145)
    top, bot = inset, h - inset
    left, right = inset, w - inset
    for (cx, cy, sx, sy) in [
        (left,  top,  1,  1),
        (right, top, -1,  1),
        (left,  bot,  1, -1),
        (right, bot, -1, -1),
    ]:
        draw.line([(cx, cy), (cx + sx * arm, cy)], fill=col, width=stroke)
        draw.line([(cx, cy), (cx, cy + sy * arm)], fill=col, width=stroke)


def _draw_tick_ruler(draw: ImageDraw.Draw, x: int, h: int):
    """Vertical precision tick ruler."""
    for y in range(0, h, 6):
        if y % 40 == 0:
            w_line, alpha = 14, 100
        elif y % 20 == 0:
            w_line, alpha = 9, 62
        else:
            w_line, alpha = 4, 28
        col = (*GREEN, alpha)
        draw.line([(x, y), (x + w_line, y)], fill=col)


def _draw_concentric_rings(img: Image.Image, cx: int, cy: int,
                            base_r: int, num_rings: int = 6):
    """
    Draw concentric glowing rings — the Scoring Zone targeting scope.
    Drawn on a separate RGBA layer for clean compositing.
    """
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for i in range(num_rings):
        r = base_r - i * int(base_r / num_rings)
        if r <= 6:
            break
        # Outer rings: faint; inner rings: brighter
        alpha = int(30 + (num_rings - i) * 18)
        alpha = min(alpha, 200)
        stroke = 2 if i > 1 else 3
        col = (*GREEN, alpha)
        d.ellipse(
            [(cx - r, cy - r), (cx + r, cy + r)],
            outline=col, width=stroke
        )
    # Glow passes (blur the ring layer)
    for blur_r, blend_alpha in [(40, 0.18), (20, 0.25), (8, 0.16)]:
        blurred = layer.filter(ImageFilter.GaussianBlur(radius=blur_r))
        # Reduce alpha
        ba = np.array(blurred, dtype=np.float32)
        ba[:, :, 3] *= blend_alpha
        img.alpha_composite(Image.fromarray(ba.clip(0, 255).astype(np.uint8), "RGBA"))
    img.alpha_composite(layer)

    # Centre dot (the hole)
    d2 = ImageDraw.Draw(img)
    hole_r = max(8, int(base_r * 0.045))
    d2.ellipse(
        [(cx - hole_r, cy - hole_r), (cx + hole_r, cy + hole_r)],
        fill=(0, 0, 0, 255)
    )
    # Small green ring around hole
    d2.ellipse(
        [(cx - hole_r - 3, cy - hole_r - 3), (cx + hole_r + 3, cy + hole_r + 3)],
        outline=(*GREEN, 200), width=2
    )


def _draw_vignette(img: Image.Image):
    """Subtle corner vignette."""
    vign = Image.new("RGBA", img.size, (0, 0, 0, 0))
    arr = np.zeros((img.height, img.width, 4), dtype=np.uint8)
    cx, cy = img.width / 2, img.height / 2
    max_d = math.sqrt(cx ** 2 + cy ** 2)
    for y in range(img.height):
        for x in range(img.width):
            dist = math.sqrt((x - cx) ** 2 + (y - cy) ** 2) / max_d
            if dist > 0.72:
                a = int(min(255, (dist - 0.72) / 0.28 * 180))
                arr[y, x] = [0, 0, 0, a]
    vign = Image.fromarray(arr, "RGBA")
    img.alpha_composite(vign)


def _draw_dark_overlay(img: Image.Image):
    """Graduated dark overlay — heavier at edges, lighter in centre."""
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    arr = np.array(overlay, dtype=np.uint8)
    # left→right gradient
    for x in range(img.width):
        alpha = int(160 - (x / img.width) * 60)
        arr[:, x, 3] = alpha
    arr[:, :, 0] = 0; arr[:, :, 1] = 0; arr[:, :, 2] = 0
    img.alpha_composite(Image.fromarray(arr, "RGBA"))


def _draw_green_tint(img: Image.Image):
    """Subtle green colour grade over the whole image."""
    tint = Image.new("RGBA", img.size, (0, 18, 0, 22))
    img.alpha_composite(tint)


# ── Bullet / stat data ─────────────────────────────────────────────────────────

def _make_bullets(topic_lower: str) -> list[str]:
    # Putting
    if any(w in topic_lower for w in ["3-putt", "3 putt", "three putt"]):
        return ["Ladder drill: 3, 6, 9, 12, 15 ft", "3 consecutive makes to advance", "Track your putting HCP in real time"]
    if any(w in topic_lower for w in ["lag putt", "lag"]):
        return ["All putts must finish within 3 ft", "5 balls from 20, 30 & 40 ft", "Penalty: restart distance on miss"]
    if any(w in topic_lower for w in ["putt", "green", "hole"]):
        return ["Gate challenge: hole must stay in gate", "Consecutive makes = pressure simulation", "Earn XP · watch your putting HCP drop"]
    # Chipping
    if any(w in topic_lower for w in ["bump", "run"]):
        return ["Low trajectory · land short of green", "Let the ball release to the hole", "Score your up & down success rate"]
    if any(w in topic_lower for w in ["flop", "lob"]):
        return ["Open clubface before gripping", "Swing hard · face stays open", "Target: soft landing, minimal roll"]
    if any(w in topic_lower for w in ["up and down", "up & down", "scrambl"]):
        return ["10 total shots · 5 up-and-downs", "Track your chip-and-putt success rate", "Score 3/5 to pass · 5/5 for elite XP"]
    if any(w in topic_lower for w in ["chip", "around the green", "short game"]):
        return ["Weight forward 60/40 at address", "Shaft lean toward target at impact", "Score every rep · track your chipping HCP"]
    # Pitching / wedges
    if any(w in topic_lower for w in ["pitch", "wedge", "100 yard", "distance control"]):
        return ["Ladder drill: 20, 40, 60, 80 yds", "Land zone must be within 6 ft of target", "Scored reps · earn 280 XP on completion"]
    # Bunker
    if any(w in topic_lower for w in ["bunker", "sand"]):
        return ["Open clubface before gripping", "Entry point: 2 inches behind the ball", "Swing through · finish high every time"]
    # Pressure / mental
    if any(w in topic_lower for w in ["pressure", "mental", "nerves", "tournament"]):
        return ["Timer running · consecutive required", "Penalty system mirrors on-course stakes", "Simulate tournament pressure every rep"]
    # Driving / distance
    if any(w in topic_lower for w in ["driv", "distance", "carry", "tee shot", "driver"]):
        return ["Attack angle +3° or higher", "Tee ball level with lead ear", "Max shoulder turn · quiet lower body"]
    # Iron / approach
    if any(w in topic_lower for w in ["iron", "approach", "ball striking", "fairway"]):
        return ["Ball center-to-back in stance", "Hands ahead at impact · compress down", "Track greens in regulation per round"]
    # Handicap / scoring
    if any(w in topic_lower for w in ["handicap", "hcp", "scoring", "score"]):
        return ["Every drill feeds your short game HCP", "Benchmark: beat your score to earn 2× XP", "3.2 avg stroke improvement with Scoring Zone"]
    # Generic short game / improvement
    return ["50+ scored drills across 4 categories", "Real-time HCP scoring every session", "Pressure Test your short game at scoringzone.net"]


def _make_stat(topic_lower: str) -> tuple[str, str]:
    # Putting
    if any(w in topic_lower for w in ["3-putt", "3 putt", "three putt"]):
        return "84%", "of amateurs 3-putt from outside 20 ft"
    if any(w in topic_lower for w in ["lag putt", "lag"]):
        return "62%", "of 3-putts start from poor lag distance"
    if any(w in topic_lower for w in ["putt", "green", "hole"]):
        return "43%", "of all golf strokes are putts"
    # Chipping
    if any(w in topic_lower for w in ["bump", "run"]):
        return "80%", "of chips should be bump & runs"
    if any(w in topic_lower for w in ["flop", "lob"]):
        return "1 in 5", "amateurs can execute a flop shot"
    if any(w in topic_lower for w in ["up and down", "up & down", "scrambl"]):
        return "18%", "amateur up-and-down success rate"
    if any(w in topic_lower for w in ["chip", "around the green", "short game"]):
        return "60%", "of shots occur within 100 yards"
    # Pitching
    if any(w in topic_lower for w in ["pitch", "wedge", "100 yard", "distance control"]):
        return "67%", "of all shots happen inside 100 yds"
    # Bunker
    if any(w in topic_lower for w in ["bunker", "sand"]):
        return "2\"", "behind the ball · every single time"
    # Pressure
    if any(w in topic_lower for w in ["pressure", "mental", "nerves", "tournament"]):
        return "3.2", "avg strokes saved with pressure practice"
    # Driving
    if any(w in topic_lower for w in ["driv", "distance", "carry", "tee shot", "driver"]):
        return "41 yds", "average gap: amateur vs tour pro"
    # Iron
    if any(w in topic_lower for w in ["iron", "approach", "ball striking", "fairway"]):
        return "68%", "of amateurs miss greens on approach"
    # Handicap
    if any(w in topic_lower for w in ["handicap", "hcp", "scoring", "score"]):
        return "3.2", "avg stroke improvement with Scoring Zone"
    # Default
    return "50+", "scored drills to pressure test your short game"


def _topic_label(topic_lower: str) -> str:
    if any(w in topic_lower for w in ["3-putt", "3 putt", "three putt", "lag"]):
        return "PUTTING DRILL"
    if any(w in topic_lower for w in ["putt", "green", "hole"]):
        return "PUTTING DRILL"
    if any(w in topic_lower for w in ["bump", "run"]):
        return "CHIPPING DRILL"
    if any(w in topic_lower for w in ["flop", "lob"]):
        return "CHIPPING DRILL"
    if any(w in topic_lower for w in ["up and down", "up & down", "scrambl"]):
        return "UP & DOWN DRILL"
    if any(w in topic_lower for w in ["chip", "around the green", "short game"]):
        return "CHIPPING DRILL"
    if any(w in topic_lower for w in ["pitch", "wedge", "100 yard", "distance control"]):
        return "PITCHING DRILL"
    if any(w in topic_lower for w in ["bunker", "sand"]):
        return "BUNKER DRILL"
    if any(w in topic_lower for w in ["pressure", "mental", "nerves", "tournament"]):
        return "PRESSURE TEST"
    if any(w in topic_lower for w in ["driv", "distance", "carry", "tee shot", "driver"]):
        return "DRIVING DRILL"
    if any(w in topic_lower for w in ["iron", "approach", "ball striking", "fairway"]):
        return "IRON PLAY DRILL"
    if any(w in topic_lower for w in ["handicap", "hcp", "scoring", "score"]):
        return "SCORING ZONE"
    return "SHORT GAME DRILL"


# ── Wrap text ─────────────────────────────────────────────────────────────────

def _wrap(text: str, font: ImageFont.FreeTypeFont, max_w: int) -> list[str]:
    words = text.upper().split()
    lines, cur = [], []
    tmp = Image.new("RGB", (1, 1))
    d = ImageDraw.Draw(tmp)
    for w in words:
        trial = " ".join(cur + [w])
        if cur and d.textlength(trial, font=font) > max_w:
            lines.append(" ".join(cur))
            cur = [w]
        else:
            cur.append(w)
    if cur:
        lines.append(" ".join(cur))
    return lines[:3]


# ── Variant builders ──────────────────────────────────────────────────────────

def _variant_monumental(
    topic: str,
    opportunity_score: float,
    trend_direction: str,
    bullets: list[str],
    stat: str,
    stat_lbl: str,
    drill_label: str,
    logo: Image.Image | None,
    photo_bg: Image.Image | None = None,
) -> Image.Image:
    """
    Variant 1: Neon Gradient
    Full-bleed photo. Dark gradient wells up from the bottom half.
    Headline stacks at the bottom in massive type. Stat floats mid-frame.
    No rings — completely photographic energy.
    """
    if photo_bg is not None:
        img = photo_bg.copy()
    else:
        img = Image.new("RGBA", (W, H), (*BG_DARK, 255))

    # Dark gradient rising from bottom — photo visible in top ~40%
    grad = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grad)
    grad_start = int(H * 0.28)
    for y_g in range(grad_start, H):
        t = (y_g - grad_start) / (H - grad_start)
        alpha = int(min(255, t * t * 235))
        gd.line([(0, y_g), (W, y_g)], fill=(*BG_DARK, alpha))
    img.alpha_composite(grad)

    draw = ImageDraw.Draw(img)

    # ── Top bar ──
    draw.rectangle([(0, 0), (W, BAR_H)], fill=(*GREEN, 255))
    bar_font = _fnt(GEIST_B, 22)
    bar_text = "FREE EARLY ACCESS  ·  scoringzone.net"
    bt_w = int(draw.textlength(bar_text, font=bar_font))
    draw.text(((W - bt_w) // 2, (BAR_H - 22) // 2), bar_text, fill=BAR_TEXT, font=bar_font)

    # ── Corner brackets (top only) ──
    _draw_corner_brackets(draw, W, H, arm=28, inset=60)

    # ── Drill label chip — top left ──
    dl_font = _fnt(GEIST_B, 20)
    dl_w = int(draw.textlength(drill_label, font=dl_font)) + 24
    draw.rounded_rectangle([(56, BAR_H + 22), (56 + dl_w, BAR_H + 56)], radius=3, fill=(*GREEN, 255))
    draw.text((68, BAR_H + 28), drill_label, fill=BAR_TEXT, font=dl_font)

    # ── Score badge top-right ──
    sc_num  = _fnt(BARLOW_XB, 52)
    sc_lbl  = _fnt(GEIST_R, 17)
    sx = W - 160
    draw.text((sx, BAR_H + 18), f"{opportunity_score:.0f}", fill=(*GREEN, 255), font=sc_num)
    draw.text((sx, BAR_H + 74), "/ 100", fill=(*TEXT_GHOST, 255), font=sc_lbl)
    sym = {"rising": "↑ RISING", "falling": "↓ FALLING"}.get(trend_direction, "→ STEADY")
    col = GREEN if trend_direction == "rising" else (200, 200, 200)
    draw.text((sx, BAR_H + 94), sym, fill=(*col, 230), font=sc_lbl)

    # ── Mid-frame: stat floats just above the text zone ──
    stat_y = int(H * 0.50)
    stat_font = _fnt(BARLOW_XB, 100)
    lbl_font  = _fnt(GEIST_R, 26)
    sw = int(draw.textlength(stat, font=stat_font))

    # Glow behind stat
    glow_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd2 = ImageDraw.Draw(glow_layer)
    gd2.text((60, stat_y), stat, fill=(*GREEN, 80), font=stat_font)
    img.alpha_composite(glow_layer.filter(ImageFilter.GaussianBlur(radius=18)))

    draw = ImageDraw.Draw(img)
    draw.text((60, stat_y), stat, fill=(*GREEN, 255), font=stat_font)
    draw.text((60 + sw + 20, stat_y + 40), stat_lbl, fill=(*TEXT_MID, 210), font=lbl_font)

    # Thin rule between stat and headline
    rule_y = stat_y + 116
    draw.rectangle([(56, rule_y), (W - 56, rule_y + 1)], fill=(*GREEN, 60))

    # ── Headline at bottom — big, left-anchored ──
    hfont = _fnt(BARLOW_XB, 122)
    hs = 122
    lines = _wrap(topic, hfont, W - 72)
    if len(lines) > 2:
        hfont = _fnt(BARLOW_XB, 86)
        hs = 86
        lines = _wrap(topic, hfont, W - 72)
    line_h = int(hs * 1.04)

    # Stack from bottom up
    footer_reserve = 62
    total_text_h = len(lines) * line_h
    y_hl = H - footer_reserve - total_text_h - 12

    txt_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    td = ImageDraw.Draw(txt_layer)
    for i, line in enumerate(lines):
        col_t = TEXT_PURE if i == 0 else GREEN_HI
        td.text((56, y_hl + i * line_h), line, fill=(*col_t, 255), font=hfont)
    img.alpha_composite(txt_layer)

    draw = ImageDraw.Draw(img)

    # ── Footer bar ──
    footer_y = H - footer_reserve
    draw.rectangle([(0, footer_y), (W, H)], fill=(0, 0, 0, 255))
    draw.rectangle([(0, footer_y), (W, footer_y + 2)], fill=(*GREEN, 160))
    ff = _fnt(BARLOW_B, 28)
    ft = "FREE ACCESS IS NOW LIVE!!  ·  Visit ScoringZone.net"
    ft_w = int(draw.textlength(ft, font=ff))
    draw.text(((W - ft_w) // 2, footer_y + 14), ft, fill=(*GREEN, 255), font=ff)

    _draw_vignette(img)
    img_rgb = img.convert("RGB")
    img_rgb = ImageEnhance.Contrast(img_rgb).enhance(1.12)
    img_rgb = ImageEnhance.Sharpness(img_rgb).enhance(1.12)
    return img_rgb


def _variant_data_readout(
    topic: str,
    opportunity_score: float,
    trend_direction: str,
    bullets: list[str],
    stat: str,
    stat_lbl: str,
    drill_label: str,
    logo: Image.Image | None,
    photo_bg: Image.Image | None = None,
) -> Image.Image:
    """
    Variant 2: Data Readout / Technical Interface
    Top: logo centred with rings. Bottom: structured data in GeistMono.
    Feels like a performance analytics instrument panel.
    """
    if photo_bg is not None:
        img = photo_bg.copy()
    else:
        img = Image.new("RGBA", (W, H), (*BG_DARK, 255))

    # Grid (denser — feels more technical)
    grid_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    _draw_grid(ImageDraw.Draw(grid_layer), W, H, spacing=32)
    img.alpha_composite(grid_layer)

    # Centre rings (top half)
    _draw_concentric_rings(img, cx=W // 2, cy=int(H * 0.32), base_r=240)

    # Horizontal separator lines
    draw = ImageDraw.Draw(img)
    sep_y = int(H * 0.57)
    draw.rectangle([(0, sep_y), (W, sep_y + 1)], fill=(*GREEN, 60))
    draw.rectangle([(0, sep_y + 3), (W, sep_y + 4)], fill=(*GREEN, 20))

    # ── Top bar ──
    draw.rectangle([(0, 0), (W, BAR_H)], fill=(*GREEN, 255))
    draw.rectangle([(0, BAR_H), (W, BAR_H + 2)], fill=(0, 30, 0, 220))
    bar_font = _fnt(GEIST_B, 22)
    bar_text = "FREE EARLY ACCESS  ·  scoringzone.net"
    bt_w = int(draw.textlength(bar_text, font=bar_font))
    draw.text(((W - bt_w) // 2, (BAR_H - 22) // 2), bar_text, fill=BAR_TEXT, font=bar_font)

    # ── Corner brackets ──
    _draw_corner_brackets(draw, W, H, arm=30, inset=80)

    # ── Drill label centred under rings ──
    dl_font = _fnt(GEIST_B, 22)
    dl_w = int(draw.textlength(drill_label, font=dl_font)) + 32
    draw.rounded_rectangle(
        [(W // 2 - dl_w // 2, sep_y - 44), (W // 2 + dl_w // 2, sep_y - 10)],
        radius=4, fill=(*GREEN, 255)
    )
    draw.text(
        (W // 2 - dl_w // 2 + 16, sep_y - 40),
        drill_label, fill=BAR_TEXT, font=dl_font
    )

    # ── Headline (Barlow, left-aligned, below separator) ──
    y = sep_y + 28
    hfont = _fnt(BARLOW_XB, 92)
    hs = 92
    lines = _wrap(topic, hfont, W - 120)
    line_h = int(hs * 1.06)

    txt_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    td = ImageDraw.Draw(txt_layer)
    for i, line in enumerate(lines):
        col = TEXT_PURE if i == 0 else GREEN_HI
        td.text((60, y), line, fill=(*col, 255), font=hfont)
        y += line_h
    img.alpha_composite(txt_layer)

    draw = ImageDraw.Draw(img)
    y += 8

    # ── Stat row ──
    s_big  = _fnt(BARLOW_XB, 72)
    s_lbl  = _fnt(GEIST_R, 22)
    draw.text((60, y), stat, fill=(*GREEN, 255), font=s_big)
    sw = int(draw.textlength(stat, font=s_big))
    draw.text((60 + sw + 20, y + 28), stat_lbl, fill=(*TEXT_MID, 255), font=s_lbl)
    y += 82

    # ── Bullets as GeistMono technical readout ──
    bf = _fnt(GEIST_R, 24)
    for i, bullet in enumerate(bullets):
        idx_str = f"[{i+1:02d}]"
        draw.text((60, y), idx_str, fill=(*TEXT_GHOST, 255), font=bf)
        draw.text((124, y), bullet, fill=(*TEXT_PURE, 255), font=bf)
        y += 42

    # ── Opportunity score — right column ──
    oc_font  = _fnt(BARLOW_XB, 52)
    oc_label = _fnt(GEIST_R, 18)
    draw.text((W - 200, sep_y + 28), f"{opportunity_score:.0f}", fill=(*GREEN, 255), font=oc_font)
    draw.text((W - 200, sep_y + 84), "SCORE/100", fill=(*TEXT_GHOST, 255), font=oc_label)
    sym = {"rising": "↑ RISING", "falling": "↓ FALLING"}.get(trend_direction, "→ STEADY")
    col = GREEN if trend_direction == "rising" else (200, 200, 200)
    draw.text((W - 200, sep_y + 108), sym, fill=(*col, 255), font=oc_label)

    # ── Bottom CTA ──
    cta_y = H - 108
    draw.rectangle([(0, cta_y), (W, cta_y + 62)], fill=(*GREEN, 255))
    cta1_font = _fnt(BARLOW_B, 32)
    cta2_font = _fnt(GEIST_R, 22)
    draw.text((48, cta_y + 6),  "Free early access now live!!", fill=(*BAR_TEXT, 255), font=cta1_font)
    draw.text((48, cta_y + 38), "scoringzone.net", fill=(*BAR_TEXT, 200), font=cta2_font)

    # Brand bar
    bar2_y = H - 46
    draw.rectangle([(0, bar2_y), (W, H)], fill=(*BG_DARK, 255))
    draw.rectangle([(0, bar2_y), (W, bar2_y + 2)], fill=(*GREEN, 180))
    bfont = _fnt(GEIST_B, 20)
    brand_text = "● SCORING ZONE  ·  scoringzone.net"
    bt_w2 = int(draw.textlength(brand_text, font=bfont))
    draw.text(((W - bt_w2) // 2, bar2_y + 12), brand_text, fill=(*GREEN, 200), font=bfont)

    _draw_vignette(img)

    img_rgb = img.convert("RGB")
    img_rgb = ImageEnhance.Contrast(img_rgb).enhance(1.10)
    img_rgb = ImageEnhance.Sharpness(img_rgb).enhance(1.12)
    return img_rgb


def _variant_precision_scope(
    topic: str,
    opportunity_score: float,
    trend_direction: str,
    bullets: list[str],
    stat: str,
    stat_lbl: str,
    drill_label: str,
    logo: Image.Image | None,
    photo_bg: Image.Image | None = None,
) -> Image.Image:
    """
    Variant 3: Corner Box
    Full-bleed photo with moderate overlay.
    All content locked into a neon-bordered card anchored to the bottom-left.
    Photo breathes above and to the right. Minimal, editorial.
    """
    if photo_bg is not None:
        img = photo_bg.copy()
        ov = Image.new("RGBA", (W, H), (*BG_DARK, 130))
        img.alpha_composite(ov)
    else:
        img = Image.new("RGBA", (W, H), (*BG_DARK, 255))

    draw = ImageDraw.Draw(img)

    # ── Top bar ──
    draw.rectangle([(0, 0), (W, BAR_H)], fill=(*GREEN, 255))
    bar_font = _fnt(GEIST_B, 22)
    bar_text = "FREE EARLY ACCESS  ·  scoringzone.net"
    bt_w = int(draw.textlength(bar_text, font=bar_font))
    draw.text(((W - bt_w) // 2, (BAR_H - 22) // 2), bar_text, fill=BAR_TEXT, font=bar_font)

    # ── Neon-bordered content card — bottom left ──
    card_pad   = 48
    card_x     = card_pad
    card_w     = int(W * 0.72)
    card_bot   = H - 52
    card_inner = 28  # padding inside card

    # Measure content height first
    hfont = _fnt(BARLOW_XB, 96)
    hs = 96
    lines = _wrap(topic, hfont, card_w - card_inner * 2 - 16)
    if len(lines) > 3:
        hfont = _fnt(BARLOW_XB, 72)
        hs = 72
        lines = _wrap(topic, hfont, card_w - card_inner * 2 - 16)
    line_h = int(hs * 1.05)
    content_h = (
        len(lines) * line_h
        + 12        # gap
        + 38        # drill chip
        + 12        # gap
        + 72        # stat row
        + len(bullets) * 38
        + card_inner * 2
    )
    card_top = card_bot - content_h

    # Semi-dark fill behind card
    card_bg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cbd = ImageDraw.Draw(card_bg)
    cbd.rounded_rectangle(
        [(card_x, card_top), (card_x + card_w, card_bot)],
        radius=6, fill=(*BG_DARK, 215)
    )
    img.alpha_composite(card_bg)

    # Neon border
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle(
        [(card_x, card_top), (card_x + card_w, card_bot)],
        radius=6, outline=(*GREEN, 180), width=2
    )
    # Left accent bar
    draw.rectangle([(card_x, card_top + 6), (card_x + 3, card_bot - 6)], fill=(*GREEN, 255))

    # Content inside card
    cx = card_x + card_inner + 8
    cy = card_top + card_inner

    # Headline
    txt_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    td = ImageDraw.Draw(txt_layer)
    for i, line in enumerate(lines):
        col_t = TEXT_PURE if i == 0 else GREEN_HI
        td.text((cx, cy), line, fill=(*col_t, 255), font=hfont)
        cy += line_h
    img.alpha_composite(txt_layer)
    draw = ImageDraw.Draw(img)

    cy += 10
    # Drill chip
    dl_font = _fnt(GEIST_B, 18)
    dl_w = int(draw.textlength(drill_label, font=dl_font)) + 20
    draw.rounded_rectangle([(cx, cy), (cx + dl_w, cy + 32)], radius=3, fill=(*GREEN, 255))
    draw.text((cx + 10, cy + 6), drill_label, fill=BAR_TEXT, font=dl_font)
    cy += 44

    # Stat inline with label
    sf = _fnt(BARLOW_XB, 64)
    sl = _fnt(GEIST_R, 19)
    draw.text((cx, cy), stat, fill=(*GREEN, 255), font=sf)
    sw = int(draw.textlength(stat, font=sf))
    draw.text((cx + sw + 16, cy + 22), stat_lbl, fill=(*TEXT_MID, 210), font=sl)
    cy += 72

    # Bullets compact
    bf = _fnt(GEIST_R, 20)
    for bullet in bullets[:3]:
        draw.rectangle([(cx, cy + 6), (cx + 7, cy + 14)], fill=(*GREEN, 200))
        draw.text((cx + 16, cy), bullet, fill=(*TEXT_PURE, 220), font=bf)
        cy += 34

    # ── Score + trend — top right of image ──
    sc_num = _fnt(BARLOW_XB, 56)
    sc_lbl = _fnt(GEIST_R, 17)
    sx = W - 160
    draw.text((sx, BAR_H + 20), f"{opportunity_score:.0f}", fill=(*GREEN, 255), font=sc_num)
    draw.text((sx, BAR_H + 80), "/ 100", fill=(*TEXT_GHOST, 200), font=sc_lbl)
    sym = {"rising": "↑ RISING", "falling": "↓ FALLING"}.get(trend_direction, "→ STEADY")
    col = GREEN if trend_direction == "rising" else (200, 200, 200)
    draw.text((sx, BAR_H + 100), sym, fill=(*col, 230), font=sc_lbl)

    # ── Thin bottom brand strip ──
    draw.rectangle([(0, H - 50), (W, H)], fill=(0, 0, 0, 220))
    draw.rectangle([(0, H - 50), (W, H - 49)], fill=(*GREEN, 100))
    bf2 = _fnt(GEIST_B, 18)
    bt2 = "● SCORING ZONE  ·  scoringzone.net"
    bt2_w = int(draw.textlength(bt2, font=bf2))
    draw.text(((W - bt2_w) // 2, H - 34), bt2, fill=(*GREEN, 180), font=bf2)

    _draw_vignette(img)
    img_rgb = img.convert("RGB")
    img_rgb = ImageEnhance.Contrast(img_rgb).enhance(1.10)
    img_rgb = ImageEnhance.Sharpness(img_rgb).enhance(1.12)
    return img_rgb


# ── Additional Variants (4-8) ──────────────────────────────────────────────────

def _variant_split_screen(
    topic: str,
    opportunity_score: float,
    trend_direction: str,
    bullets: list[str],
    stat: str,
    stat_lbl: str,
    drill_label: str,
    logo: Image.Image | None,
    photo_bg: Image.Image | None = None,
) -> Image.Image:
    """
    Variant 4: Split Screen
    Left panel: pure dark brand space with headline + data.
    Right panel: golf photo exposed with minimal overlay — the course breathes.
    A hard vertical neon line splits the two worlds.
    """
    base = Image.new("RGBA", (W, H), (*BG_DARK, 255))

    # Right panel — photo with lighter overlay so it shows strongly
    if photo_bg is not None:
        # Re-composite with lower alpha overlay so photo bleeds through more
        split_x = int(W * 0.48)
        right_crop = photo_bg.crop((split_x, 0, W, H))
        # Reduce the existing overlay by blending with a semi-transparent black
        photo_light = Image.new("RGBA", right_crop.size, (2, 6, 2, 60))
        right_panel = Image.alpha_composite(right_crop, photo_light)
        base.paste(right_panel.convert("RGB"), (split_x, 0))
        base = base.convert("RGBA")

    # Left panel dark overlay (full left half)
    split_x = int(W * 0.48)
    left_panel = Image.new("RGBA", (split_x, H), (*BG_DARK, 242))
    base.alpha_composite(left_panel)

    # Grid on left panel only
    grid_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    _draw_grid(ImageDraw.Draw(grid_layer), split_x, H, spacing=36)
    base.alpha_composite(grid_layer)

    # Vertical neon divider
    div_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dd = ImageDraw.Draw(div_layer)
    dd.line([(split_x, BAR_H), (split_x, H)], fill=(*GREEN, 220), width=2)
    # Glow pass
    div_blur = div_layer.filter(ImageFilter.GaussianBlur(radius=8))
    ba = np.array(div_blur, dtype=np.float32)
    ba[:, :, 3] *= 0.5
    base.alpha_composite(Image.fromarray(ba.clip(0, 255).astype(np.uint8), "RGBA"))
    base.alpha_composite(div_layer)

    draw = ImageDraw.Draw(base)

    # ── Top bar ──
    draw.rectangle([(0, 0), (W, BAR_H)], fill=(*GREEN, 255))
    bar_font = _fnt(GEIST_B, 22)
    bar_text = "FREE EARLY ACCESS  ·  scoringzone.net"
    bt_w = int(draw.textlength(bar_text, font=bar_font))
    draw.text(((W - bt_w) // 2, (BAR_H - 22) // 2), bar_text, fill=BAR_TEXT, font=bar_font)

    # ── Left panel content ──
    pad = 62
    y = BAR_H + 36

    # Drill chip
    dl_font = _fnt(GEIST_B, 20)
    dl_w = int(draw.textlength(drill_label, font=dl_font)) + 24
    draw.rounded_rectangle([(pad, y), (pad + dl_w, y + 36)], radius=3, fill=(*GREEN, 255))
    draw.text((pad + 12, y + 6), drill_label, fill=BAR_TEXT, font=dl_font)
    y += 52

    # Headline
    hfont = _fnt(BARLOW_XB, 112)
    hs = 112
    lines = _wrap(topic, hfont, split_x - pad - 24)
    if len(lines) > 2:
        hfont = _fnt(BARLOW_XB, 82)
        hs = 82
        lines = _wrap(topic, hfont, split_x - pad - 24)
    line_h = int(hs * 1.06)

    txt_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    td = ImageDraw.Draw(txt_layer)
    for i, line in enumerate(lines):
        col = TEXT_PURE if i == 0 else GREEN_HI
        td.text((pad, y), line, fill=(*col, 255), font=hfont)
        y += line_h
    base.alpha_composite(txt_layer)
    draw = ImageDraw.Draw(base)

    # Thin horizontal rule
    y += 16
    draw.rectangle([(pad, y), (split_x - 32, y + 1)], fill=(*GREEN, 80))
    y += 18

    # Big stat
    sf = _fnt(BARLOW_XB, 80)
    sl = _fnt(GEIST_R, 20)
    draw.text((pad, y), stat, fill=(*GREEN, 255), font=sf)
    y_sl = y + 84
    draw.text((pad, y_sl), stat_lbl, fill=(*TEXT_MID, 255), font=sl)
    y = y_sl + 34

    # Bullets — clipped to left panel width so they never bleed into photo
    bf = _fnt(GEIST_R, 22)
    max_bullet_w = split_x - pad - 32  # available text width inside left panel
    for bullet in bullets[:3]:
        # Truncate text so it fits
        btext = bullet
        while int(draw.textlength(btext, font=bf)) > max_bullet_w and len(btext) > 4:
            btext = btext[:-4].rstrip() + "…"
        draw.rectangle([(pad, y + 7), (pad + 8, y + 17)], fill=(*GREEN, 200))
        draw.text((pad + 20, y), btext, fill=(*TEXT_PURE, 230), font=bf)
        y += 38

    # Trend indicator on right panel (bottom right)
    sym = {"rising": "↑ RISING", "falling": "↓ FALLING"}.get(trend_direction, "→ STEADY")
    col = GREEN if trend_direction == "rising" else (200, 200, 200)
    tf = _fnt(GEIST_B, 20)
    tw = int(draw.textlength(sym, font=tf))
    draw.text((W - tw - 36, H - 90), sym, fill=(*col, 200), font=tf)

    # Logo small on right panel, upper right
    if logo:
        ls = int(W * 0.22)
        lh_px = int(logo.height * (ls / logo.width))
        lsm = logo.resize((ls, lh_px), Image.LANCZOS)
        lx = split_x + (W - split_x) // 2 - ls // 2
        ly = BAR_H + 30
        base.alpha_composite(lsm, (lx, ly))

    # ── Bottom bar ──
    footer_h = 54
    footer_y = H - footer_h
    draw.rectangle([(0, footer_y), (W, H)], fill=(0, 0, 0, 255))
    draw.rectangle([(0, footer_y), (W, footer_y + 2)], fill=(*GREEN, 140))
    ff = _fnt(BARLOW_B, 28)
    ft = "FREE ACCESS IS NOW LIVE!!  ·  Visit ScoringZone.net"
    ft_w = int(draw.textlength(ft, font=ff))
    draw.text(((W - ft_w) // 2, footer_y + 12), ft, fill=(*GREEN, 255), font=ff)

    _draw_vignette(base)
    img_rgb = base.convert("RGB")
    img_rgb = ImageEnhance.Contrast(img_rgb).enhance(1.08)
    img_rgb = ImageEnhance.Sharpness(img_rgb).enhance(1.12)
    return img_rgb


def _variant_minimalist(
    topic: str,
    opportunity_score: float,
    trend_direction: str,
    bullets: list[str],
    stat: str,
    stat_lbl: str,
    drill_label: str,
    logo: Image.Image | None,
    photo_bg: Image.Image | None = None,
) -> Image.Image:
    """
    Variant 5: Exposed
    Photo shows fully — light overlay only. One massive stat top-center.
    Topic in bold at the bottom. Maximum photographic impact.
    """
    if photo_bg is not None:
        img = photo_bg.copy()
        # Light overlay — photo breathes strongly through
        light = Image.new("RGBA", (W, H), (*BG_DARK, 95))
        img.alpha_composite(light)
    else:
        img = Image.new("RGBA", (W, H), (*BG_DARK, 255))

    # Dark vignette corners only — keep center open
    vig = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for radius in range(0, min(W, H) // 2, 4):
        t = 1 - (radius / (min(W, H) / 2))
        alpha = int(t * t * 160)
        if alpha <= 0:
            break
        ImageDraw.Draw(vig).ellipse(
            [(W // 2 - radius, H // 2 - radius), (W // 2 + radius, H // 2 + radius)],
            outline=(0, 0, 0, alpha), width=4
        )
    img.alpha_composite(vig)

    draw = ImageDraw.Draw(img)

    # ── Top bar ──
    draw.rectangle([(0, 0), (W, BAR_H)], fill=(*GREEN, 255))
    bar_font = _fnt(GEIST_B, 22)
    bar_text = "FREE EARLY ACCESS  ·  scoringzone.net"
    bt_w = int(draw.textlength(bar_text, font=bar_font))
    draw.text(((W - bt_w) // 2, (BAR_H - 22) // 2), bar_text, fill=BAR_TEXT, font=bar_font)

    # ── Massive stat centered near top third ──
    stat_font = _fnt(BARLOW_XB, 220)
    while int(draw.textlength(stat, font=stat_font)) > W - 60:
        stat_font = _fnt(BARLOW_XB, stat_font.size - 20)
    sw = int(draw.textlength(stat, font=stat_font))
    sh = stat_font.size
    stat_y = BAR_H + 40

    # Dark halo behind stat for legibility
    halo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    hd = ImageDraw.Draw(halo)
    hd.text(((W - sw) // 2, stat_y), stat, fill=(*BG_DARK, 180), font=stat_font)
    img.alpha_composite(halo.filter(ImageFilter.GaussianBlur(radius=28)))

    # Glow
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.text(((W - sw) // 2, stat_y), stat, fill=(*GREEN, 55), font=stat_font)
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(radius=20)))

    txt_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    td = ImageDraw.Draw(txt_layer)
    td.text(((W - sw) // 2, stat_y), stat, fill=(*GREEN, 255), font=stat_font)
    img.alpha_composite(txt_layer)

    draw = ImageDraw.Draw(img)

    # Stat label below
    sl_font = _fnt(GEIST_B, 28)
    sl_up = stat_lbl.upper()
    sl_w = int(draw.textlength(sl_up, font=sl_font))
    sl_y = stat_y + sh + 8
    draw.text(((W - sl_w) // 2, sl_y), sl_up, fill=(*TEXT_MID, 210), font=sl_font)

    # ── Thin rule at ~65% height ──
    rule_y = int(H * 0.65)
    draw.rectangle([(64, rule_y), (W - 64, rule_y + 1)], fill=(*GREEN, 70))

    # ── Drill chip centered on rule ──
    dl_font = _fnt(GEIST_B, 20)
    dl_w = int(draw.textlength(drill_label, font=dl_font)) + 24
    dl_x = (W - dl_w) // 2
    draw.rounded_rectangle([(dl_x, rule_y - 18), (dl_x + dl_w, rule_y + 18)], radius=3, fill=(*GREEN, 255))
    draw.text((dl_x + 12, rule_y - 12), drill_label, fill=BAR_TEXT, font=dl_font)

    # ── Topic headline bottom ──
    hfont = _fnt(BARLOW_XB, 88)
    hs = 88
    lines = _wrap(topic, hfont, W - 80)
    if len(lines) > 2:
        hfont = _fnt(BARLOW_XB, 64)
        hs = 64
        lines = _wrap(topic, hfont, W - 80)
    line_h = int(hs * 1.04)
    footer_h = 58
    total_hl = len(lines) * line_h
    hl_y = H - footer_h - total_hl - 12

    hl_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    hld = ImageDraw.Draw(hl_layer)
    # Dark shadow for legibility
    for i, line in enumerate(lines):
        shadow_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        sd = ImageDraw.Draw(shadow_layer)
        sd.text((40, hl_y + i * line_h), line, fill=(*BG_DARK, 180), font=hfont)
        hl_layer.alpha_composite(shadow_layer.filter(ImageFilter.GaussianBlur(radius=12)))
    for i, line in enumerate(lines):
        col_t = TEXT_PURE if i == 0 else GREEN_HI
        hld.text((40, hl_y + i * line_h), line, fill=(*col_t, 255), font=hfont)
    img.alpha_composite(hl_layer)

    draw = ImageDraw.Draw(img)

    # Score + trend bottom right
    sc_font = _fnt(BARLOW_XB, 42)
    sc_lbl2 = _fnt(GEIST_R, 16)
    draw.text((W - 148, hl_y + 4), f"{opportunity_score:.0f}", fill=(*GREEN, 230), font=sc_font)
    draw.text((W - 148, hl_y + 50), "/ 100", fill=(*TEXT_GHOST, 180), font=sc_lbl2)
    sym = {"rising": "↑ RISING", "falling": "↓ FALLING"}.get(trend_direction, "→ STEADY")
    col = GREEN if trend_direction == "rising" else (200, 200, 200)
    draw.text((W - 148, hl_y + 70), sym, fill=(*col, 200), font=sc_lbl2)

    # ── Footer ──
    footer_y = H - footer_h
    draw.rectangle([(0, footer_y), (W, H)], fill=(0, 0, 0, 255))
    draw.rectangle([(0, footer_y), (W, footer_y + 2)], fill=(*GREEN, 150))
    ff = _fnt(BARLOW_B, 28)
    ft = "FREE ACCESS IS NOW LIVE!!  ·  Visit ScoringZone.net"
    ft_w = int(draw.textlength(ft, font=ff))
    draw.text(((W - ft_w) // 2, footer_y + 14), ft, fill=(*GREEN, 255), font=ff)

    img_rgb = img.convert("RGB")
    img_rgb = ImageEnhance.Contrast(img_rgb).enhance(1.14)
    img_rgb = ImageEnhance.Sharpness(img_rgb).enhance(1.12)
    return img_rgb


def _variant_headline_card(
    topic: str,
    opportunity_score: float,
    trend_direction: str,
    bullets: list[str],
    stat: str,
    stat_lbl: str,
    drill_label: str,
    logo: Image.Image | None,
    photo_bg: Image.Image | None = None,
) -> Image.Image:
    """
    Variant 6: Triple Band Score Card
    Three horizontal bands stacked: vivid photo strip on top (no overlay),
    inverted neon green band in the middle carrying the big stat in dark type,
    pure dark band at the bottom with headline + bullets.
    The colour inversion on the middle band is unique and scroll-stopping.
    """
    img = Image.new("RGBA", (W, H), (*BG_DARK, 255))

    # Band boundaries
    band1_y = 0           # top of photo strip (below top bar)
    band1_h = int(H * 0.38)   # photo takes ~38% of height
    band2_y = band1_h
    band2_h = int(H * 0.20)   # neon band ~20%
    band3_y = band2_y + band2_h  # dark content band fills remainder

    # ── Band 1: vivid photo — no dark overlay ──
    if photo_bg is not None:
        # Use the raw photo_bg but strip the existing vignette by pasting raw photo
        photo_strip = photo_bg.crop((0, BAR_H, W, band1_h))
        # Brighten it slightly so it really pops
        bright = ImageEnhance.Brightness(photo_strip.convert("RGB")).enhance(1.15)
        sat = ImageEnhance.Color(bright).enhance(1.3)
        img.paste(sat, (0, BAR_H))
        img = img.convert("RGBA")

    draw = ImageDraw.Draw(img)

    # ── Top bar (sits above photo) ──
    draw.rectangle([(0, 0), (W, BAR_H)], fill=(*GREEN, 255))
    bar_font = _fnt(GEIST_B, 22)
    bar_text = "FREE EARLY ACCESS  ·  scoringzone.net"
    bt_w = int(draw.textlength(bar_text, font=bar_font))
    draw.text(((W - bt_w) // 2, (BAR_H - 22) // 2), bar_text, fill=BAR_TEXT, font=bar_font)

    # Drill chip overlaid bottom-left of photo strip
    dl_font = _fnt(GEIST_B, 20)
    dl_w = int(draw.textlength(drill_label, font=dl_font)) + 24
    draw.rounded_rectangle([(52, band1_h - 48), (52 + dl_w, band1_h - 14)],
                            radius=3, fill=(*GREEN, 255))
    draw.text((62, band1_h - 44), drill_label, fill=BAR_TEXT, font=dl_font)

    # ── Band 2: solid neon green — inverted colours ──
    draw.rectangle([(0, band2_y), (W, band2_y + band2_h)], fill=(*GREEN, 255))

    # Stat in dark type on the neon band
    sf_big = _fnt(BARLOW_XB, 110)
    sf_lbl = _fnt(GEIST_B, 24)
    stat_w = int(draw.textlength(stat, font=sf_big))
    stat_lbl_w = int(draw.textlength(stat_lbl, font=sf_lbl))

    # Vertically centre in band2
    stat_x = (W - stat_w - stat_lbl_w - 24) // 2
    stat_y = band2_y + (band2_h - 110) // 2 - 6
    draw.text((stat_x, stat_y), stat, fill=BAR_TEXT, font=sf_big)
    draw.text((stat_x + stat_w + 18, stat_y + 50), stat_lbl, fill=(0, 40, 0), font=sf_lbl)

    # Thin dark border lines on band2
    draw.rectangle([(0, band2_y), (W, band2_y + 3)], fill=(0, 40, 0, 180))
    draw.rectangle([(0, band2_y + band2_h - 3), (W, band2_y + band2_h)], fill=(0, 40, 0, 180))

    # ── Band 3: dark content ──
    pad = 60
    y = band3_y + 32

    # Headline
    hfont = _fnt(BARLOW_XB, 104)
    hs = 104
    lines = _wrap(topic, hfont, W - pad * 2)
    if len(lines) > 2:
        hfont = _fnt(BARLOW_XB, 78)
        hs = 78
        lines = _wrap(topic, hfont, W - pad * 2)
    line_h = int(hs * 1.04)

    txt_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    td = ImageDraw.Draw(txt_layer)
    for i, line in enumerate(lines):
        col_hl = TEXT_PURE if i == 0 else GREEN_HI
        td.text((pad, y), line, fill=(*col_hl, 255), font=hfont)
        y += line_h
    img.alpha_composite(txt_layer)
    draw = ImageDraw.Draw(img)

    y += 14
    draw.rectangle([(pad, y), (W - pad, y + 1)], fill=(*GREEN, 50))
    y += 20

    # Bullets — two max, clean and tight
    bf = _fnt(GEIST_R, 23)
    max_bw = W - pad * 2 - 24
    for bullet in bullets[:2]:
        btext = bullet
        while int(draw.textlength(btext, font=bf)) > max_bw and len(btext) > 4:
            btext = btext[:-4].rstrip() + "…"
        draw.rectangle([(pad, y + 8), (pad + 8, y + 18)], fill=(*GREEN, 200))
        draw.text((pad + 20, y), btext, fill=(*TEXT_MID, 230), font=bf)
        y += 40

    # ── Footer strip ──
    footer_y = H - 52
    draw.rectangle([(0, footer_y), (W, H)], fill=(0, 0, 0, 255))
    draw.rectangle([(0, footer_y), (W, footer_y + 2)], fill=(*GREEN, 130))
    ff = _fnt(BARLOW_B, 26)
    ft = "FREE ACCESS IS NOW LIVE!!  ·  ScoringZone.net"
    ft_w = int(draw.textlength(ft, font=ff))
    draw.text(((W - ft_w) // 2, footer_y + 12), ft, fill=(*GREEN, 255), font=ff)

    img_rgb = img.convert("RGB")
    img_rgb = ImageEnhance.Contrast(img_rgb).enhance(1.08)
    img_rgb = ImageEnhance.Sharpness(img_rgb).enhance(1.1)
    return img_rgb


def _variant_quote_pull(
    topic: str,
    opportunity_score: float,
    trend_direction: str,
    bullets: list[str],
    stat: str,
    stat_lbl: str,
    drill_label: str,
    logo: Image.Image | None,
    photo_bg: Image.Image | None = None,
) -> Image.Image:
    """
    Variant 7: Quote Pull
    One punchy insight in massive centered type between giant quote marks.
    The course photograph breathes behind it. Scroll-stopping stillness.
    """
    if photo_bg is not None:
        img = photo_bg.copy()
        ov = Image.new("RGBA", (W, H), (*BG_DARK, 155))
        img.alpha_composite(ov)
    else:
        img = Image.new("RGBA", (W, H), (*BG_DARK, 255))

    draw = ImageDraw.Draw(img)

    # ── Top bar ──
    draw.rectangle([(0, 0), (W, BAR_H)], fill=(*GREEN, 255))
    bar_font = _fnt(GEIST_B, 22)
    bar_text = "FREE EARLY ACCESS  ·  scoringzone.net"
    bt_w = int(draw.textlength(bar_text, font=bar_font))
    draw.text(((W - bt_w) // 2, (BAR_H - 22) // 2), bar_text, fill=BAR_TEXT, font=bar_font)

    # ── Giant opening quote mark ──
    q_font = _fnt(BARLOW_XB, 280)
    q_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    qd = ImageDraw.Draw(q_layer)
    qd.text((52, BAR_H - 60), "\u201c", fill=(*GREEN, 38), font=q_font)
    img.alpha_composite(q_layer)
    draw = ImageDraw.Draw(img)

    # ── Centered quote text ──
    # Use stat_lbl as the insight (it's short and punchy)
    insight_lines = [
        stat + "  " + stat_lbl.upper(),
    ]
    # Also add the topic as sub-line
    pad = 80
    center_y = int(H * 0.38)

    # Large centered stat
    big_font = _fnt(BARLOW_XB, 120)
    bw = int(draw.textlength(stat, font=big_font))
    stat_x = (W - bw) // 2

    # Glow
    g_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd2 = ImageDraw.Draw(g_layer)
    gd2.text((stat_x, center_y), stat, fill=(*GREEN, 80), font=big_font)
    gb = g_layer.filter(ImageFilter.GaussianBlur(radius=24))
    img.alpha_composite(gb)

    txt_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    td = ImageDraw.Draw(txt_layer)
    td.text((stat_x, center_y), stat, fill=(*TEXT_PURE, 255), font=big_font)
    img.alpha_composite(txt_layer)
    draw = ImageDraw.Draw(img)

    # Stat label
    sl_font = _fnt(GEIST_R, 30)
    sl_text = stat_lbl.upper()
    sl_w = int(draw.textlength(sl_text, font=sl_font))
    draw.text(((W - sl_w) // 2, center_y + 128), sl_text, fill=(*TEXT_MID, 220), font=sl_font)

    # Thin rule
    rule_y = center_y + 178
    draw.rectangle([((W - 200) // 2, rule_y), ((W + 200) // 2, rule_y + 1)], fill=(*GREEN, 90))

    # Topic below rule
    t_font = _fnt(BARLOW_XB, 56)
    t_lines = _wrap(topic, t_font, W - pad * 2)
    ty = rule_y + 20
    txt2 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    t2d = ImageDraw.Draw(txt2)
    for line in t_lines[:2]:
        lw2 = int(t2d.textlength(line, font=t_font))
        t2d.text(((W - lw2) // 2, ty), line, fill=(*GREEN_HI, 255), font=t_font)
        ty += 60
    img.alpha_composite(txt2)
    draw = ImageDraw.Draw(img)

    # ── Scoring Zone tagline (rotates by topic hash) ──
    _SZ_TAGLINES = [
        "Pressure drills that build skills that transfer to the course.",
        "Scored challenges. Measurable results. Real improvement.",
        "Data-driven practice — know exactly what to work on next.",
        "Make practice competitive. Turn every session into a game.",
        "Structured scored practice beats aimless grinding every time.",
    ]
    tagline = _SZ_TAGLINES[hash(topic) % len(_SZ_TAGLINES)]
    tg_font = _fnt(GEIST_R, 19)
    tg_w = int(draw.textlength(tagline, font=tg_font))
    # Shrink if too wide
    if tg_w > W - 120:
        tg_font = _fnt(GEIST_R, 16)
        tg_w = int(draw.textlength(tagline, font=tg_font))
    draw.text(((W - tg_w) // 2, ty + 8), tagline, fill=(*TEXT_MID, 210), font=tg_font)

    attr_font = _fnt(GEIST_B, 17)
    attr_text = "— SCORING ZONE  ·  scoringzone.net"
    attr_w = int(draw.textlength(attr_text, font=attr_font))
    draw.text(((W - attr_w) // 2, ty + 36), attr_text, fill=(*TEXT_GHOST, 190), font=attr_font)

    # Drill chip bottom-left
    dl_font = _fnt(GEIST_B, 20)
    dl_w = int(draw.textlength(drill_label, font=dl_font)) + 24
    draw.rounded_rectangle([(pad, H - 90), (pad + dl_w, H - 58)], radius=3, fill=(*GREEN, 255))
    draw.text((pad + 12, H - 86), drill_label, fill=BAR_TEXT, font=dl_font)

    # Trend bottom-right
    sym = {"rising": "↑ RISING", "falling": "↓ FALLING"}.get(trend_direction, "→ STEADY")
    col_t = GREEN if trend_direction == "rising" else (200, 200, 200)
    tf = _fnt(GEIST_B, 20)
    tw = int(draw.textlength(sym, font=tf))
    draw.text((W - tw - pad, H - 86), sym, fill=(*col_t, 200), font=tf)

    # Bottom line
    draw.rectangle([(0, H - 46), (W, H)], fill=(0, 0, 0, 200))
    draw.rectangle([(0, H - 46), (W, H - 44)], fill=(*GREEN, 120))
    sf2 = _fnt(GEIST_B, 20)
    st2 = "● SCORING ZONE  ·  SHORT GAME PERFORMANCE TRACKING"
    sw2 = int(draw.textlength(st2, font=sf2))
    draw.text(((W - sw2) // 2, H - 36), st2, fill=(*GREEN, 180), font=sf2)

    _draw_vignette(img)
    img_rgb = img.convert("RGB")
    img_rgb = ImageEnhance.Contrast(img_rgb).enhance(1.08)
    img_rgb = ImageEnhance.Sharpness(img_rgb).enhance(1.14)
    return img_rgb


def _variant_cinematic(
    topic: str,
    opportunity_score: float,
    trend_direction: str,
    bullets: list[str],
    stat: str,
    stat_lbl: str,
    drill_label: str,
    logo: Image.Image | None,
    photo_bg: Image.Image | None = None,
) -> Image.Image:
    """
    Variant 8: Leaderboard
    Augusta-style scoreboard energy. Photo cropped into a circle top-right.
    Dark panel with ranked data rows below. Clean, authoritative.
    """
    img = Image.new("RGBA", (W, H), (*BG_DARK, 255))

    # Subtle dot grid texture
    grid_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grid_layer)
    for gx in range(0, W, 40):
        for gy in range(0, H, 40):
            gd.point((gx, gy), fill=(*GREEN, 10))
    img.alpha_composite(grid_layer)

    draw = ImageDraw.Draw(img)

    # ── Circle photo — top-right ──
    circle_r = 220
    circle_cx = int(W * 0.72)
    circle_cy = BAR_H + circle_r + 36

    if photo_bg is not None:
        # Crop a square from the photo centred on the subject
        src = photo_bg.convert("RGBA")
        # Crop to square
        sq_size = circle_r * 2
        src_sq = src.crop((
            max(0, circle_cx - circle_r),
            max(BAR_H, circle_cy - circle_r),
            min(W, circle_cx + circle_r),
            min(H, circle_cy + circle_r),
        )).resize((sq_size, sq_size), Image.LANCZOS)

        # Circular mask
        mask = Image.new("L", (sq_size, sq_size), 0)
        ImageDraw.Draw(mask).ellipse([(0, 0), (sq_size - 1, sq_size - 1)], fill=255)
        src_sq.putalpha(mask)

        paste_x = circle_cx - circle_r
        paste_y = circle_cy - circle_r
        img.alpha_composite(src_sq, (paste_x, paste_y))

    draw = ImageDraw.Draw(img)

    # Neon circle border
    draw.ellipse(
        [(circle_cx - circle_r - 3, circle_cy - circle_r - 3),
         (circle_cx + circle_r + 3, circle_cy + circle_r + 3)],
        outline=(*GREEN, 200), width=3
    )
    # Second ring (glow effect)
    draw.ellipse(
        [(circle_cx - circle_r - 10, circle_cy - circle_r - 10),
         (circle_cx + circle_r + 10, circle_cy + circle_r + 10)],
        outline=(*GREEN, 40), width=6
    )

    # ── Top bar ──
    draw.rectangle([(0, 0), (W, BAR_H)], fill=(*GREEN, 255))
    bar_font = _fnt(GEIST_B, 22)
    bar_text = "FREE EARLY ACCESS  ·  scoringzone.net"
    bt_w = int(draw.textlength(bar_text, font=bar_font))
    draw.text(((W - bt_w) // 2, (BAR_H - 22) // 2), bar_text, fill=BAR_TEXT, font=bar_font)

    # ── Left panel: headline ──
    pad = 56
    y = BAR_H + 32

    hfont = _fnt(BARLOW_XB, 108)
    hs = 108
    max_w = circle_cx - circle_r - pad - 24
    lines = _wrap(topic, hfont, max_w)
    if len(lines) > 3:
        hfont = _fnt(BARLOW_XB, 78)
        hs = 78
        lines = _wrap(topic, hfont, max_w)
    line_h = int(hs * 1.04)

    txt_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    td = ImageDraw.Draw(txt_layer)
    for i, line in enumerate(lines):
        col_t = TEXT_PURE if i == 0 else GREEN_HI
        td.text((pad, y), line, fill=(*col_t, 255), font=hfont)
        y += line_h
    img.alpha_composite(txt_layer)
    draw = ImageDraw.Draw(img)

    # Drill chip below headline
    dl_font = _fnt(GEIST_B, 19)
    dl_w = int(draw.textlength(drill_label, font=dl_font)) + 22
    draw.rounded_rectangle([(pad, y + 10), (pad + dl_w, y + 42)], radius=3, fill=(*GREEN, 255))
    draw.text((pad + 11, y + 14), drill_label, fill=BAR_TEXT, font=dl_font)

    # ── Leaderboard rows ── start below circle bottom
    board_top = circle_cy + circle_r + 48
    row_h = 82
    row_pad_left = 48

    # Header rule
    draw.rectangle([(0, board_top - 14), (W, board_top - 13)], fill=(*GREEN, 180))
    draw.rectangle([(0, board_top - 11), (W, board_top - 10)], fill=(*GREEN, 40))

    # Column header labels
    col_hdr = _fnt(GEIST_B, 14)
    draw.text((row_pad_left + 60, board_top - 30), "METRIC", fill=(*TEXT_GHOST, 200), font=col_hdr)
    draw.text((W - 220, board_top - 30), "VALUE", fill=(*TEXT_GHOST, 200), font=col_hdr)
    draw.text((W - 120, board_top - 30), "STATUS", fill=(*TEXT_GHOST, 200), font=col_hdr)

    sym = {"rising": "+ RISING", "falling": "- FALLING"}.get(trend_direction, "= STEADY")
    col_sym = GREEN if trend_direction == "rising" else (200, 200, 200)

    rows = [
        ("01", stat_lbl.upper(),              stat,                         (*GREEN, 255)),
        ("02", bullets[0] if bullets else "", drill_label,                  (*TEXT_PURE, 220)),
        ("03", bullets[1] if len(bullets) > 1 else "", sym,                 (*col_sym, 230)),
        ("04", bullets[2] if len(bullets) > 2 else "", f"{opportunity_score:.0f} / 100", (*GREEN, 200)),
    ]

    rank_font   = _fnt(BARLOW_XB, 36)
    metric_font = _fnt(GEIST_R, 22)
    val_font    = _fnt(BARLOW_XB, 28)

    # Expand rows to fill available space above footer
    available_h = (H - 54) - board_top
    row_h = available_h // len(rows)

    for i, (rank, metric, value, val_col) in enumerate(rows):
        ry = board_top + i * row_h
        # Alternating row bg
        row_fill = (0, 14, 0, 45) if i % 2 == 0 else (0, 0, 0, 0)
        draw.rectangle([(0, ry), (W, ry + row_h - 1)], fill=row_fill)
        draw.rectangle([(0, ry + row_h - 1), (W, ry + row_h)], fill=(*GREEN, 22))

        row_mid = ry + row_h // 2

        # Rank number — vertically centered in row
        rk_h = rank_font.size
        draw.text((row_pad_left, row_mid - rk_h // 2), rank, fill=(*GREEN, 190), font=rank_font)

        # Metric label — vertically centered
        mt_h = metric_font.size
        metric_str = metric[:36] + ".." if len(metric) > 36 else metric
        draw.text((row_pad_left + 62, row_mid - mt_h // 2), metric_str, fill=(*TEXT_PURE, 210), font=metric_font)

        # Value — right-aligned block
        val_x = W - 260
        vl_h = val_font.size
        draw.text((val_x, row_mid - vl_h // 2), value, fill=val_col, font=val_font)

    # ── Footer ──
    footer_y = H - 54
    draw.rectangle([(0, footer_y), (W, H)], fill=(0, 0, 0, 255))
    draw.rectangle([(0, footer_y), (W, footer_y + 2)], fill=(*GREEN, 180))
    ff = _fnt(BARLOW_B, 26)
    ft = "FREE ACCESS IS NOW LIVE!!  ·  Visit ScoringZone.net"
    ft_w = int(draw.textlength(ft, font=ff))
    draw.text(((W - ft_w) // 2, footer_y + 14), ft, fill=(*GREEN, 255), font=ff)

    img_rgb = img.convert("RGB")
    img_rgb = ImageEnhance.Contrast(img_rgb).enhance(1.10)
    img_rgb = ImageEnhance.Sharpness(img_rgb).enhance(1.12)
    return img_rgb


# ── Public API ─────────────────────────────────────────────────────────────────

def generate_images(
    topic: str,
    opportunity_score: float,
    trend_direction: str,
    output_folder: str,
    n_variants: int = 8,
    rotation_seed: str = "",
) -> list[str]:
    """
    Generate n_variants Neon Meridian branded images for the given topic.
    Returns list of saved file paths.
    """
    os.makedirs(output_folder, exist_ok=True)

    tl       = topic.lower()
    bullets  = _make_bullets(tl)
    stat, stat_lbl = _make_stat(tl)
    drill_label = _topic_label(tl)
    logo     = _get_logo()

    builders = [
        _variant_monumental,
        _variant_data_readout,
        _variant_precision_scope,
        _variant_split_screen,
        _variant_minimalist,
        _variant_headline_card,
        _variant_quote_pull,
        _variant_cinematic,
    ]

    # Load photo backgrounds — one per variant, rotated by output_folder path
    # so different packages of the same topic use different photos
    seed = rotation_seed or os.path.basename(output_folder)
    photo_filenames = _get_topic_photos(tl, n=n_variants, rotation_seed=seed)

    paths = []
    for v in range(min(n_variants, len(builders))):
        photo_bg = _make_photo_bg(photo_filenames[v % len(photo_filenames)])
        img = builders[v](
            topic=topic,
            opportunity_score=opportunity_score,
            trend_direction=trend_direction,
            bullets=bullets,
            stat=stat,
            stat_lbl=stat_lbl,
            drill_label=drill_label,
            logo=logo,
            photo_bg=photo_bg,
        )
        path = os.path.join(output_folder, f"image_{v+1:02d}.jpg")
        img.save(path, "JPEG", quality=95)
        paths.append(path)

    return paths
