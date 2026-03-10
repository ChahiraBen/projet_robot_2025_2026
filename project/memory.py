conversation_history = []
MAX_HISTORY = 6

conversation_context = {
    "last_service": None,
    "last_doctor": None,
    "last_intent": None
}

def add_to_history(role, text):
    conversation_history.append({
        "role": role,
        "text": text
    })
    if len(conversation_history) > MAX_HISTORY:
        conversation_history.pop(0)

def get_history():
    return conversation_history

def clear_history():
    conversation_history.clear()
    conversation_context["last_service"] = None
    conversation_context["last_doctor"] = None
    conversation_context["last_intent"] = None

def update_context(service=None, doctor=None, intent=None):
    if service:
        conversation_context["last_service"] = service
    if doctor:
        conversation_context["last_doctor"] = doctor
    if intent:
        conversation_context["last_intent"] = intent

def get_context():
    return conversation_context