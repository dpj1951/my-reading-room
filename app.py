from flask import Flask, render_template, request, redirect, url_for, jsonify
import json
import os
import uuid
import requests
from datetime import date

LIBRARY_FILE = "library.json"
app = Flask(__name__)

# ── helpers ───────────────────────────────────────────────────────────────────

def load_library():
    if os.path.exists(LIBRARY_FILE):
        with open(LIBRARY_FILE, "r") as f:
            return json.load(f)
    return []

def save_library(library):
    with open(LIBRARY_FILE, "w") as f:
        json.dump(library, f, indent=2)

def find_book(library, book_id):
    return next((b for b in library if b.get("id") == book_id), None)

# ── routes ────────────────────────────────────────────────────────────────────
@app.route("/")
def home():
    return render_template("home.html")

@app.route("/books")
def index():
    library = load_library()
    query  = request.args.get("q", "").strip().lower()
    fmt    = request.args.get("format", "").strip()
    sort   = request.args.get("sort", "date_desc")

    if query:
        library = [b for b in library if
                   query in b.get("title", "").lower() or
                   query in b.get("author", "").lower()]
    if fmt:
        library = [b for b in library if b.get("format", "") == fmt]

    def sort_key(b):
        if sort == "author": return b.get("author", "").lower()
        if sort == "title":
            t = b.get("title", "").lower()
            for art in ("the ", "a ", "an "):
                if t.startswith(art): t = t[len(art):]
            return t
        if sort == "date_asc": return b.get("read_date", "0000-00-00")
        return b.get("read_date", "0000-00-00")

    reverse = sort == "date_desc"
    library = sorted(library, key=sort_key, reverse=reverse)

    return render_template("index.html", books=library, query=query,
                           selected_format=fmt, sort=sort,
                           today=date.today().isoformat())

@app.route("/authors")
def authors():
    return "Authors page coming soon", 200

@app.route("/utilities")
def utilities():
    return "Utilities page coming soon", 200

# ── Open Library API proxy ─────────────────────────────────────────────────────

@app.route("/api/search")
def api_search():
    q     = request.args.get("q", "").strip()
    field = request.args.get("field", "q")   # q | title | author | isbn
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
            results.append({
                "title":          d.get("title", ""),
                "author":         ", ".join(d.get("author_name", [])),
                "isbn":           (d.get("isbn") or [""])[0],
                "cover_url":      f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg" if cover_id else "",
                "pages":          str(d.get("number_of_pages_median", "")),
                "copyright_year": str(d.get("first_publish_year", "")),
                "work_key":       d.get("key", ""),
            })
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

if __name__ == "__main__":
    app.run(debug=True)
