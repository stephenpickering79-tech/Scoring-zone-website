"""
Generate all 40 social media designs as HTML + PNG.
Run from the social-designs/ directory.
"""
import os
import json
from pathlib import Path

OUT_DIR = Path(__file__).parent / "library"
CAPTION_DIR = Path(__file__).parent / "captions"
OUT_DIR.mkdir(exist_ok=True)
CAPTION_DIR.mkdir(exist_ok=True)

# ── Image paths (relative from library/ to Landing Page) ──────────────────
IMG_BASE = "../../../../Landing Page/features/images"

# ── Design data ───────────────────────────────────────────────────────────

DESIGNS = []

# ═══════════════════════════════════════════════════════════════════════════
# FORMAT A: App Screenshot Showcase
# ═══════════════════════════════════════════════════════════════════════════

def _showcase_html(tag, headline_l1, headline_l2, subline, img_file,
                   stat1_num, stat1_lbl, stat2_num, stat2_lbl, stat2_color="#a259ff"):
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=1080">
<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700;800;900&family=DM+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1080px;height:1080px;overflow:hidden;font-family:'DM Sans',sans-serif;background:#050505;position:relative}}
.bg{{position:absolute;inset:0;background:radial-gradient(ellipse 80% 60% at 75% 85%,rgba(110,60,200,0.12)0%,transparent 70%),radial-gradient(ellipse 60% 50% at 20% 20%,rgba(0,237,4,0.06)0%,transparent 60%)}}
.bg-grid{{position:absolute;inset:0;background-image:linear-gradient(rgba(0,237,4,0.03)1px,transparent 1px),linear-gradient(90deg,rgba(0,237,4,0.03)1px,transparent 1px);background-size:40px 40px}}
.content{{position:relative;z-index:1;width:100%;height:100%;display:flex;flex-direction:column}}
.top{{padding:56px 60px 0;flex-shrink:0}}
.tag{{display:inline-flex;align-items:center;gap:6px;font-family:'JetBrains Mono',monospace;font-size:16px;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:#00ed04;background:rgba(0,237,4,0.08);border:1px solid rgba(0,237,4,0.2);padding:8px 16px;border-radius:4px;margin-bottom:24px}}
.tag::before{{content:'';width:6px;height:6px;background:#00ed04;border-radius:50%;box-shadow:0 0 8px rgba(0,237,4,0.6)}}
.headline{{font-family:'Barlow Condensed',sans-serif;font-weight:900;font-size:62px;line-height:0.95;letter-spacing:0.02em;text-transform:uppercase;color:#fff;max-width:520px;margin-bottom:16px}}
.headline em{{font-style:normal;color:#00ed04;text-shadow:0 0 30px rgba(0,237,4,0.3)}}
.subline{{font-size:20px;color:rgba(255,255,255,0.5);font-weight:400;max-width:460px;line-height:1.5}}
.phone-area{{flex:1;position:relative;display:flex;justify-content:center;align-items:flex-end}}
.phone-frame{{width:320px;height:640px;background:#1a1a1a;border-radius:36px;border:3px solid #333;overflow:hidden;position:relative;box-shadow:0 0 0 1px rgba(0,237,4,0.1),0 20px 60px rgba(0,0,0,0.6);margin-bottom:-80px}}
.phone-frame img{{width:100%;height:100%;object-fit:cover;object-position:top}}
.phone-frame::before{{content:'';position:absolute;top:0;left:50%;transform:translateX(-50%);width:120px;height:28px;background:#1a1a1a;border-radius:0 0 16px 16px;z-index:2}}
.float-card{{position:absolute;background:rgba(15,15,15,0.92);backdrop-filter:blur(12px);border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:16px 20px;box-shadow:0 12px 40px rgba(0,0,0,0.5)}}
.float-left{{left:48px;top:420px}}
.float-right{{right:48px;top:520px}}
.stat-num{{font-family:'Barlow Condensed',sans-serif;font-weight:800;font-size:48px;color:#00ed04;line-height:1;text-shadow:0 0 20px rgba(0,237,4,0.3)}}
.stat-num.alt{{color:{stat2_color};text-shadow:0 0 20px {stat2_color}33}}
.stat-lbl{{font-family:'JetBrains Mono',monospace;font-size:13px;color:rgba(255,255,255,0.45);letter-spacing:0.06em;text-transform:uppercase;margin-top:4px}}
.bottom-bar{{position:absolute;bottom:0;left:0;right:0;height:56px;background:rgba(0,0,0,0.9);border-top:1px solid rgba(0,237,4,0.15);display:flex;align-items:center;justify-content:space-between;padding:0 32px;z-index:10}}
.brand{{display:flex;align-items:center;gap:10px}}
.brand-dot{{width:24px;height:24px;border:2px solid #00ed04;border-radius:50%;position:relative}}
.brand-dot::after{{content:'';position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:8px;height:8px;background:#00ed04;border-radius:50%}}
.brand-name{{font-family:'Barlow Condensed',sans-serif;font-weight:700;font-size:16px;letter-spacing:0.12em;text-transform:uppercase;color:#fff}}
.cta{{font-size:14px;font-weight:600;color:#000;background:#00ed04;padding:8px 20px;border-radius:20px;box-shadow:0 0 16px rgba(0,237,4,0.3)}}
</style></head>
<body>
<div class="bg"></div><div class="bg-grid"></div>
<div class="content">
<div class="top">
<div class="tag">{tag}</div>
<div class="headline">{headline_l1}<br><em>{headline_l2}</em></div>
<div class="subline">{subline}</div>
</div>
<div class="phone-area">
<div class="float-card float-left"><div class="stat-num">{stat1_num}</div><div class="stat-lbl">{stat1_lbl}</div></div>
<div class="float-card float-right"><div class="stat-num alt">{stat2_num}</div><div class="stat-lbl">{stat2_lbl}</div></div>
<div class="phone-frame"><img src="{IMG_BASE}/{img_file}" alt=""></div>
</div>
<div class="bottom-bar"><div class="brand"><div class="brand-dot"></div><div class="brand-name">Scoring Zone</div></div><div class="cta">Free early access &rarr;</div></div>
</div>
</body></html>"""

showcases = [
    # Already done: A01 putting-drills-1.jpg
    ("A02", "Chipping Drills", "chipping drills", "Scored reps that", "fix your short game.", "One-Club Wizard, 21 Shots, Par in 2 — every chip scored against handicap benchmarks.", "challenge-complete.jpg", "65%", "of score inside 100yds", "50 XP", "per completed drill"),
    ("A03", "Practice Assistant", "practice assistant", "Your coach.", "In your pocket.", "Structured sessions, guided warmups, and pressure drills — all personalized to your weaknesses.", "assistant-main.jpg", "30 min", "guided session length", "3 FOCUS", "areas per plan", "#a259ff"),
    ("A04", "Round Stats", "round tracking", "Track every", "shot on course.", "FIR, GIR, putts, scrambling — hole-by-hole stats that show exactly where strokes are lost.", "stats-1.jpg", "18", "holes tracked per round", "4 STATS", "per hole", "#4a9eff"),
    ("A05", "Sim Lab", "simulator drills", "Built for your", "launch monitor.", "20 precision tests designed for Trackman, Mevo+, and simulator sessions.", "sim-1.jpg", "20", "simulator-specific drills", "5 ACTIVE", "tests available", "#00ed04"),
    ("A06", "Challenge Complete", "achievements", "Every drill.", "Every score. Tracked.", "Complete challenges, earn XP, and watch your short game HCP drop over time.", "challenge-complete.jpg", "15 ft", "avg proximity result", "280 XP", "earned this session", "#f5c518"),
    ("A07", "Benchmarks", "performance levels", "Where do you", "really stand?", "Tour Pro, Scratch, Under 5 — see exactly how your putting and chipping compare.", "putting-score-3.jpg", "11", "putts = Under 5 HCP", "8", "benchmark levels", "#a259ff"),
    ("A08", "Elite Mode", "elite mode", "No gimmes.", "No comfort zone.", "Tighter targets, penalty restarts, and 2x XP. Pressure that transfers to the course.", "elite-challenge.jpg", "2x", "XP multiplier", "0", "gimmes allowed", "#ff6030"),
    ("A09", "Your Stats", "stats dashboard", "Data that makes", "you better.", "Putting HCP, scrambling %, proximity trends — see your improvement across every session.", "stats-2.jpg", "7.1", "current putting HCP", "-5.3", "strokes gained", "#00ed04"),
    ("A10", "Pressure Combine", "pressure testing", "30 minutes.", "Maximum pressure.", "Short game + putting combine with timer, penalties, and real tournament pressure simulation.", "assistant-pressure.jpg", "30 min", "combine duration", "4", "pressure stages", "#ff6030"),
]

for item in showcases:
    if len(item) == 11:
        sid, tag, _, hl1, hl2, sub, img, s1n, s1l, s2n, s2l = item
        s2c = "#a259ff"
    else:
        sid, tag, _, hl1, hl2, sub, img, s1n, s1l, s2n, s2l, s2c = item
    DESIGNS.append({
        "id": sid,
        "format": "showcase",
        "html": _showcase_html(tag, hl1, hl2, sub, img, s1n, s1l, s2n, s2l, s2c),
    })


# ═══════════════════════════════════════════════════════════════════════════
# FORMAT B: Before/After Stats
# ═══════════════════════════════════════════════════════════════════════════

def _beforeafter_html(headline, timeframe, rows):
    """rows = list of (metric, before_val, before_ctx, after_val, after_ctx)"""
    before_rows = ""
    after_rows = ""
    for metric, bv, bc, av, ac in rows:
        before_rows += f'<div class="stat-row"><div class="metric">{metric}</div><div class="value bad">{bv}</div><div class="context">{bc}</div></div>\n'
        after_rows += f'<div class="stat-row"><div class="metric">{metric}</div><div class="value good">{av}</div><div class="context">{ac}</div></div>\n'

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=1080">
<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700;800;900&family=DM+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1080px;height:1080px;overflow:hidden;font-family:'DM Sans',sans-serif;background:#050505;position:relative}}
.bg{{position:absolute;inset:0;background:radial-gradient(ellipse 70% 50% at 25% 80%,rgba(255,50,50,0.06)0%,transparent 60%),radial-gradient(ellipse 70% 50% at 75% 80%,rgba(0,237,4,0.08)0%,transparent 60%),linear-gradient(180deg,#080808 0%,#040404 100%)}}
.content{{position:relative;z-index:1;width:100%;height:100%;display:flex;flex-direction:column;padding:56px 60px}}
.header{{display:flex;align-items:center;justify-content:space-between;margin-bottom:20px}}
.tag{{display:inline-flex;align-items:center;gap:6px;font-family:'JetBrains Mono',monospace;font-size:16px;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:#00ed04;background:rgba(0,237,4,0.08);border:1px solid rgba(0,237,4,0.2);padding:8px 16px;border-radius:4px}}
.timeframe{{font-family:'JetBrains Mono',monospace;font-size:15px;font-weight:600;color:rgba(255,255,255,0.4);letter-spacing:0.08em;text-transform:uppercase}}
.headline{{font-family:'Barlow Condensed',sans-serif;font-weight:900;font-size:56px;line-height:0.95;letter-spacing:0.02em;text-transform:uppercase;color:#fff;margin-bottom:40px}}
.comparison{{display:grid;grid-template-columns:1fr 60px 1fr;flex:1;align-items:stretch}}
.side{{display:flex;flex-direction:column;gap:14px}}
.side-label{{font-family:'Barlow Condensed',sans-serif;font-weight:700;font-size:28px;letter-spacing:0.12em;text-transform:uppercase;margin-bottom:6px;padding-bottom:10px}}
.side-label.before{{color:rgba(255,80,80,0.7);border-bottom:2px solid rgba(255,80,80,0.2)}}
.side-label.after{{color:#00ed04;border-bottom:2px solid rgba(0,237,4,0.3)}}
.stat-row{{background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);border-radius:10px;padding:16px 20px;display:flex;flex-direction:column;gap:2px}}
.stat-row .metric{{font-family:'JetBrains Mono',monospace;font-size:14px;color:rgba(255,255,255,0.35);letter-spacing:0.08em;text-transform:uppercase}}
.stat-row .value{{font-family:'Barlow Condensed',sans-serif;font-weight:800;font-size:48px;line-height:1}}
.stat-row .value.bad{{color:rgba(255,100,100,0.8)}}.stat-row .value.good{{color:#00ed04;text-shadow:0 0 20px rgba(0,237,4,0.2)}}
.stat-row .context{{font-size:15px;color:rgba(255,255,255,0.3)}}
.divider{{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:12px;padding-top:48px}}
.divider-line{{width:2px;flex:1;background:linear-gradient(180deg,rgba(255,80,80,0.3),rgba(255,255,255,0.1)50%,rgba(0,237,4,0.4))}}
.divider-arrow{{font-size:20px;color:rgba(255,255,255,0.3)}}
.bottom-bar{{display:flex;align-items:center;justify-content:space-between;margin-top:36px;padding-top:18px;border-top:1px solid rgba(255,255,255,0.06)}}
.brand{{display:flex;align-items:center;gap:10px}}
.brand-dot{{width:24px;height:24px;border:2px solid #00ed04;border-radius:50%;position:relative}}
.brand-dot::after{{content:'';position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:8px;height:8px;background:#00ed04;border-radius:50%}}
.brand-name{{font-family:'Barlow Condensed',sans-serif;font-weight:700;font-size:16px;letter-spacing:0.12em;text-transform:uppercase;color:#fff}}
.cta{{font-size:15px;font-weight:600;color:#00ed04}}
</style></head>
<body>
<div class="bg"></div>
<div class="content">
<div class="header"><div class="tag">Real Results</div><div class="timeframe">{timeframe}</div></div>
<div class="headline">{headline}</div>
<div class="comparison">
<div class="side"><div class="side-label before">Before</div>{before_rows}</div>
<div class="divider"><div class="divider-line"></div><div class="divider-arrow">&rarr;</div><div class="divider-line"></div></div>
<div class="side"><div class="side-label after">After</div>{after_rows}</div>
</div>
<div class="bottom-bar"><div class="brand"><div class="brand-dot"></div><div class="brand-name">Scoring Zone</div></div><div class="cta">Free early access &rarr; scoringzone.net</div></div>
</div>
</body></html>"""

beforeafters = [
    # Already done: B01 putting
    ("B02", "Your chipping in<br>4 weeks.", "4 weeks · 3 sessions/week", [
        ("Up & Down %", "18%", "scrambling rate", "41%", "+23% improvement"),
        ("Avg chip proximity", "24 ft", "from hole", "12 ft", "50% closer"),
        ("Skulled chips/round", "4.1", "per 18 holes", "0.8", "80% fewer"),
        ("Chipping HCP", "14.2", "ScoringZone metric", "8.6", "-5.6 strokes"),
    ]),
    ("B03", "How to break 90<br>in 6 weeks.", "6 weeks · 3 sessions/week", [
        ("Avg score", "94", "last 5 rounds", "87", "7 strokes lower"),
        ("3-putts per round", "4.8", "distance control", "1.4", "71% fewer"),
        ("Up & Down %", "16%", "scrambling", "35%", "+19% improvement"),
        ("Short game HCP", "15.1", "ScoringZone metric", "9.3", "-5.8 strokes"),
    ]),
    ("B04", "Your bunker game<br>transformed.", "3 weeks · 2 sessions/week", [
        ("Bunker escape %", "51%", "first attempt", "89%", "+38% improvement"),
        ("Avg sand proximity", "28 ft", "from hole", "14 ft", "50% closer"),
        ("Sand saves", "8%", "up-and-down from sand", "31%", "+23% improvement"),
        ("Fear factor", "High", "avoids bunkers", "Low", "attacks pins"),
    ]),
    ("B05", "Kill your 3-putts<br>in 2 weeks.", "2 weeks · 4 sessions/week", [
        ("3-putts per round", "5.2", "avg across 4 rounds", "1.8", "65% fewer"),
        ("Lag putt proximity", "7.4 ft", "from 30+ feet", "3.1 ft", "58% closer"),
        ("Putts per round", "34.6", "total putts", "30.2", "-4.4 putts"),
        ("Putting HCP", "12.4", "ScoringZone metric", "7.1", "-5.3 strokes"),
    ]),
    ("B06", "What consistent<br>practice does.", "8 weeks · tracked in app", [
        ("Sessions/week", "0.5", "unstructured", "3.2", "6x more frequent"),
        ("Session length", "45 min", "unfocused range", "20 min", "focused drills"),
        ("Drills completed", "12", "over 2 months", "96", "8x more reps"),
        ("HCP change", "+0.2", "no improvement", "-4.1", "real progress"),
    ]),
    ("B07", "Your short game HCP<br>over 8 weeks.", "8 weeks · scored drills", [
        ("Week 1 HCP", "16.2", "starting point", "Week 8 HCP", ""),
        ("Putting HCP", "13.8", "lag + short putts", "8.4", "-5.4 drop"),
        ("Chipping HCP", "15.1", "proximity + up/down", "9.7", "-5.4 drop"),
        ("Combined", "14.5", "short game average", "9.1", "-5.4 strokes"),
    ]),
    ("B08", "Lag putting:<br>the real fix.", "3 weeks · Lag King drill", [
        ("Putts inside 3ft", "4/10", "from 30+ feet", "8/10", "doubled"),
        ("3-putts from 30ft+", "62%", "of attempts", "18%", "71% fewer"),
        ("Avg leave distance", "6.8 ft", "from hole", "2.9 ft", "57% closer"),
        ("Lag King score", "4/10", "Under 15 level", "8/10", "Under 5 level"),
    ]),
    ("B09", "Scrambling: where<br>scores are saved.", "4 weeks · chipping + putting", [
        ("Scrambling %", "14%", "up-and-down rate", "38%", "+24% improvement"),
        ("Missed green saves", "2.5", "per round", "6.8", "per round"),
        ("Strokes saved", "0", "vs handicap avg", "3.2", "per round"),
        ("Short game rank", "Bottom 20%", "for handicap", "Top 40%", "for handicap"),
    ]),
    ("B10", "Approach proximity<br>with Sim Lab.", "4 weeks · simulator drills", [
        ("100yd proximity", "34 ft", "from pin", "18 ft", "47% closer"),
        ("50yd proximity", "22 ft", "from pin", "11 ft", "50% closer"),
        ("GIR %", "28%", "greens in regulation", "44%", "+16% improvement"),
        ("Scoring avg", "5.2", "on par 4s", "4.6", "-0.6 strokes"),
    ]),
]

for sid, headline, timeframe, rows in beforeafters:
    DESIGNS.append({
        "id": sid,
        "format": "beforeafter",
        "html": _beforeafter_html(headline, timeframe, rows),
    })


# ═══════════════════════════════════════════════════════════════════════════
# FORMAT C: Drill Explainer
# ═══════════════════════════════════════════════════════════════════════════

def _explainer_html(drill_name, category, time_info, xp, purpose,
                    steps, benchmarks):
    """steps = [(title, desc, highlight_or_None), ...]
       benchmarks = [(score, label, color), ...]"""
    steps_html = ""
    for i, (title, desc, hl) in enumerate(steps, 1):
        hl_html = f'<div class="step-hl">{hl}</div>' if hl else ""
        steps_html += f'''<div class="step"><div class="step-num">{i}</div><div class="step-content"><div class="step-title">{title}</div><div class="step-desc">{desc}</div>{hl_html}</div></div>\n'''

    bm_html = ""
    for score, label, color in benchmarks:
        bm_html += f'<div class="bm"><div class="bm-score" style="color:{color}">{score}</div><div class="bm-tag">{label}</div></div>'

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=1080">
<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700;800;900&family=DM+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1080px;height:1080px;overflow:hidden;font-family:'DM Sans',sans-serif;background:#050505;position:relative}}
.bg{{position:absolute;inset:0;background:radial-gradient(ellipse 80% 70% at 80% 30%,rgba(110,60,200,0.1)0%,transparent 60%),radial-gradient(ellipse 50% 40% at 10% 90%,rgba(0,237,4,0.06)0%,transparent 50%)}}
.content{{position:relative;z-index:1;width:100%;height:100%;display:flex;flex-direction:column}}
.intro{{background:linear-gradient(135deg,rgba(0,237,4,0.1)0%,rgba(0,237,4,0.03)100%);border-bottom:1px solid rgba(0,237,4,0.15);padding:28px 60px;display:flex;align-items:center;justify-content:space-between}}
.intro-left{{display:flex;flex-direction:column;gap:4px}}
.intro-eye{{font-family:'JetBrains Mono',monospace;font-size:16px;font-weight:600;letter-spacing:0.12em;text-transform:uppercase;color:#00ed04;display:flex;align-items:center;gap:8px}}
.intro-eye::before{{content:'';width:6px;height:6px;background:#00ed04;border-radius:50%;box-shadow:0 0 8px rgba(0,237,4,0.6)}}
.intro-hl{{font-family:'Barlow Condensed',sans-serif;font-weight:800;font-size:42px;text-transform:uppercase;letter-spacing:0.03em;color:#fff;line-height:1}}
.intro-hl em{{font-style:normal;color:#00ed04}}
.intro-right{{display:flex;align-items:center;gap:12px}}
.app-icon{{width:44px;height:44px;border:2px solid #00ed04;border-radius:12px;display:flex;align-items:center;justify-content:center;background:rgba(0,237,4,0.06)}}
.app-icon::after{{content:'◎';color:#00ed04;font-size:20px}}
.app-lbl{{font-family:'Barlow Condensed',sans-serif;font-weight:700;font-size:16px;letter-spacing:0.1em;text-transform:uppercase;color:rgba(255,255,255,0.6);line-height:1.3}}
.main{{flex:1;padding:28px 60px 0;display:flex;flex-direction:column}}
.drill-header{{display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:20px}}
.drill-badge{{display:flex;align-items:center;gap:14px}}
.drill-icon{{width:50px;height:50px;border:2px solid rgba(110,60,200,0.6);border-radius:50%;display:flex;align-items:center;justify-content:center;background:rgba(110,60,200,0.1)}}
.drill-icon::after{{content:'◎';color:#a259ff;font-size:22px}}
.drill-name{{font-family:'Barlow Condensed',sans-serif;font-weight:800;font-size:38px;text-transform:uppercase;letter-spacing:0.04em;color:#fff}}
.drill-meta{{display:flex;gap:12px;font-family:'JetBrains Mono',monospace;font-size:14px}}
.drill-cat{{color:#a259ff;letter-spacing:0.1em;text-transform:uppercase}}
.drill-time{{color:rgba(255,255,255,0.3);letter-spacing:0.06em}}
.xp{{font-family:'JetBrains Mono',monospace;font-size:14px;font-weight:600;color:#f5c518;background:rgba(245,197,24,0.08);border:1px solid rgba(245,197,24,0.2);padding:6px 14px;border-radius:4px}}
.purpose{{font-size:20px;color:rgba(255,255,255,0.5);line-height:1.5;margin-bottom:24px;max-width:750px}}
.purpose strong{{color:#fff;font-weight:600}}
.steps{{display:flex;flex-direction:column;flex:1}}
.step{{display:flex;gap:18px;padding:16px 0;border-bottom:1px solid rgba(255,255,255,0.04);align-items:flex-start}}
.step:last-child{{border-bottom:none}}
.step-num{{width:38px;height:38px;background:rgba(0,237,4,0.08);border:1px solid rgba(0,237,4,0.25);border-radius:8px;display:flex;align-items:center;justify-content:center;font-family:'Barlow Condensed',sans-serif;font-weight:800;font-size:20px;color:#00ed04;flex-shrink:0}}
.step-title{{font-family:'Barlow Condensed',sans-serif;font-weight:700;font-size:24px;text-transform:uppercase;letter-spacing:0.03em;color:#fff;margin-bottom:2px}}
.step-desc{{font-size:17px;color:rgba(255,255,255,0.38);line-height:1.4}}
.step-hl{{font-family:'JetBrains Mono',monospace;font-size:13px;color:#00ed04;background:rgba(0,237,4,0.06);border:1px solid rgba(0,237,4,0.15);padding:3px 10px;border-radius:3px;display:inline-block;margin-top:5px}}
.benchmark{{background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);border-radius:10px;padding:14px 24px;display:flex;align-items:center;justify-content:space-between;margin-top:auto;margin-bottom:8px}}
.bm-label{{font-family:'JetBrains Mono',monospace;font-size:13px;color:rgba(255,255,255,0.3);letter-spacing:0.08em;text-transform:uppercase}}
.bm-levels{{display:flex;gap:24px}}
.bm{{text-align:center}}
.bm-score{{font-family:'Barlow Condensed',sans-serif;font-weight:800;font-size:30px;line-height:1}}
.bm-tag{{font-family:'JetBrains Mono',monospace;font-size:11px;color:rgba(255,255,255,0.3);letter-spacing:0.06em;text-transform:uppercase;margin-top:3px}}
.bottom-bar{{display:flex;align-items:center;justify-content:space-between;padding:12px 60px 36px;border-top:1px solid rgba(0,237,4,0.1)}}
.brand{{display:flex;align-items:center;gap:10px}}
.brand-dot{{width:22px;height:22px;border:2px solid #00ed04;border-radius:50%;position:relative}}
.brand-dot::after{{content:'';position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:7px;height:7px;background:#00ed04;border-radius:50%}}
.brand-name{{font-family:'Barlow Condensed',sans-serif;font-weight:700;font-size:15px;letter-spacing:0.12em;text-transform:uppercase;color:#fff}}
.cta{{font-size:14px;font-weight:600;color:#00ed04}}
</style></head>
<body>
<div class="bg"></div>
<div class="content">
<div class="intro"><div class="intro-left"><div class="intro-eye">Inside the app</div><div class="intro-hl">Here's a drill from <em>Scoring Zone</em></div></div><div class="intro-right"><div class="app-icon"></div><div class="app-lbl">Performance based<br>golf app</div></div></div>
<div class="main">
<div class="drill-header"><div class="drill-badge"><div class="drill-icon"></div><div><div class="drill-name">{drill_name}</div><div class="drill-meta"><span class="drill-cat">{category}</span><span class="drill-time">{time_info}</span></div></div></div><div class="xp">★ {xp} XP</div></div>
<div class="purpose">{purpose}</div>
<div class="steps">{steps_html}</div>
<div class="benchmark"><div class="bm-label">Benchmark levels</div><div class="bm-levels">{bm_html}</div></div>
</div>
<div class="bottom-bar"><div class="brand"><div class="brand-dot"></div><div class="brand-name">Scoring Zone</div></div><div class="cta">Free early access &rarr; scoringzone.net</div></div>
</div>
</body></html>"""

explainers = [
    # Already done: C01 Lag King
    ("C02", "Clock Drill", "Read & Roll · Putting", "10 min · Medium", "55",
     "Master break reading by putting from every angle around the hole — like a clock face.",
     [("Set up the clock", "Place balls at 3, 6, 9, and 12 o'clock positions, 6 feet from the hole.", None),
      ("Putt all 4 positions", "Read the break from each angle. Adjust aim and speed for every putt.", "Each position has different break"),
      ("Score & advance", "Make 3/4 to pass. The app tracks your read accuracy across sessions.", "Score 4/4 → Under 3 HCP level")],
     [("4/4", "Tour Pro", "#f5c518"), ("3/4", "Under 5", "#a259ff"), ("2/4", "Under 10", "#00ed04")]),

    ("C03", "One-Club Wizard", "Versatility · Chipping", "12 min · Medium", "60",
     "Master <strong>one wedge for every chip</strong>. Change trajectory by setup, not club selection.",
     [("Pick your pitching wedge", "One club for the entire drill. Low runners, mid-trajectory, and high soft shots — all from the same wedge.", None),
      ("Hit 10 chips to 3 targets", "Vary ball position and shaft lean to control trajectory. Score proximity to each target.", "Back = low runner · Middle = standard · Forward = high"),
      ("Score in the app", "Points based on proximity. The app benchmarks your versatility vs handicap levels.", "Avg 8ft proximity → Under 5 HCP")],
     [("5ft", "Tour Pro", "#f5c518"), ("8ft", "Under 5", "#a259ff"), ("14ft", "Under 10", "#00ed04")]),

    ("C04", "Streak Survivor", "Mental Game · Putting", "10 min · Hard", "55",
     "Build <strong>clutch putting nerves</strong>. Consecutive makes required — one miss resets your streak.",
     [("Start at 3 feet", "Make consecutive putts. Your streak counter climbs with each make.", None),
      ("Miss = restart from zero", "The pressure builds with every putt. This mirrors tournament nerves on short putts.", "Simulates real on-course pressure"),
      ("Beat your best streak", "The app tracks your longest streak across sessions. Chase your personal record.", "Streak 10+ → Under 3 HCP nerve control")],
     [("15+", "Tour Pro", "#f5c518"), ("10", "Under 5", "#a259ff"), ("6", "Under 10", "#00ed04")]),

    ("C05", "Par in 2", "Elite · Chipping", "15 min · Hard", "70",
     "Complete each chip in <strong>2 strokes max</strong> — but your second shot must be at least a putter length away. No gimmes.",
     [("Set up 9 chip shots", "Different lies around the green — uphill, downhill, tight, fluffy. Variety is the point.", None),
      ("Chip + putt in 2 or less", "Get it close enough to one-putt, but it MUST be at least a putter length away.", "No gimmes — Elite Mode rules apply"),
      ("Count your pars", "Score how many of 9 you complete in 2 or fewer. The app compares to handicap benchmarks.", "Score 7/9 → Under 5 HCP level")],
     [("9/9", "Tour Pro", "#f5c518"), ("7/9", "Under 5", "#a259ff"), ("5/9", "Under 10", "#00ed04")]),

    ("C06", "Knockout Ladder", "Clutch Putting · Putting", "10-15 min · Hard", "70",
     "Ladder from <strong>3 to 15 feet</strong>. Make 3 in a row to advance. Miss = back one rung.",
     [("Start at 3 feet", "Make 3 consecutive putts to advance to 6 feet. Miss any = drop back one distance.", None),
      ("Climb the ladder", "3ft → 6ft → 9ft → 12ft → 15ft. Each distance requires 3 consecutive makes.", "Miss at 9ft = back to 6ft"),
      ("Complete all 5 rungs", "Reach the top of the ladder. The app tracks how many attempts it takes.", "Complete in <20 putts → Under 5 HCP")],
     [("<15", "Tour Pro", "#f5c518"), ("<20", "Under 5", "#a259ff"), ("<30", "Under 10", "#00ed04")]),

    ("C07", "21 Shots", "Mixed · Short Game", "20 min · Medium", "60",
     "The ultimate <strong>short game sampler</strong>. 7 chips, 7 pitches, 7 putts — all scored for proximity.",
     [("7 chips from different lies", "Tight, fluffy, uphill, downhill — score each by proximity to the hole.", None),
      ("7 pitches from 20-50 yards", "Distance control is everything. Each pitch scored by how close you land to target.", "Avg proximity under 10ft = bonus XP"),
      ("7 putts from 6-30 feet", "Mix of short, mid, and lag putts. Score makes and proximity of misses.", "21 total shots → full short game picture")],
     [("18+", "Tour Pro", "#f5c518"), ("14", "Under 5", "#a259ff"), ("10", "Under 10", "#00ed04")]),

    ("C08", "Pitching Ladder", "Distance Control · Sim Lab", "15 min · Medium", "55",
     "Dial in <strong>wedge distances</strong> on your launch monitor. 5 shots each at 30/50/70/90 yards.",
     [("Set 4 distance targets", "30, 50, 70, and 90 yards. Hit 5 shots at each distance on your simulator.", None),
      ("Score by proximity", "The app measures carry distance vs target. Points for shots within 6ft of the pin.", "Designed for Trackman, Mevo+, SkyTrak"),
      ("Track your distance gaps", "See exactly where your wedge distances break down. The app finds your weak range.", "Most amateurs are worst at 50-70 yards")],
     [("16+", "Tour Pro", "#f5c518"), ("12", "Under 5", "#a259ff"), ("8", "Under 10", "#00ed04")]),

    ("C09", "Speed Master", "Speed Control · Putting", "8 min · Medium", "50",
     "Train <strong>lag putt speed</strong> by putting to a line, not a hole. Pure distance control.",
     [("Place a club 3ft past the hole", "Every putt must stop between the hole and the club. This is your speed zone.", None),
      ("Hit 10 putts from 25+ feet", "Ignore the break. Focus only on speed. Did it stop in the zone?", "Speed zone = hole to 3ft past"),
      ("Score zone hits out of 10", "The app tracks your speed control accuracy. This is the #1 lag putting skill.", "Score 8/10 → Under 5 HCP speed control")],
     [("10/10", "Tour Pro", "#f5c518"), ("8/10", "Under 5", "#a259ff"), ("5/10", "Under 10", "#00ed04")]),

    ("C10", "Pressure Combine", "Mixed · Pressure Test", "30 min · Hard", "100",
     "The <strong>full short game pressure test</strong>. 4 stages, timed, with penalties. No shortcuts.",
     [("Stage 1: Putting under pressure", "Streak drill + lag ladder combined. Timer running. Miss = penalty strokes added.", None),
      ("Stage 2: Chipping with consequences", "10 chips scored for proximity. Must avg under 10ft or restart the stage.", "Restart penalty simulates tournament nerves"),
      ("Stage 3: Combined score", "Total your putting + chipping scores. The app compares your combine result to benchmarks.", "Top 10% combine score → Elite badge")],
     [("90+", "Tour Pro", "#f5c518"), ("75", "Under 5", "#a259ff"), ("60", "Under 10", "#00ed04")]),
]

for sid, name, cat, time, xp, purpose, steps, bms in explainers:
    DESIGNS.append({
        "id": sid,
        "format": "explainer",
        "html": _explainer_html(name, cat, time, xp, purpose, steps, bms),
    })


# ═══════════════════════════════════════════════════════════════════════════
# FORMAT D: Feature Highlight
# ═══════════════════════════════════════════════════════════════════════════

def _feature_html(tag_text, tag_color, headline, subline, img1, img1_label,
                  img2, img2_label, pills):
    pills_html = ""
    for title, desc in pills:
        pills_html += f'<div class="fp"><div class="fp-title">{title}</div><div class="fp-desc">{desc}</div></div>'

    border_style = f"border-color:rgba({tag_color[0]},{tag_color[1]},{tag_color[2]},0.3);box-shadow:0 16px 48px rgba(0,0,0,0.5),0 0 40px rgba({tag_color[0]},{tag_color[1]},{tag_color[2]},0.06)"
    tag_css = f"color:rgb({tag_color[0]},{tag_color[1]},{tag_color[2]});background:rgba({tag_color[0]},{tag_color[1]},{tag_color[2]},0.1);border:1px solid rgba({tag_color[0]},{tag_color[1]},{tag_color[2]},0.3)"
    bar_border = f"border-top:1px solid rgba({tag_color[0]},{tag_color[1]},{tag_color[2]},0.2)"

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=1080">
<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700;800;900&family=DM+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1080px;height:1080px;overflow:hidden;font-family:'DM Sans',sans-serif;background:#050505;position:relative}}
.bg{{position:absolute;inset:0;background:radial-gradient(ellipse 60% 40% at 50% 0%,rgba({tag_color[0]},{tag_color[1]},{tag_color[2]},0.08)0%,transparent 60%),linear-gradient(180deg,#0a0404 0%,#050505 30%)}}
.content{{position:relative;z-index:1;width:100%;height:100%;display:flex;flex-direction:column;padding:48px 60px 0}}
.tag-row{{display:flex;align-items:center;gap:10px;margin-bottom:28px}}
.tag{{font-family:'JetBrains Mono',monospace;font-size:14px;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;{tag_css};padding:6px 14px;border-radius:4px}}
.headline{{font-family:'Barlow Condensed',sans-serif;font-weight:900;font-size:58px;line-height:0.92;letter-spacing:0.02em;text-transform:uppercase;color:#fff;margin-bottom:12px}}
.headline em{{font-style:normal;color:rgb({tag_color[0]},{tag_color[1]},{tag_color[2]});text-shadow:0 0 30px rgba({tag_color[0]},{tag_color[1]},{tag_color[2]},0.25)}}
.subline{{font-size:18px;color:rgba(255,255,255,0.4);line-height:1.5;max-width:500px;margin-bottom:32px}}
.phones{{flex:1;display:flex;gap:28px;position:relative;overflow:hidden}}
.phone-col{{flex:1;display:flex;flex-direction:column;gap:10px}}
.phone-lbl{{font-family:'JetBrains Mono',monospace;font-size:11px;color:rgba(255,255,255,0.3);letter-spacing:0.1em;text-transform:uppercase}}
.phone{{flex:1;background:#111;border-radius:24px;border:2px solid rgba(255,255,255,0.08);overflow:hidden;box-shadow:0 16px 48px rgba(0,0,0,0.5)}}
.phone.accent{{  {border_style} }}
.phone img{{width:100%;height:100%;object-fit:cover;object-position:top}}
.pills{{position:absolute;bottom:80px;left:0;right:0;display:flex;gap:14px;padding:0 16px}}
.fp{{background:rgba(10,10,10,0.88);backdrop-filter:blur(8px);border:1px solid rgba(255,255,255,0.08);border-radius:8px;padding:12px 14px;flex:1}}
.fp-title{{font-family:'Barlow Condensed',sans-serif;font-weight:700;font-size:16px;text-transform:uppercase;letter-spacing:0.04em;color:#fff;margin-bottom:2px}}
.fp-desc{{font-size:12px;color:rgba(255,255,255,0.35);line-height:1.3}}
.bottom-bar{{position:absolute;bottom:0;left:0;right:0;height:56px;background:rgba(0,0,0,0.9);{bar_border};display:flex;align-items:center;justify-content:space-between;padding:0 32px;z-index:10}}
.brand{{display:flex;align-items:center;gap:10px}}
.brand-dot{{width:22px;height:22px;border:2px solid #00ed04;border-radius:50%;position:relative}}
.brand-dot::after{{content:'';position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:7px;height:7px;background:#00ed04;border-radius:50%}}
.brand-name{{font-family:'Barlow Condensed',sans-serif;font-weight:700;font-size:15px;letter-spacing:0.12em;text-transform:uppercase;color:#fff}}
.cta{{font-size:13px;font-weight:600;color:#000;background:#00ed04;padding:7px 18px;border-radius:20px}}
</style></head>
<body>
<div class="bg"></div>
<div class="content">
<div class="tag-row"><div class="tag">{tag_text}</div></div>
<div class="headline">{headline}</div>
<div class="subline">{subline}</div>
<div class="phones">
<div class="phone-col"><div class="phone-lbl">{img1_label}</div><div class="phone"><img src="{IMG_BASE}/{img1}" alt=""></div></div>
<div class="phone-col"><div class="phone-lbl">{img2_label}</div><div class="phone accent"><img src="{IMG_BASE}/{img2}" alt=""></div></div>
<div class="pills">{pills_html}</div>
</div>
</div>
<div class="bottom-bar"><div class="brand"><div class="brand-dot"></div><div class="brand-name">Scoring Zone</div></div><div class="cta">Free early access &rarr;</div></div>
</body></html>"""

features = [
    # Already done: D01 Elite Mode
    ("D02", "Practice Assistant", (162,89,255), "Your personal<br>golf coach. <em>Free.</em>",
     "Guided sessions, structured warmups, and drills tailored to your weaknesses. 30 minutes that actually improve your game.",
     "assistant-main.jpg", "Practice assistant", "assistant-structured.jpg", "Guided session",
     [("Guided sessions", "1-hour structured practice with drills selected for you"),
      ("Focus areas", "Targets your weakest short game skills automatically"),
      ("Practice notepad", "Track what you're working on between sessions")]),

    ("D03", "XP & Leveling", (245,197,24), "Every rep earns<br>you <em>something.</em>",
     "Complete drills, earn XP, level up your short game HCP. Practice becomes a game — with real stakes and real rewards.",
     "putting-drills-1.jpg", "Earn XP per drill", "challenge-complete.jpg", "Challenge complete",
     [("50-100 XP per drill", "Harder drills = more XP. Elite mode = 2x multiplier"),
      ("Level up your HCP", "Your short game handicap updates after every session"),
      ("Benchmark levels", "Compare to Tour Pro, Scratch, Under 5, Under 10")]),

    ("D04", "Round Stats", (74,158,255), "Know exactly where<br>you <em>lose strokes.</em>",
     "Track every round hole-by-hole. FIR, GIR, putts, scrambling — the data that shows where to practice.",
     "stats-1.jpg", "Hole-by-hole entry", "stats-2.jpg", "Stats dashboard",
     [("18-hole tracking", "Score, fairways, greens, putts, scrambling per hole"),
      ("Trends over time", "See which stats are improving and which need work"),
      ("Practice connection", "Stats feed into Practice Assistant recommendations")]),

    ("D05", "Sim Lab", (0,237,4), "Built for your<br><em>launch monitor.</em>",
     "20 precision tests designed for Trackman, Mevo+, SkyTrak, and simulator sessions. Real data, real improvement.",
     "sim-1.jpg", "Sim Lab drills", "sim-2.jpg", "Simulator test",
     [("20 simulator tests", "Distance control, proximity, consistency challenges"),
      ("Launch monitor data", "Works with Trackman, Mevo+, SkyTrak, and more"),
      ("Performance tracking", "Track your simulator improvement over time")]),

    ("D06", "Structured Practice", (162,89,255), "Stop wasting time<br>at the <em>range.</em>",
     "Guided 30-60 minute sessions that mix technical work, variable practice, and scored challenges. Structure that works.",
     "assistant-main.jpg", "Session overview", "assistant-pressure.jpg", "Pressure phase",
     [("3-phase structure", "Block practice → variable → scored challenge"),
      ("Time-boxed", "20, 30, or 60 minute sessions that fit your schedule"),
      ("Scored output", "Every session produces a score you can track over time")]),

    ("D07", "Short Game HCP", (0,237,4), "Your putting has<br>a <em>handicap.</em>",
     "Scoring Zone tracks your putting, chipping, and overall short game as a separate handicap — updated after every drill.",
     "putting-score-3.jpg", "Benchmark levels", "benchmarks.jpg", "All benchmarks",
     [("Separate HCPs", "Putting HCP, chipping HCP, combined short game HCP"),
      ("Updated every session", "Complete a drill → your HCP recalculates instantly"),
      ("Benchmark comparison", "See where you rank: Tour, Scratch, Under 5, Under 10")]),

    ("D08", "Benchmarks", (245,197,24), "Are you tour level<br>from <em>6 feet?</em>",
     "Every drill in Scoring Zone has benchmarks from Tour Pro to 15+ handicap. Know exactly where you stand.",
     "putting-score-3.jpg", "Score to beat", "putting-drills-1.jpg", "All drills scored",
     [("8 benchmark levels", "Tour Pro, Elite, Scratch, Under 3, 5, 6, 10, 15"),
      ("Per-drill targets", "Each drill has specific scores for each level"),
      ("Track progression", "Watch yourself move up benchmark levels over weeks")]),

    ("D09", "Practice Notes", (162,89,255), "Remember what<br>you <em>worked on.</em>",
     "The practice notepad lets you log what you're focusing on — so every session has purpose and continuity.",
     "assistant-main.jpg", "Notepad feature", "assistant-clock.jpg", "Clock system",
     [("Session notes", "Write what you're working on before each practice"),
      ("Focus tracking", "The app remembers your focus areas across sessions"),
      ("Clock system", "Reference guide for wedge carry distances — always handy")]),

    ("D10", "Pressure Test", (255,96,48), "Practice under<br><em>real pressure.</em>",
     "Timer, penalties, consecutive requirements — drills that simulate the pressure of a real round. Build nerves of steel.",
     "assistant-pressure.jpg", "Pressure combine", "elite-challenge.jpg", "Elite challenge",
     [("Timer pressure", "Clock running — no time for doubt or second-guessing"),
      ("Penalty system", "Miss = restart or lose points. Real consequences"),
      ("Transfer to course", "Pressure practice builds the nerves you need on #18")]),
]

for sid, tag, color, headline, sub, i1, l1, i2, l2, pills in features:
    DESIGNS.append({
        "id": sid,
        "format": "feature",
        "html": _feature_html(tag, color, headline, sub, i1, l1, i2, l2, pills),
    })


# ═══════════════════════════════════════════════════════════════════════════
# WRITE ALL HTML FILES
# ═══════════════════════════════════════════════════════════════════════════

# Add the 4 already-done designs (A01, B01, C01, D01) by copying them
already_done = {"A01", "B01", "C01", "D01"}

for d in DESIGNS:
    html_path = OUT_DIR / f"{d['id']}.html"
    html_path.write_text(d["html"], encoding="utf-8")

print(f"Generated {len(DESIGNS)} HTML files in {OUT_DIR}")
print(f"(A01, B01, C01, D01 already exist as standalone files)")
print(f"Total designs including originals: {len(DESIGNS) + 4}")
