"""
Connexion à la base de données MySQL.
Fournit get_db() qui retourne un connecteur lié au contexte de la requête Flask.
"""

import os
import mysql.connector
from flask import g


def get_db():
    """Retourne la connexion DB du contexte de la requête (crée si absente)."""
    if "db" not in g:
        g.db = mysql.connector.connect(
            host=os.getenv("MYSQL_HOST", "127.0.0.1"),
            port=int(os.getenv("MYSQL_PORT", "3306")),
            database=os.getenv("MYSQL_DATABASE"),
            user=os.getenv("MYSQL_USER"),
            password=os.getenv("MYSQL_PASSWORD"),
        )
    return g.db


def close_db(e=None):
    """Ferme la connexion DB en fin de requête."""
    db = g.pop("db", None)
    if db is not None and db.is_connected():
        db.close()
