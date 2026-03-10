import json
from config import client
from memory import get_history

def generate_final_response_with_gemini(user_message, analysis=None, db_result=None):
    try:
        history = get_history()
        history_text = "\n".join(
            [f"{item['role']}: {item['text']}" for item in history]
        )

        prompt = f"""
Tu es un assistant d'accueil hospitalier.
Tu réponds en français, de manière claire, naturelle, polie et concise.

Règles importantes :
- Utilise uniquement les informations fournies.
- N'invente jamais d'information.
- Si une information manque, dis-le simplement.
- Tiens compte de l'historique si c'est utile.
- Réponds en 1 à 3 phrases maximum.
- Ne réponds pas en JSON.
- Ne mets pas de balises markdown.

Historique de conversation :
{history_text if history_text else "Aucun historique."}

Dernière question utilisateur :
{user_message}

Analyse de la demande :
{json.dumps(analysis, ensure_ascii=False, indent=2) if analysis is not None else "Aucune analyse."}

Résultat base de données :
{json.dumps(db_result, ensure_ascii=False, indent=2) if db_result is not None else "Aucun résultat."}

Rédige maintenant la réponse finale pour l'utilisateur :
"""

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        text = (response.text or "").strip()

        if not text:
            return "Je n'ai pas pu générer une réponse pour le moment."

        return text

    except Exception as e:
        print("Erreur Gemini réponse :", e)
        return "Je suis désolé, je n'ai pas pu générer une réponse pour le moment."