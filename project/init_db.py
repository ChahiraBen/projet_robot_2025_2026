import sqlite3

DB_NAME = "database.db"

schema_sql = """
DROP TABLE IF EXISTS Medecin;
DROP TABLE IF EXISTS Pharmacie;
DROP TABLE IF EXISTS Service;
DROP TABLE IF EXISTS Hopital;

CREATE TABLE Hopital (
    id_hopital INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL,
    num_tel TEXT NOT NULL,
    adresse TEXT NOT NULL
);

CREATE TABLE Service (
    id_service INTEGER PRIMARY KEY AUTOINCREMENT,
    nom_service TEXT NOT NULL UNIQUE,
    id_hopital INTEGER NOT NULL,
    etage INTEGER NOT NULL,
    horaire TEXT NOT NULL,
    batiment TEXT NOT NULL,
    FOREIGN KEY (id_hopital) REFERENCES Hopital(id_hopital)
);

CREATE TABLE Medecin (
    id_medecin INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL,
    id_service INTEGER NOT NULL,
    horaire TEXT,
    photo TEXT,
    bureau TEXT,
    FOREIGN KEY (id_service) REFERENCES Service(id_service)
);

CREATE TABLE Pharmacie (
    id_phar INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL,
    adresse TEXT NOT NULL,
    distance REAL NOT NULL,
    horaire TEXT NOT NULL
);
"""

conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

cursor.executescript(schema_sql)

cursor.execute("""
INSERT INTO Hopital (nom, num_tel, adresse)
VALUES (?, ?, ?)
""", ("Centre Hospitalier Avignon", "04 90 00 00 00", "305 Rue Raoul Follereau, Avignon"))

services = [
    ("cardiologie", 1, 2, "08:00-17:00", "A"),
    ("radiologie", 1, 1, "08:30-18:00", "B"),
    ("urgences", 1, 0, "24h/24", "C"),
    ("admissions", 1, 0, "08:00-16:30", "A"),
    ("pediatrie", 1, 3, "08:00-17:00", "B"),
    ("laboratoire", 1, 1, "07:30-16:00", "A")
]

cursor.executemany("""
INSERT INTO Service (nom_service, id_hopital, etage, horaire, batiment)
VALUES (?, ?, ?, ?, ?)
""", services)

medecins = [
    ("Martin", 1, "09:00-16:00", None, "Bureau 201"),
    ("Dupont", 2, "10:00-17:00", None, "Bureau 105"),
    ("Bernard", 3, "24h/24", None, "Salle U3"),
    ("Petit", 5, "09:00-15:00", None, "Bureau 302")
]

cursor.executemany("""
INSERT INTO Medecin (nom, id_service, horaire, photo, bureau)
VALUES (?, ?, ?, ?, ?)
""", medecins)

pharmacies = [
    ("Pharmacie Centrale", "12 rue Victor Hugo, Avignon", 0.4, "08:30-19:30"),
    ("Pharmacie République", "25 boulevard République, Avignon", 0.8, "09:00-19:00"),
    ("Pharmacie Saint-Roch", "8 avenue Saint-Roch, Avignon", 1.2, "08:00-20:00")
]

cursor.executemany("""
INSERT INTO Pharmacie (nom, adresse, distance, horaire)
VALUES (?, ?, ?, ?)
""", pharmacies)

conn.commit()
conn.close()

print("Base de données initialisée avec succès.")