# ScoringZone Content Command Centre

A local dashboard for reviewing, approving, and posting AI-researched golf content to Instagram and X.

## Quick Start

```bash
cd content-command-centre
./START_DASHBOARD.sh
```

Then open **http://localhost:5050** in your browser.

---

## Setup: Social Media Credentials

Edit `.env` and fill in your credentials:

### Instagram
1. Go to [Meta Developer Console](https://developers.facebook.com/apps/)
2. Create an app → Add Instagram Basic Display product
3. Connect your Instagram Professional account
4. Generate a **long-lived user access token** (valid 60 days, refresh monthly)
5. Find your **Instagram Business Account ID** in the app dashboard

### X / Twitter
1. Go to [developer.twitter.com](https://developer.twitter.com/en/apps)
2. Create an app — set permissions to **Read + Write**
3. Generate API Key, API Secret, Access Token, Access Token Secret

### Imgur (needed for Instagram image hosting)
1. Go to [api.imgur.com/oauth2/addclient](https://api.imgur.com/oauth2/addclient)
2. Register an **Anonymous usage** app (free)
3. Copy the **Client ID** (not the secret)

---

## Workflow

1. **Research runs** (manually or scheduled) add new packages to `packages/`
2. Open the dashboard → review each post's images + captions
3. Edit captions if needed (character count shown for each platform)
4. Click **Approve** to mark as ready
5. Click **Post to Instagram** and/or **Post to X** — done ✓

---

## File Structure

```
content-command-centre/
├── dashboard.py          # Flask server (run this)
├── dashboard.html        # Frontend UI (auto-served)
├── poster.py             # Instagram + X posting logic
├── config.py             # Paths + settings
├── .env                  # Your API keys (never commit this)
├── scoringzone_logo.png  # Brand logo for image overlays
├── packages/             # Generated content packages
│   └── cycle_XXXX_topic/
│       ├── image_01.jpg
│       ├── caption_instagram.txt
│       ├── caption_x.txt
│       ├── manifest.json
│       └── brief_summary.md
├── history/              # Raw research data archive
├── outputs/              # Cycle output files
└── logs/                 # Server logs
```
