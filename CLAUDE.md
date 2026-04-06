# CLAUDE.md – My Reading Alcove

This file gives Claude full context on this project so sessions can resume without re-explaining.

## Project Overview
My Reading Alcove is a personal book tracking web app. Users can log books they've read, store cover art, ratings, summaries, read dates, and format (paper/ebook/audiobook). It has a barcode scanner for ISBN lookup, Google Books and Open Library API integration, CSV import/export, cover/ISBN backfill tools, and backup/restore. It is a PWA (installable on mobile). It is being evolved into a multi-user subscription product.

## Repository & Deployment
- Repo: https://github.com/dpj1951/my-reading-room
- Stable branch: `reading-alcove` → https://my-reading-room2.onrender.com (single-user, no auth — DO NOT touch)
- Auth branch: `phase-1-auth` → https://reading-alcove-auth.onrender.com (multi-user with Supabase auth — ACTIVE DEV)
- Platform: Render (free tier, Flask web service)
- Push method: GitHub web editor UI (REST API returns 401 from browser — no PAT stored)

## Infrastructure Details

### Render
- Service: reading-alcove-auth
- Service ID: srv-d7a20q5m5p6s73b4u5v0
- Dashboard: https://dashboard.render.com/web/srv-d7a20q5m5p6s73b4u5v0
- Free tier — uses IPv4 only, cannot use Supabase direct connection (IPv6)

### Supabase
- Project ref: ijrepkmhqdiezvbxxzke
- Region: us-west-2 (AWS)
- Dashboard: https://supabase.com/dashboard/project/ijrepkmhqdiezvbxxzke
- Auth: Supabase Auth (supabase-py) — handles signup/login/logout
- Email confirmation: DISABLED (mailer_autoconfirm: true) — users sign up without email verify
- Database connection: Transaction pooler (IPv4-compatible)
  - Host: aws-1-us-west-2.pooler.supabase.com
  - Port: 6543
  - DATABASE_URL on Render uses this pooler URL (NOT the direct IPv6 connection)

### Database Schema
- books table — all existing columns plus user_id (text, FK to Supabase auth.users.id)
- All book queries filtered by user_id for per-user data isolation
- Supabase manages users (auth.users) — no separate users table in app DB

## Phase 1 — Completed

Goal: Add multi-user authentication to the existing single-user app.

What was built:
- Supabase Auth integration (signup, login, logout) via supabase-py
- @login_required decorator using Flask session to store user_id
- Per-user data isolation — all book queries filtered by user_id
- books table migrated to include user_id column
- Render deployment configured with Transaction pooler DATABASE_URL
- Email confirmation disabled (mailer_autoconfirm: true) for frictionless signup
- Full auth flow tested: signup → auto-login → add book → logout → redirect to /login

Key files changed:
- app.py — added session import, login_required decorator, user_id filtering, Supabase auth routes
- requirements.txt — added supabase
- templates/login.html, templates/signup.html — new auth pages

Last commit on phase-1-auth: fc77375

## Phase 2 — Planned (Next)

Goal: Turn the app into a paid subscription product.

Planned work:
1. Subscription tiers — Free (limited books, e.g. 20) vs Pro (unlimited)
2. Stripe billing — checkout, webhooks, subscription management, customer portal
3. Admin panel — view all users, subscription status, manually adjust tiers
4. Subscription enforcement — gate features/book-count by tier in app.py
5. User profile page — show current plan, upgrade/downgrade button
6. Transactional email — welcome email, payment receipt (via Resend or SendGrid)
7. Stripe env vars on Render: STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET, STRIPE_PRICE_ID_PRO

Notes for Phase 2 start:
- Admin login is NOT a separate auth system — use Supabase Auth + is_admin flag in a profiles table (or hard-coded admin email check for now)
- Stripe test mode first, live keys only when ready to charge real users
- Keep reading-alcove (stable) branch untouched throughout

## Development Notes

### Updating env vars on Render (UI masks values — use API instead)
1. Go to Render Dashboard → Account Settings → API Keys → Create temporary key
2. Use it:
   GET https://api.render.com/v1/services/srv-d7a20q5m5p6s73b4u5v0/envVars
   Authorization: Bearer YOUR_KEY
3. Build new value, then PUT back
4. Revoke the key immediately after

### Disabling email confirmation on Supabase
From a logged-in supabase.com tab:
  const r = await fetch('/api/platform/token');
  const { token } = await r.json();
  fetch('https://api.supabase.com/v1/projects/ijrepkmhqdiezvbxxzke/config/auth', {
    method: 'PATCH',
    headers: { Authorization: 'Bearer ' + token, 'Content-Type': 'application/json' },
    body: JSON.stringify({ mailer_autoconfirm: true })
  });

### GitHub REST API note
The API returns 401 from a logged-in GitHub browser tab (session cookies not passed to REST API).
Use the GitHub web editor (https://github.com/dpj1951/my-reading-room/edit/phase-1-auth/FILENAME)
or generate a PAT (Settings → Developer settings → Personal access tokens) with repo scope.
