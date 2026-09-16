"""
Script de seed pour la base de données EduLink.
Crée les rôles, classes, 1 admin, 6 profs, 9 élèves et un emploi du temps.
Les mots de passe sont générés aléatoirement et forts.

Usage :
    python seed.py           → seed sans credentials.txt
    python seed.py --creds   → seed + génération de credentials.txt
"""

import os
import sys
import secrets
import string
import bcrypt
import mysql.connector
from datetime import date, timedelta
from dotenv import load_dotenv

load_dotenv()

CREDENTIALS_FILE = "credentials.txt"
GENERER_CREDS = "--creds" in sys.argv


# ── Helpers ───────────────────────────────────────────────────────────────────

def generer_mdp(longueur: int = 14) -> str:
    """Génère un mot de passe aléatoire fort (CSPRNG) : majuscule, minuscule, chiffre, symbole."""
    alphabet = string.ascii_letters + string.digits + "!@#$%&*+-?"
    while True:
        mdp = "".join(secrets.choice(alphabet) for _ in range(longueur))
        if (any(c.isupper() for c in mdp)
                and any(c.islower() for c in mdp)
                and any(c.isdigit() for c in mdp)
                and any(c in "!@#$%&*+-?" for c in mdp)):
            return mdp


def hash_mdp(mdp: str) -> str:
    return bcrypt.hashpw(mdp.encode(), bcrypt.gensalt()).decode()


# ── Connexion ─────────────────────────────────────────────────────────────────

conn = mysql.connector.connect(
    host=os.getenv("MYSQL_HOST", "127.0.0.1"),
    port=int(os.getenv("MYSQL_PORT", "3306")),
    database=os.getenv("MYSQL_DATABASE"),
    user=os.getenv("MYSQL_USER"),
    password=os.getenv("MYSQL_PASSWORD"),
)
cur = conn.cursor()


# ── 1. Nettoyage ──────────────────────────────────────────────────────────────

cur.execute("DELETE FROM Notes")
cur.execute("DELETE FROM Evaluation")
cur.execute("DELETE FROM Emploi_du_temps")
cur.execute("DELETE FROM Prof_Classe")
cur.execute("DELETE FROM Utilisateurs")
cur.execute("DELETE FROM Classes")
cur.execute("DELETE FROM Roles")
cur.execute("ALTER TABLE Roles AUTO_INCREMENT = 1")
cur.execute("ALTER TABLE Classes AUTO_INCREMENT = 1")
cur.execute("ALTER TABLE Utilisateurs AUTO_INCREMENT = 1")


# ── 2. Rôles ──────────────────────────────────────────────────────────────────

roles = [(1, "Admin"), (2, "Professeur"), (3, "Eleve")]
cur.executemany("INSERT INTO Roles (id_role, nom_role) VALUES (%s, %s)", roles)
print("✓ Rôles insérés")


# ── 3. Classes ────────────────────────────────────────────────────────────────

classes = [(1, "2nde A"), (2, "1ère B"), (3, "Tle C")]
cur.executemany("INSERT INTO Classes (id_classe, nom_classe) VALUES (%s, %s)", classes)
print("✓ Classes insérées")


# ── 4. Admin ──────────────────────────────────────────────────────────────────

ADMIN_COMPTE = "admin"
ADMIN_MDP = generer_mdp()

cur.execute(
    """
    INSERT INTO Utilisateurs
        (id_role, compte, mdp, nom, prenom, matiere, id_classe)
    VALUES (%s, %s, %s, %s, %s, NULL, NULL)
    """,
    (1, ADMIN_COMPTE, hash_mdp(ADMIN_MDP), "Directeur", "Michel"),
)
print(f"✓ Admin inséré  (compte: {ADMIN_COMPTE})")


# ── 5. Professeurs ────────────────────────────────────────────────────────────

profs_data = [
    ("prof.martin",  "Martin",  "Sophie",   "Mathématiques"),
    ("prof.dubois",  "Dubois",  "Pierre",   "Français"),
    ("prof.bernard", "Bernard", "Claire",   "Histoire-Géographie"),
    ("prof.thomas",  "Thomas",  "Julien",   "Physique-Chimie"),
    ("prof.moreau",  "Moreau",  "Isabelle", "Sciences de la Vie et de la Terre"),
    ("prof.lefevre", "Lefèvre", "Antoine",  "Anglais"),
]

profs = []   # (compte, nom, prenom, matiere, mdp_clair, id_user)
prof_ids = []

for compte, nom, prenom, matiere in profs_data:
    mdp = generer_mdp()
    cur.execute(
        """
        INSERT INTO Utilisateurs
            (id_role, compte, mdp, nom, prenom, matiere, id_classe)
        VALUES (%s, %s, %s, %s, %s, %s, NULL)
        """,
        (2, compte, hash_mdp(mdp), nom, prenom, matiere),
    )
    uid = cur.lastrowid
    prof_ids.append(uid)
    profs.append((compte, nom, prenom, matiere, mdp, uid))

print(f"✓ {len(profs)} professeurs insérés")


