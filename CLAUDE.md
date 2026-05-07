# My Reading Alcove

This file gives Claude full context on this project so sessions can resume without re-explaining.

---

## Project Overview

My Reading Alcove is a personal book tracking web app. Users can log books they've read, store cover art, ratings, summaries, read dates, and format (paper/ebook/audiobook). It has a barcode scanner for ISBN lookup, Google Books and Open Library API integration, CSV import/export, cover/ISBN backfill tools, and backup/restore. It is a PWA (installable on mobile).

---

## Repository & Deployment

- Repo: https://github.com/dpj1951/my-reading-room
- Working branch: `reading-alcove`
- Primary live app: https://myreadingalcove.com / https://my-reading-room2.onrender.com
- Platform: Render (Starter $7/mo â always-on, no sleep) Flask + Gunicorn
- Database: Supabase PostgreSQL (Pro + IPv4, direct connection)
- Render service ID: srv-d6fo4v1r0fns73ai5e2g
- Render shell URL: https://dashboard.render.com/web/srv-d6fo4v1r0fns73ai5e2g/shell

---

## Pricing & Business Model

- $1.99/month after a 30-day free trial
- No credit card required to start trial
- One plan, everything included
- Stripe: NOT YET wired up (next task)
- Email: freetrial@myreadingalcove.com (Namecheap Private Email, forwarding to Gmail)

---

## Current Status (May 7, 2026)

- MAINTENANCE_MODE=true in Render env vars â site closed to public
- Preview bypass: myreadingalcove.com/?preview=alcove2026
- 215 books in library (213 read + 1 reading + 1 want to read)
- Use my-reading-room2.onrender.com to verify deploys (DNS caching on custom domain)

---

## Architecture

- Framework: Flask + Gunicorn
- Auth: Supabase Auth (JWT in session)
- Templates: Jinja2 in /templates/
- Procfile: `web: gunicorn app:app --bind 0.0.0.0:$PORT --timeout 120`

### Key files

| File | Purpose |
|---|---|
| app.py | main Flask app (all routes) |
| templates/landing.html | public landing page |
| templates/books.html | library view with shelves |
| templates/add.html | add book page |
| templates/edit.html | edit book page |
| templates/authors.html | authors view |
| templates/home.html | logged-in dashboard (nav: Books, Authors, Add a Book, Utilities, Stats) |
| templates/stats.html | reading stats page |

---

## Book Status System

- `read` â main grid, sorted by read_date desc
- `reading` â Currently Reading horizontal scroll shelf (top of books page)
- `want_to_read` â Want to Read shelf (bottom of books page)
- `dnf` â Did Not Finish shelf (below Want to Read, dimmed/grayscale)
- Default is `read` if no status set

---

## Supabase Schema (books table â 14 columns)

`id, title, author, isbn, format, pages (varchar), copyright_year, read_date (varchar), rating (varchar/float), cover_url, summary, read_time_hrs, user_id, status`

- read_date formats: %m/%d/%y, %Y-%m-%d, %m/%d/%Y
- pages stored as varchar string â parse with int()
- rating stored as float (supports half-stars e.g. 2.5, 3.0, 4.5)
- date_added: timestamptz DEFAULT now() (added May 2, 2026)

---

## Google Books API

