"""
Point d'entrée de l'application EduLink.

Sécurité mise en place :
- Flask-WTF : protection CSRF sur tous les formulaires POST
- Flask-Limiter : limitation du taux de requêtes sur le login (anti brute-force)
- Sessions sécurisées : HttpOnly, SameSite=Strict, durée de vie limitée à 1h
- Headers HTTP : X-Frame-Options, X-Content-Type-Options, CSP, Referrer-Policy,
                 HSTS (prod), Permissions-Policy
- Logs : accès non autorisés tracés via le décorateur role_required
- Requêtes paramétrées : dans chaque blueprint (aucune concaténation SQL)
"""

import logging
import os
from datetime import timedelta

from dotenv import load_dotenv
from flask import Flask, render_template
from flask_wtf.csrf import CSRFProtect

from db import close_db
from extensions import limiter
from blueprints.auth.routes import auth_bp
from blueprints.admin.routes import admin_bp
from blueprints.prof.routes import prof_bp
from blueprints.eleve.routes import eleve_bp

load_dotenv()

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)

# ── Application ───────────────────────────────────────────────────────────────
app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY")

# ── Sessions sécurisées ───────────────────────────────────────────────────────
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Strict"
app.config["SESSION_COOKIE_SECURE"] = os.getenv("FLASK_ENV") == "production"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=1)

# ── CSRF (Flask-WTF) ──────────────────────────────────────────────────────────
csrf = CSRFProtect(app)

# ── Rate limiting (Flask-Limiter) ─────────────────────────────────────────────
limiter.init_app(app)

# ── Blueprints ────────────────────────────────────────────────────────────────
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(prof_bp)
app.register_blueprint(eleve_bp)

# ── Fermeture DB en fin de requête ────────────────────────────────────────────
app.teardown_appcontext(close_db)


# ── Headers HTTP de sécurité ──────────────────────────────────────────────────
@app.after_request
def set_security_headers(response):
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net; "
        "font-src 'self' https://fonts.gstatic.com https://cdn.jsdelivr.net; "
        "img-src 'self' data:; "
        "script-src 'self'"
    )
    if os.getenv("FLASK_ENV") == "production":
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
    return response


# ── Gestionnaire d'erreur 403 ────────────────────────────────────────────────
@app.errorhandler(403)
def forbidden(_e):
    return render_template("403.html"), 403


# ── Gestionnaire d'erreur 404 ────────────────────────────────────────────────
@app.errorhandler(404)
def not_found(_e):
    return render_template("404.html"), 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
