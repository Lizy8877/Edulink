"""
Blueprint eleve — espace réservé aux élèves (id_role = 3).
Toute route de ce blueprint exige @role_required(3).

Fonctionnalités :
  - Dashboard : vue d'ensemble (nb notes, moyenne, prochain cours)
  - Notes     : liste de toutes les notes par évaluation
  - Emploi du temps : planning hebdomadaire de la classe
"""

import logging
from datetime import date, timedelta

from flask import Blueprint, render_template, session
from decorators import role_required
from db import get_db

eleve_bp = Blueprint("eleve", __name__, url_prefix="/eleve",
                     template_folder="../../templates/eleve")

logger = logging.getLogger(__name__)


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_eleve_id():
    return session.get("user_id")


def _fmt_time(t):
    """Convertit un timedelta ou time MySQL en chaîne HH:MM."""
    if hasattr(t, "total_seconds"):
        s = int(t.total_seconds())
        return "%02d:%02d" % (s // 3600, (s % 3600) // 60)
    return t.strftime("%H:%M")


# ── Dashboard ─────────────────────────────────────────────────────────────────

@eleve_bp.route("/dashboard")
@role_required(3)
def dashboard():
    eleve_id = get_eleve_id()
    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute(
        "SELECT id_classe FROM Utilisateurs WHERE id_user = %s",
        (eleve_id,)
    )
    row = cur.fetchone()
    id_classe = row["id_classe"] if row else None

    cur.execute(
        "SELECT COUNT(*) AS nb, AVG(note) AS moyenne FROM Notes WHERE id_eleve = %s",
        (eleve_id,)
    )
    stats = cur.fetchone()

    prochain_cours = None
    if id_classe:
        cur.execute(
            """
            SELECT e.date, e.heure_debut, e.heure_fin, e.salle,
                   u.nom, u.prenom, u.matiere
            FROM Emploi_du_temps e
            JOIN Utilisateurs u ON u.id_user = e.id_prof
            WHERE e.id_classe = %s AND e.date >= CURDATE()
            ORDER BY e.date ASC, e.heure_debut ASC
            LIMIT 1
            """,
            (id_classe,)
        )
        prochain_cours = cur.fetchone()
        if prochain_cours:
            prochain_cours["hd_str"] = _fmt_time(prochain_cours["heure_debut"])
            prochain_cours["hf_str"] = _fmt_time(prochain_cours["heure_fin"])

    cur.execute(
        """
        SELECT n.note, ev.nom_eval, ev.date_fin,
               u.nom AS prof_nom, u.prenom AS prof_prenom
        FROM Notes n
        JOIN Evaluation ev ON ev.id_eval = n.id_eval
        JOIN Utilisateurs u ON u.id_user = n.id_prof
        WHERE n.id_eleve = %s
        ORDER BY ev.date_fin DESC
        LIMIT 5
        """,
        (eleve_id,)
    )
    dernieres_notes = cur.fetchall()
    cur.close()

    moyenne = round(stats["moyenne"], 2) if stats and stats["moyenne"] else None

    return render_template(
        "eleve/dashboard.html",
        nom=session.get("nom"),
        prenom=session.get("prenom"),
        nb_notes=stats["nb"],
        moyenne=moyenne,
        prochain_cours=prochain_cours,
        dernieres_notes=dernieres_notes,
    )


# ── Notes ─────────────────────────────────────────────────────────────────────

@eleve_bp.route("/notes")
@role_required(3)
def notes():
    eleve_id = get_eleve_id()
    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute(
        """
        SELECT n.note,
               ev.nom_eval, ev.description, ev.date_fin,
               u.nom AS prof_nom, u.prenom AS prof_prenom, u.matiere
        FROM Notes n
        JOIN Evaluation ev ON ev.id_eval = n.id_eval
        JOIN Utilisateurs u ON u.id_user = n.id_prof
        WHERE n.id_eleve = %s
        ORDER BY ev.date_fin DESC
        """,
        (eleve_id,)
    )
    notes_list = cur.fetchall()

    cur.execute(
        "SELECT AVG(note) AS moyenne FROM Notes WHERE id_eleve = %s",
        (eleve_id,)
    )
    row = cur.fetchone()
    moyenne = round(row["moyenne"], 2) if row and row["moyenne"] else None

    cur.close()
    return render_template(
        "eleve/notes.html",
        nom=session.get("nom"),
        prenom=session.get("prenom"),
        notes=notes_list,
        moyenne=moyenne,
    )


# ── Emploi du temps ───────────────────────────────────────────────────────────

@eleve_bp.route("/emploi-du-temps")
@role_required(3)
def emploi_du_temps():
    eleve_id = get_eleve_id()
    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute(
        "SELECT id_classe FROM Utilisateurs WHERE id_user = %s",
        (eleve_id,)
    )
    row = cur.fetchone()
    id_classe = row["id_classe"] if row else None

    semaines = []
    creneaux = []

    if id_classe:
        cur.execute(
            """
            SELECT e.date, e.heure_debut, e.heure_fin, e.salle,
                   u.nom, u.prenom, u.matiere
            FROM Emploi_du_temps e
            JOIN Utilisateurs u ON u.id_user = e.id_prof
            WHERE e.id_classe = %s
            ORDER BY e.date ASC, e.heure_debut ASC
            """,
            (id_classe,)
        )
        cours_list = cur.fetchall()

        for c in cours_list:
            c["hd_str"] = _fmt_time(c["heure_debut"])
            c["hf_str"] = _fmt_time(c["heure_fin"])

        creneaux_dict = {}
        for c in cours_list:
            creneaux_dict[c["hd_str"]] = c["hf_str"]
        creneaux = sorted(creneaux_dict.items())

        semaines_raw = {}
        for c in cours_list:
            d = c["date"]
            lundi = d - timedelta(days=d.weekday())
            semaines_raw.setdefault(lundi, {})
            semaines_raw[lundi].setdefault(d.weekday(), {})
            semaines_raw[lundi][d.weekday()][c["hd_str"]] = c

        semaines = [
            {
                "lundi": lundi,
                "jours_dates": [lundi + timedelta(days=i) for i in range(5)],
                "par_jour": par_jour,
            }
            for lundi, par_jour in sorted(semaines_raw.items())
        ]

    cur.close()
    return render_template(
        "eleve/emploi_du_temps.html",
        nom=session.get("nom"),
        prenom=session.get("prenom"),
        semaines=semaines,
        creneaux=creneaux,
        jours_noms=["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"],
        today=date.today(),
    )