- Key stored in Render env var: GOOGLE_BOOKS_API_KEY
- Already wired into app.py: `GOOGLE_BOOKS_API_KEY = os.environ.get('GOOGLE_BOOKS_API_KEY', '')`
- All Google Books calls pass `'key': api_key` in params
- Key restricted in Google Cloud Console (project: my-project-37669-book-trace)
- HTTP referrer restricted to: myreadingalcove.com/* and my-reading-room2.onrender.com/*
- Quota: 10,000 requests/day

---

## Scalability Notes

- Render Starter ($7/mo): always-on, 512MB RAM, 0.5 CPU â good for early growth
- Set WEB_CONCURRENCY=3 env var on Render when traffic grows
- Supabase Pro: handles 100k MAU; switch to PgBouncer pooler at ~200 concurrent users
- CSV import does synchronous Google Books/Open Library lookups â future: use ThreadPoolExecutor
- **Render pricing update coming August 1, 2026 â review before that date**

---

## PWA Icons & Branding (updated May 6, 2026)

- static/icons/icon-192.png â PWA app icon 192Ã192 (blue alcove illustration on cream background)
- static/icons/icon-512.png â PWA app icon 512Ã512 (same illustration, higher res)
- static/icons/alcove_logo.png â standalone logo for home page footer (300Ã400 portrait)
- Home page footer logo: centered, 140px wide, 60% opacity, soft drop shadow
- All icons: blue line-art style matching the uploaded alcove illustration (person reading in arched alcove with bookshelves, lanterns, plants)
- manifest.json already references icon-192 and icon-512
- Source image: alcove_logo_copy.jpeg (portrait ~686Ã1024)
- Icon crop: square crop starting at ~22% from top of source image, capturing arch + reader + bookshelves + lanterns

---

## What Was Done May 7, 2026

### Updated PWA icons (icon-192 and icon-512) with new crop
- User provided new pre-cropped source image (window/reader illustration, portrait)
- Detected and removed large black border surrounding the illustration
- Found clean content bounds: rows 288–907, cols 275–685; trimmed stray bottom line artifacts
- Generated icon-192.png (192×192) and icon-512.png (512×512) centered on cream background
- Uploaded both to static/icons/ via GitHub web UI drag-and-drop
- Render auto-deployed on push to reading-alcove branch

## What Was Done May 6, 2026

### Fixed PWA launcher icons (icon-192 and icon-512)
- Discovered existing icon-192.png and icon-512.png were wrong (showed a barcode/columns logo, not the alcove illustration)
- User provided alcove_logo_copy.jpeg as source image
- Generated correct square crops using Pillow â crop starts at ~22% from top to show the sitting reader prominently
- icon-192.png: 192Ã192px square crop of alcove illustration
- icon-512.png: 512Ã512px square crop of same illustration
- Both uploaded to static/icons/ via GitHub web UI drag-and-drop
- Render auto-deployed on push to reading-alcove branch

---

## What Was Done May 4, 2026

### New app logo & PWA icons
- User uploaded alcove_logo.jpeg â blue line-art reading alcove illustration (portrait orientation)
- Generated PWA icons (192Ã192 and 512Ã512) from the illustration using canvas
- Generated alcove_logo.png (300Ã400) for home page footer logo
- Pushed 3 new/updated icon files to static/icons/
- Updated templates/home.html to add centered footer logo (140px wide, subtle, with drop shadow)

---

## What Was Done May 4, 2026 â Session 2 (Responsive Footer Logo)
- Created 3 responsive logo sizes: alcove_logo_sm.png (147Ã220), alcove_logo_md.png (206Ã307), alcove_logo_lg.png (270Ã402)
- All 3 uploaded to static/icons/ via GitHub web UI
- templates/home.html footer updated to use picture element with responsive breakpoints

---

## What Was Done May 2, 2026

- DNF button fix, date_added column, missing read dates tool updated
- DNF shelf added to books page
- Find Missing Read Dates utility added
- Find & Fill Missing Page Counts utility added (73% hit rate first run)

---

## What Was Done May 1, 2026

- Author shelf feature â full publication shelf per author with Google Books API (client-side)

---

## What Was Done April 30, 2026

- Stats page added (/stats route, stats.html)
- Google Books API key created and added to Render

---

## What Was Done April 29, 2026

- Email setup (freetrial@ and support@)
- Half-star ratings (0.5â5.0)

---

## What Was Done April 28, 2026

- books.html nav updated, CSS variables added

---

## What Was Done April 27, 2026

- Fixed UTF-8 encoding issues, removed 20-book limit, fixed books.html, added status badge pills

---

## What Was Done April 26, 2026

- Full rewrite of landing.html for $1.99/month pricing
- Added horizontal scroll CSS for Currently Reading shelf

---

## Token Push Workflow

1. User pastes short-lived GitHub token in chat
2. Claude pushes via GitHub Contents API through Chrome extension JS fetch()
3. User revokes immediately at github.com/settings/tokens

**NEVER store tokens. Revoke immediately after each use.**

---

## Render Deployment Notes

- Auto-deploys on push to reading-alcove branch
- If old page serves after deploy: Render Shell â kill -9 $(pgrep -f gunicorn) â Render restarts automatically

---

## Chrome Extension

- Browser 1, macOS, deviceId: faa72e7f-e3e3-4136-a503-62581d7b9376
- Can access: github.com, dashboard.render.com
- Cannot access: myreadingalcove.com, my-reading-room2.onrender.com
- Use JS fetch() in extension to call GitHub API
- Note: extension blocks SHA/base64 values returned from JS â use split workarounds to retrieve SHAs

---

## Next Tasks
- Wire up Stripe ($1.99/month after 30-day trial)
- Turn off maintenance mode when ready to launch
- Review Render pricing changes before August 1, 2026
- Consider reducing footer logo max-width (currently rendering large on desktop)
- Consider: date_started column when book moves to reading shelf
- Consider: stamp date_added on want_to_read â reading transition