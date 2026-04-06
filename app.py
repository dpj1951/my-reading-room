



from flask import Flask, session, render_template, request, redirect, url_for, abort, jsonify, send_file, flash
import json
import os
import uuid
import requests
import csv
import io
from datetime import date
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
try:
    from supabase import create_client
except ImportError:
    create_client = None
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
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True,
    "pool_recycle": 300,
}
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
