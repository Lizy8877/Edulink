"""
Blueprint prof — espace réservé aux professeurs (id_role = 2).
Toute route de ce blueprint exige @role_required(2).

Fonctionnalités :
  - Dashboard avec vue d'ensemble
  - Mes classes (liste des classes attribuées + élèves)
  - Évaluations : créer un projet/évaluation, liste, suppression
  - Notes : attribuer / modifier une note par élève et par éval
  - Emploi du temps : consulter le planning du prof
"""

from datetime import date, timedelta

from flask import Blueprint, render_template, session, request, redirect, url_for, flash
from decorators import role_required
from db import get_db

prof_bp = Blueprint("prof", __name__, url_prefix="/prof",
                    template_folder="../../templates/prof")


# ── Helpers ────────────────────────────────────────────────────────────────────

def get_prof_id():
    return session.get("user_id")


def get_mes_classes(prof_id):
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute(
        """
        SELECT c.id_classe, c.nom_classe
        FROM Classes c
        JOIN Prof_Classe pc ON pc.id_classe = c.id_classe
        WHERE pc.id_prof = %s
        ORDER BY c.nom_classe
        """,
        (prof_id,)
    )
    classes = cur.fetchall()
    cur.close()
    return classes


# ── Dashboard ─────────────────────────────────────────────────────────────────

@prof_bp.route("/dashboard")
@role_required(2)
def dashboard():
    prof_id = get_prof_id()
    db = get_db()
    cur = db.cursor(dictionary=True)

    classes = get_mes_classes(prof_id)

    cur.execute("SELECT COUNT(*) AS nb FROM Evaluation WHERE id_prof = %s", (prof_id,))
    nb_evals = cur.fetchone()["nb"]

    cur.execute("SELECT COUNT(*) AS nb FROM Notes WHERE id_prof = %s", (prof_id,))
    nb_notes = cur.fetchone()["nb"]

    cur.execute(
        """
        SELECT e.date, e.heure_debut, e.heure_fin, e.salle, c.nom_classe
        FROM Emploi_du_temps e
        JOIN Classes c ON c.id_classe = e.id_classe
        WHERE e.id_prof = %s AND e.date >= CURDATE()
        ORDER BY e.date ASC, e.heure_debut ASC
        LIMIT 1
        """,
        (prof_id,)
    )
    prochain_cours = cur.fetchone()

    cur.execute(
        """
        SELECT ev.nom_eval, ev.date_fin, c.nom_classe
        FROM Evaluation ev
        JOIN Classes c ON c.id_classe = ev.id_classe
        WHERE ev.id_prof = %s
        ORDER BY ev.date_fin DESC
        LIMIT 5
        """,
        (prof_id,)
    )
    evals_recentes = cur.fetchall()
    cur.close()

    return render_template(
        "prof/dashboard.html",
        nom=session.get("nom"),
        prenom=session.get("prenom"),
        matiere=session.get("matiere"),
        classes=classes,
        nb_evals=nb_evals,
        nb_notes=nb_notes,
        prochain_cours=prochain_cours,
        evals_recentes=evals_recentes,
    )


# ── Mes Classes ───────────────────────────────────────────────────────────────

@prof_bp.route("/classes")
@role_required(2)
def mes_classes():
    prof_id = get_prof_id()
    classes = get_mes_classes(prof_id)

    db = get_db()
    cur = db.cursor(dictionary=True)

    for classe in classes:
        cur.execute(
            """
            SELECT u.id_user, u.nom, u.prenom, u.compte
            FROM Utilisateurs u
            WHERE u.id_classe = %s AND u.id_role = 3
            ORDER BY u.nom, u.prenom
            """,
            (classe["id_classe"],)
        )
        classe["eleves"] = cur.fetchall()

    cur.close()
    return render_template(
        "prof/classes.html",
        nom=session.get("nom"),
        prenom=session.get("prenom"),
        classes=classes,
    )


# ── Évaluations ───────────────────────────────────────────────────────────────