# ── 6. Élèves ─────────────────────────────────────────────────────────────────

eleves_data = [
    ("eleve.lucas",   "Petit",     "Lucas",   1),
    ("eleve.camille", "Roux",      "Camille", 1),
    ("eleve.noah",    "Garnier",   "Noah",    1),
    ("eleve.lea",     "Morel",     "Léa",     2),
    ("eleve.maxime",  "Fontaine",  "Maxime",  2),
    ("eleve.ines",    "Benali",    "Inès",    2),
    ("eleve.hugo",    "Lemaire",   "Hugo",    3),
    ("eleve.manon",   "Girard",    "Manon",   3),
    ("eleve.theo",    "Blanchard", "Théo",    3),
]

eleves = []   # (compte, nom, prenom, id_classe, mdp_clair)

for compte, nom, prenom, id_classe in eleves_data:
    mdp = generer_mdp()
    cur.execute(
        """
        INSERT INTO Utilisateurs
            (id_role, compte, mdp, nom, prenom, matiere, id_classe)
        VALUES (%s, %s, %s, %s, %s, NULL, %s)
        """,
        (3, compte, hash_mdp(mdp), nom, prenom, id_classe),
    )
    eleves.append((compte, nom, prenom, id_classe, mdp))

print(f"✓ {len(eleves)} élèves insérés")


# ── 7. Liaison Prof <-> Classe ────────────────────────────────────────────────

prof_classe_liens = [
    (prof_ids[0], 1), (prof_ids[0], 2),   # Martin  (Maths)    → 2nde A, 1ère B
    (prof_ids[1], 1), (prof_ids[1], 3),   # Dubois  (Français) → 2nde A, Tle C
    (prof_ids[2], 2), (prof_ids[2], 3),   # Bernard (Hist-Géo) → 1ère B, Tle C
    (prof_ids[3], 1), (prof_ids[3], 2),   # Thomas  (Phy-Chi)  → 2nde A, 1ère B
    (prof_ids[4], 2), (prof_ids[4], 3),   # Moreau  (SVT)      → 1ère B, Tle C
    (prof_ids[5], 1), (prof_ids[5], 3),   # Lefèvre (Anglais)  → 2nde A, Tle C
]

cur.executemany(
    "INSERT INTO Prof_Classe (id_prof, id_classe) VALUES (%s, %s)",
    prof_classe_liens,
)
print(f"✓ {len(prof_classe_liens)} liens Prof-Classe insérés")


# ── 8. Emploi du temps ────────────────────────────────────────────────────────
# Génère 3 semaines de cours à partir de lundi prochain.
# Chaque prof a 2 créneaux par semaine par classe qu'il enseigne.

def prochain_lundi() -> date:
    today = date.today()
    jours_avant_lundi = today.weekday()   # 0 = lundi
    return today + timedelta(days=(7 - jours_avant_lundi) % 7 or 7)


CRENEAUX = [
    ("08:00", "09:00"),
    ("09:00", "10:00"),
    ("10:15", "11:15"),
    ("11:15", "12:15"),
    ("14:00", "15:00"),
    ("15:00", "16:00"),
    ("16:15", "17:15"),
]

SALLES = ["A101", "A102", "B201", "B202", "C301", "C302", "Amphi"]

# Programme hebdomadaire fixe : (prof_index, id_classe, jour_semaine 0=lun, créneau_index, salle_index)
PROGRAMME = [
    (0, 1, 0, 0, 0),   # Martin / Maths     / 2nde A / lundi    08h-09h / A101
    (0, 1, 2, 2, 0),   # Martin / Maths     / 2nde A / mercredi 10h15   / A101
    (0, 2, 1, 4, 1),   # Martin / Maths     / 1ère B / mardi    14h     / A102
    (0, 2, 3, 1, 1),   # Martin / Maths     / 1ère B / jeudi    09h     / A102

    (1, 1, 0, 4, 2),   # Dubois / Français  / 2nde A / lundi    14h     / B201
    (1, 1, 3, 0, 2),   # Dubois / Français  / 2nde A / jeudi    08h     / B201
    (1, 3, 1, 2, 3),   # Dubois / Français  / Tle C  / mardi    10h15   / B202
    (1, 3, 4, 5, 3),   # Dubois / Français  / Tle C  / vendredi 15h     / B202

    (2, 2, 0, 2, 4),   # Bernard / Hist-Géo / 1ère B / lundi    10h15   / C301
    (2, 2, 3, 4, 4),   # Bernard / Hist-Géo / 1ère B / jeudi    14h     / C301
    (2, 3, 2, 0, 5),   # Bernard / Hist-Géo / Tle C  / mercredi 08h     / C302
    (2, 3, 4, 2, 5),   # Bernard / Hist-Géo / Tle C  / vendredi 10h15   / C302

    (3, 1, 1, 0, 0),   # Thomas / Phy-Chi   / 2nde A / mardi    08h     / A101
    (3, 1, 4, 4, 0),   # Thomas / Phy-Chi   / 2nde A / vendredi 14h     / A101
    (3, 2, 2, 4, 6),   # Thomas / Phy-Chi   / 1ère B / mercredi 14h     / Amphi
    (3, 2, 4, 0, 6),   # Thomas / Phy-Chi   / 1ère B / vendredi 08h     / Amphi

    (4, 2, 1, 5, 4),   # Moreau / SVT       / 1ère B / mardi    15h     / C301
    (4, 2, 3, 2, 4),   # Moreau / SVT       / 1ère B / jeudi    10h15   / C301
    (4, 3, 0, 5, 5),   # Moreau / SVT       / Tle C  / lundi    15h     / C302
    (4, 3, 2, 6, 5),   # Moreau / SVT       / Tle C  / mercredi 16h15   / C302

    (5, 1, 2, 5, 1),   # Lefèvre / Anglais  / 2nde A / mercredi 15h     / A102
    (5, 1, 4, 6, 1),   # Lefèvre / Anglais  / 2nde A / vendredi 16h15   / A102
    (5, 3, 1, 6, 3),   # Lefèvre / Anglais  / Tle C  / mardi    16h15   / B202
    (5, 3, 3, 5, 3),   # Lefèvre / Anglais  / Tle C  / jeudi    15h     / B202
]

