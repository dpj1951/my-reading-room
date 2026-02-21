
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

@app.route("/")
def index():
    library = load_library()
    query = request.args.get("q", "").lower()
    if query:
        library = [b for b in library if query in b["title"].lower() or query in b["author"].lower()]
    return render_template("index.html", books=library, query=query)

@app.route("/add", methods=["POST"])
def add():
    library = load_library()
    title = request.form["title"]
    author = request.form["author"]
    library.append({"title": title, "author": author, "status": "To Read"})
    save_library(library)
    return redirect(url_for("index"))

@app.route("/remove/<int:index>")
def remove(index):
    library = load_library()
    library.pop(index)
    save_library(library)
    return redirect(url_for("index"))

@app.route("/status/<int:index>/<status>")
def update_status(index, status):
    library = load_library()
    library[index]["status"] = status
    save_library(library)
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)