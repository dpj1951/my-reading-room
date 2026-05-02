# CLAUDE.md ÃÂ¢ÃÂÃÂ My Reading Alcove

This file gives Claude full context on this project so sessions can resume without re-explaining.

## Project Overview
My Reading Alcove is a personal book tracking web app. Users can log books they've read, store cover art, ratings, summaries, read dates, and format (paper/ebook/audiobook). It has a barcode scanner for ISBN lookup, Google Books and Open Library API integration, CSV import/export, cover/ISBN backfill tools, and backup/restore. It is a PWA (installable on mobile).

## Repository & Deployment
- Repo: https://github.com/dpj1951/my-reading-room
- Working branch: reading-alcove
- Primary live app: https://myreadingalcove.com / https://my-reading-room2.onrender.com
- Platform: Render (Starter $7/mo ÃÂ¢ÃÂÃÂ always-on, no sleep)
- Flask + Gunicorn
- Database: Supabase PostgreSQL (Pro + IPv4, direct connection)
- Render service ID: srv-d6fo4v1r0fns73ai5e2g
- Render shell URL: https://dashboard.render.com/web/srv-d6fo4v1r0fns73ai5e2g/shell

## Pricing & Business Model
- $1.99/month after a 30-day free trial
- No credit card required to start trial
- One plan, everything included
- Stripe: NOT YET wired up (next task after author shelf)
- Email: freetrial@myreadingalcove.com (Namecheap Private Email, forwarding to Gmail)

## Current Status (April 30, 2026)
- MAINTENANCE_MODE=true in Render env vars ÃÂ¢ÃÂÃÂ site closed to public
- Preview bypass: myreadingalcove.com/?preview=alcove2026
- 215 books in library (213 read + 1 reading + 1 want to read)
- Use my-reading-room2.onrender.com to verify deploys (DNS caching on custom domain)

## Architecture
- Framework: Flask + Gunicorn
- Auth: Supabase Auth (JWT in session)
- Templates: Jinja2 in /templates/
- Procfile: web: gunicorn app:app --bind 0.0.0.0:$PORT --timeout 120

### Key files
- app.py ÃÂ¢ÃÂÃÂ main Flask app (all routes)
- templates/landing.html ÃÂ¢ÃÂÃÂ public landing page
- templates/books.html ÃÂ¢ÃÂÃÂ library view with shelves
- templates/add.html ÃÂ¢ÃÂÃÂ add book page
- templates/edit.html ÃÂ¢ÃÂÃÂ edit book page
- templates/authors.html ÃÂ¢ÃÂÃÂ authors view
- templates/home.html ÃÂ¢ÃÂÃÂ logged-in dashboard (nav: Books, Authors, Add a Book, Utilities, Stats)
- templates/stats.html ÃÂ¢ÃÂÃÂ reading stats page

## Book Status System
- 'read' ÃÂ¢ÃÂÃÂ main grid, sorted by read_date desc
- 'reading' ÃÂ¢ÃÂÃÂ Currently Reading horizontal scroll shelf (top of books page)
- 'want_to_read' ÃÂ¢ÃÂÃÂ Want to Read shelf (bottom of books page)
- Default is 'read' if no status set

## Supabase Schema (books table ÃÂ¢ÃÂÃÂ 14 columns)
id, title, author, isbn, format, pages (varchar), copyright_year, read_date (varchar), rating (varchar/float), cover_url, summary, read_time_hrs, user_id, status
- read_date formats: %m/%d/%y, %Y-%m-%d, %m/%d/%Y
- pages stored as varchar string ÃÂ¢ÃÂÃÂ parse with int()
- rating stored as float (supports half-stars e.g. 2.5, 3.0, 4.5)

