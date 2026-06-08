from flask import Flask, render_template, request, redirect, url_for, abort, jsonify, send_file, flash, session, g, make_response
import json
import os
import uuid
import requests
import re
import csv
import io
from datetime import date, datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from functools import wraps
import jwt as pyjwt
import stripe

app = Flask(__name__)
app.jinja_env.filters['enumerate'] = enumerate

STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY', '')
STRIPE_SECRET_KEY      = os.environ.get('STRIPE_SECRET_KEY', '')
STRIPE_PRICE_ID        = os.environ.get('STRIPE_PRICE_ID', '')
STRIPE_WEBHOOK_SECRET  = os.environ.get('STRIPE_WEBHOOK_SECRET', '')
stripe.api_key = STRIPE_SECRET_KEY

#  Â¢ Â¢  Maintenance mode  Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ 
MAINTENANCE_MODE = os.environ.get("MAINTENANCE_MODE", "false").lower() == "true"

@app.before_request
def check_maintenance():
    if MAINTENANCE_MODE:
        # Always allow static files, login, and logout through
        if request.path.startswith('/static'):
            return None
        if request.path in ('/login', '/logout', '/forgot-password', '/reset-password', '/signup'):
            return None
        # Set session flag when preview token is present
        if request.args.get('preview') == 'alcove2026':
            session['preview_bypass'] = True
        # Allow through if session flag is set
        if session.get('preview_bypass'):
            return None
        # Allow through if user is logged in
        if get_current_user():
            return None
        return render_template('maintenance.html'), 503


LIBRARY_FILE = "library.json"

#  Â¢ Â¢  Supabase config  Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ 
SUPABASE_URL        = os.environ.get("SUPABASE_URL", "https://ijrepkmhqdiezvbxxzke.supabase.co")
SUPABASE_ANON_KEY   = os.environ.get("SUPABASE_ANON_KEY", "")
SUPABASE_JWT_SECRET = os.environ.get("SUPABASE_JWT_SECRET", "")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

#  Â¢ Â¢  Role helpers  Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ 
def get_user_role(user_id):
    """Fetch role from user_roles table. Returns 'free' if not found."""
    try:
        url = SUPABASE_URL + "/rest/v1/user_roles?user_id=eq." + user_id + "&select=role"
        _key = SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY
        headers = {
            "apikey": _key,
            "Authorization": "Bearer " + _key,
        }
        resp = requests.get(url, headers=headers, timeout=5)
        rows = resp.json()
        if rows and isinstance(rows, list) and len(rows) > 0:
            return rows[0].get("role", "free")
    except Exception:
        pass
    return "free"

FREE_BOOK_LIMIT = 20

def is_subscriber():
    """Return True if current user has full access (subscriber, beta, or owner)."""
    role = session.get("user_role", "free")
    return role in ("subscriber", "beta", "owner", "trial")

#  Â¢ Â¢  Database  Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ 
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///library.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True, "pool_recycle": 300}
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
app.config["SESSION_COOKIE_SECURE"] = True
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["PERMANENT_SESSION_LIFETIME"] = 86400 * 30
GOOGLE_BOOKS_API_KEY = os.environ.get("GOOGLE_BOOKS_API_KEY", "")

db = SQLAlchemy(app)

#  Â¢ Â¢  Book model  Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ 
class Book(db.Model):
    __tablename__ = "books"
    id             = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title          = db.Column(db.String(500), nullable=False)
    author         = db.Column(db.String(500), nullable=False)
    isbn           = db.Column(db.String(20), default="")
    format         = db.Column(db.String(20), default="Paper")
    pages          = db.Column(db.String(10), default="")
    copyright_year = db.Column(db.String(10), default="")
    read_date      = db.Column(db.String(10), default="")
    rating         = db.Column(db.String(5), default="")
    cover_url      = db.Column(db.Text, default="")
    summary        = db.Column(db.Text, default="")
    read_time_hrs  = db.Column(db.String(10), default="")
    user_id        = db.Column(db.String(36), nullable=True)
    status         = db.Column(db.String(20), default="read")
    date_added     = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {"id": self.id, "title": self.title, "author": self.author, "isbn": self.isbn,
                "format": self.format, "pages": self.pages, "copyright_year": self.copyright_year,
                "read_date": self.read_date, "rating": self.rating, "cover_url": self.cover_url,
                "summary": self.summary, "read_time_hrs": self.read_time_hrs, "user_id": self.user_id, "status": self.status or "read"}

#  Â¢ Â¢  Auth helpers  Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ 
def get_current_user():
    token = session.get("access_token")
    if not token:
        return None
    try:
        # Decode without signature verification - token was issued by Supabase auth
        # and stored in server-side session, so we trust it implicitly
        payload = pyjwt.decode(token, options={"verify_signature": False})
        uid = payload.get("sub")
        if not uid:
            return None
        return {"id": uid, "email": payload.get("email", ""), "role": session.get("user_role", "free")}
    except Exception:
        return None

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user:
            flash("Please log in to access your library.", "info")
            return redirect(url_for("login", next=request.path))
        g.user = user
        return f(*args, **kwargs)
    return decorated

def supabase_sign_in(email, password):
    r = requests.post(
        SUPABASE_URL + "/auth/v1/token?grant_type=password",
        headers={"apikey": SUPABASE_ANON_KEY, "Content-Type": "application/json"},
        json={"email": email, "password": password}, timeout=10)
    return r.json()

def supabase_sign_up(email, password):
    r = requests.post(
        SUPABASE_URL + "/auth/v1/signup",
        headers={"apikey": SUPABASE_ANON_KEY, "Content-Type": "application/json"},
        json={"email": email, "password": password}, timeout=10)
    return r.json()

def supabase_reset_password(email, redirect_to=None):
    payload = {"email": email}
    if redirect_to:
        payload["redirect_to"] = redirect_to
    requests.post(
        SUPABASE_URL + "/auth/v1/recover",
        headers={"apikey": SUPABASE_ANON_KEY, "Content-Type": "application/json"},
        json=payload, timeout=10)

#  Â¢ Â¢  DB init  Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ 
def load_library():
    if os.path.exists(LIBRARY_FILE):
        with open(LIBRARY_FILE, "r") as f:
            return json.load(f)
    return []

def migrate_from_json():
    if Book.query.count() == 0:
        for b in load_library():
            db.session.add(Book(
                id=b.get("id", str(uuid.uuid4())),
                title=b.get("title",""), author=b.get("author",""),
                isbn=b.get("isbn",""), format=b.get("format","Paper"),
                pages=b.get("pages",""), copyright_year=b.get("copyright_year",""),
                read_date=b.get("read_date",""), rating=b.get("rating",""),
                cover_url=b.get("cover_url",""), summary=b.get("summary",""),
                read_time_hrs=b.get("read_time_hrs",""),
            ))
        db.session.commit()

