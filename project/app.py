from flask import Flask, request, jsonify, render_template
import sqlite3
import unicodedata
import re

app = Flask(__name__)
DATABASE = "database.db"


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def strip_accents(text):
    return ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )


def normalize_text(text):
    text = text.lower().strip()
    text = strip_accents(text)
    return text


KNOWN_SERVICES = [
    "cardiologie",
    "radiologie",
    "urgences",
    "admissions",
    "pediatrie",
    "laboratoire"
]

SERVICE_ALIASES = {
    "cardiologue": "cardiologie",
    "cardio": "cardiologie",
    "radiologue": "radiologie",
    "radiologie": "radiologie",
    "urgentiste": "urgences",
    "urgence": "urgences",
    "urgences": "urgences",
    "pediatre": "pediatrie",
    "pédiatre": "pediatrie",
    "enfant": "pediatrie",
    "admission": "admissions",
    "laboratoire": "laboratoire",
    "labo": "laboratoire"
}

def extract_service_name(message):
    msg = normalize_text(message)

    # 1) correspondance directe service exact
    for service in KNOWN_SERVICES:
        if service in msg:
            return service

    # 2) correspondance via alias / spécialité
    for alias, service in SERVICE_ALIASES.items():
        if normalize_text(alias) in msg:
            return service

    return None


def extract_doctor_name(message):
    match = re.search(r"(?:docteur|dr|medecin)\s+([a-zA-ZÀ-ÿ\-]+)", message, re.IGNORECASE)
    if match:
        return match.group(1).strip().title()
    return None


def detect_intent(message):
    msg = normalize_text(message)

    if any(word in msg for word in ["bonjour", "salut", "bonsoir"]):
        return "salutation"

    if any(expr in msg for expr in ["au revoir", "a bientot", "bye"]):
        return "au_revoir"

    if "pharmacie" in msg:
        return "information_pharmacie"

    if any(word in msg for word in ["telephone", "contact", "numero", "appeler"]):
        return "contact_service"

    if any(word in msg for word in ["horaire", "horaires", "ouvre", "ferme"]):
        return "horaires_service"

    if any(word in msg for word in ["docteur", "dr", "medecin"]):
        return "localisation_medecin"

    if any(word in msg for word in ["ou", "trouve", "localisation", "aller", "service"]):
        return "localisation_service"

    return "inconnu"


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/services", methods=["GET"])
def get_services():
    conn = get_db_connection()
    rows = conn.execute("""
        SELECT id_service, nom_service, etage, horaire, batiment
        FROM Service
        ORDER BY nom_service
    """).fetchall()
    conn.close()

    return jsonify([dict(row) for row in rows])


@app.route("/api/pharmacies", methods=["GET"])
def get_pharmacies():
    conn = get_db_connection()
    rows = conn.execute("""
        SELECT nom, adresse, distance, horaire
        FROM Pharmacie
        ORDER BY distance ASC
    """).fetchall()
    conn.close()

    return jsonify([dict(row) for row in rows])


