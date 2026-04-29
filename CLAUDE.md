# CLAUDE.md ÃÂ¢ÃÂÃÂ My Reading Alcove

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
MAINTENANCE_MODE=true in Render env vars ÃÂ¢ÃÂÃÂ site closed to public
Preview bypass: myreadingalcove.com/?preview=alcove2026
215 books in library (213 read + 1 reading + 1 want to read)
myreadingalcove.com has DNS/CDN caching ÃÂ¢ÃÂÃÂ use my-reading-room2.onrender.com to verify deploys

## Architecture
Framework: Flask + Gunicorn
Auth: Supabase Auth (JWT in session)
Templates: Jinja2 in /templates/
Procfile: web: gunicorn app:app --bind 0.0.0.0:$PORT --timeout 120

Key files:
- app.py ÃÂ¢ÃÂÃÂ main Flask app (all routes)
- templates/landing.html ÃÂ¢ÃÂÃÂ public landing page
- templates/books.html ÃÂ¢ÃÂÃÂ library view with shelves
- templates/add.html ÃÂ¢ÃÂÃÂ add book page
- templates/edit.html ÃÂ¢ÃÂÃÂ edit book page
- templates/authors.html ÃÂ¢ÃÂÃÂ authors view
- templates/home.html ÃÂ¢ÃÂÃÂ logged-in dashboard

## Book Status System
"read" ÃÂ¢ÃÂÃÂ main grid, sorted by read_date desc
"reading" ÃÂ¢ÃÂÃÂ Currently Reading horizontal scroll shelf (top of books page)
"want_to_read" ÃÂ¢ÃÂÃÂ Want to Read shelf (bottom of books page)
Default is "read" if no status set

## Currently Reading Shelf Flow
Add/edit book, set status to Reading
Book appears in horizontal scroll shelf at top of books page
Click cover ÃÂ¢ÃÂÃÂ open edit page ÃÂ¢ÃÂÃÂ set read date + status=Read ÃÂ¢ÃÂÃÂ save
Book moves to main grid as most recent

## What Was Done April 29, 2026

### Email Setup â DONE
Set up two @myreadingalcove.com mailboxes in Namecheap Private Email:
- freetrial@myreadingalcove.com
- support@myreadingalcove.com
Both added to Gmail (dpjohnson1951@gmail.com) via POP3 (mail.privateemail.com, port 995, SSL).
"Send mail as" configured for support@ via SMTP (mail.privateemail.com, port 587, TLS).
Key fix: mailboxes must be TURNED ON in Namecheap Private Email dashboard before Gmail can connect.
Key fix: username must be full email address (not just "freetrial").
freetrial@ verification email pending (check Gmail sidebar label).

### Half-Star Ratings â DONE
Upgraded rating system from whole stars (1â5) to half-star increments (0.5â5.0).
- add.html: New half-star picker UI â hover left half of star = 0.5, right half = full star
- edit.html: Same half-star picker, pre-fills existing rating on page load via initStars()
- books.html: Star rating now displayed under each book cover in main grid
- JS functions: renderStars(), hoverStar(), unhoverStars(), clickStar() replace old setRating()
- Rating stored as float in hidden input (f-rating), e.g. 2.5, 3.0, 4.5

### Rating Display Follow-up (April 29 evening)
- books.html: Fixed triple-encoding garble (ÃÂÃÂ mess) — same fix pattern as April 27
- books.html: Book grid now shows ★★★½ under covers, or blue "NR" badge if no rating set
- authors.html: Rating display added below book title in each row — ★★★½ or blue "NR"
- Note: Half-star displayed as ½ symbol to save space
- TODO: Verify Supabase 'rating' column is NUMERIC/FLOAT (not INTEGER) to support half values

## What Was Done April 28 2026

### books.html Nav Header Ã¢ÂÂ DONE
- Nav header now matches authors.html exactly
- Added :root CSS variables to books.html (--accent, --muted, --border, --text, --bg, --surface, --card, --radius)
- Updated nav CSS: DM Serif Display font, var(--accent) gold title color, var(--muted) Home link, height 64px, rgba(14,14,18,0.85) background

## What Was Done April 27 2026

### Encoding Fix ÃÂ¢ÃÂÃÂ DONE
All three templates had triple-encoded UTF-8 (garbled emojis, em dashes, etc).
Fixed by triple-decoding bytes and pushing clean base64 directly via GitHub Contents API.
Files fixed: add.html, edit.html, books.html

### Free Tier Limit ÃÂ¢ÃÂÃÂ REMOVED
Removed 20-book limit banner from add.html (template).
Removed is_subscriber() block from app.py add_manual_save route.
No free tier exists ÃÂ¢ÃÂÃÂ all users get unlimited books.

### books.html Fixes ÃÂ¢ÃÂÃÂ DONE
- Removed duplicate full HTML document that was concatenated at end of file
- Removed duplicate legacy bare cover-grid loop
- Fixed nav bar: added dark sticky background so Home button is visible
- Added ÃÂ°ÃÂÃÂÃÂ Reading / ÃÂ°ÃÂÃÂÃÂ Want to Read status badge pills under covers on shelf sections
- Badges are teal for Reading, purple for Want to Read

### authors.html ÃÂ¢ÃÂÃÂ DONE
Added status badge pills to book rows ÃÂ¢ÃÂÃÂ teal ÃÂ°ÃÂÃÂÃÂ Reading, purple ÃÂ°ÃÂÃÂÃÂ Want to Read.
Only shown for non-read books. Read books show no badge.

### Landing Page ÃÂ¢ÃÂÃÂ DONE (April 26)
Full rewrite of templates/landing.html for $1.99/month pricing
Dark theme, DM Serif Display + DM Sans, animated floating book spines
Commit 830c4b2 on reading-alcove branch

### Currently Reading Shelf CSS ÃÂ¢ÃÂÃÂ DONE (April 26)
Added horizontal scroll CSS to books.html (commit cb3a7bc)

## Token Push Workflow
Claude uses the GitHub Contents API via the Chrome extension to push files directly.
User pastes a short-lived token in chat ÃÂ¢ÃÂÃÂ Claude pushes immediately ÃÂ¢ÃÂÃÂ user revokes at github.com/settings/tokens
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
