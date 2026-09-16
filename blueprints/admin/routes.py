"""
Blueprint admin — espace réservé aux administrateurs (id_role = 1).
Toute route de ce blueprint exige @role_required(1).
"""

import logging

import bcrypt
from datetime import date, timedelta

from flask import Blueprint, render_template, session, request, redirect, url_for, flash
from decorators import role_required
from db import get_db

logger = logging.getLogger(__name__)

admin_bp = Blueprint("admin", __name__, url_prefix="/admin",
                     template_folder="../../templates/admin")


# ── Accueil admin ──────────────────────────────────────────────────────────────
@admin_bp.route("/dashboard")
@role_required(1)
def dashboard():
    return render_template("admin/dashboard.html",
                           nom=session.get("nom"),
                           prenom=session.get("prenom"))


# ── Gestion des classes ────────────────────────────────────────────────────────
@admin_bp.route("/classes")
@role_required(1)
def classes_page():
    classes = []
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT id_classe, nom_classe FROM Classes")
        classes = cursor.fetchall()
    except Exception as e:
        logger.error("classes_page: %s", e)
        flash("Une erreur interne s'est produite.", "danger")
    return render_template("admin/classe.html", classes=classes)


@admin_bp.route("/add-class", methods=["POST"])
@role_required(1)
def add_class():
    nom = request.form.get("nom_classe", "").strip()
    if not nom or len(nom) > 100:
        flash("Nom de classe invalide (1–100 caractères).", "danger")
        return redirect(url_for("admin.classes_page"))
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("INSERT INTO Classes (nom_classe) VALUES (%s)", (nom,))
        db.commit()
        flash(f"Classe '{nom}' ajoutée avec succès !", "success")
    except Exception as e:
        logger.error("add_class: %s", e)
        flash("Une erreur interne s'est produite.", "danger")
    return redirect(url_for("admin.classes_page"))


@admin_bp.route("/delete-class/<int:id_classe>", methods=["POST"])
@role_required(1)
def delete_class(id_classe):
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("DELETE FROM Classes WHERE id_classe = %s", (id_classe,))
        db.commit()
        flash("Classe supprimée avec succès.", "success")
    except Exception as e:
        logger.error("delete_class id=%s: %s", id_classe, e)
        flash("Une erreur interne s'est produite.", "danger")
    return redirect(url_for("admin.classes_page"))


