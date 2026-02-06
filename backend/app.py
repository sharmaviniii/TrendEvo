# import os
# from flask import send_from_directory 
# from flask import Flask, request, jsonify, session, send_from_directory
# from flask import Flask, request, jsonify, session
# from flask_pymongo import PyMongo
# from werkzeug.security import generate_password_hash, check_password_hash
# from datetime import datetime
# from bson.objectid import ObjectId
# from functools import wraps
# from flask_cors import CORS
# import pymongo



# app = Flask(__name__, static_folder="static")  # static_folder points to ./static
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))   # backend/
# # frontend directory is sibling to backend (D:\Trendevo\frontend)
# FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "frontend"))
# FRONTEND_IMAGES_DIR = os.path.join(FRONTEND_DIR, "images")

# # Debug route to quickly confirm paths (open in browser)
# @app.route("/__debug_frontend_paths", methods=["GET"])
# def __debug_frontend_paths():
#     return {
#         "backend_base": BASE_DIR,
#         "frontend_dir": FRONTEND_DIR,
#         "frontend_exists": os.path.isdir(FRONTEND_DIR),
#         "images_dir": FRONTEND_IMAGES_DIR,
#         "images_exists": os.path.isdir(FRONTEND_IMAGES_DIR),
#         "shop_exists": os.path.isfile(os.path.join(FRONTEND_DIR, "shop.html"))
#     }

# # # ---------------- Serve frontend files ----------------
# # @app.route("/frontend/<path:filename>")
# # def frontend_files(filename):
# #     # serves any file under ../frontend/...
# #     return send_from_directory(FRONTEND_DIR, filename)

# # # serve shop page at /shop
# # # NOTE: remove @login_required while debugging (or keep it if you already implement login properly)
# # @app.route("/shop", methods=["GET"])
# # def shop_page():
# #     return send_from_directory(FRONTEND_DIR, "shop.html")

# # # serve images from frontend/images via /images/<filename>
# # @app.route("/images/<path:filename>")
# # def serve_images(filename):
# #     return send_from_directory(FRONTEND_IMAGES_DIR, filename)




# # -------- CONFIG (DEV) --------
# app.config["SECRET_KEY"] = "change-this-secret"  # use env var in prod
# app.config["MONGO_URI"] = "mongodb://localhost:27017/trendevo"

# # Session cookie settings (DEV only)
# app.config['SESSION_COOKIE_HTTPONLY'] = True
# app.config['SESSION_COOKIE_SAMESITE'] = 'None'   # allow cross-site for dev
# app.config['SESSION_COOKIE_SECURE'] = False      # use True in prod with HTTPS

# # Allow CORS from dev frontend origins
# CORS(app,
#      supports_credentials=True,
#      origins=[
#          "http://127.0.0.1:5500",
#          "http://localhost:5500",
#          "http://127.0.0.1:3000",
#          "http://localhost:3000"
#      ])

# mongo = PyMongo(app)

# # Ensure unique email index (safe: do it inside try/except so server won't crash)
# with app.app_context():
#     try:
#         mongo.db.users.create_index("email", unique=True)
#     except Exception:
#         # ignore index creation errors in dev (DB may be unreachable)
#         pass

# # -------- Home route (simple health check) --------
# # This is the friendly route you asked to add.
# @app.route("/", methods=["GET"])
# def home():
#     return "Backend is running!"


# @app.route("/app", methods=["GET"])
# def index():

#     try:
#         return app.send_static_file("index.html")
#     except Exception:
#         return "Frontend file not found on server. Serve frontend with a static server (python -m http.server 3000).", 404


# # -------- HELPERS --------
# def login_required(fn):
#     @wraps(fn)
#     def wrapper(*args, **kwargs):
#         if "user_id" not in session:
#             return jsonify({"success": False, "message": "Authentication required."}), 401
#         return fn(*args, **kwargs)
#     return wrapper


# def serialize_user(user_doc):
#     return {
#         "id": str(user_doc["_id"]),
#         "name": user_doc.get("name"),
#         "email": user_doc.get("email"),
#         "created_at": user_doc.get("created_at").isoformat()
#             if isinstance(user_doc.get("created_at"), datetime)
#             else str(user_doc.get("created_at"))
#     }


# # -------- AUTH ROUTES --------
# @app.route("/api/auth/signup", methods=["POST"])
# def signup():
#     data = request.get_json(silent=True) or request.form
#     name = (data.get("name") or "").strip()
#     email = (data.get("email") or "").strip().lower()
#     password = data.get("password") or ""

#     if not name or not email or not password:
#         return jsonify({"success": False, "message": "Name, email and password are required."}), 400

