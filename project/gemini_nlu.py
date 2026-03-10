import json
from typing import Optional
from pydantic import BaseModel
from google.genai import types
from config import client

class NLUResponse(BaseModel):
    intent: str
    service: Optional[str] = None
    doctor: Optional[str] = None
    needs_clarification: bool
    clarification_question: Optional[str] = None

NLU_PROMPT = """
Tu es un module NLU pour un robot d'accueil hospitalier.

Analyse le message utilisateur et retourne uniquement un objet JSON.

Intentions autorisées :
- salutation
- au_revoir
- localisation_service
- horaires_service
- localisation_medecin
- contact_service
- information_pharmacie
- inconnu

Règles :
- salutation : bonjour, salut...
- au_revoir : au revoir, bye...
- localisation_service : l'utilisateur cherche où se trouve un service
- horaires_service : l'utilisateur demande les horaires d'un service
- localisation_medecin : l'utilisateur cherche un docteur / médecin
- contact_service : l'utilisateur demande numéro, téléphone, contact d'un service
- information_pharmacie : l'utilisateur demande une pharmacie
- inconnu : si la demande ne correspond à rien

Normalisation :
- Pour les services, utilise si possible ces noms :
  cardiologie, radiologie, urgences, admissions, pediatrie, laboratoire
- Convertis par exemple :
  cardio -> cardiologie
  cardiologue -> cardiologie
  radio -> radiologie
  urgence -> urgences
  labo -> laboratoire
  pédiatrie -> pediatrie
  pédiatre -> pediatrie

Retourne ce format JSON :
{
  "intent": "inconnu",
  "service": null,
  "doctor": null,
  "needs_clarification": false,
  "clarification_question": null
}

Message utilisateur :
"""

def analyze_with_gemini(message):
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"{NLU_PROMPT}\n{message}",
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=NLUResponse
            )
        )

        data = json.loads(response.text)
        print("Analyse Gemini :", data)

        return {
            "intent": data.get("intent", "inconnu"),
            "service": data.get("service"),
            "doctor": data.get("doctor"),
            "needs_clarification": data.get("needs_clarification", False),
            "clarification_question": data.get("clarification_question")
        }

    except Exception as e:
        print("Erreur Gemini NLU :", e)
        return {
            "intent": "inconnu",
            "service": None,
            "doctor": None,
            "needs_clarification": False,
            "clarification_question": None
        }