def init_db():
    try:
        db.create_all()
        try:
            db.session.execute(db.text("ALTER TABLE books ALTER COLUMN cover_url TYPE TEXT"))
            db.session.commit()
        except Exception:
            db.session.rollback()
        try:
            db.session.execute(db.text("ALTER TABLE books ADD COLUMN IF NOT EXISTS user_id VARCHAR(36)"))
            db.session.commit()
        except Exception:
            db.session.rollback()
        migrate_from_json()
    except Exception as e:
        print(f"DB init error: {e}")

@app.before_request
def ensure_db():
    if not getattr(app, "_db_initialized", False):
        init_db()
        app._db_initialized = True

#  Â¢ Â¢  Auth routes  Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ Â¢ 

@app.context_processor
def inject_user():
    return dict()


@app.context_processor
def inject_trial_context():
    from flask import g
    user = getattr(g, 'user', None)
    if not user:
        return {}
    role = session.get('user_role', 'free')
    if role in ('subscriber', 'beta', 'owner'):
        return {'trial_banner': None, 'trial_days_left': None, 'stripe_pub_key': STRIPE_PUBLISHABLE_KEY, 'google_books_api_key': GOOGLE_BOOKS_API_KEY}
    trial_end = session.get('trial_end')
    if not trial_end:
        return {'trial_banner': 'expired', 'trial_days_left': 0, 'stripe_pub_key': STRIPE_PUBLISHABLE_KEY, 'google_books_api_key': GOOGLE_BOOKS_API_KEY}
    try:
        end_date = datetime.fromisoformat(trial_end)
        days_left = max(0, (end_date - datetime.utcnow()).days)
    except Exception:
        days_left = 0
    banner = 'expired' if days_left == 0 else ('urgent' if days_left <= 7 else 'info')
    return {'trial_banner': banner, 'trial_days_left': days_left, 'stripe_pub_key': STRIPE_PUBLISHABLE_KEY, 'google_books_api_key': GOOGLE_BOOKS_API_KEY}

@app.route("/login", methods=["GET", "POST"])
def login():
    if get_current_user():
        return redirect(url_for("home"))
    error = None
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        pw    = request.form.get("password", "")
        data  = supabase_sign_in(email, pw)
        if "access_token" in data:
            session["access_token"]  = data["access_token"]
            session["refresh_token"] = data.get("refresh_token", "")
            user_info = get_current_user()
            if user_info:
                session["user_role"] = get_user_role(user_info["id"])
            next_page = request.args.get("next")
            return redirect(next_page or url_for("home"))
        error = data.get("error_description") or data.get("msg") or "Invalid email or password."
    return render_template("login.html", error=error)

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if get_current_user():
        return redirect(url_for("books"))
    error = None
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        pw    = request.form.get("password", "")
        pw2   = request.form.get("password2", "")
        if not email or not pw:
            error = "Email and password are required."
        elif pw != pw2:
            error = "Passwords do not match."
        elif len(pw) < 8:
            error = "Password must be at least 8 characters."
        else:
            data = supabase_sign_up(email, pw)
            if "access_token" in data:
                session["access_token"]  = data["access_token"]
                session["refresh_token"] = data.get("refresh_token", "")
                session['trial_end'] = (datetime.utcnow() + timedelta(days=30)).isoformat()
                session['user_role'] = 'trial'
                flash("Welcome to My Reading Alcove! Your 30-day free trial has started.", "success")
                return redirect(url_for("home"))
            elif data.get("id"):
                flash("Account created! Check your email to confirm before logging in.", "info")
                return redirect(url_for("login"))
            error = data.get("error_description") or data.get("msg") or data.get("message") or "Signup failed."
    return render_template("signup.html", error=error)


@app.route("/reset-password/exchange", methods=["POST"])
def reset_password_exchange():
    data = request.get_json(silent=True, force=True) or {}
    code = data.get("code", "")
    if not code:
        return {"error": "missing code"}, 400
    r = requests.post(
        SUPABASE_URL + "/auth/v1/token?grant_type=pkce",
        headers={"apikey": SUPABASE_ANON_KEY, "Content-Type": "application/json"},
        json={"auth_code": code, "code_verifier": ""},
        timeout=10
    )
    d = r.json()
    if r.status_code == 200 and d.get("access_token"):
        return {"access_token": d["access_token"]}
    return {"error": d.get("error_description") or d.get("message") or "Exchange failed"}, 400

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    sent = False
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        supabase_reset_password(email, redirect_to="https://myreadingalcove.com/reset-password")
        sent = True
    return render_template("forgot_password.html", sent=sent)


@app.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        new_password = request.form.get("password", "").strip()
        confirm = request.form.get("password2", "").strip()
        if not email or not new_password:
            return render_template("reset_password.html", error="Email and password are required.", done=False)
        if new_password != confirm:
            return render_template("reset_password.html", error="Passwords do not match.", done=False)
        if len(new_password) < 8:
            return render_template("reset_password.html", error="Password must be at least 8 characters.", done=False)
        # Look up user by email using service role key
        lookup = requests.get(
            SUPABASE_URL + "/auth/v1/admin/users",
            headers={
                "apikey": SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": "Bearer " + SUPABASE_SERVICE_ROLE_KEY,
            },
            params={"email": email},
            timeout=10
        )
        users = lookup.json().get("users", [])
        if not users:
            return render_template("reset_password.html", error="No account found with that email address.", done=False)
        user_id = users[0]["id"]
        # Update password via Admin API
        upd = requests.put(
            SUPABASE_URL + "/auth/v1/admin/users/" + user_id,
            headers={
                "apikey": SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": "Bearer " + SUPABASE_SERVICE_ROLE_KEY,
                "Content-Type": "application/json"
            },
            json={"password": new_password},
            timeout=10
        )
        if upd.status_code == 200:
            return render_template("reset_password.html", done=True, error=None)
        else:
            err = upd.json().get("message") or "Password update failed. Please try again."
            return render_template("reset_password.html", error=err, done=False)
    return render_template("reset_password.html", done=False, error=None)




@app.route("/settings/change-password", methods=["POST"])
def change_password():
    if "access_token" not in session:
        return {"error": "Not authenticated"}, 401
    new_password = request.form.get("password", "").strip()
    confirm = request.form.get("confirm", "").strip()
    if not new_password or len(new_password) < 8:
        flash("Password must be at least 8 characters.", "error")
        return redirect(url_for("settings"))
    if new_password != confirm:
        flash("Passwords do not match.", "error")
        return redirect(url_for("settings"))
    r = requests.put(
        SUPABASE_URL + "/auth/v1/user",
        headers={
            "apikey": SUPABASE_ANON_KEY,
            "Authorization": "Bearer " + session["access_token"],
            "Content-Type": "application/json"
        },
        json={"password": new_password},
        timeout=10
    )
    if r.status_code == 200:
        flash("Password updated successfully.", "success")
    else:
        err = r.json().get("message") or r.json().get("error_description") or "Update failed."
        flash(err, "error")
    return redirect(url_for("settings"))


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))

