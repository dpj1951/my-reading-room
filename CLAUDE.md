# CLAUDE.md — My Reading Alcove

This file gives Claude full context on this project so sessions can resume without re-explaining.

## Project Overview

My Reading Alcove is a personal book tracking web app. Users can log books they've read, store cover art, ratings, summaries, read dates, and format (paper/ebook/audiobook). It has a barcode scanner for ISBN lookup, Google Books and Open Library API integration, CSV import/export, cover/ISBN backfill tools, and backup/restore. It is a PWA (installable on mobile). It is being evolved into a **multi-user subscription product**.

## Repository & Deployment

- Repo: https://github.com/dpj1951/my-reading-room
- **Stable branch:** `reading-alcove` → https://my-reading-room2.onrender.com (single-user, no auth — DO NOT touch)
- **Dev branch:** `phase-1-auth` → second Render service (to be set up) with Supabase auth
- Platform: Render (free tier, Flask web service + PostgreSQL)
- Push method: GitHub Contents API via browser JS from the Render app page

## Tech Stack

- Backend: Python / Flask (single file: app.py)
- Database: SQLAlchemy + PostgreSQL (Render managed DB for stable; Supabase PostgreSQL for phase-1-auth)
- Templates: Jinja2 (all in templates/)
- Frontend: Vanilla JS + CSS (dark theme, DM Serif Display + DM Sans fonts)
- Static: static/enrich.js, service worker (sw.js), PWA manifest + icons
- Auth: Supabase Auth (phase-1-auth branch)
- Dependencies: flask, flask-sqlalchemy, psycopg2-binary, requests, gunicorn, supabase

## Database Model (Book)

```
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
user_id          String(36)   # Added in Phase 1 — Supabase auth user UUID
```

## How to Push Changes

The shell sandbox has no external network access. The browser (Claude in Chrome) CAN reach api.github.com when the active tab is on my-reading-room2.onrender.com.

```js
const TOKEN = 'ghp_...'; // get fresh token from user if expired
// 1. Fetch file meta (gets SHA + base64 content)
const meta = await (await fetch('https://api.github.com/repos/dpj1951/my-reading-room/contents/FILENAME?ref=BRANCH', {
  headers: { 'Authorization': 'token ' + TOKEN }
})).json();
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
  body: JSON.stringify({ message: 'commit message', content: btoa(bin), sha: meta.sha, branch: 'BRANCH' })
})).json();
```

## Environment Variables

### Current (reading-alcove / Render managed DB)
- `DATABASE_URL` — PostgreSQL connection string (Render managed)
- `SECRET_KEY` — Flask session secret
- `GOOGLE_BOOKS_API_KEY` — for book lookup and cover/ISBN backfill

### To add for phase-1-auth Render service
- `DATABASE_URL` — Supabase PostgreSQL connection string
- `SECRET_KEY` — Flask session secret
- `SUPABASE_URL` — https://ijrepkmhqdiezvbxxzke.supabase.co
- `SUPABASE_KEY` — Supabase service role key (sb_secret_...)
- `GOOGLE_BOOKS_API_KEY`

## Phase Progress

### ✅ Completed bugs (Apr 5 2026)
1. 500 error on edit save (stale DB connection) — fixed with pool_pre_ping
2. Edit save silently failing — fixed with error banner in edit.html
3. StringDataRightTruncation on cover_url — fixed by widening to db.Text

### ✅ Phase 1 — Auth & Per-User Data (Apr 6 2026, branch: phase-1-auth)
- Created `phase-1-auth` branch from `reading-alcove`
- Added Supabase auth client (supabase-py)
- Added `user_id` column to Book model + migration in init_db
- Added `login_required` decorator + `get_user_id()` helper
- Added auth routes: /login, /signup, /logout, /forgot-password
- All routes protected with @login_required
- All Book queries filtered by user_id
- Added auth templates: login.html, signup.html, forgot_password.html
- **TODO:** Set up second Render service pointing at phase-1-auth branch
- **TODO:** Get Supabase DB connection string and set DATABASE_URL on new Render service
- **TODO:** Test signup → login → add book → logout flow end-to-end

### 🔜 Phase 2 — Stripe Billing
- Flat monthly subscription fee model
- Stripe customer created on signup
- Subscription checkout flow
- Webhook endpoint (activate/deactivate on payment success/failure)
- Gate entire app behind active subscription check

### 🔜 Phase 3 — Account Page & Email
- Account page: view plan, cancel subscription
- Stripe customer portal for billing management
- Welcome email on signup
- Failed payment handling

### 🔜 Phase 4 — Production Readiness
- New environment variables on Render
- End-to-end testing with Stripe test cards
- Privacy policy page
- Deployment config review

## Product & Distribution Decisions

- **Distribution:** Web-first. PWA installs on home screen. No App Store planned initially.
- **Auth:** Supabase Auth (free up to 50k MAU)
- **Billing:** Stripe flat monthly fee. Customer portal for cancellation.
- **Hosting:** Render for Flask backend. Supabase for database.
- **Email:** Postmark or Resend for transactional email.