@prof_bp.route("/evaluations")
@role_required(2)
def evaluations():
    prof_id = get_prof_id()
    classes = get_mes_classes(prof_id)

    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute(
        """
        SELECT ev.id_eval, ev.nom_eval, ev.description, ev.date_fin,
               c.nom_classe, c.id_classe,
               COUNT(n.id_note) AS nb_notes
        FROM Evaluation ev
        JOIN Classes c ON c.id_classe = ev.id_classe
        LEFT JOIN Notes n ON n.id_eval = ev.id_eval
        WHERE ev.id_prof = %s
        GROUP BY ev.id_eval, ev.nom_eval, ev.description, ev.date_fin, c.nom_classe, c.id_classe
        ORDER BY ev.date_fin DESC
        """,
        (prof_id,)
    )
    evals = cur.fetchall()
    cur.close()

    return render_template(
        "prof/evaluations.html",
        nom=session.get("nom"),
        prenom=session.get("prenom"),
        evals=evals,
        classes=classes,
    )


@prof_bp.route("/evaluations/creer", methods=["POST"])
@role_required(2)
def creer_evaluation():
    prof_id     = get_prof_id()
    nom_eval    = request.form.get("nom_eval", "").strip()
    description = request.form.get("description", "").strip()
    date_fin    = request.form.get("date_fin", "").strip()
    id_classe   = request.form.get("id_classe", "").strip()

    if not nom_eval or not date_fin or not id_classe:
        flash("Tous les champs obligatoires doivent être remplis.", "error")
        return redirect(url_for("prof.evaluations"))

    classes    = get_mes_classes(prof_id)
    ids_valides = [str(c["id_classe"]) for c in classes]
    if id_classe not in ids_valides:
        flash("Classe non autorisée.", "error")
        return redirect(url_for("prof.evaluations"))

    db = get_db()
    cur = db.cursor()
    cur.execute(
        """
        INSERT INTO Evaluation (id_prof, id_classe, nom_eval, description, date_fin)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (prof_id, int(id_classe), nom_eval, description or None, date_fin)
    )
    db.commit()
    cur.close()
    flash(f"Évaluation « {nom_eval} » créée avec succès.", "success")
    return redirect(url_for("prof.evaluations"))


@prof_bp.route("/evaluations/<int:id_eval>/supprimer", methods=["POST"])
@role_required(2)
def supprimer_evaluation(id_eval):
    prof_id = get_prof_id()
    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("SELECT id_prof FROM Evaluation WHERE id_eval = %s", (id_eval,))
    row = cur.fetchone()
    if not row or row["id_prof"] != prof_id:
        flash("Action non autorisée.", "error")
        cur.close()
        return redirect(url_for("prof.evaluations"))

    cur.execute("DELETE FROM Evaluation WHERE id_eval = %s", (id_eval,))
    db.commit()
    cur.close()
    flash("Évaluation supprimée.", "success")
    return redirect(url_for("prof.evaluations"))


# ── Notes ─────────────────────────────────────────────────────────────────────

@prof_bp.route("/notes")
@role_required(2)
def notes():
    prof_id = get_prof_id()
    classes = get_mes_classes(prof_id)
    id_classe_filtre = request.args.get("id_classe", type=int)

    db = get_db()
    cur = db.cursor(dictionary=True)

    if id_classe_filtre:
        cur.execute(
            """
            SELECT ev.id_eval, ev.nom_eval, ev.date_fin, c.nom_classe, ev.id_classe
            FROM Evaluation ev
            JOIN Classes c ON c.id_classe = ev.id_classe
            WHERE ev.id_prof = %s AND ev.id_classe = %s
            ORDER BY ev.date_fin DESC
            """,
            (prof_id, id_classe_filtre)
        )
    else:
        cur.execute(
            """
            SELECT ev.id_eval, ev.nom_eval, ev.date_fin, c.nom_classe, ev.id_classe
            FROM Evaluation ev
            JOIN Classes c ON c.id_classe = ev.id_classe
            WHERE ev.id_prof = %s
            ORDER BY ev.date_fin DESC
            """,
            (prof_id,)
        )
    evals = cur.fetchall()

    for ev in evals:
        cur.execute(
            """
            SELECT u.id_user, u.nom, u.prenom,
                   n.id_note, n.note
            FROM Utilisateurs u
            LEFT JOIN Notes n ON n.id_eleve = u.id_user AND n.id_eval = %s
            WHERE u.id_classe = %s AND u.id_role = 3
            ORDER BY u.nom, u.prenom
            """,
            (ev["id_eval"], ev["id_classe"])
        )
        ev["eleves"] = cur.fetchall()

    cur.close()
    return render_template(
        "prof/notes.html",
        nom=session.get("nom"),
        prenom=session.get("prenom"),
        classes=classes,
        evals=evals,
        id_classe_filtre=id_classe_filtre,
    )


@prof_bp.route("/notes/attribuer", methods=["POST"])
@role_required(2)
def attribuer_note():
    prof_id  = get_prof_id()
    id_eval  = request.form.get("id_eval",  type=int)
    id_eleve = request.form.get("id_eleve", type=int)
    note_val = request.form.get("note",     type=float)
    id_note  = request.form.get("id_note",  type=int)

    if id_eval is None or id_eleve is None or note_val is None:
        flash("Données invalides.", "error")
        return redirect(url_for("prof.notes"))

    if note_val < 0 or note_val > 20:
        flash("La note doit être comprise entre 0 et 20.", "error")
        return redirect(url_for("prof.notes"))

    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("SELECT id_prof, id_classe FROM Evaluation WHERE id_eval = %s", (id_eval,))
    ev = cur.fetchone()
    if not ev or ev["id_prof"] != prof_id:
        flash("Action non autorisée.", "error")
        cur.close()
        return redirect(url_for("prof.notes"))

    cur.execute(
        "SELECT id_classe FROM Utilisateurs WHERE id_user = %s AND id_role = 3",
        (id_eleve,)
    )
    eleve = cur.fetchone()
    if not eleve or eleve["id_classe"] != ev["id_classe"]:
        flash("Élève non autorisé.", "error")
        cur.close()
        return redirect(url_for("prof.notes"))

    if id_note:
        cur.execute(
            "UPDATE Notes SET note = %s WHERE id_note = %s AND id_prof = %s",
            (note_val, id_note, prof_id)
        )
    else:
        cur.execute(
            "INSERT INTO Notes (id_eleve, id_prof, id_eval, note) VALUES (%s, %s, %s, %s)",
            (id_eleve, prof_id, id_eval, note_val)
        )

    db.commit()
    cur.close()
    flash("Note enregistrée.", "success")
    return redirect(url_for("prof.notes"))


# ── Emploi du temps ───────────────────────────────────────────────────────────

def _fmt_time(t):
    """Convertit un timedelta ou time MySQL en chaîne HH:MM."""
    if hasattr(t, "total_seconds"):
        s = int(t.total_seconds())
        return "%02d:%02d" % (s // 3600, (s % 3600) // 60)
    return t.strftime("%H:%M")


@prof_bp.route("/emploi-du-temps")
@role_required(2)
def emploi_du_temps():
    prof_id = get_prof_id()
    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute(
        """
        SELECT e.id_cours, e.date, e.heure_debut, e.heure_fin, e.salle,
               c.nom_classe, c.id_classe
        FROM Emploi_du_temps e
        JOIN Classes c ON c.id_classe = e.id_classe
        WHERE e.id_prof = %s
        ORDER BY e.date ASC, e.heure_debut ASC
        """,
        (prof_id,)
    )
    cours_list = cur.fetchall()
    cur.close()

    # Normalise les champs TIME en chaînes HH:MM
    for c in cours_list:
        c["hd_str"] = _fmt_time(c["heure_debut"])
        c["hf_str"] = _fmt_time(c["heure_fin"])

    # Créneaux uniques triés (hd_str, hf_str)
    creneaux_dict = {}
    for c in cours_list:
        creneaux_dict[c["hd_str"]] = c["hf_str"]
    creneaux = sorted(creneaux_dict.items())

    # Regroupement par semaine → jour (0=lun…4=ven) → créneau
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

    return render_template(
        "prof/emploi_du_temps.html",
        nom=session.get("nom"),
        prenom=session.get("prenom"),
        matiere=session.get("matiere"),
        semaines=semaines,
        creneaux=creneaux,
        jours_noms=["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"],
        today=date.today(),
    )