@app.route("/")
def index():
    user = get_current_user()
    if user:
        g.user = user
        return render_template("home.html")
    return render_template("landing.html")

@app.route("/home")
@login_required
def home():
    return render_template("home.html")

@app.route("/books")
@login_required
def books():
    from datetime import datetime
    all_books = [b.to_dict() for b in Book.query.filter_by(user_id=g.user["id"]).all()]
    def parse_date(b):
        d = b.get("read_date") or ""
        if not d:
            return datetime.min
        for fmt in ("%m/%d/%y", "%Y-%m-%d", "%m/%d/%Y"):
            try:
                return datetime.strptime(d.strip(), fmt)
            except ValueError:
                continue
        return datetime.min
    reading = [b for b in all_books if (b.get("status") or "read") == "reading"]
    want    = [b for b in all_books if (b.get("status") or "read") == "want_to_read"]
    dnf     = [b for b in all_books if (b.get("status") or "read") == "dnf"]
    read    = [b for b in all_books if (b.get("status") or "read") == "read"]
    read    = sorted(read, key=parse_date, reverse=True)
    return render_template("books.html", reading=reading, want=want, dnf=dnf, books=read)



@app.route('/books/data')
@login_required
def books_data():
    """JSON endpoint for offline-capable library cache."""
    import json
    from datetime import datetime
    all_books = [b.to_dict() for b in Book.query.filter_by(user_id=g.user["id"]).all()]
    return app.response_class(
        response=json.dumps(all_books),
        status=200,
        mimetype='application/json'
    )


@app.route('/offline')
def offline_page():
    return render_template('offline.html')

@app.route('/help')
def help_page():
    return render_template('help.html')

@app.route('/terms')
def terms_page():
    return render_template('terms.html')

@app.route('/privacy')
def privacy_page():
    return render_template('privacy.html')

