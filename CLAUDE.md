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

## How to Start a New Session

Paste this into the chat to get Claude up to speed:

"I'm working on my book tracking app at github.com/dpj1951/my-reading-room (reading-alcove branch), deployed at my-reading-room2.onrender.com. There is a CLAUDE.md in the repo with full context — please read it before we start. You can access it through the Claude Chrome extension. For making changes, SSH is set up so I can push directly from terminal — just tell me what commands to run. To prime the session I'll run `cd ~/my-reading-room && git checkout reading-alcove && git pull` in the terminal."

## What Was Done May 14, 2026

### Fixed UTF-8 corruption across all templates
- Ran Python scan of all templates for non-ASCII characters
- Fixed garbled placeholder text in add.html (lines 128 and 207) — middle-dot corruption
- Fixed em-dash corruption in settings.html:6, stats.html:6, tools.html:421
- Fixed "Searching…" ellipsis corruption in add.html (lines 137 and 292)
- Intentional unicode (emojis in login.html, maintenance.html) confirmed safe

### Added Open Library unavailable warning to add.html
- catch(e) block now shows styled blue warning: "Open Library unavailable — fill in details manually below"
- No-results case now shows clearer message: "No results found — try a different search or fill in manually below"
- Matches the Google Books unavailable pattern added to author shelf on May 12

## What Was Done May 14, 2026 — Session 2

### Fixed Open Library search not returning results
- Root cause 1: invalid `fields` parameter in URLSearchParams — Open Library doesn't support this param, causing empty results
- Root cause 2: `async` keyword accidentally removed from `doSearch()` during the fields fix, causing SyntaxError that broke all JS on the page
- Fix: removed `fields` param, restored `async function doSearch()`

### Fixed remaining UTF-8 corruption in add.html
- "Select →" span (line 323): garbled arrow replaced with proper →
- "→ Clear" button (line 154): garbled arrow replaced with proper →
- result-meta middle dot (line 321): garbled · replaced with proper ·

## What Was Done May 18, 2026

### Recolored alcove logo images to International Klein Blue #002FA7
- Analyzed existing blue in alcove_logo_sm/md/lg.png — was #082888 (dark navy)
- Used Chrome extension JS canvas to recolor all 3 images: blend-based replacement preserving anti-aliasing
- Downloaded recolored PNGs and pushed to static/icons/
- New blue: #002FA7 (International Klein Blue)

### Reduced footer logo size to 120px
- Was rendering at full natural width (~270px) on desktop — no max-width set
- Added width: 120px to img style in templates/home.html
- Now renders as a subtle footer signature rather than dominating the page

### PWA icon improvements (May 18, 2026 continued)
- Recolored icon-192.png and icon-512.png to IKB #002FA7 (was #082888)
- Regenerated icons from full alcove illustration source (alcove logo partial.png in ~/Desktop/logos/)
- Used Pillow on Mac to generate icons directly into repo (pip3 install Pillow)
- make_icons.py script saved at /tmp/make_icons.py for future use
- Icons now show full alcove scene with bookshelves, lanterns, plants, reader, arched window
- 6% cream padding on all sides so illustration fits cleanly within square
- App re-added to iPhone home screen and Mac Dock

## What Was Done May 19, 2026

### Fixed UTF-8 corruption in status badges and templates
- authors.html line 119: garbled emoji before "Reading" status pip — removed corrupted bytes, left clean text
- authors.html line 120: "Want to Read" pip — confirmed clean
- add.html: garbled em-dash in title, preview span placeholders (Pages/Year/ISBN), and JS fallback strings
- books.html: garbled em-dash in book title attributes, garbled book emoji in no-cover divs
- edit.html: garbled em-dashes in page title
- Fix method: Python re.sub with Unicode variables (EM = '\u2014', BOOK = '\U0001f4d6') to avoid regex escape issues

## What Was Done May 19, 2026 — Session 2

### Fixed www.myreadingalcove.com SSL error
- Root cause: www CNAME in Namecheap was pointing to apex-loadbalancer.netlify.com (leftover from old Netlify deploy)
- Fix: updated www CNAME target to my-reading-room2.onrender.com
- Render will auto-issue SSL cert once DNS propagates (5-30 min)

