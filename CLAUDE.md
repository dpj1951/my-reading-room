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
- Platform: Render (Starter $7/mo ÃÂ¢ÃÂÃÂ always-on, no sleep) Flask + Gunicorn
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

- MAINTENANCE_MODE=true in Render env vars ÃÂ¢ÃÂÃÂ site closed to public
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

- `read` ÃÂ¢ÃÂÃÂ main grid, sorted by read_date desc
- `reading` ÃÂ¢ÃÂÃÂ Currently Reading horizontal scroll shelf (top of books page)
- `want_to_read` ÃÂ¢ÃÂÃÂ Want to Read shelf (bottom of books page)
- `dnf` ÃÂ¢ÃÂÃÂ Did Not Finish shelf (below Want to Read, dimmed/grayscale)
- Default is `read` if no status set

---

## Supabase Schema (books table ÃÂ¢ÃÂÃÂ 14 columns)

`id, title, author, isbn, format, pages (varchar), copyright_year, read_date (varchar), rating (varchar/float), cover_url, summary, read_time_hrs, user_id, status`

- read_date formats: %m/%d/%y, %Y-%m-%d, %m/%d/%Y
- pages stored as varchar string ÃÂ¢ÃÂÃÂ parse with int()
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

- Render Starter ($7/mo): always-on, 512MB RAM, 0.5 CPU ÃÂ¢ÃÂÃÂ good for early growth
- Set WEB_CONCURRENCY=3 env var on Render when traffic grows
- Supabase Pro: handles 100k MAU; switch to PgBouncer pooler at ~200 concurrent users
- CSV import does synchronous Google Books/Open Library lookups ÃÂ¢ÃÂÃÂ future: use ThreadPoolExecutor
- **Render pricing update coming August 1, 2026 ÃÂ¢ÃÂÃÂ review before that date**

---

## PWA Icons & Branding (updated May 6, 2026)

- static/icons/icon-192.png ÃÂ¢ÃÂÃÂ PWA app icon 192ÃÂÃÂ192 (blue alcove illustration on cream background)
- static/icons/icon-512.png ÃÂ¢ÃÂÃÂ PWA app icon 512ÃÂÃÂ512 (same illustration, higher res)
- static/icons/alcove_logo.png ÃÂ¢ÃÂÃÂ standalone logo for home page footer (300ÃÂÃÂ400 portrait)
- Home page footer logo: centered, 140px wide, 60% opacity, soft drop shadow
- All icons: blue line-art style matching the uploaded alcove illustration (person reading in arched alcove with bookshelves, lanterns, plants)
- manifest.json already references icon-192 and icon-512
- Source image: alcove_logo_copy.jpeg (portrait ~686ÃÂÃÂ1024)
- Icon crop: square crop starting at ~22% from top of source image, capturing arch + reader + bookshelves + lanterns

---

## What Was Done May 12, 2026

### Fixed author shelf — fallback when Google Books unavailable
- Root cause: Google Books API returns 503 periodically; client-side fetch got empty result and showed "No books found"
- Fix: `fetchAllBooks()` now returns `{ books, apiError }` object; detects API errors and network failures
- `init()` falls back to showing the user's library books for that author when Google Books is unavailable
- Subtitle shows "· Google Books unavailable" notice when in fallback mode
- When Google Books is working normally, behavior is unchanged

### Fixed owner account showing expired trial banner
- Root cause: `get_user_role()` used `SUPABASE_ANON_KEY` to query `user_roles` table, but RLS policies block anon key (require `auth.uid()` match)
- Fix: added `SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")` to app.py
- `get_user_role()` now uses service role key (bypasses RLS), falling back to anon key if not set
- Service role key was already in Render env vars
- Owner row (`role='owner'`) was already in `user_roles` table since April 18 — just wasn't being read
- After fresh login, `session["user_role"]"` = `"owner"` correctly and banner is gone

## What Was Done May 9, 2026