## Google Books API
- Key stored in Render env var: GOOGLE_BOOKS_API_KEY
- Already wired into app.py: GOOGLE_BOOKS_API_KEY = os.environ.get('GOOGLE_BOOKS_API_KEY', '')
- All Google Books calls pass 'key': api_key in params
- Key restricted in Google Cloud Console (project: my-project-37669-book-trace)
- HTTP referrer restricted to: myreadingalcove.com/* and my-reading-room2.onrender.com/*
- Quota: 10,000 requests/day

## Scalability Notes
- Render Starter ($7/mo): always-on, 512MB RAM, 0.5 CPU ÃÂ¢ÃÂÃÂ good for early growth
- Set WEB_CONCURRENCY=3 env var on Render when traffic grows
- Supabase Pro: handles 100k MAU; switch to PgBouncer pooler at ~200 concurrent users
- CSV import does synchronous Google Books/Open Library lookups ÃÂ¢ÃÂÃÂ future: use ThreadPoolExecutor
- Render pricing update coming August 1, 2026 ÃÂ¢ÃÂÃÂ review before that date

## What Was Done May 2, 2026
Find Missing Read Dates — updated to show date_added as hint
date_added column added to Supabase books table (timestamptz DEFAULT now())
Book model updated: date_added = db.Column(db.DateTime, default=datetime.utcnow)
datetime import updated: from datetime import date, datetime
All add paths stamp date_added: manual add, add_want_to_read, CSV import
missing_dates route returns date_added formatted MM/DD/YYYY as hint per book
tools.html shows green "added MM/DD/YYYY" hint next to each missing-date book

DNF (Did Not Finish) shelf added — May 2, 2026
New status value: dnf alongside read, reading, want_to_read
books.html: DNF shelf below Want to Read, red-tinted label, dimmed/grayscale covers
edit.html: ✗ DNF button added to Reading Status row
add.html: ✗ DNF button added to Reading Status row
app.py books route: dnf list filtered and passed to template
CSS: .shelf-dnf, .dnf-label styles added

Find Missing Read Dates utility added to More Tools
New button: Find Missing Read Dates (calendar icon)
Lists all books with no read_date recorded, sorted alphabetically
Each row is a clickable link to /book/<id>/edit
New Flask route: GET /utilities/missing-dates using Book.query pattern
utilities.html More Tools card updated to mention "find missing pages & dates"

Find & Fill Missing Page Counts utility added to More Tools
New button: Find & Fill Missing Page Counts (replaces simple lister)
Auto-lookups page counts from Open Library (by ISBN, then title/author) and Google Books (by ISBN, then title/author) Ã¢ÂÂ 4 sources tried in order
Progress bar shows live lookup progress across all missing books
Auto-saves all found page counts in one batch POST to /utilities/missing-pages-save
Results list: found books shown in green with page count, not-found in grey with click-to-edit link
New Flask routes: GET /utilities/missing-pages, POST /utilities/missing-pages-save
Both use SQLAlchemy Book.query pattern (not Supabase client)
More Tools card description on utilities.html updated to include "find missing pages"
First run: 24 of 33 missing books auto-filled (73% hit rate)

What Was Done May 1, 2026
- **Author shelf feature** ÃÂ¢ÃÂÃÂ full publication shelf for each author
  - Author name on authors page is now a clickable pill button
  - New route `/author/<name>` renders author_shelf.html
  - Google Books API called CLIENT-SIDE (browser fetch) ÃÂ¢ÃÂÃÂ server-side calls blocked by Render IP
  - Books cross-referenced with user library: read=blue glow, reading=teal, want=purple, unowned=dimmed
  - Clicking unowned book opens confirm modal, adds to want_to_read, card flips in place (no page reload)
  - Deleting from library restores unowned state on next shelf load
  - New Flask route `/add_want_to_read` POST endpoint
  - New template: `templates/author_shelf.html`
  - Key bug fixed: year sent as int from JS, route called .strip() ÃÂ¢ÃÂÃÂ fixed with str() conversion
  - Want to Read shelf on books page now sorted by insertion order (newest last)

## What Was Done April 30, 2026

### Stats Page
- New /stats route added to app.py (inserted after /books route)
- New templates/stats.html ÃÂ¢ÃÂÃÂ dark theme, DM Serif Display, matches app style
- Summary cards: Total Books, Total Pages, This Month, This Year, Pages/Week (52-wk avg), Pages This Year
- Bar chart toggle: Books or Pages per month (last 12 months)
- By-year table with progress bars for books and pages (newest first)
- Nudge banner when books missing page counts or read dates
- Stats button added to home.html nav (after Utilities)
- Stats page nav: Library, Authors, Add, Utilities, Stats (active), Home
- pages and read_date are nullable ÃÂ¢ÃÂÃÂ stats work with partial data, users self-edit to improve

### Google Books API Key
- Created in Google Cloud Console
- Restricted to Books API only + HTTP referrers
- Added to Render env vars as GOOGLE_BOOKS_API_KEY
- Code was already wired up ÃÂ¢ÃÂÃÂ no app.py changes needed

### Render Plan Confirmed
- Workspace: Hobby (legacy)
- Service instance: Starter ($7/mo) ÃÂ¢ÃÂÃÂ always-on, no sleep

## What Was Done April 29, 2026

### Email Setup
- freetrial@myreadingalcove.com and support@myreadingalcove.com in Namecheap Private Email
- Both added to Gmail via POP3; Send mail as support@ via SMTP (port 587, TLS)

### Half-Star Ratings
- Upgraded from whole stars (1-5) to half-star increments (0.5-5.0)
- add.html + edit.html: half-star picker UI
- books.html + authors.html: star display with half symbol
- Rating stored as float

## What Was Done April 28, 2026
- books.html nav header updated to match authors.html
- Added :root CSS variables to books.html

## What Was Done April 27, 2026
- Fixed triple-encoded UTF-8 in add.html, edit.html, books.html
- Removed 20-book free tier limit from add.html and app.py
- Fixed books.html: removed duplicate HTML, fixed nav, added status badge pills
- authors.html: added status badge pills

## What Was Done April 26, 2026
- Full rewrite of landing.html for $1.99/month pricing
- Added horizontal scroll CSS for Currently Reading shelf

## Token Push Workflow
- User pastes short-lived GitHub token in chat
- Claude pushes via GitHub Contents API through Chrome extension
- User revokes immediately at github.com/settings/tokens
- NEVER store tokens. Revoke immediately after each use.

## Render Deployment Notes
- Auto-deploys on push to reading-alcove branch
- If old page serves after deploy: Render Shell -> kill -9 $(pgrep -f gunicorn)
- Render restarts Gunicorn automatically

## Chrome Extension
- Browser 1, macOS, deviceId: faa72e7f-e3e3-4136-a503-62581d7b9376
- Can access: github.com, dashboard.render.com
- Cannot access: myreadingalcove.com, my-reading-room2.onrender.com
- Use JS fetch() in extension to call GitHub API

## Next Tasks
1. Wire up Stripe ($1.99/month after 30-day trial)
2. Second new feature (TBD ÃÂ¢ÃÂÃÂ discuss next session)
3. Turn off maintenance mode when ready to launch
4. Review Render pricing changes before August 1, 2026