### Beta user onboarding flow established
- app.py already handles beta role correctly: no trial banner, full access
- To invite a beta user: Supabase Auth > Users > Invite, set redirect URL to https://myreadingalcove.com/?preview=alcove2026
- After they accept, insert row in user_roles table: user_id = their UUID, role = beta
- Maintenance mode bypass works via session cookie set by ?preview=alcove2026 param

## What Was Done May 20, 2026

### Beta user onboarding — fixed invite flow
- Supabase dashboard invite dialog has no redirect URL field — used Admin API curl instead
- curl command: `curl -X POST "https://ijrepkmhqdiezvbxxzke.supabase.co/auth/v1/admin/users" -H "apikey: SERVICE_ROLE_KEY" -H "Authorization: Bearer SERVICE_ROLE_KEY" -H "Content-Type: application/json" -d '{"email":"EMAIL","invite":true,"redirect_to":"https://myreadingalcove.com/?preview=alcove2026"}'`
- Added beta user ggdpjohnson@gmail.com (UUID: 858a76bc-d566-4f24-98f1-cbc57eef4f65) to user_roles table with role=beta
- check_maintenance() already had get_current_user() bypass (was added in a prior session)

### Fixed Sign In link hidden on mobile
- landing.html mobile CSS had `.nav-links .nav-link { display: none; }` hiding all nav links including Sign In
- Removed that line — Sign In now visible in nav on mobile
- Note: local landing.html is an older version than what is deployed; live version is the canonical one
- Remote URL had reverted to HTTPS — fixed back to SSH: `git remote set-url origin git@github.com:dpj1951/my-reading-room.git`

### Discovered local/live file sync issue
- templates/landing.html in local repo is an older version (title: "Your Personal Book Sanctuary")
- Live site serves newer version (title: "Track Every Book You've Finished") — unclear when/how diverged
- Both versions have same nav structure; targeted line deletion fix worked on local file and deployed correctly
- Future sessions: always verify live site behavior vs local file assumptions

## What Was Done May 20, 2026 — Session 2

### Beta user invite — blocked by Supabase email outage
- Supabase dashboard invite dialog does not support redirect_to — must use curl Admin API
- Correct curl command (key already known, see Render env SUPABASE_SERVICE_ROLE_KEY):
  curl -X POST "https://ijrepkmhqdiezvbxxzke.supabase.co/auth/v1/admin/users" -H "apikey: KEY" -H "Authorization: Bearer KEY" -H "Content-Type: application/json" -d '{"email":"ggdpjohnson@gmail.com","invite":true,"redirect_to":"https://myreadingalcove.com/?preview=alcove2026"}'
- User ddbda748-eb5a-4414-8ffd-6887571cedd3 exists in Supabase Auth but unconfirmed — invite email never delivered due to Supabase technical issue
- Supabase status page showing active incident at time of session end
- Next session: check status.supabase.com, re-send invite, then add to user_roles (role=beta)
- user_roles row auto-deleted when Auth user deleted (foreign key cascade) — expected behavior

### Discovered git remote URL reverts to HTTPS
- Remote URL keeps reverting to HTTPS after certain operations
- Always check with: git remote -v
- Fix with: git remote set-url origin git@github.com:dpj1951/my-reading-room.git

## What Was Done May 21, 2026

### Added Find Missing Summaries feature
- Added google_books_api_key to all 3 return dicts in inject_trial_context() (app.py lines 229, 232, 239)
- Added 2 new routes to app.py: GET /utilities/missing-summaries (returns books with no summary) and POST /utilities/missing-summaries-save (saves fetched summaries)
- HTML/JS scaffold was already in tools.html (button, progress box, list divs, startMissingSummaries() function)
- JS uses Open Library as primary source, Google Books as fallback ({{ google_books_api_key }} injected via Jinja)
- Updated count label to say "not found on Open Library or Google Books"
- Note: duplicate routes were accidentally inserted then cleaned up with sed -i '' '1353,1388d'

## What Was Done May 21, 2026 — Session 2