@app.route('/stats')
@login_required
def stats():
    from datetime import datetime, timedelta
    from collections import defaultdict

    all_books = [b.to_dict() for b in Book.query.filter_by(user_id=g.user["id"]).all()]
    read_books = [b for b in all_books if (b.get("status") or "read") == "read"]

    def parse_date(d_str):
        if not d_str:
            return None
        for fmt in ("%m/%d/%y", "%Y-%m-%d", "%m/%d/%Y"):
            try:
                return datetime.strptime(d_str.strip(), fmt)
            except ValueError:
                continue
        return None

    def parse_pages(p_str):
        try:
            return int(str(p_str).strip().replace(",", "")) if p_str else 0
        except (ValueError, TypeError):
            return 0

    now = datetime.now()

    books_by_month = defaultdict(int)
    pages_by_month = defaultdict(int)
    for b in read_books:
        dt = parse_date(b.get("read_date"))
        if dt:
            key = dt.strftime("%Y-%m")
            books_by_month[key] += 1
            pages_by_month[key] += parse_pages(b.get("pages"))

    months_12 = []
    for i in range(11, -1, -1):
        m = (now.month - i - 1) % 12 + 1
        y = now.year + ((now.month - i - 1) // 12)
        key = f"{y}-{m:02d}"
        label = datetime(y, m, 1).strftime("%b %y")
        months_12.append({"key": key, "label": label, "books": books_by_month.get(key, 0), "pages": pages_by_month.get(key, 0)})

    books_by_year = defaultdict(int)
    pages_by_year = defaultdict(int)
    for b in read_books:
        dt = parse_date(b.get("read_date"))
        if dt:
            books_by_year[dt.year] += 1
            pages_by_year[dt.year] += parse_pages(b.get("pages"))

    years = sorted(books_by_year.keys())
    years_data = [{"year": y, "books": books_by_year[y], "pages": pages_by_year[y]} for y in years]

    pages_by_week = defaultdict(int)
    for b in read_books:
        dt = parse_date(b.get("read_date"))
        if dt and (now - dt).days <= 364:
            week_start = (dt - timedelta(days=dt.weekday())).strftime("%Y-%m-%d")
            pages_by_week[week_start] += parse_pages(b.get("pages"))

    total_books = len(read_books)
    books_with_pages = [b for b in read_books if parse_pages(b.get("pages")) > 0]
    total_pages = sum(parse_pages(b.get("pages")) for b in books_with_pages)
    books_with_dates = [b for b in read_books if parse_date(b.get("read_date"))]
    missing_pages = total_books - len(books_with_pages)
    missing_dates = total_books - len(books_with_dates)

    books_this_year  = books_by_year.get(now.year, 0)
    this_month_key   = now.strftime("%Y-%m")
    books_this_month = books_by_month.get(this_month_key, 0)
    pages_this_year  = pages_by_year.get(now.year, 0)
    pages_this_month = pages_by_month.get(this_month_key, 0)

    weeks_with_pages = [v for v in pages_by_week.values() if v > 0]
    avg_pages_per_week = int(sum(weeks_with_pages) / len(weeks_with_pages)) if weeks_with_pages else 0

    return render_template("stats.html",
        total_books=total_books,
        total_pages=total_pages,
        books_this_year=books_this_year,
        books_this_month=books_this_month,
        pages_this_year=pages_this_year,
        pages_this_month=pages_this_month,
        avg_pages_per_week=avg_pages_per_week,
        months_12=months_12,
        years_data=years_data,
        missing_pages=missing_pages,
        missing_dates=missing_dates,
    )

 
#  Â¢ Â¢  ADD BOOK (page)  Â¢ Â¢ 
@app.route("/add")
@login_required
def add_choice():
    return render_template("add_choice.html")
 
#  Â¢ Â¢  ADD: SCANNER  Â¢ Â¢ 
@app.route("/add/scan")
@login_required
def add_scan():
    return render_template("scan.html")
 
#  Â¢ Â¢  ADD: MANUAL FORM  Â¢ Â¢ 
@app.route("/add/manual")
@login_required
def add_manual():
    return render_template("add.html", isbn_prefill=request.args.get("isbn", ""))
 
#  Â¢ Â¢  ADD: SAVE  Â¢ Â¢ 
@app.route("/add/manual/save", methods=["POST"])
@login_required
def add_manual_save():
    title = request.form.get("title", "").strip()
    author = request.form.get("author", "").strip()
    if not title or not author:
        flash("Title and author are required.", "error")
        return redirect(url_for("add_manual"))
    db.session.add(Book(
        title          = title,
        author         = author,
        user_id        = g.user["id"],
        isbn           = request.form.get("isbn", "").strip(),
        copyright_year = request.form.get("copyright_year", "").strip(),
        pages          = request.form.get("pages", "").strip() or None,
        read_date      = request.form.get("read_date") or None,
        format         = request.form.get("format", "Paper"),
        read_time_hrs  = request.form.get("read_time_hrs") or None,
        summary        = request.form.get("plot_summary", "").strip(),
        cover_url      = request.form.get("cover_url", "").strip(),
        rating         = request.form.get("rating") or None,
        status         = request.form.get("status", "read").strip() or "read",
        date_added     = datetime.utcnow(),
    ))
    db.session.commit()
    return redirect(url_for("books"))
 
#  Â¢ Â¢  AUTHORS  Â¢ Â¢ 
@app.route("/authors")
@login_required
def authors():
    library = [b.to_dict() for b in Book.query.filter_by(user_id=g.user["id"]).all()]
    author_map = {}
    for book in library:
        a = (book["author"] or "").strip()
        a = " ".join(w.capitalize() for w in re.split(r"\s+", a.strip())) if a else ""
        author_map.setdefault(a, []).append(book)
    authors_sorted = sorted(author_map.items(), key=lambda x: x[0].strip().split()[-1].lower() if x[0].strip() else "")
    return render_template("authors.html", authors=authors_sorted)



# âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
# AUTHOR SHELF  /author/<name>  â client-side Google Books fetch
# âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
@app.route("/author/<path:author_name>")
@login_required
def author_shelf(author_name):
    # Pass library books + API key to template.
    # Google Books fetch happens client-side so the HTTP-referrer-restricted
    # API key is sent with the correct Referer header from the browser.
    library_books = Book.query.filter(
        Book.user_id == g.user["id"],
        func.lower(func.trim(Book.author)) == author_name.strip().lower()
    ).all()
    return render_template(
        "author_shelf.html",
        author_name=author_name,
        library_books=[b.to_dict() for b in library_books],
        google_api_key=GOOGLE_BOOKS_API_KEY,
        current_user=g.user,
    )


@app.route("/add_want_to_read", methods=["POST"])
@login_required
def add_want_to_read():
    data = request.get_json()
    if not data or not data.get("title"):
        return jsonify({"success": False, "error": "Missing title"}), 400

    user_id = g.user["id"]
    title   = data.get("title", "").strip()
    isbn    = data.get("isbn", "").strip() or None
    cover   = data.get("coverUrl", "").strip() or None
    year    = str(data.get("year", "") or "").strip() or None
    author  = data.get("author", "").strip() or None

    # Duplicate check
    existing = Book.query.filter_by(user_id=user_id, title=title).first()
    if existing:
        return jsonify({"success": False, "error": "Already in your library"})

    new_book = Book(
        id=str(uuid.uuid4()),
        user_id=user_id,
        title=title,
        author=author or "",
        isbn=isbn,
        cover_url=cover,
        copyright_year=str(year) if year else None,
        status="want_to_read",
        format="",
        pages=None,
        read_date=None,
        rating=None,
        summary=None,
        read_time_hrs=None,
        date_added=datetime.utcnow(),
    )
    db.session.add(new_book)
    db.session.commit()
    return jsonify({"success": True, "id": new_book.id})

 
#  Â¢ Â¢  UTILITIES  Â¢ Â¢ 
@app.route("/utilities")
@login_required
def utilities():
    current_user = get_current_user()
    return render_template("utilities.html", current_user=current_user)
 

@app.route("/utilities/tools")
@login_required
def tools():
    current_user = get_current_user()
    return render_template("tools.html", current_user=current_user)

@app.route("/utilities/export")
@login_required
def export_csv():
    books = Book.query.filter_by(user_id=g.user["id"]).all()
    fields = ["id","title","author","isbn","format","pages","copyright_year","read_date","rating","cover_url","summary","read_time_hrs","status"]
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    for book in books:
        row = book.to_dict()
        if row.get('isbn'):
            row['isbn'] = '\t' + str(row['isbn'])
        writer.writerow(row)
    csv_bytes = output.getvalue().encode("utf-8")
    response = make_response(csv_bytes)
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    response.headers["Content-Disposition"] = "attachment; filename=my_reading_alcove.csv"
    return response
 
@app.route("/utilities/import", methods=["POST"])
@login_required
def import_csv():
    if not is_subscriber():
        flash("CSV import is available on the subscriber plan. Upgrade to unlock bulk import.", "upgrade")
        return redirect(url_for("utilities"))
    file = request.files.get("file")
    if not file or not file.filename.endswith(".csv"):
        flash("Please upload a valid .csv file.", "error")
        return redirect(url_for("utilities"))
    try:
        raw = file.stream.read()
        try:
            content = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            content = raw.decode("latin-1")
        content = content.replace('\r\n', '\n').replace('\r', '\n')
        stream = io.StringIO(content)
        reader = csv.DictReader(stream)
        rows = list(reader)
        if not rows:
            flash("CSV file appears to be empty.", "error")
            return redirect(url_for("utilities"))

        # Detect Goodreads format by checking for Goodreads-specific columns
        headers = set(rows[0].keys())
        is_goodreads = "Exclusive Shelf" in headers or "Book Id" in headers

        def clean_isbn(val):
            # Goodreads wraps ISBNs like ="9780385333849"
            if not val:
                return ""
            return val.strip().strip('="').strip()

        def map_status(shelf):
            if shelf == "currently-reading":
                return "reading"
            elif shelf == "to-read":
                return "want_to_read"
            else:
                return "read"

        def clean_date(val):
            # Goodreads: "2023/04/15" -> "2023-04-15"
            if not val:
                return ""
            return val.strip().replace("/", "-")

        def get_field(row, *keys):
            for k in keys:
                v = row.get(k, "")
                if v:
                    return v.strip()
            return ""

        added = 0
        skipped = 0
        for row in rows:
            if is_goodreads:
                title  = get_field(row, "Title")
                author = get_field(row, "Author")
                isbn   = clean_isbn(get_field(row, "ISBN13", "ISBN"))
                pages  = get_field(row, "Number of Pages")
                year   = get_field(row, "Original Publication Year", "Year Published")
                date   = clean_date(get_field(row, "Date Read"))
                rating = get_field(row, "My Rating")
                if rating == "0":
                    rating = ""
                summary = get_field(row, "My Review")
                shelf   = get_field(row, "Exclusive Shelf")
                status  = map_status(shelf)
                fmt     = "Paper"
                cover   = ""
                read_time = ""
            else:
                title  = get_field(row, "title")
                author = get_field(row, "author")
                isbn   = get_field(row, "isbn")
                pages  = get_field(row, "pages")
                year   = get_field(row, "copyright_year")
                date   = get_field(row, "read_date")
                rating = get_field(row, "rating")
                summary = get_field(row, "summary")
                fmt    = get_field(row, "format") or "Paper"
                cover  = get_field(row, "cover_url")
                read_time = get_field(row, "read_time_hrs")
                status = get_field(row, "status") or "read"

            if not title or not author:
                skipped += 1
                continue

            existing = Book.query.filter_by(title=title, author=author, user_id=g.user["id"]).first()
            if existing:
                skipped += 1
                continue

            db.session.add(Book(
                id            = str(uuid.uuid4()),
                user_id       = g.user["id"],
                title         = title,
                author        = author,
                isbn          = isbn,
                format        = fmt,
                pages         = pages,
                copyright_year= year,
                read_date     = date or None,
                rating        = rating or None,
                cover_url     = cover,
                summary       = summary,
                read_time_hrs = read_time or None,
                status        = status,
                date_added    = datetime.utcnow(),
            ))
            added += 1

        db.session.commit()
        source = "Goodreads library" if is_goodreads else "CSV"
        flash(f"Import complete: {added} book(s) added from your {source}, {skipped} skipped (duplicates or missing title/author).", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Import failed: {str(e)}", "error")
    return redirect(url_for("utilities"))
@app.route("/utilities/wipe", methods=["POST"])
@login_required
def wipe_library():
    try:
        uid = str(g.user["id"]).strip()
        num_deleted = Book.query.filter(Book.user_id == uid).delete(synchronize_session=False)
        db.session.commit()
        wiped_flag = os.path.join(os.path.dirname(__file__), ".library_wiped")
        open(wiped_flag, "w").close()
        json_path = os.path.join(os.path.dirname(__file__), "library.json")
        if os.path.exists(json_path):
            with open(json_path, "w") as f:
                json.dump([], f)
        flash(f"Library wiped. {num_deleted} book(s) deleted. You're starting fresh!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Wipe failed: {str(e)}", "error")
    return redirect(url_for("utilities"))
 
@app.route("/settings")
@login_required
def settings():
    return render_template("settings.html")
 
@app.route("/settings/backup")
@login_required
def settings_backup():
    from datetime import date
    user = get_current_user()
    books = [b.to_dict() for b in Book.query.filter_by(user_id=user["id"]).all()]
    payload = json.dumps({"version": 1, "exported": str(date.today()), "books": books}, indent=2)
    return send_file(
        io.BytesIO(payload.encode("utf-8")),
        mimetype="application/json",
        as_attachment=True,
        download_name=f"reading-alcove-backup-{date.today()}.json"
    )
 
@app.route("/settings/restore", methods=["POST"])
@login_required
def settings_restore():
    from flask import flash
    file = request.files.get("file")
    mode = request.form.get("mode", "merge")
    if not file or not file.filename.endswith(".json"):
        flash("Please upload a valid .json backup file.", "error")
        return redirect(url_for("settings"))
    try:
        data = json.loads(file.stream.read().decode("utf-8"))
        books_data = data if isinstance(data, list) else data.get("books", [])
        if not isinstance(books_data, list):
            raise ValueError("Invalid backup format")
        if mode == "overwrite":
            Book.query.delete()
            db.session.flush()
        added = 0
        skipped = 0
        for b in books_data:
            book_id = b.get("id", "").strip()
            if mode == "merge":
                if book_id and db.session.get(Book, book_id):
                    skipped += 1
                    continue
                if Book.query.filter_by(title=b.get("title", "").strip(), author=b.get("author", "").strip()).first():
                    skipped += 1
                    continue
            book = Book(
                id=book_id or str(uuid.uuid4()),
                user_id=g.user["id"],
                title=b.get("title", "").strip(),
                author=b.get("author", "").strip(),
                isbn=b.get("isbn", "").strip(),
                format=b.get("format", "Paper"),
                pages=b.get("pages", "").strip(),
                copyright_year=b.get("copyright_year", "").strip(),
                read_date=b.get("read_date", "").strip(),
                rating=b.get("rating", "").strip(),
                cover_url=b.get("cover_url", "").strip(),
                summary=b.get("summary", "").strip(),
                read_time_hrs=b.get("read_time_hrs", "").strip()
            )
            db.session.add(book)
            added += 1
        db.session.commit()
        action = "Overwrite" if mode == "overwrite" else "Merge"
        flash(f"{action} complete: {added} book(s) restored, {skipped} skipped.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Restore failed: {str(e)}", "error")
    return redirect(url_for("settings"))
 
 
@app.route("/utilities/enrich", methods=["POST"])
def enrich_csv():
    file = request.files.get("file")
    if not file or not file.filename.endswith(".csv"):
        flash("Please upload a valid .csv file with 'title' and 'author' columns.", "error")
        return redirect(url_for("utilities"))
    api_key = request.form.get("api_key", "").strip() or GOOGLE_BOOKS_API_KEY
    try:
        import re
        raw = file.stream.read()
        try:
            content = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            content = raw.decode("latin-1")
        content = content.replace('\r\n', '\n').replace('\r', '\n')
        stream = io.StringIO(content)
        reader = csv.DictReader(stream)
        fieldnames_lower = [f.lower().strip() for f in (reader.fieldnames or [])]
        if "title" not in fieldnames_lower or "author" not in fieldnames_lower:
            flash("CSV must contain 'title' and 'author' columns.", "error")
            return redirect(url_for("utilities"))
        output_fields = ["title","author","isbn","publisher","published_year","pages","genre","summary","cover_url","google_books_id"]
        results = []
        for row in reader:
            row_lower = {k.lower().strip(): v for k, v in row.items()}
            title  = row_lower.get("title", "").strip()
            author = row_lower.get("author", "").strip()
            if not title:
                continue
            enriched = {"title": title, "author": author, "isbn": "", "publisher": "", "published_year": "", "pages": "", "genre": "", "summary": "", "cover_url": "", "google_books_id": ""}
            try:
                query = f"intitle:{title}"
                if author:
                    query += f"+inauthor:{author}"
                resp = requests.get("https://www.googleapis.com/books/v1/volumes", params={"q": query, "maxResults": 1, "langRestrict": "en", "key": api_key}, timeout=8)
                resp.raise_for_status()
                items = resp.json().get("items", [])
                if items:
                    item = items[0]
                    vol  = item.get("volumeInfo", {})
                    isbns = vol.get("industryIdentifiers", [])
                    isbn13 = next((x["identifier"] for x in isbns if x["type"] == "ISBN_13"), "")
                    isbn10 = next((x["identifier"] for x in isbns if x["type"] == "ISBN_10"), "")
                    pub_date = vol.get("publishedDate", "")
                    pub_year = pub_date[:4] if pub_date else ""
                    image_links = vol.get("imageLinks", {})
                    cover = image_links.get("thumbnail", "") or image_links.get("smallThumbnail", "")
                    cover = cover.replace("http://", "https://").replace("&zoom=1", "&zoom=2")
                    raw_desc = vol.get("description", "")
                    clean_desc = re.sub(r"<[^>]+>", "", raw_desc)
                    enriched.update({"title": vol.get("title", title), "author": ", ".join(vol.get("authors", [author])), "isbn": isbn13 or isbn10, "publisher": vol.get("publisher", ""), "published_year": pub_year, "pages": str(vol.get("pageCount", "")), "genre": ", ".join(vol.get("categories", [])), "summary": clean_desc[:800], "cover_url": cover, "google_books_id": item.get("id", "")})
            except Exception as e:
                enriched["summary"] = f"LOOKUP_ERROR: {str(e)}"
            results.append(enriched)
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=output_fields)
        writer.writeheader()
        writer.writerows(results)
        output.seek(0)
        return send_file(io.BytesIO(output.getvalue().encode("utf-8")), mimetype="text/csv", as_attachment=True, download_name="enriched_books.csv")
    except Exception as e:
        flash(f"Enrichment failed: {str(e)}", "error")
        return redirect(url_for("utilities"))
 
 
#  Â¢ Â¢  BOOK DETAIL  Â¢ Â¢ 
@app.route("/utilities/test-google-books")
def test_google_books():
    import requests as req
    api_key = GOOGLE_BOOKS_API_KEY
    try:
        resp = req.get("https://www.googleapis.com/books/v1/volumes",
                       params={"q": "intitle:Dune+inauthor:Herbert", "maxResults": 1, "key": api_key},
                       timeout=8)
        data = resp.json()
        items = data.get("items", [])
        if items:
            vol = items[0].get("volumeInfo", {})
            return jsonify({"status": "ok", "title": vol.get("title"), "author": vol.get("authors"),
                            "api_key_used": bool(api_key), "http_status": resp.status_code})
        else:
            return jsonify({"status": "no_results", "raw": data,
                            "api_key_used": bool(api_key), "http_status": resp.status_code})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e), "api_key_used": bool(api_key)})
 
 
