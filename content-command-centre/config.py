"""
config.py — Central config for the ScoringZone Golf Content Autoresearch system.

Edit the paths here if you move the project folder.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# ─────────────────────────────────────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────────────────────────────────────

# Base directory = folder containing this file
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
PACKAGES_DIR = os.path.join(BASE_DIR, "packages")
OUTPUTS_DIR  = os.path.join(BASE_DIR, "outputs")
HISTORY_DIR  = os.path.join(BASE_DIR, "history")
LOGS_DIR     = os.path.join(BASE_DIR, "logs")
ASSETS_DIR   = os.path.join(BASE_DIR, "assets")

# Ensure key dirs exist
for _d in [PACKAGES_DIR, OUTPUTS_DIR, HISTORY_DIR, LOGS_DIR]:
    os.makedirs(_d, exist_ok=True)

# ─────────────────────────────────────────────────────────────────────────────
# Environment
# ─────────────────────────────────────────────────────────────────────────────

load_dotenv(os.path.join(BASE_DIR, ".env"), override=False)

# ─────────────────────────────────────────────────────────────────────────────
# Research settings
# ─────────────────────────────────────────────────────────────────────────────

MAX_YOUTUBE_RESULTS  = 15
MAX_TRENDS_KEYWORDS  = 10
TOP_N_TOPICS         = 5   # How many top topics to package each cycle

# Social captions
INSTAGRAM_HASHTAGS = [
    "#golf", "#shortgame", "#golfpractice", "#golftips",
    "#chipping", "#putting", "#golfdrills", "#scoringzone",
    "#golfer", "#improveyourgolf",
]
X_HASHTAGS = ["#golf", "#shortgame", "#golfpractice", "#scoringzone"]
