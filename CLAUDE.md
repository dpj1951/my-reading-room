# CLAUDE.md — My Reading Alcove
This file gives Claude full context on this project so sessions can resume without re-explaining.

## Project Overview
**My Reading Alcove** is a personal book tracking web app. Users can log books they've read, store cover art, ratings, summaries, read dates, and format (paper/ebook/audiobook). It has a barcode scanner for ISBN lookup, Google Books and Open Library API integration, CSV import/export, cover/ISBN backfill tools, and backup/restore. It is a PWA (installable on mobile).

## Repository & Deployment
- **Repo:** https://github.com/dpj1951/my-reading-room
- **Working branch:** `reading-alcove`
- **Primary live app:** https://myreadingalcove.com (custom domain) / https://my-reading-room2.onrender.com (Render URL)
- **Secondary service:** https://reading-alcove-auth.onrender.com (older service, ignore)
- **Platform:** Render (Starter $0/mo free tier currently), Flask web service
- **Database:** Supabase PostgreSQL (project: ijrepkmhqdiezvbxxzke, region: AWS us-west-2)
- **Auth:** Supabase Auth (email/password, JWT tokens stored in Flask session)
- **Push method:** GitHub Contents API via browser JS (Claude Chrome extension) OR terminal python3 script with GH_TOKEN

## Tech Stack
- **Backend:** Python / Flask (single file: `app.py`)
- **Database:** SQLAlchemy + Supabase PostgreSQL
- **Auth:** Supabase Auth via REST API + PyJWT for token verification
- **Templates:** Jinja2 (all in `templates/`)
- **Frontend:** Vanilla JS + CSS (dark theme, DM Serif Display + DM Sans fonts)
- **Static:** `static/enrich.js`, service worker (`sw.js`), PWA manifest + icons
- **Dependencies:** flask, flask-sqlalchemy, psycopg2-binary, requests, gunicorn, werkzeug, PyJWT

## Database Model (Book)
```python
id             String(36)   # UUID primary key
title          String(500)
author         String(500)
isbn           String(20)
format         String(20)   # 'Paper', 'Ebook', 'Audiobook'
pages          String(10)
copyright_year String(10)
read_date      String(10)   # stored as YYYY-MM-DD
rating         String(5)
cover_url      Text
summary        Text
read_time_hrs  String(10)
user_id        String(36)   # FK to Supabase auth.users.id
```

## Supabase Config
- **Project ref:** ijrepkmhqdiezvbxxzke
- **Project URL:** https://ijrepkmhqdiezvbxxzke.supabase.co
- **Publishable key (use this one):** sb_publishable_25JxbKV5-pocxq9xrEE6bQ_ORKEBSvL
- **Secret key:** sb_secret_bE_NO... (see Supabase dashboard)
- **Service role key:** eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlqcmVwa21ocWRpZXp2Ynh4emtlIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NTUwMTQ4NiwiZXhwIjoyMDkxMDc3NDg2fQ.icmO0p4L7eUBaBQbXjfzhrqrCuJhj7QYUmZT6rlQzTc
- **Auth user (owner):** dpjohnson1951@gmail.com (UID: 13a4418d-7a34-4c6c-bbfd-6bda8cfedd45)
- **Books:** 213 books all assigned to owner user_id
- **Email confirmations:** disabled (mailer_autoconfirm: true)
- **Site URL:** https://myreadingalcove.com

## Render Environment Variables (my-reading-room2)
- `DATABASE_URL` — Supabase PostgreSQL connection string
- `GOOGLE_BOOKS_API_KEY` — for book lookup and cover/ISBN backfill
- `SUPABASE_URL` — https://ijrepkmhqdiezvbxxzke.supabase.co
- `SUPABASE_ANON_KEY` — must be the LEGACY JWT key (eyJhbGci...), NOT the sb_publishable_ key
- `SECRET_KEY` — reading-alcove-secret-2026 (added Apr 10 2026)
- `SUPABASE_JWT_SECRET` — for JWT token verification
- `MAINTENANCE_MODE` — currently `true` — set to `false` to reopen site

## CRITICAL: Password Reset Procedure
The only working method is the Supabase Admin API. DO NOT use SQL crypt() — it corrupts the GoTrue password.
Run this from https://supabase.com/dashboard/project/ijrepkmhqdiezvbxxzke/auth/users:
```javascript
fetch('https://ijrepkmhqdiezvbxxzke.supabase.co/auth/v1/admin/users/13a4418d-7a34-4c6c-bbfd-6bda8cfedd45', {
  method: 'PUT',
  headers: { 'apikey': 'SERVICE_ROLE_KEY', 'Authorization': 'Bearer SERVICE_ROLE_KEY', 'Content-Type': 'application/json' },
  body: JSON.stringify({ password: 'NEW_PASSWORD' })
}).then(r => r.json()).then(d => { window._r = {email: d.email}; });
```
Then immediately try logging in — do NOT run any SQL queries between the API call and login attempt.
Note: Supabase free tier rate-limits failed logins. After many failures, wait 1+ hour before retrying.