@app.route("/book/<book_id>")
@login_required
def book_detail(book_id):
    book = db.session.get(Book, book_id)
    if not book: abort(404)
    return render_template("detail.html", book=book.to_dict())
 
#  Â¢ Â¢  BOOK EDIT  Â¢ Â¢ 
@app.route("/book/<book_id>/edit", methods=["GET", "POST"])
def book_edit(book_id):
    book = db.session.get(Book, book_id)
    if not book: abort(404)
    save_error = None
    if request.method == "POST":
        try:
            book.title = request.form.get("title", "").strip()
            book.author = request.form.get("author", "").strip()
            book.isbn = request.form.get("isbn", "").strip()
            book.format = request.form.get("format", "Paper")
            book.pages = request.form.get("pages", "").strip() or None
            book.copyright_year = request.form.get("copyright_year", "").strip()
            book.read_date = request.form.get("read_date") or None
            book.rating = request.form.get("rating") or None
            book.cover_url = request.form.get("cover_url", "").strip()
            book.summary = request.form.get("summary", "").strip()
            book.read_time_hrs = request.form.get("read_time_hrs") or None
            book.status = request.form.get("status", "read").strip() or "read"
            db.session.commit()
            return redirect(url_for("book_detail", book_id=book_id))
        except Exception as e:
            db.session.rollback()
            save_error = f"{type(e).__name__}: {e}"
            app.logger.error(f"book_edit save error: {save_error}")
    from datetime import date
    return render_template("edit.html", book=book.to_dict(), today=str(date.today()), save_error=save_error)
 
