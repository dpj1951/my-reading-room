# CLAUDE.md — My Reading Alcove

This file gives Claude full context on this project so sessions can resume without re-explaining.

## Project Overview
**My Reading Alcove** is a personal book tracking web app. Users can log books they've read, store cover art, ratings, summaries, read dates, and format (paper/ebook/audiobook). It has a barcode scanner for ISBN lookup, Google Books and Open Library API integration, CSV import/export, cover/ISBN backfill tools, and backup/restore. It is a PWA (installable on mobile).

## Repository & Deployment
- **Repo:** https://github.com/dpj1951/my-reading-room
- **Working branch:** `reading-alcove`
- **Primary live app:** https://myreadingalcove.com (custom domain) / https://my-reading-room2.onrender.com (Render URL)
- **Secondary service:** https://reading-alcove-auth.onrender.com (older service, ignore)
- **Platform:** Render (free tier, Flask web service)
- **Database:** Supabase PostgreSQL (project: ijrepkmhqdiezvbxxzke, region: AWS us-west-2)
- **Auth:** Supabase Auth (email/password, JWT tokens stored in Flask session)
- **Push method:** GitHub Contents API via browser JS

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
id               String(36)   # UUID primary key
title            String(500)
author           String(500)
isbn             String(20)
format           String(20)   # 'Paper', 'Ebook', 'Audiobook'
pages            String(10)
copyright_year   String(10)
read_date        String(10)   # stored as YYYY-MM-DD
rating           String(5)
cover_url        Text
summary          Text
read_time_hrs    String(10)
user_id          String(36)   # FK to Supabase auth.users.id
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

## CRITICAL: Password Reset Procedure
The only working method is the Supabase Admin API. DO NOT use SQL crypt() — it corrupts the GoTrue password.
Run this from https://supabase.com/dashboard/project/ijrepkmhqdiezvbxxzke/auth/users:
```javascript
fetch('https://ijrepkmhqdiezvbxxzke.supabase.co/auth/v1/admin/users/13a4418d-7a34-4c6c-bbfd-6bda8cfedd45', {
  method: 'PUT',
  headers: {
    'apikey': 'SERVICE_ROLE_KEY',
    'Authorization': 'Bearer SERVICE_ROLE_KEY',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ password: 'NEW_PASSWORD' })
}).then(r => r.json()).then(d => { window._r = {email: d.email}; });
```
Then immediately try logging in — do NOT run any SQL queries between the API call and login attempt.
Note: Supabase free tier rate-limits failed logins. After many failures, wait 1+ hour before retrying.

## Auth Implementation (Phase 1 — Complete Apr 8 2026)
- Supabase Auth via REST API (`/auth/v1/token` for sign-in, `/auth/v1/signup`)
- JWT access token stored in Flask `session["access_token"]`
- `get_current_user()` decodes JWT to get user id + email
- `@login_required` decorator on all routes including home
- `@app.context_processor` injects `current_user` dict into all templates
- Logout bar added to books.html, settings.html, utilities.html, authors.html
- `/signup`, `/login`, `/logout`, `/forgot-password`, `/reset-password` routes
- All book queries scoped to `g.user["id"]`

## Changes (Apr 16 2026)
- Custom domain myreadingalcove.com purchased and configured (Namecheap: A @ → 216.24.57.1, CNAME www → my-reading-room2.onrender.com)
- Supabase Site URL updated to https://myreadingalcove.com
- PWA manifest start_url fixed: /books → / (was causing mobile PWA to skip home page)
- Login redirect fixed: now lands on home page instead of books after login
- Removed Wipe Library UI from utilities page (backend route kept for future use)

## Changes (Apr 15 2026)
- Removed "Log in" link from home page (home.html) — was appearing in bottom-right corner for logged-in users
- Push method: GitHub Contents API via Chrome extension JS (GH_TOKEN pasted in chat, revoke after session)

## Changes (Apr 14 2026)
- Fixed garbled mojibake emoji in format buttons on add.html (📖 Paper, 📱 Ebook, 🎧 Audiobook) and page title — UTF-8 bytes were stored as latin-1 characters
- Home page shelf: removed 📚 and 🔖, kept only 📖
- Authors page filter: now searches both author names and book titles (added `data-titles` attribute to each author-group, updated JS filter)
- Authors page filter: shows "No results found" message instead of blank when search has no matches
- Wipe Library feature: discussed restricting to owner only — reverted pending decision on approach (hardcoded UID vs email vs DB flag)
- Push method: GitHub Contents API via Chrome extension JS (GH_TOKEN pasted in chat, revoke after session)

