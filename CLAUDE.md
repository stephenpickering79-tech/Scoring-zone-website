# Scoring Zone Landing Page

## Project Overview

Simplar Single-page signup website for Scoring Zone early access users, a golf short game performance app. Early access framing. Early access bage.  Static HTML files with embedded CSS and JavaScript—no build step required. Focuses on branding from website and app.  Keep the website simple with logo, main strap line and sign up box which has a link to the app one users have entered their details, one they sumbitt form they can click link to the app.  promod video is underneath to present the product. 

## Related Sites

- **Live Site**: http://thescoringzone.surge.sh/#
- **Live Site**: https://the-scoring-zone.vercel.app/

##media file: inbed promo video file to below the form sign up 

## Tech Stack

- **Framework**: Static HTML (no build step)
- **Styling**: Embedded CSS
- **JavaScript**: Vanilla JS, embedded
- **Hosting**: Lovable/Netlify
- **Fonts**: Inter or similar sans-serif (Google Fonts CDN)

## File Structure

```
/Users/stephenpickering/Documents/Claude Code /Scoring Website/
├── index.html          # Main landing page (hero, features, how it works, drills, CTA)
├── CLAUDE.md           # This file
└── assets/             # Images (golf balls, greens, app screenshots)
```

## Git Workflow

### Branch Naming Convention

Feature branches use the `feature/` prefix:
- `feature/hero-redesign`
- `feature/drills-section`
- `feature/cta-optimization`

### Merging Feature Branches

When merging multiple feature branches into main:

```bash
# 1. Check current status and list branches
git status
git branch -a

# 2. Merge each feature branch
git merge feature/hero-redesign -m "Merge feature/hero-redesign: description"
git merge feature/drills-section -m "Merge feature/drills-section: description"

# 3. Push to remote
git push origin main
```

### IMPORTANT: Handling index.html Conflicts

Feature branches often use `index.html` as their main file during development. When merging, this can **overwrite the main landing page**.

**After merging, always verify:**
1. `index.html` contains the **main landing page** (title: "Scoring Zone | Pressure Test Your Short Game")
2. Feature content is integrated properly

**If a feature branch overwrote index.html:**
```bash
# 1. Save the feature content to a backup
cp index.html index_backup.html

# 2. Restore the original landing page from before the merge
git show <commit-before-merge>:index.html > index.html

# 3. Commit the fix
git add index.html
git commit -m "fix: Restore landing page after merge"
```

**To find the original index.html:**
```bash
# View commit history
git log --oneline

# Show index.html from a specific commit
git show f87222a:index.html | head -20
```

## Design System

### Colors
| Token | Hex | Usage |
|-------|-----|-------|
| Golf green primary | `#4CAF50` | Accents, CTAs, buttons |
| Golf green light | `#66BB6A` | Hover states, secondary elements |
| Golf green dark | `#388E3C` | Active states, borders |
| Dark background | `#0a0a0a` | Main background |
| Card gray | `#111111` | Cards, sections |
| Text white | `#ffffff` | Headlines, body text |
| Accent gold | `#FFD700` | Highlights, badges (e.g., Elite Mode) |

### Typography
- **Font**: Inter (or similar clean sans-serif)
- **Weights**: 300-700
- **Letter spacing**: -0.02em (tight for modern look)

### Corner Radii
Modern, slightly rounded for approachability:
- Small: `6px`
- Medium: `8px`
- Large: `12px`

### Logo
"SCORING ZONE" with target icon, golf ball imagery. Use green accent for "ZONE".

## Page Structure

### index.html (Main Landing Page)
1. **Hero** — Headline "PRESSURE TEST YOUR SHORT GAME", subtitle, CTA buttons ("Start Practicing Free", "Download App"), golf ball image overlay
2. **Features** — 6 cards: Scoring Drills, Pressure Mode, Track Progress, Compete & Compare, Performance Analytics, Quick Sessions
3. **How It Works** — 4-step process: Pick a Drill, Hit Your Shots, Log Your Score, Level Up
4. **Sample Drills** — 4 challenge cards: Up & Down Challenge (Chipping), Ladder Putting (Putting), Bunker Escape (Bunker), Pitch Perfect (Pitching) with difficulty levels
5. **Stats Preview** — Mini dashboard showing sample HCP, drills done, level/XP
6. **Testimonials/Social Proof** — User quotes, app store ratings
7. **CTA** — Final call-to-action "Ready to Lower Your Scores?" with app link
8. **Footer** — Logo, nav links (Home, Practice, Stats, Settings), copyright

## Interactive Features

- Scroll-triggered reveal animations via Intersection Observer
- Animated progress bars and counters (e.g., drills completed)
- Mouse-following cursor effect (desktop only)
- Scroll progress indicator in header
- Smooth scroll navigation to sections
- Mobile-responsive with touch-friendly CTAs

## Deployment

### Deploy to Production
```bash
# If using Netlify
netlify deploy --prod

# Or via Lovable's deploy button
```

### Preview Deploy
```bash
netlify deploy
```

### Requirements
- Netlify CLI installed (`npm install -g netlify-cli`) or Lovable account
- Authenticated with hosting platform

## External Dependencies

- **App Links**: Direct to https://the-scoring-zone.lovable.app/
- **Google Fonts**: Inter font family via CDN
- **No npm packages** — Zero build dependencies

## Common Tasks

### Update Content
Edit index.html directly. All content, styles, and scripts are embedded.

### Change Colors
Search for hex codes:
- Primary green: `#4CAF50`
- Light green: `#66BB6A`
- Dark green: `#388E3C`

### Update App Links
Search for `https://the-scoring-zone.lovable.app/` and replace if needed.

### Add/Remove Features or Drills
Find the relevant section (e.g., `.features-grid` or `.drills-grid`). Each item is a `.card` or `.drill-card` element.

### Update Stats Preview
Locate the `.stats-preview` section. Modify counters and labels as needed.

## Notes

- Keep the single-file architecture — no bundlers or build steps
- Maintain the green golf theme for branding consistency
- Test animations after content changes (scroll reveals, counters)
- Ensure mobile-first design for golfers on the go
- **index.html is the main landing page** — don't overwrite with unrelated content
- Align with app's gamified tone: Use urgent, motivational language (e.g., "Beat your benchmarks", "Simulate pressure")</content>
<parameter name="filePath">/Users/stephenpickering/Documents/Claude Code /Scoring Website/CLAUDE.md