#  Â¢ Â¢  BOOK DELETE  Â¢ Â¢ 
@app.route("/book/<book_id>/delete", methods=["POST"])
def book_delete(book_id):
    book = db.session.get(Book, book_id)
    if not book: abort(404)
    db.session.delete(book)
    db.session.commit()
    return redirect(url_for("books"))
 
#  Â¢ Â¢  API SEARCH (Open Library)  Â¢ Â¢ 
@app.route("/api/search")
@login_required
def api_search():
    import requests as req_lib
    q = request.args.get("q", "")
    field = request.args.get("field", "q")
    try:
        r = req_lib.get("https://openlibrary.org/search.json",
            params={field: q, "limit": 8, "fields": "key,title,author_name,isbn,first_publish_year,number_of_pages_median,cover_i"},
            timeout=8)
        results = []
        for d in r.json().get("docs", [])[:6]:
            cover = f"https://covers.openlibrary.org/b/id/{d['cover_i']}-M.jpg" if d.get("cover_i") else ""
            results.append({"title": d.get("title",""), "author": (d.get("author_name") or [""])[0],
                "isbn": next((i for i in (d.get("isbn") or []) if len(i) == 13 and i.isdigit()), ((d.get("isbn") or [""])[0] if d.get("isbn") else "")), "pages": str(d.get("number_of_pages_median","") or ""),
                "copyright_year": str(d.get("first_publish_year","") or ""), "cover_url": cover, "work_key": d.get("key","")})
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
 
#  Â¢ Â¢  API SUMMARY  Â¢ Â¢ 
@app.route("/api/summary")
@login_required
def api_summary():
    import requests as req_lib
    key = request.args.get("key", "")
    try:
        r = req_lib.get(f"https://openlibrary.org{key}.json", timeout=8)
        desc = r.json().get("description", "")
        if isinstance(desc, dict): desc = desc.get("value", "")
        return jsonify({"summary": desc[:800]})
    except Exception:
        return jsonify({"summary": ""})
 
@app.route('/sw.js')
def service_worker():
    from flask import send_from_directory
    response = send_from_directory('static', 'sw.js', mimetype='application/javascript')
    response.headers['Service-Worker-Allowed'] = '/'
    return response


@app.route("/utilities/backfill-isbn-data")
@login_required
def backfill_isbn_data():
    """Return books missing ISBN-13 so the client can look them up."""
    user = get_current_user()
    books = Book.query.filter_by(user_id=user["id"]).all()
    needs_update = []
    for b in books:
        isbn = (b.isbn or "").strip()
        if not isbn or not (len(isbn) == 13 and isbn.isdigit()):
            needs_update.append({"id": b.id, "title": b.title, "author": b.author, "isbn": isbn})
    return jsonify(needs_update)

@app.route("/utilities/backfill-isbn-save", methods=["POST"])
@login_required
def backfill_isbn_save():
    """Accept a list of {id, isbn} pairs and update the database."""
    data = request.get_json()
    if not data or not isinstance(data, list):
        return jsonify({"error": "Invalid data"}), 400
    updated = 0
    for item in data:
        book_id = str(item.get("id", "")).strip()
        try:
            book_id_int = int(book_id)
        except (ValueError, TypeError):
            continue
        new_isbn = item.get("isbn", "").strip()
        if not book_id or not new_isbn:
            continue
        book = db.session.get(Book, book_id)
        if book:
            book.isbn = new_isbn
            updated += 1
    db.session.commit()
    return jsonify({"updated": updated})


