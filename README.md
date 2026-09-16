# Edulink
Voici le repo pour l'application EduLink du projet DevSecOps en B2 au sein de la Guardia Cybersecurity School

Plateforme de gestion scolaire développée dans le cadre d'un projet DevSecOps (Guardia GCS2).  
Elle permet à un administrateur de gérer classes, utilisateurs et emplois du temps ; aux professeurs de gérer évaluations et notes ; aux élèves de consulter leurs résultats.

## Stack technique

| Composant | Technologie |
|-----------|-------------|
| Backend | Python 3.11 · Flask 3 · Flask-WTF (CSRF) |
| Base de données | MySQL 8.0 |
| Authentification | bcrypt · sessions sécurisées (HttpOnly, SameSite=Strict) · Flask-Limiter (brute-force) |
| Conteneurisation | Docker · Docker Compose |
| CI/CD | GitHub Actions (Gitleaks · Flake8 · pip-audit · Trivy · OWASP ZAP) |

## Installation

### Prérequis

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installé et lancé
- Git

### 1. Cloner le dépôt

```bash
git clone https://github.com/Foxoni/EduLink.git
cd EduLink
```

### 2. Créer le fichier `.env`

Copier le fichier d'exemple et renseigner les valeurs :

```bash
cp .env.example .env
```

Éditer `.env` :

```env
MYSQL_ROOT_PASSWORD=<mot_de_passe_root_fort>
MYSQL_DATABASE=EduLink
MYSQL_USER=dev_user
MYSQL_PASSWORD=<mot_de_passe_user_fort>
FLASK_SECRET_KEY=<chaine_aleatoire_longue_min_32_caracteres>
```

> Pour générer une `FLASK_SECRET_KEY` : `python -c "import secrets; print(secrets.token_hex(32))"`

### 3. Lancer les conteneurs

```bash
docker compose up -d --build
```

Docker va :
1. Démarrer MySQL 8.0 et exécuter `init.sql` (création des tables)
2. Construire l'image Flask et démarrer Gunicorn sur le port `5000`
3. Attendre que MySQL soit prêt avant de démarrer Flask (healthcheck)

Vérifier que tout est en ordre :

```bash
docker compose ps
docker compose logs app
```

### 4. Peupler la base de données (seed)

Le script `seed.py` crée les rôles, classes, 1 admin, 6 professeurs, 9 élèves et 3 semaines de cours dans l'emploi du temps. Les mots de passe sont générés aléatoirement.

**Sans** générer de fichier de credentials :

```bash
docker compose exec app python seed.py
```

**Avec** génération du fichier `credentials.txt` (comptes et mots de passe en clair) :

```bash
docker compose exec app python seed.py --creds
```

> `credentials.txt` est ignoré par Git (`.gitignore`). Ne jamais le committer.

Le fichier `credentials.txt` contient la liste complète des comptes générés avec leurs mots de passe. Il est régénéré à chaque exécution de `seed.py --creds`.

### 5. Accéder à l'application

