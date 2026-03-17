from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, send_file
import os
import uuid
import requests
import csv
import ti
import io
from datetime import date
from flask_sqlalchemy import SQLAlchemy
app = Flask(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///library.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

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

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/books")
def index():
    query = request.args.get("q", "").strip().lower()
    fmt = request.args.get("format", "").strip()
    sort = request.args.get("sort", "date_desc")
    q = Book.query
    if query:
        q = q.filter(db.or_(Book.title.ilike(f"%{query}%"), Book.author.ilike(f"%{query}%")))
    if fmt:
        q = q.filter(Book.format == fmt)
    books = q.all()
    def sort_key(b):
        if sort == "author": return b.author.lower()
        if sort == "title":
            t = b.title.lower()
            for art in ("the ", "a ", "an "):
                if t.startswith(art): t = t[len(art):]
            return t
        return b.read_date or "0000-00-00"
    books = sorted(books, key=sort_key, reverse=(sort == "date_desc"))
    books = [b.to_dict() for b in books]
    return render_template("index.html", books=books, query=query, selected_format=fmt, sort=sort, today=date.today().isoformat())

@app.route("/book/<book_id>")
def book_detail(book_id):
    book = Book.query.get_or_404(book_id)
    return render_template("detail.html", book=book.to_dict(), today=date.today().isoformat())

@app.route("/book/<book_id>/edit", methods=["GET"])
def edit_book(book_id):
    book = Book.query.get_or_404(book_id)
    return render_template("edit.html", book=book.to_dict(), today=date.today().isoformat())

@app.route("/book/<book_id>/edit", methods=["POST"])
def edit_book_save(book_id):
    book = Book.query.get_or_404(book_id)
    book.title = request.form.get("title", book.title)
    book.author = request.form.get("author", book.author)
    book.isbn = request.form.get("isbn", "")
    book.format = request.form.get("format", "Paper")
    book.pages = request.form.get("pages", "")
    book.copyright_year = request.form.get("copyright_year", "")
    book.read_date = request.form.get("read_date", "")
    book.rating = request.form.get("rating", "")
    book.cover_url = request.form.get("cover_url", "")
    book.summary = request.form.get("summary", "")
    book.read_time_hrs = request.form.get("read_time_hrs", "")
    db.session.commit()
    return redirect(url_for("book_detail", book_id=book_id))

@app.route("/book/<book_id>/delete", methods=["POST"])
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)
    db.session.delete(book)
    db.session.commit()
    return redirect(url_for("index"))

@app.route("/add")
def add_choice():
    return render_template("add_choice.html")

@app.route("/add/manual")
def add_manual():
    return render_template("add.html", today=date.today().isoformat())

@app.route("/add/scan")
def add_scan():
    return render_template("scan.html")

@app.route("/authors")
def authors():
    from collections import defaultdict, OrderedDict
    books = Book.query.all()
    def author_sort_key(name):
        parts = name.strip().rsplit(" ", 1)
        return (parts[-1].lower(), parts[0].lower()) if len(parts) == 2 else (name.lower(), "")
    def display_name(name):
        parts = name.strip().rsplit(" ", 1)
        return f"{parts[1]}, {parts[0]}" if len(parts) == 2 else name
    by_author = defaultdict(list)
    for book in books:
        by_author[book.author or "Unknown"].append(book.to_dict())
    sorted_authors = sorted(by_author.keys(), key=author_sort_key)
    grouped = OrderedDict()
    for author in sorted_authors:
        parts = author.strip().rsplit(" ", 1)
        last = parts[-1] if parts else author
        letter = last[0].upper() if last and last[0].isalpha() else "#"
        if letter not in grouped:
            grouped[letter] = []
        grouped[letter].append((display_name(author), by_author[author]))
    return render_template("authors.html", grouped_authors=grouped, author_count=len(by_author), total_books=len(books))

@app.route("/add/manual/save", methods=["POST"])
def add_manual_save():
    book = Book(title=request.form.get("title", ""), author=request.form.get("author", ""),
                isbn=request.form.get("isbn", ""), format=request.form.get("format", "Paper"),
                pages=request.form.get("pages", ""), copyright_year=request.form.get("copyright_year", ""),
                read_date=request.form.get("read_date", ""), rating=request.form.get("rating", ""),
                cover_url=request.form.get("cover_url", ""),
                summary=request.form.get("summary", request.form.get("plot_summary", "")),
                read_time_hrs=request.form.get("read_time_hrs", ""))
    db.session.add(book)
    db.session.commit()
    return redirect(url_for("index"))

@app.route("/api/search")
def api_search():
    q = request.args.get("q", "").strip()
    field = request.args.get("field", "q")
    if not q:
        return jsonify([])
    params = {field: q, "limit": 10, "fields": "title,author_name,isbn,cover_i,first_publish_year,key,number_of_pages_median"}
    try:
        r = requests.get("https://openlibrary.org/search.json", params=params, timeout=6)
        r.raise_for_status()
        docs = r.json().get("docs", [])
        results = []
        for d in docs:
            cover_id = d.get("cover_i")
            results.append({"title": d.get("title", ""), "author": ", ".join(d.get("author_name", [])),
                            "isbn": (d.get("isbn") or [""])[0],
                            "cover_url": f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg" if cover_id else "",
                            "pages": str(d.get("number_of_pages_median", "")),
                            "copyright_year": str(d.get("first_publish_year", "")),
                            "work_key": d.get("key", "")})
        return jsonify(results)
    except Exception:
        return jsonify([])

@app.route("/api/summary")
def api_summary():
    work_key = request.args.get("key", "").strip()
    if not work_key:
        return jsonify({"summary": ""})
    try:
        r = requests.get(f"https://openlibrary.org{work_key}.json", timeout=6)
        r.raise_for_status()
        data = r.json()
        desc = data.get("description", "")
        if isinstance(desc, dict):
            desc = desc.get("value", "")
        return jsonify({"summary": desc[:600]})
    except Exception:
        return jsonify({"summary": ""})

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
    return "Settings page coming soon"

@app.route("/help_page")
def help_page():
    return "Help page coming soon"


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
    init_db()
    app.run(debug=True)
