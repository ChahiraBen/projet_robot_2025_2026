from flask import request, jsonify, render_template
from database import get_db_connection
from gemini_nlu import analyze_with_gemini
from gemini_response import generate_final_response_with_gemini
from memory import add_to_history, update_context, get_context

def register_routes(app):
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

        analysis = analyze_with_gemini(message)
        intent = analysis["intent"]
        nom_service = analysis["service"]
        nom_medecin = analysis["doctor"]

        context = get_context()

        # Réutilisation du contexte conversationnel
        if not nom_service and intent in ["horaires_service", "contact_service", "localisation_service"]:
            nom_service = context["last_service"]

        if not nom_medecin and intent == "localisation_medecin":
            nom_medecin = context["last_doctor"]

        # Si Gemini demande une clarification mais qu'on a déjà le contexte, on annule la clarification
        if analysis["needs_clarification"]:
            if intent in ["horaires_service", "contact_service", "localisation_service"] and nom_service:
                analysis["needs_clarification"] = False
            elif intent == "localisation_medecin" and nom_medecin:
                analysis["needs_clarification"] = False
            else:
                response_text = analysis["clarification_question"] or "Pouvez-vous préciser votre demande ?"
                add_to_history("user", message)
                add_to_history("assistant", response_text)
                return jsonify({
                    "intent": intent,
                    "response": response_text
                })

        # Mise à jour du contexte après résolution
        update_context(service=nom_service, doctor=nom_medecin, intent=intent)

        conn = get_db_connection()

        if intent == "salutation":
            db_result = {"type": "salutation"}

        elif intent == "au_revoir":
            db_result = {"type": "au_revoir"}

        elif intent == "localisation_service":
            if not nom_service:
                conn.close()
                response_text = "Pouvez-vous préciser le nom du service recherché ?"
                add_to_history("user", message)
                add_to_history("assistant", response_text)
                return jsonify({"intent": intent, "response": response_text})

            row = conn.execute("""
                SELECT nom_service, etage, batiment, horaire
                FROM Service
                WHERE lower(nom_service) = lower(?)
            """, (nom_service,)).fetchone()

            if not row:
                conn.close()
                db_result = {"error": "service_introuvable", "service": nom_service}
                response_text = generate_final_response_with_gemini(message, analysis, db_result)
                add_to_history("user", message)
                add_to_history("assistant", response_text)
                return jsonify({"intent": intent, "response": response_text})

            db_result = dict(row)
            update_context(service=db_result.get("nom_service"), intent=intent)

        elif intent == "horaires_service":
            if not nom_service:
                conn.close()
                response_text = "Pouvez-vous préciser le service dont vous voulez les horaires ?"
                add_to_history("user", message)
                add_to_history("assistant", response_text)
                return jsonify({"intent": intent, "response": response_text})

            row = conn.execute("""
                SELECT nom_service, horaire
                FROM Service
                WHERE lower(nom_service) = lower(?)
            """, (nom_service,)).fetchone()

            if not row:
                conn.close()
                db_result = {"error": "horaires_introuvables", "service": nom_service}
                response_text = generate_final_response_with_gemini(message, analysis, db_result)
                add_to_history("user", message)
                add_to_history("assistant", response_text)
                return jsonify({"intent": intent, "response": response_text})

            db_result = dict(row)
            update_context(service=db_result.get("nom_service"), intent=intent)

        elif intent == "localisation_medecin":
            if not nom_medecin:
                conn.close()
                response_text = "Pouvez-vous préciser le nom du médecin ?"
                add_to_history("user", message)
                add_to_history("assistant", response_text)
                return jsonify({"intent": intent, "response": response_text})

            row = conn.execute("""
                SELECT Medecin.nom, Medecin.bureau, Medecin.horaire,
                       Service.nom_service, Service.etage, Service.batiment
                FROM Medecin
                JOIN Service ON Medecin.id_service = Service.id_service
                WHERE lower(Medecin.nom) = lower(?)
            """, (nom_medecin,)).fetchone()

            if not row:
                conn.close()
                db_result = {"error": "medecin_introuvable", "doctor": nom_medecin}
                response_text = generate_final_response_with_gemini(message, analysis, db_result)
                add_to_history("user", message)
                add_to_history("assistant", response_text)
                return jsonify({"intent": intent, "response": response_text})

            db_result = dict(row)
            update_context(
                doctor=db_result.get("nom"),
                service=db_result.get("nom_service"),
                intent=intent
            )

        elif intent == "contact_service":
            if not nom_service:
                conn.close()
                response_text = "Pouvez-vous préciser le service concerné ?"
                add_to_history("user", message)
                add_to_history("assistant", response_text)
                return jsonify({"intent": intent, "response": response_text})

            row = conn.execute("""
                SELECT Service.nom_service, Hopital.num_tel, Hopital.nom
                FROM Hopital
                JOIN Service ON Hopital.id_hopital = Service.id_hopital
                WHERE lower(Service.nom_service) = lower(?)
            """, (nom_service,)).fetchone()

            if not row:
                conn.close()
                db_result = {"error": "contact_introuvable", "service": nom_service}
                response_text = generate_final_response_with_gemini(message, analysis, db_result)
                add_to_history("user", message)
                add_to_history("assistant", response_text)
                return jsonify({"intent": intent, "response": response_text})

            db_result = dict(row)
            update_context(service=db_result.get("nom_service"), intent=intent)

        elif intent == "information_pharmacie":
            rows = conn.execute("""
                SELECT nom, adresse, distance, horaire
                FROM Pharmacie
                ORDER BY distance ASC
                LIMIT 3
            """).fetchall()

            db_result = [dict(row) for row in rows]
            update_context(intent=intent)

        else:
            db_result = {"error": "incompris"}
            update_context(intent=intent)

        conn.close()

        response_text = generate_final_response_with_gemini(message, analysis, db_result)
        add_to_history("user", message)
        add_to_history("assistant", response_text)

        return jsonify({
            "intent": intent,
            "response": response_text,
            "data": db_result
        })