### Stripe Test Mode Integration (full end-to-end)
- Created Stripe product "My Reading Alcove" â $1.99/month recurring (Price ID: price_1TVHJPRvjXqRXrTp1QXcjLTB)
- Added Stripe env vars to Render: STRIPE_PUBLISHABLE_KEY, STRIPE_SECRET_KEY, STRIPE_PRICE_ID, STRIPE_WEBHOOK_SECRET (placeholder)
- Added `stripe` to requirements.txt
- Added Stripe config + stripe.api_key init to app.py
- Added trial_end + user_role = 'trial' to session on successful signup
- Added context processor inject_trial_context() â injects trial_banner, trial_days_left, stripe_pub_key to all templates
- Added trial banner to home.html (3 states: info=green/30days, urgent=orange/<=7days, expired=red)
- Added routes: /subscribe/checkout, /subscribe/success, /subscribe/cancel, /subscribe/portal
- Added /stripe/webhook route with signature verification
- Added _stripe_patch() helper for Supabase profile updates on webhook events
- Tested full flow: banner shows â Stripe Checkout â test card 4242... â redirect back â "Your subscription is active" flash â banner gone
- Fixed: timedelta import missing (added to datetime import line)
- Fixed: redirect to /home after signup (was /books)
- Fixed: set trial_end at login if not already set

### Known issues to fix next session
- trial_end not being set for users who signed up before this deploy (they see expired immediately)
- Stripe webhook endpoint not yet registered in Stripe dashboard (need STRIPE_WEBHOOK_SECRET)
- Stripe Customer Portal not yet enabled in Stripe dashboard

## What Was Done May 7, 2026

### Updated PWA icons (icon-192 and icon-512) with new crop
- User provided new pre-cropped source image (window/reader illustration, portrait)
- Detected and removed large black border surrounding the illustration
- Found clean content bounds: rows 288Ã¢ÂÂ907, cols 275Ã¢ÂÂ685; trimmed stray bottom line artifacts
- Generated icon-192.png (192ÃÂ192) and icon-512.png (512ÃÂ512) centered on cream background
- Uploaded both to static/icons/ via GitHub web UI drag-and-drop
- Render auto-deployed on push to reading-alcove branch

## What Was Done May 6, 2026

### Fixed PWA launcher icons (icon-192 and icon-512)
- Discovered existing icon-192.png and icon-512.png were wrong (showed a barcode/columns logo, not the alcove illustration)
- User provided alcove_logo_copy.jpeg as source image
- Generated correct square crops using Pillow ÃÂ¢ÃÂÃÂ crop starts at ~22% from top to show the sitting reader prominently
- icon-192.png: 192ÃÂÃÂ192px square crop of alcove illustration
- icon-512.png: 512ÃÂÃÂ512px square crop of same illustration
- Both uploaded to static/icons/ via GitHub web UI drag-and-drop
- Render auto-deployed on push to reading-alcove branch

---

## What Was Done May 4, 2026

### New app logo & PWA icons
- User uploaded alcove_logo.jpeg ÃÂ¢ÃÂÃÂ blue line-art reading alcove illustration (portrait orientation)
- Generated PWA icons (192ÃÂÃÂ192 and 512ÃÂÃÂ512) from the illustration using canvas
- Generated alcove_logo.png (300ÃÂÃÂ400) for home page footer logo
- Pushed 3 new/updated icon files to static/icons/
- Updated templates/home.html to add centered footer logo (140px wide, subtle, with drop shadow)

---

## What Was Done May 4, 2026 ÃÂ¢ÃÂÃÂ Session 2 (Responsive Footer Logo)
- Created 3 responsive logo sizes: alcove_logo_sm.png (147ÃÂÃÂ220), alcove_logo_md.png (206ÃÂÃÂ307), alcove_logo_lg.png (270ÃÂÃÂ402)
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

- Author shelf feature ÃÂ¢ÃÂÃÂ full publication shelf per author with Google Books API (client-side)

---

## What Was Done April 30, 2026

- Stats page added (/stats route, stats.html)
- Google Books API key created and added to Render

---

## What Was Done April 29, 2026