@app.route("/utilities/isbn-lookup")
@login_required
def isbn_lookup():
    """Server-side Google Books ISBN-13 lookup using the stored API key."""
    title = request.args.get("title", "").strip()
    author = request.args.get("author", "").strip()
    if not title:
        return jsonify({"isbn13": "", "error": "no title"})
    api_key = GOOGLE_BOOKS_API_KEY
    try:
        query = f"intitle:{title}"
        if author:
            query += f"+inauthor:{author}"
        resp = requests.get(
            "https://www.googleapis.com/books/v1/volumes",
            params={"q": query, "maxResults": 3, "langRestrict": "en", "key": api_key},
            timeout=8
        )
        resp.raise_for_status()
        for item in resp.json().get("items", []):
            isbns = item.get("volumeInfo", {}).get("industryIdentifiers", [])
            isbn13 = next((x["identifier"] for x in isbns if x["type"] == "ISBN_13"), "")
            if isbn13:
                return jsonify({"isbn13": isbn13, "source": "google_books"})
        return jsonify({"isbn13": ""})
    except Exception as e:
        return jsonify({"isbn13": "", "error": str(e)})


@app.route("/utilities/backfill-covers-data")
@login_required
def backfill_covers_data():
    """Return books missing a cover URL."""
    user = get_current_user()
    books = Book.query.filter_by(user_id=user["id"]).all()
    needs_cover = []
    for b in books:
        if not (b.cover_url or "").strip():
            needs_cover.append({"id": b.id, "title": b.title, "author": b.author, "isbn": b.isbn or ""})
    return jsonify(needs_cover)

@app.route("/utilities/backfill-covers-save", methods=["POST"])
@login_required
def backfill_covers_save():
    """Accept a list of {id, cover_url} pairs and update the database."""
    data = request.get_json()
    if not data or not isinstance(data, list):
        return jsonify({"error": "Invalid data"}), 400
    updated = 0
    for item in data:
        book_id = item.get("id", "").strip()
        cover_url = item.get("cover_url", "").strip()
        if not book_id or not cover_url:
            continue
        book = db.session.get(Book, book_id)
        if book:
            book.cover_url = cover_url
            updated += 1
    db.session.commit()
    return jsonify({"updated": updated})

@app.route("/utilities/missing-pages")
@login_required
def missing_pages():
    """Return list of books with missing or zero page counts."""
    user = get_current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    books = Book.query.filter_by(user_id=user["id"]).all()
    missing = []
    for b in books:
        pages = (b.pages or "").strip()
        if not pages or pages == "0":
            missing.append({"id": b.id, "title": b.title, "author": b.author})
    missing.sort(key=lambda x: x.get("title", "").lower())
    return jsonify({"books": missing})


@app.route("/utilities/missing-pages-save", methods=["POST"])
@login_required
def missing_pages_save():
    """Accept a list of {id, pages} pairs and update the database."""
    user = get_current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json()
    if not data or not isinstance(data, list):
        return jsonify({"error": "Invalid data"}), 400
    updated = 0
    for item in data:
        book_id = item.get("id", "").strip()
        pages = str(item.get("pages", "")).strip()
        if not book_id or not pages:
            continue
        book = db.session.get(Book, book_id)
        if book and str(book.user_id) == str(user["id"]):
            book.pages = pages
            updated += 1
    db.session.commit()
    return jsonify({"updated": updated})


@app.route("/utilities/missing-dates")
@login_required
def missing_dates():
    """Return list of books with missing or empty read dates."""
    user = get_current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    books = Book.query.filter_by(user_id=user["id"]).all()
    missing = []
    for b in books:
        read_date = (b.read_date or "").strip()
        if not read_date:
            date_added = b.date_added.strftime("%m/%d/%Y") if b.date_added else None
            missing.append({"id": b.id, "title": b.title, "author": b.author, "date_added": date_added})
    missing.sort(key=lambda x: x.get("title", "").lower())
    return jsonify({"books": missing})

@app.route("/utilities/missing-summaries")
@login_required
def missing_summaries():
    """Return list of books with missing or empty summaries."""
    user = get_current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    books = Book.query.filter_by(user_id=user["id"]).all()
    missing = []
    for b in books:
        if not b.summary or not b.summary.strip():
            missing.append({"id": b.id, "title": b.title, "author": b.author, "isbn": b.isbn or ""})
    missing.sort(key=lambda x: x.get("title", "").lower())
    return jsonify({"books": missing})

@app.route("/utilities/missing-summaries-save", methods=["POST"])
@login_required
def missing_summaries_save():
    """Accept {id, summary} pairs from client and save to DB."""
    user = get_current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json()
    if not data or not isinstance(data, list):
        return jsonify({"error": "Invalid data"}), 400
    updated = 0
    for item in data:
        book_id = str(item.get("id", "")).strip()
        summary = str(item.get("summary", "")).strip()
        if not book_id or not summary:
            continue
        try:
            book_id_int = int(book_id)
        except (ValueError, TypeError):
            continue
            book = Book.query.filter_by(id=book_id_int, user_id=user["id"]).first()
            if book:
            book.summary = summary
            updated += 1
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"DB commit failed: {str(e)}"}), 500
    return jsonify({"updated": updated})
@app.route("/utilities/cover-lookup")
def cover_lookup():
    """Server-side Google Books cover lookup  Â¢  tries ISBN first, then title+author."""
    title = request.args.get("title", "").strip()
    author = request.args.get("author", "").strip()
    isbn = request.args.get("isbn", "").strip()
    api_key = GOOGLE_BOOKS_API_KEY
    queries = []
    if isbn:
        queries.append(f"isbn:{isbn}")
    if title:
        queries.append(f"intitle:{title}" + (f"+inauthor:{author}" if author else ""))
    if not queries:
        return jsonify({"cover_url": ""})
    try:
        for query in queries:
            resp = requests.get(
                "https://www.googleapis.com/books/v1/volumes",
                params={"q": query, "maxResults": 3, "langRestrict": "en", "key": api_key},
                timeout=8
            )
            resp.raise_for_status()
            for item in resp.json().get("items", []):
                links = item.get("volumeInfo", {}).get("imageLinks", {})
                cover = links.get("thumbnail", "") or links.get("smallThumbnail", "")
                if cover:
                    cover = cover.replace("http://", "https://").replace("&zoom=1", "&zoom=2")
                    return jsonify({"cover_url": cover})
        return jsonify({"cover_url": ""})
    except Exception as e:
        return jsonify({"cover_url": "", "error": str(e)})


@app.route("/utilities/all-books-covers")
@login_required
def all_books_covers():
    """Return books with their cover_url so the client can test which are broken."""
    user = get_current_user()
    books = Book.query.filter_by(user_id=user["id"]).all()
    return jsonify([{
        "id": b.id, "title": b.title, "author": b.author,
        "isbn": b.isbn or "", "cover_url": b.cover_url or ""
    } for b in books])