# ── Gestion des utilisateurs ───────────────────────────────────────────────────
@admin_bp.route("/utilisateurs")
@role_required(1)
def user_page():
    users, roles, classes = [], [], []
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT u.*, r.nom_role, c.nom_classe
            FROM Utilisateurs u
            JOIN Roles r ON u.id_role = r.id_role
            LEFT JOIN Classes c ON u.id_classe = c.id_classe
        """)
        users = cursor.fetchall()
        cursor.execute("SELECT * FROM Roles")
        roles = cursor.fetchall()
        cursor.execute("SELECT * FROM Classes")
        classes = cursor.fetchall()
    except Exception as e:
        logger.error("user_page: %s", e)
        flash("Une erreur interne s'est produite.", "danger")
    return render_template("admin/utilisateur.html",
                           users=users, roles=roles, classes=classes)


@admin_bp.route("/add-user", methods=["POST"])
@role_required(1)
def add_user():
    nom       = (request.form.get("nom")      or "").strip()
    prenom    = (request.form.get("prenom")   or "").strip()
    compte    = (request.form.get("compte")   or "").strip()
    mdp       = request.form.get("mdp", "")
    id_role   = request.form.get("id_role",   "").strip()
    matiere   = (request.form.get("matiere")  or "").strip()
    id_classe = (request.form.get("id_classe") or "").strip()

    # ── Validation ────────────────────────────────────────────────
    if not nom or not prenom or not compte or not mdp or not id_role:
        flash("Tous les champs obligatoires doivent être remplis.", "danger")
        return redirect(url_for("admin.user_page"))
    if len(nom) > 100 or len(prenom) > 100:
        flash("Nom ou prénom trop long (100 caractères max).", "danger")
        return redirect(url_for("admin.user_page"))
    if len(compte) > 150:
        flash("Identifiant trop long (150 caractères max).", "danger")
        return redirect(url_for("admin.user_page"))
    if len(mdp) < 8:
        flash("Le mot de passe doit faire au moins 8 caractères.", "danger")
        return redirect(url_for("admin.user_page"))
    if id_role not in ("1", "2", "3"):
        flash("Rôle invalide.", "danger")
        return redirect(url_for("admin.user_page"))

    val_matiere = matiere   or None
    val_classe  = id_classe or None

    try:
        hashed = bcrypt.hashpw(mdp.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO Utilisateurs (id_role, compte, mdp, nom, prenom, matiere, id_classe)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (id_role, compte, hashed, nom, prenom, val_matiere, val_classe))
        db.commit()
        flash(f"L'utilisateur {prenom} {nom} a été créé avec succès !", "success")
    except Exception as e:
        if "Duplicate entry" in str(e):
            flash("Ce compte existe déjà.", "danger")
        else:
            logger.error("add_user: %s", e)
            flash("Une erreur interne s'est produite.", "danger")
    return redirect(url_for("admin.user_page"))


@admin_bp.route("/update-user-class", methods=["POST"])
@role_required(1)
def update_user_class():
    id_user   = request.form.get("id_user")
    id_classe = (request.form.get("id_classe") or "").strip()
    val_classe = id_classe or None
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "UPDATE Utilisateurs SET id_classe = %s WHERE id_user = %s",
            (val_classe, id_user)
        )
        db.commit()
        flash("Classe de l'utilisateur modifiée avec succès.", "success")
    except Exception as e:
        logger.error("update_user_class user=%s: %s", id_user, e)
        flash("Une erreur interne s'est produite.", "danger")
    return redirect(url_for("admin.user_page"))


@admin_bp.route("/delete-user/<int:id_user>", methods=["POST"])
@role_required(1)
def delete_user(id_user):
    if id_user == session.get("user_id"):
        flash("Vous ne pouvez pas supprimer votre propre compte.", "danger")
        return redirect(url_for("admin.user_page"))
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("DELETE FROM Utilisateurs WHERE id_user = %s", (id_user,))
        db.commit()
        flash("Utilisateur supprimé avec succès.", "success")
    except Exception as e:
        logger.error("delete_user id=%s: %s", id_user, e)
        flash("Une erreur interne s'est produite.", "danger")
    return redirect(url_for("admin.user_page"))


# ── Emploi du temps ────────────────────────────────────────────────────────────
def _fmt_time(t):
    """Convertit un timedelta ou time MySQL en chaîne HH:MM."""
    if hasattr(t, "total_seconds"):
        s = int(t.total_seconds())
        return "%02d:%02d" % (s // 3600, (s % 3600) // 60)
    return t.strftime("%H:%M")


@admin_bp.route("/emploi-du-temps")
@role_required(1)
def emploi_page():
    class_id = request.args.get("classe_id")
    classes, semaines, creneaux, profs, current_classe = [], [], [], [], None
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT id_classe, nom_classe FROM Classes")
        classes = cursor.fetchall()

        if class_id:
            cursor.execute(
                "SELECT id_classe, nom_classe FROM Classes WHERE id_classe = %s",
                (class_id,)
            )
            current_classe = cursor.fetchone()

            cursor.execute("""
                SELECT e.id_cours, e.date, e.heure_debut, e.heure_fin, e.salle,
                       u.nom, u.prenom, u.matiere
                FROM Emploi_du_temps e
                JOIN Utilisateurs u ON e.id_prof = u.id_user
                WHERE e.id_classe = %s
                ORDER BY e.date, e.heure_debut
            """, (class_id,))
            cours_list = cursor.fetchall()

            # Normalise les champs TIME en chaînes HH:MM
            for c in cours_list:
                c["hd_str"] = _fmt_time(c["heure_debut"])
                c["hf_str"] = _fmt_time(c["heure_fin"])

            # Créneaux uniques triés
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

            cursor.execute(
                "SELECT id_user, nom, prenom, matiere FROM Utilisateurs WHERE id_role = 2"
            )
            profs = cursor.fetchall()

    except Exception as e:
        logger.error("emploi_page: %s", e)
        flash("Une erreur interne s'est produite.", "danger")

    return render_template(
        "admin/emploi.html",
        classes=classes,
        semaines=semaines,
        creneaux=creneaux,
        current_classe=current_classe,
        profs=profs,
        jours_noms=["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"],
        today=date.today(),
    )


@admin_bp.route("/add-cours", methods=["POST"])
@role_required(1)
def add_cours():
    id_classe   = request.form.get("id_classe",   "").strip()
    id_prof     = request.form.get("id_prof",     "").strip()
    date_cours  = request.form.get("date",        "").strip()
    salle       = (request.form.get("salle") or "").strip()
    heure_debut = request.form.get("heure_debut", "").strip()
    heure_fin   = request.form.get("heure_fin",   "").strip()

    if not all([id_classe, id_prof, date_cours, heure_debut, heure_fin]):
        flash("Tous les champs obligatoires doivent être remplis.", "danger")
        return redirect(url_for("admin.emploi_page", classe_id=id_classe))

    if heure_debut >= heure_fin:
        flash("L'heure de début doit être antérieure à l'heure de fin.", "danger")
        return redirect(url_for("admin.emploi_page", classe_id=id_classe))

    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        # Validation : id_prof doit être un professeur (role=2)
        cursor.execute(
            "SELECT id_user FROM Utilisateurs WHERE id_user = %s AND id_role = 2",
            (id_prof,)
        )
        if not cursor.fetchone():
            flash("Intervenant invalide.", "danger")
            return redirect(url_for("admin.emploi_page", classe_id=id_classe))

        # Conflit de créneau pour la classe
        cursor.execute("""
            SELECT id_cours FROM Emploi_du_temps
            WHERE id_classe = %s AND date = %s
            AND (heure_debut < %s AND heure_fin > %s)
        """, (id_classe, date_cours, heure_fin, heure_debut))
        if cursor.fetchone():
            flash("Conflit : la classe a déjà un cours sur ce créneau !", "danger")
            return redirect(url_for("admin.emploi_page", classe_id=id_classe))

        # Conflit de salle (F3)
        if salle:
            cursor.execute("""
                SELECT id_cours FROM Emploi_du_temps
                WHERE salle = %s AND date = %s
                AND (heure_debut < %s AND heure_fin > %s)
            """, (salle, date_cours, heure_fin, heure_debut))
            if cursor.fetchone():
                flash(f"Conflit : la salle {salle} est déjà occupée sur ce créneau !", "danger")
                return redirect(url_for("admin.emploi_page", classe_id=id_classe))

        cursor.execute("""
            INSERT INTO Emploi_du_temps (id_classe, id_prof, salle, date, heure_debut, heure_fin)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (id_classe, id_prof, salle or None, date_cours, heure_debut, heure_fin))
        db.commit()
        flash("Cours ajouté avec succès au planning.", "success")
    except Exception as e:
        logger.error("add_cours: %s", e)
        flash("Une erreur interne s'est produite.", "danger")
    return redirect(url_for("admin.emploi_page", classe_id=id_classe))


@admin_bp.route("/delete-cours/<int:id_cours>", methods=["POST"])
@role_required(1)
def delete_cours(id_cours):
    classe_id = request.form.get("classe_id")
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("DELETE FROM Emploi_du_temps WHERE id_cours = %s", (id_cours,))
        db.commit()
        flash("Cours supprimé avec succès.", "success")
    except Exception as e:
        logger.error("delete_cours id=%s: %s", id_cours, e)
        flash("Une erreur interne s'est produite.", "danger")
    return redirect(url_for("admin.emploi_page", classe_id=classe_id))
