from flask import Flask, render_template, request, redirect, url_for
import json
import os

LIBRARY_FILE = "library.json"
app = Flask(__name__)
app.jinja_env.filters['enumerate'] = enumerate

def load_library():
    if os.path.exists(LIBRARY_FILE):
        with open(LIBRARY_FILE, "r") as f:
            return json.load(f)
    return []

def save_library(library):
    with open(LIBRARY_FILE, "w") as f:
        json.dump(library, f, indent=2)

# ── HOME ──
@app.route("/")
def index():
    return render_template("home.html")

# ── BOOKS ──
@app.route("/books")
def books():
    library = load_library()
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
@app.route("/add-book")
def add_book():
    return render_template("add_book.html")

# ── ADD BOOK (form submit) ──
@app.route("/add", methods=["POST"])
def add():
    library = load_library()
    library.append({
        "title":  request.form.get("title", "").strip(),
        "author": request.form.get("author", "").strip(),
        "isbn":   request.form.get("isbn",  "").strip(),
        "year":   request.form.get("year",  "").strip(),
        "series": request.form.get("series","").strip(),
        "status": request.form.get("status","To Read"),
    })
    save_library(library)
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
    library = load_library()
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

# ── SETTINGS ──
@app.route("/settings")
def settings():
    return render_template("settings.html")

# ── HELP ──
@app.route("/help")
def help():
    return render_template("help.html")

if __name__ == "__main__":
    app.run(debug=True)