## Auth Implementation (Phase 1 — Complete Apr 8 2026)
- Supabase Auth via REST API (`/auth/v1/token` for sign-in, `/auth/v1/signup`)
- JWT access token stored in Flask `session["access_token"]`
- `get_current_user()` decodes JWT to get user id + email
- `@login_required` decorator on all routes EXCEPT `/` (see landing page below)
- `@app.context_processor` injects `current_user` dict into all templates
- Logout bar added to books.html, settings.html, utilities.html, authors.html
- `/signup`, `/login`, `/logout`, `/forgot-password`, `/reset-password` routes
- All book queries scoped to `g.user["id"]`

## Changes (Apr 20 2026)

### Multi-Device Sync — Auto-Refresh on Focus
- Added visibilitychange listener to `books.html`, `authors.html`, `home.html`
- If page has been hidden for 2+ minutes, silently reloads on return to get fresh data
- Also reloads on `online` event (device reconnects after being offline)
- No service worker caching — sw.js is already pass-through (network only)

### Subscription / Pricing Model
- **Model:** 30-day free trial (full access, no credit card) then **$0.99/month**
- **Trial users** get full access — no book limit, CSV import enabled
- **After trial:** $0.99/month via Stripe (not wired up yet)
- **Interest capture:** mailto:freetrial@myreadingalcove.com (not yet set up as mailbox)
- Wording updated across:
  - `settings.html` — new green subscription card at top with trial pitch + "Notify me" mailto button
  - `add.html` — free tier banner now reads "Your 30-day free trial has ended. Subscribe for $0.99/month"
  - `utilities.html` — locked CSV import now reads "$0.99/month, 30-day free trial"

### Public Landing Page
- Built `templates/landing.html` — full marketing page for logged-out visitors
- Sections: hero (trial badge + CTA), features grid (6 cards), Goodreads callout, pricing card, install instructions, footer
- Key messaging: 30-day free trial, $0.99/month after, editable read dates, Goodreads import, multi-device sync
- `app.py` `/` route updated: logged-out visitors → `landing.html`, logged-in → `home.html` (no longer @login_required)
- Landing page is live in code but behind maintenance mode — will show when site reopens

### Push Method Confirmed
- Best approach: Claude Chrome extension executes JS directly in browser tab
- Token pasted in chat → Claude runs GitHub API push → user revokes token immediately
- Terminal python3 fallback: `cat > /tmp/script.py << 'PYEOF' ... PYEOF && python3 /tmp/script.py`
- Avoid heredoc with triple-quoted strings — use separate file write then run

## Changes (Apr 18 2026)
### Maintenance Mode
- Added `MAINTENANCE_MODE` env var toggle to `app.py` (before_request hook)
- Added `templates/maintenance.html` — styled dark-theme page with animated 📖 icon
- Set `MAINTENANCE_MODE=true` in Render env vars — site currently closed to public
- Service worker confirmed pass-through (no caching) — maintenance works correctly
- To reopen: set `MAINTENANCE_MODE=false` in Render env vars and redeploy

### Subscription / Role System (Phase 2)
- Added `user_roles` table in Supabase (user_id uuid PK, role text default 'free', created_at)
- RLS enabled with policy "Users can read own role"
- Owner user (13a4418d-7a34-4c6c-bbfd-6bda8cfedd45) inserted as role='owner'
- Added to `app.py`:
  - `get_user_role(user_id)` — fetches role from Supabase REST API at login, cached in session["user_role"]
  - `is_subscriber()` — returns True if role in ('subscriber', 'beta', 'owner')
  - `FREE_BOOK_LIMIT = 20` — free tier cap (enforcement stays, but trial users bypass via role)
- Login route now fetches and caches role in session after token save
- `get_current_user()` now includes 'role' key from session
- `import_csv` route: blocked for free users with amber "upgrade" flash message
- `add_manual_save` route: checks book count for free users, blocks at 20 with upgrade flash
- Role management: insert into user_roles with role='beta' to grant full access manually

### Role Reference
- **free** — 20 book limit, no CSV import (post-trial default)
- **beta** — full access, free
- **subscriber** — full access, paid
- **owner** — full access, always (dpjohnson1951@gmail.com)

## Changes (Apr 16 2026)
- Custom domain myreadingalcove.com purchased and configured (Namecheap: A @ → 216.24.57.1, CNAME www → my-reading-room2.onrender.com)
- Supabase Site URL updated to https://myreadingalcove.com
- PWA manifest start_url fixed: /books → / (was causing mobile PWA to skip home page)
- Login redirect fixed: now lands on home page instead of books after login
- Removed Wipe Library UI from utilities page (backend route kept for future use)

