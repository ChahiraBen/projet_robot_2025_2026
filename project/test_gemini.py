import json
from google import genai

PROMPT_TEMPLATE = """
Tu es un module NLU pour un robot d'accueil hospitalier.

Ta tâche :
1. Détecter l'intention de l'utilisateur
2. Extraire les entités utiles
3. Répondre UNIQUEMENT en JSON valide
4. Ne rien écrire avant ou après le JSON

Intentions possibles :
- ask_service_location
- ask_doctor_info
- ask_schedule
- ask_contact
- greeting
- unknown

Format JSON attendu :
{{
  "intent": "unknown",
  "service": null,
  "doctor": null,
  "needs_clarification": false,
  "clarification_question": null
}}

Règles :
- Si l'utilisateur demande où se trouve un service, intent = "ask_service_location"
- Si l'utilisateur demande un médecin, intent = "ask_doctor_info"
- Si l'utilisateur demande un horaire, intent = "ask_schedule"
- Si l'utilisateur demande un contact ou téléphone, intent = "ask_contact"
- Si le message est une salutation simple, intent = "greeting"
- Si ce n'est pas clair, intent = "unknown"
- Si une information manque, mets needs_clarification = true
- clarification_question doit contenir une question courte si besoin, sinon null
- service et doctor doivent être null si absents

Message utilisateur :
"{user_message}"
"""

def clean_json_text(text):
    text = text.strip()

    if text.startswith("```json"):
        text = text[len("```json"):].strip()
    elif text.startswith("```"):
        text = text[len("```"):].strip()

    if text.endswith("```"):
        text = text[:-3].strip()

    return text

def analyze_message(client, user_message):
    prompt = PROMPT_TEMPLATE.format(user_message=user_message)

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    raw_text = response.text.strip()
    print("\nRéponse brute Gemini :")
    print(raw_text)

    cleaned_text = clean_json_text(raw_text)
    print("\nRéponse nettoyée :")
    print(cleaned_text)

    try:
        data = json.loads(cleaned_text)
        print("\nJSON décodé avec succès :")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return data
    except json.JSONDecodeError as e:
        print("\nErreur JSON :", e)
        return None

def main():
    client = genai.Client()

    tests = [
        "Où se trouve le service cardiologie ?",
        "Je cherche le docteur Benali",
        "Quels sont les horaires du laboratoire ?",
        "Donne-moi le numéro du service radiologie",
        "Bonjour",
        "Je cherche un service",
    ]

    for msg in tests:
        print("\n" + "=" * 60)
        print("Message :", msg)
        analyze_message(client, msg)

if __name__ == "__main__":
    main()