@app.route("/utilities/remove-duplicates", methods=["POST"])
@login_required
def remove_duplicates():
    """Find duplicate books by normalized title+author, keep most complete, delete the rest."""
    import re
    def normalize_title(t):
        t = re.sub(r'\s*[:(].*', '', t)
        t = re.sub(r'^(the|a|an)\s+', '', t.strip().lower())
        return t.strip()

    user = get_current_user()
    books = Book.query.filter_by(user_id=user["id"]).all()
    groups = {}
    for book in books:
        key = (normalize_title(book.title), book.author.strip().lower())
        groups.setdefault(key, []).append(book)

    deleted = 0
    for key, group in groups.items():
        if len(group) < 2:
            continue
        def score(b):
            return sum([
                bool(b.cover_url), bool(b.isbn), bool(b.summary),
                bool(b.read_date), bool(b.rating), bool(b.pages),
            ]) * 100 - len(b.title)
        group.sort(key=score, reverse=True)
        keeper = group[0]
        for dup in group[1:]:
            if not keeper.cover_url and dup.cover_url:
                keeper.cover_url = dup.cover_url
            if not keeper.isbn and dup.isbn:
                keeper.isbn = dup.isbn
            if not keeper.summary and dup.summary:
                keeper.summary = dup.summary
            if not keeper.read_date and dup.read_date:
                keeper.read_date = dup.read_date
            if not keeper.rating and dup.rating:
                keeper.rating = dup.rating
            if not keeper.pages and dup.pages:
                keeper.pages = dup.pages
            db.session.delete(dup)
            deleted += 1
    db.session.commit()
    return jsonify({"deleted": deleted})

@app.route("/utilities/backup-json")
@login_required
def backup_json():
    books = Book.query.filter_by(user_id=g.user["id"]).all()
    data = [b.to_dict() for b in books]
    output = io.BytesIO(json.dumps(data, indent=2).encode("utf-8"))
    return send_file(output, mimetype="application/json",
                     as_attachment=True, download_name="reading_alcove_backup.json")

@app.route("/utilities/restore-json", methods=["POST"])
@login_required
def restore_json():
    file = request.files.get("file")
    if not file or not file.filename.endswith(".json"):
        flash("Please upload a .json backup file.", "error")
        return redirect(url_for("utilities"))
    try:
        data = json.loads(file.read().decode("utf-8"))
    except Exception:
        flash("Invalid JSON file.", "error")
        return redirect(url_for("utilities"))
    if not isinstance(data, list):
        flash("Invalid backup format.", "error")
        return redirect(url_for("utilities"))
    added = 0
    skipped = 0
    user_id = g.user["id"]
    existing_titles = {(b.title.lower().strip(), b.author.lower().strip())
                       for b in Book.query.filter_by(user_id=user_id).all()}
    for item in data:
        title = (item.get("title") or "").strip()
        author = (item.get("author") or "").strip()
        if not title:
            skipped += 1
            continue
        if (title.lower(), author.lower()) in existing_titles:
            skipped += 1
            continue
        book = Book(
            id=str(uuid.uuid4()),
            title=title,
            author=author,
            isbn=item.get("isbn") or "",
            format=item.get("format") or "",
            pages=item.get("pages") or "",
            copyright_year=item.get("copyright_year") or "",
            read_date=item.get("read_date") or "",
            rating=item.get("rating") or "",
            cover_url=item.get("cover_url") or "",
            summary=item.get("summary") or "",
            read_time_hrs=item.get("read_time_hrs") or "",
            user_id=user_id
        )
        db.session.add(book)
        existing_titles.add((title.lower(), author.lower()))
        added += 1
    db.session.commit()
    flash(f"Restore complete: {added} book(s) added, {skipped} skipped (duplicates or empty).", "success")
    return redirect(url_for("utilities"))


    app.run(debug=True)

@app.route('/subscribe/checkout')
@login_required
def subscribe_checkout():
    user = g.user
    try:
        cs = stripe.checkout.Session.create(
            payment_method_types=['card'], mode='subscription',
            customer_email=user.get('email', ''),
            line_items=[{'price': STRIPE_PRICE_ID, 'quantity': 1}],
            success_url=url_for('subscribe_success', _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=url_for('subscribe_cancel', _external=True),
            metadata={'user_id': user.get('id', '')},
        )
        return redirect(cs.url, code=303)
    except Exception:
        flash('Unable to start checkout. Please try again.', 'error')
        return redirect(url_for('home'))

@app.route('/subscribe/success')
@login_required
def subscribe_success():
    try:
        cs = stripe.checkout.Session.retrieve(request.args.get('session_id'))
        if cs.payment_status == 'paid' or cs.status == 'complete':
            session['user_role'] = 'subscriber'
            flash('Your subscription is active. Welcome!', 'success')
    except Exception:
        pass
    return redirect(url_for('books'))

@app.route('/subscribe/cancel')
@login_required
def subscribe_cancel():
    flash('Checkout cancelled. Your trial is still active.', 'info')
    return redirect(url_for('home'))

@app.route('/subscribe/portal')
@login_required
def subscribe_portal():
    try:
        customers = stripe.Customer.list(email=g.user.get('email'), limit=1)
        if customers.data:
            portal = stripe.billing_portal.Session.create(
                customer=customers.data[0].id,
                return_url=url_for('home', _external=True))
            return redirect(portal.url, code=303)
    except Exception:
        pass
    flash('Could not find your billing account.', 'error')
    return redirect(url_for('home'))

@app.route('/stripe/webhook', methods=['POST'])
def stripe_webhook():
    payload = request.get_data()
    sig = request.headers.get('Stripe-Signature', '')
    try:
        event = stripe.Webhook.construct_event(payload, sig, STRIPE_WEBHOOK_SECRET)
    except (ValueError, stripe.error.SignatureVerificationError):
        return jsonify({'error': 'Invalid signature'}), 400
    etype = event['type']
    cid = event['data']['object'].get('customer')
    if etype == 'checkout.session.completed':
        uid = event['data']['object'].get('metadata', {}).get('user_id')
        if uid and cid:
            _stripe_patch(cid, {'role': 'subscriber'}, uid)
    elif etype in ('customer.subscription.deleted', 'customer.subscription.paused'):
        _stripe_patch(cid, {'role': 'free'})
    elif etype == 'customer.subscription.resumed':
        _stripe_patch(cid, {'role': 'subscriber'})
    return jsonify({'status': 'ok'}), 200

def _stripe_patch(customer_id, data, user_id=None):
    url = os.environ.get('SUPABASE_URL', '')
    key = os.environ.get('SUPABASE_ANON_KEY', '')
    hdrs = {'apikey': key, 'Authorization': f'Bearer {key}',
            'Content-Type': 'application/json', 'Prefer': 'return=minimal'}
    params = {'user_id': f'eq.{user_id}'} if user_id else {'stripe_customer_id': f'eq.{customer_id}'}
    try:
        requests.patch(f"{url}/rest/v1/profiles", headers=hdrs, params=params, json=data)
    except Exception:
        pass

