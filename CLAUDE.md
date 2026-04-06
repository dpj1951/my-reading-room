# CLAUDE.md — My Reading Alcove

This file gives Claude full context on this project so sessions can resume without re-explaining.

## Project Overview

**My Reading Alcove** is a personal book tracking web app. Users can log books they've read, store cover art, ratings, summaries, read dates, and format (paper/ebook/audiobook). It has a barcode scanner for ISBN lookup, Google Books and Open Library API integration, CSV import/export, cover/ISBN backfill tools, and backup/restore. It is a PWA (installable on mobile).

## Repository & Deployment

- **Repo:** https://github.com/dpj1951/my-reading-room
- **Working branch:** `reading-alcove`
- **Live app:** https://my-reading-room2.onrender.com
- **Platform:** Render (free tier, Flask web service + PostgreSQL)
- **Push method:** GitHub Contents API via browser JS (shell has no external network access; use fetch() from the Render app page which can reach api.github.com)

## Tech Stack

- **Backend:** Python / Flask (single file: `app.py`, ~67K)
- **Database:** SQLAlchemy + PostgreSQL (Render managed DB); SQLite locally
- **Templates:** Jinja2 (all in `templates/`)
- **Frontend:** Vanilla JS + CSS (dark theme, DM Serif Display + DM Sans fonts)
- **Static:** `static/enrich.js`, service worker (`sw.js`), PWA manifest + icons
- **Dependencies:** flask, flask-sqlalchemy, psycopg2-binary, requests, gunicorn (no pinned versions in requirements.txt)

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
cover_url      Text         # FIXED: was String(500), caused truncation errors
summary        Text
read_time_hrs  String(10)
```

## Bugs Fixed This Session (Apr 5 2026)

### 1. 500 error on edit save (stale DB connection)
- **Cause:** Render free tier sleeps after 15 min idle. SQLAlchemy pool holds stale connections. POST to /book/<id>/edit would fail on db.session.commit() with OperationalError.
- **Fix:** Added `SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True, "pool_recycle": 300}` to app config.

### 2. Edit save silently failing (no error shown)
- **Cause:** try/except was catching the DB error but edit.html had no flash message display.
- **Fix:** Changed except block to pass `save_error` variable to template; added error banner to edit.html.

### 3. StringDataRightTruncation on cover_url
- **Cause:** `cover_url` column was `VARCHAR(500)`. Some books had `data:image/webp;base64,...` URLs stored (inline encoded images, thousands of chars).
- **Fix:** Changed model to `db.Text`; added `ALTER TABLE books ALTER COLUMN cover_url TYPE TEXT` in `init_db()` so the live PostgreSQL column was widened automatically on next deploy.

## How to Push Changes

The shell sandbox has no external network access. The browser (Claude in Chrome) CAN reach api.github.com when the active tab is on `my-reading-room2.onrender.com`. 

Pattern:
```javascript
const TOKEN = 'ghp_...'; // get fresh token from user if expired
// 1. Fetch file meta (gets SHA + base64 content)
const meta = await (await fetch('https://api.github.com/repos/dpj1951/my-reading-room/contents/FILENAME?ref=reading-alcove', { headers: { 'Authorization': 'token ' + TOKEN } })).json();
// 2. Decode, patch, re-encode
const bytes = Uint8Array.from(atob(meta.content.replace(/\n/g,'')), c => c.charCodeAt(0));
let code = new TextDecoder().decode(bytes);
// ... make string replacements ...
const outBytes = new TextEncoder().encode(code);
let bin = ''; outBytes.forEach(b => bin += String.fromCharCode(b));
// 3. PUT
const put = await (await fetch('https://api.github.com/repos/dpj1951/my-reading-room/contents/FILENAME', {
  method: 'PUT',
  headers: { 'Authorization': 'token ' + TOKEN, 'Content-Type': 'application/json' },
  body: JSON.stringify({ message: 'commit message', content: btoa(bin), sha: meta.sha, branch: 'reading-alcove' })
})).json();
```

## Planned Development Roadmap

The app is being evolved into a **multi-user subscription product**. No hiring out — Claude does the implementation work with dennis testing/reviewing.

### Phase 1 — Auth & Per-User Data
- Supabase project setup (auth + database)
- Signup / login / logout / password reset pages
- Add `user_id` to books table
- Lock every route to logged-in user's data only (`@login_required` + `WHERE user_id = current_user`)

### Phase 2 — Stripe Billing
- Flat monthly subscription fee model
- Stripe customer created on signup
- Subscription checkout flow
- Webhook endpoint (activate/deactivate on payment success/failure)
- Gate entire app behind active subscription check

### Phase 3 — Account Page & Email
- Account page: view plan, cancel subscription
- Stripe customer portal for billing management
- Welcome email on signup
- Failed payment handling

### Phase 4 — Production Readiness
- New environment variables on Render (Supabase keys, Stripe keys)
- End-to-end testing with Stripe test cards
- Privacy policy page (required for billing)
- Deployment config review

## Product & Distribution Decisions

- **Distribution:** Web-first. PWA is sufficient for the user experience — installs on home screen, works offline, looks like a native app. No App Store planned initially.
- **Why not App Store:** 30% revenue cut, thin WebView apps get rejected by Apple, discoverability will come from direct channels (book communities, social) not App Store search.
- **Auth provider:** Supabase Auth (free up to 50k MAU, email/password + magic links, integrates with PostgreSQL)
- **Billing:** Stripe flat monthly fee. Stripe customer portal handles cancellation/billing UI.
- **Hosting:** Render or Fly.io for Flask backend. Supabase for database (replaces Render managed PostgreSQL).
- **Email:** Postmark or Resend for transactional email.

## Environment Variables (current)

- `DATABASE_URL` — PostgreSQL connection string (Render managed)
- `SECRET_KEY` — Flask session secret
- `GOOGLE_BOOKS_API_KEY` — for book lookup and cover/ISBN backfill

## Environment Variables (to add in Phase 1-2)

- `SUPABASE_URL`
- `SUPABASE_KEY`
- `STRIPE_SECRET_KEY`
- `STRIPE_WEBHOOK_SECRET`
- `STRIPE_PRICE_ID` — the ID of the monthly subscription price in Stripe