#     try:
#         existing = mongo.db.users.find_one({"email": email})
#     except Exception as e:
#         return jsonify({"success": False, "message": "Database error.", "error": str(e)}), 500

#     if existing:
#         return jsonify({"success": False, "message": "Email already registered."}), 400

#     password_hash = generate_password_hash(password)
#     user_doc = {"name": name, "email": email, "password_hash": password_hash, "created_at": datetime.utcnow()}

#     try:
#         result = mongo.db.users.insert_one(user_doc)
#     except Exception as e:
#         return jsonify({"success": False, "message": "Database insert error.", "error": str(e)}), 500

#     user_doc["_id"] = result.inserted_id
#     session["user_id"] = str(result.inserted_id)

#     return jsonify({"success": True, "message": "Signup successful.", "user": serialize_user(user_doc)}), 201


# @app.route("/api/auth/login", methods=["POST"])
# def login():
#     data = request.get_json(silent=True) or request.form
#     email = (data.get("email") or "").strip().lower()
#     password = data.get("password") or ""

#     if not email or not password:
#         return jsonify({"success": False, "message": "Email and password are required."}), 400

#     try:
#         user = mongo.db.users.find_one({"email": email})
#     except Exception as e:
#         return jsonify({"success": False, "message": "Database error.", "error": str(e)}), 500

#     if not user or not check_password_hash(user.get("password_hash", ""), password):
#         return jsonify({"success": False, "message": "Invalid email or password."}), 401

#     session["user_id"] = str(user["_id"])
#     return jsonify({"success": True, "message": "Login successful.", "user": serialize_user(user)}), 200


# # --------- LOGOUT ROUTE ---------
# @app.route("/api/auth/logout", methods=["POST"])
# def logout():
#     """
#     Log the user out by clearing the server session.
#     Returns JSON success message.
#     """
#     session.clear()  # remove session data on server
#     return jsonify({"success": True, "message": "Logged out."}), 200
# # ------------------------------------------------------


# @app.route("/api/user/me", methods=["GET"])
# @login_required
# def me():
#     user_id = session.get("user_id")
#     try:
#         user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
#     except Exception as e:
#         return jsonify({"success": False, "message": "Database error.", "error": str(e)}), 500

#     if not user:
#         return jsonify({"success": False, "message": "User not found."}), 404

#     return jsonify({"success": True, "user": serialize_user(user)}), 200
# # Serve any frontend file at /frontend/<path:filename>
# @app.route("/frontend/<path:filename>")
# def frontend_files(filename):
#     return send_from_directory(FRONTEND_DIR, filename)

# # Serve images via /images/<filename>
# @app.route("/images/<path:filename>")
# def serve_images(filename):
#     return send_from_directory(FRONTEND_IMAGES_DIR, filename)

# # Serve shop page at /shop (remove login_required while testing if needed)
# @app.route("/shop", methods=["GET"])
# def shop_page():
#     return send_from_directory(FRONTEND_DIR, "shop.html")



# @app.route("/api/health", methods=["GET"])
# def health():
#     return jsonify({"status": "ok"}), 200



# if __name__ == "__main__":
#     app.run(debug=True, host="127.0.0.1", port=5000)

# app.py - full working copy for your setup
# app.py — complete file (copy this over your current app.py)
# app.py — complete file (copy this over your current app.py)
import os
from datetime import datetime
from functools import wraps

from flask import Flask, request, jsonify, session, send_from_directory
from flask_cors import CORS
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
import pymongo

# ---------------------
# App & config
# ---------------------
app = Flask(__name__, static_folder="static")  # keep backend/static if you use it
app.config["SECRET_KEY"] = "change-this-secret"  # change for production (use env var)
app.config["MONGO_URI"] = "mongodb://localhost:27017/trendevo"

# Session cookie (dev-friendly settings — tighten for prod)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "None"  # allows cross-site in dev
app.config["SESSION_COOKIE_SECURE"] = False     # set True in prod with HTTPS

# Allow CORS (so frontend on other port can call your API)
CORS(app,
     supports_credentials=True,
     origins=[
         "http://127.0.0.1:5500",
         "http://localhost:5500",
         "http://127.0.0.1:3000",
         "http://localhost:3000",
         "http://127.0.0.1:5000"
     ])

# ---------------------
# Mongo (Flask-PyMongo)
# ---------------------
mongo = PyMongo(app)

# ensure unique email index (safe to run each startup)
with app.app_context():
    try:
        mongo.db.users.create_index("email", unique=True)
    except pymongo.errors.OperationFailure:
        # index creation failure (already exists or permissions) — ignore for dev
        pass

# ---------------------
# Frontend folder paths
# ---------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))                     # e.g. D:\Trendevo\backend
FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "frontend"))   # e.g. D:\Trendevo\frontend
FRONTEND_IMAGES_DIR = os.path.join(FRONTEND_DIR, "images")

