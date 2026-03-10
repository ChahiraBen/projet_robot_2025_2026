const sendBtn = document.getElementById("sendBtn");
const messageInput = document.getElementById("message");
const responseBox = document.getElementById("response");

async function sendMessage() {
    const message = messageInput.value.trim();

    if (!message) {
        responseBox.textContent = "Veuillez saisir une question.";
        return;
    }

    responseBox.textContent = "Chargement...";

    try {
        const res = await fetch("/api/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ message })
        });

        const data = await res.json();

        if (!res.ok) {
            responseBox.textContent = data.response || data.error || "Erreur serveur.";
            return;
        }

        responseBox.textContent = data.response;
    } catch (error) {
        responseBox.textContent = "Impossible de contacter le serveur.";
    }
}

sendBtn.addEventListener("click", sendMessage);

messageInput.addEventListener("keypress", function(event) {
    if (event.key === "Enter") {
        sendMessage();
    }
});