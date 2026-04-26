# CLAUDE.md — My Reading Alcove

This file gives Claude full context on this project so sessions can resume without re-explaining.

## Project Overview
**My Reading Alcove** is a personal book tracking web app. Users can log books they've read, store cover art, ratings, summaries, read dates, and format (paper/ebook/audiobook). It has a barcode scanner for ISBN lookup, Google Books and Open Library API integration, CSV import/export, cover/ISBN backfill tools, and backup/restore. It is a PWA (installable on mobile).

## Repository & Deployment
- **Repo:** https://github.com/dpj1951/my-reading-room
- **Working branch:** reading-alcove
- **Primary live app:** https://myreadingalcove.com (custom domain) / https://my-reading-room2.onrender.com
- **Platform:** Render (Starter plan), Flask + Gunicorn
- **Database:** Supabase PostgreSQL (Pro + IPv4, direct connection)
- **Render service ID:** srv-d6fo4v1r0fns73ai5e2g
- **Render shell URL:** https://dashboard.render.com/web/srv-d6fo4v1r0fns73ai5e2g/shell

## Pricing & Business Model
- **$1.99/month** after a **30-day free trial**
- No credit card required to start trial
- One plan, everything included
- Stripe: NOT YET wired up (next major task)
- Email: freetrial@myreadingalcove.com (Namecheap forwarding to Gmail, needs setup)

## Current Status (April 26, 2026)
- MAINTENANCE_MODE=true in Render env vars — site closed to public
- Preview bypass: myreadingalcove.com/?preview=alcove2026
- 213 books in library
- myreadingalcove.com has DNS/CDN caching — use my-reading-room2.onrender.com to verify deploys

## Architecture
- Framework: Flask + Gunicorn
- Auth: Supabase Auth (JWT in session)
- Templates: Jinja2 in /templates/
- Procfile: web: gunicorn app:app --bind 0.0.0.0:$PORT --timeout 120
- Key files:
  - app.py — main Flask app (all routes)
  - templates/landing.html — public landing page
  - templates/books.html — library view with shelves
  - templates/add.html — add book page
  - templates/edit.html — edit book page
  - templates/home.html — logged-in dashboard

## Book Status System
- "read" — main grid, sorted by read_date desc
- "reading" — Currently Reading horizontal scroll shelf (top of books page)
- "want_to_read" — Want to Read shelf
- Default is "read" if no status set

## Currently Reading Shelf Flow
1. Add/edit book, set status to Reading
2. Book appears in horizontal scroll shelf at top of books page (gold-outlined covers, lift on hover)
3. Click cover, open edit page, set read date + status=Read, save
4. Book moves to main grid as most recent

## What Was Done April 26 2026

### Landing Page — DONE
- Full rewrite of templates/landing.html for $1.99/month pricing
- Dark theme, DM Serif Display + DM Sans, animated floating book spines
- Commit 830c4b2 on reading-alcove branch
- Visible at my-reading-room2.onrender.com (custom domain DNS still caching)

### Currently Reading Shelf CSS — DONE
- Added horizontal scroll CSS to books.html (commit cb3a7bc)
- .shelf-reading .cover-grid is now flex row with overflow-x scroll
- 110px wide covers, 165px tall, gold border, hover lift animation

### add.html Fix — PENDING
- Problem: garbled emoji encoding in format/status buttons
- Problem: "Free accounts limited to 20 books" banner must be removed (no free tier)
- Fix script: push_add.py (download from Claude outputs or recreate)
- Same encoding issues likely in edit.html and books.html shelf icons

## Terminal Push Workflow
```bash
# Set token silently
read -s GH_TOKEN
export GH_TOKEN

# Download file
curl -s 'https://raw.githubusercontent.com/dpj1951/my-reading-room/reading-alcove/templates/FILE.html' > ~/FILE.html

# Run push script (save as .py file, not heredoc)
python3 ~/push_script.py
```
NEVER paste tokens in chat — revoke immediately at github.com/settings/tokens after each use.

## Render Deployment Notes
- Auto-deploys on push to reading-alcove branch
- If old page still serves after deploy: Render Shell -> kill -9 $(pgrep -f gunicorn)
- Render restarts Gunicorn automatically after kill
- Shell URL: https://dashboard.render.com/web/srv-d6fo4v1r0fns73ai5e2g/shell

## Chrome Extension
- Browser 1, macOS, deviceId: faa72e7f-e3e3-4136-a503-62581d7b9376
- Can access: github.com, dashboard.render.com
- Cannot access: myreadingalcove.com, my-reading-room2.onrender.com
- Use JS fetch() in extension to call GitHub API, push files via Contents API

## Next Tasks
1. Push push_add.py fix (remove 20-book limit banner, fix emoji encoding in add.html)
2. Fix encoding in edit.html and books.html shelf icons
3. Wire up Stripe ($1.99/month after 30-day trial)
4. Set up freetrial@myreadingalcove.com email forwarding (Namecheap -> Gmail)
5. Turn off maintenance mode when ready to launch