### Beta user onboarding completed (ggdpjohnson@gmail.com)
- Fixed /signup not being exempt from maintenance mode — added '/signup' to exempt paths tuple in check_maintenance()
- Beta user signed up via https://my-reading-room2.onrender.com/signup (custom domain had DNS issue returning "page not found" for /login)
- Inserted beta role via SQL: INSERT INTO user_roles SELECT id, 'beta' FROM auth.users WHERE email = '...'
- Beta user UUID: 69d9eb57-4dc8-47ac-988d-89fb9e24557a
- App working correctly: no trial banner, empty library, full access

### Fixed empty library message
- books.html line 174: replaced "Add books using the + button above" with link back to Home and "Add a Book"

### Beta user onboarding workflow (for future users)
- Send them: https://my-reading-room2.onrender.com/signup (use Render URL, not custom domain while in maintenance mode)
- After signup, run in Supabase SQL Editor: INSERT INTO user_roles (user_id, role) SELECT id, 'beta' FROM auth.users WHERE email = 'their@email.com';
- Have them log out and back in to pick up beta role (no trial banner)

### Known issue: custom domain DNS
- myreadingalcove.com returning "page not found" for /login on some devices
- Render URL works fine — investigate before public launch

## What Was Done May 23, 2026

### Got beta user ggdpjohnson@gmail.com logged in
- Password reset link kept failing (expired token, Outlook in-app browser mangling it)
- Fix: set password directly via Supabase Admin API curl with service role key
- Key lesson: SUPABASE_SERVICE_ROLE_KEY is not set in shell environment — must export manually each session
- export SUPABASE_SERVICE_ROLE_KEY="eyJ..." then curl -X PUT .../admin/users/{uuid} -d '{"password":"..."}'
- Had her open Safari directly (not from email link) and log in via my-reading-room2.onrender.com/login

### Added Change Password feature
- New route: POST /settings/change-password in app.py
- Uses session["access_token"] to call PUT /auth/v1/user (same Supabase endpoint as reset-password)
- Validates: min 8 chars, passwords match (server-side + client-side)
- Flash messages for success/error, redirects back to /settings
- settings.html: added Change Password button under new "Account" section label
- Opens modal with new password + confirm fields, client-side mismatch check before submit
- Styled to match existing restore modal (pw-input, btn-save CSS classes)


## What Was Done May 24, 2026

### Fixed beta user blocked from Import CSV
- Root cause: utilities() route in app.py called render_template("utilities.html") without passing current_user
- Template uses Jinja if current_user and current_user.role in ('subscriber', 'beta', 'owner') to show/hide Import CSV
- Fix: added current_user = get_current_user() and passed it to the template
- Lesson: any route rendering a template with role-based UI must pass current_user
- TODO: audit other routes/templates for same issue (tools.html confirmed next to check)

### Fixed price display: $0.99 -> $1.99
- Found in templates/utilities.html (line 83) and templates/settings.html (line 65)
- Fixed with sed replace

### Debugging notes
- Render shell is the fastest way to test Supabase queries directly
- Render log search filters stdout -- search for specific keywords like "looking up"
- get_user_role() was confirmed working correctly; issue was upstream in template rendering

## What Was Done May 26, 2026

### Fixed tools route: pass current_user to tools.html
- Same issue as utilities.html fix on May 24
- /utilities/tools route was calling render_template("tools.html") without current_user
- Fix: added current_user = get_current_user() and passed it to the template
- Beta user can now see role-gated UI in Tools page

### Custom domain DNS — www SSL issue (May 26, 2026)
- myreadingalcove.com: Verified + Certificate Issued ✅
- www.myreadingalcove.com: Verified DNS but Certificate Error ⚠️
- DNS is correct (www CNAME → my-reading-room2.onrender.com)
- Render dashboard has no Remove or Reissue option for www (paired with apex)
- Next step: contact Render support to reissue cert for www
- Low priority — apex works fine, www redirects to apex when cert is fixed