Ouvrir [http://localhost:5000](http://localhost:5000) dans un navigateur.

---

### Installation sans Docker (développement local)

```bash
python -m venv venv
source venv/bin/activate        # Windows : venv\Scripts\activate
pip install -r requirements.txt

# Renseigner .env avec MYSQL_HOST=127.0.0.1 pointant vers un MySQL local
python app.py
```

---

## Structure du projet

```
EduLink/
├── app.py                  # Point d'entrée Flask
├── extensions.py           # Instances partagées (Flask-Limiter)
├── db.py                   # Connexion MySQL (flask.g)
├── decorators.py           # @login_required, @role_required
├── init.sql                # Schéma de la base de données
├── seed.py                 # Données de démonstration
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── blueprints/
│   ├── auth/               # Login / logout
│   ├── admin/              # Gestion classes, utilisateurs, planning
│   ├── prof/               # Évaluations, notes, emploi du temps
│   └── eleve/              # Tableau de bord élève
├── templates/
│   ├── admin/
│   ├── prof/
│   └── eleve/
└── static/
    ├── css/                # style.css · prof.css · eleve.css
    └── js/                 # admin_emploi.js · admin_utilisateurs.js
```

---

## Règles d'engagement — Pentest

Ce document définit les conditions dans lesquelles des tests de sécurité peuvent être menés sur EduLink. Toute activité de test doit rester dans le périmètre défini ci-dessous.

### Périmètre autorisé

- Application web sur `http://localhost:5000` (instance locale ou de test dédiée)
- Base de données MySQL accessible sur le port `3306` de l'environnement de test

**Hors périmètre** : toute infrastructure de production, comptes tiers, systèmes non listés ci-dessus.

---

### Mode Black Box

> Le testeur n'a **aucune connaissance préalable** du système.

**Accès fournis :**
- URL de l'application uniquement
- Aucun compte, aucun code source, aucun fichier de configuration

**Objectifs typiques :**
- Découverte de la surface d'attaque (enumération des routes, formulaires)
- Tentatives d'authentification (brute-force, credentials par défaut)
- Injection SQL/XSS/CSRF sans connaissance de la structure interne
- Analyse des headers HTTP et des cookies

**Restrictions :**
- Ne pas utiliser `credentials.txt` ni aucune information issue du code source
- Ne pas provoquer d'interruption de service (pas de DoS)

---

### Mode Gray Box

> Le testeur dispose d'**un accès utilisateur légitime** et du fichier `credentials.txt`.

**Accès fournis :**
- `credentials.txt` généré par `seed.py --creds` (utilisé seulement les comptes eleve ou prof)

**Objectifs typiques :**
- Escalade de privilèges (accès à des routes d'un rôle supérieur)
- Manipulation de paramètres (IDOR, forged form fields)
- Tests d'autorisation inter-utilisateurs (accès aux notes/évaluations d'un autre prof)
- Bypass de protection CSRF
- Tests de session (fixation, vol, expiration)

**Restrictions :**
- Utiliser uniquement les comptes listés dans `credentials.txt` ou des comptes créer a la main via le site si réussie — pas de comptes de production
- Ne pas modifier les données de façon irréversible (préférer un environnement jetable)
- Ne pas utiliser les variables d'environnement `.env` ni les clés secrètes

---

### Mode White Box

> Le testeur a **accès complet** : code source, configuration, secrets.

**Accès fournis :**
- Intégralité du code source
- Fichier `.env` avec toutes les clés (SECRET_KEY, mots de passe MySQL)
- `credentials.txt`
- Accès direct à la base de données MySQL
- Pipeline CI/CD (`.github/workflows/`)

**Objectifs typiques :**
- Audit complet du code (revue manuelle + outils SAST)
- Analyse de la configuration Docker et des droits conteneur
- Vérification de la robustesse du hashage bcrypt et de la gestion des sessions
- Test de la chaîne CI/CD (injection dans la pipeline, secrets exposés)
- Vérification de la Content Security Policy et des headers HTTP
- Analyse des requêtes SQL (recherche de concaténations non paramétrées)

**Restrictions :**
- Ne pas exfiltrer les clés ou secrets en dehors de l'environnement de test
- Ne pas pousser de code malveillant sur le dépôt
- Tout accès doit être tracé et documenté

---

### Règles communes à tous les modes

| Règle | Détail |
|-------|--------|
| Environnement isolé | Tester uniquement sur une instance locale ou un environnement de test dédié — jamais en production |
| Non-destructif | Pas de suppression de données, pas d'altération irréversible de la base |
| Pas de DoS | Aucune attaque visant à rendre le service indisponible |
| Traçabilité | Chaque test doit être documenté dans un rapport |
| Périmètre strict | Ne pas pivoter vers d'autres systèmes du réseau local |
| Nettoyage | Supprimer tout artefact créé pendant les tests (comptes, fichiers, entrées BDD) à l'issue du pentest |

