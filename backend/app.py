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
import re
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta, timezone
from functools import wraps
from openai import OpenAI
from flask import Flask, request, jsonify, session, send_from_directory, redirect
from flask_cors import CORS
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
import pymongo
from auth_utils import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# ---------------------
# App & config
# ---------------------
app = Flask(__name__, static_folder="static")  # keep backend/static if you use it

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"]
)

from authlib.integrations.flask_client import OAuth

oauth = OAuth(app)

google = oauth.register(
    name='google',
    client_id="YOUR_GOOGLE_CLIENT_ID",
    client_secret="YOUR_SECRET",
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"}
)

app.config["SECRET_KEY"] = "change-this-secret"  # change for production (use env var)
app.config["MONGO_URI"] = "mongodb+srv://vanshika1310sharma\_db\_user:xd0CvUEgCTkNN6MI@cluster0.4r2c82p.mongodb.net/?appName=Cluster0"
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
# OpenAI: only construct client when OPENAI_API_KEY is set so `python app.py` still boots in dev.
_openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=_openai_api_key) if _openai_api_key else None

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

def send_email_otp(to_email, code):
    sender_email = "your_email@gmail.com"
    app_password = "your_app_password"  # paste here

    subject = "TrendÉvo Email Verification"
    body = f"Your OTP is: {code}. It will expire in 5 minutes."

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = to_email

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, app_password)
        server.send_message(msg)
        server.quit()
        print("OTP sent successfully")
    except Exception as e:
        print("Email error:", e)

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

@app.route("/dresses")
def dresses():
    return send_from_directory(FRONTEND_DIR, "dresses.html")

@app.route("/denims")
def denims():
    return send_from_directory(FRONTEND_DIR, "denims.html")

@app.route("/jackets")
def product():
    return send_from_directory(FRONTEND_DIR, "jackets.html")

@app.route("/knitwear")
def dresses():
    return send_from_directory(FRONTEND_DIR, "knitwear.html")

@app.route("/thrift")
def denims():
    return send_from_directory(FRONTEND_DIR, "thrift.html")

@app.route("/product")
def product():
    return send_from_directory(FRONTEND_DIR, "product.html")

@app.route("/upperwear")
def product():
    return send_from_directory(FRONTEND_DIR, "upperwear.html")
# ---------------------
# Simple index / health
# ---------------------
@app.route("/", methods=["GET"])
def home():
    return send_from_directory(FRONTEND_DIR, "shop.html")

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

# ---------------------
# Auth routes
# ---------------------
import random

@app.route("/api/auth/signup", methods=["POST"])
@limiter.limit("5 per minute")
def signup():
    data = request.get_json()
    name = data.get("name")
    email = data.get("email").lower()
    password = str(data.get("password", "")).strip()
    if not password:
        return jsonify({"message": "Password required"}), 400
    role = data.get("role", "customer")
    print("DATA RECEIVED:", data)

    EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@(gmail|yahoo|outlook)\.com$'
    if not re.match(EMAIL_REGEX, email):
        return jsonify({
            "message": "Only gmail, yahoo, outlook emails allowed"
        }), 400
    
    PASSWORD_REGEX = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{6,15}$'
    if not re.match(PASSWORD_REGEX, password):
        return jsonify({
            "message": "Password must be 6-15 chars with uppercase, lowercase, number, special character"
            }), 400
    
    if not name or not email or not password:
        return jsonify({"message": "Missing fields"}), 400

    if mongo.db.users.find_one({"email": email}):
        return jsonify({"message": "Email already exists"}), 400

    password_hash = hash_password(password)
    
    
    verification_code = str(random.randint(100000, 999999))
    expiry_time = datetime.now(timezone.utc) + timedelta(minutes=5)
    send_email_otp(email, verification_code)
    user_doc = {
        "name": name,
        "email": email,
        "password_hash": password_hash,
        "role": role,
        "is_verified": False,
        "verification_code": verification_code,
        "refresh_token": None,
        "otp_expiry": expiry_time,
        "created_at": datetime.now(timezone.utc)
    }

    mongo.db.users.insert_one(user_doc)

    print(f"Verification code for {email}: {verification_code}")

    return jsonify({
        "message": "User created. Verify email.",
        "email": email
    }), 201

