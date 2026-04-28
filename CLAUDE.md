# CLAUDE.md â My Reading Alcove

This file gives Claude full context on this project so sessions can resume without re-explaining.

## Project Overview
My Reading Alcove is a personal book tracking web app. Users can log books they've read, store cover art, ratings, summaries, read dates, and format (paper/ebook/audiobook). It has a barcode scanner for ISBN lookup, Google Books and Open Library API integration, CSV import/export, cover/ISBN backfill tools, and backup/restore. It is a PWA (installable on mobile).

## Repository & Deployment
Repo: https://github.com/dpj1951/my-reading-room
Working branch: reading-alcove
Primary live app: https://myreadingalcove.com (custom domain) / https://my-reading-room2.onrender.com
Platform: Render (Starter plan), Flask + Gunicorn
Database: Supabase PostgreSQL (Pro + IPv4, direct connection)
Render service ID: srv-d6fo4v1r0fns73ai5e2g
Render shell URL: https://dashboard.render.com/web/srv-d6fo4v1r0fns73ai5e2g/shell

## Pricing & Business Model
$1.99/month after a 30-day free trial
No credit card required to start trial
One plan, everything included
Stripe: NOT YET wired up (next major task)
Email: freetrial@myreadingalcove.com (Namecheap forwarding to Gmail, needs setup)

## Current Status (April 28, 2026)
MAINTENANCE_MODE=true in Render env vars â site closed to public
Preview bypass: myreadingalcove.com/?preview=alcove2026
215 books in library (213 read + 1 reading + 1 want to read)
myreadingalcove.com has DNS/CDN caching â use my-reading-room2.onrender.com to verify deploys

## Architecture
Framework: Flask + Gunicorn
Auth: Supabase Auth (JWT in session)
Templates: Jinja2 in /templates/
Procfile: web: gunicorn app:app --bind 0.0.0.0:$PORT --timeout 120

Key files:
- app.py â main Flask app (all routes)
- templates/landing.html â public landing page
- templates/books.html â library view with shelves
- templates/add.html â add book page
- templates/edit.html â edit book page
- templates/authors.html â authors view
- templates/home.html â logged-in dashboard

## Book Status System
"read" â main grid, sorted by read_date desc
"reading" â Currently Reading horizontal scroll shelf (top of books page)
"want_to_read" â Want to Read shelf (bottom of books page)
Default is "read" if no status set

## Currently Reading Shelf Flow
Add/edit book, set status to Reading
Book appears in horizontal scroll shelf at top of books page
Click cover â open edit page â set read date + status=Read â save
Book moves to main grid as most recent

## What Was Done April 28 2026

### books.html Nav Header — DONE
- Nav header now matches authors.html exactly
- Added :root CSS variables to books.html (--accent, --muted, --border, --text, --bg, --surface, --card, --radius)
- Updated nav CSS: DM Serif Display font, var(--accent) gold title color, var(--muted) Home link, height 64px, rgba(14,14,18,0.85) background

## What Was Done April 27 2026

### Encoding Fix â DONE
All three templates had triple-encoded UTF-8 (garbled emojis, em dashes, etc).
Fixed by triple-decoding bytes and pushing clean base64 directly via GitHub Contents API.
Files fixed: add.html, edit.html, books.html

### Free Tier Limit â REMOVED
Removed 20-book limit banner from add.html (template).
Removed is_subscriber() block from app.py add_manual_save route.
No free tier exists â all users get unlimited books.

### books.html Fixes â DONE
- Removed duplicate full HTML document that was concatenated at end of file
- Removed duplicate legacy bare cover-grid loop
- Fixed nav bar: added dark sticky background so Home button is visible
- Added ð Reading / ð Want to Read status badge pills under covers on shelf sections
- Badges are teal for Reading, purple for Want to Read

### authors.html â DONE
Added status badge pills to book rows â teal ð Reading, purple ð Want to Read.
Only shown for non-read books. Read books show no badge.

### Landing Page â DONE (April 26)
Full rewrite of templates/landing.html for $1.99/month pricing
Dark theme, DM Serif Display + DM Sans, animated floating book spines
Commit 830c4b2 on reading-alcove branch

### Currently Reading Shelf CSS â DONE (April 26)
Added horizontal scroll CSS to books.html (commit cb3a7bc)

## Token Push Workflow
Claude uses the GitHub Contents API via the Chrome extension to push files directly.
User pastes a short-lived token in chat â Claude pushes immediately â user revokes at github.com/settings/tokens
NEVER store tokens. Revoke immediately after each use.

## Render Deployment Notes
Auto-deploys on push to reading-alcove branch
If old page still serves after deploy: Render Shell -> kill -9 $(pgrep -f gunicorn)
Render restarts Gunicorn automatically after kill
Shell URL: https://dashboard.render.com/web/srv-d6fo4v1r0fns73ai5e2g/shell

## Chrome Extension
Browser 1, macOS, deviceId: faa72e7f-e3e3-4136-a503-62581d7b9376
Can access: github.com, dashboard.render.com
Cannot access: myreadingalcove.com, my-reading-room2.onrender.com
Use JS fetch() in extension to call GitHub API, push files via Contents API

## Next Tasks
1. Wire up Stripe ($1.99/month after 30-day trial)
2. Set up freetrial@myreadingalcove.com email forwarding (Namecheap -> Gmail)
3. Turn off maintenance mode when ready to launch
