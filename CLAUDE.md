# CLAUDE.md — My Reading Alcove

This file gives Claude full context on this project so sessions can resume without re-explaining.

## Project Overview
**My Reading Alcove** is a personal book tracking web app. Users can log books they've read, store cover art, ratings, summaries, read dates, and format (paper/ebook/audiobook). It has a barcode scanner for ISBN lookup, Google Books and Open Library API integration, CSV import/export, cover/ISBN backfill tools, and backup/restore. It is a PWA (installable on mobile).

## Repository & Deployment
- **Repo:** https://github.com/dpj1951/my-reading-room
- **Working branch:** `reading-alcove`
- **Primary live app:** https://myreadingalcove.com (custom domain) / https://my-reading-room2.onrender.com (Render URL)
- **Secondary service:** https://reading-alcove-auth.onrender.com (older service, ignore)
- **Platform:** Render (Starter plan $7/month), Flask web service
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
- **Plan:** PRO ($25/month) — upgraded Apr 24 2026. No project pausing, daily backups.
- **IPv4 add-on:** ENABLED ($4/month) — added Apr 24 2026
- **Project ref:** ijrepkmhqdiezvbxxzke
- **Project URL:** https://ijrepkmhqdiezvbxxzke.supabase.co
- **Publishable key:** sb_publishable_25JxbKV5-pocxq9xrEE6bQ_ORKEBSvL
- **Service role key:** eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlqcmVwa21ocWRpZXp2Ynh4emtlIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NTUwMTQ4NiwiZXhwIjoyMDkxMDc3NDg2fQ.icmO0p4L7eUBaBQbXjfzhrqrCuJhj7QYUmZT6rlQzTc
- **Auth user (owner):** dpjohnson1951@gmail.com (UID: 13a4418d-7a34-4c6c-bbfd-6bda8cfedd45)
- **Books:** 213 books confirmed displaying ✅ (216 total in DB including test accounts)
- **Database password:** TDepdKS7o9RDeurT (reset Apr 24 2026)
- **RLS:** DISABLED on books table
- **Email confirmations:** disabled (mailer_autoconfirm: true)
- **Site URL:** https://myreadingalcove.com
- **JWT:** Supabase now uses ES256 (new signing keys) — app uses verify_signature=False for JWT decode

## Render Environment Variables (my-reading-room2)
- `DATABASE_URL` — postgresql://postgres:TDepdKS7o9RDeurT@db.ijrepkmhqdiezvbxxzke.supabase.co:5432/postgres?sslmode=require
  - **CRITICAL:** Use DIRECT connection (db.ijrepkmhqdiezvbxxzke.supabase.co:5432), NOT the pooler. The pooler (aws-0-us-west-2.pooler.supabase.com) gives ENOTFOUND errors even with IPv4 add-on.
- `GOOGLE_BOOKS_API_KEY` — for book lookup and cover/ISBN backfill
- `SUPABASE_URL` — https://ijrepkmhqdiezvbxxzke.supabase.co
- `SUPABASE_ANON_KEY` — must be the LEGACY JWT key (eyJhbGci...), NOT the sb_publishable_ key
- `SECRET_KEY` — reading-alcove-secret-2026
- `SUPABASE_JWT_SECRET` — legacy JWT secret (88 chars). NOTE: Not actually used for decode (app uses verify_signature=False due to ES256 migration)
- `MAINTENANCE_MODE` — currently `true` — set to `false` to reopen site

## Owner Access During Maintenance Mode
**Permanent bypass URL:** `https://my-reading-room2.onrender.com/login`
- /login is always accessible even in maintenance mode
- After login → lands on /home with full navigation (Books, Authors, Add a Book, Utilities)
- All pages work for logged-in users even in maintenance mode

## CRITICAL: Password Reset Procedure
The only working method is the Supabase Admin API. DO NOT use SQL crypt().
```javascript
fetch('https://ijrepkmhqdiezvbxxzke.supabase.co/auth/v1/admin/users/13a4418d-7a34-4c6c-bbfd-6bda8cfedd45', {
  method: 'PUT',
  headers: { 'apikey': 'SERVICE_ROLE_KEY', 'Authorization': 'Bearer SERVICE_ROLE_KEY', 'Content-Type': 'application/json' },
  body: JSON.stringify({ password: 'NEW_PASSWORD' })
}).then(r => r.json()).then(d => { window._r = {email: d.email}; });
```