lundi = prochain_lundi()
cours_inseres = 0

for semaine in range(3):
    debut_semaine = lundi + timedelta(weeks=semaine)
    for prof_idx, id_classe, jour, creneau_idx, salle_idx in PROGRAMME:
        jour_date = debut_semaine + timedelta(days=jour)
        heure_debut, heure_fin = CRENEAUX[creneau_idx]
        salle = SALLES[salle_idx]
        cur.execute(
            """
            INSERT INTO Emploi_du_temps
                (id_classe, id_prof, salle, date, heure_debut, heure_fin)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (id_classe, prof_ids[prof_idx], salle, jour_date, heure_debut, heure_fin),
        )
        cours_inseres += 1

print(f"✓ {cours_inseres} cours insérés dans l'emploi du temps (3 semaines)")


# ── Fin DB ────────────────────────────────────────────────────────────────────

conn.commit()
cur.close()
conn.close()


# ── 9. Génération de credentials.txt (optionnel) ──────────────────────────────

if GENERER_CREDS:
    if os.path.exists(CREDENTIALS_FILE):
        os.remove(CREDENTIALS_FILE)

    lines = []
    lines.append("=" * 64)
    lines.append("  EDULINK — CREDENTIALS DE TEST")
    lines.append("  /!\\ Fichier confidentiel — ne pas committer")
    lines.append("=" * 64)

    lines.append("")
    lines.append("── CLASSES ──────────────────────────────────────────────────────")
    for id_c, nom_c in classes:
        lines.append(f"  [{id_c}] {nom_c}")

    lines.append("")
    lines.append("── COMPTE ADMIN ─────────────────────────────────────────────────")
    lines.append(f"  Compte  : {ADMIN_COMPTE}")
    lines.append(f"  Mdp     : {ADMIN_MDP}")
    lines.append(f"  Nom     : Michel Directeur")

    lines.append("")
    lines.append("── COMPTES PROFESSEURS ──────────────────────────────────────────")
    lines.append(f"  {'Compte':<22} {'Nom':<12} {'Prénom':<10} {'Matière':<36} Mdp")
    lines.append(f"  {'-'*22} {'-'*12} {'-'*10} {'-'*36} {'-'*14}")
    for compte, nom, prenom, matiere, mdp, _ in profs:
        lines.append(f"  {compte:<22} {nom:<12} {prenom:<10} {matiere:<36} {mdp}")

    lines.append("")
    lines.append("── COMPTES ÉLÈVES ───────────────────────────────────────────────")
    lines.append(f"  {'Compte':<22} {'Nom':<12} {'Prénom':<10} {'Classe':<10} Mdp")
    lines.append(f"  {'-'*22} {'-'*12} {'-'*10} {'-'*10} {'-'*14}")
    for compte, nom, prenom, id_classe, mdp in eleves:
        nom_classe = next(n for i, n in classes if i == id_classe)
        lines.append(f"  {compte:<22} {nom:<12} {prenom:<10} {nom_classe:<10} {mdp}")

    lines.append("")
    lines.append("── AFFECTATIONS PROF → CLASSES ──────────────────────────────────")
    for i, (compte, nom, prenom, matiere, _, _) in enumerate(profs):
        classes_du_prof = [
            next(n for ci, n in classes if ci == id_c)
            for pid, id_c in prof_classe_liens
            if pid == prof_ids[i]
        ]
        lines.append(f"  {prenom} {nom} ({matiere}) → {', '.join(classes_du_prof)}")

    lines.append("")
    lines.append("=" * 64)
    lines.append("  Fichier regénéré à chaque exécution de seed.py --creds")
    lines.append("=" * 64)

    with open(CREDENTIALS_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"\n✓ Fichier '{CREDENTIALS_FILE}' généré")
else:
    print("\n(credentials.txt non généré — relancer avec --creds pour l'obtenir)")

print("\n=== Seed terminé avec succès ! ===")
