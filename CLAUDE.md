# CLAUDE.md — My Reading Alcove

This file gives Claude full context on this project so sessions can resume without re-explaining.

## Project Overview
**My Reading Alcove** is a personal book tracking web app. Users can log books they've read, store cover art, ratings, summaries, read dates, and format (paper/ebook/audiobook). It has a barcode scanner for ISBN lookup, Google Books and Open Library API integration, CSV import/export, cover/ISBN backfill tools, and backup/restore. It is a PWA (installable on mobile).

## Repository & Deployment
- **Repo:** https://github.com/dpj1951/my-reading-room
- **Working branch:** `reading-alcove`
- **Primary live app:** https://myreadingalcove.com (custom domain) / https://my-reading-room2.onrender.com (Render URL)
- **Secondary service:** https://reading-alcove-auth.onrender.com (older service, ignore)
- **Platform:** Render (Starter plan), Flask web service
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
- **Plan:** PRO ($25/month) — upgraded Apr 24 2026
- **IPv4 add-on:** ENABLED ($4/month) — added Apr 24 2026, required for Render connection
- **Project ref:** ijrepkmhqdiezvbxxzke
- **Project URL:** https://ijrepkmhqdiezvbxxzke.supabase.co
- **Publishable key:** sb_publishable_25JxbKV5-pocxq9xrEE6bQ_ORKEBSvL
- **Service role key:** eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlqcmVwa21ocWRpZXp2Ynh4emtlIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NTUwMTQ4NiwiZXhwIjoyMDkxMDc3NDg2fQ.icmO0p4L7eUBaBQbXjfzhrqrCuJhj7QYUmZT6rlQzTc
- **Auth user (owner):** dpjohnson1951@gmail.com (UID: 13a4418d-7a34-4c6c-bbfd-6bda8cfedd45)
- **Books:** 213 books all assigned to owner user_id
- **Database password:** TDepdKS7o9RDeurT (reset Apr 24 2026)
- **RLS:** DISABLED on books table
- **Email confirmations:** disabled (mailer_autoconfirm: true)
- **Site URL:** https://myreadingalcove.com
- **JWT:** Supabase now uses ES256 (new signing keys) — app uses verify_signature=False for JWT decode

## Render Environment Variables (my-reading-room2)
- `DATABASE_URL` — postgresql://postgres.ijrepkmhqdiezvbxxzke:TDepdKS7o9RDeurT@aws-0-us-west-2.pooler.supabase.com:6543/postgres (updated Apr 24 2026)
- `GOOGLE_BOOKS_API_KEY` — for book lookup and cover/ISBN backfill
- `SUPABASE_URL` — https://ijrepkmhqdiezvbxxzke.supabase.co
- `SUPABASE_ANON_KEY` — must be the LEGACY JWT key (eyJhbGci...), NOT the sb_publishable_ key
- `SECRET_KEY` — reading-alcove-secret-2026
- `SUPABASE_JWT_SECRET` — legacy JWT secret (88 chars). Find at: Supabase → Settings → JWT Keys → Legacy JWT Secret → Reveal. NOTE: Not actually used for decode anymore (app uses verify_signature=False due to ES256 migration)
- `MAINTENANCE_MODE` — currently `true` — set to `false` to reopen site

## Owner Access During Maintenance Mode
**Permanent bypass URL:** `https://my-reading-room2.onrender.com/login`
- The /login route is always accessible even in maintenance mode
- After login, lands on /home with full navigation (Books, Authors, Add a Book, Utilities)
- Session persists — no need for preview token

## CRITICAL: Password Reset Procedure
The only working method is the Supabase Admin API. DO NOT use SQL crypt() — it corrupts the GoTrue password.
```javascript
fetch('https://ijrepkmhqdiezvbxxzke.supabase.co/auth/v1/admin/users/13a4418d-7a34-4c6c-bbfd-6bda8cfedd45', {
  method: 'PUT',
  headers: { 'apikey': 'SERVICE_ROLE_KEY', 'Authorization': 'Bearer SERVICE_ROLE_KEY', 'Content-Type': 'application/json' },
  body: JSON.stringify({ password: 'NEW_PASSWORD' })
}).then(r => r.json()).then(d => { window._r = {email: d.email}; });
```

## Auth Implementation
- Supabase Auth via REST API (`/auth/v1/token` for sign-in, `/auth/v1/signup`)
- JWT access token stored in Flask `session["access_token"]`
- `get_current_user()` decodes JWT using `verify_signature=False` (Supabase migrated to ES256, legacy HS256 no longer works)
- `session.permanent = True` with 30-day lifetime — sessions persist across requests
- `SESSION_COOKIE_SECURE`, `SESSION_COOKIE_HTTPONLY`, `SESSION_COOKIE_SAMESITE=Lax` configured
- `@login_required` decorator on all routes except `/` and `/login`
- All book queries scoped to `g.user["id"]`
- `/home` route added — @login_required, always serves home.html, login redirects here