- Email setup (freetrial@ and support@)
- Half-star ratings (0.5ÃÂ¢ÃÂÃÂ5.0)

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
- If old page serves after deploy: Render Shell ÃÂ¢ÃÂÃÂ kill -9 $(pgrep -f gunicorn) ÃÂ¢ÃÂÃÂ Render restarts automatically

---

## Chrome Extension

- Browser 1, macOS, deviceId: faa72e7f-e3e3-4136-a503-62581d7b9376
- Can access: github.com, dashboard.render.com
- Cannot access: myreadingalcove.com, my-reading-room2.onrender.com
- Use JS fetch() in extension to call GitHub API
- Note: extension blocks SHA/base64 values returned from JS ÃÂ¢ÃÂÃÂ use split workarounds to retrieve SHAs

---

## Next Tasks
- Wire up Stripe ($1.99/month after 30-day trial)
- Turn off maintenance mode when ready to launch
- Review Render pricing changes before August 1, 2026
- Consider reducing footer logo max-width (currently rendering large on desktop)
- Consider: date_started column when book moves to reading shelf
- Consider: stamp date_added on want_to_read ÃÂ¢ÃÂÃÂ reading transition
## What Was Done May 13, 2026

### Fixed garbled separator on authors page
- `templates/authors.html`: replaced double-encoded UTF-8 replacement character (`Ã¯Â¿Â½`) with `&middot;` HTML entity between year and page count

### Fixed author name grouping (partial)
- `app.py`: added `import re`
- `app.py`: changed author normalization to use `re.split(r'\s+', a.strip())` instead of `a.split()` to handle unicode whitespace
- Note: normalization still not merging "Peter may" with "Peter May" — root cause unknown, likely a non-standard character in the Supabase field. Manual data fix works as workaround. Revisit next session.

### Set up SSH authentication for git push
- Generated ed25519 SSH key on MacBook Air
- Added public key to github.com/settings/keys
- Switched remote URL to SSH: `git remote set-url origin git@github.com:dpj1951/my-reading-room.git`
- No more tokens or passwords needed for git push

## What Was Done May 13, 2026 — Session 2

### Fixed author shelf showing wrong book count (only 2 of 7)
- Root cause: filter_by(author=author_name) used exact string match
- Fix: replaced with func.lower(func.trim(Book.author)) == author_name.strip().lower()
- Added `from sqlalchemy import func` import
- Now correctly matches all 7 Peter May books

### Styled "Google Books unavailable" notice
- Changed subtitle element from textContent to innerHTML
- Wrapped notice in span with color:#4a9eff and font-weight:600 — now bright blue and bold

### Confirmed author name grouping fix working
- re.split normalization from previous session confirmed fully working
- Tested by changing "May" to "may" — books still grouped correctly

## Updated Workflow (May 13, 2026)

### Session Setup
1. Open terminal and run `cd ~/my-reading-room && git checkout reading-alcove && git pull` to prime the session
2. SSH authentication is set up — no tokens or passwords needed for git push

### Making Changes
3. Edit files via terminal using Python heredoc scripts (`python3 - << 'EOF' ... EOF`)
4. For CLAUDE.md updates, use `cat >> CLAUDE.md << 'DONE' ... DONE` to append (avoids quote-escaping issues with Python heredocs)
5. Push with `git add <files> && git commit -m "message" && git push`
6. Render auto-deploys on push to reading-alcove branch — verify at my-reading-room2.onrender.com
7. If old page serves after deploy: Render Shell → kill -9 $(pgrep -f gunicorn) → Render restarts automatically

### Chrome Extension
- Browser 1, macOS, deviceId: faa72e7f-e3e3-4136-a503-62581d7b9376
- Can read GitHub source files via fetch with Accept: application/vnd.github.v3.raw header
- Cannot access: myreadingalcove.com, my-reading-room2.onrender.com, raw.githubusercontent.com
- Extension sometimes blocks responses containing query strings — fall back to terminal in that case
- Local app.py has UTF-8 encoding corruption in some sections — always read source via GitHub API, not local file
