from flask import Flask, render_template, request, redirect, url_for
import json
import os
import uuid
import requests
import csv
import time
import io
from datetime import date
from flask_sqlalchemy import SQLAlchemy
app = Flask(__name__)
app.jinja_env.filters['enumerate'] = enumerate
LIBRARY_FILE = "library.json"
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///library.db")
if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

def load_library():
    if os.path.exists(LIBRARY_FILE):
        with open(LIBRARY_FILE, "r") as f:
            return json.load(f)
    return []

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
GOOGLE_BOOKS_API_KEY = os.environ.get("GOOGLE_BOOKS_API_KEY", "")

db = SQLAlchemy(app)

class Book(db.Model):
    __tablename__ = "books"
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(500), nullable=False)
    author = db.Column(db.String(500), nullable=False)
    isbn = db.Column(db.String(20), default="")
    format = db.Column(db.String(20), default="Paper")
    pages = db.Column(db.String(10), default="")
    copyright_year = db.Column(db.String(10), default="")
    read_date = db.Column(db.String(10), default="")
    rating = db.Column(db.String(5), default="")
    cover_url = db.Column(db.String(500), default="")
    summary = db.Column(db.Text, default="")
    read_time_hrs = db.Column(db.String(10), default="")

    def to_dict(self):
        return {"id": self.id, "title": self.title, "author": self.author, "isbn": self.isbn,
                "format": self.format, "pages": self.pages, "copyright_year": self.copyright_year,
                "read_date": self.read_date, "rating": self.rating, "cover_url": self.cover_url,
                "summary": self.summary, "read_time_hrs": self.read_time_hrs}

def migrate_from_json():
    import json
    json_path = os.path.join(os.path.dirname(__file__), "library.json")
    if not os.path.exists(json_path):
        return
    if Book.query.count() > 0:
        return
    try:
        with open(json_path) as f:
            books = json.load(f)
        for b in books:
            book = Book(id=b.get("id", str(uuid.uuid4())), title=b.get("title", ""),
                        author=b.get("author", ""), isbn=b.get("isbn", ""),
                        format=b.get("format", "Paper"), pages=b.get("pages", ""),
                        copyright_year=b.get("copyright_year", ""), read_date=b.get("read_date", ""),
                        rating=b.get("rating", ""), cover_url=b.get("cover_url", ""),
                        summary=b.get("summary", b.get("plot_summary", "")),
                        read_time_hrs=b.get("read_time_hrs", ""))
            db.session.add(book)
        db.session.commit()
        print(f"Migrated {len(books)} books from library.json")
    except Exception as e:
        db.session.rollback()
        print(f"Migration error: {e}")

def init_db():
    try:
        db.create_all()
        migrate_from_json()
    except Exception as e:
        print(f"DB init error: {e}")

@app.before_request
def ensure_db():
    if not getattr(app, '_db_initialized', False):
        init_db()
        app._db_initialized = True

# ── HOME ──
@app.route("/")
def index():
    return render_template("home.html")

# ── BOOKS ──
@app.route("/books")
def books():
    library = [b.to_dict() for b in Book.query.order_by(Book.author).all()]
    query = request.args.get("q", "").lower()
    sort  = request.args.get("sort", "author")
    if query:
        library = [b for b in library if query in b["title"].lower() or query in b["author"].lower()]
    if sort == "title":
        library = sorted(library, key=lambda b: b["title"].lower())
    else:
        library = sorted(library, key=lambda b: b["author"].lower())
    return render_template("books.html", books=library, query=query, sort=sort)

# ── ADD BOOK (page) ──
@app.route("/add")
def add_choice():
    return render_template("add_choice.html")

# ── ADD: SCANNER ──
@app.route("/add/scan")
def add_scan():
    return render_template("scan.html")

# ── ADD: MANUAL FORM ──
@app.route("/add/manual")
def add_manual():
    return render_template("add.html", isbn_prefill=request.args.get("isbn", ""))

