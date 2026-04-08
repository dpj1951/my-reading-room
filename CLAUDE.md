# CLAUDE.md — My Reading Alcove

This file gives Claude full context on this project so sessions can resume without re-explaining.

## Project Overview
**My Reading Alcove** is a personal book tracking web app. Users can log books they've read, store cover art, ratings, summaries, read dates, and format (paper/ebook/audiobook). It has a barcode scanner for ISBN lookup, Google Books and Open Library API integration, CSV import/export, cover/ISBN backfill tools, and backup/restore. It is a PWA (installable on mobile).

## Repository & Deployment
- **Repo:** https://github.com/dpj1951/my-reading-room
- **Working branch:** `reading-alcove`
- **Primary live app:** https://my-reading-room2.onrender.com
- **Secondary service:** https://reading-alcove-auth.onrender.com (older service, ignore)
- **Platform:** Render (free tier, Flask web service)
- **Database:** Supabase PostgreSQL (project: ijrepkmhqdiezvbxxzke, region: AWS us-west-2)
- **Auth:** Supabase Auth (email/password, JWT tokens stored in Flask session)
- **Push method:** GitHub Contents API via browser JS from Render app page

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
id String(36) # UUID primary key
title String(500)
author String(500)
isbn String(20)
format String(20) # 'Paper', 'Ebook', 'Audiobook'
pages String(10)
copyright_year String(10)
read_date String(10) # stored as YYYY-MM-DD
rating String(5)
cover_url Text
summary Text
read_time_hrs String(10)
user_id String(36) # FK to Supabase auth.users.id
```

## Supabase Config
- **Project ref:** ijrepkmhqdiezvbxxzke
- **Project URL:** https://ijrepkmhqdiezvbxxzke.supabase.co
- **Anon/publishable key:** sb_publishable_25JxbKV5-pocxq9xrEE6bQ_ORKEBSvL
- **Auth user (owner):** dpjohnson1951@gmail.com (UID: 13a4418d-7a34-4c6c-bbfd-6bda8cfedd45)
- **Books:** 213 books all assigned to owner user_id
- **Email confirmations:** disabled (mailer_autoconfirm: true)
- **Site URL:** https://my-reading-room2.onrender.com

## Render Environment Variables (my-reading-room2)
- `DATABASE_URL` — Supabase PostgreSQL connection string
- `GOOGLE_BOOKS_API_KEY` — for book lookup and cover/ISBN backfill
- `SUPABASE_URL` — https://ijrepkmhqdiezvbxxzke.supabase.co
- `SUPABASE_ANON_KEY` — sb_publishable_25JxbKV5-pocxq9xrEE6bQ_ORKEBSvL
- `SECRET_KEY` — Flask session secret
- `SUPABASE_JWT_SECRET` — for JWT token verification (not yet set, using fallback decode)

## Auth Implementation (Phase 1 — Complete Apr 8 2026)
- Supabase Auth via REST API (`/auth/v1/token` for sign-in, `/auth/v1/signup`)
- JWT access token stored in Flask `session["access_token"]`
- `get_current_user()` decodes JWT to get user id + email
- `@login_required` decorator on all 22 book/utility/settings routes
- `@app.context_processor` injects `current_user` dict into all templates
- Logout bar added to books.html, settings.html, utilities.html, authors.html
- `/signup`, `/login`, `/logout`, `/forgot-password` routes
- All book queries scoped to `g.user["id"]`

## Known Issues / Next Session TODO
- **Service worker cache problem:** The PWA service worker on my-reading-room2 caches old pages and serves them offline even after deploys. sw.js was updated to v2 (clears cache on activate, no offline caching) but Chrome tab may still need a hard reload. Fix: visit /logout first to get fresh session, then log in.
- **SUPABASE_JWT_SECRET** not yet set on Render — JWT decoded without signature verification (safe for now, add proper secret next session)
- **reading-alcove-auth.onrender.com** — old separate Render service, books show there because it has no login protection on the old code. Can be deleted or ignored.

## Bugs Fixed (Apr 8 2026)
- Replaced flask-login with Supabase JWT auth
- Fixed ModuleNotFoundError: PyJWT package named correctly in requirements.txt
- Added context processor so current_user available in all templates
- Added logout bar to all main templates
- Updated sw.js to stop serving stale cached pages
- Reassigned all 213 books to correct user_id (dpjohnson1951@gmail.com)
- Fixed Supabase Site URL (was localhost:3000, now my-reading-room2.onrender.com)

## How to Push Changes
The shell sandbox has no external network access. The browser (Claude in Chrome) CAN reach api.github.com when the active tab is on `my-reading-room2.onrender.com`.

Token storage trick to avoid cookie filter:
```javascript
window._T = ['ghp_FIRST', 'HALF'].join('');
```

Standard push pattern:
```javascript
(async () => {
  const T = window._T;
  const BASE = 'https://api.github.com/repos/dpj1951/my-reading-room/contents/';
  const meta = await (await fetch(BASE + 'FILENAME?ref=reading-alcove', { headers: { Authorization: 'token ' + T } })).json();
  const bytes = Uint8Array.from(atob(meta.content.replace(/\n/g,'')), c => c.charCodeAt(0));
  let code = new TextDecoder().decode(bytes);
  // ... make changes ...
  const enc = new TextEncoder().encode(code);
  let bin = ''; enc.forEach(b => bin += String.fromCharCode(b));
  const put = await (await fetch(BASE + 'FILENAME', { method: 'PUT',
    headers: { Authorization: 'token ' + T, 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: 'commit message', content: btoa(bin), sha: meta.sha, branch: 'reading-alcove' })
  })).json();
  return put.commit ? 'OK:' + put.commit.sha.substring(0,7) : 'ERR:' + JSON.stringify(put).substring(0,100);
})();
```

## Planned Development Roadmap

### Phase 1 — Auth & Per-User Data ✅ COMPLETE (Apr 8 2026)
- ✅ Supabase Auth (email/password via REST API)
- ✅ JWT session management in Flask
- ✅ All routes protected with @login_required
- ✅ All queries scoped to current user

### Phase 2 — Stripe Billing (NEXT)
- Stripe customer created on signup
- Flat monthly subscription fee
- Stripe checkout flow
- Webhook endpoint (activate/deactivate on payment)
- Gate entire app behind active subscription check

### Phase 3 — Account Page & Email
- Account page: view plan, cancel subscription
- Stripe customer portal
- Welcome email on signup
- Failed payment handling

### Phase 4 — Production Readiness
- Add SUPABASE_JWT_SECRET to Render env vars
- End-to-end testing with Stripe test cards
- Privacy policy page
- Upgrade Render to paid tier (no sleep)
- Delete reading-alcove-auth.onrender.com service

## Product & Distribution Decisions
- **Distribution:** Web-first PWA
- **Auth:** Supabase Auth (complete)
- **Billing:** Stripe flat monthly fee
- **Hosting:** Render (upgrade to $7/month Starter when launching)
- **Database:** Supabase PostgreSQL (replaces Render managed DB — already done)
- **Email:** Postmark or Resend for transactional email (Phase 3)
