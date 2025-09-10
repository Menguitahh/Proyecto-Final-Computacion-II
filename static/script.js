document.addEventListener("DOMContentLoaded", function() {
    const chatWindow = document.getElementById("chat-window");
    const messageInput = document.getElementById("message-input");
    const sendButton = document.getElementById("send-button");

    // Persistimos el clientId en localStorage para mantener historial entre sesiones
    let clientId = localStorage.getItem('fitbotClientId');
    if (!clientId) {
        clientId = Date.now().toString(36) + Math.random().toString(36).substring(2);
        localStorage.setItem('fitbotClientId', clientId);
    }
    
    const wsScheme = location.protocol === 'https:' ? 'wss' : 'ws';
    const wsHost = location.host || '127.0.0.1:8000';
    const ws = new WebSocket(`${wsScheme}://${wsHost}/ws/${clientId}`);

    // Tema único (oscuro minimal). Se elimina el soporte de toggle.

    function addMessage(content, sender) {
        const messageWrapper = document.createElement('div');
        
        if (sender === 'user') {
            // Burbuja del usuario
            messageWrapper.className = 'd-flex justify-content-end';
            messageWrapper.innerHTML = `
                <div class="p-2 rounded" style="background-color: #0d6efd; color: white; max-width: 80%;">
                    ${content}
                </div>
            `;
        } else {
            // Burbuja del bot
            messageWrapper.className = 'd-flex justify-content-start';
            const botMessageText = content.replace(/^FitBot:\s*/, '');
            // Convierte Markdown a HTML y lo sanitiza por seguridad
            const formattedContent = DOMPurify.sanitize(marked.parse(botMessageText));
            
            messageWrapper.innerHTML = `
                <div class="p-2 rounded bg-secondary text-white" style="max-width: 80%;">
                    <div class="bot-message-content">
                        ${formattedContent}
                    </div>
                </div>
            `;
        }
        
        chatWindow.appendChild(messageWrapper);
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }

    // El resto del script (indicador de "pensando", websockets) permanece igual.
    function showTypingIndicator() {
        if (document.getElementById('typing-indicator')) return;
        const indicatorWrapper = document.createElement('div');
        indicatorWrapper.id = 'typing-indicator';
        indicatorWrapper.className = 'd-flex justify-content-start';
        indicatorWrapper.innerHTML = `
            <div class="p-2 rounded bg-secondary text-white">
                <div class="typing-indicator-dots">
                    <span></span><span></span><span></span>
                </div>
            </div>
        `;
        chatWindow.appendChild(indicatorWrapper);
        chatWindow.scrollTop = chatWindow.scrollHeight;

        // Añadimos el CSS de la animación dinámicamente
        const style = document.createElement('style');
        style.innerHTML = `
            .typing-indicator-dots span {
                height: 8px; width: 8px; background-color: rgba(255,255,255,0.5);
                border-radius: 50%; display: inline-block; margin: 0 2px;
                animation: blink 1.2s infinite;
            }
            @keyframes blink { 50% { background-color: rgba(255,255,255,1); transform: translateY(-3px); } }
            .typing-indicator-dots span:nth-child(2) { animation-delay: 0.2s; }
            .typing-indicator-dots span:nth-child(3) { animation-delay: 0.4s; }
        `;
        document.head.appendChild(style);
    }

    function hideTypingIndicator() {
        const indicator = document.getElementById('typing-indicator');
        if (indicator) indicator.remove();
    }

    ws.onmessage = async function(event) {
        hideTypingIndicator();
        let text;
        if (typeof event.data === 'string') {
            text = event.data;
        } else if (event.data && typeof event.data.text === 'function') {
            text = await event.data.text();
        }

        if (typeof text === 'string') {
            const raw = text.trim();
            // Intentá parsear siempre; si falla, mostramos como texto
            try {
                const data = JSON.parse(raw);
                if (data && data.type === 'history' && Array.isArray(data.messages)) {
                    for (const m of data.messages) {
                        const sender = m.role === 'user' ? 'user' : 'bot';
                        addMessage(m.content, sender);
                    }
                    return;
                }
                if (data && data.type === 'message') {
                    const sender = data.role === 'user' ? 'user' : 'bot';
                    addMessage(data.content, sender);
                    return;
                }
                // Si es otro objeto, mostralo serializado por depuración
                addMessage(raw, 'bot');
                return;
            } catch {
                // No era JSON válido → texto plano
                addMessage(text, 'bot');
                return;
            }
        }
        addMessage(String(event.data), 'bot');
    };

    // Auto-resize del textarea
    function autoResize() {
        if (!messageInput) return;
        messageInput.style.height = 'auto';
        messageInput.style.height = Math.min(messageInput.scrollHeight, window.innerHeight * 0.33) + 'px';
    }
    if (messageInput) {
        messageInput.addEventListener('input', autoResize);
        // Ajuste inicial
        autoResize();
    }

    function sendMessage() {
        const message = messageInput.value.trim();
        if (message !== "" && ws.readyState === WebSocket.OPEN) {
            ws.send(message);
            addMessage(message, 'user');
            messageInput.value = "";
            autoResize();
            showTypingIndicator();
        }
    }

    sendButton.addEventListener("click", sendMessage);
    // Enter para enviar, Shift+Enter para salto de línea
    messageInput.addEventListener("keydown", (event) => {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            sendMessage();
        }
    });

    // Manejadores de conexión (onerror, onclose, etc.)
    ws.onopen = () => console.log("Conectado al servidor de FitBot.");
    ws.onerror = (event) => { console.error("Error de WebSocket:", event); hideTypingIndicator(); };
    ws.onclose = () => { console.log("Desconectado del servidor de FitBot."); hideTypingIndicator(); };
});