@app.route("/api/auth/verify", methods=["POST"])
def verify_email():
    data = request.get_json()
    email = data.get("email")
    code = data.get("code")

    user = mongo.db.users.find_one({"email": email})

    if not user:
        return jsonify({"message": "User not found"}), 404

    if user["verification_code"] != code:
        return jsonify({"message": "Invalid code"}), 400
    if datetime.utcnow() > user["otp_expiry"]:
        return jsonify({"message": "OTP expired"}), 400

    mongo.db.users.update_one(
        {"email": email},
        {"$set": {"is_verified": True}, "$unset": {"verification_code": ""}}
    )

    return jsonify({"message": "Email verified!"})

@app.route("/api/auth/resend-otp", methods=["POST"])
def resend_otp():
    data = request.get_json()
    email = data.get("email")

    user = mongo.db.users.find_one({"email": email})

    if not user:
        return jsonify({"message": "User not found"}), 404

    new_code = str(random.randint(100000, 999999))
    expiry = datetime.utcnow() + timedelta(minutes=5)

    mongo.db.users.update_one(
        {"email": email},
        {"$set": {
            "verification_code": new_code,
            "otp_expiry": expiry
        }}
    )

    send_email_otp(email, new_code)

    return jsonify({"message": "OTP resent"})

@app.route("/auth/google")
def google_login():
    return google.authorize_redirect("http://127.0.0.1:5000/auth/callback")

@app.route("/auth/callback")
def google_callback():
    token = google.authorize_access_token()
    user_info = token["userinfo"]

    email = user_info["email"]

    user = mongo.db.users.find_one({"email": email})

    if not user:
        mongo.db.users.insert_one({
            "email": email,
            "name": user_info["name"],
            "role": "customer",
            "is_verified": True
        })

    return redirect("/shop")

import pyotp

@app.route("/api/auth/setup-mfa")
def setup_mfa():
    user = mongo.db.users.find_one({"email": "test@test.com"})

    secret = pyotp.random_base32()

    mongo.db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"mfa_secret": secret}}
    )

    otp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=user["email"],
        issuer_name="TrendEvo"
    )

    return jsonify({"qr": otp_uri})

@app.route("/api/auth/verify-mfa", methods=["POST"])
def verify_mfa():
    data = request.get_json()
    code = data.get("code")

    user = mongo.db.users.find_one({"email": "test@test.com"})

    totp = pyotp.TOTP(user["mfa_secret"])

    if totp.verify(code):
        return jsonify({"message": "MFA success"})
    else:
        return jsonify({"message": "Invalid code"}), 400

@app.route("/api/auth/login", methods=["POST"])
@limiter.limit("5 per minute")
def login():
    data = request.get_json() or {}

    email = (data.get("email")or "").lower()
    password = data.get("password")

    user = mongo.db.users.find_one({"email": email})

    if not user or not verify_password(password, user["password_hash"]):
        return jsonify({"message": "Invalid credentials"}), 401

    if not user.get("is_verified"):
        return jsonify({"message": "Verify email first"}), 403

    access_token = create_access_token({
        "user_id": str(user["_id"]),
        "role": user["role"]
    })

    refresh_token = create_refresh_token()

    mongo.db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"refresh_token": refresh_token}}
    )

    response = jsonify({"message": "Login successful"})
    
    response.set_cookie(
        "access_token",
        access_token,
        httponly=True,
        secure=False,
        samesite="Strict"
        )
    response.set_cookie(
        "refresh_token",
        refresh_token,
        httponly=True,
        secure=False,
        samesite="Strict"
        )
    return response