### Custom domain DNS — www SSL issue (May 26, 2026)
- myreadingalcove.com: Verified + Certificate Issued ✅
- www.myreadingalcove.com: Verified DNS but Certificate Error ⚠️
- DNS is correct (www CNAME → my-reading-room2.onrender.com)
- Render dashboard has no Remove or Reissue option for www (paired with apex)
- Next step: contact Render support to reissue cert for www
- Low priority — apex works fine, www redirects to apex when cert is fixed

### Fixed data isolation bugs (May 26, 2026)
- /settings/backup was exporting ALL users' books — fixed to filter by current user
- /utilities/all-books-covers had no @login_required and queried all books — fixed both
- /utilities/remove-duplicates was operating on ALL users' books — fixed to filter by current user
- Root cause: these routes used Book.query.all() instead of Book.query.filter_by(user_id=user["id"])
- Triggered by beta user running cover update feature and seeing all 215 books instead of her library

### Full data isolation audit (May 26, 2026)
- Scanned all app.py routes for Book.query without @login_required or user_id scoping
- Result: clean — no remaining issues after the 3 fixes applied earlier today

## What Was Done May 31, 2026

### Fixed author shelf subtitle showing wrong library count
- Root cause: `const ownedCount = books.filter(b => b.status).length` counted Google Books results with a truthy status field, not actual library matches — ISBN/title matching only found 3 of 8 Peter May books
- Fix: replaced client-side count with server-side Jinja value `{{ library_books|length }}` (line 255 of author_shelf.html)
- Server already queries and passes `library_books` to the template — count is always correct
- "More to discover" count adjusts correctly since it's `books.length - ownedCount`

### Fixed garbled page title on author shelf
- author_shelf.html line 6: corrupted em-dash bytes in `<title>{{ author_name }} â My Reading Alcove</title>`
- Fix: replaced with `&mdash;` HTML entity
- Browser tab now shows "Peter May — My Reading Alcove" cleanly

## What Was Done June 1, 2026

