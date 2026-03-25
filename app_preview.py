from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify
import sqlite3, os, uuid, json, csv, io, requests as req_lib
from datetime import date

app = Flask(__name__)
app.secret_key = "preview-secret"
DB = os.path.join(os.path.expanduser("~"), "Downloads", "my-reading-room", "instance", "library.db")

def get_db():
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS books (
            id TEXT PRIMARY KEY, title TEXT NOT NULL, author TEXT NOT NULL,
            isbn TEXT DEFAULT '', format TEXT DEFAULT 'Paper', pages TEXT DEFAULT '',
            copyright_year TEXT DEFAULT '', read_date TEXT DEFAULT '',
            rating TEXT DEFAULT '', cover_url TEXT DEFAULT '',
            summary TEXT DEFAULT '', read_time_hrs TEXT DEFAULT '')""")
        if conn.execute("SELECT COUNT(*) FROM books").fetchone()[0] == 0:
            json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "library.json")
            if os.path.exists(json_path):
                with open(json_path) as f:
                    books = json.load(f)
                for b in books:
                    conn.execute("INSERT OR IGNORE INTO books VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                        (b.get("id", str(uuid.uuid4())), b.get("title",""), b.get("author",""),
                         b.get("isbn",""), b.get("format","Paper"), b.get("pages",""),
                         b.get("copyright_year",""), b.get("read_date",""), b.get("rating",""),
                         b.get("cover_url",""), b.get("summary", b.get("plot_summary","")), b.get("read_time_hrs","")))

init_db()
def row_to_dict(row): return dict(row)

@app.route("/")
def index(): return render_template("home.html")

@app.route("/books")
def books():
    q = request.args.get("q","").lower()
    sort = request.args.get("sort","author")
    fmt = request.args.get("format","")
    with get_db() as conn:
        library = [row_to_dict(r) for r in conn.execute("SELECT * FROM books").fetchall()]
    if q: library = [b for b in library if q in b["title"].lower() or q in b["author"].lower()]
    if fmt: library = [b for b in library if b["format"]==fmt]
    if sort=="title": library.sort(key=lambda b: b["title"].lower())
    elif sort=="date_desc": library.sort(key=lambda b: b["read_date"] or "", reverse=True)
    elif sort=="date_asc": library.sort(key=lambda b: b["read_date"] or "")
    else: library.sort(key=lambda b: b["author"].lower())
    return render_template("index.html", books=library, query=q, sort=sort, selected_format=fmt)

@app.route("/add")
def add_choice(): return render_template("add_choice.html")

@app.route("/add/scan")
def add_scan(): return render_template("scan.html")

@app.route("/add/manual")
def add_manual(): return render_template("add.html", isbn_prefill=request.args.get("isbn",""), today=str(date.today()))

@app.route("/add/manual/save", methods=["POST"])
def add_manual_save():
    with get_db() as conn:
        conn.execute("INSERT INTO books VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (str(uuid.uuid4()), request.form.get("title","").strip(), request.form.get("author","").strip(),
             request.form.get("isbn","").strip(), request.form.get("format","Paper"),
             request.form.get("pages","").strip(), request.form.get("copyright_year","").strip(),
             request.form.get("read_date","") or None, request.form.get("rating","") or None,
             request.form.get("cover_url","").strip(), request.form.get("plot_summary","").strip(),
             request.form.get("read_time_hrs","") or None))
    return redirect(url_for("books"))

@app.route("/book/<book_id>")
def book_detail(book_id):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM books WHERE id=?", (book_id,)).fetchone()
    if not row: return "Not found", 404
    return render_template("detail.html", book=row_to_dict(row))

@app.route("/book/<book_id>/edit", methods=["GET","POST"])
def book_edit(book_id):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM books WHERE id=?", (book_id,)).fetchone()
        if not row: return "Not found", 404
        if request.method == "POST":
            conn.execute("UPDATE books SET title=?,author=?,isbn=?,format=?,pages=?,copyright_year=?,read_date=?,rating=?,cover_url=?,summary=?,read_time_hrs=? WHERE id=?",
                (request.form.get("title","").strip(), request.form.get("author","").strip(),
                 request.form.get("isbn","").strip(), request.form.get("format","Paper"),
                 request.form.get("pages","").strip(), request.form.get("copyright_year","").strip(),
                 request.form.get("read_date","") or None, request.form.get("rating","") or None,
                 request.form.get("cover_url","").strip(), request.form.get("summary","").strip(),
                 request.form.get("read_time_hrs","") or None, book_id))
            return redirect(url_for("book_detail", book_id=book_id))
    return render_template("edit.html", book=row_to_dict(row), today=str(date.today()))

@app.route("/book/<book_id>/delete", methods=["POST"])
def book_delete(book_id):
    with get_db() as conn: conn.execute("DELETE FROM books WHERE id=?", (book_id,))
    return redirect(url_for("books"))

@app.route("/authors")
def authors():
    with get_db() as conn:
        library = [row_to_dict(r) for r in conn.execute("SELECT * FROM books ORDER BY author").fetchall()]
    author_map = {}
    for book in library: author_map.setdefault(book["author"],[]).append(book)
    return render_template("authors.html", authors=sorted(author_map.items(), key=lambda x: x[0].lower()))

@app.route("/utilities")
def utilities(): return render_template("utilities.html")

@app.route("/utilities/export")
def export_csv():
    with get_db() as conn:
        books = [row_to_dict(r) for r in conn.execute("SELECT * FROM books").fetchall()]
    fields = ["id","title","author","isbn","format","pages","copyright_year","read_date","rating","cover_url","summary","read_time_hrs"]
    out = io.StringIO()
    w = csv.DictWriter(out, fieldnames=fields, extrasaction='ignore')
    w.writeheader(); w.writerows(books); out.seek(0)
    return send_file(io.BytesIO(out.getvalue().encode()), mimetype="text/csv", as_attachment=True, download_name="my_reading_alcove.csv")

@app.route("/utilities/import", methods=["POST"])
def import_csv():
    file = request.files.get("file")
    if not file: flash("Please upload a CSV.", "error"); return redirect(url_for("utilities"))
    try:
        content = file.stream.read().decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(content))
        added = skipped = 0
        with get_db() as conn:
            for row in reader:
                if conn.execute("SELECT id FROM books WHERE title=? AND author=?",(row.get("title",""),row.get("author",""))).fetchone():
                    skipped += 1; continue
                conn.execute("INSERT INTO books VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    (row.get("id") or str(uuid.uuid4()), row.get("title",""), row.get("author",""),
                     row.get("isbn",""), row.get("format","Paper"), row.get("pages",""),
                     row.get("copyright_year",""), row.get("read_date",""), row.get("rating",""),
                     row.get("cover_url",""), row.get("summary",""), row.get("read_time_hrs","")))
                added += 1
        flash(f"Import complete: {added} added, {skipped} skipped.", "success")
    except Exception as e: flash(f"Import failed: {e}", "error")
    return redirect(url_for("utilities"))

@app.route("/utilities/wipe", methods=["POST"])
def wipe_library():
    with get_db() as conn: n = conn.execute("DELETE FROM books").rowcount
    flash(f"Library wiped. {n} deleted.", "success")
    return redirect(url_for("utilities"))

@app.route("/api/search")
def api_search():
    q = request.args.get("q",""); field = request.args.get("field","q")
    try:
        r = req_lib.get("https://openlibrary.org/search.json", params={field:q,"limit":8,"fields":"key,title,author_name,isbn,first_publish_year,number_of_pages_median,cover_i"}, timeout=8)
        results = []
        for d in r.json().get("docs",[])[:6]:
            cover = f"https://covers.openlibrary.org/b/id/{d['cover_i']}-M.jpg" if d.get("cover_i") else ""
            results.append({"title":d.get("title",""),"author":(d.get("author_name") or [""])[0],"isbn":((d.get("isbn") or [""])[0]),"pages":str(d.get("number_of_pages_median","") or ""),"copyright_year":str(d.get("first_publish_year","") or ""),"cover_url":cover,"work_key":d.get("key","")})
        return jsonify(results)
    except: return jsonify([])

@app.route("/api/summary")
def api_summary():
    key = request.args.get("key","")
    try:
        r = req_lib.get(f"https://openlibrary.org{key}.json", timeout=8)
        desc = r.json().get("description","")
        if isinstance(desc, dict): desc = desc.get("value","")
        return jsonify({"summary": desc[:800]})
    except: return jsonify({"summary":""})

@app.route("/settings")
def settings(): return "<h2 style='font-family:sans-serif;padding:40px'>Settings coming soon.</h2><a href='/'>Home</a>"

@app.route("/help")
def help_page(): return "<h2 style='font-family:sans-serif;padding:40px'>Help coming soon.</h2><a href='/'>Home</a>"

if __name__ == "__main__":
    print("\n App running at http://localhost:5000\n")
    app.run(debug=True, port=5000)