@app.route("/api/auth/refresh", methods=["POST"])
def refresh():
    refresh_token = request.cookies.get("refresh_token")

    user = mongo.db.users.find_one({"refresh_token": refresh_token})

    if not user:
        return jsonify({"message": "Invalid refresh token"}), 401

    new_access = create_access_token({
        "user_id": str(user["_id"]),
        "role": user["role"]
    })

    response = jsonify({"message": "Token refreshed"})

    response.set_cookie(
        "access_token",
        new_access,
        httponly=True,
        secure=False,
        samesite="Strict"
    )

    return response


@app.route("/api/auth/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"success": True, "message": "Logged out."}), 200

def role_required(allowed_roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            token = request.cookies.get("access_token")

            if not token:
                return jsonify({"message": "Unauthorized"}), 401

            decoded = decode_token(token)

            if not decoded or decoded["role"] not in allowed_roles:
                return jsonify({"message": "Forbidden"}), 403

            return fn(*args, **kwargs)
        return wrapper
    return decorator

@app.route("/api/admin/dashboard")
@role_required(["admin"])
def admin_dashboard():
    return jsonify({
        "message": "Welcome Admin",
        "stats": {
            "users": mongo.db.users.count_documents({}),
            "products": mongo.db.products.count_documents({})
        }
    })
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
# ----------------------
# Chatbot Engine Function
# ----------------------
response_cache = {}

def cached_ai_call(prompt):
    if prompt in response_cache:
        return response_cache[prompt]

    result = get_ai_response(prompt)
    response_cache[prompt] = result
    return result

def get_ai_response(prompt, model="gpt-4o-mini", system=None, max_tokens=None):
    """
    Single place for OpenAI chat calls with production-safe fallback on failure.
    """
    if not client:
        print("AI Error: OPENAI_API_KEY is not set")
        return "⚠️ AI service is temporarily unavailable. Please try again later."
    try:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        kwargs = {"model": model, "messages": messages}
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        response = client.chat.completions.create(**kwargs)
        text = response.choices[0].message.content
        return text.strip() if text else ""
    except Exception as e:
        print("AI Error:", e)
        return "⚠️ AI service is temporarily unavailable. Please try again later."


def get_trending_styles():
    return get_ai_response(
        "What are the trending fashion styles right now?",
        model="gpt-3.5-turbo",
        system="You are a fashion trend expert. Provide 3-5 current or upcoming fashion trends in a concise list.",
        max_tokens=150,
    )


def chatbot_engine(message):

    message = message.lower()

    # Trend Intent
    if "trend" in message:
        trend = cached_ai_call("trending fashion styles 2026")
    # Shop Intent
    elif "buy" in message or "shop" in message or "thrift" in message:
        products = mongo.db.products.find().limit(3)

        items = []
        for p in products:
            items.append(p.get("name","fashion item"))

        if items:
            return "You can check these trending thrift items: " + ", ".join(items)
        else:
            return "No thrift items available currently."

    # Login Help
    elif "login" in message:
        return "Go to Login page from homepage to access marketplace."

    # General AI Styling
    else:
        return get_ai_response(
            message,
            model="gpt-4.1-mini",
            system="You are TrendEvo AI stylist. Suggest sustainable fashion styling.",
        )
    
# ---------------------
# Create Chat API Route
# ---------------------
@app.route("/api/chat", methods=["POST"])
def chat():

    try:
        data = request.get_json(silent=True) or {}
        message = (data.get("message") or "").strip()
        if not message:
            return jsonify({"reply": "Please enter a message."}), 400

        # Use OpenAI-backed chatbot engine instead of Claude.
        reply = chatbot_engine(message)

        mongo.db.chat_history.insert_one({
            "message": message,
            "reply": reply,
            "time": datetime.now(timezone.utc)
        })

        return jsonify({"reply": reply})

    except Exception as e:
        print("CHAT ERROR:", e)
        return jsonify({"reply": "OpenAI chat failed. Check terminal logs."}), 500
# Run server
# ---------------------
if __name__ == "__main__":
    # debug True is convenient for development; set to False when done
    app.run(debug=True, host="127.0.0.1", port=5000)