@app.route("/api/chat", methods=["POST"])
def chat():
    payload = request.get_json(silent=True) or {}
    message = payload.get("message", "").strip()

    if not message:
        return jsonify({
            "intent": "inconnu",
            "response": "Votre message est vide."
        }), 400

    intent = detect_intent(message)
    conn = get_db_connection()

    if intent == "salutation":
        conn.close()
        return jsonify({
            "intent": intent,
            "response": "Bonjour, comment puis-je vous aider ?"
        })

    elif intent == "au_revoir":
        conn.close()
        return jsonify({
            "intent": intent,
            "response": "Au revoir et bon courage."
        })

    elif intent == "localisation_service":
        nom_service = extract_service_name(message)

        if not nom_service:
            conn.close()
            return jsonify({
                "intent": intent,
                "response": "Pouvez-vous préciser le nom du service recherché ?"
            })

        row = conn.execute("""
            SELECT nom_service, etage, batiment, horaire
            FROM Service
            WHERE lower(nom_service) = lower(?)
        """, (nom_service,)).fetchone()

        conn.close()

        if not row:
            return jsonify({
                "intent": intent,
                "response": "Je n'ai pas trouvé ce service."
            })

        return jsonify({
            "intent": intent,
            "response": f"Le service de {row['nom_service']} se trouve au {row['etage']}e étage du bâtiment {row['batiment']}.",
            "data": dict(row)
        })

    elif intent == "horaires_service":
        nom_service = extract_service_name(message)

        if not nom_service:
            conn.close()
            return jsonify({
                "intent": intent,
                "response": "Pouvez-vous préciser le service dont vous voulez les horaires ?"
            })

        row = conn.execute("""
            SELECT nom_service, horaire
            FROM Service
            WHERE lower(nom_service) = lower(?)
        """, (nom_service,)).fetchone()

        conn.close()

        if not row:
            return jsonify({
                "intent": intent,
                "response": "Je n'ai pas trouvé les horaires de ce service."
            })

        return jsonify({
            "intent": intent,
            "response": f"Les horaires du service de {row['nom_service']} sont : {row['horaire']}.",
            "data": dict(row)
        })

    elif intent == "localisation_medecin":
        nom_medecin = extract_doctor_name(message)

        if not nom_medecin:
            conn.close()
            return jsonify({
                "intent": intent,
                "response": "Pouvez-vous préciser le nom du médecin ?"
            })

        row = conn.execute("""
            SELECT Medecin.nom, Medecin.bureau, Medecin.horaire,
                   Service.nom_service, Service.etage, Service.batiment
            FROM Medecin
            JOIN Service ON Medecin.id_service = Service.id_service
            WHERE lower(Medecin.nom) = lower(?)
        """, (nom_medecin,)).fetchone()

        conn.close()

        if not row:
            return jsonify({
                "intent": intent,
                "response": f"Je n'ai pas trouvé le docteur {nom_medecin}."
            })

        return jsonify({
            "intent": intent,
            "response": (
                f"Le docteur {row['nom']} est rattaché au service de {row['nom_service']}, "
                f"au {row['etage']}e étage du bâtiment {row['batiment']}, {row['bureau']}."
            ),
            "data": dict(row)
        })

    elif intent == "contact_service":
        nom_service = extract_service_name(message)

        if not nom_service:
            conn.close()
            return jsonify({
                "intent": intent,
                "response": "Pouvez-vous préciser le service concerné ?"
            })

        row = conn.execute("""
            SELECT Service.nom_service, Hopital.num_tel, Hopital.nom
            FROM Hopital
            JOIN Service ON Hopital.id_hopital = Service.id_hopital
            WHERE lower(Service.nom_service) = lower(?)
        """, (nom_service,)).fetchone()

        conn.close()

        if not row:
            return jsonify({
                "intent": intent,
                "response": "Je n'ai pas trouvé les coordonnées demandées."
            })

        return jsonify({
            "intent": intent,
            "response": f"Pour le service de {row['nom_service']}, vous pouvez contacter {row['nom']} au {row['num_tel']}.",
            "data": dict(row)
        })

    elif intent == "information_pharmacie":
        rows = conn.execute("""
            SELECT nom, adresse, distance, horaire
            FROM Pharmacie
            ORDER BY distance ASC
            LIMIT 3
        """).fetchall()

        conn.close()

        pharmacies = [dict(row) for row in rows]

        if not pharmacies:
            return jsonify({
                "intent": intent,
                "response": "Je ne dispose pas d'information sur les pharmacies."
            })

        first = pharmacies[0]
        return jsonify({
            "intent": intent,
            "response": (
                f"La pharmacie la plus proche est {first['nom']}, située à {first['adresse']}, "
                f"à environ {first['distance']} km. Horaires : {first['horaire']}."
            ),
            "data": pharmacies
        })

    else:
        conn.close()
        return jsonify({
            "intent": "inconnu",
            "response": "Je n'ai pas compris votre demande. Vous pouvez me demander un service, un médecin, des horaires ou une pharmacie."
        })


if __name__ == "__main__":
    app.run(debug=True)