## Changes (Apr 15 2026)
- Removed "Log in" link from home page (home.html)
- Push method established: GitHub Contents API via Chrome extension JS

## Changes (Apr 14 2026)
- Fixed garbled mojibake emoji in format buttons on add.html
- Authors page filter: searches both author names and book titles
- Authors page filter: shows "No results found" when no matches

## Changes (Apr 13 2026)
- Barcode scanner fully working end-to-end (scan.html rebuilt with ZXing-js)
- Scanner redirects to /add/manual?isbn=XXXXXXX on detect
- add.html auto-populates and calls doSearch() from isbn_prefill

## Bugs Fixed (Apr 12 2026)
- Books page list view removed — grid only
- Supabase migrated to new API key format
- Import CSV: fresh UUIDs to avoid duplicate key errors, duplicate check scoped to user_id
- Wipe button still broken (deletes 0 books) — workaround: delete via Supabase REST API with service key

## Known Issues / Next Session TODO
- **Site in maintenance mode** — set `MAINTENANCE_MODE=false` in Render to reopen
- **Email setup** — freetrial@myreadingalcove.com not yet configured (Namecheap forwarding to Gmail, ~2 min setup)
- **Stripe billing** — wire up when ready; webhook just sets role='subscriber' in user_roles
- **book_count in context** — add.html banner uses current_user.book_count which isn't injected yet (cosmetic only, enforcement works)
- **Wipe Library button** — still broken, workaround via Supabase REST API
- **Render upgrade** — upgrade to $7/month Starter when ready to launch (eliminates cold start)

## Pre-Launch Checklist
1. Set up freetrial@myreadingalcove.com email forwarding (Namecheap → Gmail)
2. Set `MAINTENANCE_MODE=false` in Render env vars and redeploy
3. Verify landing page looks correct at myreadingalcove.com
4. Verify logged-in users still go to home.html correctly
5. Wire up Stripe when ready for paid subscriptions

## How to Push Changes
Preferred: Claude Chrome extension — paste token in chat, Claude runs JS push, revoke token immediately.

```javascript
(async () => {
  const T = 'ghp_TOKEN';
  const BASE = 'https://api.github.com/repos/dpj1951/my-reading-room/contents/';
  const meta = await (await fetch(BASE + 'FILENAME?ref=reading-alcove', { headers: { Authorization: 'token ' + T } })).json();
  const bytes = Uint8Array.from(atob(meta.content.replace(/\n/g,'')), c => c.charCodeAt(0));
  let code = new TextDecoder().decode(bytes);
  // ... make changes ...
  const enc = new TextEncoder().encode(code);
  let bin = ''; enc.forEach(b => bin += String.fromCharCode(b));
  const put = await (await fetch(BASE + 'FILENAME', {
    method: 'PUT',
    headers: { Authorization: 'token ' + T, 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: 'commit message', content: btoa(bin), sha: meta.sha, branch: 'reading-alcove' })
  })).json();
  return put.commit ? 'OK:' + put.commit.sha.substring(0,7) : 'ERR:' + JSON.stringify(put).substring(0,100);
})();
```

Terminal fallback: `cat > /tmp/script.py << 'PYEOF' ... PYEOF && python3 /tmp/script.py`
Token: generate at github.com/settings/tokens (classic, repo scope), revoke after session.

## Planned Development Roadmap
### Phase 1 — Auth & Per-User Data ✅ COMPLETE (Apr 8 2026)
### Phase 2 — Subscription Model (IN PROGRESS)
- ✅ Pricing model decided: 30-day free trial → $0.99/month
- ✅ Landing page built with trial/pricing messaging
- ✅ In-app wording updated
- ⬜ Email setup (freetrial@myreadingalcove.com)
- ⬜ Stripe integration (webhook → sets role='subscriber')
- ⬜ Trial timer enforcement (trial_started_at column + expiry logic)
### Phase 3 — Production Readiness
- Upgrade Render to $7/month Starter
- Delete reading-alcove-auth.onrender.com service
- Privacy policy page

## Product & Distribution Decisions
- **Distribution:** Web-first PWA
- **Auth:** Supabase Auth (complete)
- **Billing:** $0.99/month after 30-day free trial (Stripe, not yet wired)
- **Hosting:** Render free tier (upgrade to Starter $7/mo when ready to launch)
- **Database:** Supabase PostgreSQL
- **Email:** freetrial@myreadingalcove.com (Namecheap forwarding, not yet configured)
- **Domain:** myreadingalcove.com (Namecheap, pointed to Render)
