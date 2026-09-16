# ── Image de base ─────────────────────────────────────────────
FROM python:3.11-slim

# ── Dossier de travail ────────────────────────────────────────
WORKDIR /app

# ── Dépendances système minimales ────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
        default-libmysqlclient-dev \
        gcc \
    && rm -rf /var/lib/apt/lists/*

# ── Dépendances Python ────────────────────────────────────────
# Copie requirements en premier : si le code change mais pas
# les dépendances, Docker réutilise le cache de cette couche.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Code de l'application ─────────────────────────────────────
COPY . .

# ── Utilisateur non-root (bonne pratique sécurité) ───────────
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# ── Port exposé ───────────────────────────────────────────────
EXPOSE 5000

# ── Lancement via Gunicorn (serveur de production) ───────────
# -w 2 : 2 workers
# -b 0.0.0.0:5000 : écoute sur toutes les interfaces
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "app:app"]