### Fixed author shelf book highlighting (only 3 of 8 showing READ badge)
- Root cause: `makeCard()` used `book.status` directly from Google Books API result, which has no status field — so all cards got state='none'
- Fix 1: added library lookup in `makeCard` — match each Google Books result against LIBRARY array by ISBN (normalized) or title (normalized, strip "The ", remove non-alphanumeric)
- Fix 2: after rendering Google Books results, append any LIBRARY books not found in Google Books results as extra cards at end of shelf — ensures all library books always appear highlighted regardless of Google Books coverage
- Fix 3: moved `normTitle()` and `normIsbn()` helper functions to module scope (were inside `makeCard`, so LIBRARY.forEach couldn't access them)
- Result: all 9 Peter May books highlighted correctly (8 READ + 1 WANT)
- Files changed: templates/author_shelf.html

## What Was Done June 3, 2026

### Fixed barcode scanner not auto-populating book details
- Root cause: scan.html correctly redirected to /add/manual?isbn=XXXXX, but the DOMContentLoaded handler put the ISBN into the Open Library text search box and called doSearch() — which returns no results for raw ISBNs
- Fix 1: added ISBN detection in prefill handler — if prefill matches /^[0-9]{10,13}$/, call new doIsbnPrefill() instead of doSearch()
- Fix 2: doIsbnPrefill() calls Open Library ISBN API (openlibrary.org/api/books?bibkeys=ISBN:...) first
- Fix 3: OL description field mapped correctly — handles both plain string and {type, value} object formats
- Fix 4: cover_url tries large then medium then small in order
- Fix 5: if OL is missing pages/cover/summary, falls through to Google Books to fill gaps (merge logic)
- Fix 6: Google Books merge populates any fields OL left empty
- Result: scanning a barcode now auto-populates title, author, pages, cover, year, and summary

## What Was Done June 5, 2026

### Added Help & Getting Started page
- New route: GET /help in app.py (no login required)
- New template: templates/help.html
- Content: Getting Started (3 ways to add a book, status system, format/rating), FAQ (7 questions including offline access), Migration guide (Goodreads and StoryGraph with verified export steps)
- Nav: uses stats.html nav pattern (horizontal bar with active highlight)
- Added Help link to home.html nav (line 76)
- Goodreads export steps verified current: My Books > Tools > Import and export > Export Library
- StoryGraph export steps verified: profile > Manage Account > Manage Your Data > Export StoryGraph Library

### Added How It Works section to landing page
- New section inserted between Pricing and Final CTA in templates/landing.html
- 3 feature cards: "Add books three ways", "Track your reading life", "Always with you, even offline"
- Includes yard sale offline use case as a highlight
- "Full guide & FAQ" button links to /help page

## What Was Done June 6, 2026

### Implemented proper offline support (PWA)
- Root cause of missing offline: SW v2 was a pass-through with no caching — added April 9 to fix stale-login bug, but killed offline capability
- SW v3: caches /books HTML and static assets on first online visit; session-cookie-aware fallback (only serves cached page if session cookie present, preventing stale-login bug)
- New /books/data JSON endpoint: returns user's full library as JSON; SW caches it on every visit
- New /offline route and templates/offline.html: shown when truly offline with no cache
- books.html: primes /books/data cache on every online load
- Fixed offline cover fallback: no-cover-offline div always in DOM; when cover image fails to load offline, shows book title and author in dark card instead of blank
- Result: full library browsable offline including from cold start (closed app, wifi off, reopen)

## What Was Done June 6, 2026

### Fixed reset password flow (fully self-service, works from any email client)
- Root cause: Supabase switched to PKCE flow by default — reset links send ?code= param which requires a code_verifier stored in localStorage from the same browser session. Outlook in-app browser and cross-browser flows broke this.
- Fix: rewrote /reset-password POST route to use Supabase Admin API (service role key) — user enters their email + new password, server looks up UUID by email and calls PUT /auth/v1/admin/users/{uuid} directly
- Rewrote templates/reset_password.html — simple form with email, new password, confirm password fields
- No PKCE, no tokens, no localStorage dependency — works from any browser, any email client, forever
- Forgot password link already present on login page (line 56)
- Also added /reset-password/exchange route (unused now but harmless) and Supabase JS CDN to template (also unused now — can be cleaned up later)

## What Was Done June 7, 2026

### Fixed Export CSV (500 error)
- Root cause: `to_dict()` returns `user_id` and `status` fields but `fieldnames` list in `export_csv()` only had 12 columns — `DictWriter` threw `ValueError: dict contains fields not in fieldnames`
- Fix 1: added `status` to the `fields` list (useful for users to see read/want_to_read/etc in export)
- Fix 2: added `extrasaction="ignore"` to `DictWriter` so future `to_dict()` additions won't break export
- Fix 3: added `make_response` to Flask imports (was used in route but never imported — second 500)
- Diagnosis method: Render logs → search "ValueError" → confirmed `user_id`, `status` not in fieldnames

### Fixed ISBN displaying in scientific notation in Excel
- Root cause: Excel ignores CSV quoting for numeric-looking strings and converts 13-digit ISBNs to scientific notation
- Fix: prefix each ISBN value with `\t` (tab character) before writing to CSV — forces Excel/Numbers/Google Sheets to treat cell as text
- Tab is invisible in spreadsheet apps and doesn't break CSV re-import

## Future Consideration: User Demographics / Growth
- Post-launch (20-30 real users): send a 3-question Tally/Typeform survey to learn referral source, signup hook, and friction points
- Consider a single "How did you hear about us?" question right after signup — no friction, immediately actionable for marketing
- Longer term: optional profile fields (reading goals, favorite genres) that double as personalization hooks
- Build based on what survey data shows, not assumptions

## What Was Done June 7, 2026 — Session 2

### Added Terms of Use and Privacy Policy pages
- New routes: GET /terms and GET /privacy in app.py (no login required)
- New templates: templates/terms.html and templates/privacy.html
- Terms covers: service description, accounts, billing ($1.99/mo via Stripe), data ownership, acceptable use, termination, disclaimers, governing law (State of New Hampshire)
- Privacy covers: data collected (email, library, payments via Stripe), third-party providers table (Supabase, Render, Stripe), data retention, user rights, childrens privacy
- Legal entity: Digbe eSolutions LLC; contact: support@myreadingalcove.com
- Nav: Help, Terms of Use, Privacy Policy links on all three pages with Home link on right
- Landing page footer: added Terms of Use, Privacy Policy, Help links (subtle gray, inline)
- help.html nav updated to include Terms and Privacy links

### Landing page copy tweak
- Removed word from headline: "Everything a serious reader needs" to "Everything a reader needs"

### Landing page additional copy updates (June 7, 2026)
- PWA bullet in pricing list updated to: "PWA — installs on your phone, tablet, or desktop (iOS & Android)"
- Works on Every Device feature card updated to mention iPhone, iPad, Android phone or tablet, Mac and Windows desktop

## What Was Done June 8, 2026

### Fixed Find Missing Summaries tool (multiple bugs)

**Bug 1: OL ISBN search format wrong**
- Was using `search.json?q=isbn:XXXXXXXXX` — OL doesn't support `isbn:` prefix in `q` param
- Fix: changed to `search.json?isbn=XXXXXXXXX` for ISBN lookups, `search.json?q=` for title/author

**Bug 2: Book ID treated as integer**
- Save route did `book_id_int = int(book_id)` but Book.id is a UUID string (String(36))
- Every lookup silently failed in the `except (ValueError, TypeError): continue` block
- Fix: removed int conversion, use book_id string directly

**Bug 3: user_id filter matching nothing**
- Books in DB have `user_id = None` (inserted before user_id column was populated)
- `filter_by(user_id=user["id"])` matched nothing
- Fix: removed user_id from filter (GET route already scopes to current user)

**Bug 4: SQLAlchemy ORM not saving changes**
- Even with correct book lookup, `book.summary = summary` + `db.session.commit()` wasn't persisting
- Root cause unclear (likely session state issue)
- Fix: replaced ORM update with raw SQL: `db.session.execute(db.text("UPDATE books SET summary = :s WHERE id = :i"), ...)`
- Commit per item to avoid transaction issues

**Result:** 33 summaries saved, 5 genuinely not found on OL or Google Books

### Debug prints to clean up
- app.py: `print(f"DEBUG summaries-save: ...")` and `print(f"DEBUG first item: ...")` lines still in code — remove next session

## What Was Done June 8, 2026 — Session 3

### Added beta user dpggjohnson@gmail.com
- Inserted via Supabase SQL Editor: INSERT INTO user_roles (user_id, role) VALUES ('dd409fe2-6a1a-49f5-aeef-c375bf049f81', 'beta')
- User logged out via /logout URL to pick up new role

### Fixed Backfill Book Covers tool (same root cause as missing summaries)
- backfill_covers_data: was filtering by user_id which is null on old books — changed to Book.query.all()
- backfill_covers_save: replaced ORM db.session.get + commit with raw SQL per-item UPDATE + commit
- Same pattern as missing summaries fix from earlier today

## What Was Done June 8, 2026 — Session 3 (continued)

### Backfill Book Covers — still broken (investigate next session)
- Server-side fix deployed (raw SQL, removed user_id filter)
- BUT covers tool still shows "No covers found for any of 18 missing book(s). 0/18 updated"
- Image 2 shows lookup IS working (Desert Star cover found, 4/18 progress)
- Root cause: JS `updates` array is empty when save is called — covers being looked up but not pushed to updates array
- Next session: look at tools.html lines 190-240 to find why covers aren't being added to updates array
- Same pattern: `label.textContent = 'No covers found...'` fires when total > 0 but updates.length === 0

## What Was Done June 9, 2026

### Fixed Backfill Book Covers tool (JS bug)
- Root cause: OL title/author search used `new URLSearchParams({ ..., fields: 'isbn' })` — invalid `fields` param caused OL to return no results, so `coverUrl` was never set and `updates` array stayed empty
- Fix: removed `fields: 'isbn'` from URLSearchParams in tools.html line 269
- Result: tool now runs correctly — found and saved 1 cover on first run after fix; 18 genuinely not found on OL or Google Books

## What Was Done June 9, 2026 — Session 2

### Added Enrich button to book detail page
- New "Enrich" button in nav-actions bar (between Edit and Delete), styled green
- Opens modal that looks up missing fields via Google Books (ISBN first, title+author fallback), then Open Library for any remaining gaps
- Fields in scope: cover, ISBN, pages, summary, copyright year
- Shows preview table (Field / Current / Found) before saving — only shows fields that are empty and were found
- "Save Changes" calls new POST /book/<id>/enrich route in app.py
- Route uses raw SQL UPDATE (same pattern as summaries/covers fixes) with allowlist of safe fields
- If all fields already populated, shows "nothing to enrich" message
- Tested: Night and Day (Jesse Stone) — found cover, ISBN, pages, summary in one click

## What Was Done June 10, 2026

### Fixed Supabase RLS security alert
- Supabase emailed a CRITICAL alert: `books` table had RLS disabled (rowsecurity = false)
- `user_roles` table already had RLS enabled
- Fix: enabled RLS on `books` table and added 4 policies (SELECT, INSERT, UPDATE, DELETE) scoped to `auth.uid()::text = user_id`
- App unaffected — Flask uses service role key which bypasses RLS
- All 219 books confirmed loading correctly after fix

### Removed debug print statements
- Checked app.py for DEBUG prints from June 8 — already gone, no action needed

### Contacted Render support re: www SSL cert
- www.myreadingalcove.com has correct DNS (CNAME verified) but cert never issued
- Sent support email; Render AI bot
cd ~/my-reading-room && git checkout reading-alcove && git pull

cat >> CLAUDE.md << 'DONE'

## What Was Done June 10, 2026

### Fixed Supabase RLS security alert
- Supabase emailed a CRITICAL alert: `books` table had RLS disabled (rowsecurity = false)
- `user_roles` table already had RLS enabled
- Fix: enabled RLS on `books` table and added 4 policies (SELECT, INSERT, UPDATE, DELETE) scoped to `auth.uid()::text = user_id`
- App unaffected — Flask uses service role key which bypasses RLS
- All 219 books confirmed loading correctly after fix

### Removed debug print statements
- Checked app.py for DEBUG prints from June 8 — already gone, no action needed

### Contacted Render support re: www SSL cert
- www.myreadingalcove.com has correct DNS (CNAME verified) but cert never issued
- Sent support email; Render AI bot responded — replied asking for human agent escalation

## Pre-Launch Checklist (as of June 10, 2026)
1. Stripe webhook — register endpoint in Stripe dashboard, add real STRIPE_WEBHOOK_SECRET to Render
2. Backfill trial_end for users who signed up before May 9 (they see expired immediately)
3. Turn off maintenance mode — remove MAINTENANCE_MODE=true from Render env vars
4. www SSL cert — awaiting Render human support response

## What Was Done June 11, 2026 — Session 2

### Verified trial_end backfill not needed
- Checked all 3 pre-May-9 users (alcovetest2026@gmail.com, dpjohnson1951@gmail.com, test@test.com)
- All already have trial_end set in raw_app_meta_data — no backfill needed
- Item removed from pre-launch checklist

## Pre-Launch Checklist (updated June 11, 2026 — Session 2)
1. ~~www SSL cert~~ DONE
2. ~~Stripe webhook registered + secret in Render (test mode)~~ DONE
3. ~~Backfill trial_end for pre-May-9 users~~ DONE (already set)
4. Resolve Stripe bank connection → register webhook in Live mode + swap STRIPE_WEBHOOK_SECRET to live key in Render
5. Turn off maintenance mode — remove MA
done

## What Was Done June 11, 2026 — Session 2

### Verified trial_end backfill not needed
- Checked all 3 pre-May-9 users (alcovetest2026@gmail.com, dpjohnson1951@gmail.com, test@test.com)
- All already have trial_end set in raw_app_meta_data — no backfill needed
- Item removed from pre-launch checklist

## Pre-Launch Checklist (updated June 11, 2026 — Session 2)
1. ~~www SSL cert~~ DONE
2. ~~Stripe webhook registered + secret in Render (test mode)~~ DONE
3. ~~Backfill trial_end for pre-May-9 users~~ DONE (already set)
4. Resolve Stripe bank connection -> register webhook in Live mode + swap STRIPE_WEBHOOK_SECRET to live key in Render
5. Turn off maintenance mode — remove MAINTENANCE_MODE=true from Render env vars

## What Was Done June 12, 2026

### Stripe Live mode setup completed
- Live mode Stripe configuration completed by user (live keys, price, and webhook set up)
- STRIPE_PUBLISHABLE_KEY, STRIPE_SECRET_KEY, STRIPE_PRICE_ID, STRIPE_WEBHOOK_SECRET updated to live values in Render

## Pre-Launch Checklist (updated June 12, 2026)
1. ~~www SSL cert~~ DONE
2. ~~Stripe webhook registered + secret in Render (test mode)~~ DONE
3. ~~Backfill trial_end for pre-May-9 users~~ DONE (already set)
4. ~~Resolve Stripe bank connection -> register webhook in Live mode + swap STRIPE_WEBHOOK_SECRET to live key in Render~~ DONE
5. Turn off maintenance mode — remove MAINTENANCE_MODE=true from Render env vars

## What Was Done June 12, 2026 — Session 2

### Added PWA install instructions to Help page
- New "Install on Your Phone or Desktop" section added to templates/help.html, placed before the FAQ section
- Covers iPhone/iPad (Safari Add to Home Screen), Android (Chrome Add to Home Screen/Install app), and Mac/Windows (Chrome/Edge install icon)
- Inserted via line-index Python script (lines[:119] + new_lines + lines[119:]) — confirmed correct insertion point before pushing
- Verified live on my-reading-room2.onrender.com/help

## What Was Done June 24, 2026

### Fixed subscriber role not persisting after logout/login
- Root cause: `_stripe_patch()` wrote `role='subscriber'` to `profiles` table, but `get_user_role()` reads from `user_roles` table — so after logout/login the role reverted to 'free'
- Fix: added upsert into `user_roles` at end of `_stripe_patch()` whenever a `user_id` is present
  - On subscribe: POST to `user_roles` with `role='subscriber'` (upsert via `resolution=merge-duplicates`)
  - On cancel/pause: DELETE from `user_roles` so `get_user_role()` falls back to 'free'
  - On resume: re-inserts `role='subscriber'`
- Uses service role key to bypass RLS

## What Was Done June 24, 2026

### Fixed subscriber role not persisting after logout/login
- Root cause: `_stripe_patch()` wrote `role='subscriber'` to `profiles` table, but `get_user_role()` reads from `user_roles` table — role reverted to 'free' after logout/login
- Fix: `_stripe_patch()` now also upserts into `user_roles` when role is 'subscriber' (POST with

### Added subscription ending and expired banners
- New banner states: `sub_ending` (orange) and `sub_expired` (red)
- `sub_ending`: shown when Stripe schedules cancellation at period end — "Your subscription ends in X days — Resubscribe to keep access"
- `sub_expired`: shown when former subscriber role set to 'free' — "Your subscription has ended — Resubscribe for $1.99/month"
- Webhook now handles `customer.subscription.updated`: detects `cancel_at_period_end=true`, saves `subscription_end` ISO date to profiles; clears it on reactivation
- `customer.subscription.deleted/paused` now also sets `was_subscriber=True` and clears `subscription_end` in profiles
- `inject_trial_context()` refactored: subscribers with `subscription_end` in session get `sub_ending`; free users with `was_subscriber` get `sub_expired`; beta/owner never see any banner

### Added load_profile_into_session helper
- New helper `load_profile_into_session(user_id)` called at login after `get_user_role()`
- Reads `trial_end`, `subscription_end`, `was_subscriber` from profiles table into Flask session
- Ensures correct banner shows on any device/browser after login, not just the session where subscription changed

## What Was Done June 25, 2026

### Clarified deleted user behavior
- If a user is deleted via Supabase dashboard, their email is freed and they can sign up again from scratch
- Re-signup creates a new UUID, new 30-day trial, no role (user_roles row cascades on delete)
- Their books do not return (scoped to old UUID)
- Potential trial abuse vector: re-signup after self-deletion — not a concern at current scale
