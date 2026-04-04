

from flask import Flask, render_template, request, redirect, url_for, abort, jsonify, send_file, flash
import json
import os
import uuid
import requests
import csv
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
    wiped_flag = os.path.join(os.path.dirname(__file__), ".library_wiped")
    if os.path.exists(wiped_flag):
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
 
# ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¢ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¢ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ HOME ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¢ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¢ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ
@app.route("/")
def index():
    return render_template("home.html")
 
# ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¢ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¢ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ BOOKS ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¢ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¢ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ
@app.route("/books")
def books():
    from datetime import datetime
    library = [b.to_dict() for b in Book.query.all()]
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
    library = sorted(library, key=parse_date, reverse=True)
    return render_template("books.html", books=library)
 
# ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¢ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¢ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ ADD BOOK (page) ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¢ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¢ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ
@app.route("/add")
def add_choice():
    return render_template("add_choice.html")
 
# ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¢ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¢ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ ADD: SCANNER ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¢ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¢ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ
@app.route("/add/scan")
def add_scan():
    return render_template("scan.html")
 
# ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¢ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¢ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ ADD: MANUAL FORM ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¢ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¢ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ
@app.route("/add/manual")
def add_manual():
    return render_template("add.html", isbn_prefill=request.args.get("isbn", ""))
 
# ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¢ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¢ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ ADD: SAVE ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¢ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¢ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ
@app.route("/add/manual/save", methods=["POST"])
def add_manual_save():
    title = request.form.get("title", "").strip()
    author = request.form.get("author", "").strip()
    if not title or not author:
        flash("Title and author are required.", "error")
        return redirect(url_for("add_manual"))
    db.session.add(Book(
        title          = title,
        author         = author,
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
 
# ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¢ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¢ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ AUTHORS ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¢ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¢ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ
@app.route("/authors")
def authors():
    library = [b.to_dict() for b in Book.query.order_by(Book.author).all()]
    author_map = {}
    for book in library:
        a = book["author"]
        author_map.setdefault(a, []).append(book)
    authors_sorted = sorted(author_map.items(), key=lambda x: x[0].lower())
    return render_template("authors.html", authors=authors_sorted)
 
# ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¢ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¢ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ UTILITIES ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¢ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¢ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ
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
def settings():
    return render_template("settings.html")
 
@app.route("/settings/backup")
def settings_backup():
    from datetime import date
    books = [b.to_dict() for b in Book.query.all()]
    payload = json.dumps({"version": 1, "exported": str(date.today()), "books": books}, indent=2)
    return send_file(
        io.BytesIO(payload.encode("utf-8")),
        mimetype="application/json",
        as_attachment=True,
        download_name=f"reading-alcove-backup-{date.today()}.json"
    )
 
@app.route("/settings/restore", methods=["POST"])
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
 
 
# ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¢ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¢ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ BOOK DETAIL ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¢ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¢ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ
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
def book_detail(book_id):
    book = db.session.get(Book, book_id)
    if not book: abort(404)
    return render_template("detail.html", book=book.to_dict())
 
# ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¢ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¢ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ BOOK EDIT ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¢ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¢ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ
@app.route("/book/<book_id>/edit", methods=["GET", "POST"])
def book_edit(book_id):
    book = db.session.get(Book, book_id)
    if not book: abort(404)
    if request.method == "POST":
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
        db.session.commit()
        return redirect(url_for("book_detail", book_id=book_id))
    from datetime import date
    return render_template("edit.html", book=book.to_dict(), today=str(date.today()))
 
# ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¢ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¢ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ BOOK DELETE ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¢ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¢ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ
@app.route("/book/<book_id>/delete", methods=["POST"])
def book_delete(book_id):
    book = db.session.get(Book, book_id)
    if not book: abort(404)
    db.session.delete(book)
    db.session.commit()
    return redirect(url_for("books"))
 
# ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¢ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¢ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ API SEARCH (Open Library) ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¢ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¢ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ
@app.route("/api/search")
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
 
# ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¢ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¢ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ API SUMMARY ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¢ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¢ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ
@app.route("/api/summary")
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
def backfill_isbn_data():
    """Return books missing ISBN-13 so the client can look them up."""
    books = Book.query.all()
    needs_update = []
    for b in books:
        isbn = (b.isbn or "").strip()
        if not isbn or not (len(isbn) == 13 and isbn.isdigit()):
            needs_update.append({"id": b.id, "title": b.title, "author": b.author, "isbn": isbn})
    return jsonify(needs_update)

@app.route("/utilities/backfill-isbn-save", methods=["POST"])
def backfill_isbn_save():
    """Accept a list of {id, isbn} pairs and update the database."""
    data = request.get_json()
    if not data or not isinstance(data, list):
        return jsonify({"error": "Invalid data"}), 400
    updated = 0
    for item in data:
        book_id = item.get("id", "").strip()
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
def backfill_covers_data():
    """Return books missing a cover URL."""
    books = Book.query.all()
    needs_cover = []
    for b in books:
        if not (b.cover_url or "").strip():
            needs_cover.append({"id": b.id, "title": b.title, "author": b.author, "isbn": b.isbn or ""})
    return jsonify(needs_cover)

@app.route("/utilities/backfill-covers-save", methods=["POST"])
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

@app.route("/utilities/cover-lookup")
def cover_lookup():
    """Server-side Google Books cover lookup Ã¢ÂÂ tries ISBN first, then title+author."""
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
def all_books_covers():
    """Return ALL books with their cover_url so the client can test which are broken."""
    books = Book.query.all()
    return jsonify([{
        "id": b.id, "title": b.title, "author": b.author,
        "isbn": b.isbn or "", "cover_url": b.cover_url or ""
    } for b in books])

@app.route("/utilities/remove-duplicates", methods=["POST"])
def remove_duplicates():
    """Find duplicate books (same title+author), keep the most complete, delete the rest."""
    books = Book.query.all()
    groups = {}
    for book in books:
        key = (book.title.strip().lower(), book.author.strip().lower())
        groups.setdefault(key, []).append(book)

    deleted = 0
    for key, group in groups.items():
        if len(group) < 2:
            continue
        def score(b):
            return sum([
                bool(b.cover_url), bool(b.isbn), bool(b.summary),
                bool(b.read_date), bool(b.rating), bool(b.pages)
            ])
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


if __name__ == "__main__":
    app.run(debug=True)
 