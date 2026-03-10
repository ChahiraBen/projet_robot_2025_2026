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