## check_maintenance() logic
- Always allows: /static/*, /login, /logout, /forgot-password, /reset-password
- Allows preview bypass: ?preview=alcove2026 sets session['preview_bypass']
- Allows logged-in users through regardless
- Public gets maintenance.html (503) for all other routes

## Changes (Apr 24 2026)
### Session / Login Fixed
- **Root cause of empty books:** Supabase migrated to ES256 JWT signing — app was trying HS256, decode failed, session wiped on every request
- **Fix:** Changed get_current_user() to use verify_signature=False — token trusted implicitly (issued by Supabase auth endpoint, stored in server session)
- **Fix:** session.permanent=True + 30-day lifetime + secure cookie config
- **Fix:** check_maintenance() now allows /login through and allows logged-in users through
- **Fix:** Added /home route — login redirects to /home instead of / (avoids landing page)

### Database Connection Fixed
- **Root cause of 500 error on /books:** DATABASE_URL pointed to alcove-library (Render DB) not Supabase
- **Fix:** Updated DATABASE_URL to Supabase transaction pooler URL
- **Supabase Pro upgraded** ($25/month) — no project pausing, daily backups, email support
- **IPv4 add-on enabled** ($4/month) — required for Render → Supabase pooler connection
- **Database password reset** to TDepdKS7o9RDeurT
- **Status at end of session:** IPv4 DNS propagation still in progress (~10-15 min) — connection should work next session

### Infrastructure
- MAINTENANCE_MODE=true (site closed to public)
- LOGIN works: https://my-reading-room2.onrender.com/login → /home ✅
- BOOKS page: 500 error — awaiting IPv4 DNS propagation (should auto-resolve)

## Changes (Apr 20 2026)
### Multi-Device Sync — Auto-Refresh on Focus
- Added visibilitychange listener to books.html, authors.html, home.html
- If page hidden 2+ min, silently reloads on return

### Subscription / Pricing Model
- 30-day free trial → $0.99/month via Stripe (not yet wired)
- Wording updated across settings.html, add.html, utilities.html

### Public Landing Page
- templates/landing.html built — / route serves it for logged-out visitors
- Behind maintenance mode — will show when site reopens

## Changes (Apr 18 2026)
### Maintenance Mode
- MAINTENANCE_MODE env var toggle added to app.py
- templates/maintenance.html added

### Subscription / Role System
- user_roles table in Supabase (user_id, role, created_at)
- Roles: free (20 book limit), beta (full access), subscriber (paid), owner (always full)
- Owner UID inserted as role=owner

## Changes (Apr 16 2026)
- Custom domain myreadingalcove.com configured
- PWA manifest start_url fixed
- Login redirect fixed

## Known Issues / Next Session TODO
- **Books page 500 error** — IPv4 DNS propagation should complete within 10-15 min of add-on activation. Test with: `python3 -c "import psycopg2; conn = psycopg2.connect(host='aws-0-us-west-2.pooler.supabase.com', port=6543, dbname='postgres', user='postgres.ijrepkmhqdiezvbxxzke', password='TDepdKS7o9RDeurT', sslmode='require'); print('OK:', conn.cursor().execute('SELECT COUNT(*) FROM public.books') or 'connected')"`
- **Email setup** — freetrial@myreadingalcove.com not yet configured
- **Stripe billing** — wire up when ready
- **book_count in context** — add.html banner cosmetic issue only
- **Wipe Library button** — still broken
- **MAINTENANCE_MODE** — currently true, set to false to reopen

## Pre-Launch Checklist
1. Verify books load at /books after IPv4 DNS propagation
2. Set up freetrial@myreadingalcove.com email forwarding
3. Set MAINTENANCE_MODE=false in Render and redeploy
4. Verify landing page at myreadingalcove.com
5. Wire up Stripe

## How to Push Changes
Token: generate at github.com/settings/tokens (classic, repo scope), revoke after session.
```javascript
(async () => {
  const T = 'ghp_TOKEN';
  const BASE = 'https://api.github.com/repos/dpj1951/my-reading-room/contents/';
  const meta = await (await fetch(BASE + 'FILENAME?ref=reading-alcove', { headers: { Authorization: 'token ' + T } })).json();
  const bytes = Uint8Array.from(atob(meta.content.replace(/\n/g,'')), c => c.charCodeAt(0));
  let code = new TextDecoder().decode(bytes);
  // make changes to code...
  const enc = new TextEncoder().encode(code);
  let bin = ''; enc.forEach(b => bin += String.fromCharCode(b));
  const put = await (await fetch(BASE + 'FILENAME', { method: 'PUT', headers: { Authorization: 'token ' + T, 'Content-Type': 'application/json' }, body: JSON.stringify({ message: 'commit msg', content: btoa(bin), sha: meta.sha, branch: 'reading-alcove' }) })).json();
  window._r = put.commit ? 'OK:' + put.commit.sha.substring(0,7) : 'ERR:' + JSON.stringify(put).substring(0,100);
})();
```

## Planned Development Roadmap

### Phase 1 — Auth & Per-User Data COMPLETE (Apr 8 2026)

### Phase 2 — Subscription Model (IN PROGRESS)
- DONE: Pricing model: 30-day free trial → $0.99/month
- DONE: Landing page with trial/pricing messaging
- DONE: In-app wording updated
- TODO: Email setup (freetrial@myreadingalcove.com)
- TODO: Stripe integration
- TODO: Trial timer enforcement

### Phase 3 — Production Readiness
- Delete reading-alcove-auth.onrender.com service
- Privacy policy page

## Product & Distribution Decisions
- Distribution: Web-first PWA
- Auth: Supabase Auth (complete)
- Billing: $0.99/month after 30-day free trial (Stripe, not yet wired)
- Hosting: Render Starter ($7/month)
- Database: Supabase Pro ($25/month) + IPv4 add-on ($4/month)
- Email: freetrial@myreadingalcove.com (not yet configured)
- Domain: myreadingalcove.com (Namecheap, pointed to Render)
