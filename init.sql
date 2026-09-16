-- Création de la base de données (si elle n'existe pas déjà)
CREATE DATABASE IF NOT EXISTS EduLink;
USE EduLink;

-- 1. Table des rôles (Créée en premier car sans dépendance)
CREATE TABLE Roles (
    id_role INT AUTO_INCREMENT PRIMARY KEY,
    nom_role VARCHAR(50) NOT NULL COMMENT '''Admin'', ''Professeur'' ou ''Eleve'''
);

-- 2. Table des classes (Créée avant Utilisateurs car un élève y fait référence)
CREATE TABLE Classes (
    id_classe INT AUTO_INCREMENT PRIMARY KEY,
    nom_classe VARCHAR(100) NOT NULL COMMENT 'Ex: DevSecOps GCS2'
);

-- 3. Table unifiée des utilisateurs
CREATE TABLE Utilisateurs (
    id_user INT AUTO_INCREMENT PRIMARY KEY,
    id_role INT NOT NULL,
    compte VARCHAR(150) UNIQUE NOT NULL COMMENT 'Email ou pseudo',
    mdp VARCHAR(255) NOT NULL COMMENT 'Sera haché (bcrypt)',
    nom VARCHAR(100) NOT NULL,
    prenom VARCHAR(100) NOT NULL,
    matiere VARCHAR(100) NULL COMMENT 'Rempli uniquement si c est un prof',
    id_classe INT NULL COMMENT 'Rempli uniquement si c est un élève',
    FOREIGN KEY (id_role) REFERENCES Roles(id_role) ON DELETE RESTRICT,
    FOREIGN KEY (id_classe) REFERENCES Classes(id_classe) ON DELETE SET NULL
);

-- 4. Table de liaison Professeur <-> Classe
CREATE TABLE Prof_Classe (
    id_prof INT NOT NULL,
    id_classe INT NOT NULL,
    PRIMARY KEY (id_prof, id_classe),
    FOREIGN KEY (id_prof) REFERENCES Utilisateurs(id_user) ON DELETE CASCADE,
    FOREIGN KEY (id_classe) REFERENCES Classes(id_classe) ON DELETE CASCADE
);

-- 5. Table Emploi du temps
CREATE TABLE Emploi_du_temps (
    id_cours INT AUTO_INCREMENT PRIMARY KEY,
    id_classe INT NOT NULL,
    id_prof INT NOT NULL,
    salle VARCHAR(50),
    date DATE NOT NULL,
    heure_debut TIME NOT NULL,
    heure_fin TIME NOT NULL,
    FOREIGN KEY (id_classe) REFERENCES Classes(id_classe) ON DELETE CASCADE,
    FOREIGN KEY (id_prof) REFERENCES Utilisateurs(id_user) ON DELETE CASCADE
);

-- 6. Tableau projet/evaluation
CREATE TABLE Evaluation (
    id_eval INT AUTO_INCREMENT PRIMARY KEY,
    id_prof INT NOT NULL,
    id_classe INT NOT NULL,
    nom_eval VARCHAR(150) NOT NULL,
    description TEXT,
    date_fin DATE NOT NULL,
    FOREIGN KEY (id_prof) REFERENCES Utilisateurs(id_user) ON DELETE CASCADE,
    FOREIGN KEY (id_classe) REFERENCES Classes(id_classe) ON DELETE CASCADE
);

-- 7. Tableau des notes (Version Hybride)
CREATE TABLE Notes (
    id_note INT AUTO_INCREMENT PRIMARY KEY,
    id_eleve INT NOT NULL,
    id_prof INT NOT NULL COMMENT 'Toujours nécessaire pour savoir qui a noté',
    id_eval INT NULL COMMENT 'Peut être NULL si note indépendante',
    nom_note VARCHAR(150) NULL COMMENT 'Rempli uniquement si note indépendante (ex: Bonus)',
    note FLOAT NOT NULL,
    FOREIGN KEY (id_eleve) REFERENCES Utilisateurs(id_user) ON DELETE CASCADE,
    FOREIGN KEY (id_prof) REFERENCES Utilisateurs(id_user) ON DELETE CASCADE,
    FOREIGN KEY (id_eval) REFERENCES Evaluation(id_eval) ON DELETE CASCADE
);