## Auth Implementation
- Supabase Auth via REST API (`/auth/v1/token` for sign-in)
- JWT access token stored in Flask `session["access_token"]`
- `get_current_user()` decodes JWT using `verify_signature=False` (Supabase migrated to ES256)
- `session.permanent = True` with 30-day lifetime
- `SESSION_COOKIE_SECURE`, `SESSION_COOKIE_HTTPONLY`, `SESSION_COOKIE_SAMESITE=Lax` set
- `@login_required` on all routes except `/` and `/login`
- `/home` route — @login_required, always serves home.html, login redirects here
- All book queries scoped to `g.user["id"]`

## check_maintenance() logic
- Always allows: /static/*, /login, /logout, /forgot-password, /reset-password
- Allows preview bypass: ?preview=alcove2026 sets session['preview_bypass']
- Allows logged-in users through regardless
- Public gets maintenance.html (503) for all other routes

## Changes (Apr 25 2026)
### FULLY WORKING — 213 Books Displaying ✅
- **Final fix:** DATABASE_URL updated to use Supabase DIRECT connection
  - Direct host: db.ijrepkmhqdiezvbxxzke.supabase.co:5432
  - The pooler (aws-0-us-west-2.pooler.supabase.com) kept giving ENOTFOUND despite IPv4 add-on
  - Direct connection works perfectly with Supabase Pro
- Books page confirmed working: 213 books with covers loading ✅
- Home, Authors, Add a Book, Utilities all working ✅
- Login via https://my-reading-room2.onrender.com/login works ✅

## Changes (Apr 24 2026)
### Session / Login Fixed
- **Root cause:** Supabase migrated to ES256 JWT — HS256 decode failed, wiped session on every request
- **Fix:** get_current_user() uses verify_signature=False
- **Fix:** session.permanent=True + 30-day lifetime + secure cookie config
- **Fix:** check_maintenance() allows /login through + logged-in users always pass
- **Fix:** Added /home route — login redirects to /home

### Infrastructure
- Supabase Pro upgraded ($25/month) — no pausing, daily backups
- IPv4 add-on enabled ($4/month)
- Database password reset to TDepdKS7o9RDeurT
- MAINTENANCE_MODE=true (site closed to public)

## Changes (Apr 20 2026)
### Multi-Device Sync, Pricing, Landing Page
- Auto-refresh on focus (visibilitychange listener)
- 30-day free trial → $0.99/month pricing decided
- templates/landing.html built — public-facing marketing page
- / route: logged-out → landing.html, logged-in → home.html

## Changes (Apr 18 2026)
- Maintenance mode added (MAINTENANCE_MODE env var)
- user_roles table (free/beta/subscriber/owner)
- Role: owner = dpjohnson1951@gmail.com

## Changes (Apr 16 2026)
- Custom domain myreadingalcove.com configured
- PWA manifest start_url fixed

## Known Issues / Next Session TODO
- **MAINTENANCE_MODE=true** — set to false in Render env + redeploy to open to public
- **Email setup** — freetrial@myreadingalcove.com not yet configured (Namecheap → Gmail forwarding)
- **Stripe billing** — wire up when ready; webhook sets role=subscriber
- **Wipe Library button** — still broken (workaround via Supabase SQL)
- **Landing page** — ready to go, just needs maintenance mode off

## Pre-Launch Checklist
1. Set up freetrial@myreadingalcove.com email forwarding (Namecheap → Gmail)
2. Set MAINTENANCE_MODE=false in Render env vars and redeploy
3. Verify landing page at myreadingalcove.com
4. Verify logged-in users go to /home correctly
5. Wire up Stripe when ready

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

### Phase 1 — Auth & Per-User Data COMPLETE ✅

### Phase 2 — Subscription Model (IN PROGRESS)
- DONE: Pricing: 30-day free trial → $0.99/month
- DONE: Landing page
- DONE: In-app wording updated
- TODO: Email setup (freetrial@myreadingalcove.com)
- TODO: Stripe integration
- TODO: Trial timer enforcement

### Phase 3 — Production Readiness
- Delete reading-alcove-auth.onrender.com
- Privacy policy page
- Set MAINTENANCE_MODE=false and launch!

## Monthly Costs
- Render Starter: $7/month
- Supabase Pro: $25/month
- Supabase IPv4 add-on: $4/month
- **Total: $36/month** (breaks even at ~37 subscribers at $0.99/month)

## Product & Distribution Decisions
- Distribution: Web-first PWA
- Auth: Supabase Auth (complete)
- Billing: $0.99/month after 30-day free trial (Stripe, not yet wired)
- Hosting: Render Starter ($7/month)
- Database: Supabase Pro + IPv4 ($29/month)
- Email: freetrial@myreadingalcove.com (not yet configured)
- Domain: myreadingalcove.com (Namecheap, pointed to Render)