# ── ADD: SAVE ──
@app.route("/add/manual/save", methods=["POST"])
def add_manual_save():
    db.session.add(Book(
        title          = request.form.get("title", "").strip(),
        author         = request.form.get("author", "").strip(),
        isbn           = request.form.get("isbn", "").strip(),
        copyright_year = request.form.get("copyright_year", "").strip(),
        pages          = request.form.get("pages", "").strip() or None,
        read_date      = request.form.get("read_date") or None,
        format         = request.form.get("format", "Paper"),
        read_time_hrs  = request.form.get("read_time_hrs") or None,
        summary        = request.form.get("plot_summary", "").strip(),
        cover_url      = request.form.get("cover_url", "").strip(),
        rating         = request.form.get("rating") or None,
    ))
    db.session.commit()
    return redirect(url_for("books"))

# ── REMOVE ──
@app.route("/remove/<int:index>")
def remove(index):
    library = load_library()
    library.pop(index)
    save_library(library)
    return redirect(url_for("books"))

# ── UPDATE STATUS ──
@app.route("/status/<int:index>/<status>")
def update_status(index, status):
    library = load_library()
    library[index]["status"] = status
    save_library(library)
    return redirect(url_for("books"))

# ── AUTHORS ──
@app.route("/authors")
def authors():
    library = [b.to_dict() for b in Book.query.order_by(Book.author).all()]
    author_map = {}
    for book in library:
        a = book["author"]
        author_map.setdefault(a, []).append(book)
    authors_sorted = sorted(author_map.items(), key=lambda x: x[0].lower())
    return render_template("authors.html", authors=authors_sorted)

# ── UTILITIES ──
@app.route("/utilities")
def utilities():
    return render_template("utilities.html")

@app.route("/utilities/export")
def export_csv():
    books = Book.query.all()
    fields = ["id","title","author","isbn","format","pages","copyright_year","read_date","rating","cover_url","summary","read_time_hrs"]
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    for book in books:
        writer.writerow(book.to_dict())
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode("utf-8")), mimetype="text/csv",
                     as_attachment=True, download_name="my_reading_alcove.csv")

@app.route("/utilities/import", methods=["POST"])
def import_csv():
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
        added = 0
        skipped = 0
        for row in reader:
            book_id = row.get("id", "").strip()
            if book_id and db.session.get(Book, book_id):
                skipped += 1
                continue
            existing = Book.query.filter_by(title=row.get("title","").strip(), author=row.get("author","").strip()).first()
            if existing:
                skipped += 1
                continue
            book = Book(id=book_id or str(uuid.uuid4()), title=row.get("title","").strip(),
                        author=row.get("author","").strip(), isbn=row.get("isbn","").strip(),
                        format=row.get("format","Paper").strip(), pages=row.get("pages","").strip(),
                        copyright_year=row.get("copyright_year","").strip(), read_date=row.get("read_date","").strip(),
                        rating=row.get("rating","").strip(), cover_url=row.get("cover_url","").strip(),
                        summary=row.get("summary","").strip(), read_time_hrs=row.get("read_time_hrs","").strip())
            db.session.add(book)
            added += 1
        db.session.commit()
        flash(f"Import complete: {added} book(s) added, {skipped} skipped (already exist).", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Import failed: {str(e)}", "error")
    return redirect(url_for("utilities"))

@app.route("/utilities/wipe", methods=["POST"])
def wipe_library():
    try:
        num_deleted = Book.query.delete()
        db.session.commit()
        flash(f"Library wiped. {num_deleted} book(s) deleted. You're starting fresh!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Wipe failed: {str(e)}", "error")
    return redirect(url_for("utilities"))

@app.route("/settings")
def settings():
    return render_template("settings.html")

@app.route("/utilities/enrich", methods=["POST"])
def enrich_csv():
    file = request.files.get("file")
    if not file or not file.filename.endswith(".csv"):
        flash("Please upload a valid .csv file with 'title' and 'author' columns.", "error")
        return redirect(url_for("utilities"))
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
                resp = requests.get("https://www.googleapis.com/books/v1/volumes", params={"q": query, "maxResults": 1, "langRestrict": "en", "key": GOOGLE_BOOKS_API_KEY}, timeout=8)
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
            except Exception:
                pass
            results.append(enriched)
            time.sleep(0.3)
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=output_fields)
        writer.writeheader()
        writer.writerows(results)
        output.seek(0)
        return send_file(io.BytesIO(output.getvalue().encode("utf-8")), mimetype="text/csv", as_attachment=True, download_name="enriched_books.csv")
    except Exception as e:
        flash(f"Enrichment failed: {str(e)}", "error")
        return redirect(url_for("utilities"))

if __name__ == "__main__":
    app.run(debug=True)