## Changes (Apr 13 2026 — Session 2)
- Barcode scanner fully working end-to-end (scan.html rebuilt with ZXing-js)
- Scanner uses getUserMedia + decodeContinuously for rear camera on mobile
- On ISBN detect: redirects to /add/manual?isbn=XXXXXXX
- add.html auto-populates search box from isbn_prefill and calls doSearch()
- Format defaults to Paper, Read Date defaults to today when arriving from scanner
- User taps Select on result → all fields filled, then just Save
- Tested successfully: scanned Red Lily by Nora Roberts, saved to library with cover
- Terminal push workflow confirmed: cat > /tmp/fix.py << 'PYEOF' ... PYEOF && python3 /tmp/fix.py
- Token workflow: generate at github.com/settings/tokens (classic, repo scope), export GH_TOKEN=..., unset when done
- Known remaining issue: garbled emoji in format buttons on add form (pre-existing UTF-8 bug)

## Changes (Apr 13 2026 — Session 1)
- Home page nav restructured: Books / Authors / Add a Book / Utilities (Settings and Help removed)
- "+ Add Book" button removed from Books and Authors navbars — add books via home page only
- Terminal + GitHub API established as push workflow (python3 script via GH_TOKEN env var)
- Scanner page still placeholder — building barcode scanner next session
- Token workflow: generate at github.com/settings/tokens (classic, repo scope), export GH_TOKEN=..., unset when done

## Bugs Fixed (Apr 12 2026)
- Books page navbar updated to match authors page (frosted glass, DM Serif Display, sticky)
- Books page list view removed — grid only now
- Supabase migrated to new API key format — SUPABASE_ANON_KEY updated to sb_publishable_25JxbKV5-pocxq9xrEE6bQ_ORKEBSvL
- SUPABASE_JWT_SECRET deleted from Render env vars (Supabase rotated JWT signing from HS256 to ECC P-256; app uses unverified decode fallback which works fine)
- Password reset to Reading2026!
- Import CSV was failing with duplicate key error: import now generates fresh UUIDs instead of reusing CSV ids (avoids conflicts with stale local SQLite on Render disk)
- Import duplicate check scoped to user_id so books from other users don't cause false skips
- Wipe button still broken (deletes 0 books) — workaround: delete directly via Supabase REST API with service key filtering by user_id

## Bugs Fixed (Apr 10 2026)
- Added @login_required to home route (was missing)
- Authors page now sorts by last name
- Garbled UTF-8 chars removed from utilities.html script blocks
- Books page navbar updated to match authors page style (frosted glass, DM Serif Display, SVG back arrow, blue + Add Book button)
- SUPABASE_ANON_KEY corrected in Render (was sb_publishable_ format, now legacy JWT)
- SECRET_KEY added to Render env vars
- /reset-password route and template added for forgot password flow
- Service role key obtained and documented above

## Known Issues / Next Session TODO
- **Login rate limited:** After many failed attempts on Apr 10, Supabase may still be rate-limiting. Try logging in fresh — should work with password Reading2026!
- **Service worker cache:** May serve stale pages. Hard reload or visit /logout first.
- **reading-alcove-auth.onrender.com** — old service, ignore or delete.

## How to Push Changes
The GitHub API works from any page. Standard push pattern:
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

## Planned Development Roadmap
### Phase 1 — Auth & Per-User Data ✅ COMPLETE (Apr 8 2026)
### Phase 2 — Stripe Billing (SKIPPED — staying free for now)
### Phase 3 — Production Readiness
- Upgrade Render to $7/month Starter (eliminates cold start)
- Delete reading-alcove-auth.onrender.com service
- Privacy policy page

## Product & Distribution Decisions
- **Distribution:** Web-first PWA
- **Auth:** Supabase Auth (complete)
- **Billing:** None for now (free personal use)
- **Hosting:** Render free tier (upgrade to Starter $7/mo when ready to launch publicly)
- **Database:** Supabase PostgreSQL
- **Email:** Not needed yet
