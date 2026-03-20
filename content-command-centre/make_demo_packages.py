"""
make_demo_packages.py — Creates 3 realistic demo content packages.
Run: python3 make_demo_packages.py
"""
import json, os
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
PACKAGES_DIR = os.path.join(BASE_DIR, "packages")
LOGO_PATH    = os.path.join(BASE_DIR, "scoringzone_logo.png")

# System fonts
FONT_BOLD    = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
FONT_REG     = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"

def fnt(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()

# Brand
GREEN  = (2, 244, 67)
DARK   = (10, 10, 10)
WHITE  = (255, 255, 255)
GOLD   = (255, 215, 0)

DEMO_PACKAGES = [
    {
        "id": "cycle_0002_stop_3putting",
        "topic": "How to stop 3-putting",
        "score": 87.4, "trend": "rising", "cycle": 2,
        "keyword": "stop 3 putting", "views": 284000,
        "headline": ["STOP", "3-PUTTING"],
        "sub": "The Distance Control Fix",
        "bullet1": "Set 5 balls at 20, 30 & 40 ft",
        "bullet2": "Putt every ball within 3 ft",
        "bullet3": "Score 12/15 to pass",
        "stat": "84%", "stat_lbl": "of amateurs 3-putt",
        "bg1": (0, 80, 30),   "bg2": (0, 30, 12),
        "accent": GREEN,
        "ig_caption": """🟢 STOP 3-PUTTING FOR GOOD

Most golfers 3-putt because they have zero distance control.

The 3-Putt Eliminator Drill:
→ 5 balls at 20, 30, 40 ft
→ Every putt within 3-ft circle
→ Score 12/15 before you leave

🆓 Free early access now live!! Visit scoringzone.net 👇

#golf #putting #golfpractice #3putt #puttingtips #scoringzone #golfdrills #shortgame #golftips #improveyourgolf""",
        "x_caption": "🟢 Stop 3-putting: 5 balls, 3 distances (20/30/40ft). Every putt within 3 feet. Score 12/15 → tour-ready lag putting.\n\n🆓 Free early access now live!! scoringzone.net\n\n#golf #putting #scoringzone",
    },
    {
        "id": "cycle_0002_chipping_technique",
        "topic": "Chipping technique for beginners",
        "score": 79.1, "trend": "steady", "cycle": 2,
        "keyword": "chipping technique", "views": 196000,
        "headline": ["CHIP IT", "CLEAN"],
        "sub": "Fix the Wrist Flip",
        "bullet1": "Weight forward 60/40",
        "bullet2": "Shaft leaning toward target",
        "bullet3": "Quiet wrists, shoulder turn",
        "stat": "90%", "stat_lbl": "flip their wrists",
        "bg1": (0, 50, 120),  "bg2": (0, 18, 50),
        "accent": (0, 180, 255),
        "ig_caption": """🏌️ THE 1 CHIPPING MISTAKE COSTING YOU SHOTS

90% of amateur golfers flip their wrists through impact.

Fix it now:
✅ Weight forward (60/40)
✅ Shaft leaning toward target
✅ Small shoulder turn — NOT a wrist flip
✅ Follow through low

🆓 Free early access now live!! Visit scoringzone.net 👇

#golf #chipping #shortgame #golftips #golfpractice #scoringzone""",
        "x_caption": "90% of amateurs flip their wrists chipping. Fix: weight forward, shaft lean, shoulder turn. No wrist flip.\n\n🆓 Free early access now live!! scoringzone.net\n\n#golf #chipping #shortgame #scoringzone",
    },
    {
        "id": "cycle_0002_bunker_shots",
        "topic": "How to escape bunkers consistently",
        "score": 73.8, "trend": "rising", "cycle": 2,
        "keyword": "bunker shot", "views": 147000,
        "headline": ["ESCAPE", "BUNKERS"],
        "sub": "The Sand Formula",
        "bullet1": "Open clubface FIRST, then grip",
        "bullet2": "Aim 2 inches behind the ball",
        "bullet3": "Swing through — finish high",
        "stat": "2\"", "stat_lbl": "behind the ball",
        "bg1": (120, 80, 0),  "bg2": (50, 30, 0),
        "accent": GOLD,
        "ig_caption": """⛱️ BUNKERS DON'T HAVE TO BE SCARY

The secret: you're hitting the SAND, not the ball.

The Bunker Escape Formula:
✅ Open clubface first (then grip)
✅ Aim 2 inches BEHIND the ball
✅ Swing THROUGH — don't decelerate
✅ Finish HIGH

🆓 Free early access now live!! Visit scoringzone.net 👇

#golf #bunker #sandtrap #golfpractice #shortgame #scoringzone""",
        "x_caption": "Stop trying to hit the ball in bunkers. Hit the SAND 2 inches behind it. Open face → swing through → finish high.\n\n🆓 Free early access now live!! scoringzone.net\n\n#golf #bunker #shortgame #scoringzone",
    },
]


def gradient_rect(img, x0, y0, x1, y1, col_top, col_bot):
    draw = ImageDraw.Draw(img)
    h = y1 - y0
    for y in range(h):
        t = y / max(h - 1, 1)
        r = int(col_top[0] + (col_bot[0] - col_top[0]) * t)
        g = int(col_top[1] + (col_bot[1] - col_top[1]) * t)
        b = int(col_top[2] + (col_bot[2] - col_top[2]) * t)
        draw.line([(x0, y0 + y), (x1, y0 + y)], fill=(r, g, b))


def load_logo():
    if os.path.exists(LOGO_PATH):
        try:
            return Image.open(LOGO_PATH).convert("RGBA")
        except Exception:
            pass
    return None


def make_image(pkg, variant):
    W, H = 1080, 1080
    img  = Image.new("RGB", (W, H), (20, 20, 20))
    draw = ImageDraw.Draw(img)
    accent = pkg["accent"]

    # ── Gradient background ──
    gradient_rect(img, 0, 0, W, H, pkg["bg1"], pkg["bg2"])

    # ── Dark overlay bottom portion for readability ──
    gradient_rect(img, 0, int(H*0.55), W, H, (0,0,0,0), (0,0,0))

    # ── Decorative large circle ──
    positions = [(800, 150, 380), (200, 200, 300), (900, 400, 350)]
    cx, cy, cr = positions[variant % len(positions)]
    for i in range(5):
        rr = cr - i * 55
        if rr > 10:
            col = accent if i == 0 else tuple(int(c * (0.4 - i*0.06)) for c in accent)
            w = 3 if i == 0 else 1
            draw.ellipse([(cx-rr, cy-rr), (cx+rr, cy+rr)], outline=col, width=w)

    # ── Accent dot ──
    draw.ellipse([(cx-18, cy-18), (cx+18, cy+18)], fill=accent)

    # ── Score badge ──
    draw.rounded_rectangle([(36, 36), (200, 114)], radius=10, fill=(0, 0, 0))
    draw.rectangle([(36, 36), (40, 114)], fill=accent)
    draw.text((52, 44),  f"{pkg['score']:.0f}", fill=accent,  font=fnt(FONT_BOLD, 42))
    draw.text((52, 84),  "/100",               fill=(180,180,180), font=fnt(FONT_REG, 22))

    # ── Trend pill ──
    sym = "↑ RISING" if pkg["trend"]=="rising" else "→ STEADY" if pkg["trend"]=="steady" else "↓ FALLING"
    col = GREEN if pkg["trend"]=="rising" else (200,200,200)
    draw.text((W - 220, 60), sym, fill=col, font=fnt(FONT_BOLD, 26))

    # ── Main headline ──
    y = 160
    for line in pkg["headline"]:
        draw.text((60, y), line, fill=WHITE, font=fnt(FONT_BOLD, 108))
        y += 118

    # ── Sub-line chip ──
    sub_font = fnt(FONT_BOLD, 28)
    sub_w = draw.textlength(pkg["sub"], font=sub_font) + 24
    draw.rounded_rectangle([(60, y+4), (60+int(sub_w), y+46)], radius=6, fill=accent)
    draw.text((72, y+8), pkg["sub"], fill=DARK, font=sub_font)
    y += 68

    # ── Big stat ──
    draw.text((60, y),     pkg["stat"],     fill=accent,       font=fnt(FONT_BOLD, 80))
    draw.text((60, y+88),  pkg["stat_lbl"], fill=(220,220,220), font=fnt(FONT_REG,  28))
    y += 138

    # ── Bullet points ──
    bul_font = fnt(FONT_REG, 28)
    for bullet in [pkg["bullet1"], pkg["bullet2"], pkg["bullet3"]]:
        draw.rectangle([(60, y+6), (68, y+22)], fill=accent)
        draw.text((84, y), bullet, fill=WHITE, font=bul_font)
        y += 44

    # ── CTA box (above brand bar) ──
    cta_y = H - 180
    draw.rectangle([(0, cta_y), (W, cta_y + 88)], fill=accent)
    draw.text((40, cta_y + 10), "🆓 Free early access now live!!", fill=DARK, font=fnt(FONT_BOLD, 34))
    draw.text((40, cta_y + 52), "Visit scoringzone.net", fill=DARK, font=fnt(FONT_REG, 28))

    # ── Brand bar ──
    bar_y = H - 92
    draw.rectangle([(0, bar_y), (W, H)], fill=(10, 10, 10))
    draw.rectangle([(0, bar_y), (W, bar_y+3)], fill=GREEN)

    logo = load_logo()
    if logo:
        lh = 56
        lw = int(logo.width * (lh / logo.height))
        logo_sm = logo.resize((lw, lh), Image.LANCZOS)
        img.paste(logo_sm, (24, bar_y + 16), logo_sm)
        draw.text((lw + 36, bar_y + 16), "SCORING ZONE", fill=GREEN,           font=fnt(FONT_BOLD, 24))
        draw.text((lw + 36, bar_y + 48), "scoringzone.net", fill=(160,160,160), font=fnt(FONT_REG,  20))
    else:
        draw.text((24, bar_y + 22), "● SCORING ZONE", fill=GREEN, font=fnt(FONT_BOLD, 26))

    return img


def make_package(pkg):
    folder = os.path.join(PACKAGES_DIR, pkg["id"])
    os.makedirs(folder, exist_ok=True)

    for v in range(3):
        img = make_image(pkg, v)
        img.save(os.path.join(folder, f"image_{v+1:02d}.jpg"), "JPEG", quality=95)

    manifest = {
        "package_id": pkg["id"], "topic": pkg["topic"],
        "opportunity_score": pkg["score"], "trend_direction": pkg["trend"],
        "cycle_number": pkg["cycle"], "keyword": pkg["keyword"],
        "youtube_views": pkg["views"], "created_at": datetime.utcnow().isoformat(),
        "image_count": 3,
    }
    with open(os.path.join(folder, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)
    with open(os.path.join(folder, "caption_instagram.txt"), "w") as f:
        f.write(pkg["ig_caption"])
    with open(os.path.join(folder, "caption_x.txt"), "w") as f:
        f.write(pkg["x_caption"])

    brief = f"# {pkg['topic']}\n\nScore: {pkg['score']}/100 | Trend: {pkg['trend'].upper()} | Views: {pkg['views']//1000}K\n"
    with open(os.path.join(folder, "brief_summary.md"), "w") as f:
        f.write(brief)
    with open(os.path.join(folder, "posting_instructions.txt"), "w") as f:
        f.write(f"POSTING — {pkg['topic']}\nBest time: Tue/Thu 7-9am\nInstagram: image_01.jpg\nX: image_02.jpg\n")

    print(f"  ✓ {pkg['id']}")


if __name__ == "__main__":
    os.makedirs(PACKAGES_DIR, exist_ok=True)
    print(f"Generating packages ...")
    for pkg in DEMO_PACKAGES:
        make_package(pkg)
    print(f"\nDone — {len(DEMO_PACKAGES)} packages ready.")