# Print paths at start so you can confirm in terminal
print("BASE_DIR:", BASE_DIR)
print("FRONTEND_DIR:", FRONTEND_DIR)
print("FRONTEND_IMAGES_DIR:", FRONTEND_IMAGES_DIR)

# ---------------------
# Helpers
# ---------------------
def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"success": False, "message": "Authentication required."}), 401
        return fn(*args, **kwargs)
    return wrapper


def serialize_user(user_doc):
    return {
        "id": str(user_doc["_id"]),
        "name": user_doc.get("name"),
        "email": user_doc.get("email"),
        "created_at": user_doc.get("created_at").isoformat()
            if isinstance(user_doc.get("created_at"), datetime)
            else str(user_doc.get("created_at"))
    }

# ---------------------
# Debug / frontend-check route
# ---------------------
@app.route("/__debug_frontend_paths")
def _debug_frontend_paths():
    return {
        "backend_base": BASE_DIR,
        "frontend_dir": FRONTEND_DIR,
        "frontend_exists": os.path.isdir(FRONTEND_DIR),
        "images_dir": FRONTEND_IMAGES_DIR,
        "images_exists": os.path.isdir(FRONTEND_IMAGES_DIR),
        "shop_exists": os.path.isfile(os.path.join(FRONTEND_DIR, "shop.html")),
    }

# ---------------------
# Serve frontend files (optional helpers)
# ---------------------
# Use: http://127.0.0.1:5000/frontend/shop.html  -> serves the file from frontend folder
@app.route("/frontend/<path:filename>")
def frontend_files(filename):
    # safe send from frontend dir
    return send_from_directory(FRONTEND_DIR, filename)

# Serve shop page at /shop (you can require login by adding @login_required above if needed)
@app.route("/shop", methods=["GET"])
def shop_page():
    # If you want to require login, uncomment this:
    # if "user_id" not in session:
    #     return jsonify({"success": False, "message": "Authentication required."}), 401
    return send_from_directory(FRONTEND_DIR, "shop.html")

# Serve images from frontend/images via /images/<filename>
@app.route("/images/<path:filename>")
def serve_images(filename):
    return send_from_directory(FRONTEND_IMAGES_DIR, filename)

# ---------------------
# Simple index / health
# ---------------------
@app.route("/", methods=["GET"])
def home():
    return "Backend is running!"

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

# ---------------------
# Auth routes
# ---------------------
@app.route("/api/auth/signup", methods=["POST"])
def signup():
    data = request.get_json(silent=True) or request.form
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not name or not email or not password:
        return jsonify({"success": False, "message": "Name, email and password are required."}), 400

    # check existing
    try:
        existing = mongo.db.users.find_one({"email": email})
    except Exception as e:
        return jsonify({"success": False, "message": "Database error.", "error": str(e)}), 500

    if existing:
        return jsonify({"success": False, "message": "Email already registered."}), 400

    password_hash = generate_password_hash(password)
    user_doc = {"name": name, "email": email, "password_hash": password_hash, "created_at": datetime.utcnow()}

    try:
        result = mongo.db.users.insert_one(user_doc)
    except Exception as e:
        return jsonify({"success": False, "message": "Database insert error.", "error": str(e)}), 500

    user_doc["_id"] = result.inserted_id
    session["user_id"] = str(result.inserted_id)

    return jsonify({"success": True, "message": "Signup successful.", "user": serialize_user(user_doc)}), 201


@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or request.form
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"success": False, "message": "Email and password are required."}), 400

    try:
        user = mongo.db.users.find_one({"email": email})
    except Exception as e:
        return jsonify({"success": False, "message": "Database error.", "error": str(e)}), 500

    if not user or not check_password_hash(user.get("password_hash", ""), password):
        return jsonify({"success": False, "message": "Invalid email or password."}), 401

    session["user_id"] = str(user["_id"])
    return jsonify({"success": True, "message": "Login successful.", "user": serialize_user(user)}), 200


@app.route("/api/auth/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"success": True, "message": "Logged out."}), 200

# ---------------------
# Protected user info
# ---------------------
@app.route("/api/user/me", methods=["GET"])
@login_required
def me():
    user_id = session.get("user_id")
    try:
        user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    except Exception as e:
        return jsonify({"success": False, "message": "Database error.", "error": str(e)}), 500

    if not user:
        return jsonify({"success": False, "message": "User not found."}), 404

    return jsonify({"success": True, "user": serialize_user(user)}), 200

# ---------------------
# Run server
# ---------------------
if __name__ == "__main__":
    # debug True is convenient for development; set to False when done
    app.run(debug=True, host="127.0.0.1", port=5000)
